# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Signed locking: chained journal, frozen manifests, verifiable signatures,
and a locked engagement that actually refuses change."""

import json

import pytest

from assurance_application.service import (
    EngagementLockedError, WorkbenchService,
)
from assurance_artifacts.signing import LocalKeyStore, verify_signature
from assurance_artifacts.vault import ArtifactVault
from assurance_domain.readiness import COMPLETION_CHECKS
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from assurance_persistence.spine import verify_journal

ALICE, BOB = "principal-alice", "principal-bob"


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    tenant = ensure_tenant(conn, "firm")
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), tenant,
                           keystore=LocalKeyStore(tmp_path / "keys"))
    conn.close()


def _green_locked(service):
    eid = service.create_engagement(ALICE, "Zenith", "2025-06-30")["engagement_id"]
    service.update_workflow(ALICE, eid, "materiality", {"amount": 10000.0})
    for stage in ("risk_assessment", "controls"):
        service.update_workflow(ALICE, eid, "stage",
                                {"name": stage, "status": "complete"})
    for check in COMPLETION_CHECKS:
        service.update_workflow(ALICE, eid, "completion",
                                {"name": check, "done": True, "note": "done"})
    # Data-less engagement: the partner owns the silence explicitly (3.4).
    service.update_workflow(ALICE, eid, "no_data_assertion",
                            {"asserted": True,
                             "reason": "keystore/lock unit fixture; no "
                                       "client data in scope"})
    outcome = service.lock(ALICE, eid, expected_version=1)
    assert outcome["locked"] is True
    return eid, outcome


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


def test_lock_produces_signed_verifiable_snapshot(service):
    eid, outcome = _green_locked(service)
    verification = service.verify_lock(eid)
    assert verification["verified"] is True
    assert verification["snapshot_ok"] is True
    assert verification["signature_ok"] is True
    assert verification["journal_ok"] is True
    assert verification["drift"] == []
    assert verification["signer"]["principal"] == ALICE
    assert verification["signer"]["algorithm"] == "ed25519"
    assert "does not prove" in verification["limits"]

    # The signature verifies from stored material alone.
    signature = service._conn.execute(
        "SELECT * FROM lock_signature").fetchone()
    assert verify_signature(signature["public_key_pem"], outcome["digest"],
                            signature["signature_hex"]) is True


def test_post_lock_tampering_is_named_section_by_section(service):
    eid, _ = _green_locked(service)
    # Sneak a disposition in behind the service's back.
    tenant = service._tenant
    service._conn.execute(
        """INSERT INTO disposition (tenant_id, engagement_id, finding_uid,
           status, note, updated_at) VALUES (?, ?, 'd|x', 'cleared', '',
           'later')""", (tenant, eid))
    verification = service.verify_lock(eid)
    assert verification["snapshot_ok"] is False
    assert verification["drift"] == ["dispositions"]
    assert verification["signature_ok"] is True  # the signature still binds
    assert verification["verified"] is False


def test_forged_signature_fails_verification(service):
    eid, _ = _green_locked(service)
    service._conn.execute(
        "UPDATE lock_signature SET signature_hex = ?",
        ("ab" * 64,))
    verification = service.verify_lock(eid)
    assert verification["signature_ok"] is False
    assert verification["verified"] is False


def test_locked_engagements_refuse_every_mutation(service):
    eid, _ = _green_locked(service)
    with pytest.raises(EngagementLockedError):
        service.update_workflow(ALICE, eid, "materiality", {"amount": 1.0})
    with pytest.raises(EngagementLockedError):
        service.assign_team(ALICE, eid, BOB, "preparer")
    with pytest.raises(EngagementLockedError):
        service.store_source(ALICE, eid, content=b"a,b\n1,2\n",
                             media_type="text/csv", original_name="x.csv")
    with pytest.raises(EngagementLockedError):
        service.set_disposition(ALICE, eid, finding_uid="d|x",
                                status="cleared")


def test_lock_requires_a_configured_keystore(tmp_path):
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    tenant = ensure_tenant(conn, "firm")
    service = WorkbenchService(conn, ArtifactVault(tmp_path / "v"), tenant)
    eid = service.create_engagement(ALICE, "Zenith", "2025-06-30")["engagement_id"]
    service.update_workflow(ALICE, eid, "materiality", {"amount": 1000.0})
    for stage in ("risk_assessment", "controls"):
        service.update_workflow(ALICE, eid, "stage",
                                {"name": stage, "status": "complete"})
    for check in COMPLETION_CHECKS:
        service.update_workflow(ALICE, eid, "completion",
                                {"name": check, "done": True, "note": "n"})
    service.update_workflow(ALICE, eid, "no_data_assertion",
                            {"asserted": True,
                             "reason": "keystore/lock unit fixture; no "
                                       "client data in scope"})
    with pytest.raises(RuntimeError, match="signing key store"):
        service.lock(ALICE, eid, expected_version=1)
    conn.close()


def test_keys_are_stable_per_principal_and_distinct_between_them(tmp_path):
    store = LocalKeyStore(tmp_path / "keys")
    first = store.identity(ALICE)
    again = store.identity(ALICE)
    other = store.identity(BOB)
    assert first.key_id == again.key_id
    assert first.key_id != other.key_id
    digest = "ab" * 32
    assert verify_signature(first.public_key_pem, digest,
                            store.sign(ALICE, digest))
    assert not verify_signature(other.public_key_pem, digest,
                                store.sign(ALICE, digest))


def test_unlock_requires_partner_and_a_specific_reason(service):
    eid, _ = _green_locked(service)
    with pytest.raises(ValueError, match="specific reason"):
        service.unlock(ALICE, eid, reason="oops", expected_version=2)
    with pytest.raises(Exception):  # AuthorizationError: BOB holds no role
        service.unlock(BOB, eid,
                       reason="A perfectly specific reason, wrong person.",
                       expected_version=2)
    with pytest.raises(ValueError, match="not locked"):
        other = service.create_engagement(
            ALICE, "OpenCo", "2025-12-31")["engagement_id"]
        service.unlock(ALICE, other,
                       reason="This engagement was never locked at all.",
                       expected_version=1)


def test_unlock_supersedes_and_relock_names_its_predecessor(service):
    eid, first = _green_locked(service)
    reason = ("Subsequent discovery of facts: client provided a corrected "
              "AP control balance after report release.")
    outcome = service.unlock(ALICE, eid, reason=reason, expected_version=2)
    assert outcome["unlocked"] is True
    assert outcome["superseded"]["sequence"] == 1

    # The engagement accepts change again, through the same gates.
    service.update_workflow(ALICE, eid, "materiality", {"amount": 12000.0})

    # While reopened: not locked, but the superseded lock still verifies
    # from stored material and carries the documented reason.
    verification = service.verify_lock(eid)
    assert verification["locked"] is False
    assert "reopened" in verification["error"]
    [item] = verification["history"]
    assert item["manifest_ok"] is True
    assert item["signature_ok"] is True
    assert item["journal_anchor_ok"] is True
    assert item["reason"] == reason
    assert item["unlocked_by"] == ALICE

    # Re-lock: a second signed snapshot that names its predecessor.
    relock = service.lock(ALICE, eid, expected_version=3)
    assert relock["locked"] is True
    assert relock["digest"] != first["digest"]
    verification = service.verify_lock(eid)
    assert verification["verified"] is True
    assert verification["sequence"] == 2
    assert len(verification["history"]) == 1

    manifest = json.loads(service._conn.execute(
        "SELECT manifest FROM lock_snapshot WHERE status = 'active'"
    ).fetchone()["manifest"])
    assert manifest["sequence"] == 2
    assert manifest["supersedes"]["digest"] == first["digest"]
    assert manifest["supersedes"]["reason"] == reason
    assert manifest["supersedes"]["unlocked_by"] == ALICE

    # Nothing was deleted: both snapshots and both signatures remain.
    assert service._conn.execute(
        "SELECT COUNT(*) c FROM lock_snapshot").fetchone()["c"] == 2
    assert service._conn.execute(
        "SELECT COUNT(*) c FROM lock_signature").fetchone()["c"] == 2


def test_export_after_relock_carries_verifiable_amendment_history(service):
    from assurance_workpapers.packet import verify_packet

    eid, _ = _green_locked(service)
    reason = ("Corrected subledger balance received after report release; "
              "reperforming the control-account tie.")
    service.unlock(ALICE, eid, reason=reason, expected_version=2)
    service.lock(ALICE, eid, expected_version=3)

    packet = service.export_packet(ALICE, eid)
    report = verify_packet(packet)
    assert report["verified"] is True
    assert report["lock_history_ok"] is True
    [item] = packet["lock_history"]
    assert item["reason"] == reason
    assert item["signature"]["signer_principal"] == ALICE
    assert packet["lock"]["manifest"]["supersedes"]["sequence"] == 1

    html_doc = service.workpaper_html(ALICE, eid)
    assert "Lock amendment history" in html_doc
    assert reason[:40] in html_doc

    # A tampered history signature is named, not absorbed.
    packet["lock_history"][0]["signature"]["signature_hex"] = "ab" * 64
    tampered = verify_packet(packet)
    assert tampered["lock_history_ok"] is False
    assert tampered["lock_history_failures"] == [1]


def test_migration_5_rebuilds_lock_tables_without_losing_locks(tmp_path,
                                                               monkeypatch):
    """A database locked under the one-lock schema upgrades losslessly.

    The legacy lock row is written with the old schema's own SQL — the
    current service cannot produce one — then migration 5 rebuilds both
    lock tables around it. Bytes, signature, and journal anchor must
    survive, and the row must join the supersession lifecycle.
    """
    from assurance_application.service import _manifest_digest
    from assurance_persistence import database as db
    from assurance_persistence.spine import journal_head

    monkeypatch.setattr(db, "MIGRATIONS", db.MIGRATIONS[:4])
    conn = db.connect(tmp_path / "upgrade.db")
    assert db.migrate(conn) == [1, 2, 3, 4]
    tenant = ensure_tenant(conn, "firm")
    service = WorkbenchService(conn, ArtifactVault(tmp_path / "vault"),
                               tenant, keystore=LocalKeyStore(tmp_path / "keys"))
    eid = service.create_engagement(
        ALICE, "Zenith", "2025-06-30")["engagement_id"]

    manifest = {"schema": "legacy-test-manifest", "engagement": eid}
    digest = _manifest_digest(manifest)
    head_seq, head_hash = journal_head(conn)
    store = LocalKeyStore(tmp_path / "keys")
    identity = store.identity(ALICE)
    conn.execute("BEGIN IMMEDIATE")
    conn.execute(
        """INSERT INTO lock_snapshot (snapshot_id, tenant_id, engagement_id,
           manifest, digest, journal_head_seq, journal_head_hash, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("snap-legacy", tenant, eid, json.dumps(manifest), digest,
         head_seq, head_hash, "2026-01-01T00:00:00+00:00"))
    conn.execute(
        """INSERT INTO lock_signature (signature_id, snapshot_id,
           signer_principal, key_id, algorithm, public_key_pem,
           signature_hex, signed_at)
           VALUES (?, ?, ?, ?, 'ed25519', ?, ?, ?)""",
        ("sig-legacy", "snap-legacy", ALICE, identity.key_id,
         identity.public_key_pem, store.sign(ALICE, digest),
         "2026-01-01T00:00:00+00:00"))
    conn.execute(
        "UPDATE engagement SET status = 'locked', version = 2 "
        "WHERE engagement_id = ?", (eid,))
    conn.execute("COMMIT")

    monkeypatch.undo()
    assert db.migrate(conn) == [5, 6]

    row = conn.execute("SELECT * FROM lock_snapshot").fetchone()
    assert (row["snapshot_id"], row["sequence"], row["status"]) == \
        ("snap-legacy", 1, "active")
    assert row["digest"] == digest
    assert json.loads(row["manifest"]) == manifest
    signature = conn.execute("SELECT * FROM lock_signature").fetchone()
    assert signature["snapshot_id"] == "snap-legacy"
    assert verify_signature(signature["public_key_pem"], digest,
                            signature["signature_hex"]) is True

    # The migrated row participates in the new lifecycle.
    outcome = service.unlock(
        ALICE, eid,
        reason="Reopened after migration to prove the row survived.",
        expected_version=2)
    assert outcome["superseded"]["snapshot_id"] == "snap-legacy"
    history = service.verify_lock(eid)["history"]
    assert history[0]["signature_ok"] is True
    assert history[0]["journal_anchor_ok"] is True
    conn.close()


def test_snapshot_manifest_content_is_complete(service):
    eid, outcome = _green_locked(service)
    manifest = json.loads(service._conn.execute(
        "SELECT manifest FROM lock_snapshot").fetchone()["manifest"])
    assert manifest["schema"] == "noesi-lock-manifest-v1"
    assert manifest["engagement"]["status"] == "locked"
    assert manifest["workflow"]["version"] >= 1
    assert {m["role"] for m in manifest["team"]} == {"partner"}
    assert "does not prove" in manifest["limits"]
