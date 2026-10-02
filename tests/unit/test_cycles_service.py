# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Cycle procedures through the workbench: scope, ingestion, coverage, runs."""

import json

import pytest

from assurance_application.service import WorkbenchService
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
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"),
                           ensure_tenant(conn, "firm"))
    conn.close()


@pytest.fixture()
def engagement(service):
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    return eid


def _ingest(service, eid, content, name, role):
    artifact = service.store_source(BOB, eid, content=content, media_type="text/csv",
                                    original_name=name)
    proposal = service.confirm_source_mapping(BOB, eid, role=role,
                                              artifact_id=artifact["artifact_id"])
    return service.normalize_source(BOB, eid, proposal["spec_id"])


def test_no_scope_means_ap_only_coverage(service, engagement):
    _ingest(service, engagement, REC_CSV, "bank_rec.csv", "Bank_reconciliation")
    coverage = service.coverage(engagement)
    assert coverage["summary"]["total"] == 11
    assert all(not p["procedure_id"].startswith("cash.bank_rec")
               for p in coverage["procedures"])


def test_scope_refuses_an_unknown_cycle(service, engagement):
    with pytest.raises(ValueError):
        service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["not-a-cycle"]})


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
    assert coverage["summary"]["total"] == 2   # cash only: no AP procedures (K14)
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
    assert db.migrate(conn) == [8, 9, 10, 11, 12]
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


def test_r1_a_run_on_missing_data_is_recorded_as_an_error_not_completed(service, engagement):
    run = service.run_procedure(BOB, engagement, procedure_id="ap.payment_voucher_reference")
    assert run["status"] == "error" and "blocked" in run["error"]
    assert service.runs(engagement)[0]["status"] == "error"
    assert service.findings(engagement) == []


def test_r4_out_of_scope_selection_and_policy_are_refused(service, engagement):
    with pytest.raises(ValueError, match="not in scope"):
        service.update_workflow(ALICE, engagement, "procedure_selection",
                                {"procedure_id": "inventory.count_listing_trace",
                                 "selected": True, "rationale": "x"})
    with pytest.raises(ValueError, match="none of which is in scope"):
        service.update_workflow(ALICE, engagement, "policy",
                                {"name": "inventory_tolerable_misstatement", "value": "10"})
    service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["inventory"]})
    service.update_workflow(ALICE, engagement, "policy",
                            {"name": "inventory_tolerable_misstatement", "value": "10"})
    # a policy shared with the payables contracts stays settable without cycles
    service.update_workflow(ALICE, engagement, "policy",
                            {"name": "split_window_days", "value": "3"})


def test_rr1_removing_a_cycle_retires_its_settings_and_selections(service, engagement):
    service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["inventory"]})
    service.update_workflow(ALICE, engagement, "policy",
                            {"name": "inventory_tolerable_misstatement", "value": "1000"})
    service.update_workflow(ALICE, engagement, "policy",
                            {"name": "split_window_days", "value": "3"})
    service.update_workflow(ALICE, engagement, "procedure_selection",
                            {"procedure_id": "inventory.count_listing_trace",
                             "selected": False, "rationale": "not applicable"})
    service.update_workflow(ALICE, engagement, "cycles", {"cycles": []})
    document = service.workflow_document(engagement)[0]
    assert "inventory_tolerable_misstatement" not in document["policies"]
    assert document["policies"]["split_window_days"] == "3"  # payables policy stays
    assert "inventory.count_listing_trace" not in document.get("procedures", {})
    assert {(r["kind"], r["name"]) for r in document["retired"]} == {
        ("policy", "inventory_tolerable_misstatement"),
        ("procedure_selection", "inventory.count_listing_trace")}
    # switching the cycle back on does not bring the old decisions back
    service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["inventory"]})
    document = service.workflow_document(engagement)[0]
    assert "inventory_tolerable_misstatement" not in document["policies"]
    assert "inventory.count_listing_trace" not in document.get("procedures", {})


PAYROLL_REC_CSV = (
    "Account,Item Type,Reference,Amount,Date\n"
    "payroll,bank balance,,5000.00,2025-12-31\n"
    "payroll,book balance,,4600.00,2025-12-31\n"
    "payroll,outstanding check,P9,400.00,2025-12-30\n"
).encode("utf-8")


def _ingest_as(service, eid, content, name, role, mode=None):
    artifact = service.store_source(BOB, eid, content=content, media_type="text/csv",
                                    original_name=name)
    proposal = service.confirm_source_mapping(BOB, eid, role=role,
                                              artifact_id=artifact["artifact_id"])
    return proposal["spec_id"], lambda m=mode: service.normalize_source(
        BOB, eid, proposal["spec_id"], mode=m)


def test_k3_a_second_file_for_a_role_must_say_replace_or_add(service, engagement):
    _ingest(service, engagement, REC_CSV, "checking_rec.csv", "Bank_reconciliation")
    _, load = _ingest_as(service, engagement, PAYROLL_REC_CSV, "payroll_rec.csv",
                         "Bank_reconciliation")
    with pytest.raises(ValueError, match=r"already has data in use \(checking_rec.csv\)"):
        load()
    # Nothing changed: the first file is still the only one in use.
    assert [d["in_use"] for d in service.sources(engagement)["datasets"]] == [True]


def test_k3_added_files_are_all_read_and_the_run_records_them(service, engagement):
    service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["cash"]})
    first = _ingest(service, engagement, REC_CSV, "checking_rec.csv",
                    "Bank_reconciliation")
    _, load = _ingest_as(service, engagement, PAYROLL_REC_CSV, "payroll_rec.csv",
                         "Bank_reconciliation", mode="add")
    second = load()
    assert second["load_mode"] == "add"
    _ingest(service, engagement, CUTOFF_CSV, "cutoff.csv", "Cutoff_statement")
    datasets = service.sources(engagement)["datasets"]
    assert [d["in_use"] for d in datasets if d["role"] == "Bank_reconciliation"] \
        == [True, True]
    run = service.run_procedure(BOB, engagement, procedure_id="cash.bank_reconciliation")
    assert run["status"] == "completed"
    # Both accounts were tested, not just the file loaded last.
    assert set(run["summary"]["accounts"]) == {"general", "payroll"}
    manifest = json.loads(service._conn.execute(
        "SELECT manifest FROM procedure_run WHERE run_id = ?",
        (run["run_id"],)).fetchone()["manifest"])
    assert manifest["datasets"]["Bank_reconciliation"] == [
        first["dataset_id"], second["dataset_id"]]


def test_k3_replace_keeps_only_the_new_file_in_use(service, engagement):
    _ingest(service, engagement, REC_CSV, "rec_v1.csv", "Bank_reconciliation")
    _, load = _ingest_as(service, engagement, PAYROLL_REC_CSV, "rec_v2.csv",
                         "Bank_reconciliation", mode="replace")
    load()
    datasets = service.sources(engagement)["datasets"]
    assert [(d["load_mode"], d["in_use"]) for d in datasets] == [
        ("first", False), ("replace", True)]
    impact = service.revision_impact(engagement)
    [revision] = impact["revisions"]
    assert revision["load_mode"] == "replace"
    assert revision["before"]["files"] == ["rec_v1.csv"]
    assert revision["after"]["files"] == ["rec_v2.csv"]


def test_k3_adding_a_file_with_different_fields_is_refused(service, engagement):
    _ingest(service, engagement, REC_CSV, "checking_rec.csv", "Bank_reconciliation")
    narrow = b"Account,Item Type,Amount\npayroll,bank balance,5000.00\n"
    _, load = _ingest_as(service, engagement, narrow, "payroll_rec.csv",
                         "Bank_reconciliation", mode="add")
    with pytest.raises(ValueError, match="cannot add this file"):
        load()


def test_loads_in_the_same_clock_tick_keep_their_load_order(service, engagement):
    """Two loads can share a timestamp; the later one must still be the later
    one. Ordering fell back to the random dataset id and sometimes put the
    replacement first (an intermittent failure of the replace test above)."""
    _ingest(service, engagement, REC_CSV, "rec_v1.csv", "Bank_reconciliation")
    _, load = _ingest_as(service, engagement, PAYROLL_REC_CSV, "rec_v2.csv",
                         "Bank_reconciliation", mode="replace")
    second = load()["dataset_id"]
    conn = service._conn
    conn.execute("UPDATE normalized_dataset SET created_at = '2026-01-01T00:00:00+00:00'")
    conn.execute("UPDATE normalized_dataset SET dataset_id = '0' WHERE dataset_id = ?",
                 (second,))
    datasets = service.sources(engagement)["datasets"]
    assert [(d["load_mode"], d["in_use"]) for d in datasets] == [
        ("first", False), ("replace", True)]
    assert service._tables(engagement)["Bank_reconciliation"].source_file == "rec_v2.csv"


def test_k4_a_file_whose_headings_match_no_field_is_refused(service, engagement):
    artifact = service.store_source(BOB, engagement, content=b"Foo,Bar\n1,2\n3,4\n",
                                    media_type="text/csv", original_name="tb.csv")
    with pytest.raises(ValueError, match="none of this file's headings"):
        service.confirm_source_mapping(BOB, engagement, role="Trial_balance",
                                       artifact_id=artifact["artifact_id"])
    batch = service.confirm_source_mappings(
        BOB, engagement, [{"artifact_id": artifact["artifact_id"], "role": "Trial_balance"}])
    assert batch["results"][0]["status"] == "error"
