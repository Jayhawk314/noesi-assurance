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


def test_a_test_that_refused_is_not_tested_not_a_finding(svc):
    # 3 Oct walkthrough: Benford's "too few amounts" refusals were counted as
    # three things the fraud tests found.
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    art = svc.store_source("pa", eid, content=(
        b"entry_id,line,entry_date,account,debit,credit\n"
        b"J1,1,2025-03-01,6000,150.00,\nJ1,2,2025-03-01,1000,,150.00\n"
        b"J2,1,2025-04-01,6000,275.00,\nJ2,2,2025-04-01,1000,,275.00\n"),
        media_type="text/csv", original_name="journal.csv")
    spec = svc.confirm_source_mapping("pa", eid, role="Journal_entries",
                                      artifact_id=art["artifact_id"])
    svc.normalize_source("pa", eid, spec["spec_id"])
    svc.update_workflow("pa", eid, "cycles", {"cycles": ["journal_entries"]})
    svc.update_workflow("pa", eid, "policy", {"name": "benford_min_population", "value": "1000"})
    run = svc.run_procedure("pa", eid, procedure_id="forensic.benford_first_digit")
    assert run["status"] == "completed", run.get("error")
    view = svc.fraud_view(eid)
    benford = next(t for t in view["tests"] if t["procedure_id"] == "forensic.benford_first_digit")
    assert benford["findings"] == 0 and benford["open"] == 0
    assert benford["not_tested"] and "not run" in benford["not_tested"][0]
    assert view["summary"]["findings"] == 0 and view["summary"]["not_tested"] == 1
    assert not any(f["procedure_id"] == "forensic.benford_first_digit" for f in view["findings"])


def test_open_findings_are_counted_by_the_procedure_that_found_them(svc):
    # 3 Oct walkthrough: the round trip's uid starts with its domain, not its
    # procedure, so the screens showed the raw uid. Readiness now says which
    # procedure each open finding came from.
    eid = svc.create_engagement("pa", "Acme Supply", "2025-12-31")["engagement_id"]
    art = svc.store_source("pa", eid, content=(
        b"Flow ID,From,To,Amount,Date,Relation,Flow Type\n"
        b"F1,Acme Supply,Alpha Trading,5000.00,2025-05-01,payment,vendor payment\n"
        b"F2,Alpha Trading,Beta Holdings,5000.00,2025-05-03,payment,transfer\n"
        b"F3,Beta Holdings,Acme Supply,5000.00,2025-05-06,payment,customer receipt\n"),
        media_type="text/csv", original_name="flows.csv")
    spec = svc.confirm_source_mapping("pa", eid, role="Value_flows", artifact_id=art["artifact_id"])
    svc.normalize_source("pa", eid, spec["spec_id"])
    run = svc.run_procedure("pa", eid, procedure_id="forensic.closed_value_flow")
    assert run["status"] == "completed", run.get("error")
    found = [f for f in svc.findings(eid) if f["verdict"]["verdict"] != "AGREE"]
    assert found, "invented round trip was not found"
    assert not found[0]["finding_uid"].startswith("forensic.closed_value_flow")
    blocker = next(b for b in svc.readiness(eid)["blockers"] if b["code"] == "FINDINGS_OPEN")
    assert blocker["by_procedure"] == {"forensic.closed_value_flow": blocker["count"]}
