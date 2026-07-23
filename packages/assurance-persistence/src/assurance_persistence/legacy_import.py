"""One-time import of noesi-cpa JSON state into the transactional spine.

Reads the prototype's ``engagement_workflow.json``, global
``dispositions.json``, and ``trail.jsonl``, and lands them in one
transaction under opaque UUID identities.

Known legacy defect handled explicitly: disposition finding IDs are
``company|domain|key`` with no fiscal period. When one company has several
imported periods, the same legacy disposition is copied into *each* period's
scope — that reproduces the prototype's effective behavior (one shared
judgment visible everywhere) while finally making the copies independently
editable. Every such copy carries a ``migration_note`` so reviewers can see
it needs re-confirmation per period.

The import command_id is derived from the input bytes, so re-running the
tool against the same files replays the stored report instead of
duplicating state.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from assurance_domain.commands import Command
from assurance_domain.identities import new_id

from assurance_persistence.database import utcnow
from assurance_persistence.spine import CommandOutcome, UnitOfWork, run_command

LEGACY_STATUSES = ("cleared", "unadjusted", "adjusted", "waived", "follow_up")


def _read_json(path: str | Path | None) -> dict:
    if path is None:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_lines(path: str | Path | None) -> list[str]:
    if path is None:
        return []
    return [line for line in
            Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def ensure_tenant(conn: sqlite3.Connection, name: str) -> str:
    row = conn.execute("SELECT tenant_id FROM tenant WHERE name = ?",
                       (name,)).fetchone()
    if row is not None:
        return row["tenant_id"]
    tenant_id = new_id()
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            "INSERT INTO tenant (tenant_id, name, created_at) VALUES (?, ?, ?)",
            (tenant_id, name, utcnow()))
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    return tenant_id


def import_legacy(conn: sqlite3.Connection, *, tenant_id: str, actor: str,
                  workflow_path: str | Path,
                  dispositions_path: str | Path | None = None,
                  trail_path: str | Path | None = None) -> CommandOutcome:
    workflow_doc = _read_json(workflow_path)
    dispositions = _read_json(dispositions_path)
    trail_lines = _read_lines(trail_path)

    fingerprint = hashlib.sha256(json.dumps(
        [workflow_doc, dispositions, trail_lines],
        sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")).hexdigest()
    command = Command(
        command_id=f"legacy-import|{fingerprint}", tenant_id=tenant_id,
        actor=actor, kind="legacy.import",
        payload={"schema_version": workflow_doc.get("schema_version", "")})

    def handler(uow: UnitOfWork) -> dict:
        return _import(uow, workflow_doc, dispositions, trail_lines)

    return run_command(conn, command, handler)


def _import(uow: UnitOfWork, workflow_doc: dict, dispositions: dict,
            trail_lines: list[str]) -> dict:
    engagement_ids: dict[str, str] = {}   # legacy "company|fye" -> UUID
    by_company: dict[str, list[str]] = {}  # company -> [legacy keys]

    for legacy_key, record in sorted(
            (workflow_doc.get("engagements") or {}).items()):
        company = str(record.get("company") or legacy_key.rsplit("|", 1)[0])
        fye = str(record.get("fye")
                  or (legacy_key.rsplit("|", 1)[1] if "|" in legacy_key else "undated"))
        engagement_id = uow.engagements.create(company, fye)
        uow.workflows.put(engagement_id, record, expected_version=0)
        uow.emit(entity_type="engagement", entity_id=engagement_id,
                 event_type="legacy.engagement_imported",
                 payload={"legacy_key": legacy_key},
                 engagement_id=engagement_id)
        engagement_ids[legacy_key] = engagement_id
        by_company.setdefault(company, []).append(legacy_key)

    imported, ambiguous, unmatched, skipped = 0, [], [], []
    for fid, record in sorted(dispositions.items()):
        status = record.get("status", "")
        if status not in LEGACY_STATUSES:
            skipped.append({"finding_id": fid, "status": status})
            continue
        company = fid.split("|", 1)[0]
        targets = by_company.get(company, [])
        if not targets:
            unmatched.append(fid)
            continue
        note = ("copied to every period of this company during migration; "
                "legacy IDs had no period, so per-period re-confirmation is "
                "required") if len(targets) > 1 else "imported from legacy state"
        if len(targets) > 1:
            ambiguous.append({"finding_id": fid, "periods": sorted(targets)})
        for legacy_key in targets:
            uow.dispositions.set(
                engagement_ids[legacy_key], fid, status,
                note=record.get("note", ""), migration_note=note)
            imported += 1

    for index, line in enumerate(trail_lines):
        uow.emit(entity_type="legacy_trail", entity_id=f"line-{index}",
                 event_type="legacy.trail_entry",
                 payload={"index": index, "entry": line},
                 engagement_id=None)

    return {
        "schema_version": workflow_doc.get("schema_version", ""),
        "engagements": engagement_ids,
        "dispositions_imported": imported,
        "dispositions_ambiguous": ambiguous,
        "dispositions_unmatched": sorted(unmatched),
        "dispositions_skipped": skipped,
        "trail_entries_imported": len(trail_lines),
    }
