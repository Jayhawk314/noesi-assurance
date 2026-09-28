# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Completion: subsequent events, going-concern indicators, representation letter."""

from datetime import date
from decimal import Decimal as D

import pytest

from procedures_cycles.common import PolicyError
from procedures_cycles.completion import REQUIRED_REPRESENTATIONS
from procedures_cycles.engines import execute_procedure


def keys(findings):
    return {tuple(f.key[1:]) for f in findings}


# ------------------------------------------------ subsequent events
def je(entry, dated, account, amount, memo=""):
    return {"entry_id": entry, "entry_date": dated, "account": account,
            "debit": amount if amount > 0 else None,
            "credit": -amount if amount < 0 else None, "description": memo}


JOURNAL = [
    je("S1", date(2026, 1, 10), "6800", D("25000"), "lawsuit settled"),
    je("S1", date(2026, 1, 10), "2100", D("-25000"), "lawsuit settled"),
    je("S2", date(2026, 1, 12), "6000", D("500")), je("S2", date(2026, 1, 12), "2000", D("-500")),
    je("S3", date(2026, 3, 1), "1500", D("50000")),              # after the report date
    je("S3", date(2026, 3, 1), "1000", D("-50000")),
    je("E0", date(2025, 12, 15), "6000", D("90000")),            # in the period
    je("E0", date(2025, 12, 15), "2000", D("-90000")),
]
PAYMENTS = [
    {"payment_number": "P1", "payment_date": date(2026, 1, 20), "vendor_number": "V4",
     "payment_amount": D("12000")},
    {"payment_number": "P2", "payment_date": date(2026, 1, 21), "vendor_number": "V4",
     "payment_amount": D("900")},
    {"payment_number": "P3", "payment_date": date(2025, 12, 30), "vendor_number": "V4",
     "payment_amount": D("50000")},
]
SE = {"period_end": "2025-12-31", "se_threshold": "10000", "report_date": "2026-02-15"}


def test_subsequent_events_leads_from_entries_and_payments_up_to_the_report_date():
    findings, stats = execute_procedure(
        "completion.subsequent_events",
        {"Journal_entries": JOURNAL, "Payments": PAYMENTS}, SE)
    assert keys(findings) == {("s1", "journal_entry"), ("p1", "payment")}
    assert stats["reviewed"] == {"journal_entries": 2, "payments": 2}
    assert "lawsuit settled" in next(f.reason for f in findings if f.key[1] == "s1")


def test_no_subsequent_records_is_a_refusal_not_a_clean_review():
    findings, _ = execute_procedure(
        "completion.subsequent_events", {"Journal_entries": JOURNAL[-2:]}, SE)
    assert keys(findings) == {("no_subsequent_records",)}


def test_the_subsequent_events_threshold_is_the_auditors():
    with pytest.raises(PolicyError, match="se_threshold"):
        execute_procedure("completion.subsequent_events", {"Journal_entries": JOURNAL},
                          {"period_end": "2025-12-31", "report_date": "2026-02-15"})


# ------------------------------------------------ going concern
def tb(rows):
    return [{"account": a, "line": line, "balance": D(cur), "prior_balance": D(pri)}
            for a, line, cur, pri in rows]


DISTRESSED = tb([
    ("1000", "cash", "5000", "9000"), ("1100", "receivables", "20000", "25000"),
    ("1200", "inventory", "15000", "18000"), ("1500", "noncurrent_assets", "30000", "31000"),
    ("2000", "current_liabilities", "-60000", "-50000"),
    ("2500", "noncurrent_liabilities", "-15000", "-18000"),
    ("3000", "equity", "-10000", "-20000"),
    ("4000", "sales", "-100000", "-90000"), ("5000", "cost_of_sales", "80000", "70000"),
    ("6000", "operating_expense", "35000", "25000"),
    ("1199", "Accounts receivable", "0", "0"),                 # not a recognized line
])


def test_going_concern_indicators_from_a_distressed_trial_balance():
    findings, stats = execute_procedure(
        "completion.going_concern_indicators", {"Trial_balance": DISTRESSED},
        {"gc_current_ratio_floor": "1.0"})
    # working capital 40000 - 60000; loss (100000 - 80000 - 35000) = -15000;
    # equity 10000 - 15000 = -5000; last year 90000 - 70000 - 25000 = -5000
    assert keys(findings) == {("unclassified_accounts",), ("negative_working_capital",),
                              ("equity_deficit",), ("net_loss",), ("recurring_losses",),
                              ("current_ratio_below_floor",)}
    assert (stats["working_capital"], stats["net_income"]) == ("-20000.00", "-15000.00")


def test_a_healthy_trial_balance_raises_no_indicator():
    healthy = tb([("1000", "cash", "50000", "40000"),
                  ("1500", "noncurrent_assets", "20000", "20000"),
                  ("2000", "current_liabilities", "-20000", "-20000"),
                  ("3000", "equity", "-30000", "-30000"),
                  ("4000", "sales", "-100000", "-90000"),
                  ("5000", "cost_of_sales", "60000", "55000"),
                  ("6000", "operating_expense", "20000", "25000")])
    findings, _ = execute_procedure("completion.going_concern_indicators",
                                    {"Trial_balance": healthy}, {})
    assert findings == []


# ------------------------------------------------ representation letter
LETTER = {"period_end": "2025-12-31", "report_date": "2026-02-15",
          "rep_signers": "CEO, CFO"}


def rep(code=None, wording="", obtained="yes", dated=date(2026, 2, 15), signed="CEO, CFO"):
    return {"code": code, "representation": wording or (code or ""), "obtained": obtained,
            "dated": dated, "signed_by": signed}


def test_a_letter_missing_or_refusing_required_representations():
    letter = [rep(code) for code in REQUIRED_REPRESENTATIONS
              if code not in ("related_parties", "fraud_allegations")]
    letter.append(rep("fraud_allegations", obtained="refused"))
    findings, stats = execute_procedure(
        "completion.representation_letter", {"Representations": letter},
        LETTER)
    assert keys(findings) == {("related_parties", "not_obtained"),
                              ("fraud_allegations", "not_obtained")}
    assert stats["obtained"] == len(REQUIRED_REPRESENTATIONS) - 2


WORDED = [
    "We acknowledge responsibility for the fair presentation of the financial statements",
    "We are responsible for internal control relevant to the financial statements",
    "We have provided you with all information and access to all records",
    "All transactions have been recorded in the accounting records",
    "We have no knowledge of fraud or suspected fraud affecting the entity",
    "We have no knowledge of any allegations of fraud",
    "We are not aware of noncompliance with laws and regulations",
    "The effects of uncorrected misstatements are immaterial",
    "There is no litigation, claims or assessments other than disclosed",
    "Significant assumptions used in making accounting estimates are reasonable",
    "Related party relationships and transactions have been disclosed",
    "No subsequent events require adjustment or disclosure",
]


def test_wording_suggests_a_code_but_only_a_coded_row_counts():
    worded = [rep(wording=w) for w in WORDED]
    findings, stats = execute_procedure("completion.representation_letter",
                                        {"Representations": worded}, LETTER)
    # every representation is still open, each pointing at its likely sentence
    assert keys(findings) == {(code, "not_obtained") for code in REQUIRED_REPRESENTATIONS}
    assert set(stats["uncoded_suggestions"]) == set(REQUIRED_REPRESENTATIONS)
    coded = [rep(code=c, wording=w) for c, ws in stats["uncoded_suggestions"].items()
             for w in ws]
    findings, _ = execute_procedure("completion.representation_letter",
                                    {"Representations": coded}, LETTER)
    assert findings == []


def test_a_coded_letter_has_its_date_and_signature_checked():
    late = [rep(code=code, dated=date(2026, 2, 10), signed="")
            for code in REQUIRED_REPRESENTATIONS]
    findings, _ = execute_procedure("completion.representation_letter",
                                    {"Representations": late}, LETTER)
    assert keys(findings) == {("letter", "not_dated_report_date"), ("letter", "unsigned")}
