# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""D1, D3, D4 (roadmap 2026-09-30): excluding a procedure, materiality from a
benchmark, and notes, undo and sign-off on stages and completion checks."""

import pytest

from assurance_application.service import AuthorizationError, WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_domain.lifecycle import SeparationOfDutiesError
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant

ALICE, BOB, CAROL = "principal-alice", "principal-bob", "principal-carol"


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"),
                           ensure_tenant(conn, "firm"))
    conn.close()


@pytest.fixture()
def eid(service):
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    service.assign_team(ALICE, eid, BOB, "preparer")
    service.assign_team(ALICE, eid, CAROL, "reviewer")
    service.update_workflow(ALICE, eid, "cycles", {"cycles": ["receivables"]})
    return eid


def doc(service, eid):
    return service.workflow_document(eid)[0]


# ------------------------------------------------------------------ D1

def test_excluding_a_procedure_needs_the_partner_and_a_reason(service, eid):
    pid = "ar.confirmations_mus"
    with pytest.raises(AuthorizationError):
        service.update_workflow(BOB, eid, "procedure_selection",
                                {"procedure_id": pid, "selected": False,
                                 "rationale": "nonstatistical method chosen"})
    with pytest.raises(ValueError, match="say why"):
        service.update_workflow(ALICE, eid, "procedure_selection",
                                {"procedure_id": pid, "selected": False,
                                 "rationale": "  no  "})
    service.update_workflow(ALICE, eid, "procedure_selection",
                            {"procedure_id": pid, "selected": False,
                             "rationale": "nonstatistical method chosen"})
    assert doc(service, eid)["procedures"][pid] == {
        "selected": False, "rationale": "nonstatistical method chosen",
        "decided_by": ALICE}
    blockers = {b["code"]: b for b in service.readiness(eid)["blockers"]}
    assert pid not in (blockers.get("PROCEDURE_EXCLUSIONS_WITHOUT_RATIONALE")
                       or {}).get("items", [])
    # Including one again needs no reason.
    service.update_workflow(ALICE, eid, "procedure_selection",
                            {"procedure_id": pid, "selected": True})
    assert doc(service, eid)["procedures"][pid]["selected"] is True


# ------------------------------------------------------------------ D3

def test_materiality_from_a_benchmark_is_the_product_to_the_cent(service, eid):
    service.update_workflow(ALICE, eid, "materiality",
                            {"basis": "total revenue", "benchmark_amount": "1234567.89",
                             "percentage": "1.5", "rationale": "stable revenue base"})
    m = doc(service, eid)["materiality"]
    assert m["amount"] == 18518.52
    assert (m["basis"], m["benchmark_amount"], m["percentage"]) == (
        "total revenue", "1234567.89", "1.5")


def test_materiality_that_disagrees_with_its_benchmark_is_refused(service, eid):
    with pytest.raises(ValueError, match="is not 5"):
        service.update_workflow(ALICE, eid, "materiality",
                                {"amount": 20000, "benchmark_amount": "300000",
                                 "percentage": "5"})
    with pytest.raises(ValueError, match="or neither"):
        service.update_workflow(ALICE, eid, "materiality",
                                {"amount": 20000, "percentage": "5"})
    with pytest.raises(ValueError, match="between 0 and 100"):
        service.update_workflow(ALICE, eid, "materiality",
                                {"benchmark_amount": "300000", "percentage": "150"})


def test_an_amount_alone_clears_an_earlier_benchmark(service, eid):
    service.update_workflow(ALICE, eid, "materiality",
                            {"benchmark_amount": "300000", "percentage": "5"})
    service.update_workflow(ALICE, eid, "materiality", {"amount": 12000})
    m = doc(service, eid)["materiality"]
    assert (m["amount"], m["benchmark_amount"], m["percentage"]) == (12000.0, "", "")


# ------------------------------------------------------------------ D4

def test_a_completion_check_needs_a_note_and_can_be_undone(service, eid):
    with pytest.raises(ValueError, match="say what was done"):
        service.update_workflow(BOB, eid, "completion",
                                {"name": "going_concern", "done": True, "note": " "})
    service.update_workflow(BOB, eid, "completion",
                            {"name": "going_concern", "done": True,
                             "note": "indicators reviewed with the CFO"})
    check = doc(service, eid)["completion"]["going_concern"]
    assert (check["done"], check["done_by"]) == (True, BOB)
    service.update_workflow(BOB, eid, "completion",
                            {"name": "going_concern", "done": False, "note": ""})
    check = doc(service, eid)["completion"]["going_concern"]
    assert (check["done"], check["done_by"]) == (False, "")


def test_signoff_is_the_reviewers_and_never_the_preparers(service, eid):
    service.update_workflow(BOB, eid, "completion",
                            {"name": "subsequent_events", "done": True,
                             "note": "read minutes to report date"})
    with pytest.raises(AuthorizationError):  # a preparer holds no sign-off role
        service.update_workflow(BOB, eid, "signoff",
                                {"kind": "completion", "name": "subsequent_events"})
    service.update_workflow(CAROL, eid, "signoff",
                            {"kind": "completion", "name": "subsequent_events"})
    assert doc(service, eid)["completion"]["subsequent_events"]["reviewed_by"] == CAROL
    # Changing the item afterwards clears the sign-off.
    service.update_workflow(BOB, eid, "completion",
                            {"name": "subsequent_events", "done": True,
                             "note": "read minutes and board papers to report date"})
    assert "reviewed_by" not in doc(service, eid)["completion"]["subsequent_events"]


def test_the_partner_who_marked_it_done_cannot_sign_it_off(service, eid):
    service.update_workflow(ALICE, eid, "stage",
                            {"name": "risk_assessment", "status": "complete",
                             "note": "risks assessed and linked"})
    with pytest.raises(SeparationOfDutiesError):
        service.update_workflow(ALICE, eid, "signoff",
                                {"kind": "stage", "name": "risk_assessment"})
    service.update_workflow(CAROL, eid, "signoff",
                            {"kind": "stage", "name": "risk_assessment"})
    assert doc(service, eid)["stages"]["risk_assessment"]["reviewed_by"] == CAROL


def test_nothing_open_can_be_signed_off_and_stage_status_is_checked(service, eid):
    with pytest.raises(ValueError, match="not done yet"):
        service.update_workflow(CAROL, eid, "signoff",
                                {"kind": "stage", "name": "controls"})
    with pytest.raises(ValueError, match="'not_started' or 'complete'"):
        service.update_workflow(ALICE, eid, "stage",
                                {"name": "controls", "status": "done"})
