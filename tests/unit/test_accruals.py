# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Accruals and prepaids: rollforward to the ledger and time-proportion recompute.

Year end 2025-12-31. Day counts are worked by hand in the comments.
"""

from datetime import date
from decimal import Decimal as D

from procedures_cycles.engines import execute_procedure

PE = "2025-12-31"


def item(name, kind, account, begin, adds, less, end, *, total=None, start=None,
         finish=None, billed=None):
    return {"item": name, "kind": kind, "account": account, "beginning": D(begin),
            "additions": D(adds), "reductions": D(less), "ending": D(end),
            "total_amount": D(total) if total else None,
            "service_start": date.fromisoformat(start) if start else None,
            "service_end": date.fromisoformat(finish) if finish else None,
            "billed_to_date": D(billed) if billed else None}


SCHEDULE = [
    # 2025-07-01..2026-06-30 = 365 days, 184 used by year end, 181 unexpired:
    # 12000 x 181 / 365 = 5950.68
    item("Insurance", "Prepaid", "1300", "5800.00", "12000.00", "11849.32", "5950.68",
         total="12000", start="2025-07-01", finish="2026-06-30"),
    # 2025-12-01..2026-02-28 = 90 days, 31 used, 59 unexpired: 6000 x 59 / 90 =
    # 3933.33; the schedule carries two months of three, 4000.00
    item("Rent", "prepaid", "1300", "0", "6000.00", "2000.00", "4000.00",
         total="6000", start="2025-12-01", finish="2026-02-28"),
    # 2025-10-01..2026-03-31 = 182 days, 92 earned: 24000 x 92 / 182 = 12131.87,
    # less 5000 billed = 7131.87
    item("Audit fee", "accrued expense", "2150", "0", "12131.87", "5000.00", "7131.87",
         total="24000", start="2025-10-01", finish="2026-03-31", billed="5000"),
    # usage-based: not recomputed; 1500 + 1800 - 1500 = 1800, not 1850
    item("Utilities", "Accrual", "2150", "1500.00", "1800.00", "1500.00", "1850.00"),
    item("Deposit", "deposit", "1400", "0", "500.00", "0", "500.00"),
]
# 1300: 5950.68 + 4000.00 = 9950.68 (prior 5800); 2150: 7131.87 + 1850 = 8981.87
# (prior 1500)
TB = [{"account": "1300", "balance": D("9950.68"), "prior_balance": D("5800.00")},
      {"account": "2150", "balance": D("-8981.87"), "prior_balance": D("-1500.00")}]


def keys(findings):
    return {tuple(f.key[1:]) for f in findings}


def test_rollforward_foots_each_item_and_ties_each_account():
    findings, _ = execute_procedure(
        "accruals.rollforward", {"Accrual_schedule": SCHEDULE, "Trial_balance": TB}, {})
    assert keys(findings) == {("utilities", "does_not_foot"),
                              ("deposit", "kind_unknown")}


def test_rollforward_names_an_account_that_does_not_tie():
    tb = [TB[0], dict(TB[1], balance=D("-9000.00"))]
    findings, _ = execute_procedure(
        "accruals.rollforward", {"Accrual_schedule": SCHEDULE, "Trial_balance": tb}, {})
    assert ("2150", "ending_to_ledger") in keys(findings)
    assert "difference -18.13" in next(f.reason for f in findings
                                       if f.key[1:] == ("2150", "ending_to_ledger"))


def test_rollforward_without_a_trial_balance_only_foots():
    findings, stats = execute_procedure(
        "accruals.rollforward", {"Accrual_schedule": SCHEDULE}, {})
    assert keys(findings) == {("utilities", "does_not_foot"),
                              ("deposit", "kind_unknown")}
    assert "ties_to_ledger" in stats["not_performed"]


def test_time_proportion_recompute():
    findings, stats = execute_procedure(
        "accruals.recompute", {"Accrual_schedule": SCHEDULE}, {"period_end": PE})
    assert keys(findings) == {("rent", "recompute_differs")}
    assert "gives 3933.33 (difference 66.67)" in findings[0].reason
    assert stats["not_recomputed"] == ["utilities", "deposit"]
