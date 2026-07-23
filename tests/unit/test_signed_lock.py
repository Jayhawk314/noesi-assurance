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


def test_snapshot_manifest_content_is_complete(service):
    eid, outcome = _green_locked(service)
    manifest = json.loads(service._conn.execute(
        "SELECT manifest FROM lock_snapshot").fetchone()["manifest"])
    assert manifest["schema"] == "noesi-lock-manifest-v1"
    assert manifest["engagement"]["status"] == "locked"
    assert manifest["workflow"]["version"] >= 1
    assert {m["role"] for m in manifest["team"]} == {"partner"}
    assert "does not prove" in manifest["limits"]
