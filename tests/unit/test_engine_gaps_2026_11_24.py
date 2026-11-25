# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Three engine gaps a teaching case exposed (2026-11-24), fixed generically and
tested here on invented data, never on the case (ROADMAP rule):

1. the round-trip screen's 2% amount tolerance and 30-day window are now the
   auditor's settings (defaults unchanged);
2. payroll register tests compare the accounts pay actually went to, from the
   register itself;
3. a new cash test lists cash deposits kept under the currency-reporting line.
"""

from datetime import date

import pytest

from procedures_ap.engines import EXECUTORS as AP
from procedures_cycles import cash, payroll
from procedures_cycles.common import PolicyError
from procedures_cycles.contracts import CYCLE_CONTRACTS_BY_ID, SCOPE_OF


def _rows(items):
    return [{**r, "source_row": i + 2} for i, r in enumerate(items)]


# ---------------------------------------------------------------- 1. round trips
def _loop(skim):
    out, back = 10000, 10000 - skim
    return {"Value_flows": _rows([
        {"source_entity": "the company", "target_entity": "Cousin Co", "amount": float(out),
         "flow_date": date(2025, 3, 12), "relation": "payment"},
        {"source_entity": "Cousin Co", "target_entity": "the company", "amount": float(back),
         "flow_date": date(2025, 3, 18), "relation": "receipt"}])}


def test_round_trip_default_is_still_two_percent():
    findings, stats = AP["forensic.closed_value_flow"](_loop(270), {})
    assert findings == []
    assert "amount_tolerance_source" not in stats      # the Phase 0 summary, unchanged
    found, _ = AP["forensic.closed_value_flow"](_loop(150), {})
    assert len(found) == 1
    assert found[0].evidence["amount_tolerance"] == 0.02 and found[0].evidence["max_days"] == 30


def test_round_trip_tolerance_is_the_auditors_setting():
    findings, stats = AP["forensic.closed_value_flow"](
        _loop(270), {"value_flow_amount_tolerance_pct": "5"})
    assert len(findings) == 1
    assert stats["amount_tolerance_pct"] == "5" and stats["amount_tolerance_source"] == "policy"
    assert findings[0].evidence["amount_tolerance"] == 0.05


def test_round_trip_window_is_the_auditors_setting():
    findings, stats = AP["forensic.closed_value_flow"](
        _loop(100), {"value_flow_window_days": "3"})
    assert findings == [] and stats["window_days"] == 3
    assert stats["window_source"] == "policy" and stats["amount_tolerance_source"] == "default"


@pytest.mark.parametrize("name,value", [("value_flow_amount_tolerance_pct", "80"),
                                        ("value_flow_amount_tolerance_pct", "x"),
                                        ("value_flow_window_days", "0"),
                                        ("value_flow_window_days", "two")])
def test_round_trip_settings_out_of_range_are_refused(name, value):
    with pytest.raises(ValueError):
        AP["forensic.closed_value_flow"](_loop(100), {name: value})


# ---------------------------------------------------------------- 2. payroll accounts
def _payroll(register_accounts):
    master = _rows([
        {"employee_id": "E1", "name": "Ann Lee", "bank_account": "BK-1"},
        {"employee_id": "E2", "name": "Bo Diaz", "bank_account": "BK-2",
         "termination_date": "2025-01-31"}])
    register = _rows([
        {"employee_id": emp, "pay_date": "2025-03-07", "gross": "1000.00", "net": "800.00",
         "tax_withheld": "200.00", "check_number": f"DD-{emp}", "bank_account": acct}
        for emp, acct in register_accounts])
    return {"Payroll_master": master, "Payroll_register": register}


def _by_test(findings, name):
    return [f for f in findings if f.key[-1] == name]


def test_a_ghost_off_the_master_sharing_an_account_is_found_from_the_register():
    findings, stats = payroll.register_tests(
        _payroll([("E1", "BK-1"), ("E2", "BK-2"), ("E9", "BK-2")]), {})
    shared = _by_test(findings, "register_shared_bank_account")
    assert len(shared) == 1
    assert shared[0].evidence["employees"] == ["e2", "e9"]     # ids compared as key text
    assert shared[0].evidence["not_on_master"] == ["e9"]
    assert stats["register_bank_accounts"] == "compared"


def test_pay_sent_to_an_account_other_than_the_masters_is_a_lead():
    findings, _ = payroll.register_tests(_payroll([("E1", "BK-77")]), {})
    moved = _by_test(findings, "paid_to_other_account")
    assert len(moved) == 1 and moved[0].evidence["master_account"] == "bk-1"


def test_a_sharing_already_on_the_master_is_not_reported_twice():
    data = _payroll([("E1", "BK-1"), ("E2", "BK-1")])
    data["Payroll_master"][1]["bank_account"] = "BK-1"
    findings, _ = payroll.register_tests(data, {})
    assert len(_by_test(findings, "shared_bank_account")) == 1
    assert _by_test(findings, "register_shared_bank_account") == []


def test_a_register_without_accounts_says_so():
    data = _payroll([("E1", "")])
    _, stats = payroll.register_tests(data, {})
    assert stats["register_bank_accounts"].startswith("not in the register")


# ---------------------------------------------------------------- 3. deposits
def _deposits(items):
    return {"Deposits": _rows([
        {"reference": f"D{i}", "deposit_date": when, "amount": amt, "deposit_type": kind,
         "location": where} for i, (when, amt, kind, where) in enumerate(items, 1)])}


POLICY = {"structuring_threshold": "10000"}


def test_one_days_cash_split_under_the_line_is_a_lead():
    data = _deposits([("2025-04-07", "9400.00", "cash", "Main St"),
                      ("2025-04-07", "6200.00", "cash", "Strip"),
                      ("2025-04-08", "9900.00", "cash", "Main St"),
                      ("2025-04-09", "4000.00", "cash", "Main St"),
                      ("2025-04-09", "3000.00", "cash", "Main St"),
                      ("2025-04-10", "15000.00", "card settlement", "processor")])
    findings, stats = cash.deposit_structuring(data, POLICY)
    split = [f for f in findings if f.key[-1] == "same_day_split"]
    assert [f.evidence["deposit_date"] for f in split] == ["2025-04-07"]
    assert split[0].evidence["locations"] == ["Main St", "Strip"]
    assert stats["cash_deposits"] == 5 and stats["same_day_split_days"] == 1


def test_a_pile_up_just_under_the_line_is_a_lead_but_a_spread_is_not():
    piled = _deposits([("2025-05-0%d" % d, "95%02d.00" % d, "cash", "Main St")
                       for d in range(1, 7)])
    findings, stats = cash.deposit_structuring(piled, POLICY)
    band = [f for f in findings if f.key[1] == "band"]
    assert len(band) == 1 and stats["in_band"] == 6 and stats["band_just_below"] == 0
    spread = _deposits([("2025-05-01", "9500.00", "cash", "A"), ("2025-05-02", "8500.00", "cash", "A"),
                        ("2025-05-03", "8600.00", "cash", "A"), ("2025-05-04", "9600.00", "cash", "A")])
    findings, _ = cash.deposit_structuring(spread, POLICY)
    assert [f for f in findings if f.key[1] == "band"] == []


def test_exactly_the_threshold_is_under_the_line():
    data = _deposits([("2025-06-02", "10000.00", "cash", "A"),
                      ("2025-06-02", "500.00", "cash", "A")])
    findings, stats = cash.deposit_structuring(data, POLICY)
    assert stats["over_threshold"] == 0
    assert [f.key[-1] for f in findings] == ["same_day_split"]


def test_no_type_means_every_deposit_is_tested_and_it_says_so():
    data = _deposits([("2025-06-02", "9500.00", "", "A")])
    findings, stats = cash.deposit_structuring(data, POLICY)
    assert stats["cash_deposits"] == 1
    assert any(f.key == ("cash.deposit_structuring", "deposit_type", "not_supplied")
               for f in findings)


def test_no_cash_at_all_is_not_tested_never_clean():
    data = _deposits([("2025-06-02", "9500.00", "check", "A")])
    findings, stats = cash.deposit_structuring(data, POLICY)
    assert stats["cash_deposits"] == 0 and findings[0].verdict == "AMBIGUOUS"


def test_the_threshold_is_required_and_the_band_is_checked():
    data = _deposits([("2025-06-02", "9500.00", "cash", "A")])
    with pytest.raises(PolicyError):
        cash.deposit_structuring(data, {})
    with pytest.raises(PolicyError):
        cash.deposit_structuring(data, {**POLICY, "structuring_band_pct": "60"})


def test_the_deposit_test_is_a_cash_procedure_chosen_not_on_by_default():
    contract = CYCLE_CONTRACTS_BY_ID["cash.deposit_structuring"]
    assert SCOPE_OF["cash.deposit_structuring"] == "cash"
    assert contract.default_selected is False
    assert contract.required_policies == ("structuring_threshold",)


# ---------------------------------------------------------------- independent review, 2026-11-24
def test_cashiers_checks_and_cash_letters_are_not_cash():
    data = _deposits([("2025-07-01", "9500.00", "cashier's check", "A"),
                      ("2025-07-01", "9500.00", "cash letter", "A"),
                      ("2025-07-01", "9500.00", "non-cash", "A"),
                      ("2025-07-01", "900.00", "Cash", "A")])
    _, stats = cash.deposit_structuring(data, POLICY)
    assert stats["cash_deposits"] == 1


def test_undated_cash_is_refused_not_grouped_as_one_day():
    data = _deposits([("", "9500.00", "cash", "A"), ("not a date", "9600.00", "cash", "B")])
    findings, stats = cash.deposit_structuring(data, POLICY)
    assert stats["undated"] == 2
    assert [f.key[1:] for f in findings] == [("deposit_date", "not_readable"), ("cash", "not_tested")]


def test_untyped_rows_among_typed_ones_are_named():
    data = _deposits([("2025-07-01", "9500.00", "cash", "A"), ("2025-07-01", "9600.00", "", "A")])
    findings, stats = cash.deposit_structuring(data, POLICY)
    assert stats["untyped"] == 1
    assert any(f.key[1:] == ("deposit_type", "missing_on_some") for f in findings)


# ---------------------------------------------------------------- supplier statements and bank confirmations
from procedures_cycles import payables as _pay  # noqa: E402


def _ap(statement):
    return {
        "Vendors": _rows([{"vendor_number": "V1", "vendor_name": "Harbor Spirits Inc."}]),
        "Vouchers": _rows([
            {"voucher_number": "V1/A-1", "invoice_number": "A-1", "vendor_number": "V1",
             "voucher_amount": "1000.00", "voucher_date": "2025-12-01"},
            {"voucher_number": "V1/A-2", "invoice_number": "A-2", "vendor_number": "V1",
             "voucher_amount": "500.00", "voucher_date": "2025-12-10"}]),
        "Payments": _rows([
            {"payment_number": "CHK-10", "check_number": "10", "vendor_number": "V1",
             "voucher_number": "V1/A-1", "payment_amount": "1000.00", "payment_date": "2025-12-08"},
            {"payment_number": "CHK-11", "check_number": "11", "vendor_number": "V1",
             "voucher_number": "V1/A-2", "payment_amount": "500.00", "payment_date": "2025-12-29"}]),
        "Vendor_statements": _rows(statement)}


def _line(ref, amount, kind="invoice", when="2025-12-01", vendor="Harbor Spirits Inc."):
    return {"vendor": vendor, "statement_date": "2025-12-31", "item_date": when, "item_type": kind,
            "reference": ref, "amount": amount}


PE = {"period_end": "2025-12-31"}


def test_a_statement_that_agrees_reconciles_with_a_payment_in_transit():
    data = _ap([_line("A-1", "1000.00"), _line("A-2", "500.00", when="2025-12-10"),
                _line("check 10", "-1000.00", "payment received", "2025-12-11")])
    findings, stats = _pay.vendor_statement_reconciliation(data, PE)
    assert findings == []
    v = stats["per_vendor"]["v1"]
    assert v["payments_in_transit"] == ["11"] and v["unexplained"] == 0


def test_an_invoice_only_the_supplier_has_is_an_unrecorded_liability():
    data = _ap([_line("A-1", "1000.00"), _line("A-2", "500.00", when="2025-12-10"),
                _line("A-3", "740.00", when="2025-12-22"),
                _line("check 10", "-1000.00", "payment received", "2025-12-11")])
    findings, stats = _pay.vendor_statement_reconciliation(data, PE)
    assert [f.key[2:] for f in findings] == [("a3", "invoice_not_in_books")]
    assert stats["per_vendor"]["v1"]["unexplained"] == 0


def test_amount_differences_missing_bills_and_stale_payments_are_listed():
    data = _ap([_line("A-1", "1100.00")])
    data["Payments"][1]["payment_date"] = "2025-12-02"         # credited nowhere, 29 days before
    findings, stats = _pay.vendor_statement_reconciliation(data, PE)
    kinds = sorted(f.key[-1] for f in findings)
    assert kinds == ["amount_differs", "bill_not_on_statement", "payment_not_credited",
                     "payment_not_credited"]
    assert stats["per_vendor"]["v1"]["unexplained"] == 0


def test_an_unknown_supplier_is_refused():
    findings, _ = _pay.vendor_statement_reconciliation(_ap([_line("A-1", "1000.00", vendor="Nobody")]), PE)
    assert findings[0].verdict == "AMBIGUOUS" and findings[0].key[-1] == "vendor_not_identified"


def _rec_and_conf(conf):
    return {"Bank_reconciliation": _rows([
                {"account": "Operating", "item_type": "bank_balance", "amount": "802118.64"},
                {"account": "Payroll", "item_type": "bank_balance", "amount": "20000.00"}]),
            "Bank_confirmations": _rows(conf)}


def test_bank_confirmations_agree_or_name_each_problem():
    ok = _rec_and_conf([{"account": "Operating", "confirmed_balance": "802118.64", "as_of": "2025-12-31",
                         "loans_and_other": "none"},
                        {"account": "Payroll", "confirmed_balance": "20000.00", "as_of": "2025-12-31"}])
    findings, stats = cash.bank_confirmation(ok, PE)
    assert findings == [] and stats["confirmed_accounts"] == 2
    bad = _rec_and_conf([{"account": "Operating", "confirmed_balance": "802000.00", "as_of": "2025-12-30",
                          "loans_and_other": "line of credit 50,000"},
                         {"account": "Owner reserve", "confirmed_balance": "75000.00", "as_of": "2025-12-31"}])
    findings, _ = cash.bank_confirmation(bad, PE)
    assert sorted(f.key[1:] for f in findings) == sorted([
        ("operating", "not_as_of_period_end"), ("operating", "balance_differs"),
        ("operating", "obligation_reported"), ("owner reserve", "account_not_reconciled"),
        ("payroll", "not_confirmed")])


def test_a_credit_only_the_supplier_shows_is_explained_not_doubled():
    """Independent review 2026-11-24: the sign of a supplier-only payment was wrong."""
    data = _ap([_line("A-1", "1000.00"), _line("A-2", "500.00", when="2025-12-10"),
                _line("check 10", "-1000.00", "payment received", "2025-12-11"),
                _line("check 99", "-400.00", "payment received", "2025-12-12")])
    findings, stats = _pay.vendor_statement_reconciliation(data, PE)
    assert [f.key[-1] for f in findings] == ["payment_not_in_books"]
    assert stats["per_vendor"]["v1"]["unexplained"] == 0


def test_references_match_whole_or_by_digits_and_a_balance_forward_is_read():
    data = _ap([_line("Balance forward", "0.00", "balance forward", "2025-11-30"),
                _line("INV A-1", "1000.00"), _line("A-2", "500.00", when="2025-12-10"),
                _line("Check #10", "-1000.00", "payment received", "2025-12-11")])
    findings, stats = _pay.vendor_statement_reconciliation(data, PE)
    assert findings == [] and stats["per_vendor"]["v1"]["unexplained"] == 0


@pytest.mark.parametrize("field,value", [("account", ""), ("confirmed_balance", ""),
    ("confirmed_balance", "not money"), ("confirmed_balance", "NaN"),
    ("as_of", ""), ("as_of", "2025-12-31 pending")])
def test_incomplete_bank_confirmation_is_refused_never_compared(field, value):
    row = {"account": "Operating", "confirmed_balance": "802118.64", "as_of": "2025-12-31"}
    row[field] = value
    findings, stats = cash.bank_confirmation(_rec_and_conf([row]), PE)
    refused = [f for f in findings if f.evidence.get("finding_class") == "REFUSAL"]
    assert len(refused) == 1 and field in refused[0].evidence["invalid_fields"]
    assert stats["confirmed_accounts"] == 0
    assert not any(f.key[-1] in ("balance_differs", "not_as_of_period_end", "account_not_reconciled") for f in findings)


def test_zero_balance_is_a_valid_confirmation_and_none_punctuation_is_not_a_loan():
    data = _rec_and_conf([{"account": "Operating", "confirmed_balance": "0.00", "as_of": "2025-12-31", "loans_and_other": "None."}])
    data["Bank_reconciliation"] = _rows([{"account": "Operating", "item_type": "bank_balance", "amount": "0.00"}])
    findings, stats = cash.bank_confirmation(data, PE)
    assert findings == [] and stats["confirmed_accounts"] == 1


def test_whole_invoice_references_take_priority_over_colliding_numeric_aliases():
    data = _ap([_line("A-1", "1000.00"), _line("A-2", "500.00", when="2025-12-10"),
                _line("check 10", "-1000.00", "payment received", "2025-12-11")])
    # A composite voucher's digits collide with another invoice's digits.
    data["Vouchers"][0]["voucher_number"] = "V-2/A-2"
    findings, stats = _pay.vendor_statement_reconciliation(data, PE)
    assert findings == [] and stats["per_vendor"]["v1"]["unexplained"] == 0


def test_a_used_ambiguous_numeric_reference_is_refused():
    data = _ap([_line("Invoice 1", "1000.00")])
    data["Vouchers"][1]["invoice_number"] = "B-1"
    findings, _ = _pay.vendor_statement_reconciliation(data, PE)
    assert any(f.key[-1] == "duplicate_vouchers_reference" and f.evidence["finding_class"] == "REFUSAL" for f in findings)
    assert not any(f.key[-1] == "invoice_not_in_books" for f in findings)


def test_a_credit_memo_recorded_in_both_books_and_statement_is_matched():
    data = _ap([_line("A-1", "1000.00"), _line("CM-2", "-100.00", "credit memo", "2025-12-10")])
    data["Vouchers"][1].update(invoice_number="CM-2", voucher_amount="-100.00")
    data["Payments"] = []
    findings, stats = _pay.vendor_statement_reconciliation(data, PE)
    assert findings == [] and stats["per_vendor"]["v1"]["books_balance"] == 900


def test_an_unrecorded_credit_memo_is_a_lead_without_a_spurious_balance_difference():
    data = _ap([_line("A-1", "1000.00"), _line("A-2", "500.00", when="2025-12-10"),
                _line("CM-9", "-100.00", "credit memo", "2025-12-12")])
    data["Payments"] = []
    findings, stats = _pay.vendor_statement_reconciliation(data, PE)
    assert [f.key[-1] for f in findings] == ["credit_not_in_books"]
    assert stats["per_vendor"]["v1"]["unexplained"] == 0
