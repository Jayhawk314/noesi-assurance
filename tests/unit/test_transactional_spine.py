# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Phase 1 spine: atomicity, idempotency, optimistic versions, isolation."""

import pytest

from assurance_domain.commands import Command
from assurance_domain.errors import ConflictError
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from assurance_persistence.spine import run_command


@pytest.fixture()
def conn(tmp_path):
    connection = connect(tmp_path / "control.db")
    migrate(connection)
    yield connection
    connection.close()


@pytest.fixture()
def tenant(conn):
    return ensure_tenant(conn, "test-firm")


def _command(tenant, kind="test.command", command_id=None, engagement_id=None):
    return Command(command_id=command_id or f"cmd-{kind}", tenant_id=tenant,
                   actor="principal-1", kind=kind, engagement_id=engagement_id)


def _create_engagement(conn, tenant, client="Acme", period="2025-12-31",
                       command_id=None):
    outcome = run_command(
        conn, _command(tenant, "engagement.create",
                       command_id or f"create-{client}-{period}"),
        lambda uow: {"engagement_id": uow.engagements.create(client, period)})
    return outcome.result["engagement_id"]


def test_migrate_is_idempotent(tmp_path):
    connection = connect(tmp_path / "m.db")
    assert migrate(connection) == [1, 2, 3, 4, 5, 6, 7]
    assert migrate(connection) == []
    connection.close()


def test_command_commits_state_event_outbox_and_receipt_together(conn, tenant):
    engagement_id = _create_engagement(conn, tenant)
    assert conn.execute("SELECT COUNT(*) c FROM engagement").fetchone()["c"] == 1
    event = conn.execute(
        "SELECT * FROM domain_event WHERE event_type = 'engagement.created'"
    ).fetchone()
    assert event["engagement_id"] == engagement_id
    assert event["actor"] == "principal-1"
    assert conn.execute(
        "SELECT COUNT(*) c FROM outbox WHERE event_seq = ?",
        (event["event_seq"],)).fetchone()["c"] == 1
    assert conn.execute(
        "SELECT COUNT(*) c FROM idempotency").fetchone()["c"] == 1


def test_failed_handler_rolls_back_everything(conn, tenant):
    def handler(uow):
        uow.engagements.create("Acme", "2025-12-31")
        raise RuntimeError("crash after partial work")

    with pytest.raises(RuntimeError):
        run_command(conn, _command(tenant, "engagement.create", "boom"), handler)
    for table in ("engagement", "domain_event", "outbox", "idempotency"):
        assert conn.execute(
            f"SELECT COUNT(*) c FROM {table}").fetchone()["c"] == 0, table


def test_replayed_command_returns_stored_result_without_side_effects(conn, tenant):
    first = _create_engagement(conn, tenant, command_id="same-command")
    calls = []

    def handler(uow):
        calls.append(1)
        return {"engagement_id": uow.engagements.create("Acme", "2025-12-31")}

    outcome = run_command(
        conn, _command(tenant, "engagement.create", "same-command"), handler)
    assert outcome.replayed is True
    assert outcome.result["engagement_id"] == first
    assert calls == []  # handler never re-ran
    assert conn.execute("SELECT COUNT(*) c FROM engagement").fetchone()["c"] == 1


def test_optimistic_version_conflict_raises(conn, tenant):
    engagement_id = _create_engagement(conn, tenant)
    run_command(
        conn, _command(tenant, "engagement.lock", "lock-1", engagement_id),
        lambda uow: {"version": uow.engagements.set_status(
            engagement_id, "locked", expected_version=1)})
    with pytest.raises(ConflictError):
        run_command(
            conn, _command(tenant, "engagement.lock", "lock-stale", engagement_id),
            lambda uow: {"version": uow.engagements.set_status(
                engagement_id, "archived", expected_version=1)})
    row = conn.execute("SELECT status, version FROM engagement").fetchone()
    assert (row["status"], row["version"]) == ("locked", 2)


def test_workflow_state_uses_optimistic_versions(conn, tenant):
    engagement_id = _create_engagement(conn, tenant)
    run_command(
        conn, _command(tenant, "workflow.save", "wf-1", engagement_id),
        lambda uow: {"version": uow.workflows.put(
            engagement_id, {"stage": "planning"}, expected_version=0)})
    with pytest.raises(ConflictError):
        run_command(
            conn, _command(tenant, "workflow.save", "wf-stale", engagement_id),
            lambda uow: {"version": uow.workflows.put(
                engagement_id, {"stage": "late"}, expected_version=0)})


def test_dispositions_are_isolated_per_engagement(conn, tenant):
    """The P0 fix: the legacy xfail in noesi-cpa must pass here by construction.

    Same client, same finding identity, two periods — independent judgments.
    """
    fy2024 = _create_engagement(conn, tenant, period="2024-12-31")
    fy2025 = _create_engagement(conn, tenant, period="2025-12-31")
    finding_uid = "Acme|audit_procedure_run|['tie', 'x']"  # legacy-shaped, shared

    def disposer(engagement_id, status, cid):
        return run_command(
            conn, _command(tenant, "disposition.set", cid, engagement_id),
            lambda uow: {"version": uow.dispositions.set(
                engagement_id, finding_uid, status)})

    disposer(fy2024, "unadjusted", "d-2024")
    disposer(fy2025, "cleared", "d-2025")

    rows = {row["engagement_id"]: row["status"] for row in conn.execute(
        "SELECT engagement_id, status FROM disposition")}
    assert rows == {fy2024: "unadjusted", fy2025: "cleared"}
