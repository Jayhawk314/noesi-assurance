# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Regressions for the independent review of the audit-frame expansion
(docs/reviews/REVIEW-2026-09-28-audit-frame.md), one block per finding,
each reproducing the reviewer's example."""

from datetime import date
from decimal import Decimal as D

from procedures_cycles.engines import execute_procedure


def keys(findings):
    return {tuple(f.key[1:]) for f in findings}


# ------------------------------------------------ F2: blank required values
def test_f2_blank_trial_balance_values_are_refused_not_a_healthy_result():
    tb = [{"account": a, "line": line, "balance": None}
          for a, line in (("1000", "cash"), ("2000", "current_liabilities"),
                          ("3000", "equity"), ("4000", "sales"))]
    findings, stats = execute_procedure("completion.going_concern_indicators",
                                        {"Trial_balance": tb}, {})
    assert ("incomplete_rows", "Trial_balance") in keys(findings)
    assert stats["population"] == 0 and stats["excluded_incomplete_rows"] == {
        "Trial_balance": 4}


def test_f2_a_credit_memo_with_no_date_is_named_not_skipped():
    tables = {"Credit_memos": [{"memo_number": "CM1", "memo_date": None,
                                "invoice_number": "101", "amount": D("5000")}],
              "Sales_invoices": [{"invoice_number": "101",
                                  "invoice_date": date(2025, 12, 30),
                                  "amount": D("5000")}]}
    findings, _ = execute_procedure("rev.credit_memos_after_period_end", tables,
                                    {"period_end": "2025-12-31"})
    [refusal] = [f for f in findings if f.key[1] == "incomplete_rows"]
    assert refusal.verdict == "AMBIGUOUS" and "memo_date" in refusal.reason


def test_f2_complete_rows_still_run_beside_the_named_gap():
    tb = [{"account": "1000", "line": "cash", "balance": D("5000")},
          {"account": "2000", "line": "current_liabilities", "balance": D("-9000")},
          {"account": "3000", "line": "equity", "balance": None}]
    findings, _ = execute_procedure("completion.going_concern_indicators",
                                    {"Trial_balance": tb}, {})
    assert {("incomplete_rows", "Trial_balance"),
            ("negative_working_capital",)} <= keys(findings)
