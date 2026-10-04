# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The engagement record: exported unsigned at any time, checkable offline,
naming what was edited; the workpaper renders every conclusion with its
lineage."""

import json

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
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
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), tenant)
    conn.close()


@pytest.fixture()
def worked_engagement(service):
    """A fully worked engagement: data, runs, dispositions."""
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]

    for content, name, role in ((PAYMENTS_CSV, "payments.csv", "Payments"),
                                (BALANCES_CSV, "recon.csv",
                                 "AP_control_balance")):
        artifact = service.store_source(BOB, eid, content=content,
                                        media_type="text/csv",
                                        original_name=name)
        proposal = service.confirm_source_mapping(
            BOB, eid, role=role, artifact_id=artifact["artifact_id"])
        service.normalize_source(BOB, eid, proposal["spec_id"])

    # Freeze the engagement settings before the procedures run; a later
    # setting change makes their receipts historical until rerun.
    service.update_workflow(ALICE, eid, "policy",
                            {"name": "split_threshold", "value": "10000"})
    service.update_workflow(ALICE, eid, "materiality", {"amount": 10000.0})

    executed = {}
    for procedure_id, policies in (
            ("ap.split_payment_review", {}),
            ("ap.subledger_gl_balance_tie", {})):
        run = service.run_procedure(BOB, eid, procedure_id=procedure_id,
                                    policies=policies)
        executed[procedure_id] = run

    # Judge the findings.
    for item in service.findings(eid):
        status = ("unadjusted" if item["verdict"]["verdict"] == "CLASH"
                  else "cleared")
        service.set_disposition(BOB, eid, finding_uid=item["finding_uid"],
                                status=status,
                                note="reviewed with client")

    # Deselect everything the data cannot support, with rationale.
    for contract in PROCEDURES:
        if contract.procedure_id in executed:
            continue
        service.update_workflow(
            ALICE, eid, "procedure_selection",
            {"procedure_id": contract.procedure_id, "selected": False,
             "rationale": "no supporting export provided this period"})

    assert service.readiness(eid)["ready"] is True, service.readiness(eid)["blockers"]
    return eid


def test_export_produces_an_offline_verifiable_packet(service,
                                                      worked_engagement):
    packet = service.export_record(CAROL, worked_engagement)
    report = verify_packet(packet)
    assert report["verified"] is True, report
    assert report["finding_receipts_ok"] is True
    assert report["run_seals_ok"] is True
    assert report["manifest_ok"] is True
    assert len(packet["runs"]) == 2
    assert {run["procedure_id"] for run in packet["runs"]} == {
        "ap.split_payment_review", "ap.subledger_gl_balance_tie"}
    assert len(packet["procedures_not_run"]) == 9
    assert all("left out" in p["reason"]
               for p in packet["procedures_not_run"])
    sad = packet["summary_of_audit_differences"]
    assert sad["total_unadjusted"] == 5000.0
    assert sad["conclusion"] == "immaterial"
    assert packet["readiness"]["ready"] is True
    # The export itself was journaled.
    event = service._conn.execute(
        "SELECT payload FROM domain_event WHERE event_type = 'export.record'"
    ).fetchone()
    assert json.loads(event["payload"])["packet_digest"] == \
        packet["seal"]["packet_digest"]


def test_every_run_carries_who_ran_it(service, worked_engagement):
    packet = service.export_record(CAROL, worked_engagement)
    for run in packet["runs"]:
        assert run["executed_by"] == BOB
        assert run["status"] == "completed"


def test_tampering_with_a_packet_is_named_not_hidden(service,
                                                     worked_engagement):
    packet = service.export_record(CAROL, worked_engagement)

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
    # The receipts and run seals still hold; only the packet digest names
    # the edit. Each layer answers for itself.
    assert report["packet_digest_ok"] is False
    assert report["finding_receipts_ok"] is True and report["run_seals_ok"] is True

    # Unsigned: someone who edits the packet can recompute its digest. The
    # check then passes; the packet's limits say so plainly.
    from assurance_workpapers.packet import seal_packet
    resealed = seal_packet({k: v for k, v in forged.items() if k != "seal"})
    assert verify_packet(resealed)["verified"] is True
    assert "can recompute the digests" in packet["limits"]


def test_a_rerun_keeps_both_generations_in_the_record(service, worked_engagement):
    """Reperformance of the same procedure on the same data mints a distinct
    job; the record keeps both runs, each with who ran it."""
    eid = worked_engagement
    rerun = service.run_procedure(
        BOB, eid, procedure_id="ap.subledger_gl_balance_tie")
    assert rerun["status"] == "completed"
    packet = service.export_record(CAROL, eid)
    assert verify_packet(packet)["verified"] is True
    tie_runs = [run for run in packet["runs"]
                if run["procedure_id"] == "ap.subledger_gl_balance_tie"]
    assert len(tie_runs) == 2
    assert tie_runs[0]["job_id"] != tie_runs[1]["job_id"]
    assert all(run["executed_by"] == BOB for run in tie_runs)


def test_workpaper_renders_conclusions_with_lineage(service,
                                                    worked_engagement):
    html = service.workpaper_html(CAROL, worked_engagement)
    assert "<script" not in html.lower()
    assert "Acme" in html
    assert "ap.split_payment_review" in html
    assert "ap.subledger_gl_balance_tie" in html
    assert "unadjusted" in html
    assert "reviewed with client" in html
    assert "unsigned" in html
    assert "does not prove" in html
    assert "Procedures not executed" in html
    assert "verify_packet" in html


def test_the_final_file_carries_the_opinion_scope_and_decisions(service,
                                                                worked_engagement):
    """The record carries the opinion the evidence points to, the partner's
    recorded judgments, and what was covered, checkable offline like
    everything else."""
    packet = service.export_record(CAROL, worked_engagement)
    assert verify_packet(packet)["verified"] is True
    assert packet["opinion"]["proposed_opinion"]
    assert "decisions_required" in packet["opinion"]
    assert packet["scope"]["period_end"] and "policies" in packet["scope"]
    html = service.workpaper_html(CAROL, worked_engagement)
    assert "<h2>Opinion</h2>" in html and "<h2>Scope and settings</h2>" in html
