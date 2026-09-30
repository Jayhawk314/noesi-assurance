# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""WorkbenchService: typed use cases over the transactional spine.

Authorization model (pilot): the first principal to create an engagement is
its partner; partners assign the team; preparers ingest, map, normalize,
and execute; reviewers approve mappings and review runs; partners approve
reviewed runs and lock. Separation of duties comes from the domain layer
and the repositories -- this service adds the role matrix, never replaces
those checks.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sqlite3
from decimal import ROUND_HALF_UP, Decimal

from assurance_artifacts import xlsx
from assurance_artifacts.intake import store_artifact
from assurance_artifacts.vault import ArtifactVault
from assurance_domain.commands import Command
from assurance_domain.errors import ConflictError, DuplicateError, NotFoundError
from assurance_domain.identities import new_id
from assurance_domain.lifecycle import SeparationOfDutiesError
from assurance_domain.jobs import build_manifest, run_job
from assurance_domain.readiness import blank_engagement, readiness
from assurance_domain.sad import (
    requires_concurrence, summary_of_differences, trivial_rate,
)
from assurance_persistence.database import utcnow
from assurance_persistence.spine import run_command
from procedures_ap.coverage import compile_coverage, inventory_from_tables
from procedures_ap import quickbooks
from procedures_ap.engines import ENGINE_VERSION
from procedures_cycles import engines as cycle_engines
from procedures_cycles.contracts import (
    CYCLE_CONTRACTS_BY_ID, ENGAGEMENT_POLICIES, SCOPES, SCOPE_OF,
    contracts_for_scope,
)
from procedures_cycles.engines import execute_procedure
from procedures_ap.ingest import (
    MappingSpec, NormalizedTable, infer_role, normalize_table, propose_mapping,
)


def _engine_version(procedure_id: str) -> str:
    """AP runs keep their engine version (and so their job identities)."""
    return (cycle_engines.ENGINE_VERSION if procedure_id in CYCLE_CONTRACTS_BY_ID
            else ENGINE_VERSION)


class AuthorizationError(PermissionError):
    """The authenticated principal lacks the role this action requires."""


def _finding_uid(verdict: dict) -> str:
    """Engagement-scoped stable finding identity: domain + key, no company."""
    return f"{verdict['domain']}|{json.dumps(verdict['key'], ensure_ascii=False)}"


SCHEDULE_PROCEDURE = "completion.uncorrected_misstatements"

# The procedures that test for a fraud scheme, with the scheme they look for
# and the standard behind them (AU-C 240). The fraud view gathers these.
FRAUD_TESTS: dict[str, tuple[str, str]] = {
    "ap.vendor_relational_twins": ("Shell or duplicate vendors",
                                   "AU-C 240: fictitious or duplicate suppliers"),
    "ap.duplicate_bills": ("The same invoice paid twice",
                           "AU-C 240: misappropriation by duplicate payment"),
    "ap.payments_without_bills": ("Payments with no bill behind them",
                                  "AU-C 240: disbursement fraud"),
    "ap.payment_voucher_reference": ("Payments not tied to an approved voucher",
                                     "AU-C 240: disbursement fraud"),
    "ap.document_chain": ("Broken order-to-payment chain",
                          "AU-C 240: disbursement fraud"),
    "ap.split_payment_review": ("Purchases split to stay under an approval limit",
                                "AU-C 240: override of approval controls"),
    "ap.segregation_of_duties": ("One person enters and approves",
                                 "AU-C 240: opportunity from incompatible duties"),
    "forensic.closed_value_flow": ("Money that goes round in a circle",
                                   "AU-C 240: round-tripping"),
    "je.journal_entry_testing": ("Management override through journal entries",
                                 "AU-C 240.32: journal entry testing"),
    "je.population_completeness": ("A complete population for journal testing",
                                   "AU-C 240.32: the population tested is complete"),
    "payroll.register_tests": ("Ghost employees and payroll schemes",
                               "AU-C 240: payroll fraud"),
}


def _trivial_rate(document: dict) -> Decimal:
    """B1: the firm's clearly-trivial rate (policy clearly_trivial_pct), or
    the 5% default; one rate for the SAD, concurrence and revision impact."""
    return trivial_rate((document.get("policies") or {}).get("clearly_trivial_pct"))


class EngagementLockedError(PermissionError):
    """The engagement is locked; its record can no longer change."""


class EvidenceIntegrityError(RuntimeError):
    """Stored evidence no longer reproduces its recorded digest.

    Raised instead of serving unverifiable data. Distinct from a generic
    internal error so the boundary can *name* the integrity failure —
    an operator seeing it should suspect the evidence chain, not a crash
    (independent review 2026-08-07, F3).
    """


# The five judgments a disposition can record; "undisposed" is the absence
# of one, not a settable value.
_DISPOSITION_STATUSES = ("cleared", "unadjusted", "adjusted", "waived",
                         "follow_up")


class WorkbenchService:
    def __init__(self, conn: sqlite3.Connection, vault: ArtifactVault,
                 tenant_id: str, keystore=None):
        self._conn = conn
        self._vault = vault
        self._tenant = tenant_id
        self._keystore = keystore

    # ------------------------------------------------------------ plumbing

    def _command(self, actor: str, kind: str, engagement_id: str | None = None,
                 command_id: str | None = None) -> Command:
        return Command(command_id or new_id(), self._tenant, actor, kind,
                       engagement_id=engagement_id)

    def _roles(self, engagement_id: str, principal_id: str) -> set[str]:
        rows = self._conn.execute(
            """SELECT role FROM principal_assignment
               WHERE engagement_id = ? AND principal_id = ?""",
            (engagement_id, principal_id)).fetchall()
        return {row["role"] for row in rows}

    def _require(self, engagement_id: str, actor: str, *roles: str) -> None:
        have = self._roles(engagement_id, actor)
        if not have & set(roles):
            raise AuthorizationError(
                f"action requires one of {sorted(roles)} on this engagement")

    def _require_unlocked(self, engagement_id: str) -> None:
        info = self._engagement(engagement_id)
        if info["archived_at"]:
            raise EngagementLockedError(
                "the engagement is archived; restore it before changing its record")
        if info["status"] == "locked":
            raise EngagementLockedError(
                "the engagement is locked; unlock (with supersession) before "
                "changing its record")

    def _require_not_archived(self, engagement_id: str) -> None:
        if self._engagement(engagement_id)["archived_at"]:
            raise EngagementLockedError(
                "the engagement is archived; restore it first")

    def _set_archived(self, uow, engagement_id: str, expected_version: int,
                      when: str | None) -> None:
        """Set or clear the archive flag, leaving status and version alone."""
        cursor = uow.execute(
            """UPDATE engagement SET archived_at = ?
               WHERE engagement_id = ? AND tenant_id = ? AND version = ?""",
            (when, engagement_id, self._tenant, expected_version))
        if cursor.rowcount == 0:
            raise ConflictError("engagement", engagement_id, expected_version)

    # ----------------------------------------------- screen 1: engagement

    def create_engagement(self, actor: str, client_name: str,
                          period_end: str) -> dict:
        def handler(uow):
            engagement_id = uow.engagements.create(client_name, period_end)
            uow.principals.assign(engagement_id, actor, "partner")
            return {"engagement_id": engagement_id}
        return run_command(
            self._conn, self._command(actor, "engagement.create"),
            handler).result

    def list_engagements(self, *, archived: bool = False) -> list[dict]:
        """Open and locked engagements; with ``archived``, only the archived ones."""
        rows = self._conn.execute(
            f"""SELECT engagement_id, client_name, period_end, status, version
               FROM engagement WHERE tenant_id = ?
               AND archived_at IS {'NOT NULL' if archived else 'NULL'}
               ORDER BY client_name, period_end""", (self._tenant,)).fetchall()
        return [dict(row) for row in rows]

    def archive_engagement(self, actor: str, engagement_id: str, *,
                           reason: str) -> dict:
        """Take an engagement off the list without erasing its record.

        Partner only, with a specific reason. Nothing is deleted: the journal,
        sources, runs and any lock stay as they were. Archiving sets its own
        flag and never the status or version a signed lock covers, so a
        locked engagement stays locked and its lock still verifies. While
        archived, nothing in it can change.
        """
        if len(reason.strip()) < 10:
            raise ValueError("archiving requires a specific reason (ten characters or more)")
        info = self._engagement(engagement_id)
        if info["archived_at"]:
            raise ValueError("the engagement is already archived")

        def handler(uow):
            if not {"partner"} & uow.principals.roles_for(engagement_id, actor):
                raise AuthorizationError("only the partner archives an engagement")
            self._set_archived(uow, engagement_id, info["version"], utcnow())
            uow.emit(entity_type="engagement", entity_id=engagement_id,
                     event_type="engagement.archived",
                     payload={"reason": reason.strip(), "previous_status": info["status"]},
                     engagement_id=engagement_id)
            return {"engagement_id": engagement_id, "archived": True,
                    "version": info["version"]}
        return run_command(
            self._conn, self._command(actor, "engagement.archive", engagement_id),
            handler).result

    def delete_engagement(self, actor: str, engagement_id: str, *,
                          confirm_client_name: str, reason: str) -> dict:
        """Delete an engagement and everything loaded into it.

        Partner only; the exact client name must be typed back, with a reason.
        Every row that belongs to the engagement goes (sources, mappings,
        datasets, runs, dispositions, workflow, team, risks, locks), and each
        uploaded file whose bytes no other engagement uses. The journal keeps
        its lines for the engagement, plus one naming who deleted it and why:
        the journal is one hash chain across all engagements, and cutting lines
        out of it would break the trail check every other engagement relies on.
        """
        info = self._engagement(engagement_id)
        norm = lambda text: " ".join(text.split()).casefold()  # noqa: E731
        if norm(confirm_client_name) != norm(info["client_name"]):
            raise ValueError("type the client name exactly to confirm the delete")
        if len(reason.strip()) < 10:
            raise ValueError("deleting requires a specific reason (ten characters or more)")
        tables = [r["name"] for r in self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")
            if r["name"] not in ("engagement", "domain_event")
            and any(c["name"] == "engagement_id"
                    for c in self._conn.execute(f"PRAGMA table_info('{r['name']}')"))]
        shas = [r["sha256"] for r in self._conn.execute(
            "SELECT sha256 FROM artifact WHERE engagement_id = ?", (engagement_id,))]

        def handler(uow):
            if not {"partner"} & uow.principals.roles_for(engagement_id, actor):
                raise AuthorizationError("only the partner deletes an engagement")
            # A lock's signature hangs off its snapshot, not the engagement.
            uow.execute("""DELETE FROM lock_signature WHERE snapshot_id IN
                           (SELECT snapshot_id FROM lock_snapshot WHERE engagement_id = ?)""",
                        (engagement_id,))
            pending = list(tables)
            for _ in range(len(pending) + 1):          # children before parents
                left = []
                for table in pending:
                    try:
                        uow.execute(f"DELETE FROM {table} WHERE engagement_id = ?", (engagement_id,))
                    except sqlite3.IntegrityError:
                        left.append(table)
                if not left:
                    break
                pending = left
            else:
                raise RuntimeError(f"could not delete rows in {pending}")
            uow.execute("DELETE FROM engagement WHERE engagement_id = ? AND tenant_id = ?",
                        (engagement_id, self._tenant))
            uow.emit(entity_type="engagement", entity_id=engagement_id,
                     event_type="engagement.deleted",
                     payload={"client_name": info["client_name"], "period_end": info["period_end"],
                              "reason": reason.strip(), "files": len(shas)},
                     engagement_id=engagement_id)
            return {"engagement_id": engagement_id, "deleted": True}
        result = run_command(
            self._conn, self._command(actor, "engagement.delete", engagement_id), handler).result
        for sha in shas:                               # bytes no other engagement uses
            if not self._conn.execute("SELECT 1 FROM artifact WHERE sha256 = ? LIMIT 1", (sha,)).fetchone():
                self._vault.remove_blob(sha)
        return result

    def restore_engagement(self, actor: str, engagement_id: str) -> dict:
        """Bring an archived engagement back; its status never changed."""
        info = self._engagement(engagement_id)
        if not info["archived_at"]:
            raise ValueError("the engagement is not archived")

        def handler(uow):
            if not {"partner"} & uow.principals.roles_for(engagement_id, actor):
                raise AuthorizationError("only the partner restores an engagement")
            self._set_archived(uow, engagement_id, info["version"], None)
            uow.emit(entity_type="engagement", entity_id=engagement_id,
                     event_type="engagement.restored", payload={},
                     engagement_id=engagement_id)
            return {"engagement_id": engagement_id, "status": info["status"],
                    "version": info["version"]}
        return run_command(
            self._conn, self._command(actor, "engagement.restore", engagement_id),
            handler).result

    def assign_team(self, actor: str, engagement_id: str,
                    principal_id: str, role: str) -> dict:
        self._require_unlocked(engagement_id)

        def handler(uow):
            if not {"partner"} & uow.principals.roles_for(engagement_id, actor):
                raise AuthorizationError("only a partner assigns the team")
            uow.principals.assign(engagement_id, principal_id, role)
            return {"principal_id": principal_id, "role": role}
        return run_command(
            self._conn,
            self._command(actor, "team.assign", engagement_id), handler).result

    def team(self, engagement_id: str) -> list[dict]:
        rows = self._conn.execute(
            """SELECT principal_id, role FROM principal_assignment
               WHERE engagement_id = ? ORDER BY role, principal_id""",
            (engagement_id,)).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------- screen 2: sources and mappings

    def store_source(self, actor: str, engagement_id: str, *, content: bytes,
                     media_type: str, original_name: str,
                     provenance: str = "") -> dict:
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer", "partner")
        outcome = store_artifact(
            self._conn, self._vault,
            command=self._command(actor, "artifact.store", engagement_id),
            engagement_id=engagement_id, source=io.BytesIO(content),
            media_type=media_type, original_name=original_name,
            provenance=provenance)
        return outcome.result

    def propose_source_mapping(self, actor: str, engagement_id: str, *,
                               role: str, artifact_id: str,
                               extraction: dict | None = None) -> dict:
        """Propose a column mapping for one uploaded file.

        For an Excel workbook, ``extraction`` names the sheet and 1-based
        header row (defaults: the only sheet, the suggested header row).
        The resolved choice becomes part of the reviewed spec and of its
        digest, so the reviewer approves *which* rows were read, and every
        later rebuild reads exactly those rows again.
        """
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer")
        headers, _, resolved, _ = self._artifact_table(artifact_id, extraction)
        artifact = self._conn.execute(
            "SELECT sha256 FROM artifact WHERE artifact_id = ?",
            (artifact_id,)).fetchone()
        recipe = (quickbooks.get(resolved["recipe"])
                  if resolved and resolved.get("recipe") else None)
        if recipe is not None and role != recipe.role:
            raise ValueError(f"the {recipe.label} recipe produces {recipe.role}, "
                             f"not {role}")
        spec = propose_mapping(role, headers, source_sha256=artifact["sha256"],
                               proposed_by=actor,
                               column_map=recipe.column_map if recipe else None)
        if not spec.column_map:
            # K4: a mapping of nothing would "load" every row as an empty
            # record and report success. Refuse it here, where it can be fixed.
            raise ValueError(
                f"none of this file's headings ({', '.join(headers) or 'none'}) match a "
                f"{role} field ({', '.join(spec.refused_fields)}); rename the headings, "
                "choose the right sheet and heading row, or choose another role")
        stored = spec.to_dict()
        digest = spec.digest
        if resolved is not None:
            keys = ("converter", "sheet", "header_row") + (
                ("recipe", "recipe_version") if recipe else ())
            params = {k: resolved[k] for k in keys}
            stored["extraction"] = params
            if recipe is not None:
                # What the recipe checked, kept and left out, for the reviewer
                # deciding on approval. Derived from the file, so outside the
                # digest; normalization recomputes it from the vaulted bytes.
                stored["recipe_report"] = resolved["recipe_report"]
            digest = hashlib.sha256(
                (spec.digest + json.dumps(params, sort_keys=True))
                .encode("utf-8")).hexdigest()

        def handler(uow):
            spec_id = uow.mappings.propose(
                engagement_id, role=role, spec=stored,
                spec_digest=digest, proposed_by=actor,
                artifact_id=artifact_id)
            return {"spec_id": spec_id, "column_map": spec.column_map,
                    "unmapped_headers": list(spec.unmapped_headers),
                    "refused_fields": list(spec.refused_fields),
                    "extraction": resolved}
        return run_command(
            self._conn,
            self._command(actor, "mapping.propose", engagement_id),
            handler).result

    def approve_source_mapping(self, actor: str, engagement_id: str,
                               spec_id: str) -> dict:
        self._require_unlocked(engagement_id)

        def handler(uow):
            if "reviewer" not in uow.principals.roles_for(engagement_id, actor):
                raise AuthorizationError("mapping approval requires a reviewer")
            uow.mappings.approve(spec_id, approved_by=actor)
            return {"spec_id": spec_id, "status": "approved"}
        return run_command(
            self._conn,
            self._command(actor, "mapping.approve", engagement_id),
            handler).result

    def normalize_source(self, actor: str, engagement_id: str,
                         spec_id: str, *, mode: str | None = None) -> dict:
        """Load an approved mapping as a dataset.

        When the role already has data, ``mode`` must say what this file
        does: ``"replace"`` (a revised file supersedes what is in use) or
        ``"add"`` (more rows of the same kind, such as a second bank
        account's reconciliation). Guessing either way silently changes
        what every procedure reads, so a load without one is refused.
        """
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer")
        # The file and the approved mapping are immutable, so a second load
        # could only repeat the same rows as a confusing duplicate dataset.
        existing = self._conn.execute(
            "SELECT dataset_id FROM normalized_dataset WHERE mapping_spec_id = ?",
            (spec_id,)).fetchone()
        if existing is not None:
            raise DuplicateError(
                "normalized_dataset", spec_id,
                f"this mapping is already loaded (dataset "
                f"{existing['dataset_id'][:8]}); its file and approved mapping "
                f"cannot change, so loading again would only repeat the same "
                f"rows")
        table = self._rebuild_table(spec_id)
        in_use = self._role_states(engagement_id).get(table.role, [])
        if not in_use:
            load_mode = "first"
        elif mode not in ("replace", "add"):
            names = ", ".join(self._dataset_file(d) for d in in_use[-1][1])
            raise ValueError(
                f"{table.role} already has data in use ({names}). Say whether "
                f"this file replaces it (a revised file) or adds to it (more "
                f"rows of the same kind, e.g. another bank account)")
        else:
            load_mode = mode
        if load_mode == "add":
            current = self._verified_table(in_use[-1][1][0])
            if set(table.column_map) != set(current.column_map):
                raise ValueError(
                    f"cannot add this file to {table.role}: it maps "
                    f"{sorted(table.column_map)} but the data in use maps "
                    f"{sorted(current.column_map)}; rows combined across "
                    f"different fields would leave blanks a procedure would "
                    f"misread")

        def handler(uow):
            spec_row = uow.mappings.get(spec_id)
            dataset_id = uow.datasets.record(
                engagement_id, role=table.role, mapping_spec_id=spec_id,
                artifact_id=spec_row["artifact_id"],
                rows_in=len(table.records) + len(table.rejects),
                rows_loaded=len(table.records),
                rows_rejected=len(table.rejects),
                control_total=str(table.control_total)
                if table.control_total is not None else None,
                output_digest=table.output_digest, load_mode=load_mode)
            return {"dataset_id": dataset_id, "load_mode": load_mode,
                    "reconciliation": table.reconciliation()}
        return run_command(
            self._conn,
            self._command(actor, "dataset.normalize", engagement_id),
            handler).result

    # Bulk loading batches the *clicks*, never the review: each batch method
    # loops the corresponding single-item use case, so every item keeps its
    # own journaled command, its own role check, and the same separation-of-
    # duties gates. Items fail or are skipped individually — one bad file
    # never blocks the other nine — and the caller gets a per-item report.

    def propose_source_mappings(self, actor: str, engagement_id: str,
                                items: list[dict]) -> dict:
        """Batch propose. Each item: artifact_id plus an optional role; a
        missing role is inferred from the artifact's filename (still just a
        proposal for the reviewer). A file already under an active spec
        *for the same role* is skipped, so 'propose all' is safe to repeat;
        one file may still feed several roles (a QuickBooks Transaction List
        by Vendor holds both bills and purchase orders)."""
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer")
        active = {(row["artifact_id"], row["role"]) for row in self._conn.execute(
            """SELECT artifact_id, role FROM mapping_spec
               WHERE engagement_id = ? AND status != 'superseded'""",
            (engagement_id,))}
        results = []
        for item in items:
            artifact_id = str(item.get("artifact_id") or "")
            entry: dict = {"artifact_id": artifact_id}
            try:
                role = str(item.get("role") or "")
                extraction = item.get("extraction")
                if not role and isinstance(extraction, dict) \
                        and extraction.get("recipe"):
                    role = quickbooks.get(str(extraction["recipe"])).role
                if not role:
                    name = self._conn.execute(
                        "SELECT original_name FROM artifact "
                        "WHERE artifact_id = ?",
                        (artifact_id,)).fetchone()
                    if name is None:
                        raise KeyError(f"artifact {artifact_id}")
                    role = self._guess_role(artifact_id,
                                            name["original_name"])[0] or ""
                if not role:
                    raise ValueError(
                        "no role given and none inferable from the "
                        "filename or its columns; choose the role explicitly")
                if (artifact_id, role) in active:
                    entry.update(status="skipped", role=role,
                                 reason="an active mapping spec already "
                                        f"maps this file as {role}")
                    results.append(entry)
                    continue
                entry.update(self.propose_source_mapping(
                    actor, engagement_id, role=role,
                    artifact_id=artifact_id,
                    extraction=extraction if isinstance(extraction, dict)
                    else None))
                entry.update(status="proposed", role=role)
                active.add((artifact_id, role))
            except (ValueError, KeyError, NotFoundError) as exc:
                entry.update(status="error", error=str(exc))
            results.append(entry)
        return _batch_report(results, done="proposed")

    def approve_source_mappings(self, actor: str, engagement_id: str,
                                spec_ids: list[str]) -> dict:
        """Batch approve, for the reviewer's single pass over a bulk load.
        Non-proposed specs are skipped; separation of duties still refuses,
        per item, any spec the approver proposed themselves."""
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "reviewer")
        results = []
        for spec_id in spec_ids:
            entry: dict = {"spec_id": str(spec_id)}
            try:
                row = self._conn.execute(
                    "SELECT status FROM mapping_spec WHERE spec_id = ?",
                    (str(spec_id),)).fetchone()
                if row is None:
                    raise KeyError(f"mapping_spec {spec_id}")
                if row["status"] != "proposed":
                    entry.update(status="skipped",
                                 reason=f"spec is {row['status']}, "
                                        "not proposed")
                else:
                    self.approve_source_mapping(actor, engagement_id,
                                                str(spec_id))
                    entry.update(status="approved")
            except (ValueError, KeyError, NotFoundError, ConflictError,
                    SeparationOfDutiesError) as exc:
                entry.update(status="error", error=str(exc))
            results.append(entry)
        return _batch_report(results, done="approved")

    def normalize_sources(self, actor: str, engagement_id: str,
                          spec_ids: list[str],
                          modes: dict[str, str] | None = None) -> dict:
        """Batch normalize approved specs. Specs that already produced a
        dataset are skipped rather than re-recorded. ``modes`` gives the
        replace/add choice per spec where its role already has data."""
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer")
        normalized = {row["mapping_spec_id"] for row in self._conn.execute(
            "SELECT mapping_spec_id FROM normalized_dataset "
            "WHERE engagement_id = ?", (engagement_id,))}
        results = []
        for spec_id in spec_ids:
            entry: dict = {"spec_id": str(spec_id)}
            try:
                if spec_id in normalized:
                    entry.update(status="skipped",
                                 reason="this spec already produced a "
                                        "dataset")
                else:
                    entry.update(self.normalize_source(
                        actor, engagement_id, str(spec_id),
                        mode=(modes or {}).get(str(spec_id))))
                    entry.update(status="normalized")
            except (ValueError, KeyError, NotFoundError) as exc:
                entry.update(status="error", error=str(exc))
            results.append(entry)
        return _batch_report(results, done="normalized")

    def sources(self, engagement_id: str) -> dict:
        """Screen 2 inventory: artifacts, mapping specs, dataset receipts."""
        artifacts = []
        for row in self._conn.execute(
                """SELECT artifact_id, sha256, size_bytes, media_type,
                   original_name, provenance, state, created_at FROM artifact
                   WHERE engagement_id = ? ORDER BY created_at, rowid""",
                (engagement_id,)):
            item = dict(row)
            item["inferred_role"], item["inferred_from"] = self._guess_role(
                item["artifact_id"], item["original_name"])
            artifacts.append(item)
        specs = []
        for row in self._conn.execute(
                """SELECT spec_id, role, artifact_id, spec, status,
                   proposed_by, approved_by, created_at FROM mapping_spec
                   WHERE engagement_id = ? ORDER BY created_at, rowid""",
                (engagement_id,)):
            item = dict(row)
            stored = json.loads(item.pop("spec"))
            item["column_map"] = stored.get("column_map", {})
            item["unmapped_headers"] = stored.get("unmapped_headers", [])
            item["refused_fields"] = stored.get("refused_fields", [])
            item["extraction"] = stored.get("extraction")
            item["recipe_report"] = stored.get("recipe_report")
            specs.append(item)
        datasets = [dict(row) for row in self._conn.execute(
            """SELECT dataset_id, role, mapping_spec_id, artifact_id, rows_in,
               rows_loaded, rows_rejected, control_total, output_digest,
               load_mode, created_at FROM normalized_dataset
               WHERE engagement_id = ? ORDER BY created_at, rowid""",
            (engagement_id,))]
        # The datasets procedures read, from the same derivation _tables
        # uses: a replaced file is visibly out of use, an added one in use.
        in_use = {d["dataset_id"] for states in
                  self._role_states(engagement_id).values()
                  for d in states[-1][1]}
        for dataset in datasets:
            dataset["in_use"] = dataset["dataset_id"] in in_use
            dataset["rejected_reasons"] = (
                self._rejected_reasons(dataset["mapping_spec_id"])
                if dataset["rows_rejected"] else [])
        # Every data type the engine can load (payables and cycle roles), so
        # the "map as" choice always matches the engine.
        from procedures_ap.ingest import ROLE_SCHEMAS
        return {"artifacts": artifacts, "mapping_specs": specs,
                "datasets": datasets, "roles": sorted(ROLE_SCHEMAS)}

    def _rejected_reasons(self, spec_id: str) -> list[dict]:
        """Why rows were set aside, grouped by reason with their row numbers.
        Reperformed from the vaulted file like every other read; if that
        fails, the failure is the answer rather than a broken listing."""
        try:
            rejects = self._rebuild_table(spec_id).rejects
        except Exception as exc:  # noqa: BLE001 — shown, not swallowed
            return [{"reason": f"could not reperform: {exc}", "rows": 0,
                     "source_rows": []}]
        grouped: dict[str, list[int]] = {}
        for reject in rejects:
            grouped.setdefault(reject["reason"], []).append(reject["source_row"])
        return [{"reason": reason, "rows": len(rows), "source_rows": rows[:10]}
                for reason, rows in grouped.items()]

    # --------------------------------------------- screen 3: coverage

    def _contracts(self, document: dict) -> tuple:
        """The eleven AP contracts plus the cycle contracts in scope. An
        engagement that sets a scope without payables does not carry the AP
        procedures either: "11 blocked" there reads as work left undone (K14)."""
        from procedures_ap.contracts import PROCEDURES
        cycles = document.get("cycles")
        ap = PROCEDURES if not cycles or "payables" in cycles else ()
        return ap + contracts_for_scope(cycles)

    def _engagement_policies(self, engagement_id: str, document: dict) -> dict:
        """Approved policies plus the engagement's own period end and materiality.

        Cycle contracts read ``period_end`` and ``materiality`` as policies;
        they come from the engagement record, never retyped. AP runs do not
        receive them, so AP manifests (and job identities) are unchanged.
        """
        info = self._engagement(engagement_id)
        policies = dict(document.get("policies") or {})
        policies.setdefault("period_end", str(info["period_end"]))
        start = (document.get("period") or {}).get("start")
        if start:
            policies.setdefault("period_start", str(start))
        if document.get("line_mapping"):
            policies.setdefault("line_mapping",
                                json.dumps(document["line_mapping"], sort_keys=True))
        amount = (document.get("materiality") or {}).get("amount")
        if amount:
            policies.setdefault("materiality", str(amount))
        return policies

    def coverage(self, engagement_id: str) -> dict:
        tables = self._tables(engagement_id)
        document, _ = self.workflow_document(engagement_id)
        contracts = self._contracts(document)
        # An AP-only engagement (no scope) compiles exactly as it always has.
        policies = (self._engagement_policies(engagement_id, document)
                    if document.get("cycles") else document.get("policies"))
        return compile_coverage(inventory_from_tables(tables),
                                policies=policies or None, contracts=contracts,
                                executors=cycle_engines.registered_procedures())

    # ---------------------------------------- screen 4: runs and findings

    def run_procedure(self, actor: str, engagement_id: str, *,
                      procedure_id: str,
                      policies: dict | None = None) -> dict:
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer")
        tables = {role: list(t.engine_view().records)
                  for role, t in self._tables(engagement_id).items()}
        # Which loaded files the run read, so a combined input is on record.
        datasets_read = {
            role: [d["dataset_id"] for d in states[-1][1]]
            for role, states in self._role_states(engagement_id).items()}
        # Approved engagement policies (workflow document) apply to every
        # run; explicit per-run values override them. Coverage compiles
        # against the same document, so what coverage calls executable is
        # what the run actually receives.
        document, _ = self.workflow_document(engagement_id)
        if procedure_id not in {c.procedure_id for c in self._contracts(document)}:
            from procedures_ap.contracts import CONTRACTS_BY_ID
            if procedure_id in CYCLE_CONTRACTS_BY_ID or procedure_id in CONTRACTS_BY_ID:
                raise ValueError(
                    f"procedure {procedure_id!r} is outside the engagement scope")
        base = (self._engagement_policies(engagement_id, document)
                if procedure_id in CYCLE_CONTRACTS_BY_ID
                else document.get("policies") or {})
        effective_policies = {**base, **(policies or {})}
        # A run is a claim that a test was performed. Unless coverage,
        # compiled on the same data and these policies, calls the procedure
        # executable, the attempt is recorded as an error with the reason
        # (attempts are journaled, never hidden) and never as "completed":
        # otherwise a sealed record could say "completed, 0 findings" over a
        # population that was never there.
        compiled = compile_coverage(
            inventory_from_tables(self._tables(engagement_id)),
            policies=effective_policies or None,
            contracts=self._contracts(document),
            executors=cycle_engines.registered_procedures())
        row = next((r for r in compiled["procedures"]
                    if r["procedure_id"] == procedure_id), None)
        if row is None:
            raise ValueError(f"unknown procedure {procedure_id!r}")
        not_runnable = ""
        if row["status"] != "executable":
            gaps = (row["missing_roles"] or row["missing_fields"]
                    or row["missing_policies"] or row.get("unsupported_reason"))
            not_runnable = (f"{procedure_id} is {row['status']} on this engagement's "
                            f"data and policies: missing {gaps}")
        # Reperformance is legitimate — after a reviewer sends work back, or
        # after an unlock. Same procedure, same data, same policies must
        # still mint a distinct job, so the manifest carries a rerun
        # sequence instead of colliding on the frozen job_id.
        rerun_sequence = self._conn.execute(
            """SELECT COUNT(*) AS c FROM procedure_run
               WHERE engagement_id = ? AND procedure_id = ?""",
            (engagement_id, procedure_id)).fetchone()["c"]
        manifest = build_manifest(
            procedure_id=procedure_id, procedure_version="v1",
            engine_version=_engine_version(procedure_id), tables=tables,
            policies=effective_policies, rerun_sequence=rerun_sequence)
        if not_runnable:
            def refuse(*_args):
                raise ValueError(not_runnable)
            bundle = run_job(manifest, tables, refuse)
        else:
            bundle = run_job(manifest, tables, execute_procedure)

        def handler(uow):
            run_id = uow.runs.record(
                engagement_id, procedure_id=procedure_id,
                job_id=manifest.job_id,
                manifest={"input_tables": manifest.input_tables,
                          "policies": manifest.policies,
                          "engine_version": manifest.engine_version,
                          "datasets": datasets_read},
                status=bundle.status, summary=bundle.summary,
                findings=list(bundle.findings), error=bundle.error,
                result_digest=bundle.result_digest)
            return {"run_id": run_id, "job_id": manifest.job_id,
                    "status": bundle.status, "summary": bundle.summary,
                    "findings": len(bundle.findings), "error": bundle.error}
        return run_command(
            self._conn, self._command(actor, "run.execute", engagement_id),
            handler).result

    def review_run(self, actor: str, engagement_id: str, run_id: str, *,
                   target: str, expected_version: int) -> dict:
        role_needed = "reviewer" if target == "reviewed" else "partner"
        self._require_unlocked(engagement_id)

        def handler(uow):
            if role_needed not in uow.principals.roles_for(engagement_id, actor):
                raise AuthorizationError(f"{target} requires a {role_needed}")
            version = uow.runs.advance_review(
                run_id, target, expected_version=expected_version)
            return {"run_id": run_id, "status": target, "version": version}
        return run_command(
            self._conn, self._command(actor, f"run.{target}", engagement_id),
            handler).result

    def runs(self, engagement_id: str) -> list[dict]:
        rows = self._conn.execute(
            """SELECT run_id, procedure_id, job_id, status, summary, error,
               executed_by, reviewed_by, approved_by, version, created_at
               FROM procedure_run WHERE engagement_id = ?
               ORDER BY created_at, rowid""", (engagement_id,)).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["summary"] = json.loads(item["summary"])
            out.append(item)
        return out

    def findings(self, engagement_id: str) -> list[dict]:
        dispositions = {
            row["finding_uid"]: {"status": row["status"], "note": row["note"],
                                 "version": row["version"],
                                 "proposed_by": row["proposed_by"],
                                 "concurred_by": row["concurred_by"]}
            for row in self._conn.execute(
                "SELECT * FROM disposition WHERE engagement_id = ?",
                (engagement_id,))}
        document, _ = self.workflow_document(engagement_id)
        clearly_trivial = _trivial_rate(document) * (
            Decimal(str(document["materiality"].get("amount") or 0)))
        out = []
        for run in self._conn.execute(
                """SELECT run_id, procedure_id, status, findings
                   FROM procedure_run WHERE engagement_id = ?
                   ORDER BY created_at, rowid""", (engagement_id,)):
            if run["status"] == "error":
                continue
            for verdict in json.loads(run["findings"]):
                uid = _finding_uid(verdict)
                disposition = dispositions.get(
                    uid, {"status": "undisposed", "note": "", "version": 0,
                          "proposed_by": "", "concurred_by": ""})
                needs = requires_concurrence(
                    {"score": verdict.get("score"),
                     "evidence": verdict.get("evidence", {}),
                     "verdict": verdict["verdict"]}, clearly_trivial)
                out.append({
                    "finding_uid": uid,
                    "run_id": run["run_id"],
                    "procedure_id": run["procedure_id"],
                    "verdict": verdict,
                    "tags": _tags(verdict),
                    "disposition": disposition,
                    "requires_concurrence": needs,
                    "awaiting_concurrence": (
                        needs
                        and disposition["status"] not in ("undisposed",
                                                          "follow_up")
                        and not disposition["concurred_by"]),
                })
        return out

    def set_disposition(self, actor: str, engagement_id: str, *,
                        finding_uid: str, status: str, note: str = "",
                        expected_version: int = 0) -> dict:
        self._require_unlocked(engagement_id)
        # Validate before the write: the table's CHECK constraint would
        # refuse anyway, but as an IntegrityError that the repository
        # relabels as a version conflict — a misleading message for what
        # is a bad field value (review F1).
        if status not in _DISPOSITION_STATUSES:
            raise ValueError(
                f"unknown disposition status {status!r}; expected one of "
                f"{list(_DISPOSITION_STATUSES)}")

        def handler(uow):
            roles = uow.principals.roles_for(engagement_id, actor)
            if not roles & {"preparer", "reviewer", "partner"}:
                raise AuthorizationError("dispositions require a team role")
            version = uow.dispositions.set(
                engagement_id, finding_uid, status, note=note,
                expected_version=expected_version, proposed_by=actor)
            return {"finding_uid": finding_uid, "status": status,
                    "version": version}
        return run_command(
            self._conn,
            self._command(actor, "disposition.set", engagement_id),
            handler).result

    def concur_disposition(self, actor: str, engagement_id: str, *,
                           finding_uid: str, expected_version: int) -> dict:
        """A reviewer (or partner) concurs with a proposed disposition.

        Mirrors the run-review lifecycle: the proposer's judgment stands
        alone below the clearly-trivial threshold, but above it the record
        shows who judged and who concurred — and the two must differ.
        """
        self._require_unlocked(engagement_id)

        def handler(uow):
            roles = uow.principals.roles_for(engagement_id, actor)
            if not roles & {"reviewer", "partner"}:
                raise AuthorizationError(
                    "disposition concurrence requires a reviewer or partner")
            version = uow.dispositions.concur(
                engagement_id, finding_uid, concurred_by=actor,
                expected_version=expected_version)
            return {"finding_uid": finding_uid, "concurred_by": actor,
                    "version": version}
        return run_command(
            self._conn,
            self._command(actor, "disposition.concur", engagement_id),
            handler).result

    # ----------------------------- screen 4c: revised evidence and its reach

    def revision_impact(self, engagement_id: str) -> dict:
        """What a newer client file touches: runs, findings, judgments, SAD.

        Read-only. Compares each role's newest dataset with the one before it,
        finds the latest run of every procedure whose *required* inputs no
        longer match the current data, and reperforms those procedures in
        memory to show which findings appear, disappear, or move. Nothing is
        recorded; rerunning and re-judging stay the team's journaled actions.
        """
        from assurance_domain.jobs import table_digest
        from procedures_ap.contracts import PROCEDURES
        from assurance_application.impact import (
            KEY_FIELDS, compare_findings, diff_records, sad_effect,
            thresholds,
        )
        from assurance_domain.money import fnum

        document, _ = self.workflow_document(engagement_id)
        limits = thresholds(document["materiality"].get("amount") or 0,
                            _trivial_rate(document))
        current = self._tables(engagement_id)
        current_records = {role: list(t.engine_view().records)
                           for role, t in current.items()}
        current_digest = {role: table_digest(records)
                          for role, records in current_records.items()}

        revisions = []
        for role, states in sorted(self._role_states(engagement_id).items()):
            if len(states) < 2:
                continue
            # What the procedures read before the latest load, against what
            # they read now: a replacement and an addition both change it.
            (_, before_set), (latest, after_set) = states[-2], states[-1]
            previous = before_set[-1]
            old_table = _combine([self._verified_table(d) for d in before_set])
            revisions.append({
                "role": role,
                "versions": len(states),
                "load_mode": latest["load_mode"],
                "before": {"dataset_id": previous["dataset_id"],
                           "file": self._dataset_file(previous),
                           "files": [self._dataset_file(d) for d in before_set],
                           "loaded_at": previous["created_at"]},
                "after": {"dataset_id": latest["dataset_id"],
                          "file": self._dataset_file(latest),
                          "files": [self._dataset_file(d) for d in after_set],
                          "loaded_at": latest["created_at"]},
                "diff": diff_records(
                    list(old_table.engine_view().records),
                    current_records.get(role, []),
                    KEY_FIELDS.get(role, ()), limits, role),
            })

        needs = {p.procedure_id: set(p.required_fields)
                 for p in PROCEDURES + tuple(CYCLE_CONTRACTS_BY_ID.values())}
        latest_runs: dict[str, sqlite3.Row] = {}
        for run in self._conn.execute(
                """SELECT * FROM procedure_run WHERE engagement_id = ?
                   ORDER BY created_at, rowid""", (engagement_id,)):
            latest_runs[run["procedure_id"]] = run
        dispositions = {
            row["finding_uid"]: {"status": row["status"],
                                 "concurred_by": row["concurred_by"]}
            for row in self._conn.execute(
                "SELECT finding_uid, status, concurred_by FROM disposition "
                "WHERE engagement_id = ?", (engagement_id,))}
        effective_policies = document.get("policies") or {}

        runs_out, cards = [], []
        for procedure_id, run in sorted(latest_runs.items()):
            manifest = json.loads(run["manifest"])
            inputs = manifest.get("input_tables", {})
            changed_roles = sorted(
                role for role in needs.get(procedure_id, set(inputs))
                if inputs.get(role, {}).get("sha256")
                != current_digest.get(role))
            if not changed_roles:
                continue
            rerun = run_job(
                build_manifest(
                    procedure_id=procedure_id, procedure_version="v1",
                    engine_version=_engine_version(procedure_id),
                    tables=current_records,
                    policies={**effective_policies,
                              **(manifest.get("policies") or {})}),
                current_records, execute_procedure)
            old = {_finding_uid(v): v for v in json.loads(run["findings"])}
            new = {_finding_uid(v): v for v in rerun.findings}
            run_cards = compare_findings(old, new, dispositions, limits)
            for card in run_cards:
                card["procedure_id"] = procedure_id
                card["run_id"] = run["run_id"]
            cards.extend(run_cards)
            runs_out.append({
                "run_id": run["run_id"], "procedure_id": procedure_id,
                "status": run["status"],
                "changed_inputs": changed_roles,
                "findings_before": len(old), "findings_after": len(new),
                "rerun_error": rerun.error,
                "action": ("rerun, then re-review and re-approve"
                           if run["status"] in ("reviewed", "approved")
                           else "rerun"),
            })

        actions: dict[str, int] = {}
        for card in cards:
            actions[card["action"]] = actions.get(card["action"], 0) + 1
        return {
            "engagement_id": engagement_id,
            "thresholds": {key: fnum(value) for key, value in limits.items()},
            "revisions": revisions,
            "stale_runs": runs_out,
            "cards": cards,
            "summary": {
                "revised_files": len(revisions),
                "stale_runs": len(runs_out),
                "affected_findings": len(cards),
                "judgments_to_revisit": sum(
                    1 for card in cards if card["action"] in
                    ("revisit_disposition", "reassess_disposition")),
                "new_findings": sum(1 for card in cards
                                    if card["change"] == "new_after_revision"),
                "actions": actions,
                "significance": max(
                    [card["significance"] for card in cards]
                    + [rev["diff"]["significance"] for rev in revisions],
                    key=("none", "below_trivial", "not_measured", "above_trivial",
                         "above_performance").index, default="none"),
                "sad_effect": sad_effect(cards),
            },
            "limits": ("An impact report compares recorded data and reperforms "
                       "procedures in memory. It changes nothing, concludes "
                       "nothing about misstatement, and covers only procedures "
                       "that have been run at least once."),
        }

    # ------------------------------------ screen 4b: risk assessment register

    def assess_risk(self, actor: str, engagement_id: str, *,
                    risk_id: str | None = None, title: str, assertion: str,
                    level: str = "unassessed", rationale: str = "",
                    response: str = "", expected_version: int = 0,
                    fraud: bool | None = None) -> dict:
        """Record (or re-assess) a risk at the assertion level.

        ``fraud`` left out (None) keeps a re-assessed risk's flag as it was
        (a new risk starts unflagged); a value that is not true/false is
        refused rather than guessed.

        The judgment is the auditor's: this stores it, names the proposer, and
        voids any prior concurrence on a re-assessment. It computes nothing —
        the engine never grades a risk.
        """
        from procedures_ap.contracts import RISK_LEVELS
        from procedures_cycles.contracts import REGISTER_ASSERTIONS as ASSERTIONS
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer", "reviewer", "partner")
        if assertion not in ASSERTIONS:
            raise ValueError(
                f"unknown assertion {assertion!r}; one of {sorted(ASSERTIONS)}")
        if level not in RISK_LEVELS:
            raise ValueError(
                f"unknown risk level {level!r}; one of {list(RISK_LEVELS)}")
        if fraud is not None and not isinstance(fraud, bool):
            raise ValueError("fraud must be true or false")
        if fraud is None:
            row = self._conn.execute(
                "SELECT fraud FROM risk_assessment WHERE engagement_id = ? "
                "AND risk_id = ?", (engagement_id, risk_id)).fetchone()                 if risk_id else None
            fraud = bool(row["fraud"]) if row else False
        rid = risk_id or new_id()

        def handler(uow):
            version = uow.risks.assess(
                engagement_id, rid, title=title, assertion=assertion,
                level=level, rationale=rationale, response=response,
                expected_version=expected_version, proposed_by=actor,
                fraud=fraud)
            return {"risk_id": rid, "version": version}
        return run_command(
            self._conn, self._command(actor, "risk.assess", engagement_id),
            handler).result

    def link_risk_procedures(self, actor: str, engagement_id: str, *,
                             risk_id: str, procedure_ids: list[str],
                             expected_version: int) -> dict:
        """Link the procedures that respond to a risk (the audit response)."""
        from procedures_ap.contracts import CONTRACTS_BY_ID
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer", "reviewer", "partner")
        document, _ = self.workflow_document(engagement_id)
        allowed = {contract.procedure_id for contract in self._contracts(document)}
        known = set(CONTRACTS_BY_ID) | set(CYCLE_CONTRACTS_BY_ID)
        unknown = [p for p in procedure_ids if p not in known]
        if unknown:
            raise ValueError(f"unknown procedure(s): {unknown}")
        out_of_scope = [p for p in procedure_ids if p not in allowed]
        if out_of_scope:
            raise ValueError(f"out-of-scope procedure(s): {out_of_scope}")

        def handler(uow):
            version = uow.risks.link_procedures(
                engagement_id, risk_id, procedure_ids=procedure_ids,
                expected_version=expected_version)
            return {"risk_id": risk_id, "version": version}
        return run_command(
            self._conn,
            self._command(actor, "risk.link_procedures", engagement_id),
            handler).result

    def concur_risk(self, actor: str, engagement_id: str, *, risk_id: str,
                    expected_version: int) -> dict:
        """A reviewer or partner concurs with a proposed risk assessment —
        and must not be the principal who proposed it (AU-C 315/220)."""
        self._require_unlocked(engagement_id)

        def handler(uow):
            roles = uow.principals.roles_for(engagement_id, actor)
            if not roles & {"reviewer", "partner"}:
                raise AuthorizationError(
                    "risk concurrence requires a reviewer or partner")
            version = uow.risks.concur(
                engagement_id, risk_id, concurred_by=actor,
                expected_version=expected_version)
            return {"risk_id": risk_id, "concurred_by": actor,
                    "version": version}
        return run_command(
            self._conn, self._command(actor, "risk.concur", engagement_id),
            handler).result

    def archive_risk(self, actor: str, engagement_id: str, *, risk_id: str,
                     expected_version: int) -> dict:
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer", "reviewer", "partner")

        def handler(uow):
            version = uow.risks.archive(
                engagement_id, risk_id, expected_version=expected_version)
            return {"risk_id": risk_id, "archived": True, "version": version}
        return run_command(
            self._conn, self._command(actor, "risk.archive", engagement_id),
            handler).result

    def risks(self, engagement_id: str) -> dict:
        """The risk register for screen 4b: each risk with its response
        linkage and concurrence state, plus the procedures that *could*
        respond to each assertion (candidates), so the UI can suggest."""
        from procedures_ap.contracts import RISK_LEVELS
        from procedures_cycles.contracts import REGISTER_ASSERTIONS as ASSERTIONS
        document, _ = self.workflow_document(engagement_id)
        contracts = self._contracts(document)
        rows = []
        for r in self._risk_records(engagement_id):
            requires = r["level"] in ("high", "significant")
            rows.append({
                "risk_id": r["risk_id"],
                "title": r["title"],
                "assertion": r["assertion"],
                "level": r["level"],
                "fraud": bool(r.get("fraud")),
                "rationale": r["rationale"],
                "response": r["response"],
                "procedure_ids": r["procedure_ids"],
                "candidate_procedures": [
                    contract.procedure_id for contract in contracts
                    if r["assertion"] in contract.assertions
                ],
                "proposed_by": r["proposed_by"],
                "concurred_by": r["concurred_by"],
                "version": r["version"],
                "requires_concurrence": requires,
                "awaiting_concurrence": bool(
                    requires and r["proposed_by"] and r["response"]
                    and r["procedure_ids"] and not r["concurred_by"]),
            })
        return {"risks": rows, "assertions": list(ASSERTIONS),
                "levels": list(RISK_LEVELS)}

    def fraud_view(self, engagement_id: str) -> dict:
        """AU-C 240 in one place: the fraud tests, the fraud risks, and what
        the tests found. It gathers; it concludes nothing. Every test says
        whether it could run on these records, so a scheme nobody could test
        shows as untested, never as clean."""
        coverage = {row["procedure_id"]: row
                    for row in self.coverage(engagement_id)["procedures"]}
        latest, current = {}, {}
        for run in self.runs(engagement_id):
            latest[run["procedure_id"]] = run
            if run["status"] != "error":
                current[run["procedure_id"]] = run["run_id"]
        # Only the latest completed run's findings: an older run's findings
        # are superseded by the rerun, never counted twice.
        findings = [f for f in self.findings(engagement_id)
                    if f["procedure_id"] in FRAUD_TESTS
                    and f["run_id"] == current.get(f["procedure_id"])
                    and f["verdict"]["verdict"] != "AGREE"]
        tests = []
        for pid, (scheme, basis) in FRAUD_TESTS.items():
            row = coverage.get(pid)
            mine = [f for f in findings if f["procedure_id"] == pid]
            run = latest.get(pid)
            missing = []
            if row:
                missing = list(row.get("missing_roles") or []) + sorted(
                    f"{role}.{field}"
                    for role, fields in (row.get("missing_fields") or {}).items()
                    for field in fields)
            tests.append({
                "procedure_id": pid, "scheme": scheme, "basis": basis,
                "name": row["name"] if row else pid,
                "coverage": row["status"] if row else "not_available",
                "in_scope": bool(row and row.get("selected")),
                "missing": missing,
                "limitations": (row.get("limitations") or "") if row else "",
                "last_run": ({"status": run["status"], "at": run["created_at"],
                              "run_id": run["run_id"]} if run else None),
                "findings": len(mine),
                "open": sum(1 for f in mine
                            if f["disposition"]["status"] in ("undisposed", "follow_up")),
            })
        risks = [r for r in self.risks(engagement_id)["risks"] if r["fraud"]]
        return {
            "tests": tests,
            "risks": risks,
            "findings": findings,
            "summary": {
                "tests": len(tests),
                # a run that ended in error ran nothing: not counted as run
                "run": sum(1 for t in tests if t["last_run"]
                           and t["last_run"]["status"] != "error"),
                "cannot_run": sum(1 for t in tests if t["coverage"]
                                  in ("blocked", "unsupported", "not_available")),
                "partly": sum(1 for t in tests if t["coverage"] == "partial"),
                "findings": len(findings),
                "open_findings": sum(t["open"] for t in tests),
                "fraud_risks": len(risks),
            },
            "presumed_risks": [
                "Revenue recognition is presumed a fraud risk (AU-C 240.26): record it, "
                "or document why the presumption is rebutted.",
                "Management override of controls is a fraud risk in every audit "
                "(AU-C 240.31): journal entry testing responds to it.",
            ],
        }

    def _risk_records(self, engagement_id: str) -> list[dict]:
        """Active (non-archived) risks, procedure_ids decoded to a list."""
        out = []
        for row in self._conn.execute(
                "SELECT * FROM risk_assessment WHERE engagement_id = ? "
                "AND archived = 0 ORDER BY updated_at, risk_id",
                (engagement_id,)):
            item = dict(row)
            item["procedure_ids"] = json.loads(item["procedure_ids"] or "[]")
            out.append(item)
        return out

    # ------------------------------- screen 5: SAD, workflow, readiness

    def workflow_document(self, engagement_id: str) -> tuple[dict, int]:
        row = self._conn.execute(
            "SELECT payload, version FROM workflow_state WHERE engagement_id = ?",
            (engagement_id,)).fetchone()
        if row is None:
            info = self._engagement(engagement_id)
            return blank_engagement({"company": info["client_name"],
                                     "fye": info["period_end"]}), 0
        return json.loads(row["payload"]), row["version"]

    def update_workflow(self, actor: str, engagement_id: str,
                        section: str, values: dict) -> dict:
        """Constrained workflow updates: materiality, stages, completion."""
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer", "partner")
        document, version = self.workflow_document(engagement_id)
        if section == "materiality":
            # Given a benchmark amount and a percentage, the amount is their
            # product (to the cent); a stated amount that disagrees is refused
            # rather than silently replaced.
            amount = values.get("amount", 0)
            benchmark_amount = values.get("benchmark_amount")
            percentage = values.get("percentage")
            given = [v not in (None, "") for v in (benchmark_amount, percentage)]
            if any(given) and not all(given):
                raise ValueError("give both the benchmark amount and the "
                                 "percentage, or neither")
            if all(given):
                try:
                    base = Decimal(str(benchmark_amount))
                    rate = Decimal(str(percentage))
                except ArithmeticError:
                    raise ValueError("benchmark amount and percentage must be "
                                     "numbers") from None
                if not (base.is_finite() and rate.is_finite()):
                    raise ValueError("benchmark amount and percentage must be "
                                     "numbers")
                if base <= 0 or not Decimal("0") < rate <= Decimal("100"):
                    raise ValueError("the benchmark amount must be above zero and "
                                     "the percentage between 0 and 100")
                try:
                    computed = (base * rate / 100).quantize(Decimal("0.01"),
                                                            rounding=ROUND_HALF_UP)
                except ArithmeticError:
                    raise ValueError("the benchmark amount is too large") from None
                if amount not in (None, "", 0) and \
                        Decimal(str(amount)).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP) != computed:
                    raise ValueError(
                        f"materiality {amount} is not {rate}% of {base} "
                        f"({computed})")
                amount = computed
            document["materiality"].update({
                "amount": float(amount or 0),
                "basis": str(values.get("basis", "")),
                "benchmark_amount": str(benchmark_amount) if all(given) else "",
                "percentage": str(percentage) if all(given) else "",
                "rationale": str(values.get("rationale", ""))})
        elif section == "stage":
            name = values["name"]
            if name not in document["stages"]:
                raise ValueError(f"unknown stage {name!r}")
            document["stages"][name] = {
                "status": str(values.get("status", "not_started")),
                "note": str(values.get("note", ""))}
        elif section == "completion":
            name = values["name"]
            if name not in document["completion"]:
                raise ValueError(f"unknown completion check {name!r}")
            document["completion"][name] = {
                "done": bool(values.get("done", False)),
                "note": str(values.get("note", "")),
                "evidence": list(values.get("evidence", []))}
        elif section == "line_mapping":
            # The client's own trial-balance label (or one account) mapped to
            # a statement line the procedures read (K8). The preparer or the
            # partner sets it; it reaches every run as a recorded policy.
            self._require(engagement_id, actor, "preparer", "partner")
            from procedures_cycles.common import key_text as _key
            from procedures_cycles.statements import LINES
            label = " ".join(str(values.get("label") or "").split()).lower()
            account = _key(values.get("account")) if values.get("account") else ""
            if bool(label) == bool(account):
                raise ValueError("map either a label or one account, not both")
            key = f"account:{account}" if account else f"label:{label}"
            line = str(values.get("line") or "").strip()
            mapping = document.setdefault("line_mapping", {})
            if not line:
                mapping.pop(key, None)
            elif line not in LINES:
                raise ValueError(f"unknown statement line {line!r}; one of {list(LINES)}")
            else:
                mapping[key] = line
        elif section == "opinion_decision":
            # A judgment the draft opinion asks for (pervasiveness, the
            # going-concern conclusion). The partner's alone; kept, with who
            # and why, in the signed engagement record.
            self._require(engagement_id, actor, "partner")
            from assurance_domain.opinion import DECISION_ANSWERS
            decision = str(values.get("decision") or "")
            answer = str(values.get("answer") or "")
            note = " ".join(str(values.get("note") or "").split())
            if decision not in DECISION_ANSWERS:
                raise ValueError(f"unknown decision {decision!r}; one of "
                                 f"{sorted(DECISION_ANSWERS)}")
            if answer not in DECISION_ANSWERS[decision]:
                raise ValueError(f"{decision} takes one of "
                                 f"{list(DECISION_ANSWERS[decision])}, not {answer!r}")
            if len(note) < 10:
                raise ValueError("record the reason for the decision (ten characters "
                                 "or more); it becomes part of the signed record")
            document.setdefault("opinion_decisions", {})[decision] = {
                "answer": answer, "note": note, "decided_by": actor}
        elif section == "period":
            # The period's first day, when it is not the twelve months ending at
            # period end (a first year, a changed year end). The partner owns it.
            self._require(engagement_id, actor, "partner")
            from datetime import date as _date
            info = self._engagement(engagement_id)
            end = _date.fromisoformat(str(info["period_end"])[:10])
            raw = str(values.get("start") or "").strip()
            if raw:
                try:
                    # Exactly YYYY-MM-DD: trailing text is refused, not truncated.
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
                        raise ValueError
                    start = _date.fromisoformat(raw)
                except ValueError:
                    raise ValueError(f"period start {raw!r} is not a date "
                                     "(YYYY-MM-DD)") from None
                if not start < end:
                    raise ValueError(f"period start {start} must be before the period "
                                     f"end {end}")
                if (end - start).days > 731:
                    raise ValueError(f"period start {start} is more than 24 months "
                                     f"before the period end {end}")
                document["period"] = {"start": start.isoformat()}
            else:
                document.pop("period", None)
        elif section == "cycles":
            # Which cycles this engagement audits. The partner owns this; it
            # decides which cycle contracts coverage (and readiness) consider.
            # (Kept apart from document["scope"], which holds scope-limitation
            # decisions.)
            self._require(engagement_id, actor, "partner")
            cycles = [str(c) for c in values.get("cycles", [])]
            unknown = [c for c in cycles if c not in SCOPES]
            if unknown:
                raise ValueError(f"unknown scope(s) {unknown}; one of {list(SCOPES)}")
            proposed = set(cycles)
            removed_procedures = {
                pid for pid, scope in SCOPE_OF.items()
                if scope not in proposed
            }
            linked = sorted({
                pid for risk in self._risk_records(engagement_id)
                for pid in risk["procedure_ids"] if pid in removed_procedures
            })
            if linked:
                raise ValueError(
                    "cannot remove cycles while active risks link their procedures: "
                    f"{linked}")
            run_rows = self._conn.execute(
                "SELECT DISTINCT procedure_id FROM procedure_run "
                "WHERE engagement_id = ?", (engagement_id,)).fetchall()
            executed = sorted(
                row["procedure_id"] for row in run_rows
                if row["procedure_id"] in removed_procedures
            )
            if executed:
                raise ValueError(
                    "cannot remove cycles after their procedures have run: "
                    f"{executed}")
            # Settings and procedure choices owned only by a cycle leaving
            # scope are retired, not kept: kept, they would come back into
            # force unreviewed if the cycle were switched on again. The
            # retired list stays in the signed record.
            from procedures_ap.contracts import OPTIONAL_POLICIES, PROCEDURES
            from procedures_cycles.contracts import policy_scopes
            payables_policies = {p for c in PROCEDURES for p in c.required_policies}
            payables_policies.update(OPTIONAL_POLICIES)
            retired = document.setdefault("retired", [])
            policies = document.get("policies") or {}
            for name in sorted(policies):
                owners = policy_scopes(name)
                if owners and not owners & proposed and name not in payables_policies:
                    retired.append({"kind": "policy", "name": name,
                                    "value": policies.pop(name),
                                    "cycles": sorted(owners), "retired_by": actor})
            selections = document.get("procedures") or {}
            for pid in sorted(selections):
                if pid in CYCLE_CONTRACTS_BY_ID and pid in removed_procedures:
                    retired.append({"kind": "procedure_selection", "name": pid,
                                    "value": selections.pop(pid),
                                    "cycles": [SCOPE_OF[pid]], "retired_by": actor})
            if not retired:
                del document["retired"]
            document["cycles"] = sorted(set(cycles))
        elif section == "procedure_selection":
            from procedures_ap.contracts import CONTRACTS_BY_ID
            procedure_id = str(values["procedure_id"])
            if procedure_id not in CONTRACTS_BY_ID                     and procedure_id not in CYCLE_CONTRACTS_BY_ID:
                raise ValueError(f"unknown procedure {procedure_id!r}")
            if procedure_id in CYCLE_CONTRACTS_BY_ID and                     SCOPE_OF[procedure_id] not in (document.get("cycles") or []):
                raise ValueError(
                    f"{procedure_id} belongs to the "
                    f"{SCOPE_OF[procedure_id]!r} cycle, which is not in scope")
            # Leaving a procedure out is a scope decision: the partner's, and
            # never without the reason that goes into the signed record.
            self._require(engagement_id, actor, "partner")
            selected = bool(values.get("selected", True))
            rationale = " ".join(str(values.get("rationale", "")).split())
            if not selected and len(rationale) < 10:
                raise ValueError(
                    f"say why {procedure_id} is left out (ten characters or "
                    "more); the reason becomes part of the signed record")
            document.setdefault("procedures", {})[procedure_id] = {
                "selected": selected, "rationale": rationale,
                "decided_by": actor}
        elif section == "no_data_assertion":
            # Tracker 3.4: an engagement with zero normalized datasets skips
            # every procedure gate, so a lock could silently attest to no
            # substantive work. The silence must be owned — by the partner,
            # on the record, with a reason that enters the signed manifest
            # (the workflow payload hash covers it).
            self._require(engagement_id, actor, "partner")
            asserted = bool(values.get("asserted", False))
            reason = " ".join(str(values.get("reason", "")).split())
            if asserted and len(reason) < 10:
                raise ValueError(
                    "asserting that no data-dependent procedures apply "
                    "requires a specific reason (ten characters or more); "
                    "it becomes part of the signed engagement record")
            document["no_data_assertion"] = {
                "asserted": asserted, "reason": reason, "asserted_by": actor}
        elif section == "policy":
            from procedures_ap.contracts import OPTIONAL_POLICIES, PROCEDURES
            name = str(values["name"])
            known = {policy for contract in PROCEDURES
                     for policy in contract.required_policies}
            known.update(OPTIONAL_POLICIES)
            from procedures_cycles.contracts import (
                CYCLE_PROCEDURES, OPTIONAL_POLICIES as CYCLE_OPTIONAL,
            )
            known.update(policy for contract in CYCLE_PROCEDURES
                         for policy in contract.required_policies)
            known.update(CYCLE_OPTIONAL)
            if name in ENGAGEMENT_POLICIES:
                raise ValueError(
                    f"{name!r} comes from the engagement record (period end, period "
                    "section, materiality section); it is not set as a policy")
            if name not in known:
                raise ValueError(f"unknown policy {name!r}")
            from procedures_cycles.contracts import policy_scopes
            owners = policy_scopes(name)
            if owners and not owners & set(document.get("cycles") or [])                     and name not in {p for c in PROCEDURES
                                     for p in c.required_policies}                     and name not in OPTIONAL_POLICIES:
                raise ValueError(
                    f"{name!r} is used only by the {sorted(owners)} cycle(s), none of "
                    "which is in scope")
            if name == "ar_allowance_rates":  # checked now, not at run time
                from procedures_cycles.common import PolicyError
                from procedures_cycles.receivables import parse_allowance_rates
                try:
                    parse_allowance_rates(str(values["value"]))
                except PolicyError as exc:
                    raise ValueError(str(exc)) from exc
            if name == "clearly_trivial_pct":  # checked now, not when the SAD is read
                trivial_rate(values["value"])
            if name == "misstatement_likely_basis":
                from procedures_cycles.statements import LIKELY_BASES
                if str(values["value"]).strip().lower() not in LIKELY_BASES:
                    raise ValueError("misstatement_likely_basis must be 'total' or "
                                     "'beyond_identified'")
            document.setdefault("policies", {})[name] = str(values["value"])
        else:
            raise ValueError(f"unknown workflow section {section!r}")

        def handler(uow):
            new_version = uow.workflows.put(engagement_id, document,
                                            expected_version=version)
            return {"version": new_version, "section": section}
        return run_command(
            self._conn,
            self._command(actor, "workflow.update", engagement_id),
            handler).result

    def sad(self, engagement_id: str, *, materiality: float | None = None) -> dict:
        info = self._engagement(engagement_id)
        document, _ = self.workflow_document(engagement_id)
        if materiality is None:
            materiality = float(document["materiality"].get("amount") or 0)
        dispositions = {
            row["finding_uid"]: row
            for row in self._conn.execute(
                "SELECT finding_uid, status, concurred_by FROM disposition "
                "WHERE engagement_id = ?", (engagement_id,))}
        rows = []
        for item in self.findings(engagement_id):
            verdict = item["verdict"]
            uid = item["finding_uid"]
            record = dispositions.get(uid)
            # B2: the schedule's "a line reaches materiality" is an evaluation
            # of misstatements already listed, not one more misstatement; as
            # a candidate it would be counted a second time.
            evaluation = (item["procedure_id"] == SCHEDULE_PROCEDURE
                          and list(verdict["key"])[1:2] == ["material"])
            rows.append({
                **({"audit_class": "evaluation"} if evaluation else {}),
                "engagement": info["client_name"],
                "finding_uid": uid,
                "domain": verdict["domain"],
                "key": verdict["key"],
                "verdict": verdict["verdict"],
                "score": verdict.get("score"),
                "reason": verdict.get("reason", ""),
                "evidence": verdict.get("evidence", {}),
                "disposition": record["status"] if record else "undisposed",
                "disposition_concurred": bool(record["concurred_by"])
                if record else False,
            })
        summary = summary_of_differences(rows, materiality=materiality,
                                         trivial_pct=_trivial_rate(document))
        # Above-trivial dispositions are proposals until concurred (AU-C
        # 220); the SAD refuses to conclude over unreviewed judgments. The
        # domain summary keeps its golden-tested shape — these keys ride on
        # top, and readiness turns the count into a lock blocker.
        pending = sorted({
            row["finding_uid"] for row in rows
            if row["disposition"] not in ("undisposed", "follow_up")
            and not row["disposition_concurred"]
            and requires_concurrence(row, summary["clearly_trivial"])})
        summary["concurrence_pending"] = pending
        # Findings that are not dollar misstatements (leads, refusals-to-
        # evaluate, control deviations) never reach the SAD, but they still
        # need a decision: one left undisposed, or marked follow-up, is an
        # open question and must not ride silently into a signed lock.
        from assurance_domain.sad import _is_candidate
        open_findings = sorted({
            row["finding_uid"] for row in rows
            if row["verdict"] != "AGREE" and not _is_candidate(row)
            and row["disposition"] in ("undisposed", "follow_up")})
        summary["open_findings"] = open_findings
        summary["open_findings_count"] = len(open_findings)
        summary["concurrence_pending_count"] = len(pending)
        # B2: one summary. The misstatement schedule, once evaluated by
        # completion.uncorrected_misstatements, is the signed, projected,
        # by-statement-line view; it rides on the SAD, and the SAD cannot
        # conclude "immaterial" while a line there reaches materiality.
        schedule = self._misstatement_schedule(engagement_id)
        summary["schedule"] = schedule
        if schedule and schedule["material_lines"] and summary["conclusion"] == "immaterial":
            summary["conclusion"] = "material"
        if pending:
            summary["conclusion"] = None
        return summary

    def _misstatement_schedule(self, engagement_id: str) -> dict | None:
        """The latest completed evaluation of the misstatement schedule."""
        row = self._conn.execute(
            """SELECT run_id, summary FROM procedure_run
               WHERE engagement_id = ? AND procedure_id = ? AND status = 'completed'
               ORDER BY created_at DESC, rowid DESC LIMIT 1""",
            (engagement_id, SCHEDULE_PROCEDURE)).fetchone()
        if row is None:
            return None
        stats = json.loads(row["summary"])
        totals = stats.get("totals") or {}
        materiality = Decimal(str(stats.get("materiality") or 0))
        lines = {k: v for k, v in totals.items() if k not in ("identified", "likely")}
        material = sorted(k for k, v in lines.items()
                          if materiality and abs(Decimal(str(v))) >= materiality)
        return {"run_id": row["run_id"], "materiality": str(materiality),
                "lines": lines, "identified": totals.get("identified"),
                "likely": totals.get("likely"),
                "likely_basis": stats.get("likely_basis"),
                "material_lines": material,
                "note": "signed effect by statement line, projections included; the "
                        "SAD's items above are findings disposed as unadjusted, as "
                        "unsigned amounts, and belong on this schedule"}

    def trial_balance_lines(self, engagement_id: str) -> dict:
        """Each label on the loaded trial balance, whether Noesi recognizes it,
        how it is mapped, and a suggestion — for the line-mapping screen."""
        from procedures_cycles.statements import LINES, suggest_line
        document, _ = self.workflow_document(engagement_id)
        mapping = document.get("line_mapping") or {}
        table = self._tables(engagement_id).get("Trial_balance")
        labels: dict[str, dict] = {}
        for row in (table.records if table else []):
            label = " ".join(str(row.get("line") or "").split())
            item = labels.setdefault(label.lower(), {
                "label": label, "accounts": [],
                "recognized": label.lower() in LINES,
                "mapped_to": mapping.get(f"label:{label.lower()}"),
                "suggestion": suggest_line(label)})
            item["accounts"].append(str(row.get("account") or ""))
        overrides = {k[len("account:"):]: v for k, v in mapping.items()
                     if k.startswith("account:")}
        return {"lines": list(LINES), "labels": sorted(labels.values(),
                                                        key=lambda i: i["label"]),
                "account_overrides": overrides, "has_trial_balance": table is not None}

    def cycle_catalog(self) -> dict:
        """The audit areas a partner can switch on, each with its procedures
        and the policies they need (required) or can use (optional); read by
        the Scope & Policies screen so it is never hand-maintained."""
        from procedures_cycles.contracts import (
            CYCLE_PROCEDURES, OPTIONAL_POLICIES as CYCLE_OPTIONAL, policy_scopes,
        )
        areas = []
        for scope in SCOPES:
            contracts = [c for c in CYCLE_PROCEDURES if SCOPE_OF[c.procedure_id] == scope]
            required = sorted({p for c in contracts for p in c.required_policies
                               if p not in ENGAGEMENT_POLICIES})
            optional = sorted(p for p in CYCLE_OPTIONAL
                              if scope in policy_scopes(p) and p not in required
                              and p not in ENGAGEMENT_POLICIES)
            areas.append({
                "scope": scope,
                "procedures": [{"procedure_id": c.procedure_id, "title": c.name,
                                "required_policies": [p for p in c.required_policies
                                                      if p not in ENGAGEMENT_POLICIES]}
                               for c in contracts],
                "required_policies": required, "optional_policies": optional})
        # Settings that belong to no one area (e.g. the firm's clearly-trivial
        # rate, used by the SAD whatever is in scope).
        return {"areas": areas, "engagement_policies": list(ENGAGEMENT_POLICIES),
                "general_policies": ["clearly_trivial_pct"]}

    def draft_opinion(self, engagement_id: str) -> dict:
        """The opinion the evidence points to, with its basis and the
        judgments the partner must still record. Read-only; a draft."""
        from assurance_domain.opinion import draft_opinion
        document, _ = self.workflow_document(engagement_id)
        latest: dict[str, str] = {}
        runs = {}
        for run in self._conn.execute(
                """SELECT run_id, procedure_id, status, summary FROM procedure_run
                   WHERE engagement_id = ? ORDER BY created_at, rowid""",
                (engagement_id,)):
            latest[run["procedure_id"]] = run["run_id"]
            runs[run["run_id"]] = run
        current = set(latest.values())
        findings = [f for f in self.findings(engagement_id) if f["run_id"] in current]
        summary_run = None
        run_id = latest.get("completion.uncorrected_misstatements")
        if run_id and runs[run_id]["status"] == "completed":
            summary_run = {"summary": json.loads(runs[run_id]["summary"])}
        return draft_opinion(
            readiness=self.readiness(engagement_id), sad=self.sad(engagement_id),
            findings=findings, misstatement_run=summary_run,
            materiality=float(document["materiality"].get("amount") or 0),
            completion=document.get("completion") or {},
            recorded=document.get("opinion_decisions") or {})

    def readiness(self, engagement_id: str) -> dict:
        info = self._engagement(engagement_id)
        document, _ = self.workflow_document(engagement_id)
        # Team names in the workflow document come from real assignments.
        team = {"preparer": "", "reviewer": "", "engagement_partner": ""}
        for member in self.team(engagement_id):
            slot = ("engagement_partner" if member["role"] == "partner"
                    else member["role"])
            team.setdefault(slot, "")
            if not team[slot]:
                team[slot] = member["principal_id"]
        document["team"] = team

        # Assessed risks live in their own table (judgment, versioned and
        # concurred like dispositions); overlay them into the document shape
        # the readiness gates already read, so the risk→procedure linkage is
        # what a lock is refused over.
        document["risks"] = {
            r["risk_id"]: {
                "manual": True, "archived": False,
                "assertion": r["assertion"], "level": r["level"],
                "response": r["response"], "procedure_ids": r["procedure_ids"],
                "proposed_by": r["proposed_by"],
                "concurred_by": r["concurred_by"],
            }
            for r in self._risk_records(engagement_id)}

        datasets = self._conn.execute(
            "SELECT COUNT(*) c FROM normalized_dataset WHERE engagement_id = ?",
            (engagement_id,)).fetchone()["c"]
        if not datasets:
            # No data means no procedure gates at all, so readiness must
            # demand the partner's explicit no-data assertion instead of
            # silence (tracker 3.4). "required" is set here — where dataset
            # absence is a fact — and read by the domain blocker; it is
            # never persisted, so documents with data stay untouched.
            assertion = dict(document.get("no_data_assertion") or {})
            assertion["required"] = True
            document["no_data_assertion"] = assertion
        coverage = self.coverage(engagement_id) if datasets else None
        if coverage:
            coverage = self._overlay_runs(engagement_id, coverage)
        report = {
            "company": info["client_name"], "fye": info["period_end"],
            "verdicts": [], "refusals": [],
            "procedure_coverage": coverage,
        }
        from assurance_persistence.spine import verify_journal
        return readiness(report, document, self.sad(engagement_id),
                         trail_status={"ok": verify_journal(self._conn)["ok"]})

    def _overlay_runs(self, engagement_id: str, coverage: dict) -> dict:
        latest: dict[str, dict] = {}
        for run in self.runs(engagement_id):
            latest[run["procedure_id"]] = run
        for row in coverage.get("procedures", []):
            run = latest.get(row["procedure_id"])
            if not run:
                continue
            if run["status"] == "error":
                row["execution_status"] = "error"
            else:
                row["execution_status"] = "completed"
                row["procedure_run"] = {
                    "run_id": run["run_id"], "status": "completed",
                    "review_status": ("approved"
                                      if run["status"] == "approved"
                                      else "pending"),
                }
        return coverage

    # ----------------------------------------------- screen 6: lock

    def lock(self, actor: str, engagement_id: str, *,
             expected_version: int) -> dict:
        """Lock, snapshot, and sign — one transaction, or none of it.

        The manifest freezes every entity the lock covers; the signature
        binds the partner's device key to exactly that byte set. What it
        proves is stated inside the manifest itself.
        """
        self._require_not_archived(engagement_id)
        state = self.readiness(engagement_id)
        if not state["ready"]:
            return {"locked": False,
                    "blockers": state["blockers"],
                    "report_implication": state["report_implication"]}
        if self._keystore is None:
            raise RuntimeError(
                "locking requires a signing key store; none is configured")
        identity = self._keystore.identity(actor)

        def handler(uow):
            if "partner" not in uow.principals.roles_for(engagement_id, actor):
                raise AuthorizationError("locking requires the partner")
            version = uow.engagements.set_status(
                engagement_id, "locked", expected_version=expected_version)
            manifest = self._lock_manifest(engagement_id, uow.execute)
            digest = _manifest_digest(manifest)
            from assurance_persistence.spine import journal_head
            head_seq, head_hash = journal_head(self._conn)
            snapshot_id = uow.snapshots.record(
                engagement_id, manifest=manifest, digest=digest,
                journal_head_seq=head_seq, journal_head_hash=head_hash)
            signature_hex = self._keystore.sign(actor, digest)
            from assurance_artifacts.signing import ALGORITHM
            uow.snapshots.sign(
                snapshot_id, engagement_id=engagement_id,
                signer_principal=actor, key_id=identity.key_id,
                algorithm=ALGORITHM,
                public_key_pem=identity.public_key_pem,
                signature_hex=signature_hex)
            return {"locked": True, "version": version,
                    "snapshot_id": snapshot_id, "digest": digest,
                    "key_id": identity.key_id,
                    "report_implication": state["report_implication"]}
        return run_command(
            self._conn, self._command(actor, "engagement.lock", engagement_id),
            handler).result

    def unlock(self, actor: str, engagement_id: str, *, reason: str,
               expected_version: int) -> dict:
        """Reopen a locked engagement by superseding its lock — never erasing it.

        Professional basis (AU-C 230 / AS 1215): after the file is assembled,
        documentation is not deleted or discarded, and any change must record
        the specific reason, by whom, and when. Here the superseded snapshot,
        its signature, and its journal anchor remain permanently verifiable;
        the reason enters the hash-chained journal under the partner's
        principal; work after reopening flows through the same preparer /
        reviewer / partner gates (who made and reviewed each change); and the
        next lock signs a new manifest that names its predecessor and the
        reason it was reopened.
        """
        reason = " ".join(str(reason or "").split())
        if len(reason) < 10:
            raise ValueError(
                "unlocking requires a specific reason (ten characters or "
                "more); it becomes a permanent part of the engagement record")
        self._require_not_archived(engagement_id)
        if self._engagement(engagement_id)["status"] != "locked":
            raise ValueError("the engagement is not locked")

        def handler(uow):
            if "partner" not in uow.principals.roles_for(engagement_id, actor):
                raise AuthorizationError("unlocking requires the partner")
            superseded = uow.snapshots.supersede(
                engagement_id, actor=actor, reason=reason)
            version = uow.engagements.set_status(
                engagement_id, "open", expected_version=expected_version)
            return {"unlocked": True, "version": version,
                    "superseded": superseded, "reason": reason}
        return run_command(
            self._conn,
            self._command(actor, "engagement.unlock", engagement_id),
            handler).result

    def _lock_manifest(self, engagement_id: str, query,
                       schema: str = "noesi-lock-manifest-v2") -> dict:
        """Deterministic snapshot of every entity the lock covers.

        A re-lock names its predecessor: the superseded snapshot's digest and
        the documented reason ride inside the new manifest, so the partner's
        signature covers the amendment record itself (AU-C 230's reason /
        who / when for changes after assembly). A first lock has no such
        section and keeps the original v1 byte shape.

        v2 (2026-09-30) adds each risk's fraud flag. A lock is always
        re-verified in the schema it was signed in, so v1 locks still verify.
        """
        def rows(sql: str) -> list[dict]:
            return [dict(row) for row in query(sql, (engagement_id,))]

        engagement = rows("SELECT engagement_id, client_name, period_end, "
                          "status, version FROM engagement "
                          "WHERE engagement_id = ?")[0]
        workflow = query(
            "SELECT payload, version FROM workflow_state "
            "WHERE engagement_id = ?", (engagement_id,)).fetchone()
        predecessor = query(
            """SELECT snapshot_id, sequence, digest, supersede_reason,
               superseded_by, superseded_at FROM lock_snapshot
               WHERE engagement_id = ? AND status = 'superseded'
               ORDER BY sequence DESC LIMIT 1""",
            (engagement_id,)).fetchone()
        supersession = {} if predecessor is None else {
            "sequence": predecessor["sequence"] + 1,
            "supersedes": {
                "snapshot_id": predecessor["snapshot_id"],
                "sequence": predecessor["sequence"],
                "digest": predecessor["digest"],
                "reason": predecessor["supersede_reason"],
                "unlocked_by": predecessor["superseded_by"],
                "unlocked_at": predecessor["superseded_at"],
            },
        }
        import hashlib
        return {
            "schema": schema,
            **supersession,
            "engagement": engagement,
            "workflow": {
                "version": workflow["version"] if workflow else 0,
                "payload_sha256": hashlib.sha256(
                    workflow["payload"].encode("utf-8")).hexdigest()
                if workflow else None,
            },
            "artifacts": rows(
                "SELECT artifact_id, sha256, size_bytes, media_type, "
                "original_name, state FROM artifact "
                "WHERE engagement_id = ? ORDER BY artifact_id"),
            "mapping_specs": rows(
                "SELECT spec_id, role, spec_digest, status, proposed_by, "
                "approved_by, version FROM mapping_spec "
                "WHERE engagement_id = ? ORDER BY spec_id"),
            "datasets": rows(
                "SELECT dataset_id, role, mapping_spec_id, artifact_id, "
                "rows_in, rows_loaded, rows_rejected, control_total, "
                "output_digest FROM normalized_dataset "
                "WHERE engagement_id = ? ORDER BY dataset_id"),
            "runs": rows(
                "SELECT run_id, procedure_id, job_id, status, result_digest, "
                "executed_by, reviewed_by, approved_by, version "
                "FROM procedure_run WHERE engagement_id = ? ORDER BY run_id"),
            "dispositions": rows(
                "SELECT finding_uid, status, note, version FROM disposition "
                "WHERE engagement_id = ? ORDER BY finding_uid"),
            "risks": rows(
                "SELECT risk_id, assertion, level, response, procedure_ids, "
                "proposed_by, concurred_by, archived, version"
                + (", fraud" if schema != "noesi-lock-manifest-v1" else "")
                + " FROM risk_assessment WHERE engagement_id = ? "
                "ORDER BY risk_id"),
            "team": rows(
                "SELECT principal_id, role FROM principal_assignment "
                "WHERE engagement_id = ? ORDER BY role, principal_id"),
            "limits": (
                "This signature proves which principal's device key approved "
                "exactly this byte set and when the local signer recorded "
                "it. It does not prove the accounting source was complete "
                "or authentic, and it does not provide trusted time."),
        }

    def _lock_history(self, engagement_id: str) -> list[dict]:
        """Superseded locks, each re-verified from stored material alone."""
        from assurance_artifacts.signing import verify_signature

        history = []
        for row in self._conn.execute(
                """SELECT * FROM lock_snapshot WHERE engagement_id = ?
                   AND status = 'superseded' ORDER BY sequence""",
                (engagement_id,)):
            signature = self._conn.execute(
                "SELECT * FROM lock_signature WHERE snapshot_id = ?",
                (row["snapshot_id"],)).fetchone()
            head = self._conn.execute(
                "SELECT entry_hash FROM domain_event WHERE event_seq = ?",
                (row["journal_head_seq"],)).fetchone()
            history.append({
                "sequence": row["sequence"],
                "snapshot_id": row["snapshot_id"],
                "digest": row["digest"],
                "locked_at": row["created_at"],
                "manifest_ok": _manifest_digest(
                    json.loads(row["manifest"])) == row["digest"],
                "signature_ok": bool(signature) and verify_signature(
                    signature["public_key_pem"], row["digest"],
                    signature["signature_hex"]),
                "journal_anchor_ok": head is not None
                and head["entry_hash"] == row["journal_head_hash"],
                "signer": signature["signer_principal"] if signature else None,
                "signed_at": signature["signed_at"] if signature else None,
                "unlocked_by": row["superseded_by"],
                "unlocked_at": row["superseded_at"],
                "reason": row["supersede_reason"],
            })
        return history

    def verify_lock(self, engagement_id: str) -> dict:
        """Re-derive everything a lock claims; report exactly what holds."""
        from assurance_artifacts.signing import verify_signature
        from assurance_persistence.spine import verify_journal

        history = self._lock_history(engagement_id)
        snapshot = self._conn.execute(
            """SELECT * FROM lock_snapshot WHERE engagement_id = ?
               AND status = 'active'""",
            (engagement_id,)).fetchone()
        if snapshot is None:
            return {"locked": False,
                    "error": ("the lock was superseded; the engagement is "
                              "reopened" if history
                              else "no lock snapshot exists"),
                    "history": history}
        signature = self._conn.execute(
            "SELECT * FROM lock_signature WHERE snapshot_id = ?",
            (snapshot["snapshot_id"],)).fetchone()

        stored_manifest = json.loads(snapshot["manifest"])
        current_manifest = self._lock_manifest(
            engagement_id, self._conn.execute,
            schema=stored_manifest.get("schema", "noesi-lock-manifest-v1"))
        drift = sorted(
            section for section in stored_manifest
            if stored_manifest[section] != current_manifest.get(section))
        snapshot_ok = (
            not drift
            and _manifest_digest(current_manifest) == snapshot["digest"])

        signature_ok = bool(signature) and verify_signature(
            signature["public_key_pem"], snapshot["digest"],
            signature["signature_hex"])

        journal = verify_journal(self._conn)
        head_row = self._conn.execute(
            "SELECT entry_hash FROM domain_event WHERE event_seq = ?",
            (snapshot["journal_head_seq"],)).fetchone()
        journal_ok = (journal["ok"] and head_row is not None
                      and head_row["entry_hash"]
                      == snapshot["journal_head_hash"])

        return {
            "locked": True,
            "sequence": snapshot["sequence"],
            "snapshot_ok": snapshot_ok,
            "drift": drift,
            "signature_ok": signature_ok,
            "signer": dict(signature) and {
                "principal": signature["signer_principal"],
                "key_id": signature["key_id"],
                "algorithm": signature["algorithm"],
                "signed_at": signature["signed_at"],
            } if signature else None,
            "journal_ok": journal_ok,
            "journal_events_checked": journal["checked"],
            "verified": snapshot_ok and signature_ok and journal_ok,
            "history": history,
            "limits": stored_manifest.get("limits", ""),
        }

    # ------------------------------------------------- screen 6b: export

    def _packet_body(self, engagement_id: str, lock: dict | None) -> dict:
        """The evidence packet's contents, sealed or not. ``lock`` is the
        signed lock block, or None for a draft working paper."""
        from assurance_workpapers.packet import PACKET_LIMITS, PACKET_VERSION
        info = self._engagement(engagement_id)

        # Superseded locks travel whole — manifest, signature, reason — so
        # the amendment record verifies offline like everything else.
        lock_history = []
        for row in self._conn.execute(
                """SELECT * FROM lock_snapshot WHERE engagement_id = ?
                   AND status = 'superseded' ORDER BY sequence""",
                (engagement_id,)):
            old_signature = self._conn.execute(
                "SELECT * FROM lock_signature WHERE snapshot_id = ?",
                (row["snapshot_id"],)).fetchone()
            lock_history.append({
                "sequence": row["sequence"],
                "manifest": json.loads(row["manifest"]),
                "digest": row["digest"],
                "journal_head_seq": row["journal_head_seq"],
                "journal_head_hash": row["journal_head_hash"],
                "locked_at": row["created_at"],
                "signature": {
                    "signer_principal": old_signature["signer_principal"],
                    "key_id": old_signature["key_id"],
                    "algorithm": old_signature["algorithm"],
                    "public_key_pem": old_signature["public_key_pem"],
                    "signature_hex": old_signature["signature_hex"],
                    "signed_at": old_signature["signed_at"],
                } if old_signature else None,
                "unlocked_by": row["superseded_by"],
                "unlocked_at": row["superseded_at"],
                "reason": row["supersede_reason"],
            })

        runs = []
        executed = set()
        for row in self._conn.execute(
                """SELECT * FROM procedure_run WHERE engagement_id = ?
                   ORDER BY created_at, rowid""", (engagement_id,)):
            executed.add(row["procedure_id"])
            runs.append({
                "run_id": row["run_id"],
                "procedure_id": row["procedure_id"],
                "job_id": row["job_id"],
                "manifest": json.loads(row["manifest"]),
                "status": row["status"],
                # The seal was taken at execution, before review moved status.
                "status_at_execution": ("error" if row["status"] == "error"
                                        else "completed"),
                "summary": json.loads(row["summary"]),
                "findings": json.loads(row["findings"]),
                "error": row["error"],
                "result_digest": row["result_digest"],
                "executed_by": row["executed_by"],
                "reviewed_by": row["reviewed_by"],
                "approved_by": row["approved_by"],
            })
        document, _ = self.workflow_document(engagement_id)
        selections = document.get("procedures", {})
        not_run = []
        for contract in self._contracts(document):
            if contract.procedure_id in executed:
                continue
            decision = selections.get(contract.procedure_id, {})
            reason = ("deselected: " + decision.get("rationale", "")
                      if decision.get("selected") is False
                      else "not executed before lock" if lock
                      else "not executed yet")
            not_run.append({"procedure_id": contract.procedure_id,
                            "reason": reason})

        dispositions = {
            row["finding_uid"]: {"status": row["status"], "note": row["note"],
                                 "proposed_by": row["proposed_by"],
                                 "concurred_by": row["concurred_by"]}
            for row in self._conn.execute(
                "SELECT * FROM disposition WHERE engagement_id = ?",
                (engagement_id,))}

        from assurance_persistence.database import utcnow
        packet = {
            "packet_version": PACKET_VERSION,
            "generated": utcnow(),
            "software": "noesi-assurance-workbench",
            "engagement": {
                "engagement_id": engagement_id,
                "client_name": info["client_name"],
                "period_end": info["period_end"],
                "status": info["status"],
            },
            "lock": lock,
            "lock_history": lock_history,
            "runs": runs,
            "procedures_not_run": not_run,
            # Present when the partner asserted no data-dependent procedures
            # apply (tracker 3.4); the workflow payload hash in the lock
            # manifest already covers it, this puts the words in the packet.
            "no_data_assertion": document.get("no_data_assertion"),
            "dispositions": dispositions,
            "summary_of_audit_differences": self.sad(engagement_id),
            # The finished audit file: what was covered and how it was set
            # up, and the opinion the evidence supports with the partner's
            # recorded judgments — sealed with everything else.
            "scope": {
                "cycles": document.get("cycles") or [],
                "period_start": (document.get("period") or {}).get("start"),
                "period_end": info["period_end"],
                "materiality": document.get("materiality"),
                "policies": document.get("policies") or {},
                "retired": document.get("retired") or [],
            },
            "opinion": self.draft_opinion(engagement_id),
            "limits": PACKET_LIMITS,
        }
        return packet

    def export_packet(self, actor: str, engagement_id: str) -> dict:
        """Build, sign, and journal an evidence packet from the frozen lock.

        Export refuses unless the lock fully verifies right now — a drifted
        or broken engagement cannot produce a packet that pretends
        otherwise.
        """
        from assurance_artifacts.signing import ALGORITHM
        from assurance_workpapers.packet import (
            PACKET_LIMITS, PACKET_VERSION, packet_digest, seal_packet,
        )

        self._require(engagement_id, actor,
                      "preparer", "reviewer", "partner")
        verification = self.verify_lock(engagement_id)
        if not verification.get("verified"):
            raise ValueError(
                "export refused: the lock does not verify "
                f"(drift={verification.get('drift')}, "
                f"signature_ok={verification.get('signature_ok')}, "
                f"journal_ok={verification.get('journal_ok')})")
        if self._keystore is None:
            raise RuntimeError(
                "export is a signed operation; no key store is configured")

        snapshot = self._conn.execute(
            """SELECT * FROM lock_snapshot WHERE engagement_id = ?
               AND status = 'active'""",
            (engagement_id,)).fetchone()
        signature = self._conn.execute(
            "SELECT * FROM lock_signature WHERE snapshot_id = ?",
            (snapshot["snapshot_id"],)).fetchone()
        packet = self._packet_body(engagement_id, {
            "manifest": json.loads(snapshot["manifest"]),
            "digest": snapshot["digest"],
            "journal_head_seq": snapshot["journal_head_seq"],
            "journal_head_hash": snapshot["journal_head_hash"],
            "signature": {
                "signer_principal": signature["signer_principal"],
                "key_id": signature["key_id"],
                "algorithm": signature["algorithm"],
                "public_key_pem": signature["public_key_pem"],
                "signature_hex": signature["signature_hex"],
                "signed_at": signature["signed_at"],
            },
        })
        identity = self._keystore.identity(actor)
        digest = packet_digest(packet)
        seal_packet(
            packet, exporter=actor, key_id=identity.key_id,
            public_key_pem=identity.public_key_pem,
            signature_hex=self._keystore.sign(actor, digest),
            algorithm=ALGORITHM)

        def handler(uow):
            uow.emit(entity_type="evidence_packet",
                     entity_id=snapshot["snapshot_id"],
                     event_type="export.packet",
                     payload={"packet_digest": digest,
                              "exporter": actor,
                              "key_id": identity.key_id},
                     engagement_id=engagement_id)
            return {"packet_digest": digest}
        run_command(self._conn,
                    self._command(actor, "export.packet", engagement_id),
                    handler)
        return packet

    def workpaper_html(self, actor: str, engagement_id: str) -> str:
        """The working paper: from the signed packet once locked; before
        that, a draft from the live record, marked as such, unsigned."""
        from assurance_workpapers.workpaper import render_workpaper
        if self._engagement(engagement_id)["status"] == "locked":
            return render_workpaper(self.export_packet(actor, engagement_id))
        return render_workpaper(self.draft_packet(actor, engagement_id))

    def draft_packet(self, actor: str, engagement_id: str) -> dict:
        """The packet's contents as they stand now: not locked, not signed,
        not an export. For reading the file while the work goes on."""
        self._require(engagement_id, actor, "preparer", "reviewer", "partner")
        packet = self._packet_body(engagement_id, None)
        packet["draft"] = True
        packet["draft_manifest"] = self._lock_manifest(
            engagement_id, self._conn.execute)
        return packet

    # ------------------------------------------------------------ helpers

    def _engagement(self, engagement_id: str) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT * FROM engagement WHERE engagement_id = ? AND tenant_id = ?",
            (engagement_id, self._tenant)).fetchone()
        if row is None:
            raise KeyError(f"engagement {engagement_id}")
        return row

    def _artifact_content(self, artifact_id: str) -> bytes:
        artifact = self._conn.execute(
            "SELECT sha256, state FROM artifact WHERE artifact_id = ?",
            (artifact_id,)).fetchone()
        if artifact is None:
            raise KeyError(f"artifact {artifact_id}")
        if artifact["state"] != "promoted":
            raise ValueError("artifact is retired; its content is gone")
        return self._vault.read_bytes(artifact["sha256"])

    def _artifact_table(self, artifact_id: str, extraction: dict | None = None
                        ) -> tuple[list[str], list[dict], dict | None, list[int] | None]:
        """Header-keyed rows from a CSV or an Excel workbook.

        Returns the resolved workbook extraction (sheet, header row, what
        was read and where it stopped), or None for CSV, and each row's
        sheet row number when a recipe dropped rows (None: contiguous).
        A QuickBooks recipe named in the extraction flattens the report and
        adds its check report. Legacy .xls and unreadable workbooks are
        refused with instructions; the original bytes stay in the vault as
        evidence either way.
        """
        content = self._artifact_content(artifact_id)
        if xlsx.is_xlsx(content) or xlsx.is_legacy_xls(content):
            if extraction and extraction.get("converter") not in (None, xlsx.CONVERTER):
                raise ValueError(
                    f"this spec was read with {extraction.get('converter')!r}; "
                    f"this build reads workbooks with {xlsx.CONVERTER!r}")
            header_row = (extraction or {}).get("header_row")
            try:
                resolved, headers, rows = xlsx.extract(
                    content, sheet=(extraction or {}).get("sheet"),
                    header_row=int(header_row) if header_row else None)
            except xlsx.WorkbookError as exc:
                raise ValueError(str(exc)) from exc
            recipe_id = (extraction or {}).get("recipe")
            if not recipe_id:
                return headers, rows, resolved, None
            recipe = quickbooks.get(str(recipe_id))
            version = extraction.get("recipe_version") or quickbooks.RECIPE_VERSION
            if version != quickbooks.RECIPE_VERSION:
                raise ValueError(
                    f"this spec was read with recipe version {version!r}; "
                    f"this build has {quickbooks.RECIPE_VERSION!r}")
            headers, rows, source_rows, report = quickbooks.apply(
                recipe.recipe_id, headers, rows, resolved["header_row"] + 1)
            resolved.update(recipe=recipe.recipe_id,
                            recipe_version=quickbooks.RECIPE_VERSION,
                            recipe_report=report)
            return headers, rows, resolved, source_rows
        if (extraction or {}).get("recipe"):
            raise ValueError("QuickBooks recipes read .xlsx exports; "
                             "this artifact is not a workbook")
        text = content.decode("utf-8-sig", errors="replace")
        rows = list(csv.DictReader(text.splitlines()))
        headers = list(rows[0].keys()) if rows else []
        return headers, rows, None, None

    # ------------------------------------------ AP control balance (QuickBooks)

    def _qbo_workbooks(self, engagement_id: str) -> list[dict]:
        """Promoted .xlsx artifacts with their raw first-sheet rows."""
        out = []
        for row in self._conn.execute(
                """SELECT artifact_id, original_name, sha256 FROM artifact
                   WHERE engagement_id = ? AND state = 'promoted'
                   ORDER BY created_at, rowid""", (engagement_id,)):
            content = self._vault.read_bytes(row["sha256"])
            if not xlsx.is_xlsx(content):
                continue
            try:
                [first, *_] = xlsx.preview(content, max_rows=xlsx.MAX_ROWS)
            except (xlsx.WorkbookError, ValueError):
                continue
            out.append({**dict(row), "content": content, "rows": first["rows"],
                        "sheet": first["sheet"]})
        return out

    def ap_control_candidates(self, engagement_id: str) -> dict:
        """Uploaded files that can serve as each side of the AP tie."""
        subledger, ledger = [], []
        for book in self._qbo_workbooks(engagement_id):
            entry = {"artifact_id": book["artifact_id"],
                     "original_name": book["original_name"]}
            if any(m["recipe"] == "qbo.unpaid_bills.vouchers"
                   for m in quickbooks.recognize(book["rows"])):
                subledger.append(entry)
            elif quickbooks.is_general_ledger(book["rows"]):
                ledger.append(entry)
        return {"subledger": subledger, "ledger": ledger}

    def build_ap_control_balance(self, actor: str, engagement_id: str, *,
                                 subledger_artifact_id: str,
                                 ledger_artifact_id: str) -> dict:
        """Prepare the AP control balance schedule from two QuickBooks exports.

        The subledger balance is Unpaid Bills' grand-total open balance; the
        ledger balance is the Accounts Payable account's ending balance in
        the General Ledger export. Both are footed first, and a report that
        does not foot is refused. The schedule is stored as an ordinary
        source file whose provenance names both exports by SHA-256, then goes
        through the same propose, approve and normalize path as any other
        file: the preparer builds it, a reviewer approves its mapping.
        """
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer")
        books = {b["artifact_id"]: b for b in self._qbo_workbooks(engagement_id)}
        sub, gl = books.get(subledger_artifact_id), books.get(ledger_artifact_id)
        if sub is None or gl is None:
            raise KeyError("both files must be .xlsx exports in this engagement")
        if not any(m["recipe"] == "qbo.unpaid_bills.vouchers"
                   for m in quickbooks.recognize(sub["rows"])):
            raise ValueError(f"{sub['original_name']!r} is not QuickBooks' "
                             f"standard Unpaid Bills export")
        extraction, headers, rows = xlsx.extract(sub["content"], sheet=sub["sheet"])
        _, _, _, report = quickbooks.apply(
            "qbo.unpaid_bills.vouchers", headers, rows, extraction["header_row"] + 1)
        if report["totals_disagreeing"]:
            raise ValueError(f"Unpaid Bills does not foot: "
                             f"{report['totals_disagreeing']}")
        open_total = next((t for t in report["grand_total"] or []
                           if t["column"] == "Open balance"), None)
        if open_total is None:
            raise ValueError("Unpaid Bills has no grand TOTAL of open balances")
        ledger = quickbooks.gl_account_balance(gl["rows"])
        if ledger["as_of"] is None:
            raise ValueError(f"the ledger's period {ledger['period']!r} names no end date")

        sub_block = quickbooks.title_block(sub["rows"])
        sub_as_of = (quickbooks.last_date(sub_block["period"])
                     or quickbooks.last_date(sub_block["footer"]))
        subledger = Decimal(open_total["computed"])
        control = Decimal(ledger["ending"])
        period_end = self._conn.execute(
            "SELECT period_end FROM engagement WHERE engagement_id = ?",
            (engagement_id,)).fetchone()["period_end"]
        notes = []
        if ledger["as_of"] != period_end:
            notes.append(f"the ledger runs to {ledger['as_of']}, not the "
                         f"engagement's period end {period_end}")
        if sub_as_of != ledger["as_of"]:
            notes.append(
                f"Unpaid Bills is as of {sub_as_of or 'an undated run'} "
                f"({sub_block['period'] or 'no period'}), the ledger to "
                f"{ledger['as_of']}: confirm both describe the same date")

        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(["Period End", "Subledger Balance", "GL Balance",
                         "Subledger Source", "Subledger As Of", "GL Source",
                         "GL Period", "GL Basis", "Notes"])
        writer.writerow([ledger["as_of"], str(subledger), str(control),
                         f"{sub['original_name']} (sha256 {sub['sha256'][:12]})",
                         sub_as_of or "", f"{gl['original_name']} "
                         f"(sha256 {gl['sha256'][:12]})", ledger["period"],
                         ledger["basis"] or "", "; ".join(notes)])
        provenance = json.dumps({
            "prepared_by": "noesi build_ap_control_balance",
            "recipe_version": quickbooks.RECIPE_VERSION,
            "subledger": {"artifact_id": sub["artifact_id"], "sha256": sub["sha256"],
                          "grand_total": open_total},
            "ledger": {"artifact_id": gl["artifact_id"], "sha256": gl["sha256"],
                       "account": ledger["account"], "beginning": ledger["beginning"],
                       "activity": ledger["activity"], "checks": ledger["checks"]},
        }, sort_keys=True)
        artifact = self.store_source(
            actor, engagement_id, content=buffer.getvalue().encode("utf-8"),
            media_type="text/csv",
            original_name=f"AP control balance {ledger['as_of']} - QuickBooks.csv",
            provenance=provenance)
        return {**artifact, "period_end": ledger["as_of"],
                "subledger_balance": str(subledger), "gl_balance": str(control),
                "difference": str(subledger - control), "notes": notes}

    def workbook_preview(self, engagement_id: str, artifact_id: str) -> dict:
        """Sheets, first rows and suggested header rows of an uploaded workbook."""
        row = self._conn.execute(
            "SELECT engagement_id FROM artifact WHERE artifact_id = ?",
            (artifact_id,)).fetchone()
        if row is None or row["engagement_id"] != engagement_id:
            raise KeyError(f"artifact {artifact_id}")
        content = self._artifact_content(artifact_id)
        if not xlsx.is_xlsx(content):
            raise ValueError("this artifact is not an .xlsx workbook")
        try:
            sheets = xlsx.preview(content)
        except xlsx.WorkbookError as exc:
            raise ValueError(str(exc)) from exc
        for sheet in sheets:
            sheet["recipes"] = quickbooks.recognize(sheet["rows"])
            sheet["quickbooks_note"] = quickbooks.unsupported_report(sheet["rows"])
        return {"artifact_id": artifact_id, "sheets": sheets}

    def _rebuild_table(self, spec_id: str) -> NormalizedTable:
        """Reperform normalization from immutable inputs; verify the digest."""
        spec_row = self._conn.execute(
            "SELECT * FROM mapping_spec WHERE spec_id = ?",
            (spec_id,)).fetchone()
        if spec_row is None:
            raise KeyError(f"mapping_spec {spec_id}")
        if spec_row["status"] != "approved":
            raise ValueError("normalization requires an approved mapping spec")
        stored = json.loads(spec_row["spec"])
        spec = MappingSpec(
            role=stored["role"], headers=tuple(stored["headers"]),
            column_map=stored["column_map"],
            unmapped_headers=tuple(stored["unmapped_headers"]),
            refused_fields=tuple(stored["refused_fields"]),
            source_sha256=stored["source_sha256"], status="approved",
            proposed_by=spec_row["proposed_by"],
            approved_by=spec_row["approved_by"])
        _, rows, _, source_rows = self._artifact_table(
            spec_row["artifact_id"], stored.get("extraction"))
        artifact_name = self._conn.execute(
            "SELECT original_name FROM artifact WHERE artifact_id = ?",
            (spec_row["artifact_id"],)).fetchone()["original_name"]
        extraction = stored.get("extraction")
        return normalize_table(
            rows, spec, source_file=artifact_name,
            first_row=int(extraction["header_row"]) + 1 if extraction else 2,
            source_rows=source_rows)

    def _guess_role(self, artifact_id: str, filename: str) -> tuple[str | None, str]:
        """The role a stored file most likely carries: its name first, then
        its column headings when the name says nothing. A suggestion for the
        preparer and reviewer, cached per file (stored files never change)."""
        role = infer_role(filename)
        if role:
            return role, "filename"
        cache = self.__dict__.setdefault("_role_guess_cache", {})
        if artifact_id not in cache:
            from procedures_ap.ingest import infer_role_from_headers
            try:
                headers, _, _, _ = self._artifact_table(artifact_id, None)
                cache[artifact_id] = infer_role_from_headers(list(headers))
            except (ValueError, KeyError, UnicodeDecodeError):
                cache[artifact_id] = None       # unreadable, several sheets, sections
        guess = cache[artifact_id]
        return guess, ("columns" if guess else "")

    def _role_states(self, engagement_id: str) -> dict[str, list]:
        """Per role, after each load: (that load, the datasets then in use).

        A first load or a replacement starts the in-use set over; an
        addition extends it. The last state is what procedures read.
        """
        states: dict[str, list] = {}
        for dataset in self._conn.execute(
                """SELECT * FROM normalized_dataset WHERE engagement_id = ?
                   ORDER BY created_at, rowid""", (engagement_id,)):
            history = states.setdefault(dataset["role"], [])
            in_use = (history[-1][1] + [dataset]
                      if history and dataset["load_mode"] == "add" else [dataset])
            history.append((dataset, in_use))
        return states

    def _verified_table(self, dataset) -> NormalizedTable:
        table = self._rebuild_table(dataset["mapping_spec_id"])
        if table.output_digest != dataset["output_digest"]:
            raise EvidenceIntegrityError(
                f"dataset {dataset['dataset_id']} no longer reproduces its "
                "recorded digest; refusing to serve unverifiable data")
        return table

    def _dataset_file(self, dataset) -> str:
        row = self._conn.execute(
            "SELECT original_name FROM artifact WHERE artifact_id = ?",
            (dataset["artifact_id"],)).fetchone()
        return row["original_name"] if row else ""

    def _tables(self, engagement_id: str) -> dict:
        """The in-use datasets per role, rebuilt, digest-verified, combined."""
        return {role: _combine([self._verified_table(d) for d in states[-1][1]])
                for role, states in self._role_states(engagement_id).items()}


def _combine(tables: list[NormalizedTable]) -> NormalizedTable:
    """One table from same-role files loaded with mode 'add'."""
    if len(tables) == 1:
        return tables[0]
    from dataclasses import replace as _replace
    totals = [t.control_total for t in tables]
    return _replace(
        tables[0],
        records=[r for t in tables for r in t.records],
        rejects=[r for t in tables for r in t.rejects],
        control_total=(sum(totals) if all(v is not None for v in totals)
                       else None),
        source_file=" + ".join(t.source_file for t in tables),
        source_sha256="",
        diagnostics={"combined_from": [t.source_file for t in tables]})


def _batch_report(results: list[dict], *, done: str) -> dict:
    """Per-item results plus honest counts of what happened and what didn't."""
    return {"results": results,
            done: sum(r["status"] == done for r in results),
            "skipped": sum(r["status"] == "skipped" for r in results),
            "errors": sum(r["status"] == "error" for r in results)}


def _manifest_digest(manifest: dict) -> str:
    import hashlib
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _tags(verdict: dict) -> dict:
    """Tag a stored verdict dict without re-instantiating a Receipt."""
    from procedures_ap import unified

    class _View:
        def __init__(self, data: dict):
            self.domain = data["domain"]
            self.key = tuple(data["key"])
            self.verdict = data["verdict"]
            self.policy = data["policy"]
            self.score = data.get("score")
            self.reason = data.get("reason", "")
            self.evidence = data.get("evidence", {})
    return unified.classify_verdict(_View(verdict))
