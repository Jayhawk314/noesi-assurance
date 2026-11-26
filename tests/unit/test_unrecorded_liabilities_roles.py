# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The search for unrecorded liabilities with its own inputs (25 Nov 2026).

The search read Payments as the payments after year end and Vouchers as the
year-end listing, so an engagement that loads the year's own bills and
payments (for the duplicate, sequence and approval tests) could not run it.
Subsequent_payments and Unpaid_bills now serve each purpose, role by role,
with the older reading kept when they are not loaded. Invented data.
"""

from datetime import date
from decimal import Decimal as D

from procedures_ap.contracts import active_input_set
from procedures_ap.coverage import compile_coverage
from procedures_cycles.contracts import CYCLE_CONTRACTS_BY_ID
from procedures_cycles.engines import execute_procedure

PID = "ap.unrecorded_liabilities_search"
POLICIES = {"period_end": "2025-12-31", "search_threshold": "5000"}

# The year's own records: a December bill paid in December. Read as the
# payments after year end they would be selected (9,000 > 5,000) and, with no
# inspection, reported as "selected_not_inspected".
YEAR_VOUCHERS = [{"voucher_number": "V1/A-1", "voucher_amount": D("9000")},
                 {"voucher_number": "V1/A-2", "voucher_amount": D("6000")}]
YEAR_PAYMENTS = [{"payment_number": "CHK-100", "check_number": "100",
                  "voucher_number": "V1/A-1", "payment_amount": D("9000"),
                  "payment_date": date(2025, 12, 10)}]

# Unpaid at year end: A-2 (6,000).
UNPAID = [{"voucher_number": "V1/A-2", "voucher_amount": D("6000")}]


def pay(number, voucher, amount, when, check=""):
    return {"payment_number": number, "check_number": check, "voucher_number": voucher,
            "payment_amount": D(amount), "payment_date": when}


SUBSEQUENT = [
    pay("CHK-101", "V1/A-2", "6000", date(2026, 1, 8), "101"),     # listed, paid: included
    pay("CHK-102", "V2/R-9", "8000", date(2026, 1, 20), "102"),    # December work, never billed
    pay("EFT-0115", "", "7000", date(2026, 1, 15)),                # December sales tax
    pay("CHK-103", "V3/RENT-1", "12000", date(2026, 2, 2), "103"),  # February rent
    pay("CHK-104", "V4/X", "400", date(2026, 1, 9), "104"),         # below the threshold
]
INSPECTED = [
    {"payment_number": "CHK-101", "liability_date": date(2025, 12, 22)},
    {"payment_number": "CHK-102", "liability_date": date(2025, 12, 20)},
    {"payment_number": "EFT-0115", "liability_date": date(2025, 12, 31),
     "recorded_account": "2200 Sales Tax Payable"},
    {"payment_number": "CHK-103", "liability_date": date(2026, 2, 1)},
]


def keys(findings, verdict=None):
    return {tuple(f.key[1:]) for f in findings if verdict is None or f.verdict == verdict}


def test_the_search_reads_its_own_roles_and_ignores_the_years_records():
    tables = {"Vouchers": YEAR_VOUCHERS, "Payments": YEAR_PAYMENTS,
              "Unpaid_bills": UNPAID, "Subsequent_payments": SUBSEQUENT,
              "Disbursement_inspection": INSPECTED}
    findings, stats = execute_procedure(PID, tables, POLICIES)
    assert (stats["payments_from"], stats["listing_from"]) == ("Subsequent_payments",
                                                                 "Unpaid_bills")
    assert stats["population"] == 5 and stats["listed_vouchers"] == 1
    # above 5,000: 101 (6,000), 102 (8,000), EFT-0115 (7,000), 103 (12,000)
    assert stats["selected_above_threshold"] == ["101", "102", "EFT-0115", "103"]
    # the December check in the year's Payments is not part of the search
    assert not any("chk-100" in str(f.key) for f in findings)
    assert keys(findings) == {("chk-102", "unrecorded")}
    assert stats["outcomes"]["unrecorded"] == 1
    assert stats["outcomes"]["properly_included"] == 1          # A-2, 6,000 as listed
    assert stats["outcomes"]["recorded_outside_payables"] == 1  # the sales tax EFT
    assert stats["outcomes"]["properly_excluded"] == 1          # February rent
    assert D(stats["net_misstatement"]) == D("-8000")           # payables understated


def test_a_liability_traced_to_another_account_is_not_called_unrecorded():
    no_account = [dict(r) for r in INSPECTED]
    for r in no_account:
        r.pop("recorded_account", None)
    findings, stats = execute_procedure(
        PID, {"Unpaid_bills": UNPAID, "Subsequent_payments": SUBSEQUENT,
              "Disbursement_inspection": no_account}, POLICIES)
    # Without the auditor's note of where it was recorded, the December tax
    # paid in January is not on the payables listing: named as unrecorded.
    assert ("eft-0115", "unrecorded") in keys(findings, "CLASH")
    findings, _ = execute_procedure(
        PID, {"Unpaid_bills": UNPAID, "Subsequent_payments": SUBSEQUENT,
              "Disbursement_inspection": INSPECTED}, POLICIES)
    assert ("eft-0115", "unrecorded") not in keys(findings)


def test_a_payment_dated_by_year_end_in_the_register_is_named_and_left_out():
    register = SUBSEQUENT + [pay("CHK-099", "V9/Z", "20000", date(2025, 12, 30), "99"),
                             pay("CHK-098", "V9/Y", "15000", None, "98")]
    findings, stats = execute_procedure(
        PID, {"Unpaid_bills": UNPAID, "Subsequent_payments": register,
              "Disbursement_inspection": INSPECTED}, POLICIES)
    refused = [f for f in findings if f.key[2] == "not_after_period_end"]
    assert {f.key[1] for f in refused} == {"chk-099", "chk-098"}
    assert all(f.evidence["finding_class"] == "REFUSAL" for f in refused)
    assert "dated 2025-12-30" in next(f.reason for f in refused if f.key[1] == "chk-099")
    assert "undated" in next(f.reason for f in refused if f.key[1] == "chk-098")
    assert "99" not in stats["selected_above_threshold"]
    assert "98" not in stats["selected_above_threshold"]
    assert stats["population"] == 5


def test_each_new_role_serves_alone_and_the_older_reading_is_unchanged():
    # payments after year end, with the listing still in Vouchers
    _, stats = execute_procedure(
        PID, {"Vouchers": UNPAID, "Subsequent_payments": SUBSEQUENT,
              "Disbursement_inspection": INSPECTED}, POLICIES)
    assert (stats["payments_from"], stats["listing_from"]) == ("Subsequent_payments",
                                                                 "Vouchers")
    # the older reading: Payments and Vouchers
    old = [pay("CHK-101", "V1/A-2", "6000", date(2026, 1, 8), "101")]
    findings, stats = execute_procedure(
        PID, {"Vouchers": UNPAID, "Payments": old,
              "Disbursement_inspection": INSPECTED[:1]}, POLICIES)
    assert (stats["payments_from"], stats["listing_from"]) == ("Payments", "Vouchers")
    assert stats["outcomes"]["properly_included"] == 1 and findings == []


def test_coverage_names_the_input_set_the_engine_uses():
    contract = CYCLE_CONTRACTS_BY_ID[PID]
    loaded = {"Vouchers", "Payments", "Unpaid_bills", "Subsequent_payments",
              "Disbursement_inspection"}
    assert set(active_input_set(contract, lambda r: r in loaded)) == {
        "Subsequent_payments", "Unpaid_bills", "Disbursement_inspection"}
    assert set(active_input_set(contract, lambda r: r in loaded - {"Unpaid_bills"})) == {
        "Subsequent_payments", "Vouchers", "Disbursement_inspection"}
    assert set(active_input_set(contract, lambda r: r in {
        "Vouchers", "Payments", "Disbursement_inspection"})) == {
        "Payments", "Vouchers", "Disbursement_inspection"}
    fields = {"Subsequent_payments": ["payment_number", "voucher_number", "payment_amount",
                                      "payment_date"],
              "Unpaid_bills": ["voucher_number", "voucher_amount"],
              "Disbursement_inspection": ["payment_number", "liability_date"],
              "Payments": ["payment_number", "voucher_number", "payment_amount"],
              "Vouchers": ["voucher_number", "voucher_amount"]}
    inventory = {role: {"fields": f, "rows": 7 if role == "Subsequent_payments" else 3}
                 for role, f in fields.items()}
    coverage = compile_coverage(inventory, policies={"period_end": "2025-12-31",
                                                     "search_threshold": "5000"},
                                contracts=(contract,), executors=frozenset({PID}))
    row = next(r for r in coverage["procedures"] if r["procedure_id"] == PID)
    assert row["status"] == "executable"
    assert row["population"] == 7
    assert "satisfied_by" not in row


def test_the_subsequent_events_review_reads_the_register_and_counts_a_payment_once():
    policies = {"period_end": "2025-12-31", "report_date": "2026-03-20", "se_threshold": "5000"}
    year = YEAR_PAYMENTS + [pay("CHK-101", "V1/A-2", "6000", date(2026, 1, 8), "101")]
    findings, stats = execute_procedure(
        "completion.subsequent_events",
        {"Journal_entries": [{"entry_id": "J1", "account": "6000", "entry_date": date(2025, 6, 1),
                              "debit": D("100"), "credit": None}],
         "Payments": year, "Subsequent_payments": SUBSEQUENT}, policies)
    # in the window: CHK-101 (in both files, once), 102, EFT-0115, 103, 104
    assert stats["reviewed"]["payments"] == 5
    # at or above 5,000: 101, 102, EFT-0115, 103
    assert {f.key[1] for f in findings} == {"chk-101", "chk-102", "eft-0115", "chk-103"}
    assert next(f for f in findings if f.key[1] == "chk-102").evidence[
        "source_rows"][0]["table"] == "Subsequent_payments"


# ------------------------------------------- independent review, 25 Nov 2026
SE_POLICIES = {"period_end": "2025-12-31", "report_date": "2026-03-20", "se_threshold": "5000"}
JOURNAL = [{"entry_id": "J1", "account": "6000", "entry_date": date(2025, 6, 1),
            "debit": D("100"), "credit": None}]


def test_two_payments_lines_with_one_number_are_both_examined_as_before():
    lines = [pay("501", "", "6000", date(2026, 1, 9)), pay("501", "", "8000", date(2026, 1, 9))]
    findings, stats = execute_procedure("completion.subsequent_events",
                                        {"Journal_entries": JOURNAL, "Payments": lines},
                                        SE_POLICIES)
    assert stats["reviewed"]["payments"] == 2 and len(findings) == 2


def test_a_register_line_that_differs_from_payments_is_its_own_lead():
    findings, stats = execute_procedure(
        "completion.subsequent_events",
        {"Journal_entries": JOURNAL,
         "Payments": [pay("CHK-101", "V1/A-2", "6000", date(2026, 1, 8), "101")],
         "Subsequent_payments": [pay("CHK-101", "V1/A-2", "6500", date(2026, 1, 8), "101")]},
        SE_POLICIES)
    assert stats["reviewed"]["payments"] == 2
    assert {tuple(f.key[1:]) for f in findings} == {("chk-101", "payment"),
                                                    ("chk-101", "payment_in_register")}


def test_coverage_and_the_run_choose_the_same_inputs_when_a_field_is_missing():
    # the register loaded without a voucher number column: it does not serve
    register = [{k: v for k, v in p.items() if k != "voucher_number"} for p in SUBSEQUENT]
    tables = {"Payments": [pay("CHK-101", "V1/A-2", "6000", date(2026, 1, 8), "101")],
              "Subsequent_payments": register, "Unpaid_bills": UNPAID,
              "Disbursement_inspection": INSPECTED[:1], "Vouchers": YEAR_VOUCHERS}
    _, stats = execute_procedure(PID, tables, POLICIES)
    assert (stats["payments_from"], stats["listing_from"]) == ("Payments", "Unpaid_bills")
    inventory = {role: {"fields": sorted(set().union(*(r.keys() for r in rows))),
                        "rows": len(rows)} for role, rows in tables.items()}
    coverage = compile_coverage(inventory, policies=POLICIES,
                                contracts=(CYCLE_CONTRACTS_BY_ID[PID],),
                                executors=frozenset({PID}))
    row = coverage["procedures"][0]
    assert row["status"] == "executable"
    assert row["satisfied_by"] == ["Payments", "Unpaid_bills", "Disbursement_inspection"]
    assert row["population"] == 1


def test_coverage_names_only_the_missing_inspection_for_the_older_inputs():
    inventory = {"Payments": {"fields": ["payment_number", "voucher_number", "payment_amount"],
                              "rows": 40},
                 "Vouchers": {"fields": ["voucher_number", "voucher_amount"], "rows": 30}}
    coverage = compile_coverage(inventory, policies=POLICIES,
                                contracts=(CYCLE_CONTRACTS_BY_ID[PID],),
                                executors=frozenset({PID}))
    row = coverage["procedures"][0]
    assert row["status"] == "blocked"
    assert row["missing_roles"] == ["Disbursement_inspection"]
    assert row["population"] == 40


def test_an_inspected_register_row_refused_for_its_date_is_not_also_an_orphan():
    register = SUBSEQUENT + [pay("CHK-099", "V9/Z", "20000", date(2025, 12, 30), "99")]
    inspected = INSPECTED + [{"payment_number": "CHK-099", "liability_date": date(2025, 12, 1)}]
    findings, _ = execute_procedure(
        PID, {"Unpaid_bills": UNPAID, "Subsequent_payments": register,
              "Disbursement_inspection": inspected}, POLICIES)
    assert ("chk-099", "not_after_period_end") in keys(findings)
    assert ("chk-099", "inspection_without_payment") not in keys(findings)


def test_the_new_roles_take_no_file_from_the_older_ones():
    import procedures_cycles.roles  # noqa: F401  (registers the cycle roles)
    from procedures_ap.ingest import infer_role, infer_role_from_headers
    assert infer_role("Unpaid_Bills.xlsx") == "Vouchers"
    assert infer_role("unpaid_bills_report.xlsx") == "Vouchers"
    assert infer_role("subsequent_payments.csv") == "Subsequent_payments"
    assert infer_role("year_end_unpaid_bills.csv") == "Unpaid_bills"
    assert infer_role_from_headers(["Payment Number", "Vendor Number", "Payment Date",
                                    "Payment Amount", "Check Number", "Voucher Number"]) == "Payments"
    assert infer_role_from_headers(["Voucher Number", "Vendor Number", "Invoice Number",
                                    "Voucher Date", "Voucher Amount"]) == "Vouchers"


def _tb(account, balance, side, description="Sales Tax Payable"):
    return [{"account": "1010", "description": "Cash", "balance": D("50000"), "side": "DR"},
            {"account": account, "description": description, "balance": D(balance),
             "side": side}]


def _search(tb, recorded="2200 Sales Tax Payable"):
    inspected = [dict(r) for r in INSPECTED]
    inspected[2]["recorded_account"] = recorded
    tables = {"Unpaid_bills": UNPAID, "Subsequent_payments": SUBSEQUENT,
              "Disbursement_inspection": inspected}
    if tb is not None:
        tables["Trial_balance"] = tb
    return execute_procedure(PID, tables, POLICIES)


def test_a_recorded_account_is_checked_against_the_trial_balance():
    # 26 Nov 2026: the account the auditor traced a liability to was taken at
    # its word. With a trial balance loaded it must exist there and its
    # period-end credit must cover the liability. Invented figures.
    for recorded in ("2200", "2200 Sales Tax Payable", "sales tax payable"):
        findings, stats = _search(_tb("2200", "9500", "CR"), recorded)
        assert stats["recorded_accounts_checked"] is True
        assert stats["outcomes"]["recorded_outside_payables"] == 1, recorded
        assert not {k for k in keys(findings) if k[0] == "eft-0115"}, recorded
    # A QuickBooks-style account cell, number and name together.
    findings, stats = _search(_tb("2200 Sales Tax Payable", "9500", "CR"), "2200")
    assert stats["outcomes"]["recorded_outside_payables"] == 1
    assert not {k for k in keys(findings) if k[0] == "eft-0115"}


def test_a_recorded_account_missing_from_the_trial_balance_is_refused():
    findings, stats = _search(_tb("2200", "9500", "CR"), "2210")
    assert ("eft-0115", "recorded_account_not_in_trial_balance") in keys(findings, "AMBIGUOUS")
    # Neither recorded nor unrecorded: the inspection must be corrected first.
    assert stats["outcomes"]["recorded_outside_payables"] == 0
    assert ("eft-0115", "unrecorded") not in keys(findings)


def test_a_recorded_account_too_small_to_hold_the_liability_is_a_lead():
    findings, stats = _search(_tb("2200", "3000", "CR"))   # 3,000 credit < 7,000 owed
    (lead,) = [f for f in findings if f.key[1:] == ("eft-0115", "recorded_account_below_liability")]
    assert lead.verdict == "TENSION" and lead.score == D("4000")
    assert stats["outcomes"]["recorded_outside_payables"] == 1
    findings, _ = _search(_tb("2200", "500", "DR"))        # a debit holds none of it
    (lead,) = [f for f in findings if f.key[1:] == ("eft-0115", "recorded_account_below_liability")]
    assert lead.score == D("7000")


def test_without_a_trial_balance_the_recorded_account_is_taken_as_stated():
    findings, stats = _search(None, "2210")
    assert stats["recorded_accounts_checked"] is False
    assert stats["outcomes"]["recorded_outside_payables"] == 1
    assert not {k for k in keys(findings) if k[0] == "eft-0115"}
