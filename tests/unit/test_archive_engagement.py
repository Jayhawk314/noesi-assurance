"""Archiving an engagement: partner only, with a reason, journaled, reversible."""
import pytest


@pytest.fixture
def svc(tmp_path):
    from assurance_application.service import WorkbenchService
    from assurance_artifacts.vault import ArtifactVault
    from assurance_persistence.database import connect, migrate
    from assurance_persistence.legacy_import import ensure_tenant
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "o"))
    conn.close()


def test_archived_engagements_leave_the_list_and_come_back_on_restore(svc):
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    svc.archive_engagement("pa", eid, reason="practice run, no longer needed")
    assert svc.list_engagements() == []
    assert [e["engagement_id"] for e in svc.list_engagements(archived=True)] == [eid]
    svc.restore_engagement("pa", eid)
    assert [e["status"] for e in svc.list_engagements()] == ["open"]


def test_only_the_partner_archives_and_a_reason_is_required(svc):
    from assurance_application.service import AuthorizationError
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    svc.assign_team("pa", eid, "prep", "preparer")
    with pytest.raises(AuthorizationError):
        svc.archive_engagement("prep", eid, reason="practice run, no longer needed")
    with pytest.raises(ValueError):
        svc.archive_engagement("pa", eid, reason="old")
    assert [e["engagement_id"] for e in svc.list_engagements()] == [eid]


def test_the_archive_is_journaled_with_who_and_why(svc):
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    svc.archive_engagement("pa", eid, reason="practice run, no longer needed")
    rows = svc._conn.execute(
        "SELECT actor, event_type, payload FROM domain_event WHERE engagement_id = ? "
        "AND event_type = 'engagement.archived'", (eid,)).fetchall()
    assert len(rows) == 1 and rows[0]["actor"] == "pa"
    assert "practice run" in rows[0]["payload"]


def test_archive_and_restore_leave_the_status_alone(svc):
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    svc.archive_engagement("pa", eid, reason="finished engagement, file away")
    assert svc._engagement(eid)["status"] == "open" and svc._engagement(eid)["archived_at"]
    svc.restore_engagement("pa", eid)
    assert svc._engagement(eid)["status"] == "open"
    assert svc._engagement(eid)["archived_at"] is None


def test_delete_removes_the_case_and_keeps_the_journal_chain_whole(svc):
    from assurance_persistence.spine import verify_journal
    keep = svc.create_engagement("pa", "Keep Co", "2025-12-31")["engagement_id"]
    gone = svc.create_engagement("pa", "Gone Co", "2025-12-31")["engagement_id"]
    svc.assign_team("pa", gone, "prep", "preparer")
    svc.store_source("prep", gone, content=b"a,b\n1,2\n", media_type="text/csv",
                     original_name="x.csv", provenance="test")
    sha = svc._conn.execute("SELECT sha256 FROM artifact WHERE engagement_id = ?", (gone,)).fetchone()[0]
    svc.delete_engagement("pa", gone, confirm_client_name="Gone Co", reason="loaded by mistake, remove")
    assert [e["engagement_id"] for e in svc.list_engagements()] == [keep]
    assert svc.list_engagements(archived=True) == []
    for table in ("engagement", "artifact", "principal_assignment"):
        assert svc._conn.execute(f"SELECT COUNT(*) FROM {table} WHERE engagement_id = ?", (gone,)).fetchone()[0] == 0
    assert not svc._vault.has_blob(sha)
    assert verify_journal(svc._conn)["ok"]
    row = svc._conn.execute("SELECT actor, payload FROM domain_event WHERE event_type = 'engagement.deleted'").fetchone()
    assert row["actor"] == "pa" and "loaded by mistake" in row["payload"]


def test_delete_needs_the_partner_and_the_exact_client_name(svc):
    from assurance_application.service import AuthorizationError
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    svc.assign_team("pa", eid, "prep", "preparer")
    with pytest.raises(ValueError):
        svc.delete_engagement("pa", eid, confirm_client_name="Acme Inc", reason="loaded by mistake, remove")
    with pytest.raises(AuthorizationError):
        svc.delete_engagement("prep", eid, confirm_client_name="Acme", reason="loaded by mistake, remove")
    assert len(svc.list_engagements()) == 1


def test_a_blob_shared_with_another_engagement_is_kept(svc):
    a = svc.create_engagement("pa", "A", "2025-12-31")["engagement_id"]
    b = svc.create_engagement("pa", "B", "2025-12-31")["engagement_id"]
    for eid in (a, b):
        svc.assign_team("pa", eid, "prep", "preparer")
        svc.store_source("prep", eid, content=b"same\n", media_type="text/csv", original_name="s.csv")
    sha = svc._conn.execute("SELECT sha256 FROM artifact WHERE engagement_id = ?", (b,)).fetchone()[0]
    svc.delete_engagement("pa", b, confirm_client_name="B", reason="duplicate practice copy")
    assert svc._vault.has_blob(sha)


def test_the_typed_name_ignores_case_and_spacing(svc):
    eid = svc.create_engagement("pa", "Kestrel Valley (demo)", "2025-12-31")["engagement_id"]
    svc.delete_engagement("pa", eid, confirm_client_name="  kestrel   valley (DEMO) ", reason="loaded by mistake, remove")
    assert svc.list_engagements() == []


def test_loading_an_archived_case_restores_it(svc):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "workbench-api"))
    from workbench_api import demo
    eid = svc.create_engagement("pa", demo.DEMO_CLIENT, demo.DEMO_PERIOD)["engagement_id"]
    svc.archive_engagement("pa", eid, reason="hide it for a while")
    out = demo.load_case(svc, "harborline", "pa")
    assert out == {"engagement_id": eid, "seeded": False, "restored": True}
    assert [e["engagement_id"] for e in svc.list_engagements()] == [eid]


def test_the_server_sends_dates_as_iso_text():
    import json, sys
    from datetime import date
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "workbench-api"))
    from workbench_api.server import _json_default
    assert json.dumps({"d": date(2026, 6, 30)}, default=_json_default) == '{"d": "2026-06-30"}'
