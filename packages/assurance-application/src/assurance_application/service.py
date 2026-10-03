# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""WorkbenchService: typed use cases over the transactional spine.

One user per engagement (D9 stage 3, 2 Oct 2026): Noesi supplements an
audit, so it has no chairs, role checks or approvals. Whoever runs the
session does every step, and every command is journaled under that
principal. A column mapping is confirmed in one step by the person who maps
the file. Runs, dispositions and risks carry no review or sign-off (removed
1 Oct 2026).
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
from assurance_domain.jobs import build_manifest, run_job
from assurance_domain.readiness import blank_engagement, readiness
from assurance_domain.sad import (
    performance_rate, summary_of_differences, trivial_rate,
)
from assurance_persistence.database import utcnow
from assurance_persistence.spine import run_command
from procedures_ap.coverage import (apply_selections, compile_coverage,
                                    inventory_from_tables)
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


def _finding_uid(verdict: dict) -> str:
    """Engagement-scoped stable finding identity: domain + key, no company."""
    return f"{verdict['domain']}|{json.dumps(verdict['key'], ensure_ascii=False)}"


SCHEDULE_PROCEDURE = "completion.uncorrected_misstatements"
# The A/P tie's ledger side taken from the loaded trial balance (no GL export).
TB_LEDGER = "trial_balance"
TB_RECIPE = "qbo.trial_balance.trial_balance"

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
    "forensic.check_number_sequence": ("Missing or reused check numbers",
                                       "AU-C 240: concealed disbursements"),
    "forensic.vendor_employee_match": ("Vendors that match an employee",
                                       "AU-C 240: fictitious vendors, conflicts of interest"),
    "forensic.self_approved_payments": ("Payments approved by the person who prepared them",
                                        "AU-C 240: opportunity from incompatible duties"),
    "forensic.benford_first_digit": ("Amounts that do not look natural",
                                     "AU-C 240: invented figures"),
}


def _performance_rate(document: dict) -> Decimal:
    """The engagement's performance-materiality rate (policy
    performance_materiality_pct), or the 75% default when unset."""
    return performance_rate((document.get("policies") or {}).get("performance_materiality_pct"))


def _trivial_rate(document: dict) -> Decimal:
    """B1: the firm's clearly-trivial rate (policy clearly_trivial_pct), or
    the 5% default; one rate for the SAD and revision impact."""
    return trivial_rate((document.get("policies") or {}).get("clearly_trivial_pct"))


class EngagementArchivedError(PermissionError):
    """The engagement is archived; its record cannot change until restored."""


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
                 tenant_id: str):
        self._conn = conn
        self._vault = vault
        self._tenant = tenant_id

    # ------------------------------------------------------------ plumbing

    def _command(self, actor: str, kind: str, engagement_id: str | None = None,
                 command_id: str | None = None) -> Command:
        return Command(command_id or new_id(), self._tenant, actor, kind,
                       engagement_id=engagement_id)

    def _require_own(self, engagement_id: str, *, artifact_id: str | None = None,
                     spec_id: str | None = None) -> None:
        """The file or mapping belongs to this engagement (review 2026-10-02
        batch, M1: another engagement's file could be confirmed and loaded
        here). Refused as not found, so nothing about the other is said."""
        for table, key, value in (("artifact", "artifact_id", artifact_id),
                                  ("mapping_spec", "spec_id", spec_id)):
            if value is None:
                continue
            row = self._conn.execute(
                f"SELECT engagement_id FROM {table} WHERE {key} = ? AND tenant_id = ?",
                (value, self._tenant)).fetchone()
            if row is None or row["engagement_id"] != engagement_id:
                raise NotFoundError(f"{table} {value}")

    def _require_open(self, engagement_id: str) -> None:
        if self._engagement(engagement_id)["archived_at"]:
            raise EngagementArchivedError(
                "the engagement is archived; restore it before changing its record")

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
            # The creator is recorded as the engagement's one user. The
            # "partner" label is kept so older records read the same way.
            uow.principals.assign(engagement_id, actor, "partner")
            return {"engagement_id": engagement_id}
        return run_command(
            self._conn, self._command(actor, "engagement.create"),
            handler).result

    def list_engagements(self, *, archived: bool = False) -> list[dict]:
        """Engagements in use; with ``archived``, only the archived ones."""
        rows = self._conn.execute(
            f"""SELECT engagement_id, client_name, period_end, status, version
               FROM engagement WHERE tenant_id = ?
               AND archived_at IS {'NOT NULL' if archived else 'NULL'}
               ORDER BY client_name, period_end""", (self._tenant,)).fetchall()
        return [dict(row) for row in rows]

    def archive_engagement(self, actor: str, engagement_id: str, *,
                           reason: str) -> dict:
        """Take an engagement off the list without erasing its record.

        A specific reason is required. Nothing is deleted: the journal,
        sources and runs stay as they were. Archiving sets its own flag and
        never the status or version. While archived, nothing in it can change.
        """
        if len(reason.strip()) < 10:
            raise ValueError("archiving requires a specific reason (ten characters or more)")
        info = self._engagement(engagement_id)
        if info["archived_at"]:
            raise ValueError("the engagement is already archived")

        def handler(uow):
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

        The exact client name must be typed back, with a reason.
        Every row that belongs to the engagement goes (sources, mappings,
        datasets, runs, dispositions, workflow, team, risks, and any lock
        recorded before locks were removed), and each
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
            self._set_archived(uow, engagement_id, info["version"], None)
            uow.emit(entity_type="engagement", entity_id=engagement_id,
                     event_type="engagement.restored", payload={},
                     engagement_id=engagement_id)
            return {"engagement_id": engagement_id, "status": info["status"],
                    "version": info["version"]}
        return run_command(
            self._conn, self._command(actor, "engagement.restore", engagement_id),
            handler).result

    def team(self, engagement_id: str) -> list[dict]:
        """Who is on record: the creator, plus any chairs assigned before
        chairs were removed (2 Oct 2026). Read-only history."""
        rows = self._conn.execute(
            """SELECT principal_id, role FROM principal_assignment
               WHERE engagement_id = ? ORDER BY role, principal_id""",
            (engagement_id,)).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------- screen 2: sources and mappings

    def store_source(self, actor: str, engagement_id: str, *, content: bytes,
                     media_type: str, original_name: str,
                     provenance: str = "") -> dict:
        self._require_open(engagement_id)
        outcome = store_artifact(
            self._conn, self._vault,
            command=self._command(actor, "artifact.store", engagement_id),
            engagement_id=engagement_id, source=io.BytesIO(content),
            media_type=media_type, original_name=original_name,
            provenance=provenance)
        return outcome.result

    def confirm_source_mapping(self, actor: str, engagement_id: str, *,
                               role: str, artifact_id: str,
                               extraction: dict | None = None) -> dict:
        """Map one uploaded file's columns and confirm the mapping, in one
        step; the file is then ready to load.

        Checking the columns map right is a data check, not a sign-off, so
        there is no second person. For an Excel workbook, ``extraction``
        names the sheet and 1-based header row (defaults: the only sheet,
        the suggested header row). The choice becomes part of the spec and
        of its digest, so every later rebuild reads exactly those rows again.
        """
        self._require_open(engagement_id)
        self._require_own(engagement_id, artifact_id=artifact_id)
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
                # What the recipe checked, kept and left out, shown with the
                # mapping. Derived from the file, so outside the
                # digest; normalization recomputes it from the vaulted bytes.
                stored["recipe_report"] = resolved["recipe_report"]
            digest = hashlib.sha256(
                (spec.digest + json.dumps(params, sort_keys=True))
                .encode("utf-8")).hexdigest()

        def handler(uow):
            spec_id = uow.mappings.confirm(
                engagement_id, role=role, spec=stored,
                spec_digest=digest, confirmed_by=actor,
                artifact_id=artifact_id)
            return {"spec_id": spec_id, "status": "approved",
                    "column_map": spec.column_map,
                    "unmapped_headers": list(spec.unmapped_headers),
                    "refused_fields": list(spec.refused_fields),
                    "extraction": resolved}
        return run_command(
            self._conn,
            self._command(actor, "mapping.confirm", engagement_id),
            handler).result

    def confirm_pending_mapping(self, actor: str, engagement_id: str,
                                spec_id: str) -> dict:
        """Confirm a mapping proposed before 2 Oct 2026 and never approved,
        so older engagements are not stuck with it."""
        self._require_open(engagement_id)
        self._require_own(engagement_id, spec_id=spec_id)

        def handler(uow):
            uow.mappings.confirm_pending(spec_id, confirmed_by=actor,
                                         engagement_id=engagement_id)
            return {"spec_id": spec_id, "status": "approved"}
        return run_command(
            self._conn,
            self._command(actor, "mapping.confirm", engagement_id),
            handler).result

    def normalize_source(self, actor: str, engagement_id: str,
                         spec_id: str, *, mode: str | None = None) -> dict:
        """Load a confirmed mapping as a dataset.

        When the role already has data, ``mode`` must say what this file
        does: ``"replace"`` (a revised file supersedes what is in use) or
        ``"add"`` (more rows of the same kind, such as a second bank
        account's reconciliation). Guessing either way silently changes
        what every procedure reads, so a load without one is refused.
        """
        self._require_open(engagement_id)
        self._require_own(engagement_id, spec_id=spec_id)
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
            if "entry_id" in table.column_map:
                self._refuse_repeated_entries(table, in_use[-1][1])

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

    # Bulk loading batches the clicks: each batch method loops the
    # single-item use case, so every item keeps its own journaled command and
    # its own checks. Items fail or are skipped individually — one bad file
    # never blocks the other nine — and the caller gets a per-item report.

    def confirm_source_mappings(self, actor: str, engagement_id: str,
                                items: list[dict]) -> dict:
        """Batch map and confirm. Each item: artifact_id plus an optional
        role; a missing role is inferred from the artifact's filename or
        columns. A file already under an active spec *for the same role* is
        skipped, so 'map all' is safe to repeat;
        one file may still feed several roles (a QuickBooks Transaction List
        by Vendor holds both bills and purchase orders)."""
        self._require_open(engagement_id)
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
                entry.update(self.confirm_source_mapping(
                    actor, engagement_id, role=role,
                    artifact_id=artifact_id,
                    extraction=extraction if isinstance(extraction, dict)
                    else None))
                entry.update(status="confirmed", role=role)
                active.add((artifact_id, role))
            except (ValueError, KeyError, NotFoundError) as exc:
                entry.update(status="error", error=str(exc))
            results.append(entry)
        return _batch_report(results, done="confirmed")

    def normalize_sources(self, actor: str, engagement_id: str,
                          spec_ids: list[str],
                          modes: dict[str, str] | None = None) -> dict:
        """Batch normalize confirmed specs. Specs that already produced a
        dataset are skipped rather than re-recorded. ``modes`` gives the
        replace/add choice per spec where its role already has data."""
        self._require_open(engagement_id)
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
        # A schedule the Workbench built (trial balance, AP control balance)
        # names its source exports in its provenance. Those exports are its
        # inputs, not data to load as well, so they are marked: "map all"
        # leaves them out (seen on Kestrel, 2 Oct 2026); mapping one on its
        # own stays possible.
        built_from: dict[str, str] = {}
        for item in artifacts:
            try:
                prov = json.loads(item["provenance"] or "")
            except ValueError:
                continue
            if not (isinstance(prov, dict)
                    and str(prov.get("prepared_by", "")).startswith("noesi build_")):
                continue
            for part in prov.values():
                if isinstance(part, dict) and part.get("artifact_id"):
                    built_from[str(part["artifact_id"])] = item["original_name"]
        for item in artifacts:
            item["built_into"] = built_from.get(item["artifact_id"])
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

    @staticmethod
    def _inventory(tables: dict, document: dict) -> dict:
        """What each loaded role holds, for coverage. A trial balance's
        statement line comes either from a column of the file or from the
        engagement's line mapping (by label or by account): a QuickBooks
        trial balance has no line column at all, so a mapping supplies it.
        The run applies the same mapping first and sets aside any account it leaves
        without a line, listing its sheet rows; the line counts only when the
        mapping reaches at least one loaded account."""
        inventory = inventory_from_tables(tables)
        tb = inventory.get("Trial_balance")
        mapping = document.get("line_mapping") or {}
        if tb is not None and mapping and "line" not in tb["fields"]:
            from procedures_cycles.common import key_text
            rows = tables["Trial_balance"].engine_view().records
            # Only when the mapping gives at least one loaded account a line:
            # a mapping that reaches none of them supplies nothing.
            if any(mapping.get(f"account:{key_text(r.get('account'))}")
                   or mapping.get(f"label:{' '.join(str(r.get('line') or '').split()).lower()}")
                   for r in rows):
                tb["fields"] = sorted({*tb["fields"], "line"})
        return inventory

    def coverage(self, engagement_id: str) -> dict:
        tables = self._tables(engagement_id)
        document, _ = self.workflow_document(engagement_id)
        contracts = self._contracts(document)
        # An AP-only engagement (no scope) compiles exactly as it always has.
        policies = (self._engagement_policies(engagement_id, document)
                    if document.get("cycles") else document.get("policies"))
        compiled = compile_coverage(self._inventory(tables, document),
                                    policies=policies or None, contracts=contracts,
                                    executors=cycle_engines.registered_procedures())
        # The auditor's choices (a procedure included or left out, and why)
        # apply here, so every screen and every caller sees the same audit.
        return {**apply_selections(compiled, document.get("procedures") or {}),
                "source_notes": self._source_notes(engagement_id)}

    def _source_notes(self, engagement_id: str) -> list[dict]:
        """What a builder noted about a file now in use (a trial balance not
        at the period end, a prior year not one year before), so it stays in
        view wherever coverage is read, not only on the panel that built it."""
        out = []
        for role, states in self._role_states(engagement_id).items():
            for dataset in states[-1][1]:
                row = self._conn.execute(
                    "SELECT original_name, provenance FROM artifact WHERE artifact_id = ?",
                    (dataset["artifact_id"],)).fetchone()
                try:
                    notes = json.loads(row["provenance"] or "{}").get("notes") or []
                except (TypeError, ValueError, AttributeError):
                    notes = []
                out.extend({"role": role, "file": row["original_name"], "note": str(n)}
                           for n in notes)
        return out

    # ---------------------------------------- screen 4: runs and findings

    def run_procedure(self, actor: str, engagement_id: str, *,
                      procedure_id: str,
                      policies: dict | None = None) -> dict:
        self._require_open(engagement_id)
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
            self._inventory(self._tables(engagement_id), document),
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
        # Reperformance is legitimate — after a correction or a revised
        # file. Same procedure, same data, same policies must
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

    def runs(self, engagement_id: str) -> list[dict]:
        rows = self._conn.execute(
            """SELECT run_id, procedure_id, job_id, status, summary, error,
               executed_by, version, created_at
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
                                 "proposed_by": row["proposed_by"]}
            for row in self._conn.execute(
                "SELECT * FROM disposition WHERE engagement_id = ?",
                (engagement_id,))}
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
                          "proposed_by": ""})
                out.append({
                    "finding_uid": uid,
                    "run_id": run["run_id"],
                    "procedure_id": run["procedure_id"],
                    "verdict": verdict,
                    "tags": _tags(verdict),
                    "disposition": disposition,
                })
        return out

    def set_disposition(self, actor: str, engagement_id: str, *,
                        finding_uid: str, status: str, note: str = "",
                        expected_version: int = 0) -> dict:
        self._require_open(engagement_id)
        # Validate before the write: the table's CHECK constraint would
        # refuse anyway, but as an IntegrityError that the repository
        # relabels as a version conflict — a misleading message for what
        # is a bad field value (review F1).
        if status not in _DISPOSITION_STATUSES:
            raise ValueError(
                f"unknown disposition status {status!r}; expected one of "
                f"{list(_DISPOSITION_STATUSES)}")

        def handler(uow):
            version = uow.dispositions.set(
                engagement_id, finding_uid, status, note=note,
                expected_version=expected_version, proposed_by=actor)
            return {"finding_uid": finding_uid, "status": status,
                    "version": version}
        return run_command(
            self._conn,
            self._command(actor, "disposition.set", engagement_id),
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
                            _trivial_rate(document), _performance_rate(document))
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

        # Every role any of a procedure's input sets reads (review L5).
        needs = {p.procedure_id: {role for fields in p.input_sets() for role in fields}
                 for p in PROCEDURES + tuple(CYCLE_CONTRACTS_BY_ID.values())}
        latest_runs: dict[str, sqlite3.Row] = {}
        for run in self._conn.execute(
                """SELECT * FROM procedure_run WHERE engagement_id = ?
                   ORDER BY created_at, rowid""", (engagement_id,)):
            latest_runs[run["procedure_id"]] = run
        dispositions = {
            row["finding_uid"]: {"status": row["status"]}
            for row in self._conn.execute(
                "SELECT finding_uid, status FROM disposition "
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
                "action": "rerun",
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

        The judgment is the auditor's: this stores it and names who made it.
        It computes nothing — the engine never grades a risk.
        """
        from procedures_ap.contracts import RISK_LEVELS
        from procedures_cycles.contracts import REGISTER_ASSERTIONS as ASSERTIONS
        self._require_open(engagement_id)
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
        self._require_open(engagement_id)
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

    def archive_risk(self, actor: str, engagement_id: str, *, risk_id: str,
                     expected_version: int) -> dict:
        self._require_open(engagement_id)

        def handler(uow):
            version = uow.risks.archive(
                engagement_id, risk_id, expected_version=expected_version)
            return {"risk_id": risk_id, "archived": True, "version": version}
        return run_command(
            self._conn, self._command(actor, "risk.archive", engagement_id),
            handler).result

    def risks(self, engagement_id: str) -> dict:
        """The risk register for screen 4b: each risk with its response
        linkage, plus the procedures that *could*
        respond to each assertion (candidates), so the UI can suggest."""
        from procedures_ap.contracts import RISK_LEVELS
        from procedures_cycles.contracts import REGISTER_ASSERTIONS as ASSERTIONS
        document, _ = self.workflow_document(engagement_id)
        contracts = self._contracts(document)
        rows = []
        for r in self._risk_records(engagement_id):
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
                "version": r["version"],
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
        gathered = [f for f in self.findings(engagement_id)
                    if f["procedure_id"] in FRAUD_TESTS
                    and f["run_id"] == current.get(f["procedure_id"])
                    and f["verdict"]["verdict"] != "AGREE"]
        # A refusal ("too few amounts", "nothing numbered") says the test did
        # not test; counting it as something found would overstate the work.
        findings = [f for f in gathered if f["tags"].get("class") != "refusal"]
        refusals = [f for f in gathered if f["tags"].get("class") == "refusal"]
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
                "not_tested": [f["verdict"].get("reason", "") for f in refusals
                               if f["procedure_id"] == pid],
            })
        risks = [r for r in self.risks(engagement_id)["risks"] if r["fraud"]]
        return {
            "tests": tests,
            "risks": risks,
            "findings": findings,
            "not_tested": refusals,
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
                "not_tested": sum(1 for t in tests if t["not_tested"]),
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
        self._require_open(engagement_id)
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
        elif section == "line_mapping":
            # The client's own trial-balance label (or one account) mapped to
            # a statement line the procedures read (K8). The preparer or the
            # partner sets it; it reaches every run as a recorded policy.
            from procedures_cycles.common import key_text as _key
            from procedures_cycles.statements import LINES
            if isinstance(values.get("accounts"), dict):
                # Many accounts at once ({account: line}), for a trial balance
                # with no labels of its own (QuickBooks); all checked first.
                if values.get("label") or values.get("account"):
                    raise ValueError("send either accounts, a label or one account")
                changes = [(f"account:{_key(a)}", str(l or "").strip())
                           for a, l in values["accounts"].items() if _key(a)]
                if not changes:
                    raise ValueError("no accounts to map")
            else:
                label = " ".join(str(values.get("label") or "").split()).lower()
                account = _key(values.get("account")) if values.get("account") else ""
                if bool(label) == bool(account):
                    raise ValueError("map either a label or one account, not both")
                changes = [(f"account:{account}" if account else f"label:{label}",
                            str(values.get("line") or "").strip())]
            unknown = sorted({line for _, line in changes if line and line not in LINES})
            if unknown:
                raise ValueError(f"unknown statement line {unknown[0]!r}; one of {list(LINES)}")
            mapping = document.setdefault("line_mapping", {})
            for key, line in changes:
                if line:
                    mapping[key] = line
                else:
                    mapping.pop(key, None)
        elif section == "opinion_decision":
            # A judgment the draft opinion asks for (pervasiveness, the
            # going-concern conclusion). The partner's alone; kept, with who
            # and why, in the engagement record.
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
                                 "or more); it becomes part of the engagement record")
            document.setdefault("opinion_decisions", {})[decision] = {
                "answer": answer, "note": note, "decided_by": actor}
        elif section == "period":
            # The period's first day, when it is not the twelve months ending at
            # period end (a first year, a changed year end). The partner owns it.
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
            # retired list stays in the engagement record.
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
            # never without the reason that goes into the engagement record.
            selected = bool(values.get("selected", True))
            rationale = " ".join(str(values.get("rationale", "")).split())
            if not selected and len(rationale) < 10:
                raise ValueError(
                    f"say why {procedure_id} is left out (ten characters or "
                    "more); the reason becomes part of the engagement record")
            document.setdefault("procedures", {})[procedure_id] = {
                "selected": selected, "rationale": rationale,
                "decided_by": actor}
        elif section == "no_data_assertion":
            # Tracker 3.4: an engagement with zero normalized datasets skips
            # every procedure gate, so readiness could silently pass with no
            # substantive work. The silence must be owned — by the partner,
            # on the record, with a reason that enters the exported record.
            asserted = bool(values.get("asserted", False))
            reason = " ".join(str(values.get("reason", "")).split())
            if asserted and len(reason) < 10:
                raise ValueError(
                    "asserting that no data-dependent procedures apply "
                    "requires a specific reason (ten characters or more); "
                    "it becomes part of the engagement record")
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
            if name == "performance_materiality_pct":
                performance_rate(values["value"])
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
                "SELECT finding_uid, status FROM disposition "
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
                "procedure_id": item["procedure_id"],
                "domain": verdict["domain"],
                "key": verdict["key"],
                "verdict": verdict["verdict"],
                "score": verdict.get("score"),
                "reason": verdict.get("reason", ""),
                "evidence": verdict.get("evidence", {}),
                "disposition": record["status"] if record else "undisposed",
            })
        summary = summary_of_differences(rows, materiality=materiality,
                                         trivial_pct=_trivial_rate(document),
                                         performance_pct=_performance_rate(document))
        # Findings that are not dollar misstatements (leads, refusals-to-
        # evaluate, control deviations) never reach the SAD, but they still
        # need a decision: one left undisposed, or marked follow-up, is an
        # open question and must not pass readiness silently.
        from assurance_domain.sad import _is_candidate
        open_findings = sorted({
            row["finding_uid"] for row in rows
            if row["verdict"] != "AGREE" and not _is_candidate(row)
            and row["disposition"] in ("undisposed", "follow_up")})
        summary["open_findings"] = open_findings
        summary["open_findings_count"] = len(open_findings)
        # Which procedure each open finding came from, counted: a finding's
        # uid names its domain and key, not its procedure, so the screens
        # must not guess the procedure from the uid.
        procedure_of = {row["finding_uid"]: row["procedure_id"] for row in rows}
        by_procedure: dict[str, int] = {}
        for uid in open_findings:
            by_procedure[procedure_of[uid]] = by_procedure.get(procedure_of[uid], 0) + 1
        summary["open_findings_by_procedure"] = by_procedure
        # B2: one summary. The misstatement schedule, once evaluated by
        # completion.uncorrected_misstatements, is the signed, projected,
        # by-statement-line view; it rides on the SAD, and the SAD cannot
        # conclude "immaterial" while a line there reaches materiality.
        schedule = self._misstatement_schedule(engagement_id)
        summary["schedule"] = schedule
        if schedule and schedule["material_lines"] and summary["conclusion"] == "immaterial":
            summary["conclusion"] = "material"
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
        from procedures_cycles.common import key_text
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
        # Accounts whose own label is not a statement line, one by one, each
        # with a suggestion from its name: a QuickBooks trial balance has no
        # labels at all, so this is where its accounts get mapped.
        accounts = []
        for row in (table.records if table else []):
            label = " ".join(str(row.get("line") or "").split())
            if label.lower() in LINES:
                continue
            account = str(row.get("account") or "")
            description = " ".join(str(row.get("description") or "").split())
            accounts.append({
                "account": account, "description": description, "label": label,
                "mapped_to": (overrides.get(key_text(account))
                              or mapping.get(f"label:{label.lower()}")),
                "suggestion": suggest_line(description) or suggest_line(label)})
        return {"lines": list(LINES), "labels": sorted(labels.values(),
                                                        key=lambda i: i["label"]),
                "accounts": accounts,
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
        from procedures_cycles.policy_text import policy_text
        shown = {"clearly_trivial_pct", "performance_materiality_pct"} | {p for a in areas
                                           for p in a["required_policies"] + a["optional_policies"]}
        return {"areas": areas, "engagement_policies": list(ENGAGEMENT_POLICIES),
                "general_policies": ["performance_materiality_pct", "clearly_trivial_pct"],
                "policy_text": {p: policy_text(p) for p in sorted(shown)}}

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

        # Assessed risks live in their own table (judgment, versioned like
        # dispositions); overlay them into the document shape
        # the readiness gates already read.
        document["risks"] = {
            r["risk_id"]: {
                "manual": True, "archived": False, "title": r["title"],
                "assertion": r["assertion"], "level": r["level"],
                "response": r["response"], "procedure_ids": r["procedure_ids"],
                "proposed_by": r["proposed_by"],
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
        # A run whose every finding is a refusal ("too few amounts", "nothing
        # numbered") completed but tested nothing; say so beside "completed".
        classes: dict[str, set] = {}
        for finding in self.findings(engagement_id):
            classes.setdefault(finding["run_id"], set()).add(
                finding["tags"].get("class"))
        for row in coverage.get("procedures", []):
            run = latest.get(row["procedure_id"])
            if not run:
                continue
            if run["status"] == "error":
                row["execution_status"] = "error"
            else:
                row["execution_status"] = "completed"
                row["procedure_run"] = {"run_id": run["run_id"], "status": "completed"}
                if classes.get(run["run_id"]) == {"refusal"}:
                    row["tested_nothing"] = True
        return coverage

    # ----------------------------------------------- screen 6: the record

    def _record_manifest(self, engagement_id: str) -> dict:
        """Deterministic digest list of every entity in the engagement record:
        its files, mappings, datasets, runs, dispositions, risks and team,
        and the journal position it was taken at. It travels in the exported
        record so a reader can see exactly what the record covered."""
        def rows(sql: str) -> list[dict]:
            return [dict(row) for row in self._conn.execute(sql, (engagement_id,))]

        engagement = rows("SELECT engagement_id, client_name, period_end, "
                          "status, version FROM engagement "
                          "WHERE engagement_id = ?")[0]
        workflow = self._conn.execute(
            "SELECT payload, version FROM workflow_state "
            "WHERE engagement_id = ?", (engagement_id,)).fetchone()
        from assurance_persistence.spine import journal_head, verify_journal
        head_seq, head_hash = journal_head(self._conn)
        # The decision trail's own check, taken when the record is made. A
        # broken chain does not stop the export (the record is still the
        # auditor's), but the record says so and its offline check fails.
        trail = verify_journal(self._conn)
        import hashlib
        return {
            "schema": "noesi-record-manifest-v2",
            "engagement": engagement,
            "journal_head": {"seq": head_seq, "hash": head_hash},
            "journal_check": {"ok": trail["ok"], "checked": trail["checked"],
                              "break_at_seq": trail["break_at_seq"]},
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
                "executed_by, version "
                "FROM procedure_run WHERE engagement_id = ? ORDER BY run_id"),
            "dispositions": rows(
                "SELECT finding_uid, status, note, proposed_by, version "
                "FROM disposition WHERE engagement_id = ? ORDER BY finding_uid"),
            "risks": rows(
                "SELECT risk_id, title, rationale, assertion, level, response, "
                "procedure_ids, proposed_by, archived, fraud, version FROM risk_assessment "
                "WHERE engagement_id = ? ORDER BY risk_id"),
            "team": rows(
                "SELECT principal_id, role FROM principal_assignment "
                "WHERE engagement_id = ? ORDER BY role, principal_id"),
        }

    def _packet_body(self, engagement_id: str) -> dict:
        """The engagement record's contents, as they stand now."""
        from assurance_workpapers.packet import (
            PACKET_LIMITS, PACKET_VERSION, manifest_digest,
        )
        info = self._engagement(engagement_id)
        runs, executed = [], set()
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
                # The seal was taken at execution: completed or error.
                "status_at_execution": ("error" if row["status"] == "error"
                                        else "completed"),
                "summary": json.loads(row["summary"]),
                "findings": json.loads(row["findings"]),
                "error": row["error"],
                "result_digest": row["result_digest"],
                "executed_by": row["executed_by"],
            })
        document, _ = self.workflow_document(engagement_id)
        selections = document.get("procedures", {})
        not_run = []
        for contract in self._contracts(document):
            if contract.procedure_id in executed:
                continue
            decision = selections.get(contract.procedure_id, {})
            reason = ("left out: " + decision.get("rationale", "")
                      if decision.get("selected") is False
                      else "not executed yet")
            not_run.append({"procedure_id": contract.procedure_id,
                            "reason": reason})

        dispositions = {
            row["finding_uid"]: {"status": row["status"], "note": row["note"],
                                 "proposed_by": row["proposed_by"]}
            for row in self._conn.execute(
                "SELECT * FROM disposition WHERE engagement_id = ?",
                (engagement_id,))}

        manifest = self._record_manifest(engagement_id)
        from assurance_persistence.database import utcnow
        return {
            "packet_version": PACKET_VERSION,
            "generated": utcnow(),
            "software": "noesi-assurance-workbench",
            "engagement": {
                "engagement_id": engagement_id,
                "client_name": info["client_name"],
                "period_end": info["period_end"],
            },
            "manifest": manifest,
            "manifest_digest": manifest_digest(manifest),
            "runs": runs,
            "procedures_not_run": not_run,
            # Present when the partner asserted no data-dependent procedures
            # apply (tracker 3.4).
            "no_data_assertion": document.get("no_data_assertion"),
            "dispositions": dispositions,
            "summary_of_audit_differences": self.sad(engagement_id),
            "readiness": self.readiness(engagement_id),
            # What was covered and how it was set up, and the opinion the
            # evidence points to with the partner's recorded judgments.
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

    def export_record(self, actor: str, engagement_id: str) -> dict:
        """The engagement record as one JSON packet, at any time, unsigned.

        Each export is journaled with its digest, so the journal says which
        record left the Workbench, when and by whom. The packet's own digests
        let anyone check it is internally consistent (see the packet's
        limits for what they do not prove)."""
        from assurance_workpapers.packet import packet_digest, seal_packet
        packet = seal_packet(self._packet_body(engagement_id))
        digest = packet_digest(packet)

        def handler(uow):
            uow.emit(entity_type="evidence_packet", entity_id=engagement_id,
                     event_type="export.record",
                     payload={"packet_digest": digest, "exporter": actor},
                     engagement_id=engagement_id)
            return {"packet_digest": digest}
        run_command(self._conn,
                    self._command(actor, "export.record", engagement_id),
                    handler)
        return packet

    def workpaper_html(self, actor: str, engagement_id: str) -> str:
        """The working paper, rendered from the record as it stands now."""
        from assurance_workpapers.workpaper import render_workpaper
        from assurance_workpapers.packet import seal_packet
        return render_workpaper(seal_packet(self._packet_body(engagement_id)))

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
            version = extraction.get("recipe_version") or recipe.version
            if version != recipe.version:
                raise ValueError(
                    f"this spec was read with {recipe.report} recipe version "
                    f"{version!r}; this build reads it as {recipe.version!r}. "
                    f"Map and confirm the file again")
            headers, rows, source_rows, report = quickbooks.apply(
                recipe.recipe_id, headers, rows, resolved["header_row"] + 1)
            resolved.update(recipe=recipe.recipe_id,
                            recipe_version=recipe.version,
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
        # Without a General Ledger export, the loaded trial balance can give
        # the ledger side (the accounts named in ap_control_accounts).
        if "Trial_balance" in self._tables(engagement_id):
            ledger.append({"artifact_id": TB_LEDGER,
                           "original_name": "the loaded trial balance "
                                            "(A/P control accounts setting)"})
        return {"subledger": subledger, "ledger": ledger}

    def build_ap_control_balance(self, actor: str, engagement_id: str, *,
                                 subledger_artifact_id: str,
                                 ledger_artifact_id: str) -> dict:
        """Prepare the AP control balance schedule from two QuickBooks exports.

        The subledger balance is Unpaid Bills' grand-total open balance; the
        ledger balance is the Accounts Payable account's ending balance in
        the General Ledger export. Both are footed first, and a report that
        does not foot is refused. The schedule is stored as an ordinary
        source file whose provenance names both exports by SHA-256, then is
        mapped, confirmed and loaded like any other file.
        """
        self._require_open(engagement_id)
        books = {b["artifact_id"]: b for b in self._qbo_workbooks(engagement_id)}
        sub = books.get(subledger_artifact_id)
        if ledger_artifact_id == TB_LEDGER:
            gl = self._tb_ledger(engagement_id)
        else:
            gl = books.get(ledger_artifact_id)
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
        ledger = (gl["balance"] if ledger_artifact_id == TB_LEDGER
                  else quickbooks.gl_account_balance(gl["rows"]))
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
        notes = [gl["note"]] if gl.get("note") else []
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

    def trial_balance_candidates(self, engagement_id: str) -> dict:
        """Uploaded QuickBooks Trial Balance exports, with the date each is as of."""
        out = []
        for book in self._qbo_workbooks(engagement_id):
            if any(m["recipe"] == TB_RECIPE for m in quickbooks.recognize(book["rows"])):
                block = quickbooks.title_block(book["rows"])
                out.append({"artifact_id": book["artifact_id"],
                            "original_name": book["original_name"],
                            "as_of": quickbooks.last_date(block["period"]),
                            "period": block["period"]})
        return {"trial_balances": out}

    def build_trial_balance(self, actor: str, engagement_id: str, *,
                            current_artifact_id: str,
                            prior_artifact_id: str | None = None) -> dict:
        """Prepare the trial balance from QuickBooks Trial Balance exports:
        this period's, and optionally the prior period's for the comparative
        column. QuickBooks exports one date per report, so the two are joined
        by account here. Each export is footed against its TOTAL first and a
        report that does not foot is refused. The schedule is stored as an
        ordinary source file whose provenance names both exports by SHA-256,
        then is mapped and loaded like any other file.
        """
        self._require_open(engagement_id)
        books = {b["artifact_id"]: b for b in self._qbo_workbooks(engagement_id)}
        chosen = {"current": books.get(current_artifact_id)}
        if prior_artifact_id:
            chosen["prior"] = books.get(prior_artifact_id)
        if any(b is None for b in chosen.values()):
            raise KeyError("the trial balances must be .xlsx exports in this engagement")
        read: dict[str, dict] = {}
        for side, book in chosen.items():
            if not any(m["recipe"] == TB_RECIPE for m in quickbooks.recognize(book["rows"])):
                raise ValueError(f"{book['original_name']!r} is not QuickBooks' standard "
                                 f"Trial Balance export")
            extraction, headers, rows = xlsx.extract(book["content"], sheet=book["sheet"])
            _, flat, _, report = quickbooks.apply(TB_RECIPE, headers, rows,
                                                  extraction["header_row"] + 1)
            if report["totals_disagreeing"]:
                raise ValueError(f"{book['original_name']!r} does not foot: "
                                 f"{report['totals_disagreeing']}")
            block = quickbooks.title_block(book["rows"])
            read[side] = {"rows": flat, "report": report,
                          "as_of": quickbooks.last_date(block["period"]),
                          "period": block["period"], "book": book}
        period_end = self._conn.execute(
            "SELECT period_end FROM engagement WHERE engagement_id = ?",
            (engagement_id,)).fetchone()["period_end"]
        notes = []
        if read["current"]["as_of"] != period_end:
            notes.append(f"this period's trial balance is as of "
                         f"{read['current']['as_of'] or read['current']['period']!r}, "
                         f"not the engagement's period end {period_end}")
        if "prior" in read:
            cur, pri = read["current"]["as_of"], read["prior"]["as_of"]
            if not (cur and pri and pri < cur):
                raise ValueError(f"the prior trial balance ({pri or 'undated'}) must be "
                                 f"dated before this period's ({cur or 'undated'})")
            expected = _year_before(cur)
            if pri != expected:
                notes.append(f"the prior trial balance is as of {pri}, not one year "
                             f"before ({expected})")
        schedule = quickbooks.combine_trial_balances(
            read["current"]["rows"], read["prior"]["rows"] if "prior" in read else None)
        columns = ["Account", "Description", "Balance"] + (
            ["Prior Balance"] if "prior" in read else [])
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(columns)
        for item in schedule:
            writer.writerow([item[c] for c in columns])
        provenance = json.dumps({
            "prepared_by": "noesi build_trial_balance",
            "recipe": TB_RECIPE, "recipe_version": quickbooks.get(TB_RECIPE).version,
            **{side: {"artifact_id": r["book"]["artifact_id"],
                      "sha256": r["book"]["sha256"], "as_of": r["as_of"],
                      "grand_total": r["report"]["grand_total"]}
               for side, r in read.items()},
            "notes": notes,
        }, sort_keys=True)
        artifact = self.store_source(
            actor, engagement_id, content=buffer.getvalue().encode("utf-8"),
            media_type="text/csv",
            original_name=f"Trial balance {read['current']['as_of']} - QuickBooks.csv",
            provenance=provenance)
        return {**artifact, "as_of": read["current"]["as_of"],
                "prior_as_of": read.get("prior", {}).get("as_of"),
                "accounts": len(schedule), "notes": notes}

    def _tb_ledger(self, engagement_id: str) -> dict:
        """The A/P ledger balance from the loaded trial balance: the credit
        balance of the accounts the team named in ap_control_accounts. Every
        row of a named account counts (an account may appear in more than one
        loaded file); a named account with no balance is refused. A trial
        balance carries no date of its own, so the schedule says so rather than
        claim one. Shaped like a ledger for the builder."""
        document, _ = self.workflow_document(engagement_id)
        named = [a.strip() for a in str((document.get("policies") or {})
                                        .get("ap_control_accounts") or "")
                 .replace(";", ",").split(",") if a.strip()]
        if not named:
            raise ValueError("set 'ap_control_accounts' on Scope & Policies: the trial "
                             "balance accounts that hold accounts payable")
        table = self._tables(engagement_id).get("Trial_balance")
        if table is None:
            raise KeyError("no trial balance is loaded")
        from procedures_cycles.common import key_text
        from procedures_cycles.statements import _signed
        rows: dict[str, list[dict]] = {}
        for r in table.engine_view().records:
            rows.setdefault(key_text(r.get("account")), []).append(r)
        missing = [a for a in named if key_text(a) not in rows]
        if missing:
            raise ValueError(f"the trial balance has no account {', '.join(missing)}")
        debit_positive = Decimal("0")
        for a in named:
            for r in rows[key_text(a)]:
                amount = _signed(r)
                if amount is None:
                    raise ValueError(f"trial balance account {a} has a row with no balance")
                debit_positive += amount
        period_end = self._conn.execute(
            "SELECT period_end FROM engagement WHERE engagement_id = ?",
            (engagement_id,)).fetchone()["period_end"]
        digests = [d["output_digest"] for d in self.sources(engagement_id)["datasets"]
                   if d["role"] == "Trial_balance"]
        return {"artifact_id": TB_LEDGER, "sha256": ";".join(digests),
                "original_name": "trial balance (loaded)",
                "note": (f"the trial balance carries no date of its own: confirm it is "
                         f"the one as of {period_end}"),
                "balance": {"as_of": period_end, "ending": str(-debit_positive),
                            "period": f"taken as of {period_end} (not stated in the file)",
                            "basis": "trial balance", "account": ", ".join(named),
                            "beginning": None, "activity": None,
                            "checks": {"accounts": named, "datasets": digests}}}

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
        user to check, cached per file (stored files never change)."""
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

    def _refuse_repeated_entries(self, table: NormalizedTable, in_use) -> None:
        """Journal procedures group lines by entry, so an entry already in use
        would silently gain this file's lines: an overlapping or re-exported
        Journal would double-count and every doubled entry would still balance."""
        loaded: dict[str, str] = {}
        for dataset in in_use:
            name = self._dataset_file(dataset)
            for record in self._verified_table(dataset).records:
                loaded.setdefault(str(record.get("entry_id") or ""), name)
        repeated = sorted({str(r.get("entry_id") or "") for r in table.records}
                          & (loaded.keys() - {""}))
        if repeated:
            shown = "; ".join(f"{e} (in {loaded[e]})" for e in repeated[:3])
            more = f" and {len(repeated) - 3} more" if len(repeated) > 3 else ""
            raise ValueError(
                f"cannot add this file to {table.role}: {len(repeated)} of its "
                f"entries are already loaded: {shown}{more}. Adding would "
                f"merge their lines and double-count them. If this file covers "
                f"the same period, load it as a replacement instead")

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


def _year_before(iso: str) -> str:
    """The same date a year earlier; a month end maps to that month's end, so
    a February year end compares 2025-02-28 with 2024-02-29 (and back)."""
    from datetime import date, timedelta
    day = date.fromisoformat(iso)
    month_end = (day + timedelta(days=1)).day == 1
    if month_end:
        following = date(day.year - 1 + day.month // 12, day.month % 12 + 1, 1)
        return (following - timedelta(days=1)).isoformat()
    return date(day.year - 1, day.month, day.day).isoformat()


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
