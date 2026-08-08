"""The transactional spine: one command, one transaction, or nothing.

``run_command`` wraps a handler so that its domain changes, append-only
events, outbox records, and idempotency receipt commit atomically. A replayed
command_id returns the stored result without re-executing the handler.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Callable

from assurance_domain.commands import Command
from assurance_domain.errors import ConflictError, NotFoundError
from assurance_domain.identities import new_id

from assurance_persistence.database import utcnow


@dataclass(frozen=True)
class CommandOutcome:
    result: dict
    replayed: bool


def event_entry_hash(prev_hash: str, tenant_id: str, engagement_id: str | None,
                     command_id: str, actor: str, entity_type: str,
                     entity_id: str, event_type: str,
                     before_version: int | None, after_version: int | None,
                     payload_json: str, created_at: str) -> str:
    """Chain hash of one journal entry over its full content."""
    import hashlib
    content = json.dumps(
        [prev_hash, tenant_id, engagement_id, command_id, actor, entity_type,
         entity_id, event_type, before_version, after_version, payload_json,
         created_at],
        ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def verify_journal(conn: sqlite3.Connection) -> dict:
    """Walk the journal in order; recompute every chained hash.

    Events older than migration 4 carry empty hashes; the chain (and the
    verification) starts at the first hashed event.
    """
    checked = 0
    prev_hash = ""
    started = False
    for row in conn.execute(
            "SELECT * FROM domain_event ORDER BY event_seq"):
        if not row["entry_hash"] and not started:
            continue  # pre-chain prefix
        started = True
        expected = event_entry_hash(
            prev_hash if checked else row["prev_hash"],
            row["tenant_id"], row["engagement_id"], row["command_id"],
            row["actor"], row["entity_type"], row["entity_id"],
            row["event_type"], row["before_version"], row["after_version"],
            row["payload"], row["created_at"])
        if expected != row["entry_hash"] or (
                checked and row["prev_hash"] != prev_hash):
            return {"ok": False, "checked": checked,
                    "break_at_seq": row["event_seq"]}
        prev_hash = row["entry_hash"]
        checked += 1
    return {"ok": True, "checked": checked, "break_at_seq": None}


def journal_head(conn: sqlite3.Connection) -> tuple[int, str]:
    row = conn.execute(
        "SELECT event_seq, entry_hash FROM domain_event "
        "ORDER BY event_seq DESC LIMIT 1").fetchone()
    return (row["event_seq"], row["entry_hash"]) if row else (0, "")


class UnitOfWork:
    """Repositories and event emission bound to one open transaction."""

    def __init__(self, conn: sqlite3.Connection, command: Command):
        self._conn = conn
        self.command = command
        self.engagements = EngagementRepository(self)
        self.workflows = WorkflowStateRepository(self)
        self.dispositions = DispositionRepository(self)
        self.artifacts = ArtifactRepository(self)
        self.mappings = MappingSpecRepository(self)
        self.datasets = DatasetRepository(self)
        self.principals = PrincipalRepository(self)
        self.runs = ProcedureRunRepository(self)
        self.snapshots = LockSnapshotRepository(self)

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def emit(self, *, entity_type: str, entity_id: str, event_type: str,
             before_version: int | None = None, after_version: int | None = None,
             payload: dict | None = None,
             engagement_id: str | None = None) -> int:
        """Append a hash-chained domain event and its outbox row."""
        scope = engagement_id if engagement_id is not None \
            else self.command.engagement_id
        body = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)
        created = utcnow()
        head = self.execute(
            "SELECT entry_hash FROM domain_event "
            "ORDER BY event_seq DESC LIMIT 1").fetchone()
        prev_hash = head["entry_hash"] if head is not None else ""
        entry_hash = event_entry_hash(
            prev_hash, self.command.tenant_id, scope, self.command.command_id,
            self.command.actor, entity_type, entity_id, event_type,
            before_version, after_version, body, created)
        cursor = self.execute(
            """INSERT INTO domain_event (tenant_id, engagement_id, command_id,
               actor, entity_type, entity_id, event_type, before_version,
               after_version, payload, created_at, prev_hash, entry_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (self.command.tenant_id, scope, self.command.command_id,
             self.command.actor, entity_type, entity_id, event_type,
             before_version, after_version, body, created,
             prev_hash, entry_hash))
        event_seq = cursor.lastrowid
        self.execute(
            "INSERT INTO outbox (event_seq, topic, payload, created_at) VALUES (?, ?, ?, ?)",
            (event_seq, event_type, body, utcnow()))
        return event_seq


def run_command(conn: sqlite3.Connection, command: Command,
                handler: Callable[[UnitOfWork], dict]) -> CommandOutcome:
    """Execute a command exactly once inside a single transaction."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT result FROM idempotency WHERE command_id = ?",
            (command.command_id,)).fetchone()
        if row is not None:
            conn.execute("COMMIT")
            return CommandOutcome(json.loads(row["result"]), replayed=True)
        uow = UnitOfWork(conn, command)
        result = handler(uow)
        if not isinstance(result, dict):
            raise TypeError("command handlers must return a JSON-safe dict")
        conn.execute(
            "INSERT INTO idempotency (command_id, kind, result, created_at) VALUES (?, ?, ?, ?)",
            (command.command_id, command.kind,
             json.dumps(result, ensure_ascii=False, sort_keys=True), utcnow()))
        conn.execute("COMMIT")
        return CommandOutcome(result, replayed=False)
    except BaseException:
        conn.execute("ROLLBACK")
        raise


class EngagementRepository:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def create(self, client_name: str, period_end: str) -> str:
        engagement_id = new_id()
        self._uow.execute(
            """INSERT INTO engagement (engagement_id, tenant_id, client_name,
               period_end, created_at) VALUES (?, ?, ?, ?, ?)""",
            (engagement_id, self._uow.command.tenant_id, client_name,
             period_end, utcnow()))
        self._uow.emit(
            entity_type="engagement", entity_id=engagement_id,
            event_type="engagement.created", after_version=1,
            payload={"client_name": client_name, "period_end": period_end},
            engagement_id=engagement_id)
        return engagement_id

    def get(self, engagement_id: str) -> sqlite3.Row:
        row = self._uow.execute(
            "SELECT * FROM engagement WHERE engagement_id = ? AND tenant_id = ?",
            (engagement_id, self._uow.command.tenant_id)).fetchone()
        if row is None:
            raise NotFoundError(f"engagement {engagement_id}")
        return row

    def set_status(self, engagement_id: str, status: str,
                   expected_version: int) -> int:
        cursor = self._uow.execute(
            """UPDATE engagement SET status = ?, version = version + 1
               WHERE engagement_id = ? AND tenant_id = ? AND version = ?""",
            (status, engagement_id, self._uow.command.tenant_id,
             expected_version))
        if cursor.rowcount == 0:
            raise ConflictError("engagement", engagement_id, expected_version)
        self._uow.emit(
            entity_type="engagement", entity_id=engagement_id,
            event_type="engagement.status_changed",
            before_version=expected_version, after_version=expected_version + 1,
            payload={"status": status}, engagement_id=engagement_id)
        return expected_version + 1


class WorkflowStateRepository:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def get(self, engagement_id: str) -> tuple[dict, int]:
        row = self._uow.execute(
            "SELECT payload, version FROM workflow_state WHERE engagement_id = ?",
            (engagement_id,)).fetchone()
        if row is None:
            return {}, 0
        return json.loads(row["payload"]), row["version"]

    def put(self, engagement_id: str, payload: dict, expected_version: int) -> int:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if expected_version == 0:
            try:
                self._uow.execute(
                    """INSERT INTO workflow_state (engagement_id, payload, version,
                       updated_at) VALUES (?, ?, 1, ?)""",
                    (engagement_id, body, utcnow()))
            except sqlite3.IntegrityError as exc:
                # A row already exists: the caller's view (version 0) is stale.
                raise ConflictError("workflow_state", engagement_id, 0) from exc
            after = 1
        else:
            cursor = self._uow.execute(
                """UPDATE workflow_state SET payload = ?, version = version + 1,
                   updated_at = ? WHERE engagement_id = ? AND version = ?""",
                (body, utcnow(), engagement_id, expected_version))
            if cursor.rowcount == 0:
                raise ConflictError("workflow_state", engagement_id,
                                    expected_version)
            after = expected_version + 1
        self._uow.emit(
            entity_type="workflow_state", entity_id=engagement_id,
            event_type="workflow.saved", before_version=expected_version or None,
            after_version=after, payload={"bytes": len(body)},
            engagement_id=engagement_id)
        return after


class DispositionRepository:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def set(self, engagement_id: str, finding_uid: str, status: str,
            note: str = "", expected_version: int = 0,
            migration_note: str = "", proposed_by: str = "") -> int:
        # A set (or re-set) is the proposer's judgment: any prior
        # concurrence is void, because it concurred with a different one.
        if expected_version == 0:
            try:
                self._uow.execute(
                    """INSERT INTO disposition (tenant_id, engagement_id,
                       finding_uid, status, note, migration_note,
                       proposed_by, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (self._uow.command.tenant_id, engagement_id, finding_uid,
                     status, note, migration_note, proposed_by, utcnow()))
            except sqlite3.IntegrityError as exc:
                raise ConflictError("disposition",
                                    f"{engagement_id}/{finding_uid}", 0) from exc
            after = 1
        else:
            cursor = self._uow.execute(
                """UPDATE disposition SET status = ?, note = ?,
                   proposed_by = ?, concurred_by = '',
                   version = version + 1, updated_at = ?
                   WHERE engagement_id = ? AND finding_uid = ? AND version = ?""",
                (status, note, proposed_by, utcnow(), engagement_id,
                 finding_uid, expected_version))
            if cursor.rowcount == 0:
                raise ConflictError("disposition",
                                    f"{engagement_id}/{finding_uid}",
                                    expected_version)
            after = expected_version + 1
        self._uow.emit(
            entity_type="disposition", entity_id=finding_uid,
            event_type="disposition.set",
            before_version=expected_version or None, after_version=after,
            payload={"status": status, "note": note,
                     "proposed_by": proposed_by},
            engagement_id=engagement_id)
        return after

    def concur(self, engagement_id: str, finding_uid: str, *,
               concurred_by: str, expected_version: int) -> int:
        """A second person concurs with the proposed disposition.

        Separation is enforced against the recorded proposer, exactly as
        mapping approval enforces it against the mapping's proposer.
        """
        from assurance_domain.lifecycle import require_separation
        row = self._uow.execute(
            """SELECT status, proposed_by FROM disposition
               WHERE engagement_id = ? AND finding_uid = ?""",
            (engagement_id, finding_uid)).fetchone()
        if row is None:
            raise NotFoundError(f"disposition {engagement_id}/{finding_uid}")
        require_separation(prepared_by=row["proposed_by"],
                           approved_by=concurred_by)
        cursor = self._uow.execute(
            """UPDATE disposition SET concurred_by = ?,
               version = version + 1, updated_at = ?
               WHERE engagement_id = ? AND finding_uid = ? AND version = ?""",
            (concurred_by, utcnow(), engagement_id, finding_uid,
             expected_version))
        if cursor.rowcount == 0:
            raise ConflictError("disposition",
                                f"{engagement_id}/{finding_uid}",
                                expected_version)
        self._uow.emit(
            entity_type="disposition", entity_id=finding_uid,
            event_type="disposition.concurred",
            before_version=expected_version,
            after_version=expected_version + 1,
            payload={"status": row["status"], "concurred_by": concurred_by},
            engagement_id=engagement_id)
        return expected_version + 1

    def list_for(self, engagement_id: str) -> list[sqlite3.Row]:
        return self._uow.execute(
            "SELECT * FROM disposition WHERE engagement_id = ? ORDER BY finding_uid",
            (engagement_id,)).fetchall()


class ArtifactRepository:
    """Immutable artifact manifests; retirement is a one-way tombstone."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def register(self, engagement_id: str, *, sha256: str, size_bytes: int,
                 media_type: str, original_name: str,
                 provenance: str = "", retention_class: str = "engagement",
                 ) -> str:
        artifact_id = new_id()
        try:
            self._uow.execute(
                """INSERT INTO artifact (artifact_id, tenant_id, engagement_id,
                   sha256, size_bytes, media_type, original_name, provenance,
                   retention_class, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (artifact_id, self._uow.command.tenant_id, engagement_id,
                 sha256, size_bytes, media_type, original_name, provenance,
                 retention_class, utcnow()))
        except sqlite3.IntegrityError as exc:
            raise ConflictError(
                "artifact", f"{engagement_id}/{sha256}", 0) from exc
        self._uow.emit(
            entity_type="artifact", entity_id=artifact_id,
            event_type="artifact.registered", after_version=1,
            payload={"sha256": sha256, "size_bytes": size_bytes,
                     "media_type": media_type, "original_name": original_name},
            engagement_id=engagement_id)
        return artifact_id

    def get(self, artifact_id: str) -> sqlite3.Row:
        row = self._uow.execute(
            "SELECT * FROM artifact WHERE artifact_id = ? AND tenant_id = ?",
            (artifact_id, self._uow.command.tenant_id)).fetchone()
        if row is None:
            raise NotFoundError(f"artifact {artifact_id}")
        return row

    def retire(self, artifact_id: str, reason: str) -> None:
        cursor = self._uow.execute(
            """UPDATE artifact SET state = 'retired', retired_at = ?,
               retire_reason = ? WHERE artifact_id = ? AND tenant_id = ?
               AND state = 'promoted'""",
            (utcnow(), reason, artifact_id, self._uow.command.tenant_id))
        if cursor.rowcount == 0:
            raise ConflictError("artifact", artifact_id, 1)
        self._uow.emit(
            entity_type="artifact", entity_id=artifact_id,
            event_type="artifact.retired", payload={"reason": reason})


class MappingSpecRepository:
    """Durable reviewed-transformation objects: proposed, then approved."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def propose(self, engagement_id: str, *, role: str, spec: dict,
                spec_digest: str, proposed_by: str,
                artifact_id: str | None = None) -> str:
        spec_id = new_id()
        self._uow.execute(
            """INSERT INTO mapping_spec (spec_id, tenant_id, engagement_id,
               role, artifact_id, spec, spec_digest, proposed_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (spec_id, self._uow.command.tenant_id, engagement_id, role,
             artifact_id, json.dumps(spec, ensure_ascii=False, sort_keys=True),
             spec_digest, proposed_by, utcnow()))
        self._uow.emit(
            entity_type="mapping_spec", entity_id=spec_id,
            event_type="mapping.proposed", after_version=1,
            payload={"role": role, "spec_digest": spec_digest,
                     "proposed_by": proposed_by},
            engagement_id=engagement_id)
        return spec_id

    def approve(self, spec_id: str, *, approved_by: str) -> None:
        from assurance_domain.lifecycle import require_separation
        row = self._uow.execute(
            "SELECT proposed_by, status FROM mapping_spec "
            "WHERE spec_id = ? AND tenant_id = ?",
            (spec_id, self._uow.command.tenant_id)).fetchone()
        if row is None:
            raise NotFoundError(f"mapping_spec {spec_id}")
        # Enforced server-side, never a UI nicety.
        require_separation(prepared_by=row["proposed_by"],
                           approved_by=approved_by)
        cursor = self._uow.execute(
            """UPDATE mapping_spec SET status = 'approved', approved_by = ?,
               approved_at = ? WHERE spec_id = ? AND status = 'proposed'""",
            (approved_by, utcnow(), spec_id))
        if cursor.rowcount == 0:
            raise ConflictError("mapping_spec", spec_id, 1)
        self._uow.emit(
            entity_type="mapping_spec", entity_id=spec_id,
            event_type="mapping.approved",
            payload={"approved_by": approved_by})

    def get(self, spec_id: str) -> sqlite3.Row:
        row = self._uow.execute(
            "SELECT * FROM mapping_spec WHERE spec_id = ? AND tenant_id = ?",
            (spec_id, self._uow.command.tenant_id)).fetchone()
        if row is None:
            raise NotFoundError(f"mapping_spec {spec_id}")
        return row


class DatasetRepository:
    """Normalization receipts: what came in, what loaded, what was rejected."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def record(self, engagement_id: str, *, role: str, mapping_spec_id: str,
               artifact_id: str, rows_in: int, rows_loaded: int,
               rows_rejected: int, control_total: str | None,
               output_digest: str) -> str:
        dataset_id = new_id()
        self._uow.execute(
            """INSERT INTO normalized_dataset (dataset_id, tenant_id,
               engagement_id, role, mapping_spec_id, artifact_id, rows_in,
               rows_loaded, rows_rejected, control_total, output_digest,
               created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (dataset_id, self._uow.command.tenant_id, engagement_id, role,
             mapping_spec_id, artifact_id, rows_in, rows_loaded,
             rows_rejected, control_total, output_digest, utcnow()))
        self._uow.emit(
            entity_type="normalized_dataset", entity_id=dataset_id,
            event_type="dataset.normalized", after_version=1,
            payload={"role": role, "rows_in": rows_in,
                     "rows_loaded": rows_loaded,
                     "rows_rejected": rows_rejected,
                     "control_total": control_total,
                     "output_digest": output_digest},
            engagement_id=engagement_id)
        return dataset_id

    def list_for(self, engagement_id: str) -> list[sqlite3.Row]:
        return self._uow.execute(
            """SELECT * FROM normalized_dataset WHERE engagement_id = ?
               ORDER BY created_at, dataset_id""",
            (engagement_id,)).fetchall()


class PrincipalRepository:
    """Engagement role assignments: the only authorization input."""

    ROLES = ("preparer", "reviewer", "partner")

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def assign(self, engagement_id: str, principal_id: str, role: str) -> None:
        if role not in self.ROLES:
            raise ValueError(f"unknown role {role!r}")
        try:
            self._uow.execute(
                """INSERT INTO principal_assignment (tenant_id, engagement_id,
                   principal_id, role, assigned_by, assigned_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (self._uow.command.tenant_id, engagement_id, principal_id,
                 role, self._uow.command.actor, utcnow()))
        except sqlite3.IntegrityError as exc:
            raise ConflictError(
                "principal_assignment",
                f"{engagement_id}/{principal_id}/{role}", 0) from exc
        self._uow.emit(
            entity_type="principal_assignment",
            entity_id=f"{principal_id}/{role}",
            event_type="team.assigned",
            payload={"principal_id": principal_id, "role": role},
            engagement_id=engagement_id)

    def roles_for(self, engagement_id: str, principal_id: str) -> set[str]:
        rows = self._uow.execute(
            """SELECT role FROM principal_assignment
               WHERE engagement_id = ? AND principal_id = ?""",
            (engagement_id, principal_id)).fetchall()
        return {row["role"] for row in rows}

    def team(self, engagement_id: str) -> list[sqlite3.Row]:
        return self._uow.execute(
            """SELECT principal_id, role, assigned_at
               FROM principal_assignment WHERE engagement_id = ?
               ORDER BY role, principal_id""",
            (engagement_id,)).fetchall()

    def any_assigned(self, engagement_id: str) -> bool:
        return self._uow.execute(
            "SELECT 1 FROM principal_assignment WHERE engagement_id = ? LIMIT 1",
            (engagement_id,)).fetchone() is not None


class ProcedureRunRepository:
    """Immutable run receipts walking one review lifecycle."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def record(self, engagement_id: str, *, procedure_id: str, job_id: str,
               manifest: dict, status: str, summary: dict,
               findings: list[dict], error: str,
               result_digest: str) -> str:
        if status not in ("completed", "error"):
            raise ValueError("a new run is 'completed' or 'error', never reviewed")
        run_id = new_id()
        try:
            self._uow.execute(
                """INSERT INTO procedure_run (run_id, tenant_id, engagement_id,
                   procedure_id, job_id, manifest, status, summary, findings,
                   error, result_digest, executed_by, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, self._uow.command.tenant_id, engagement_id,
                 procedure_id, job_id,
                 json.dumps(manifest, ensure_ascii=False, sort_keys=True),
                 status,
                 json.dumps(summary, ensure_ascii=False, sort_keys=True),
                 json.dumps(findings, ensure_ascii=False),
                 error, result_digest, self._uow.command.actor, utcnow()))
        except sqlite3.IntegrityError as exc:
            raise ConflictError(
                "procedure_run", f"{engagement_id}/{job_id}", 0) from exc
        self._uow.emit(
            entity_type="procedure_run", entity_id=run_id,
            event_type="run.recorded", after_version=1,
            payload={"procedure_id": procedure_id, "job_id": job_id,
                     "status": status, "result_digest": result_digest},
            engagement_id=engagement_id)
        return run_id

    def get(self, run_id: str) -> sqlite3.Row:
        row = self._uow.execute(
            "SELECT * FROM procedure_run WHERE run_id = ? AND tenant_id = ?",
            (run_id, self._uow.command.tenant_id)).fetchone()
        if row is None:
            raise NotFoundError(f"procedure_run {run_id}")
        return row

    def list_for(self, engagement_id: str) -> list[sqlite3.Row]:
        return self._uow.execute(
            """SELECT * FROM procedure_run WHERE engagement_id = ?
               ORDER BY created_at, run_id""",
            (engagement_id,)).fetchall()

    def advance_review(self, run_id: str, target: str, *,
                       expected_version: int) -> int:
        """Move a run along completed -> reviewed -> approved.

        Transition legality comes from the domain state machine; separation
        (executor may not review, reviewer may not approve their own review)
        is enforced here, server-side.
        """
        from assurance_domain.lifecycle import advance, require_separation
        row = self.get(run_id)
        advance("procedure_run", row["status"], target)
        actor = self._uow.command.actor
        if target == "reviewed":
            require_separation(prepared_by=row["executed_by"],
                               approved_by=actor)
            extra_sql, extra_val = "reviewed_by = ?", actor
        elif target == "approved":
            require_separation(prepared_by=row["reviewed_by"],
                               approved_by=actor)
            extra_sql, extra_val = "approved_by = ?", actor
        else:
            raise ValueError(f"review can only reach reviewed/approved, not {target!r}")
        cursor = self._uow.execute(
            f"""UPDATE procedure_run SET status = ?, {extra_sql},
               version = version + 1 WHERE run_id = ? AND version = ?""",
            (target, extra_val, run_id, expected_version))
        if cursor.rowcount == 0:
            raise ConflictError("procedure_run", run_id, expected_version)
        self._uow.emit(
            entity_type="procedure_run", entity_id=run_id,
            event_type=f"run.{target}", before_version=expected_version,
            after_version=expected_version + 1,
            payload={"by": actor}, engagement_id=row["engagement_id"])
        return expected_version + 1


class LockSnapshotRepository:
    """Frozen lock manifests and the signatures bound to them."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def record(self, engagement_id: str, *, manifest: dict, digest: str,
               journal_head_seq: int, journal_head_hash: str) -> str:
        snapshot_id = new_id()
        sequence = self._uow.execute(
            """SELECT COALESCE(MAX(sequence), 0) + 1 AS seq
               FROM lock_snapshot WHERE engagement_id = ?""",
            (engagement_id,)).fetchone()["seq"]
        try:
            self._uow.execute(
                """INSERT INTO lock_snapshot (snapshot_id, tenant_id,
                   engagement_id, sequence, manifest, digest,
                   journal_head_seq, journal_head_hash, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)""",
                (snapshot_id, self._uow.command.tenant_id, engagement_id,
                 sequence,
                 json.dumps(manifest, ensure_ascii=False, sort_keys=True),
                 digest, journal_head_seq, journal_head_hash, utcnow()))
        except sqlite3.IntegrityError as exc:
            # The partial unique index: an active lock already exists.
            raise ConflictError("lock_snapshot", engagement_id, 0) from exc
        self._uow.emit(
            entity_type="lock_snapshot", entity_id=snapshot_id,
            event_type="lock.snapshot_recorded", after_version=sequence,
            payload={"digest": digest, "journal_head_seq": journal_head_seq,
                     "sequence": sequence},
            engagement_id=engagement_id)
        return snapshot_id

    def supersede(self, engagement_id: str, *, actor: str,
                  reason: str) -> dict:
        """Retire the active lock in place — nothing is deleted, ever.

        The reason, actor, and timestamp ride the journal event, so the
        amendment record itself is inside the hash chain.
        """
        row = self._uow.execute(
            """SELECT snapshot_id, sequence, digest FROM lock_snapshot
               WHERE engagement_id = ? AND status = 'active'""",
            (engagement_id,)).fetchone()
        if row is None:
            raise NotFoundError(
                f"no active lock snapshot for engagement {engagement_id}")
        self._uow.execute(
            """UPDATE lock_snapshot SET status = 'superseded',
               superseded_at = ?, superseded_by = ?, supersede_reason = ?
               WHERE snapshot_id = ?""",
            (utcnow(), actor, reason, row["snapshot_id"]))
        self._uow.emit(
            entity_type="lock_snapshot", entity_id=row["snapshot_id"],
            event_type="lock.superseded",
            before_version=row["sequence"], after_version=row["sequence"],
            payload={"digest": row["digest"], "sequence": row["sequence"],
                     "reason": reason, "superseded_by": actor},
            engagement_id=engagement_id)
        return {"snapshot_id": row["snapshot_id"],
                "sequence": row["sequence"], "digest": row["digest"]}

    def sign(self, snapshot_id: str, *, engagement_id: str,
             signer_principal: str, key_id: str, algorithm: str,
             public_key_pem: str, signature_hex: str) -> str:
        signature_id = new_id()
        self._uow.execute(
            """INSERT INTO lock_signature (signature_id, snapshot_id,
               signer_principal, key_id, algorithm, public_key_pem,
               signature_hex, signed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (signature_id, snapshot_id, signer_principal, key_id,
             algorithm, public_key_pem, signature_hex, utcnow()))
        self._uow.emit(
            entity_type="lock_signature", entity_id=signature_id,
            event_type="lock.signed", after_version=1,
            payload={"snapshot_id": snapshot_id, "key_id": key_id,
                     "algorithm": algorithm,
                     "signer_principal": signer_principal},
            engagement_id=engagement_id)
        return signature_id
