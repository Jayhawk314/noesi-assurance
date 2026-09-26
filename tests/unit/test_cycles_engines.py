# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Cycle executors on small invented populations with planted errors."""

from datetime import date
from decimal import Decimal as D

import pytest

from procedures_cycles.common import PolicyError
from procedures_cycles.engines import EXECUTORS, execute_procedure, registered_procedures
from procedures_cycles.contracts import CYCLE_PROCEDURES, contracts_for_scope


def keys(findings, verdict=None):
    return {f.key[1:] for f in findings if verdict is None or f.verdict == verdict}


def test_every_cycle_contract_has_an_executor_and_vice_versa():
    assert {c.procedure_id for c in CYCLE_PROCEDURES} == set(EXECUTORS)
    assert "ap.three_way_receipt_match" in registered_procedures()


def test_scope_filters_contracts():
    assert contracts_for_scope(None) == ()
    ids = {c.procedure_id for c in contracts_for_scope(["cash", "nonsense"])}
    assert ids == {"cash.bank_reconciliation", "cash.interbank_transfers"}


TB = [
    {"account": "1010", "balance": D("100000"), "side": "DR", "line": "cash",
     "prior_balance": D("80000")},
    {"account": "1100", "balance": D("50000"), "side": "DR", "line": "receivables",
     "prior_balance": D("40000")},
    {"account": "1110", "balance": D("5000"), "side": "CR", "line": "allowance",
     "prior_balance": D("4000")},
    {"account": "1200", "balance": D("80000"), "side": "DR", "line": "inventory",
     "prior_balance": D("70000")},
    {"account": "1500", "balance": D("60000"), "side": "DR", "line": "noncurrent_assets",
     "prior_balance": D("60000")},
    {"account": "2010", "balance": D("70000"), "side": "CR", "line": "current_liabilities",
     "prior_balance": D("50000")},
    {"account": "3000", "balance": D("150000"), "side": "CR", "line": "equity",
     "prior_balance": D("150000")},
    {"account": "4000", "balance": D("400000"), "side": "CR", "line": "sales",
     "prior_balance": D("350000")},
    {"account": "5000", "balance": D("300000"), "side": "DR", "line": "cost_of_sales",
     "prior_balance": D("260000")},
    {"account": "6000", "balance": D("35000"), "side": "DR", "line": "operating_expense",
     "prior_balance": D("54000")},
]


def test_trial_balance_analytics_foots_ratios_and_flags_movements():
    findings, stats = execute_procedure("fs.trial_balance_analytics", {"Trial_balance": TB},
                                        {"analytics_threshold_pct": "20"})
    assert stats["debits"] == stats["credits"] == "625000"
    r = stats["current"]["ratios"]
    # current assets 100000+45000+80000 = 225000 / 70000
    assert D(r["current_ratio"]) == D("3.2143")
    assert D(r["gross_margin"]) == D("0.2500")
    flagged = keys(findings, "TENSION")
    assert ("movement", "2010") in flagged and ("movement", "6000") in flagged
    assert ("movement", "4000") not in flagged  # 14.3%


def test_trial_balance_out_of_balance_is_an_exception():
    rows = TB + [{"account": "9999", "balance": D("1"), "side": "DR", "line": "cash"}]
    findings, _ = execute_procedure("fs.trial_balance_analytics", {"Trial_balance": rows}, {})
    assert ("tb_out_of_balance",) in keys(findings, "CLASH")


def test_adjusted_trial_balance_applies_entries():
    entries = [
        {"entry_id": "1", "account": "6000", "debit": D("2000"), "credit": None},
        {"entry_id": "1", "account": "1110", "debit": None, "credit": D("2000")},
        {"entry_id": "2", "account": "6000", "debit": D("10"), "credit": None},
        {"entry_id": "3", "account": "7777", "debit": D("5"), "credit": None},
        {"entry_id": "3", "account": "1010", "debit": None, "credit": D("5")},
    ]
    findings, stats = execute_procedure("fs.adjusted_trial_balance",
                                        {"Trial_balance": TB, "Adjusting_entries": entries}, {})
    assert ("unbalanced_entry", "2") in keys(findings, "CLASH")
    assert ("unknown_account", "3", "7777") in keys(findings, "ORPHAN")
    assert D(stats["income_before_taxes"]["unadjusted"]) == D("65000.00")
    assert D(stats["income_before_taxes"]["adjusted"]) == D("63000.00")


def test_performance_materiality_ceiling_needs_policies():
    rows = [{"account": "Cash", "performance_materiality": D("20000")},
            {"account": "AR", "performance_materiality": D("25000")}]
    with pytest.raises(PolicyError):
        execute_procedure("planning.performance_materiality",
                          {"Performance_materiality": rows}, {})
    findings, stats = execute_procedure(
        "planning.performance_materiality", {"Performance_materiality": rows},
        {"materiality": "15000", "pm_allocation_multiple": "3"})
    assert ("over_allocated",) not in keys(findings)
    assert {("above_materiality", "Cash"), ("above_materiality", "AR")} <= keys(findings)
    assert stats["headroom"] == "0.00"


def test_attribute_evaluation_statistical_and_nonstatistical():
    rows = [
        {"attribute": "1", "method": "statistical", "expected_rate": "1.5",
         "tolerable_rate": "8", "risk": "10", "sample_size": "50", "deviations": "2"},
        {"attribute": "2", "method": "statistical", "expected_rate": "0",
         "tolerable_rate": "5", "risk": "10", "sample_size": "50", "deviations": "1"},
        {"attribute": "3", "method": "nonstatistical", "tolerable_rate": "0.07",
         "sample_size": "55", "deviations": "2", "estimated_sampling_risk": "0.04"},
        {"attribute": "4", "method": "statistical", "tolerable_rate": "5",
         "sample_size": "30", "deviations": "0"},
    ]
    findings, stats = execute_procedure("controls.attribute_evaluation",
                                        {"Attribute_tests": rows}, {})
    by = {a["attribute"]: a for a in stats["attributes"]}
    assert D(by["1"]["cuer"]) == D("0.103") and by["1"]["reliance_supported"] is False
    assert D(by["2"]["cuer"]) == D("0.076") and by["2"]["reliance_supported"] is False
    assert by["3"]["reliance_supported"] is False  # 3.6% + 4% > 7%
    assert ("4", "incomplete") in keys(findings, "AMBIGUOUS")  # no risk stated


LISTING = [{"customer_number": str(i), "balance": D(b)} for i, b in
           enumerate(["60000", "45000", "9000", "8000", "7000", "6000", "5000",
                      "4000", "3000", "2000"], 1)]
TB_AR = [{"account": "1100", "balance": D("149000"), "side": "DR", "line": "receivables"}]


def test_ar_listing_tie():
    findings, stats = execute_procedure("ar.listing_tie",
                                        {"AR_listing": LISTING, "Trial_balance": TB_AR}, {})
    assert findings == [] and stats["listing_total"] == "149000.00"
    findings, _ = execute_procedure(
        "ar.listing_tie", {"AR_listing": LISTING,
                           "Trial_balance": [{**TB_AR[0], "balance": D("150000")}]}, {})
    assert ("listing_to_gl",) in keys(findings, "CLASH")


def test_ar_allowance_recomputed_from_aging():
    listing = [{"customer_number": "1", "balance": D("1000"), "current": D("600"),
                "days_31_60": D("300"), "days_61_90": D("100"), "days_over_90": D("0")}]
    tb = [{"account": "1100", "balance": D("1000"), "side": "DR", "line": "receivables"},
          {"account": "1110", "balance": D("40"), "side": "CR", "line": "allowance"}]
    findings, stats = execute_procedure("ar.listing_tie",
                                        {"AR_listing": listing, "Trial_balance": tb},
                                        {"ar_allowance_rates": "0.03,0.10,0.15,0.30"})
    assert stats["allowance_required"] == "63"  # 18 + 30 + 15
    assert ("allowance_estimate",) in keys(findings, "CLASH")


CONFIRMS = [
    {"customer_number": "1", "book_value": D("60000"), "confirmed_value": D("59000"),
     "classification": "client misstatement"},
    {"customer_number": "3", "book_value": D("9000"), "confirmed_value": D("8100"),
     "classification": "client misstatement"},
    {"customer_number": "5", "book_value": D("7000"), "confirmed_value": D("6000"),
     "classification": "timing"},
    {"customer_number": "7", "book_value": D("5000"), "confirmed_value": D("5000"),
     "classification": ""},
    {"customer_number": "9", "book_value": D("3000"), "confirmed_value": D("2500"),
     "classification": ""},
]


def test_confirmations_nonstatistical_projects_and_refuses_unclassified():
    tables = {"AR_listing": LISTING, "Confirmations": CONFIRMS}
    findings, stats = execute_procedure("ar.confirmations_nonstatistical", tables,
                                        {"ar_tolerable_misstatement": "40000"})
    assert ("unclassified_difference", "9") in keys(findings, "AMBIGUOUS")
    # stratum ≤ 40000 = 44000; sample book = 9000+7000+5000 = 21000; misstatement 900
    assert stats["stratum_value"] == "44000.00" and stats["sample_value"] == "21000"
    assert D(stats["projected_sample_misstatement"]) == D("1885.71")
    assert D(stats["projected_total"]) == D("2885.71")
    assert ("evaluation",) in keys(findings, "AGREE")


def test_confirmations_mus_and_difference():
    tables = {"AR_listing": LISTING, "Confirmations": CONFIRMS[:4]}
    findings, stats = execute_procedure(
        "ar.confirmations_mus", tables,
        {"ar_tolerable_misstatement": "40000", "ar_risk_incorrect_acceptance": "20%",
         "mus_interval": "1000"})
    # items ≥ interval are all "large" here → misstatements added unprojected
    assert D(stats["large_item_misstatement"]) == D("1900.00")
    assert D(stats["upper_misstatement_limit"]) == D("3510.00")  # 1000×1.61 + 1900
    findings, stats = execute_procedure(
        "ar.confirmations_difference", tables,
        {"ar_tolerable_misstatement": "40000", "ar_risk_incorrect_acceptance": "0.2"})
    assert D(stats["projected_misstatement"]) == D("4750.00")  # 1900/4 × 10
    assert stats["within_tolerable"] is True


PAYMENTS = [
    {"payment_number": "701-1", "check_number": "701", "voucher_number": "100",
     "payment_amount": D("35000")},
    {"payment_number": "702-1", "check_number": "702", "voucher_number": "205",
     "payment_amount": D("12000")},
    {"payment_number": "703-1", "check_number": "703", "voucher_number": "101",
     "payment_amount": D("990")},
    {"payment_number": "704-1", "check_number": "704", "voucher_number": "210",
     "payment_amount": D("40000")},
    {"payment_number": "705-1", "check_number": "705", "voucher_number": "102",
     "payment_amount": D("500")},
]
VOUCHERS = [{"voucher_number": "100", "voucher_amount": D("35000")},
            {"voucher_number": "101", "voucher_amount": D("1000")},
            {"voucher_number": "102", "voucher_amount": D("500")},
            {"voucher_number": "210", "voucher_amount": D("40000")}]
INSPECTED = [
    {"payment_number": "701-1", "liability_date": date(2026, 12, 20)},
    {"payment_number": "702-1", "liability_date": date(2026, 12, 28),
     "liability_amount": D("12000")},
    {"payment_number": "704-1", "liability_date": date(2027, 1, 5)},
    {"payment_number": "705-1", "conclusion": "no misstatement"},
]


def test_unrecorded_liabilities_search():
    tables = {"Vouchers": VOUCHERS, "Payments": PAYMENTS,
              "Disbursement_inspection": INSPECTED}
    policies = {"period_end": "2026-12-31", "search_threshold": "30000",
                "search_interval": "2", "search_start": "1"}
    findings, stats = execute_procedure("ap.unrecorded_liabilities_search", tables, policies)
    assert stats["selected_above_threshold"] == ["701", "704"]
    assert stats["selected_systematic"] == ["702", "705"]
    assert ("702-1", "unrecorded") in keys(findings, "CLASH")
    assert ("704-1", "improperly_included") in keys(findings, "CLASH")
    assert ("703-1", "paid_differs_from_listed") in keys(findings, "TENSION")
    assert ("705", "selected_not_inspected") not in keys(findings)
    assert stats["outcomes"]["concluded_by_reference"] == 1
    assert stats["outcomes"]["properly_included"] == 1
    assert D(stats["net_misstatement"]) == D("28000.00")  # +40000 over, −12000 under


REC = [
    {"account": "general", "item_type": "bank_balance", "amount": D("10000")},
    {"account": "general", "item_type": "book_balance", "amount": D("9300")},
    {"account": "general", "item_type": "deposit_in_transit", "amount": D("500"),
     "item_date": date(2026, 12, 28)},
    {"account": "general", "item_type": "outstanding_check", "reference": "101",
     "amount": D("700")},
    {"account": "general", "item_type": "outstanding_check", "reference": "104",
     "amount": D("300")},
    {"account": "general", "item_type": "outstanding_check", "reference": "107",
     "amount": D("200")},
    {"account": "general", "item_type": "last_check_issued", "reference": "105",
     "amount": D("0")},
    {"account": "payroll", "item_type": "bank_balance", "amount": D("2000")},
    {"account": "payroll", "item_type": "book_balance", "amount": D("2000")},
]
CUTOFF = [
    {"account": "general", "reference": "101", "item_type": "check", "amount": D("700"),
     "cleared_date": date(2027, 1, 4)},
    {"account": "general", "reference": "103", "item_type": "check", "amount": D("150"),
     "cleared_date": date(2027, 1, 5)},
    {"account": "general", "reference": "dep", "item_type": "deposit", "amount": D("500"),
     "cleared_date": date(2027, 1, 2)},
]


def test_bank_reconciliation_cutoff_tests():
    findings, stats = execute_procedure("cash.bank_reconciliation",
                                        {"Bank_reconciliation": REC, "Cutoff_statement": CUTOFF},
                                        {"period_end": "2026-12-31"})
    general = stats["accounts"]["general"]
    assert general["adjusted_bank"] == "9300.00" == general["adjusted_book"]
    assert ("general", "check_after_period", "107") in keys(findings, "CLASH")
    assert ("general", "outstanding_not_cleared", "104") in keys(findings, "TENSION")
    assert ("general", "omitted_outstanding_check", "103") in keys(findings, "ORPHAN")
    assert general["deposits_in_transit_not_cleared"] == []
    findings, _ = execute_procedure("cash.bank_reconciliation",
                                    {"Bank_reconciliation": REC, "Cutoff_statement": CUTOFF},
                                    {"period_end": "2026-12-31", "dit_max_days": "3"})
    assert ("general", "deposit_cleared_slowly", "500.00") in keys(findings, "TENSION")


def test_interbank_transfers_detects_kiting_and_missing_rec_items():
    transfers = [
        {"transfer_id": "901", "amount": D("5000"), "from_account": "general",
         "to_account": "payroll", "disbursed_books": date(2027, 1, 2),
         "disbursed_bank": date(2027, 1, 4), "received_books": date(2026, 12, 30),
         "received_bank": date(2026, 12, 30)},
        {"transfer_id": "902", "amount": D("800"), "from_account": "general",
         "to_account": "payroll", "disbursed_books": date(2026, 12, 29),
         "disbursed_bank": date(2027, 1, 3), "received_books": date(2026, 12, 29),
         "received_bank": date(2027, 1, 2)},
    ]
    findings, _ = execute_procedure("cash.interbank_transfers",
                                    {"Transfers": transfers, "Bank_reconciliation": REC},
                                    {"period_end": "2026-12-31"})
    clash = keys(findings, "CLASH")
    assert ("901", "kiting") in clash
    assert ("902", "missing_outstanding_check") in clash
    assert ("902", "missing_deposit_in_transit") in clash


def test_inventory_trace_and_pricing():
    listing = [{"stock_number": "1", "description": "Acme", "model": "X1", "cost": D("1000")},
               {"stock_number": "2", "description": "Acme", "model": "X2", "cost": D("2000")},
               {"stock_number": "3", "description": "Brio", "model": "B", "cost": D("3000")}]
    count = [{"stock_number": "1", "description": "Acme", "model": "X1"},
             {"stock_number": "2", "description": "Acme", "model": "X9"},
             {"stock_number": "4", "description": "Brio", "model": "B"}]
    findings, stats = execute_procedure("inventory.count_listing_trace",
                                        {"Inventory_listing": listing, "Inventory_count": count},
                                        {})
    assert stats["counted_not_listed"] == ["4"] and stats["listed_not_counted"] == ["3"]
    assert ("details_differ", "2") in keys(findings, "TENSION")
    tests = [{"stock_number": "1", "recorded_cost": D("1000"), "audited_cost": D("900")},
             {"stock_number": "2", "recorded_cost": D("2000"), "audited_cost": D("2000")}]
    findings, stats = execute_procedure("inventory.pricing_projection",
                                        {"Inventory_listing": listing, "Pricing_tests": tests},
                                        {"inventory_tolerable_misstatement": "500"})
    assert D(stats["projected_misstatement"]) == D("200.00")  # 100 × 6000 / 3000
    assert ("evaluation",) in keys(findings, "AGREE")


def test_uncorrected_misstatements_against_materiality():
    rows = [{"description": "Obsolete stock", "identified": D("10000"), "likely": D("10000"),
             "current_assets": D("10000"), "income_before_taxes": D("10000")},
            {"description": "Prepaid", "identified": D("-4000"), "likely": D("-4000"),
             "current_assets": D("-4000"), "income_before_taxes": D("-4000")}]
    findings, stats = execute_procedure("completion.uncorrected_misstatements",
                                        {"Misstatements": rows}, {"materiality": "5000"})
    assert stats["totals"]["current_assets"] == "6000.00"
    assert ("material", "current_assets") in keys(findings, "CLASH")
    findings, stats = execute_procedure("completion.uncorrected_misstatements",
                                        {"Misstatements": rows}, {"materiality": "50000"})
    assert findings == [] and stats["remaining"]["income_before_taxes"] == "44000.00"
