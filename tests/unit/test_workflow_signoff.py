# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""D1 and D3 (roadmap 2026-09-30): excluding a procedure with a reason, and
materiality from a benchmark."""

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant

ALICE = "principal-alice"


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
    service.update_workflow(ALICE, eid, "cycles", {"cycles": ["receivables"]})
    return eid


def doc(service, eid):
    return service.workflow_document(eid)[0]


# ------------------------------------------------------------------ D1

def test_excluding_a_procedure_needs_a_reason(service, eid):
    pid = "ar.confirmations_mus"
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
