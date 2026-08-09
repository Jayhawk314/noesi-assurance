# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Risk-assessment register: assertion-level risks, procedure linkage, and a
concurrence gate that refuses a lock over an unconcurred significant risk —
the same separation dispositions enforce, applied to planning judgment."""

import pytest

from assurance_application.service import (
    AuthorizationError, WorkbenchService,
)
from assurance_artifacts.signing import LocalKeyStore
from assurance_artifacts.vault import ArtifactVault
from assurance_domain.lifecycle import SeparationOfDutiesError
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant

ALICE, BOB, CARE = "principal-alice", "principal-bob", "principal-carol"


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    tenant = ensure_tenant(conn, "firm")
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), tenant,
                           keystore=LocalKeyStore(tmp_path / "keys"))
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
    assert risk["requires_concurrence"] is True
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


def test_proposer_cannot_concur_their_own_risk(service):
    eid = _engagement(service)
    # Give BOB the reviewer role too, so the role gate passes and the identity
    # check is the thing under test.
    service.assign_team(ALICE, eid, BOB, "reviewer")
    rid = service.assess_risk(
        BOB, eid, title="x", assertion="occurrence", level="significant",
        response="expanded vendor testing")["risk_id"]
    with pytest.raises(SeparationOfDutiesError):
        service.concur_risk(BOB, eid, risk_id=rid, expected_version=1)


def test_concurrence_requires_reviewer_or_partner(service):
    eid = _engagement(service)
    rid = service.assess_risk(
        BOB, eid, title="x", assertion="occurrence", level="high",
        response="r")["risk_id"]
    # BOB is only a preparer: the role gate refuses before identity.
    with pytest.raises(AuthorizationError):
        service.concur_risk(BOB, eid, risk_id=rid, expected_version=1)


def test_significant_risk_gates_the_lock_until_answered_and_concurred(service):
    eid = _engagement(service)
    # A significant risk with no response, no linked procedure, no concurrence.
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

    # Now it is fully specified but not concurred: the concurrence gate holds.
    codes = _blocker_codes(service, eid)
    assert "HIGH_RISKS_WITHOUT_RESPONSE" not in codes
    assert "HIGH_RISKS_WITHOUT_PROCEDURE" not in codes
    assert "RISKS_AWAITING_CONCURRENCE" in codes

    # A distinct reviewer concurs; the risk gate clears.
    risk = service.risks(eid)["risks"][0]
    service.concur_risk(CARE, eid, risk_id=rid,
                        expected_version=risk["version"])
    assert "RISKS_AWAITING_CONCURRENCE" not in _blocker_codes(service, eid)


def test_reassessing_a_concurred_risk_voids_the_concurrence(service):
    eid = _engagement(service)
    rid = service.assess_risk(
        BOB, eid, title="x", assertion="occurrence", level="high",
        response="r")["risk_id"]
    service.link_risk_procedures(
        BOB, eid, risk_id=rid, procedure_ids=["ap.vendor_relational_twins"],
        expected_version=1)
    risk = service.risks(eid)["risks"][0]
    service.concur_risk(CARE, eid, risk_id=rid, expected_version=risk["version"])
    assert service.risks(eid)["risks"][0]["concurred_by"] == CARE

    # Re-assessing the judgment voids the concurrence: it concurred a
    # different risk.
    v = service.risks(eid)["risks"][0]["version"]
    service.assess_risk(BOB, eid, risk_id=rid, title="x",
                        assertion="occurrence", level="high", response="r2",
                        expected_version=v)
    reloaded = service.risks(eid)["risks"][0]
    assert reloaded["concurred_by"] == ""
    assert reloaded["awaiting_concurrence"] is True
