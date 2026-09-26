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
        service.update_workflow(BOB, engagement, "scope", {"cycles": ["cash"]})
    with pytest.raises(ValueError):
        service.update_workflow(ALICE, engagement, "scope", {"cycles": ["payroll"]})


def test_engagement_values_are_not_retyped_as_policies(service, engagement):
    with pytest.raises(ValueError, match="engagement record"):
        service.update_workflow(ALICE, engagement, "policy",
                                {"name": "period_end", "value": "2025-12-31"})


def test_cash_scope_runs_through_the_job_runner(service, engagement):
    service.update_workflow(ALICE, engagement, "scope", {"cycles": ["cash"]})
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
    service.update_workflow(ALICE, engagement, "scope", {"cycles": ["completion"]})
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
