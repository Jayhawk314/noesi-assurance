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

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def emit(self, *, entity_type: str, entity_id: str, event_type: str,
             before_version: int | None = None, after_version: int | None = None,
             payload: dict | None = None,
             engagement_id: str | None = None) -> int:
        """Append a domain event and its outbox row; returns the event_seq."""
        scope = engagement_id if engagement_id is not None \
            else self.command.engagement_id
        body = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)
        cursor = self.execute(
            """INSERT INTO domain_event (tenant_id, engagement_id, command_id,
               actor, entity_type, entity_id, event_type, before_version,
               after_version, payload, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (self.command.tenant_id, scope, self.command.command_id,
             self.command.actor, entity_type, entity_id, event_type,
             before_version, after_version, body, utcnow()))
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
            migration_note: str = "") -> int:
        if expected_version == 0:
            try:
                self._uow.execute(
                    """INSERT INTO disposition (tenant_id, engagement_id,
                       finding_uid, status, note, migration_note, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (self._uow.command.tenant_id, engagement_id, finding_uid,
                     status, note, migration_note, utcnow()))
            except sqlite3.IntegrityError as exc:
                raise ConflictError("disposition",
                                    f"{engagement_id}/{finding_uid}", 0) from exc
            after = 1
        else:
            cursor = self._uow.execute(
                """UPDATE disposition SET status = ?, note = ?,
                   version = version + 1, updated_at = ?
                   WHERE engagement_id = ? AND finding_uid = ? AND version = ?""",
                (status, note, utcnow(), engagement_id, finding_uid,
                 expected_version))
            if cursor.rowcount == 0:
                raise ConflictError("disposition",
                                    f"{engagement_id}/{finding_uid}",
                                    expected_version)
            after = expected_version + 1
        self._uow.emit(
            entity_type="disposition", entity_id=finding_uid,
            event_type="disposition.set",
            before_version=expected_version or None, after_version=after,
            payload={"status": status, "note": note},
            engagement_id=engagement_id)
        return after

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
