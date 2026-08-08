# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Legacy import: UUID identities, explicit ambiguity handling, idempotency."""

import json

import pytest

from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant, import_legacy

LEGACY_WORKFLOW = {
    "schema_version": "legacy-workflow-v1",
    "engagements": {
        "Acme|2024-12-31": {"company": "Acme", "fye": "2024-12-31",
                            "materiality": {"amount": 10000.0}},
        "Acme|2025-12-31": {"company": "Acme", "fye": "2025-12-31",
                            "materiality": {"amount": 12000.0}},
        "Zenith|2025-06-30": {"company": "Zenith", "fye": "2025-06-30",
                              "materiality": {"amount": 5000.0}},
    },
}

LEGACY_DISPOSITIONS = {
    # Period-ambiguous: Acme has two imported periods.
    "Acme|audit_procedure_run|['tie', 'x']": {
        "status": "unadjusted", "note": "client will not adjust"},
    # Unambiguous: Zenith has one period.
    "Zenith|audit_procedure_run|['match', 'v9']": {
        "status": "cleared", "note": "timing difference"},
    # Orphaned: no imported engagement for this company.
    "Ghost|audit_procedure_run|['x']": {"status": "cleared", "note": ""},
    # Unknown status: must be skipped, not guessed.
    "Acme|audit_procedure_run|['odd']": {"status": "mystery", "note": ""},
}

LEGACY_TRAIL = [
    json.dumps({"seq": 1, "action": "workflow_saved", "hash": "aa"}),
    json.dumps({"seq": 2, "action": "disposition_set", "hash": "bb"}),
]


@pytest.fixture()
def env(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    (tmp_path / "engagement_workflow.json").write_text(
        json.dumps(LEGACY_WORKFLOW), encoding="utf-8")
    (tmp_path / "dispositions.json").write_text(
        json.dumps(LEGACY_DISPOSITIONS), encoding="utf-8")
    (tmp_path / "trail.jsonl").write_text(
        "\n".join(LEGACY_TRAIL) + "\n", encoding="utf-8")
    yield conn, tmp_path
    conn.close()


def _run(conn, tmp_path):
    tenant = ensure_tenant(conn, "default")
    return import_legacy(
        conn, tenant_id=tenant, actor="migration-tool",
        workflow_path=tmp_path / "engagement_workflow.json",
        dispositions_path=tmp_path / "dispositions.json",
        trail_path=tmp_path / "trail.jsonl")


def test_import_assigns_opaque_ids_and_scopes_state(env):
    conn, tmp_path = env
    outcome = _run(conn, tmp_path)
    report = outcome.result

    ids = report["engagements"]
    assert set(ids) == set(LEGACY_WORKFLOW["engagements"])
    assert len(set(ids.values())) == 3  # distinct UUIDs, no legacy keys
    for legacy_key, engagement_id in ids.items():
        assert legacy_key not in engagement_id

    row = conn.execute(
        """SELECT e.client_name, e.period_end, w.payload FROM engagement e
           JOIN workflow_state w ON w.engagement_id = e.engagement_id
           WHERE e.period_end = '2024-12-31'""").fetchone()
    assert row["client_name"] == "Acme"
    assert json.loads(row["payload"])["materiality"]["amount"] == 10000.0


def test_ambiguous_dispositions_are_copied_and_flagged(env):
    conn, tmp_path = env
    report = _run(conn, tmp_path).result

    # 2 Acme copies + 1 Zenith = 3 imported rows.
    assert report["dispositions_imported"] == 3
    assert report["dispositions_unmatched"] == ["Ghost|audit_procedure_run|['x']"]
    assert report["dispositions_skipped"] == [
        {"finding_id": "Acme|audit_procedure_run|['odd']", "status": "mystery"}]
    assert len(report["dispositions_ambiguous"]) == 1
    assert report["dispositions_ambiguous"][0]["periods"] == [
        "Acme|2024-12-31", "Acme|2025-12-31"]

    acme_rows = conn.execute(
        """SELECT d.migration_note, e.period_end FROM disposition d
           JOIN engagement e ON e.engagement_id = d.engagement_id
           WHERE e.client_name = 'Acme'""").fetchall()
    assert len(acme_rows) == 2
    assert all("re-confirmation" in row["migration_note"] for row in acme_rows)

    zenith = conn.execute(
        """SELECT d.migration_note FROM disposition d
           JOIN engagement e ON e.engagement_id = d.engagement_id
           WHERE e.client_name = 'Zenith'""").fetchone()
    assert zenith["migration_note"] == "imported from legacy state"


def test_trail_is_preserved_in_order(env):
    conn, tmp_path = env
    report = _run(conn, tmp_path).result
    assert report["trail_entries_imported"] == 2
    entries = [json.loads(row["payload"])["entry"] for row in conn.execute(
        """SELECT payload FROM domain_event
           WHERE event_type = 'legacy.trail_entry' ORDER BY event_seq""")]
    assert entries == LEGACY_TRAIL


def test_reimport_replays_instead_of_duplicating(env):
    conn, tmp_path = env
    first = _run(conn, tmp_path)
    second = _run(conn, tmp_path)
    assert first.replayed is False
    assert second.replayed is True
    assert second.result == first.result
    assert conn.execute("SELECT COUNT(*) c FROM engagement").fetchone()["c"] == 3
    assert conn.execute("SELECT COUNT(*) c FROM disposition").fetchone()["c"] == 3
