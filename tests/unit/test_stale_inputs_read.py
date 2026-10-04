"""A result is stale only when an input its procedure read has changed.

3 Oct 2026 review: every run recorded every loaded file and every setting,
so an unrelated upload or setting marked the whole audit stale. Runs now
record what the engine read. Invented data throughout.
"""
import json

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant

JOURNAL = (b"entry_id,line,entry_date,account,debit,credit\n"
           b"J1,1,2025-03-01,6000,150.00,\nJ1,2,2025-03-01,1000,,150.00\n"
           b"J2,1,2025-04-01,6000,275.00,\nJ2,2,2025-04-01,1000,,275.00\n")
ASSETS = (b"asset_id,description,cost,acquired,life_years,method\n"
          b"FA1,Truck,30000,2024-01-01,5,straight line\n")
PAYMENTS = b"payment_number,vendor_id,payment_date,amount\nP1,V1,2025-03-01,100.00\n"


@pytest.fixture()
def svc(tmp_path):
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "o"))
    conn.close()


def _load(svc, eid, role, name, content, mode=None):
    art = svc.store_source("me", eid, content=content, media_type="text/csv", original_name=name)
    spec = svc.confirm_source_mapping("me", eid, role=role, artifact_id=art["artifact_id"])
    svc.normalize_source("me", eid, spec["spec_id"], mode=mode)


def _benford(svc):
    eid = svc.create_engagement("me", "Invented Co", "2025-12-31")["engagement_id"]
    _load(svc, eid, "Journal_entries", "journal.csv", JOURNAL)
    svc.update_workflow("me", eid, "cycles", {"cycles": ["journal_entries", "ppe"]})
    svc.update_workflow("me", eid, "policy", {"name": "benford_min_population", "value": "2"})
    svc.run_procedure("me", eid, procedure_id="forensic.benford_first_digit")
    return eid


def _latest_reasons(svc, eid):
    return svc.runs(eid)[-1]["stale_reasons"]


def test_a_run_records_the_tables_and_settings_its_engine_read(svc):
    eid = _benford(svc)
    manifest = json.loads(svc._conn.execute("SELECT manifest FROM procedure_run").fetchone()[0])
    read = manifest["inputs_read"]
    # looked for bills and payments too, though none were loaded
    assert {"Journal_entries", "Vouchers", "Payments"} <= set(read["roles"])
    assert "Fixed_assets" not in read["roles"]
    assert "benford_min_population" in read["policies"]


def test_an_unrelated_setting_or_file_leaves_the_result_current(svc):
    eid = _benford(svc)
    svc.update_workflow("me", eid, "policy", {"name": "ppe_rounding_tolerance", "value": "5"})
    _load(svc, eid, "Fixed_assets", "fa.csv", ASSETS)
    assert _latest_reasons(svc, eid) == []
    assert not any(b["code"] == "PROCEDURE_RESULTS_STALE"
                   for b in svc.readiness(eid)["blockers"])


def test_its_own_setting_a_newly_arrived_table_or_a_replaced_file_makes_it_stale(svc):
    eid = _benford(svc)
    svc.update_workflow("me", eid, "policy", {"name": "benford_min_population", "value": "3"})
    assert _latest_reasons(svc, eid) == ["settings changed"]
    svc.run_procedure("me", eid, procedure_id="forensic.benford_first_digit")
    assert _latest_reasons(svc, eid) == []
    _load(svc, eid, "Payments", "p.csv", PAYMENTS)   # it looked for payments before
    assert _latest_reasons(svc, eid) == ["loaded data changed"]
    svc.run_procedure("me", eid, procedure_id="forensic.benford_first_digit")
    _load(svc, eid, "Journal_entries", "journal_v2.csv", JOURNAL[:130], mode="replace")
    assert _latest_reasons(svc, eid) == ["loaded data changed"]


TRIAL_BALANCE = (b"account,description,balance,line\n"
                 b"1000,Cash,5000.00,cash\n2000,Accounts payable,-3000.00,current_liabilities\n"
                 b"3000,Equity,-2000.00,equity\n")


def test_a_line_mapping_edit_marks_only_runs_that_read_the_trial_balance(svc):
    # Review 3 Oct: every cycle run logged the line mapping as read, so one
    # mapping edit marked 31 unrelated Kestrel results stale.
    eid = _benford(svc)
    _load(svc, eid, "Trial_balance", "tb.csv", TRIAL_BALANCE)
    svc.update_workflow("me", eid, "cycles", {"cycles": ["journal_entries", "completion"]})
    # A mapping already in force when the runs happen (as on Kestrel): the
    # engine relabels the trial balance for every run, which is not a read.
    svc.update_workflow("me", eid, "line_mapping", {"account": "2000", "line": "current_liabilities"})
    svc.run_procedure("me", eid, procedure_id="forensic.benford_first_digit")
    svc.run_procedure("me", eid, procedure_id="completion.going_concern_indicators")
    latest = {r["procedure_id"]: r for r in svc.runs(eid)}
    assert latest["completion.going_concern_indicators"]["status"] == "completed"
    svc.update_workflow("me", eid, "line_mapping", {"account": "1000", "line": "cash"})
    latest = {r["procedure_id"]: r for r in svc.runs(eid)}
    assert latest["forensic.benford_first_digit"]["stale_reasons"] == []
    assert latest["completion.going_concern_indicators"]["stale_reasons"] == ["settings changed"]


def test_a_run_from_before_the_read_record_stays_cautious(svc):
    eid = _benford(svc)
    row = svc._conn.execute("SELECT run_id, manifest FROM procedure_run").fetchone()
    manifest = json.loads(row["manifest"])
    manifest.pop("inputs_read")
    svc._conn.execute("UPDATE procedure_run SET manifest = ? WHERE run_id = ?",
                      (json.dumps(manifest), row["run_id"]))
    svc.update_workflow("me", eid, "policy", {"name": "ppe_rounding_tolerance", "value": "5"})
    assert _latest_reasons(svc, eid) == ["settings changed"]
