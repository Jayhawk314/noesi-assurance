# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Retrospective review of estimates, and related-party matching."""

from decimal import Decimal as D

import pytest

from procedures_cycles.common import PolicyError
from procedures_cycles.engines import execute_procedure


def est(name, prior, outcome):
    return {"estimate": name, "prior_estimate": D(prior) if prior else None,
            "outcome": D(outcome) if outcome else None}


ESTIMATES = [
    est("Allowance", "10000", "13000"),    # +3000, 30%: beyond 20%
    est("Warranty", "5000", "5600"),       # +600, 12%: within
    est("Legal", "20000", "26000"),        # +6000, 30%: beyond
    est("Reserve", "0", "0"),              # no miss
    est("Bonus", "8000", None),            # not resolved yet
]


def keys(findings):
    return {tuple(f.key[1:]) for f in findings}


def test_retrospective_review_flags_large_misses_and_one_way_bias():
    findings, stats = execute_procedure(
        "estimates.retrospective_review", {"Estimates": ESTIMATES},
        {"estimates_hindsight_pct": "20"})
    assert keys(findings) == {("allowance", "outcome_differs"),
                              ("legal", "outcome_differs"),
                              ("bonus", "not_resolved"),
                              ("all_estimates", "one_direction")}
    assert stats["misses"] == 3


def test_misses_in_both_directions_are_not_a_bias_indicator():
    findings, _ = execute_procedure(
        "estimates.retrospective_review",
        {"Estimates": ESTIMATES + [est("Returns", "4000", "3900")]},
        {"estimates_hindsight_pct": "20"})
    assert ("all_estimates", "one_direction") not in keys(findings)


def test_the_hindsight_threshold_is_the_auditors():
    with pytest.raises(PolicyError, match="estimates_hindsight_pct"):
        execute_procedure("estimates.retrospective_review", {"Estimates": ESTIMATES}, {})


PARTIES = [
    {"party_name": "Hawk Ridge Holdings, LLC", "relationship": "owned by the CEO"},
    {"party_name": "Dana Merritt", "relationship": "CFO's spouse",
     "address": "12 Aspen Ln"},
    {"party_name": "Summit Group Inc.", "relationship": "director's company"},
    {"party_name": "Birch and Company", "relationship": "CEO's brother"},
    {"party_name": "Nobody Here", "relationship": "former owner"},
]
TABLES = {
    "Related_parties": PARTIES,
    "Vendors": [{"vendor_number": "V1", "vendor_name": "Hawk Ridge Holdings"},
                {"vendor_number": "V2", "vendor_name": "Other Supply"}],
    "Payments": [{"vendor_number": "V1", "payment_amount": D("5000.00")},
                 {"vendor_number": "V1", "payment_amount": D("2500.00")},
                 {"vendor_number": "V2", "payment_amount": D("900.00")}],
    "AR_listing": [{"customer_number": "C9", "customer_name": "Summit Group",
                    "balance": D("1200.00")}],
    "Sales_invoices": [{"customer": "Summit Group", "amount": D("3000.00")},
                       {"customer": "Birch & Co", "amount": D("900.00")},
                       {"customer": "Birch & Co", "amount": D("100.00")}],
    "Payroll_master": [{"employee_id": "E7", "address": "12 aspen ln."},
                       {"employee_id": "E8", "address": "40 Elm St"}],
}


def test_related_parties_are_matched_across_the_engagements_data():
    findings, stats = execute_procedure("related_parties.matching", TABLES, {})
    assert keys(findings) == {
        ("hawk ridge holdings, llc", "vendor", "v1"),
        ("summit group inc.", "customer", "c9"),
        ("birch and company", "customer", "birch and"),
        ("dana merritt", "employee_address", "e7"),
    }
    reasons = {f.key[-1]: f.reason for f in findings}      # by counterparty id
    assert "7500.00 paid" in reasons["v1"]
    assert "1200.00 owing at period end" in reasons["c9"]
    assert "1000.00 invoiced" in reasons["birch and"]
    assert stats["matches"] == 4


def test_nothing_to_match_against_is_a_refusal_not_a_clean_result():
    findings, _ = execute_procedure("related_parties.matching",
                                    {"Related_parties": PARTIES}, {})
    assert keys(findings) == {("no_counterparties",)}
