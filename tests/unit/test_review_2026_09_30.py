# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Codex's review of 2026-09-30 (docs/reviews/REVIEW-2026-09-30-uncommitted.md):
one test per finding (not run against the pre-fix code)."""

import json
from decimal import Decimal

import pytest

from assurance_application.impact import KEY_FIELDS, diff_records, thresholds
from assurance_application.service import (
    AuthorizationError, EngagementLockedError, WorkbenchService,
)
from assurance_artifacts.signing import LocalKeyStore
from assurance_artifacts.vault import ArtifactVault
from assurance_domain.readiness import COMPLETION_CHECKS
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant

PA, PREP, REV = "pa", "prep", "rev"


@pytest.fixture()
def svc(tmp_path):
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "o"),
                           keystore=LocalKeyStore(tmp_path / "keys"))
    conn.close()


def _locked(svc, name="Zenith"):
    eid = svc.create_engagement(PA, name, "2025-06-30")["engagement_id"]
    svc.update_workflow(PA, eid, "materiality", {"amount": 10000.0})
    for stage in ("risk_assessment", "controls"):
        svc.update_workflow(PA, eid, "stage", {"name": stage, "status": "complete",
                                               "note": "done for the fixture"})
    for check in COMPLETION_CHECKS:
        svc.update_workflow(PA, eid, "completion", {"name": check, "done": True,
                                                    "note": "done for the fixture"})
    svc.update_workflow(PA, eid, "no_data_assertion",
                        {"asserted": True, "reason": "unit fixture, no client data"})
    assert svc.lock(PA, eid, expected_version=1)["locked"] is True
    return eid


# 1. archived engagements are read-only ---------------------------------------

def test_1_an_archived_engagement_refuses_every_change(svc):
    eid = svc.create_engagement(PA, "Acme", "2025-12-31")["engagement_id"]
    svc.archive_engagement(PA, eid, reason="practice run, file it away")
    with pytest.raises(EngagementLockedError, match="archived"):
        svc.assign_team(PA, eid, PREP, "preparer")
    with pytest.raises(EngagementLockedError, match="archived"):
        svc.update_workflow(PA, eid, "materiality", {"amount": 5000})
    with pytest.raises(EngagementLockedError, match="archived"):
        svc.assess_risk(PA, eid, title="x", assertion="occurrence")
    with pytest.raises(EngagementLockedError, match="archived"):
        svc.lock(PA, eid, expected_version=1)
    svc.restore_engagement(PA, eid)
    svc.assign_team(PA, eid, PREP, "preparer")        # writable again


# 2. archive and restore leave a signed lock verified ------------------------

def test_2_archive_and_restore_keep_a_signed_lock_verified(svc):
    eid = _locked(svc)
    assert svc.verify_lock(eid)["verified"] is True
    svc.archive_engagement(PA, eid, reason="finished engagement, file away")
    assert svc.verify_lock(eid)["verified"] is True
    assert [e["engagement_id"] for e in svc.list_engagements(archived=True)] == [eid]
    svc.restore_engagement(PA, eid)
    lock = svc.verify_lock(eid)
    assert lock["verified"] is True and not lock.get("drift")
    assert svc._engagement(eid)["status"] == "locked"


def test_2_migration_11_brings_old_style_archives_back_to_their_status(tmp_path):
    from assurance_persistence import database as db
    conn = connect(tmp_path / "old.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
        version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)""")
    # Build the schema as it was before migration 11.
    ten = [m for m in db.MIGRATIONS if m[0] <= 10]
    original = db.MIGRATIONS
    db.MIGRATIONS = tuple(ten)
    try:
        db.migrate(conn)
    finally:
        db.MIGRATIONS = original
    svc = WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "o"))
    a = svc.create_engagement(PA, "Was Locked", "2025-12-31")["engagement_id"]
    b = svc.create_engagement(PA, "Was Open", "2025-12-31")["engagement_id"]
    for eid, before in ((a, "locked"), (b, "open")):
        conn.execute("UPDATE engagement SET status = 'archived' WHERE engagement_id = ?", (eid,))
        conn.execute(
            "INSERT INTO domain_event (tenant_id, engagement_id, command_id, actor, entity_type, "
            "entity_id, event_type, payload, created_at) SELECT tenant_id, engagement_id, 'c', 'pa', "
            "'engagement', engagement_id, 'engagement.archived', ?, '2026-09-29T00:00:00+00:00' "
            "FROM engagement WHERE engagement_id = ?",
            (json.dumps({"reason": "old", "previous_status": before}), eid))
    assert db.migrate(conn) == [11]
    rows = {r["engagement_id"]: r for r in conn.execute("SELECT * FROM engagement")}
    assert (rows[a]["status"], rows[b]["status"]) == ("locked", "open")
    assert rows[a]["archived_at"] and rows[b]["archived_at"]
    conn.close()


# 3. cycle-record revisions carry their dollar change ------------------------

def test_3_a_trial_balance_revision_is_measured_in_dollars():
    limits = thresholds(15000)
    old = [{"account": "1000", "balance": Decimal("1000000")}]
    new = [{"account": "1000", "balance": Decimal("2000000")}]
    diff = diff_records(old, new, KEY_FIELDS["Trial_balance"], limits, "Trial_balance")
    assert diff["changed"][0]["amount_change"] == 1000000.0
    assert diff["net_amount_change"] == 1000000.0
    assert diff["significance"] == "above_performance"


def test_3_journal_lines_measure_debit_less_credit():
    limits = thresholds(15000)
    old = [{"entry_id": "J1", "line": 1, "debit": Decimal("100"), "credit": None}]
    new = [{"entry_id": "J1", "line": 1, "debit": Decimal("40100"), "credit": None}]
    diff = diff_records(old, new, KEY_FIELDS["Journal_entries"], limits, "Journal_entries")
    assert diff["changed"][0]["amount_change"] == 40000.0


def test_3_a_change_with_no_dollar_measure_is_not_called_none():
    limits = thresholds(15000)
    old = [{"tag_number": "T1", "stock_number": "S1", "quantity": 5}]
    new = [{"tag_number": "T1", "stock_number": "S1", "quantity": 500}]
    diff = diff_records(old, new, KEY_FIELDS["Inventory_count"], limits, "Inventory_count")
    assert diff["changed"][0]["significance"] == "not_measured"
    assert diff["changed"][0]["amount_change"] is None
    assert diff["significance"] == "not_measured"


# 4. the fraud flag is inside the signed manifest ----------------------------

def test_4_changing_a_fraud_flag_after_the_lock_breaks_verification(svc):
    eid = svc.create_engagement(PA, "Zenith", "2025-06-30")["engagement_id"]
    svc.assess_risk(PA, eid, title="Override", assertion="occurrence",
                    level="moderate", fraud=True)
    svc.update_workflow(PA, eid, "materiality", {"amount": 10000.0})
    for stage in ("risk_assessment", "controls"):
        svc.update_workflow(PA, eid, "stage", {"name": stage, "status": "complete",
                                               "note": "done for the fixture"})
    for check in COMPLETION_CHECKS:
        svc.update_workflow(PA, eid, "completion", {"name": check, "done": True,
                                                    "note": "done for the fixture"})
    svc.update_workflow(PA, eid, "no_data_assertion",
                        {"asserted": True, "reason": "unit fixture, no client data"})
    assert svc.lock(PA, eid, expected_version=1)["locked"] is True
    assert svc.verify_lock(eid)["verified"] is True
    svc._conn.execute("UPDATE risk_assessment SET fraud = 0 WHERE engagement_id = ?", (eid,))
    lock = svc.verify_lock(eid)
    assert lock["verified"] is False and "risks" in lock["drift"]


# 5. a signed engagement can be deleted --------------------------------------

def test_5_a_signed_engagement_deletes_completely(svc):
    eid = _locked(svc)
    svc.delete_engagement(PA, eid, confirm_client_name="Zenith",
                          reason="practice file, remove it")
    for table in ("engagement", "lock_snapshot"):
        assert svc._conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE engagement_id = ?", (eid,)).fetchone()[0] == 0
    assert svc._conn.execute("SELECT COUNT(*) FROM lock_signature").fetchone()[0] == 0


# 6. the fraud tab counts only the latest run --------------------------------

def test_6_a_rerun_does_not_double_count_fraud_findings(svc):
    eid = svc.create_engagement(PA, "Acme", "2025-12-31")["engagement_id"]
    svc.assign_team(PA, eid, PREP, "preparer")
    svc.assign_team(PA, eid, REV, "reviewer")
    svc.update_workflow(PA, eid, "cycles", {"cycles": ["payables"]})
    csv = ("Voucher Number,Invoice Number,Vendor Number,Voucher Amount,Voucher Date\n"
           "V1,A-100,Acme Supply,500.00,2025-03-03\n"
           "V2,a 100,Acme Supply,500.00,2025-03-17\n").encode()
    art = svc.store_source(PREP, eid, content=csv, media_type="text/csv", original_name="v.csv")
    spec = svc.propose_source_mapping(PREP, eid, role="Vouchers", artifact_id=art["artifact_id"])
    svc.approve_source_mapping(REV, eid, spec["spec_id"])
    svc.normalize_source(PREP, eid, spec["spec_id"])
    for _ in range(2):
        run = svc.run_procedure(PREP, eid, procedure_id="ap.duplicate_bills")
        assert run["status"] == "completed", run
    test = next(t for t in svc.fraud_view(eid)["tests"]
                if t["procedure_id"] == "ap.duplicate_bills")
    assert test["findings"] == 1 and test["open"] == 1
    assert svc.fraud_view(eid)["summary"]["findings"] == 1


# 7. row keys do not include the values a corrected file changes -------------

def test_7_a_corrected_cutoff_date_is_one_changed_row():
    limits = thresholds(15000)
    old = [{"account": "general", "item_type": "check", "reference": "101",
            "cleared_date": "2026-01-04", "amount": Decimal("700")}]
    new = [dict(old[0], cleared_date="2026-01-05")]
    diff = diff_records(old, new, KEY_FIELDS["Cutoff_statement"], limits, "Cutoff_statement")
    assert (len(diff["added"]), len(diff["removed"]), len(diff["changed"])) == (0, 0, 1)
    assert diff["changed"][0]["fields"][0]["field"] == "cleared_date"


def test_7_the_same_reference_in_two_accounts_does_not_collide():
    limits = thresholds(15000)
    rows = [{"account": "general", "item_type": "check", "reference": "101", "amount": Decimal("1")},
            {"account": "payroll", "item_type": "check", "reference": "101", "amount": Decimal("2")}]
    diff = diff_records(rows, rows, KEY_FIELDS["Bank_reconciliation"], limits, "Bank_reconciliation")
    assert diff["duplicate_keys"] == []


# 8. leaving out the fraud flag keeps it; a non-boolean is refused -----------

def test_8_updating_a_fraud_risk_without_the_flag_keeps_it(svc):
    eid = svc.create_engagement(PA, "Acme", "2025-12-31")["engagement_id"]
    out = svc.assess_risk(PA, eid, title="Override", assertion="occurrence",
                          level="moderate", fraud=True)
    svc.assess_risk(PA, eid, risk_id=out["risk_id"], title="Override, restated",
                    assertion="occurrence", level="moderate",
                    expected_version=out["version"])
    assert svc.risks(eid)["risks"][0]["fraud"] is True
    with pytest.raises(ValueError, match="true or false"):
        svc.assess_risk(PA, eid, title="x", assertion="occurrence", fraud="false")


# Second review, REVIEW-2026-09-30-claude-batch.md ---------------------------

def test_b1_a_draft_working_paper_says_not_ready_before_any_opinion(svc):
    eid = svc.create_engagement(PA, "Acme", "2025-12-31")["engagement_id"]
    html = svc.workpaper_html(PA, eid)
    assert "<b>NOT READY.</b>" in html
    assert html.index("NOT READY") < html.index("Draft opinion")
    assert "<b>Opinion:" not in html
    assert "representations obtained" not in html


def test_b2_rows_sharing_a_key_are_compared_not_dropped():
    limits = thresholds(15000)
    old = [{"account": "general", "item_type": "deposit in transit", "reference": "",
            "amount": Decimal("500")},
           {"account": "general", "item_type": "deposit in transit", "reference": "",
            "amount": Decimal("700")}]
    new = [old[0], dict(old[1], amount=Decimal("250700"))]
    diff = diff_records(old, new, KEY_FIELDS["Bank_reconciliation"], limits,
                        "Bank_reconciliation")
    assert (len(diff["added"]), len(diff["removed"])) == (1, 1)
    assert diff["net_amount_change"] == 250000.0
    assert diff["significance"] == "above_performance"
    assert diff["rows_before"] == 2 and diff["duplicate_keys"] == ["general|deposit in transit|"]


def test_b5_a_fraud_test_that_errored_is_not_counted_as_run(svc):
    eid = svc.create_engagement(PA, "Acme", "2025-12-31")["engagement_id"]
    svc.assign_team(PA, eid, PREP, "preparer")
    svc.update_workflow(PA, eid, "cycles", {"cycles": ["payables"]})
    run = svc.run_procedure(PREP, eid, procedure_id="ap.duplicate_bills")
    assert run["status"] == "error"          # no vouchers loaded
    view = svc.fraud_view(eid)
    assert view["summary"]["run"] == 0
    test = next(t for t in view["tests"] if t["procedure_id"] == "ap.duplicate_bills")
    assert test["last_run"]["status"] == "error"


def test_b7_materiality_rounds_half_up_and_refuses_non_numbers(svc):
    eid = svc.create_engagement(PA, "Acme", "2025-12-31")["engagement_id"]
    svc.update_workflow(PA, eid, "materiality",
                        {"benchmark_amount": "250000.10", "percentage": "5"})
    assert svc.workflow_document(eid)[0]["materiality"]["amount"] == 12500.01
    with pytest.raises(ValueError, match="too large"):
        svc.update_workflow(PA, eid, "materiality",
                            {"benchmark_amount": "1e999999", "percentage": "5"})
    for bad in ("NaN", "Infinity"):
        with pytest.raises(ValueError, match="must be numbers"):
            svc.update_workflow(PA, eid, "materiality",
                                {"benchmark_amount": bad, "percentage": "5"})
