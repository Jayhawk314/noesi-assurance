# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Regressions for the independent review of the audit-frame expansion
(docs/reviews/REVIEW-2026-09-28-audit-frame.md), one block per finding,
each reproducing the reviewer's example."""

from datetime import date
from decimal import Decimal as D

import pytest

from procedures_cycles.common import PolicyError
from procedures_cycles.completion import REQUIRED_REPRESENTATIONS
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


# ------------------------------------------------ F1: representation letter
LETTER = {"period_end": "2025-12-31", "report_date": "2026-02-15"}


def letter(obtained="yes", signed="CEO", dated=date(2026, 2, 15)):
    return [{"code": code, "representation": code, "obtained": obtained,
             "dated": dated, "signed_by": signed} for code in REQUIRED_REPRESENTATIONS]


@pytest.mark.parametrize("value", ["", "pending", "unknown"])
def test_f1_blank_or_pending_is_not_obtained(value):
    findings, stats = execute_procedure("completion.representation_letter",
                                        {"Representations": letter(obtained=value)},
                                        LETTER)
    assert stats["obtained"] == 0
    assert len([f for f in findings if f.key[2] == "not_obtained"]) == 12


@pytest.mark.parametrize("signer", ["no", "unsigned", "n/a", "TBD"])
def test_f1_a_placeholder_is_not_a_signature(signer):
    findings, _ = execute_procedure("completion.representation_letter",
                                    {"Representations": letter(signed=signer)}, LETTER)
    assert keys(findings) == {("letter", "unsigned")}


def test_f1_the_report_date_is_required_and_must_follow_period_end():
    with pytest.raises(PolicyError, match="report_date"):
        execute_procedure("completion.representation_letter",
                          {"Representations": letter()}, {"period_end": "2025-12-31"})
    with pytest.raises(PolicyError, match="must follow the period end"):
        execute_procedure("completion.representation_letter",
                          {"Representations": letter()},
                          {"period_end": "2025-12-31", "report_date": "2025-12-15"})


def test_f1_mentioning_the_subject_is_not_making_the_representation():
    rows = [{"representation": "The financial statements were delivered",
             "obtained": "yes", "dated": date(2026, 2, 15), "signed_by": "CEO"}]
    findings, stats = execute_procedure("completion.representation_letter",
                                        {"Representations": rows}, LETTER)
    assert ("fs_responsibility", "not_obtained") in keys(findings)
    assert stats["unrecognized_rows"] == ["The financial statements were delivered"]


# ------------------------------------------------ F4: subsequent-events window
LATE = [{"entry_id": "S9", "entry_date": date(2035, 1, 10), "account": "6000",
         "debit": D("500"), "credit": None},
        {"entry_id": "S9", "entry_date": date(2035, 1, 10), "account": "2000",
         "debit": None, "credit": D("500")}]


def test_f4_no_report_date_is_refused_not_an_unbounded_review():
    with pytest.raises(PolicyError, match="report_date"):
        execute_procedure("completion.subsequent_events", {"Journal_entries": LATE},
                          {"period_end": "2025-12-31", "se_threshold": "10000"})


def test_f4_a_report_date_before_period_end_is_refused():
    with pytest.raises(PolicyError, match="must follow the period end"):
        execute_procedure("completion.subsequent_events", {"Journal_entries": LATE},
                          {"period_end": "2025-12-31", "se_threshold": "10000",
                           "report_date": "2025-12-15"})


def test_f4_entries_after_the_report_date_are_outside_the_window():
    findings, stats = execute_procedure(
        "completion.subsequent_events", {"Journal_entries": LATE},
        {"period_end": "2025-12-31", "se_threshold": "10000",
         "report_date": "2026-02-15"})
    assert keys(findings) == {("no_subsequent_records",)}
    assert stats["reviewed"]["journal_entries"] == 0


def test_f4_coverage_needs_the_report_date():
    from procedures_ap.coverage import compile_coverage
    from procedures_cycles.contracts import CYCLE_CONTRACTS_BY_ID
    from procedures_cycles.engines import registered_procedures
    contract = CYCLE_CONTRACTS_BY_ID["completion.subsequent_events"]
    inventory = {"Journal_entries": {"fields": ["entry_id", "account", "entry_date"],
                                     "rows": 2}}
    row = compile_coverage(inventory, policies={"period_end": "2025-12-31",
                                                "se_threshold": "1"},
                           contracts=(contract,),
                           executors=registered_procedures())["procedures"][0]
    assert row["status"] == "partial" and "report_date" in row["missing_policies"]
