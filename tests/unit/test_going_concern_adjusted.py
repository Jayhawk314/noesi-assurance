# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Going-concern indicators are judged on the adjusted figures (25 Nov 2026).

The test read the trial balance before the audit adjustments, so an
adjustment that turned working capital negative, or a loss into a profit,
never reached the indicators. Invented data, worked by hand in the comments.
"""

from decimal import Decimal as D

from procedures_cycles.engines import execute_procedure

GC = "completion.going_concern_indicators"


def tb(rows):
    return [{"account": a, "line": line, "balance": D(cur), "prior_balance": D(pri)}
            for a, line, cur, pri in rows]


# Before adjustments: current assets 50,000, current liabilities 40,000
# (working capital 10,000, ratio 1.25); income 100,000 - 60,000 - 30,000 =
# 10,000; equity 20,000 + 10,000 = 30,000. Last year a profit of 5,000.
BOOKS = tb([
    ("1000", "cash", "30000", "20000"), ("1100", "receivables", "20000", "15000"),
    ("1500", "noncurrent_assets", "20000", "20000"),
    ("2000", "current_liabilities", "-40000", "-30000"),
    ("2500", "noncurrent_liabilities", "0", "0"),
    ("3000", "equity", "-20000", "-15000"),
    ("4000", "sales", "-100000", "-90000"), ("5000", "cost_of_sales", "60000", "55000"),
    ("6000", "operating_expense", "30000", "30000"),
])


def aje(entry, account, debit=None, credit=None):
    return {"entry_id": entry, "account": account,
            "debit": D(debit) if debit else None, "credit": D(credit) if credit else None}


def keys(findings):
    return {f.key[1] for f in findings}


def test_without_adjusting_entries_the_books_are_judged_and_nothing_is_added():
    findings, stats = execute_procedure(GC, {"Trial_balance": BOOKS},
                                        {"gc_current_ratio_floor": "1.0"})
    assert findings == []
    assert stats["basis"] == "unadjusted trial balance"
    assert (stats["working_capital"], stats["net_income"]) == ("10000.00", "10000.00")
    assert "before_adjustments" not in stats


def test_an_unrecorded_accrual_raises_indicators_only_after_the_adjustment():
    # AJE-1 accrues 15,000 of expense: working capital 50,000 - 55,000 = -5,000;
    # income 10,000 - 15,000 = -5,000; ratio 50,000 / 55,000 = 0.909 < 1.0.
    # Equity 20,000 - 5,000 = 15,000 stays positive; last year was a profit.
    entries = [aje("AJE-1", "6000", debit="15000"), aje("AJE-1", "2000", credit="15000")]
    findings, stats = execute_procedure(
        GC, {"Trial_balance": BOOKS, "Adjusting_entries": entries},
        {"gc_current_ratio_floor": "1.0"})
    assert keys(findings) == {"negative_working_capital", "net_loss",
                              "current_ratio_below_floor"}
    assert all(f.verdict == "TENSION" for f in findings)
    assert all("only after the adjusting entries" in f.reason for f in findings)
    assert all(f.evidence["basis"] == "after adjusting entries" for f in findings)
    assert stats["basis"] == "after adjusting entries"
    assert (stats["working_capital"], stats["net_income"], stats["equity"]) == \
        ("-5000.00", "-5000.00", "15000.00")
    assert stats["before_adjustments"]["working_capital"] == "10000.00"
    assert stats["before_adjustments"]["current_ratio"] == "1.2500"
    assert stats["raised_by_adjustments"] == ["negative_working_capital", "net_loss",
                                              "current_ratio_below_floor"]
    assert stats["cleared_by_adjustments"] == []


def test_an_indicator_the_adjustments_clear_is_named_not_raised():
    # A 15,000 note payable sits in current liabilities (55,000): working
    # capital -5,000 on the books. AJE-2 moves it to long-term debt:
    # current liabilities 40,000, working capital 10,000.
    books = [dict(r) for r in BOOKS]
    for r in books:
        if r["account"] == "2000":
            r["balance"] = D("-55000")
        if r["account"] == "1500":
            r["balance"] = D("35000")
    entries = [aje("AJE-2", "2000", debit="15000"), aje("AJE-2", "2500", credit="15000")]
    findings, stats = execute_procedure(
        GC, {"Trial_balance": books, "Adjusting_entries": entries}, {})
    assert findings == []
    assert stats["before_adjustments"]["working_capital"] == "-5000.00"
    assert stats["working_capital"] == "10000.00"
    assert stats["cleared_by_adjustments"] == ["negative_working_capital"]


def test_entries_that_cannot_be_applied_are_refused_by_name_and_the_rest_applied():
    entries = [aje("AJE-1", "6000", debit="15000"), aje("AJE-1", "2000", credit="15000"),
               aje("AJE-3", "6000", debit="500"), aje("AJE-3", "2000", credit="400"),
               aje("AJE-4", "9999", debit="700"), aje("AJE-4", "2000", credit="700")]
    findings, stats = execute_procedure(
        GC, {"Trial_balance": BOOKS, "Adjusting_entries": entries}, {})
    refusal = [f for f in findings if f.key[1] == "adjustments_not_applied"]
    assert len(refusal) == 1 and refusal[0].verdict == "AMBIGUOUS"
    assert refusal[0].evidence["finding_class"] == "REFUSAL"
    assert "AJE-3 (does not balance)" in refusal[0].reason
    assert "AJE-4 (account 9999 is not on the trial balance)" in refusal[0].reason
    # AJE-1 is applied in full; AJE-3 not at all; AJE-4's line to 2000 is
    # applied (as fs.adjusted_trial_balance does), its unknown line is not.
    assert stats["working_capital"] == "-5700.00"
    assert {"negative_working_capital", "net_loss"} <= keys(findings)


def test_the_adjusted_trial_balance_procedure_is_unchanged_by_the_shared_helper():
    entries = [aje("AJE-1", "6000", debit="15000"), aje("AJE-1", "2000", credit="15000"),
               aje("AJE-3", "6000", debit="500"), aje("AJE-3", "2000", credit="400"),
               aje("AJE-4", "9999", debit="700"), aje("AJE-4", "2000", credit="700")]
    findings, stats = execute_procedure(
        "fs.adjusted_trial_balance", {"Trial_balance": BOOKS, "Adjusting_entries": entries}, {})
    assert [tuple(f.key[1:]) for f in findings] == [
        ("unbalanced_entry", "AJE-3"), ("unknown_account", "AJE-4", "9999"),
        ("adjusted_tb_out_of_balance",)]
    assert stats["entries"] == 3
    assert stats["adjustments"] == {"2000": "-15700.00", "6000": "15000.00"}


# ------------------------------------------- independent review, 25 Nov 2026
ZERO_EFFECT = [aje("Z", "1000", debit="1000"), aje("Z", "1000", credit="1000")]


def test_a_side_column_trial_balance_keeps_last_years_signs_after_adjustments():
    # Dr/Cr side column, amounts unsigned. Last year: sales 300 Cr, expense
    # 250 Dr, a profit of 50. This year: sales 100, expense 200, a loss of 100.
    sided = [
        {"account": "1000", "line": "cash", "balance": D("500"), "side": "Dr",
         "prior_balance": D("400")},
        {"account": "3000", "line": "equity", "balance": D("500"), "side": "Cr",
         "prior_balance": D("350")},
        {"account": "4000", "line": "sales", "balance": D("100"), "side": "Cr",
         "prior_balance": D("300")},
        {"account": "6000", "line": "operating_expense", "balance": D("200"), "side": "Dr",
         "prior_balance": D("250")},
    ]
    plain, _ = execute_procedure(GC, {"Trial_balance": sided}, {})
    adjusted, stats = execute_procedure(
        GC, {"Trial_balance": sided, "Adjusting_entries": ZERO_EFFECT}, {})
    assert keys(plain) == keys(adjusted) == {"net_loss"}
    assert stats["raised_by_adjustments"] == []


def test_an_account_on_two_rows_is_counted_once_per_row_after_adjustments():
    # Cash 1,000 on one row and -200 on another (current assets 800); current
    # liabilities 900: working capital -100, ratio 0.8889, before and after a
    # zero-effect entry.
    rows = [{"account": "1000", "line": "cash", "balance": D("1000")},
            {"account": "1000", "line": "cash", "balance": D("-200")},
            {"account": "2000", "line": "current_liabilities", "balance": D("-900")},
            {"account": "3000", "line": "equity", "balance": D("100")}]
    _, stats = execute_procedure(
        GC, {"Trial_balance": rows, "Adjusting_entries": ZERO_EFFECT},
        {"gc_current_ratio_floor": "1.2"})
    assert stats["working_capital"] == stats["before_adjustments"]["working_capital"] == "-100.00"
    assert stats["current_ratio"] == stats["before_adjustments"]["current_ratio"] == "0.8889"
    # Before 25 Nov, fs.adjusted_trial_balance kept only the last row of a
    # repeated account and reported a false "does not foot".
    atb_findings, atb = execute_procedure(
        "fs.adjusted_trial_balance", {"Trial_balance": rows, "Adjusting_entries": ZERO_EFFECT}, {})
    assert atb["adjusted_balances"]["1000"] == "800.00"
    assert atb_findings == []
    assert D(atb["adjusted_debits"]) == D(atb["adjusted_credits"]) == D("1100")
