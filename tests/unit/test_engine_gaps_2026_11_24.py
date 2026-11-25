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
