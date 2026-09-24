# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""QuickBooks Online report exports: recognized, flattened, checked, reviewed.

The fixtures are real Excel exports from QuickBooks Online's public sample
company (Craig's Design and Landscaping Services, report period All Dates,
exported 2026-09-24): a title block, grouped detail rows, "Total for ..."
subtotals and a timestamp footer, exactly as QuickBooks writes them.
"""

from pathlib import Path

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts import xlsx
from assurance_artifacts.vault import ArtifactVault
from assurance_domain.errors import DuplicateError
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from procedures_ap import quickbooks as qb

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "quickbooks"
BILL_PAYMENTS = (FIXTURES / "bill_payment_list.xlsx").read_bytes()
BY_VENDOR = (FIXTURES / "transaction_list_by_vendor.xlsx").read_bytes()
UNPAID = (FIXTURES / "unpaid_bills_report.xlsx").read_bytes()
CONTACTS = (FIXTURES / "vendor_contact_list.xlsx").read_bytes()
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PREPARER, REVIEWER, PARTNER = "p-prep", "p-rev", "p-partner"


def _flatten(content, recipe_id):
    extraction, headers, rows = xlsx.extract(content)
    return qb.apply(recipe_id, headers, rows, extraction["header_row"] + 1)


def test_reports_are_recognized_by_title_and_exact_headings():
    by_vendor = qb.recognize(xlsx.preview(BY_VENDOR)[0]["rows"])
    assert {m["role"] for m in by_vendor} == {"Vouchers", "Payments", "Purchase_orders"}
    assert all(m["header_row"] == 5 for m in by_vendor)
    [payments] = qb.recognize(xlsx.preview(BILL_PAYMENTS)[0]["rows"])
    assert payments["recipe"] == "qbo.bill_payment_list.payments"

    # A report with customized columns is not claimed by any recipe.
    rows = [list(r) for r in xlsx.preview(BILL_PAYMENTS)[0]["rows"]]
    rows[4][4] = "Open Balance"
    assert qb.recognize(rows) == []


def test_reports_without_a_dependable_structure_are_not_claimed():
    # Bills and Applied Payments shows bills and payments side by side with
    # nothing linking them; the General Ledger nests sub-accounts. Neither
    # is offered a recipe, so neither can be read as if it said more.
    for name in ("bills_and_applied_payments", "general_ledger"):
        rows = xlsx.preview((FIXTURES / f"{name}.xlsx").read_bytes())[0]["rows"]
        assert qb.recognize(rows) == [], name


def test_unpaid_bills_check_both_amount_columns():
    headers, rows, source_rows, report = _flatten(UNPAID, "qbo.unpaid_bills.vouchers")
    assert report["subtotals_checked"] == 10          # 5 vendors x 2 columns
    assert [(t["column"], t["stated"]) for t in report["grand_total"]] ==            [("Amount", "1602.67"), ("Open balance", "1602.67")]
    assert all(t["agrees"] for t in report["grand_total"])
    assert report["totals_disagreeing"] == []
    assert [r["Vendor"] for r in rows][:2] == ["Brosnahan Insurance Agency",
                                              "Diego's Road Warrior Bodyshop"]
    assert source_rows == [7, 10, 13, 16, 19]


def test_the_vendor_contact_list_is_flat_and_keyed_by_name():
    [match] = qb.recognize(xlsx.preview(CONTACTS)[0]["rows"])
    assert match["recipe"] == "qbo.vendor_contact_list.vendors"
    assert match["header_row"] == 4
    headers, rows, source_rows, report = _flatten(CONTACTS, match["recipe"])
    assert headers[0] == "Vendor" and len(rows) == 26     # timestamp footer excluded
    assert source_rows[0] == 5 and source_rows[-1] == 30
    assert report["subtotals_checked"] == 0 and report["grand_total"] is None


def test_every_subtotal_is_recomputed_and_the_groups_become_columns():
    headers, rows, source_rows, report = _flatten(
        BY_VENDOR, "qbo.transaction_list_by_vendor.vouchers")
    assert headers[0] == "Vendor"
    assert report["subtotals_checked"] == 19
    assert report["grand_total"] == [{"group": "TOTAL", "column": "Amount",
                                      "sheet_row": 105, "computed": "1718.69",
                                      "stated": "1718.69", "agrees": True}]
    assert report["totals_disagreeing"] == []
    # Only bills are kept, and what was left out is counted, not hidden.
    assert report["rows_kept"] == 15 == report["transaction_types"]["Bill"]["kept"]
    assert report["transaction_types"]["Expense"] == {"kept": 0, "left_out": 15}
    assert rows[0]["Vendor"] == "Books by Bessie" and source_rows[0] == 13
    assert all(r["Transaction type"] == "Bill" for r in rows)


def test_payments_are_positive_and_the_signs_seen_are_reported():
    _, rows, source_rows, report = _flatten(
        BILL_PAYMENTS, "qbo.bill_payment_list.payments")
    assert report["subtotals_checked"] == 2 and report["totals_disagreeing"] == []
    assert report["amount_signs_by_account"] == {
        "Checking": {"negative": 7, "positive": 0, "zero": 0},
        "Mastercard": {"negative": 0, "positive": 3, "zero": 0}}
    first = rows[0]
    assert (first["Paid From Account"], first["Amount"], first["Paid Amount"]) == \
           ("Checking", "-2000", "2000")
    assert source_rows == [7, 8, 9, 10, 11, 12, 13, 16, 17, 18]


def test_a_wrong_subtotal_is_reported_not_absorbed():
    extraction, headers, rows = xlsx.extract(BILL_PAYMENTS)
    assert rows[8]["Column A"] == "Total for Checking"      # sheet row 14
    rows[8]["Amount"] = "-4305.10"
    _, _, _, report = qb.apply("qbo.bill_payment_list.payments", headers, rows, 6)
    [bad] = report["totals_disagreeing"]
    assert bad == {"group": "Checking", "column": "Amount", "sheet_row": 14,
                   "computed": "-4305.09", "stated": "-4305.10", "agrees": False}


def test_a_file_that_departs_from_the_layout_is_refused_with_the_row():
    extraction, headers, rows = xlsx.extract(BILL_PAYMENTS)
    with pytest.raises(qb.RecipeError, match="not QuickBooks' standard"):
        qb.apply("qbo.transaction_list_by_vendor.payments", headers, rows, 6)
    del rows[0]                              # the "Checking" group heading
    with pytest.raises(qb.RecipeError, match="sheet row 6: a detail row outside any group"):
        qb.apply("qbo.bill_payment_list.payments", headers, rows, 6)


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    svc = WorkbenchService(conn, ArtifactVault(tmp_path / "vault"),
                           ensure_tenant(conn, "qbo"))
    eid = svc.create_engagement(PARTNER, "Craig's Design", "2026-12-31")["engagement_id"]
    svc.assign_team(PARTNER, eid, PREPARER, "preparer")
    svc.assign_team(PARTNER, eid, REVIEWER, "reviewer")
    yield svc, eid
    conn.close()


def _load(svc, eid, content, name, role, recipe):
    artifact = svc.store_source(PREPARER, eid, content=content,
                                media_type=XLSX_TYPE, original_name=name)
    proposal = svc.propose_source_mapping(
        PREPARER, eid, role=role, artifact_id=artifact["artifact_id"],
        extraction={"recipe": recipe})
    svc.approve_source_mapping(REVIEWER, eid, proposal["spec_id"])
    return artifact, proposal, svc.normalize_source(PREPARER, eid, proposal["spec_id"])


def test_bill_payment_list_loads_as_reviewed_payments(service):
    svc, eid = service
    artifact, proposal, normalized = _load(
        svc, eid, BILL_PAYMENTS, "Bill Payment List.xlsx", "Payments",
        "qbo.bill_payment_list.payments")
    preview = svc.workbook_preview(eid, artifact["artifact_id"])
    assert preview["sheets"][0]["recipes"][0]["role"] == "Payments"

    assert proposal["column_map"] == {"payment_number": "Num", "vendor_number": "Vendor",
                                      "payment_amount": "Paid Amount",
                                      "payment_date": "Date"}
    # What QuickBooks does not export is refused, not invented.
    assert "voucher_number" in proposal["refused_fields"]
    assert proposal["extraction"]["recipe_report"]["totals_disagreeing"] == []

    rec = normalized["reconciliation"]
    assert rec["rows_loaded"] == 10 and rec["rows_rejected"] == 0
    assert rec["control_total"] == "4539.50"     # 4,305.09 checks + 234.41 card
    assert rec["diagnostics"]["duplicate_keys"] == ["1"]
    records = svc._rebuild_table(proposal["spec_id"]).records
    assert [r["source_row"] for r in records][:3] == [7, 8, 9]

    # The recipe is part of the reviewed spec and its digest; the reviewer
    # also sees its check report beside the spec.
    spec = next(s for s in svc.sources(eid)["mapping_specs"]
                if s["spec_id"] == proposal["spec_id"])
    assert spec["extraction"]["recipe"] == "qbo.bill_payment_list.payments"
    assert spec["recipe_report"]["subtotals_checked"] == 2


def test_bills_without_a_number_are_quarantined_with_the_reason(service):
    svc, eid = service
    _, proposal, normalized = _load(svc, eid, UNPAID, "Unpaid Bills.xlsx",
                                    "Vouchers", "qbo.unpaid_bills.vouchers")
    # Said before approval ...
    assert proposal["extraction"]["recipe_report"]["missing_required"] == [
        {"field": "voucher_number", "heading": "Num", "rows": 5, "of": 5}]
    rec = normalized["reconciliation"]
    assert rec["rows_loaded"] == 0 and rec["rows_rejected"] == 5
    # ... and explained after loading, with the sheet rows to look at.
    [dataset] = svc.sources(eid)["datasets"]
    assert dataset["rejected_reasons"] == [{
        "reason": "required field(s) blank: ['voucher_number']",
        "rows": 5, "source_rows": [7, 10, 13, 16, 19]}]


def test_a_mismatched_role_is_refused_and_purchase_orders_load(service):
    svc, eid = service
    artifact = svc.store_source(PREPARER, eid, content=BY_VENDOR, media_type=XLSX_TYPE,
                                original_name="Transaction List by Vendor.xlsx")
    recipe = {"recipe": "qbo.transaction_list_by_vendor.purchase_orders"}
    with pytest.raises(ValueError, match="produces Purchase_orders, not Vouchers"):
        svc.propose_source_mapping(PREPARER, eid, role="Vouchers",
                                   artifact_id=artifact["artifact_id"], extraction=recipe)
    # In a batch, the recipe names its own role.
    [item] = svc.propose_source_mappings(
        PREPARER, eid, [{"artifact_id": artifact["artifact_id"],
                         "extraction": recipe}])["results"]
    assert item["status"] == "proposed" and item["role"] == "Purchase_orders"
    svc.approve_source_mapping(REVIEWER, eid, item["spec_id"])
    rec = svc.normalize_source(PREPARER, eid, item["spec_id"])["reconciliation"]
    assert rec["rows_loaded"] == 3 and rec["control_total"] == "558.75"


def test_vendor_contact_list_loads_as_reviewed_vendors(service):
    svc, eid = service
    _, proposal, normalized = _load(svc, eid, CONTACTS, "Vendor Contact List.xlsx",
                                    "Vendors", "qbo.vendor_contact_list.vendors")
    assert proposal["column_map"] == {"vendor_number": "Vendor", "vendor_name": "Vendor"}
    rec = normalized["reconciliation"]
    assert rec["rows_loaded"] == 26 and rec["rows_rejected"] == 0
    assert rec["diagnostics"]["duplicate_keys"] == []


def test_duplicates_are_named_not_crashes(service):
    svc, eid = service
    with pytest.raises(DuplicateError, match="already exists; open it instead"):
        svc.create_engagement(PARTNER, "Craig's Design", "2026-12-31")
    svc.store_source(PREPARER, eid, content=CONTACTS, media_type=XLSX_TYPE,
                     original_name="contacts.xlsx")
    with pytest.raises(DuplicateError, match="already in the engagement's evidence as 'contacts.xlsx'"):
        svc.store_source(PREPARER, eid, content=CONTACTS, media_type=XLSX_TYPE,
                         original_name="contacts again.xlsx")


def test_a_second_load_of_a_role_is_marked_as_replacing_the_first(service):
    svc, eid = service
    _load(svc, eid, BILL_PAYMENTS, "Bill Payment List.xlsx", "Payments",
          "qbo.bill_payment_list.payments")
    _load(svc, eid, BY_VENDOR, "Transaction List by Vendor.xlsx", "Payments",
          "qbo.transaction_list_by_vendor.payments")
    datasets = svc.sources(eid)["datasets"]
    assert [d["in_use"] for d in datasets] == [False, True]
    # Exactly the one the procedures read.
    used = svc._tables(eid)["Payments"]
    assert used.output_digest == datasets[1]["output_digest"]
    # Two independent QuickBooks reports agree on what was paid.
    assert datasets[0]["control_total"] == datasets[1]["control_total"] == "4539.50"


def test_a_loaded_mapping_is_not_loaded_twice(service):
    svc, eid = service
    _, proposal, _ = _load(svc, eid, CONTACTS, "contacts.xlsx", "Vendors",
                           "qbo.vendor_contact_list.vendors")
    with pytest.raises(DuplicateError, match="already loaded"):
        svc.normalize_source(PREPARER, eid, proposal["spec_id"])
    assert len(svc.sources(eid)["datasets"]) == 1


LEDGER = (FIXTURES / "general_ledger.xlsx").read_bytes()


def test_the_general_ledger_gives_the_ap_account_footed():
    rows = xlsx.preview(LEDGER, max_rows=xlsx.MAX_ROWS)[0]["rows"]
    ap = qb.gl_account_balance(rows)
    assert (ap["beginning"], ap["activity"], ap["ending"]) == ("1602.67", "0.00", "1602.67")
    assert ap["as_of"] == "2026-09-23" and ap["basis"] == "Accrual"
    # Cross-check on an account with activity: ending equals the running balance.
    assert qb.gl_account_balance(rows, "Mastercard")["ending"] == "157.72"
    with pytest.raises(qb.RecipeError, match="sub-account"):
        qb.gl_account_balance(rows, "Truck")
    assert qb.last_date("January 1-September 23, 2026") == "2026-09-23"
    assert qb.last_date("All Dates") is None


def test_ap_subledger_ties_to_the_ledger_through_the_review_path(service):
    svc, eid = service
    sub = svc.store_source(PREPARER, eid, content=UNPAID, media_type=XLSX_TYPE,
                           original_name="Unpaid Bills.xlsx")
    gl = svc.store_source(PREPARER, eid, content=LEDGER, media_type=XLSX_TYPE,
                          original_name="General Ledger.xlsx")
    assert svc.ap_control_candidates(eid) == {
        "subledger": [{"artifact_id": sub["artifact_id"], "original_name": "Unpaid Bills.xlsx"}],
        "ledger": [{"artifact_id": gl["artifact_id"], "original_name": "General Ledger.xlsx"}]}
    with pytest.raises(ValueError, match="not QuickBooks' standard Unpaid Bills"):
        svc.build_ap_control_balance(PREPARER, eid, subledger_artifact_id=gl["artifact_id"],
                                     ledger_artifact_id=gl["artifact_id"])

    built = svc.build_ap_control_balance(
        PREPARER, eid, subledger_artifact_id=sub["artifact_id"],
        ledger_artifact_id=gl["artifact_id"])
    assert (built["subledger_balance"], built["gl_balance"], built["difference"]) == \
           ("1602.67", "1602.67", "0.00")
    # The dates are stated, not assumed to match.
    assert any("not the engagement's period end 2026-12-31" in n for n in built["notes"])
    assert any("confirm both describe the same date" in n for n in built["notes"])

    # The schedule is an ordinary source: its name suggests the role, and it
    # crosses the reviewer like every other file.
    [item] = svc.propose_source_mappings(
        PREPARER, eid, [{"artifact_id": built["artifact_id"]}])["results"]
    assert item["role"] == "AP_control_balance" and item["refused_fields"] == []
    svc.approve_source_mapping(REVIEWER, eid, item["spec_id"])
    svc.normalize_source(PREPARER, eid, item["spec_id"])
    tie = next(p for p in svc.coverage(eid)["procedures"]
               if p["procedure_id"] == "ap.subledger_gl_balance_tie")
    assert tie["status"] == "executable"
    run = svc.run_procedure(PREPARER, eid, procedure_id="ap.subledger_gl_balance_tie")
    assert run["status"] == "completed"
    assert [f for f in svc.findings(eid)
            if f["procedure_id"] == "ap.subledger_gl_balance_tie"] == []


def test_quickbooks_reports_without_a_recipe_are_named_not_guessed(service):
    svc, eid = service
    gl = svc.store_source(PREPARER, eid, content=LEDGER, media_type=XLSX_TYPE,
                          original_name="general_ledger.xlsx")
    [sheet] = svc.workbook_preview(eid, gl["artifact_id"])["sheets"]
    assert sheet["recipes"] == [] and "do not map it as a table" in sheet["quickbooks_note"]
    applied = (FIXTURES / "bills_and_applied_payments.xlsx").read_bytes()
    rows = xlsx.preview(applied)[0]["rows"]
    assert "links a payment" in qb.unsupported_report(rows)
    assert qb.unsupported_report(xlsx.preview(UNPAID)[0]["rows"]) is None
