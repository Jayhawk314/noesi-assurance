# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Risk-assessment register: assertion-level risks and their procedure
linkage. A significant risk needs a response and a responding procedure; no
second person's concurrence (sign-offs removed 1 Oct 2026)."""

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant

ALICE, BOB, CARE = "principal-alice", "principal-bob", "principal-carol"


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    tenant = ensure_tenant(conn, "firm")
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), tenant)
    conn.close()


def _engagement(service):
    eid = service.create_engagement(ALICE, "Zenith", "2025-06-30")["engagement_id"]
    service.assign_team(ALICE, eid, BOB, "preparer")
    service.assign_team(ALICE, eid, CARE, "reviewer")
    return eid


def _blocker_codes(service, eid):
    return {b["code"] for b in service.readiness(eid)["blockers"]}


def test_assess_records_a_risk_at_the_assertion_level(service):
    eid = _engagement(service)
    out = service.assess_risk(
        BOB, eid, title="Fictitious vendors", assertion="occurrence",
        level="significant", rationale="new vendors spiked late in the year")
    assert out["version"] == 1
    [risk] = service.risks(eid)["risks"]
    assert risk["assertion"] == "occurrence"
    assert risk["level"] == "significant"
    assert risk["proposed_by"] == BOB
    assert "requires_concurrence" not in risk and "concurred_by" not in risk
    assert risk["candidate_procedures"]  # occurrence maps to real procedures


def test_unknown_assertion_or_level_is_refused(service):
    eid = _engagement(service)
    with pytest.raises(ValueError, match="assertion"):
        service.assess_risk(BOB, eid, title="x", assertion="made_up")
    with pytest.raises(ValueError, match="level"):
        service.assess_risk(BOB, eid, title="x", assertion="occurrence",
                            level="catastrophic")


def test_link_rejects_unknown_procedures(service):
    eid = _engagement(service)
    rid = service.assess_risk(
        BOB, eid, title="x", assertion="occurrence", level="high")["risk_id"]
    with pytest.raises(ValueError, match="unknown procedure"):
        service.link_risk_procedures(
            BOB, eid, risk_id=rid, procedure_ids=["ap.not_a_procedure"],
            expected_version=1)


def test_significant_risk_gates_the_lock_until_answered(service):
    eid = _engagement(service)
    # A significant risk with no response and no linked procedure.
    rid = service.assess_risk(
        BOB, eid, title="Management override", assertion="authorization",
        level="significant")["risk_id"]
    codes = _blocker_codes(service, eid)
    assert "HIGH_RISKS_WITHOUT_RESPONSE" in codes

    # Give it a response and a responding procedure.
    v = service.assess_risk(
        BOB, eid, risk_id=rid, title="Management override",
        assertion="authorization", level="significant",
        response="test journal entries and approvals",
        expected_version=1)["version"]
    service.link_risk_procedures(
        BOB, eid, risk_id=rid,
        procedure_ids=["ap.segregation_of_duties"], expected_version=v)

    # Answered and linked: the risk gates clear, with no sign-off asked for.
    codes = _blocker_codes(service, eid)
    assert "HIGH_RISKS_WITHOUT_RESPONSE" not in codes
    assert "HIGH_RISKS_WITHOUT_PROCEDURE" not in codes
    assert "RISKS_AWAITING_CONCURRENCE" not in codes
