"""The fraud view: AU-C 240's tests, risks and findings in one place."""
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


def test_a_risk_can_be_marked_as_a_fraud_risk_and_keeps_the_mark(svc):
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    out = svc.assess_risk("pa", eid, title="Fictitious vendors", assertion="occurrence",
                          level="significant", fraud=True)
    svc.assess_risk("pa", eid, title="Cutoff", assertion="cutoff", level="moderate")
    risks = {r["title"]: r for r in svc.risks(eid)["risks"]}
    assert risks["Fictitious vendors"]["fraud"] is True and risks["Cutoff"]["fraud"] is False
    svc.assess_risk("pa", eid, risk_id=out["risk_id"], title="Fictitious vendors",
                    assertion="occurrence", level="significant", fraud=False,
                    expected_version=out["version"])
    assert not any(r["fraud"] for r in svc.risks(eid)["risks"])


def test_the_view_lists_every_fraud_test_and_only_fraud_risks(svc):
    from assurance_application.service import FRAUD_TESTS
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    svc.assess_risk("pa", eid, title="Override", assertion="occurrence", level="significant", fraud=True)
    svc.assess_risk("pa", eid, title="Cutoff", assertion="cutoff", level="moderate")
    view = svc.fraud_view(eid)
    assert [t["procedure_id"] for t in view["tests"]] == list(FRAUD_TESTS)
    assert [r["title"] for r in view["risks"]] == ["Override"]
    # nothing loaded: no test has run, and none is reported clean
    assert view["summary"]["run"] == 0 and view["summary"]["findings"] == 0
    assert all(t["last_run"] is None for t in view["tests"])


def test_the_summary_counts_tests_that_can_run_only_in_part(svc):
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    view = svc.fraud_view(eid)
    partial = sum(1 for t in view["tests"] if t["coverage"] == "partial")
    assert view["summary"]["partly"] == partial
