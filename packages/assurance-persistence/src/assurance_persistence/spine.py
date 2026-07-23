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
