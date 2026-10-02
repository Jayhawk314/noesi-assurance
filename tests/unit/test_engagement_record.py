# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The engagement record: a hash-chained journal, and an unsigned export
whose own digests show it is internally consistent. Locks and signatures
were removed on 1 Oct 2026 (Noesi supplements an audit; it does not approve
one)."""

import json

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from assurance_persistence.spine import verify_journal
from assurance_workpapers.packet import PACKET_VERSION, verify_packet

ALICE, BOB = "principal-alice", "principal-bob"


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    tenant = ensure_tenant(conn, "firm")
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), tenant)
    conn.close()


def test_journal_is_hash_chained_and_verifies(service):
    service.create_engagement(ALICE, "Acme", "2025-12-31")
    report = verify_journal(service._conn)
    assert report["ok"] is True
    assert report["checked"] >= 2  # created + team.assigned at minimum
    rows = service._conn.execute(
        "SELECT prev_hash, entry_hash FROM domain_event ORDER BY event_seq"
    ).fetchall()
    assert rows[0]["prev_hash"] == ""
    assert rows[1]["prev_hash"] == rows[0]["entry_hash"]


def test_tampered_journal_breaks_verification_and_blocks_readiness(service):
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    service._conn.execute(
        "UPDATE domain_event SET payload = '{\"forged\":true}' "
        "WHERE event_seq = 1")
    report = verify_journal(service._conn)
    assert report["ok"] is False
    assert report["break_at_seq"] == 1
    state = service.readiness(eid)
    assert {"code": "DECISION_TRAIL_BROKEN", "count": 1} in state["blockers"]


def test_the_record_exports_any_time_and_checks_itself(service):
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    packet = service.export_record(ALICE, eid)
    assert packet["packet_version"] == PACKET_VERSION
    assert "lock" not in packet and "signature" not in json.dumps(packet["seal"])
    report = verify_packet(packet)
    assert report["verified"] is True, report
    assert "not signed" in report["limits"]
    # The export itself is journaled with its digest.
    event = service._conn.execute(
        "SELECT payload FROM domain_event WHERE event_type = 'export.record'"
    ).fetchone()
    assert json.loads(event["payload"])["packet_digest"] == packet["seal"]["packet_digest"]
    # The engagement stays open and changeable after an export.
    service.update_workflow(ALICE, eid, "materiality", {"amount": 5000.0})
    assert not hasattr(service, "lock") and not hasattr(service, "unlock")


def test_an_edited_record_fails_its_own_check(service):
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    packet = service.export_record(ALICE, eid)
    edited = json.loads(json.dumps(packet))
    edited["manifest"]["engagement"]["client_name"] = "Someone else"
    report = verify_packet(edited)
    assert report["verified"] is False
    assert report["manifest_ok"] is False and report["packet_digest_ok"] is False
    with pytest.raises(ValueError, match="noesi-evidence-packet-v3"):
        verify_packet({**packet, "packet_version": "noesi-evidence-packet-v3"})


def test_an_engagement_locked_before_the_removal_is_reopened(tmp_path):
    # Migration 12: nothing can unlock any more, so a locked engagement is
    # reopened; its old lock rows stay as history.
    path = tmp_path / "control.db"
    conn = connect(path)
    migrate(conn)
    conn.execute("DELETE FROM schema_migrations WHERE version = 12")
    tenant = ensure_tenant(conn, "firm")
    service = WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), tenant)
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    conn.execute("UPDATE engagement SET status = 'locked' WHERE engagement_id = ?", (eid,))
    assert migrate(conn) == [12]
    assert conn.execute("SELECT status FROM engagement WHERE engagement_id = ?",
                        (eid,)).fetchone()["status"] == "open"
    service.update_workflow(ALICE, eid, "materiality", {"amount": 5000.0})
    conn.close()
