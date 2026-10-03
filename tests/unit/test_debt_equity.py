# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Debt and equity: schedule rollforward and interest, covenants, equity rollforward.

Figures are worked by hand in the comments.
"""

from decimal import Decimal as D

import pytest

from procedures_cycles.common import PolicyError
from procedures_cycles.engines import execute_procedure

PE = "2025-12-31"


def loan(lid, begin, borrowed, repaid, end, rate, interest):
    return {"loan_id": lid, "beginning_balance": D(begin), "borrowings": D(borrowed),
            "repayments": D(repaid), "ending_balance": D(end), "interest_rate": rate,
            "interest_expense": D(interest)}


LOANS = [
    # average 175000 x 6.5% = 11375, as recorded
    loan("L1", "200000", "0", "50000", "150000", "6.5%", "11375.00"),
    # average 37500 x 7% = 2625; 1200 recorded (borrowed late?) -> a lead
    loan("L2", "0", "80000", "5000", "75000", "0.07", "1200.00"),
    # 30000 - 10000 = 20000, the schedule says 21000; average 25500 x 5% = 1275
    loan("L3", "30000", "0", "10000", "21000", "5", "1275.00"),
]
TB = [
    {"account": "1000", "balance": D("50000"), "prior_balance": D("40000")},
    {"account": "1100", "balance": D("70000"), "prior_balance": D("65000")},
    {"account": "2000", "balance": D("-60000"), "prior_balance": D("-55000")},
    {"account": "2100", "balance": D("-20000"), "prior_balance": D("-18000")},
    # 150000 + 75000 + 21000 = 246000; beginning 200000 + 0 + 30000 = 230000
    {"account": "2300", "balance": D("-246000"), "prior_balance": D("-230000")},
    {"account": "3000", "balance": D("-100000"), "prior_balance": D("-100000")},
    {"account": "3200", "balance": D("-55000"), "prior_balance": D("-40000")},
    # 11375 + 1200 + 1275 = 13850
    {"account": "6900", "balance": D("13850.00"), "prior_balance": D("15000")},
]
DEBT_POLICIES = {"period_end": PE, "debt_accounts": "2300",
                 "debt_interest_tolerance_pct": "10", "debt_interest_accounts": "6900"}


def keys(findings):
    return {tuple(f.key[1:]) for f in findings}


def test_debt_schedule_foots_ties_and_tests_interest():
    findings, stats = execute_procedure(
        "debt.rollforward_and_interest", {"Debt_schedule": LOANS, "Trial_balance": TB},
        DEBT_POLICIES)
    assert keys(findings) == {("l2", "interest_unexpected"), ("l3", "does_not_foot")}
    assert (stats["beginning_debt"], stats["ending_debt"]) == ("230000.00", "246000.00")


def test_debt_schedule_that_disagrees_with_the_ledger():
    tb = [dict(r, balance=D("-245000")) if r["account"] == "2300" else r for r in TB]
    findings, _ = execute_procedure(
        "debt.rollforward_and_interest", {"Debt_schedule": LOANS, "Trial_balance": tb},
        DEBT_POLICIES)
    assert ("ending_debt", "schedule_to_ledger") in keys(findings)


def test_interest_is_not_tested_without_a_tolerance():
    policies = {k: v for k, v in DEBT_POLICIES.items()
                if k != "debt_interest_tolerance_pct"}
    findings, stats = execute_procedure(
        "debt.rollforward_and_interest", {"Debt_schedule": LOANS, "Trial_balance": TB},
        policies)
    assert keys(findings) == {("l3", "does_not_foot")}
    assert "interest" in stats["not_performed"]


def test_debt_accounts_must_be_named():
    with pytest.raises(PolicyError, match="debt_accounts"):
        execute_procedure("debt.rollforward_and_interest",
                          {"Debt_schedule": LOANS, "Trial_balance": TB},
                          {"period_end": PE})


COVENANTS = [
    # (50000 + 70000) / (60000 + 20000) = 1.5, at least 1.25: met
    {"covenant": "Current ratio", "numerator_accounts": "1000, 1100",
     "denominator_accounts": "2000, 2100", "operator": ">=", "threshold": D("1.25")},
    # 246000 / 100000 = 2.46, at most 2.0: breached
    {"covenant": "Debt to equity", "numerator_accounts": "2300",
     "denominator_accounts": "3000", "operator": "<=", "threshold": D("2.0")},
    # 100000, at least 75000: met
    {"covenant": "Minimum equity", "numerator_accounts": "3000",
     "denominator_accounts": "", "operator": "min", "threshold": D("75000")},
    {"covenant": "Fixed charge", "numerator_accounts": "9999",
     "denominator_accounts": "6900", "operator": ">=", "threshold": D("1.2")},
]


def test_covenants_measured_from_the_trial_balance():
    findings, stats = execute_procedure(
        "debt.covenants", {"Covenants": COVENANTS, "Trial_balance": TB}, {})
    assert keys(findings) == {("debt to equity", "breached"),
                              ("fixed charge", "not_measurable")}
    values = {m["covenant"]: m["value"] for m in stats["measured"]}
    assert values == {"Current ratio": "1.5000", "Debt to equity": "2.4600",
                      "Minimum equity": "100000.00"}


EQUITY = [
    {"component": "Members' capital", "account": "3000", "beginning": D("100000"),
     "additions": D("0"), "reductions": D("0"), "ending": D("100000")},
    # 40000 + 25000 - 10000 = 55000; the rollforward says 56000
    {"component": "Retained earnings", "account": "3200", "beginning": D("40000"),
     "additions": D("25000"), "reductions": D("10000"), "ending": D("56000")},
]


def test_equity_rollforward_foots_and_ties():
    findings, _ = execute_procedure(
        "equity.rollforward", {"Equity_rollforward": EQUITY, "Trial_balance": TB}, {})
    assert keys(findings) == {("retained earnings", "does_not_foot"),
                              ("retained earnings", "ending_to_ledger")}


def test_equity_rollforward_without_a_trial_balance_only_foots():
    findings, stats = execute_procedure(
        "equity.rollforward", {"Equity_rollforward": EQUITY}, {})
    assert keys(findings) == {("retained earnings", "does_not_foot")}
    assert "ties_to_ledger" in stats["not_performed"]


def test_covenants_after_the_audit_adjustments():
    # Depth pass (2 Oct 2026). An adjustment writes 30000 off account 1100:
    # current ratio (50000 + 40000) / 80000 = 1.125, below 1.25 -> compliance
    # changes. Debt to equity is untouched (still breached, no change finding).
    ajes = [{"entry_id": "AJE-1", "account": "1100", "debit": "", "credit": D("30000")},
            {"entry_id": "AJE-1", "account": "6000", "debit": D("30000"), "credit": ""}]
    findings, stats = execute_procedure(
        "debt.covenants",
        {"Covenants": COVENANTS, "Trial_balance": TB, "Adjusting_entries": ajes}, {})
    assert ("current ratio", "adjustments_change_compliance") in keys(findings)
    assert ("debt to equity", "adjustments_change_compliance") not in keys(findings)
    adjusted = {m["covenant"]: m.get("adjusted_value") for m in stats["measured"]}
    assert adjusted["Current ratio"] == "1.1250" and adjusted["Debt to equity"] == "2.4600"


def test_covenant_add_backs_and_the_trailing_basis():
    # Add-back: debt to equity with 30000 added to equity: 246000 / 130000 = 1.8923, met.
    added = [dict(COVENANTS[1], denominator_adjustment=D("30000"),
                  adjustment_note="subordinated loan counted as equity (s. 7.2)")]
    findings, stats = execute_procedure(
        "debt.covenants", {"Covenants": added, "Trial_balance": TB}, {})
    assert findings == [] and stats["measured"][0]["value"] == "1.8923"
    # Trailing twelve months: measured on a twelve-month period, refused on six.
    ttm = [dict(COVENANTS[0], basis="TTM")]
    year = {"period_start": "2025-01-01", "period_end": PE}
    findings, stats = execute_procedure(
        "debt.covenants", {"Covenants": ttm, "Trial_balance": TB}, year)
    assert findings == [] and stats["measured"][0]["value"] == "1.5000"
    half = {"period_start": "2025-07-01", "period_end": PE}
    findings, _ = execute_procedure(
        "debt.covenants", {"Covenants": ttm, "Trial_balance": TB}, half)
    assert keys(findings) == {("current ratio", "not_measurable")}
    assert "6 months" in findings[0].reason
