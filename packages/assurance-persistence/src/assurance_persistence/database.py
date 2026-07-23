"""SQLite control database: connection policy and migrations.

Pilot profile: one application process is the only writer. Autocommit is
disabled at the driver level; the spine issues explicit BEGIN IMMEDIATE /
COMMIT / ROLLBACK so a transaction's boundaries are always visible in code.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MIGRATIONS: tuple[tuple[int, str, str], ...] = (
    (1, "phase1-transactional-spine", """
CREATE TABLE tenant (
    tenant_id  TEXT PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE engagement (
    engagement_id TEXT PRIMARY KEY,
    tenant_id     TEXT NOT NULL REFERENCES tenant(tenant_id),
    client_name   TEXT NOT NULL,
    period_end    TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'open'
                  CHECK (status IN ('open', 'locked', 'archived')),
    version       INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL,
    UNIQUE (tenant_id, client_name, period_end)
);

-- Phase 1 carries the legacy workflow dict as one versioned document per
-- engagement; Phase 2 explodes it into typed entities and state machines.
CREATE TABLE workflow_state (
    engagement_id TEXT PRIMARY KEY REFERENCES engagement(engagement_id),
    payload       TEXT NOT NULL,
    version       INTEGER NOT NULL DEFAULT 1,
    updated_at    TEXT NOT NULL
);

-- Dispositions are engagement-scoped by construction: the primary key makes
-- the legacy cross-period collision structurally impossible.
CREATE TABLE disposition (
    tenant_id      TEXT NOT NULL REFERENCES tenant(tenant_id),
    engagement_id  TEXT NOT NULL REFERENCES engagement(engagement_id),
    finding_uid    TEXT NOT NULL,
    status         TEXT NOT NULL CHECK (status IN
                   ('cleared', 'unadjusted', 'adjusted', 'waived', 'follow_up')),
    note           TEXT NOT NULL DEFAULT '',
    version        INTEGER NOT NULL DEFAULT 1,
    migration_note TEXT NOT NULL DEFAULT '',
    updated_at     TEXT NOT NULL,
    PRIMARY KEY (engagement_id, finding_uid)
);

CREATE TABLE domain_event (
    event_seq      INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id      TEXT NOT NULL,
    engagement_id  TEXT,          -- NULL only for tenant-level/legacy-global events
    command_id     TEXT NOT NULL,
    actor          TEXT NOT NULL,
    entity_type    TEXT NOT NULL,
    entity_id      TEXT NOT NULL,
    event_type     TEXT NOT NULL,
    before_version INTEGER,
    after_version  INTEGER,
    payload        TEXT NOT NULL,
    created_at     TEXT NOT NULL
);
CREATE INDEX idx_event_engagement ON domain_event(engagement_id, event_seq);

CREATE TABLE outbox (
    outbox_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    event_seq     INTEGER NOT NULL REFERENCES domain_event(event_seq),
    topic         TEXT NOT NULL,
    payload       TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    dispatched_at TEXT
);

CREATE TABLE idempotency (
    command_id TEXT PRIMARY KEY,
    kind       TEXT NOT NULL,
    result     TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""),
    (2, "phase3-artifacts-and-mapping", """
-- Immutable artifact manifests. Bytes live in the vault, addressed by
-- sha256; the row is the authority on existence and retention. Retirement
-- is a tombstone, never a delete.
CREATE TABLE artifact (
    artifact_id     TEXT PRIMARY KEY,
    tenant_id       TEXT NOT NULL REFERENCES tenant(tenant_id),
    engagement_id   TEXT NOT NULL REFERENCES engagement(engagement_id),
    sha256          TEXT NOT NULL,
    size_bytes      INTEGER NOT NULL,
    media_type      TEXT NOT NULL,
    original_name   TEXT NOT NULL,
    provenance      TEXT NOT NULL DEFAULT '',
    state           TEXT NOT NULL DEFAULT 'promoted'
                    CHECK (state IN ('promoted', 'retired')),
    retention_class TEXT NOT NULL DEFAULT 'engagement',
    created_at      TEXT NOT NULL,
    retired_at      TEXT,
    retire_reason   TEXT NOT NULL DEFAULT '',
    UNIQUE (engagement_id, sha256)
);

-- Reviewed transformation model: a mapping is a durable object that is
-- proposed, then approved by a different principal, then consumed.
CREATE TABLE mapping_spec (
    spec_id       TEXT PRIMARY KEY,
    tenant_id     TEXT NOT NULL REFERENCES tenant(tenant_id),
    engagement_id TEXT NOT NULL REFERENCES engagement(engagement_id),
    role          TEXT NOT NULL,
    artifact_id   TEXT REFERENCES artifact(artifact_id),
    spec          TEXT NOT NULL,
    spec_digest   TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'proposed'
                  CHECK (status IN ('proposed', 'approved', 'superseded')),
    proposed_by   TEXT NOT NULL,
    approved_by   TEXT NOT NULL DEFAULT '',
    version       INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL,
    approved_at   TEXT
);

CREATE TABLE normalized_dataset (
    dataset_id      TEXT PRIMARY KEY,
    tenant_id       TEXT NOT NULL REFERENCES tenant(tenant_id),
    engagement_id   TEXT NOT NULL REFERENCES engagement(engagement_id),
    role            TEXT NOT NULL,
    mapping_spec_id TEXT NOT NULL REFERENCES mapping_spec(spec_id),
    artifact_id     TEXT NOT NULL REFERENCES artifact(artifact_id),
    rows_in         INTEGER NOT NULL,
    rows_loaded     INTEGER NOT NULL,
    rows_rejected   INTEGER NOT NULL,
    control_total   TEXT,
    output_digest   TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
"""),
)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def migrate(conn: sqlite3.Connection) -> list[int]:
    """Apply pending migrations; returns the versions applied. Idempotent."""
    conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)""")
    applied = {row["version"] for row in
               conn.execute("SELECT version FROM schema_migrations")}
    done = []
    for version, name, sql in MIGRATIONS:
        if version in applied:
            continue
        conn.execute("BEGIN IMMEDIATE")
        try:
            # Not executescript(): it implicitly COMMITs any open transaction,
            # which would break the atomicity of a failed migration. Comment
            # lines are stripped first so ';' inside them cannot split a
            # statement.
            bare = "\n".join(line for line in sql.splitlines()
                             if not line.lstrip().startswith("--"))
            for statement in bare.split(";"):
                if statement.strip():
                    conn.execute(statement)
            conn.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (version, name, utcnow()))
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        done.append(version)
    return done
