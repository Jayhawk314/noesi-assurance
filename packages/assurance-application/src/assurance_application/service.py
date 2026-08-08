# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
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
import io
import json
import sqlite3
from decimal import Decimal

from assurance_artifacts.intake import store_artifact
from assurance_artifacts.vault import ArtifactVault
from assurance_domain.commands import Command
from assurance_domain.errors import ConflictError, NotFoundError
from assurance_domain.identities import new_id
from assurance_domain.lifecycle import SeparationOfDutiesError
from assurance_domain.jobs import build_manifest, run_job
from assurance_domain.readiness import blank_engagement, readiness
from assurance_domain.sad import (
    TRIVIAL_PCT, requires_concurrence, summary_of_differences,
)
from assurance_persistence.spine import run_command
from procedures_ap.coverage import compile_coverage, inventory_from_tables
from procedures_ap.engines import ENGINE_VERSION, execute_procedure
from procedures_ap.ingest import (
    MappingSpec, NormalizedTable, infer_role, normalize_table, propose_mapping,
)


class AuthorizationError(PermissionError):
    """The authenticated principal lacks the role this action requires."""


def _finding_uid(verdict: dict) -> str:
    """Engagement-scoped stable finding identity: domain + key, no company."""
    return f"{verdict['domain']}|{json.dumps(verdict['key'], ensure_ascii=False)}"


class EngagementLockedError(PermissionError):
    """The engagement is locked; its record can no longer change."""


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
        if self._engagement(engagement_id)["status"] == "locked":
            raise EngagementLockedError(
                "the engagement is locked; unlock (with supersession) before "
                "changing its record")

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

    def list_engagements(self) -> list[dict]:
        rows = self._conn.execute(
            """SELECT engagement_id, client_name, period_end, status, version
               FROM engagement WHERE tenant_id = ?
               ORDER BY client_name, period_end""", (self._tenant,)).fetchall()
        return [dict(row) for row in rows]

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
                               role: str, artifact_id: str) -> dict:
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer")
        headers, _ = self._artifact_rows(artifact_id)
        artifact = self._conn.execute(
            "SELECT sha256 FROM artifact WHERE artifact_id = ?",
            (artifact_id,)).fetchone()
        spec = propose_mapping(role, headers, source_sha256=artifact["sha256"],
                               proposed_by=actor)

        def handler(uow):
            spec_id = uow.mappings.propose(
                engagement_id, role=role, spec=spec.to_dict(),
                spec_digest=spec.digest, proposed_by=actor,
                artifact_id=artifact_id)
            return {"spec_id": spec_id, "column_map": spec.column_map,
                    "unmapped_headers": list(spec.unmapped_headers),
                    "refused_fields": list(spec.refused_fields)}
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
                         spec_id: str) -> dict:
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer")
        table = self._rebuild_table(spec_id)

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
                output_digest=table.output_digest)
            return {"dataset_id": dataset_id,
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
        proposal for the reviewer). Artifacts that already carry an active
        spec are skipped, so 'propose all' is safe to repeat."""
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer")
        active = {row["artifact_id"] for row in self._conn.execute(
            """SELECT artifact_id FROM mapping_spec
               WHERE engagement_id = ? AND status != 'superseded'""",
            (engagement_id,))}
        results = []
        for item in items:
            artifact_id = str(item.get("artifact_id") or "")
            entry: dict = {"artifact_id": artifact_id}
            try:
                if artifact_id in active:
                    entry.update(status="skipped",
                                 reason="an active mapping spec already "
                                        "exists for this artifact")
                else:
                    role = str(item.get("role") or "")
                    if not role:
                        name = self._conn.execute(
                            "SELECT original_name FROM artifact "
                            "WHERE artifact_id = ?",
                            (artifact_id,)).fetchone()
                        if name is None:
                            raise KeyError(f"artifact {artifact_id}")
                        role = infer_role(name["original_name"]) or ""
                    if not role:
                        raise ValueError(
                            "no role given and none inferable from the "
                            "filename; choose the role explicitly")
                    entry.update(self.propose_source_mapping(
                        actor, engagement_id, role=role,
                        artifact_id=artifact_id))
                    entry.update(status="proposed", role=role)
                    active.add(artifact_id)
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
                          spec_ids: list[str]) -> dict:
        """Batch normalize approved specs. Specs that already produced a
        dataset are skipped rather than re-recorded."""
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
                        actor, engagement_id, str(spec_id)))
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
                   WHERE engagement_id = ? ORDER BY created_at""",
                (engagement_id,)):
            item = dict(row)
            item["inferred_role"] = infer_role(item["original_name"])
            artifacts.append(item)
        specs = []
        for row in self._conn.execute(
                """SELECT spec_id, role, artifact_id, spec, status,
                   proposed_by, approved_by, created_at FROM mapping_spec
                   WHERE engagement_id = ? ORDER BY created_at""",
                (engagement_id,)):
            item = dict(row)
            stored = json.loads(item.pop("spec"))
            item["column_map"] = stored.get("column_map", {})
            item["unmapped_headers"] = stored.get("unmapped_headers", [])
            item["refused_fields"] = stored.get("refused_fields", [])
            specs.append(item)
        datasets = [dict(row) for row in self._conn.execute(
            """SELECT dataset_id, role, mapping_spec_id, artifact_id, rows_in,
               rows_loaded, rows_rejected, control_total, output_digest,
               created_at FROM normalized_dataset
               WHERE engagement_id = ? ORDER BY created_at""",
            (engagement_id,))]
        return {"artifacts": artifacts, "mapping_specs": specs,
                "datasets": datasets}

    # --------------------------------------------- screen 3: coverage

    def coverage(self, engagement_id: str) -> dict:
        tables = self._tables(engagement_id)
        document, _ = self.workflow_document(engagement_id)
        return compile_coverage(inventory_from_tables(tables),
                                policies=document.get("policies") or None)

    # ---------------------------------------- screen 4: runs and findings

    def run_procedure(self, actor: str, engagement_id: str, *,
                      procedure_id: str,
                      policies: dict | None = None) -> dict:
        self._require_unlocked(engagement_id)
        self._require(engagement_id, actor, "preparer")
        tables = {role: list(t.engine_view().records)
                  for role, t in self._tables(engagement_id).items()}
        # Approved engagement policies (workflow document) apply to every
        # run; explicit per-run values override them. Coverage compiles
        # against the same document, so what coverage calls executable is
        # what the run actually receives.
        document, _ = self.workflow_document(engagement_id)
        effective_policies = {**(document.get("policies") or {}),
                              **(policies or {})}
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
            engine_version=ENGINE_VERSION, tables=tables,
            policies=effective_policies, rerun_sequence=rerun_sequence)
        bundle = run_job(manifest, tables, execute_procedure)

        def handler(uow):
            run_id = uow.runs.record(
                engagement_id, procedure_id=procedure_id,
                job_id=manifest.job_id,
                manifest={"input_tables": manifest.input_tables,
                          "policies": manifest.policies,
                          "engine_version": manifest.engine_version},
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
               ORDER BY created_at, run_id""", (engagement_id,)).fetchall()
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
        clearly_trivial = TRIVIAL_PCT * (
            Decimal(str(document["materiality"].get("amount") or 0)))
        out = []
        for run in self._conn.execute(
                """SELECT run_id, procedure_id, status, findings
                   FROM procedure_run WHERE engagement_id = ?
                   ORDER BY created_at, run_id""", (engagement_id,)):
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
            document["materiality"].update({
                "amount": float(values.get("amount", 0)),
                "basis": str(values.get("basis", "")),
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
        elif section == "procedure_selection":
            from procedures_ap.contracts import CONTRACTS_BY_ID
            procedure_id = str(values["procedure_id"])
            if procedure_id not in CONTRACTS_BY_ID:
                raise ValueError(f"unknown procedure {procedure_id!r}")
            document.setdefault("procedures", {})[procedure_id] = {
                "selected": bool(values.get("selected", True)),
                "rationale": str(values.get("rationale", ""))}
        elif section == "policy":
            from procedures_ap.contracts import OPTIONAL_POLICIES, PROCEDURES
            name = str(values["name"])
            known = {policy for contract in PROCEDURES
                     for policy in contract.required_policies}
            known.update(OPTIONAL_POLICIES)
            if name not in known:
                raise ValueError(f"unknown policy {name!r}")
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
        if materiality is None:
            document, _ = self.workflow_document(engagement_id)
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
            rows.append({
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
        summary = summary_of_differences(rows, materiality=materiality)
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
        summary["concurrence_pending_count"] = len(pending)
        if pending:
            summary["conclusion"] = None
        return summary

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

        datasets = self._conn.execute(
            "SELECT COUNT(*) c FROM normalized_dataset WHERE engagement_id = ?",
            (engagement_id,)).fetchone()["c"]
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

    def _lock_manifest(self, engagement_id: str, query) -> dict:
        """Deterministic snapshot of every entity the lock covers.

        A re-lock names its predecessor: the superseded snapshot's digest and
        the documented reason ride inside the new manifest, so the partner's
        signature covers the amendment record itself (AU-C 230's reason /
        who / when for changes after assembly). A first lock has no such
        section and keeps the original v1 byte shape.
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
            "schema": "noesi-lock-manifest-v1",
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
            engagement_id, self._conn.execute)
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
        from procedures_ap.contracts import PROCEDURES

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
                   ORDER BY created_at, run_id""", (engagement_id,)):
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
        for contract in PROCEDURES:
            if contract.procedure_id in executed:
                continue
            decision = selections.get(contract.procedure_id, {})
            reason = ("deselected: " + decision.get("rationale", "")
                      if decision.get("selected") is False
                      else "not executed before lock")
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
            "lock": {
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
            },
            "lock_history": lock_history,
            "runs": runs,
            "procedures_not_run": not_run,
            "dispositions": dispositions,
            "summary_of_audit_differences": self.sad(engagement_id),
            "limits": PACKET_LIMITS,
        }
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
        from assurance_workpapers.workpaper import render_workpaper
        return render_workpaper(self.export_packet(actor, engagement_id))

    # ------------------------------------------------------------ helpers

    def _engagement(self, engagement_id: str) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT * FROM engagement WHERE engagement_id = ? AND tenant_id = ?",
            (engagement_id, self._tenant)).fetchone()
        if row is None:
            raise KeyError(f"engagement {engagement_id}")
        return row

    def _artifact_rows(self, artifact_id: str) -> tuple[list[str], list[dict]]:
        artifact = self._conn.execute(
            "SELECT sha256, state FROM artifact WHERE artifact_id = ?",
            (artifact_id,)).fetchone()
        if artifact is None:
            raise KeyError(f"artifact {artifact_id}")
        if artifact["state"] != "promoted":
            raise ValueError("artifact is retired; its content is gone")
        content = self._vault.read_bytes(artifact["sha256"])
        # Refuse with instructions rather than mis-parse: Excel workbooks
        # (xlsx = zip, legacy xls = OLE) are common uploads and would
        # otherwise decode into one garbage header row. The original bytes
        # stay in the vault as evidence either way.
        if content[:4] == b"PK\x03\x04" or content[:4] == b"\xd0\xcf\x11\xe0":
            raise ValueError(
                "this artifact is an Excel workbook, not CSV; export the "
                "sheet as CSV and upload that (the original workbook stays "
                "in the evidence vault)")
        text = content.decode("utf-8-sig", errors="replace")
        rows = list(csv.DictReader(text.splitlines()))
        headers = list(rows[0].keys()) if rows else []
        return headers, rows

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
        _, rows = self._artifact_rows(spec_row["artifact_id"])
        artifact_name = self._conn.execute(
            "SELECT original_name FROM artifact WHERE artifact_id = ?",
            (spec_row["artifact_id"],)).fetchone()["original_name"]
        return normalize_table(rows, spec, source_file=artifact_name)

    def _tables(self, engagement_id: str) -> dict:
        """Latest normalized dataset per role, rebuilt and digest-verified."""
        tables: dict[str, NormalizedTable] = {}
        for dataset in self._conn.execute(
                """SELECT * FROM normalized_dataset WHERE engagement_id = ?
                   ORDER BY created_at, dataset_id""", (engagement_id,)):
            table = self._rebuild_table(dataset["mapping_spec_id"])
            if table.output_digest != dataset["output_digest"]:
                raise RuntimeError(
                    f"dataset {dataset['dataset_id']} no longer reproduces its "
                    "recorded digest; refusing to serve unverifiable data")
            tables[dataset["role"]] = table
        return tables


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
