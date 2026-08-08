# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Evidence packets: exported from a frozen verified lock, offline-verifiable,
tamper-naming; the workpaper renders every conclusion with its lineage."""

import json

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.signing import LocalKeyStore
from assurance_artifacts.vault import ArtifactVault
from assurance_domain.readiness import COMPLETION_CHECKS
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from assurance_workpapers.packet import verify_packet
from procedures_ap.contracts import PROCEDURES

ALICE, BOB, CAROL = "principal-alice", "principal-bob", "principal-carol"

PAYMENTS_CSV = (
    "Payment No,Invoice No,Vendor No,Amount,Payment Date\n"
    "P1,I1,V1,6000.00,2025-03-01\n"
    "P2,I2,V1,5000.00,2025-03-01\n"
    "P3,I3,V2,2000.00,2025-03-01\n"
).encode("utf-8")

BALANCES_CSV = (
    "Period End,Subledger Balance,GL Balance\n"
    "2025-12-31,125000.00,120000.00\n"
).encode("utf-8")


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    tenant = ensure_tenant(conn, "firm")
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), tenant,
                           keystore=LocalKeyStore(tmp_path / "keys"))
    conn.close()


@pytest.fixture()
def locked_engagement(service):
    """A fully worked engagement: data, runs, reviews, dispositions, lock."""
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    service.assign_team(ALICE, eid, BOB, "preparer")
    service.assign_team(ALICE, eid, CAROL, "reviewer")

    for content, name, role in ((PAYMENTS_CSV, "payments.csv", "Payments"),
                                (BALANCES_CSV, "recon.csv",
                                 "AP_control_balance")):
        artifact = service.store_source(BOB, eid, content=content,
                                        media_type="text/csv",
                                        original_name=name)
        proposal = service.propose_source_mapping(
            BOB, eid, role=role, artifact_id=artifact["artifact_id"])
        service.approve_source_mapping(CAROL, eid, proposal["spec_id"])
        service.normalize_source(BOB, eid, proposal["spec_id"])

    executed = {}
    for procedure_id, policies in (
            ("ap.split_payment_review", {"split_threshold": "10000"}),
            ("ap.subledger_gl_balance_tie", {})):
        run = service.run_procedure(BOB, eid, procedure_id=procedure_id,
                                    policies=policies)
        reviewed = service.review_run(CAROL, eid, run["run_id"],
                                      target="reviewed", expected_version=1)
        service.review_run(ALICE, eid, run["run_id"], target="approved",
                           expected_version=reviewed["version"])
        executed[procedure_id] = run

    # Judge the findings; the reviewer concurs with judgments above
    # clearly-trivial (the lock blocks on unconcurred ones).
    for item in service.findings(eid):
        status = ("unadjusted" if item["verdict"]["verdict"] == "CLASH"
                  else "cleared")
        service.set_disposition(BOB, eid, finding_uid=item["finding_uid"],
                                status=status,
                                note="reviewed with client")
    for item in service.findings(eid):
        if item["awaiting_concurrence"]:
            service.concur_disposition(
                CAROL, eid, finding_uid=item["finding_uid"],
                expected_version=item["disposition"]["version"])

    # Deselect everything the data cannot support, with rationale.
    for contract in PROCEDURES:
        if contract.procedure_id in executed:
            continue
        service.update_workflow(
            ALICE, eid, "procedure_selection",
            {"procedure_id": contract.procedure_id, "selected": False,
             "rationale": "no supporting export provided this period"})

    # The split threshold is an approved engagement policy, not a run knob.
    service.update_workflow(ALICE, eid, "policy",
                            {"name": "split_threshold", "value": "10000"})
    service.update_workflow(ALICE, eid, "materiality", {"amount": 10000.0})
    for stage in ("risk_assessment", "controls"):
        service.update_workflow(ALICE, eid, "stage",
                                {"name": stage, "status": "complete"})
    for check in COMPLETION_CHECKS:
        service.update_workflow(ALICE, eid, "completion",
                                {"name": check, "done": True,
                                 "note": "performed"})
    outcome = service.lock(ALICE, eid, expected_version=1)
    assert outcome["locked"] is True, outcome.get("blockers")
    return eid


def test_export_produces_an_offline_verifiable_packet(service,
                                                      locked_engagement):
    packet = service.export_packet(CAROL, locked_engagement)
    report = verify_packet(packet)
    assert report["verified"] is True, report
    assert report["finding_receipts_ok"] is True
    assert report["run_seals_ok"] is True
    assert report["lock_signature_ok"] is True
    assert report["export_signature_ok"] is True

    assert packet["engagement"]["status"] == "locked"
    assert len(packet["runs"]) == 2
    assert {run["procedure_id"] for run in packet["runs"]} == {
        "ap.split_payment_review", "ap.subledger_gl_balance_tie"}
    assert len(packet["procedures_not_run"]) == 9
    assert all("deselected" in p["reason"]
               for p in packet["procedures_not_run"])
    sad = packet["summary_of_audit_differences"]
    assert sad["total_unadjusted"] == 5000.0
    assert sad["conclusion"] == "immaterial"
    # The export itself was journaled.
    event = service._conn.execute(
        "SELECT payload FROM domain_event WHERE event_type = 'export.packet'"
    ).fetchone()
    assert json.loads(event["payload"])["packet_digest"] == \
        packet["seal"]["packet_digest"]


def test_review_chain_travels_with_every_run(service, locked_engagement):
    packet = service.export_packet(CAROL, locked_engagement)
    for run in packet["runs"]:
        assert run["executed_by"] == BOB
        assert run["reviewed_by"] == CAROL
        assert run["approved_by"] == ALICE
        assert run["status"] == "approved"


def test_tampering_with_a_packet_is_named_not_hidden(service,
                                                     locked_engagement):
    packet = service.export_packet(CAROL, locked_engagement)

    forged = json.loads(json.dumps(packet))
    forged["runs"][0]["findings"][0]["score"] = 1.0
    report = verify_packet(forged)
    assert report["verified"] is False
    assert report["finding_receipts_ok"] is False
    assert report["run_seals_ok"] is False       # the run seal covers findings
    assert report["packet_digest_ok"] is False

    forged = json.loads(json.dumps(packet))
    forged["summary_of_audit_differences"]["total_unadjusted"] = 0.0
    report = verify_packet(forged)
    assert report["verified"] is False
    # The signature still validly covers the *claimed* digest; the forgery
    # is caught because the content no longer matches that claim. Each
    # layer answers for itself.
    assert report["packet_digest_ok"] is False
    assert report["export_signature_ok"] is True
    assert report["lock_signature_ok"] is True


def test_export_refuses_unlocked_and_drifted_engagements(service):
    eid = service.create_engagement(ALICE, "Fresh", "2025-12-31")["engagement_id"]
    with pytest.raises(ValueError, match="does not verify"):
        service.export_packet(ALICE, eid)


def test_export_refuses_when_post_lock_drift_exists(service,
                                                    locked_engagement):
    service._conn.execute(
        "UPDATE disposition SET note = 'edited after lock' "
        "WHERE engagement_id = ?", (locked_engagement,))
    with pytest.raises(ValueError, match="drift"):
        service.export_packet(CAROL, locked_engagement)


def test_reopened_work_is_regated_before_relock(service, locked_engagement):
    """After unlock, rework passes the same gates a first lock required.

    Reperformance of the same procedure on the same data is the normal
    post-reopening event (AU-C 230 changes after assembly), so the rerun
    must mint a distinct job, and the re-lock must refuse until the new run
    is reviewed and approved like any other.
    """
    eid = locked_engagement
    service.unlock(
        ALICE, eid,
        reason="Client delivered a corrected AP control balance after "
               "archiving; reperforming the control-account tie.",
        expected_version=2)

    # Same procedure, same tables, same policies — a true reperformance.
    rerun = service.run_procedure(
        BOB, eid, procedure_id="ap.subledger_gl_balance_tie")
    assert rerun["status"] == "completed"

    attempt = service.lock(ALICE, eid, expected_version=3)
    assert attempt["locked"] is False
    codes = {b["code"] for b in attempt["blockers"]}
    assert "PROCEDURE_RUN_REVIEW_PENDING" in codes

    reviewed = service.review_run(CAROL, eid, rerun["run_id"],
                                  target="reviewed", expected_version=1)
    service.review_run(ALICE, eid, rerun["run_id"], target="approved",
                       expected_version=reviewed["version"])

    relock = service.lock(ALICE, eid, expected_version=3)
    assert relock["locked"] is True, relock.get("blockers")
    verification = service.verify_lock(eid)
    assert verification["verified"] is True
    assert verification["sequence"] == 2
    # Both generations of the tie run are in the packet, review chains intact.
    packet = service.export_packet(CAROL, eid)
    tie_runs = [run for run in packet["runs"]
                if run["procedure_id"] == "ap.subledger_gl_balance_tie"]
    assert len(tie_runs) == 2
    assert tie_runs[0]["job_id"] != tie_runs[1]["job_id"]
    assert all(run["approved_by"] == ALICE for run in tie_runs)


def test_workpaper_renders_conclusions_with_lineage(service,
                                                    locked_engagement):
    html = service.workpaper_html(CAROL, locked_engagement)
    assert "<script" not in html.lower()
    assert "Acme" in html
    assert "ap.split_payment_review" in html
    assert "ap.subledger_gl_balance_tie" in html
    assert "unadjusted" in html
    assert "reviewed with client" in html
    assert "principal-alice" in html          # lock signer
    assert "does not prove" in html or "Nothing here" in html
    assert "Procedures not executed" in html
    assert "verify_packet" in html
