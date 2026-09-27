# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Cycle procedures through the workbench: scope, ingestion, coverage, runs."""

import pytest

from assurance_application.service import AuthorizationError, WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant

ALICE, BOB, CAROL = "principal-alice", "principal-bob", "principal-carol"

REC_CSV = (
    "Account,Item Type,Reference,Amount,Date\n"
    "general,bank balance,,10000.00,2025-12-31\n"
    "general,book balance,,9300.00,2025-12-31\n"
    "general,deposit in transit,,500.00,2025-12-30\n"
    "general,outstanding check,101,700.00,2025-12-28\n"
    "general,outstanding check,104,500.00,2025-12-29\n"
    "general,last check issued,105,0,2025-12-31\n"
).encode("utf-8")

CUTOFF_CSV = (
    "Account,Reference,Type,Amount,Cleared Date\n"
    "general,101,check,700.00,2026-01-04\n"
    "general,103,check,150.00,2026-01-05\n"
    "general,D1,deposit,500.00,2026-01-02\n"
).encode("utf-8")


@pytest.fixture()
def service(tmp_path):
    from assurance_artifacts.signing import LocalKeyStore
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"),
                           ensure_tenant(conn, "firm"),
                           keystore=LocalKeyStore(tmp_path / "keys"))
    conn.close()


@pytest.fixture()
def engagement(service):
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    service.assign_team(ALICE, eid, BOB, "preparer")
    service.assign_team(ALICE, eid, CAROL, "reviewer")
    return eid


def _ingest(service, eid, content, name, role):
    artifact = service.store_source(BOB, eid, content=content, media_type="text/csv",
                                    original_name=name)
    proposal = service.propose_source_mapping(BOB, eid, role=role,
                                              artifact_id=artifact["artifact_id"])
    service.approve_source_mapping(CAROL, eid, proposal["spec_id"])
    return service.normalize_source(BOB, eid, proposal["spec_id"])


def test_no_scope_means_ap_only_coverage(service, engagement):
    _ingest(service, engagement, REC_CSV, "bank_rec.csv", "Bank_reconciliation")
    coverage = service.coverage(engagement)
    assert coverage["summary"]["total"] == 11
    assert all(not p["procedure_id"].startswith("cash.bank_rec")
               for p in coverage["procedures"])


def test_only_the_partner_sets_scope(service, engagement):
    with pytest.raises(AuthorizationError):
        service.update_workflow(BOB, engagement, "cycles", {"cycles": ["cash"]})
    with pytest.raises(ValueError):
        service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["payroll"]})


def test_cycle_execution_and_risk_links_require_engagement_scope(service, engagement):
    with pytest.raises(ValueError, match="outside the engagement scope"):
        service.run_procedure(
            BOB, engagement, procedure_id="inventory.count_listing_trace")

    risk = service.assess_risk(
        BOB, engagement, title="Inventory existence", assertion="existence",
        level="high", rationale="portable assets")
    with pytest.raises(ValueError, match="out-of-scope"):
        service.link_risk_procedures(
            BOB, engagement, risk_id=risk["risk_id"],
            procedure_ids=["inventory.count_listing_trace"],
            expected_version=risk["version"])
    row = service.risks(engagement)["risks"][0]
    assert "inventory.count_listing_trace" not in row["candidate_procedures"]

    service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["inventory"]})
    linked = service.link_risk_procedures(
        BOB, engagement, risk_id=risk["risk_id"],
        procedure_ids=["inventory.count_listing_trace"],
        expected_version=risk["version"])
    assert "inventory.count_listing_trace" in \
        service.risks(engagement)["risks"][0]["candidate_procedures"]
    with pytest.raises(ValueError, match="active risks link"):
        service.update_workflow(ALICE, engagement, "cycles", {"cycles": []})
    assert linked["version"] == 2


def test_engagement_values_are_not_retyped_as_policies(service, engagement):
    with pytest.raises(ValueError, match="engagement record"):
        service.update_workflow(ALICE, engagement, "policy",
                                {"name": "period_end", "value": "2025-12-31"})


def test_cash_scope_runs_through_the_job_runner(service, engagement):
    service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["cash"]})
    coverage = service.coverage(engagement)
    status = {p["procedure_id"]: p["status"] for p in coverage["procedures"]}
    assert coverage["summary"]["total"] == 13
    assert status["cash.bank_reconciliation"] == "blocked"
    recon = _ingest(service, engagement, REC_CSV, "bank_rec.csv",
                    "Bank_reconciliation")["reconciliation"]
    assert recon["rows_loaded"] == 6 and recon["refused_fields"] == []
    _ingest(service, engagement, CUTOFF_CSV, "cutoff statement.csv", "Cutoff_statement")
    status = {p["procedure_id"]: p["status"]
              for p in service.coverage(engagement)["procedures"]}
    assert status["cash.bank_reconciliation"] == "executable"  # period_end from engagement
    assert status["cash.interbank_transfers"] == "blocked"
    run = service.run_procedure(BOB, engagement, procedure_id="cash.bank_reconciliation")
    assert run["status"] == "completed", run["error"]
    reasons = {tuple(f["verdict"]["key"][1:]): f["verdict"]["verdict"]
               for f in service.findings(engagement)}
    # 9300 + 500 − 1200 = 9300 ≠ ... bank side: 10000 + 500 − 1200 = 9300 = books
    assert ("general", "does_not_reconcile") not in reasons
    assert reasons[("general", "outstanding_not_cleared", "104")] == "TENSION"
    assert reasons[("general", "omitted_outstanding_check", "103")] == "ORPHAN"


def test_materiality_section_feeds_completion(service, engagement):
    service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["completion"]})
    service.update_workflow(BOB, engagement, "materiality",
                            {"amount": 5000, "basis": "pretax income", "rationale": "5%"})
    misstatements = ("Description,Reference,Identified,Likely,Current Assets,"
                     "Income Before Taxes\nObsolete stock,22-1,6000,6000,6000,6000\n"
                     ).encode("utf-8")
    _ingest(service, engagement, misstatements, "misstatements.csv", "Misstatements")
    run = service.run_procedure(BOB, engagement,
                                procedure_id="completion.uncorrected_misstatements")
    assert run["status"] == "completed", run["error"]
    keys = {tuple(f["verdict"]["key"][1:]) for f in service.findings(engagement)}
    assert ("material", "current_assets") in keys


def test_risk_register_takes_cycle_assertions(service, engagement):
    from assurance_persistence.database import migrate
    assert migrate(service._conn) == []  # already at the latest version
    risk = service.assess_risk(BOB, engagement, title="Boats may not exist",
                               assertion="existence", level="high",
                               rationale="high value, portable")
    service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["inventory"]})
    service.link_risk_procedures(BOB, engagement, risk_id=risk["risk_id"],
                                 procedure_ids=["inventory.count_listing_trace"],
                                 expected_version=risk["version"])
    row = service.risks(engagement)["risks"][0]
    assert "inventory.count_listing_trace" in row["candidate_procedures"]
    assert "valuation" in service.risks(engagement)["assertions"]


def test_migration_8_keeps_existing_risks(tmp_path, monkeypatch):
    from assurance_persistence import database as db
    conn = db.connect(tmp_path / "v7.db")
    monkeypatch.setattr(db, "MIGRATIONS", db.MIGRATIONS[:7])
    assert db.migrate(conn) == [1, 2, 3, 4, 5, 6, 7]
    conn.execute("INSERT INTO tenant VALUES ('t', 'firm', '2026-01-01')")
    conn.execute("INSERT INTO engagement (engagement_id, tenant_id, client_name, "
                 "period_end, created_at) VALUES ('e', 't', 'Acme', '2025-12-31', "
                 "'2026-01-01')")
    conn.execute("INSERT INTO risk_assessment (tenant_id, engagement_id, risk_id, title, "
                 "assertion, level, updated_at) VALUES ('t', 'e', 'r1', 'Cutoff', "
                 "'cutoff', 'high', '2026-01-01')")
    monkeypatch.undo()
    assert db.migrate(conn) == [8]
    row = conn.execute("SELECT * FROM risk_assessment").fetchone()
    assert (row["risk_id"], row["assertion"], row["level"]) == ("r1", "cutoff", "high")
    conn.execute("INSERT INTO risk_assessment (tenant_id, engagement_id, risk_id, "
                 "assertion, updated_at) VALUES ('t', 'e', 'r2', 'valuation', "
                 "'2026-01-01')")
    conn.close()


def test_open_leads_block_the_lock_until_decided(service, engagement):
    service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["cash"]})
    _ingest(service, engagement, REC_CSV, "bank_rec.csv", "Bank_reconciliation")
    _ingest(service, engagement, CUTOFF_CSV, "cutoff statement.csv", "Cutoff_statement")
    service.run_procedure(BOB, engagement, procedure_id="cash.bank_reconciliation")
    leads = [f for f in service.findings(engagement)
             if f["verdict"]["verdict"] in ("TENSION", "ORPHAN")]
    assert leads

    def codes():
        return {b["code"] for b in service.readiness(engagement)["blockers"]}
    assert "FINDINGS_OPEN" in codes()  # undisposed
    versions = {}
    for f in leads:
        versions[f["finding_uid"]] = service.set_disposition(
            BOB, engagement, finding_uid=f["finding_uid"], status="follow_up",
            note="awaiting the January statement")["version"]
    assert "FINDINGS_OPEN" in codes()  # follow-up is still open
    for f in leads:
        service.set_disposition(BOB, engagement, finding_uid=f["finding_uid"],
                                status="cleared", note="cleared in January",
                                expected_version=versions[f["finding_uid"]])
    assert "FINDINGS_OPEN" not in codes()
