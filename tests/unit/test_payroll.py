# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Payroll: register re-performance, ghost/terminated leads, register to ledger."""

from datetime import date
from decimal import Decimal as D

import pytest

from procedures_cycles.common import PolicyError
from procedures_cycles.engines import execute_procedure

PE = "2025-12-31"


def pay(emp, paid, gross, taxes, net, *, hours=None, rate=None, check=None):
    return {"employee_id": emp, "pay_date": date.fromisoformat(paid), "gross": D(gross),
            "tax_withheld": D(taxes), "net": D(net), "hours": hours, "pay_rate": rate,
            "check_number": check or f"{emp}-{paid}"}


REGISTER = [
    pay("E1", "2025-06-15", "2000.00", "400.00", "1600.00", hours="80", rate="25.00"),
    pay("E2", "2025-06-15", "1800.00", "360.00", "1500.00"),               # net wrong
    pay("E3", "2025-06-15", "2100.00", "420.00", "1680.00", hours="80", rate="25.00"),
    pay("E4", "2025-06-15", "1500.00", "300.00", "1200.00"),               # not on master
    pay("E5", "2025-08-15", "1000.00", "200.00", "800.00"),                # after termination
    pay("E1", "2025-06-15", "2000.00", "400.00", "1600.00", check="dup"),  # twice
    pay("E6", "2026-01-15", "900.00", "180.00", "720.00"),                 # next period
]
MASTER = [
    {"employee_id": "E1", "bank_account": "111-222", "address": "1 Elm St"},
    {"employee_id": "E2", "bank_account": "333-444", "address": "9 Oak Ave"},
    {"employee_id": "E3", "bank_account": "111-222", "address": "5 Pine Rd"},  # shares E1's
    {"employee_id": "E5", "termination_date": date(2025, 7, 31),
     "bank_account": "555-666", "address": "9  oak ave"},                     # shares E2's
    {"employee_id": "E6", "bank_account": "777-888", "address": "2 Ash Ct"},
]


def leads(findings):
    return {f.key[1:] for f in findings}


def test_register_tests_find_each_planted_payroll_error():
    findings, stats = execute_procedure(
        "payroll.register_tests", {"Payroll_register": REGISTER, "Payroll_master": MASTER},
        {})
    assert leads(findings) == {
        ("e2", "E2-2025-06-15", "net_pay_differs"),
        ("e3", "E3-2025-06-15", "gross_pay_differs"),
        ("e4", "E4-2025-06-15", "not_on_employee_master"),
        ("e5", "E5-2025-08-15", "paid_after_termination"),
        ("e1", "2025-06-15", "paid_twice_same_date"),
        ("e1,e3", "shared_bank_account"),
        ("e2,e5", "shared_address"),
    }
    assert stats["final_pay_grace_days"] == 0


def test_a_final_check_inside_the_grace_period_is_not_a_lead():
    findings, stats = execute_procedure(
        "payroll.register_tests", {"Payroll_register": REGISTER, "Payroll_master": MASTER},
        {"payroll_final_pay_days": "20"})
    assert ("e5", "E5-2025-08-15", "paid_after_termination") not in leads(findings)
    assert stats["final_pay_grace_days"] == 20


def test_register_to_ledger_compares_the_periods_gross_with_named_wage_accounts():
    tb = [{"account": "6100", "balance": D("9000.00")},
          {"account": "6110", "balance": D("1400.00")},
          {"account": "4000", "balance": D("-50000.00")}]
    tables = {"Payroll_register": REGISTER, "Trial_balance": tb}
    findings, stats = execute_procedure(
        "payroll.register_to_ledger", tables,
        {"period_end": PE, "payroll_expense_accounts": "6100, 6110"})
    # 2000+1800+2100+1500+1000+2000 in the period; E6 is next period
    assert stats["register_gross"] == "10400.00" and stats["ledger_wages"] == "10400.00"
    assert findings == [] and stats["payments_outside_period"] == 1
    findings, stats = execute_procedure(
        "payroll.register_to_ledger", tables,
        {"period_end": PE, "payroll_expense_accounts": "6100"})
    [gap] = findings
    assert gap.verdict == "TENSION" and stats["difference"] == "1400.00"


def test_register_to_ledger_needs_the_wage_accounts_named():
    with pytest.raises(PolicyError, match="payroll_expense_accounts"):
        execute_procedure("payroll.register_to_ledger",
                          {"Payroll_register": REGISTER,
                           "Trial_balance": [{"account": "6100", "balance": D("1")}]},
                          {"period_end": PE})


def test_net_pay_check_that_cannot_run_is_said_not_skipped():
    register = [{"employee_id": "E1", "pay_date": date(2025, 6, 15),
                 "gross": D("1000.00"), "net": D("900.00")}]         # no withholding column
    findings, stats = execute_procedure(
        "payroll.register_tests",
        {"Payroll_register": register, "Payroll_master": [{"employee_id": "E1"}]}, {})
    assert ("net_pay", "not_performed") in leads(findings)
    assert "net_pay" in stats["not_performed"]


def test_taxes_withheld_heading_is_recognized():
    from procedures_ap.ingest import propose_mapping
    from procedures_cycles.roles import register_roles
    register_roles()
    spec = propose_mapping("Payroll_register",
                           ["Employee ID", "Check Date", "Gross Pay", "Taxes Withheld",
                            "Net Pay"])
    assert spec.column_map["tax_withheld"] == "Taxes Withheld"
