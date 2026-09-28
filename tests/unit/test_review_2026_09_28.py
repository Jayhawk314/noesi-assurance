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
LETTER = {"period_end": "2025-12-31", "report_date": "2026-02-15",
          "rep_signers": "CEO"}


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


# ------------------------------------------------ F3: total-row label
def test_f3_a_payee_named_total_is_never_a_total_row():
    from procedures_ap.ingest import approve_mapping, normalize_table, propose_mapping
    headers = ["Payment Number", "Payment Amount", "Vendor"]
    rows = [dict(zip(headers, r)) for r in (("P1", "100.00", "Acme"),
                                            ("P2", "100.00", "Total Cycling"))]
    spec = approve_mapping(propose_mapping("Payments", headers, proposed_by="p"),
                           approved_by="r")
    table = normalize_table(rows, spec)
    assert [r["payment_number"] for r in table.records] == ["P1", "P2"]
    assert table.diagnostics["total_rows_set_aside"] == 0


# ================================================ re-review 2026-09-29 (RR1-RR4)
NEGATED = {
    "fs_responsibility": "Management is not responsible for the financial statements",
    "internal_control": "Management disclaims responsibility for internal control",
    "estimates": "The accounting estimates are not reasonable",
    "related_parties": "Related parties were not disclosed",
    "subsequent_events": "Subsequent events were not adjusted or disclosed",
}


@pytest.mark.parametrize("target, sentence", sorted(NEGATED.items()))
def test_rr1_a_sentence_that_denies_a_representation_never_provides_it(target, sentence):
    rows = [r for r in letter() if r["code"] != target]
    rows.append({"representation": sentence, "obtained": "yes",
                 "dated": date(2026, 2, 15), "signed_by": "CEO"})
    findings, _ = execute_procedure("completion.representation_letter",
                                    {"Representations": rows}, LETTER)
    assert keys(findings) == {(target, "not_obtained")}


@pytest.mark.parametrize("signer", ["false", "true", "0", "yes", "X"])
def test_rr1_booleans_and_marks_are_not_signatures(signer):
    findings, _ = execute_procedure("completion.representation_letter",
                                    {"Representations": letter(signed=signer)}, LETTER)
    assert keys(findings) == {("letter", "unsigned")}


def test_rr1_a_conflicting_representation_is_named_not_resolved_to_obtained():
    rows = letter() + [{"code": "fraud", "representation": "fraud", "obtained": "refused",
                        "dated": date(2026, 2, 15), "signed_by": "CEO"}]
    findings, _ = execute_procedure("completion.representation_letter",
                                    {"Representations": rows}, LETTER)
    [conflict] = findings
    assert conflict.key[1:] == ("fraud", "not_obtained")
    assert "both obtained and ['refused']" in conflict.reason


def test_rr2_a_shipping_document_without_a_date_is_not_a_clean_cutoff():
    invoices = [{"invoice_number": "I1", "invoice_date": date(2025, 12, 30),
                 "amount": D("4000"), "ship_date": None, "shipping_document": "BOL-9"}]
    findings, stats = execute_procedure("rev.sales_cutoff", {"Sales_invoices": invoices},
                                        {"period_end": "2025-12-31"})
    assert keys(findings) == {("i1", "no_ship_date")} and stats["exceptions"] == 1


@pytest.mark.parametrize("method, policies", [
    ("ar.confirmations_nonstatistical", {"ar_tolerable_misstatement": "5000"}),
    ("ar.confirmations_mus", {"ar_tolerable_misstatement": "5000",
                              "ar_risk_incorrect_acceptance": "0.05",
                              "mus_interval": "10000"}),
    ("ar.confirmations_difference", {"ar_tolerable_misstatement": "5000",
                                     "ar_risk_incorrect_acceptance": "0.05"}),
])
def test_rr2_a_confirmation_with_no_confirmed_value_is_not_a_zero(method, policies):
    listing = [{"customer_number": c, "balance": D(b)}
               for c, b in (("C1", "20000"), ("C2", "8000"), ("C3", "6000"))]
    replies = [{"customer_number": "C1", "book_value": D("20000"),
                "confirmed_value": D("20000"), "classification": "no_difference"},
               {"customer_number": "C2", "book_value": D("8000"),
                "confirmed_value": None, "classification": "timing"}]
    findings, _ = execute_procedure(method, {"AR_listing": listing,
                                             "Confirmations": replies}, policies)
    assert ("incomplete_rows", "Confirmations") in keys(findings)


def test_rr3_column_order_cannot_turn_a_payee_into_a_total():
    from procedures_ap.ingest import approve_mapping, normalize_table, propose_mapping
    headers = ["Vendor", "Payment Number", "Payment Amount"]
    rows = [dict(zip(headers, r)) for r in (("Acme", "P1", "100.00"),
                                            ("Total Cycling", "P2", "100.00"))]
    spec = approve_mapping(propose_mapping("Payments", headers, proposed_by="p"),
                           approved_by="r")
    table = normalize_table(rows, spec)
    assert [r["payment_number"] for r in table.records] == ["P1", "P2"]


@pytest.mark.parametrize("value", ["2026-02-15garbage", "2026-02-15T10:00:00", "Feb 15"])
def test_rr4_a_malformed_report_date_is_refused_not_truncated(value):
    with pytest.raises(PolicyError, match="not a date"):
        execute_procedure("completion.subsequent_events", {"Journal_entries": LATE},
                          {"period_end": "2025-12-31", "se_threshold": "1",
                           "report_date": value})


# ================================================ second re-review (RRR1-RRR3)
@pytest.mark.parametrize("signer", ["refused", "not signed by management",
                                    "signature pending", "CEO (unsigned)",
                                    "not applicable"])
def test_rrr1_a_phrase_about_signing_is_not_the_named_signer(signer):
    findings, _ = execute_procedure("completion.representation_letter",
                                    {"Representations": letter(signed=signer)}, LETTER)
    assert keys(findings) == {("letter", "unsigned")}


def test_rrr1_every_named_signer_must_sign_and_who_is_the_auditors_call():
    both = {**LETTER, "rep_signers": "CEO, CFO"}
    findings, _ = execute_procedure("completion.representation_letter",
                                    {"Representations": letter(signed="CEO")}, both)
    [unsigned] = findings
    assert "not signed by cfo" in unsigned.reason
    findings, _ = execute_procedure("completion.representation_letter",
                                    {"Representations": letter(signed="CEO and CFO")},
                                    both)
    assert findings == []
    with pytest.raises(PolicyError, match="rep_signers"):
        execute_procedure("completion.representation_letter",
                          {"Representations": letter()},
                          {"period_end": "2025-12-31", "report_date": "2026-02-15"})


def test_rrr2_a_post_period_invoice_without_a_ship_date_is_not_clean():
    invoices = [{"invoice_number": "I1", "invoice_date": date(2026, 1, 2),
                 "amount": D("4000"), "ship_date": None, "shipping_document": "BOL-9"}]
    findings, stats = execute_procedure("rev.sales_cutoff", {"Sales_invoices": invoices},
                                        {"period_end": "2025-12-31"})
    assert keys(findings) == {("i1", "no_ship_date")} and stats["exceptions"] == 1


def _normalize(role, headers, lines):
    from procedures_ap.ingest import approve_mapping, normalize_table, propose_mapping
    spec = approve_mapping(propose_mapping(role, headers, proposed_by="p"),
                           approved_by="r")
    return normalize_table([dict(zip(headers, line)) for line in lines], spec)


def test_rrr3_an_entity_named_total_in_a_name_key_is_still_a_record():
    table = _normalize("Value_flows", ["Source Entity", "Target Entity", "Amount", "Date"],
                       [("Acme", "Bank", "100.00", "2025-01-01"),
                        ("Total Cycling", "Bank", "100.00", "2025-01-02")])
    assert [r["source_entity"] for r in table.records] == ["Acme", "Total Cycling"]
    assert table.diagnostics["total_rows_set_aside"] == 0


def test_rrr3_a_vendor_keyed_purchase_order_named_total_is_still_a_record():
    table = _normalize("Purchase_orders", ["Vendor", "PO Amount", "PO Date"],
                       [("Acme", "100.00", "2025-01-01"),
                        ("Total Cycling", "100.00", "2025-01-02")])
    assert len(table.records) == 2 and table.rejects == []


def test_rrr3_a_real_report_total_is_still_set_aside():
    table = _normalize("Value_flows", ["Source Entity", "Target Entity", "Amount", "Date"],
                       [("Acme", "Bank", "100.00", "2025-01-01"),
                        ("Birch", "Bank", "50.00", "2025-01-02"),
                        ("TOTAL", "", "150.00", "")])
    assert len(table.records) == 2
    assert table.diagnostics["total_rows_set_aside"] == 1


# ================================================ third re-review (RRRR1)
def test_rrrr1_a_numeric_looking_identifier_is_not_a_total_measure():
    table = _normalize("Value_flows", ["Source Entity", "Target Entity", "Amount", "Date"],
                       [("Acme", "Bank", "100.00", "2025-01-01"),
                        ("Total Cycling", "12345", "100.00", "")])
    assert [r["source_entity"] for r in table.records] == ["Acme", "Total Cycling"]


def test_rrrr1_a_compact_date_is_not_a_total_measure():
    table = _normalize("Purchase_orders", ["Vendor", "PO Amount", "PO Date"],
                       [("Acme", "100.00", "2025-01-01"),
                        ("Total Cycling", "100.00", "20250102")])
    assert len(table.records) == 2 and table.rejects == []


# ================================================ fourth re-review (RRRRR1-2)
def test_rrrrr1_a_payroll_total_with_hours_is_a_total_not_an_employee():
    table = _normalize("Payroll_register",
                       ["Employee ID", "Pay Date", "Hours", "Gross", "Net"],
                       [("E1", "2025-06-15", "80", "2000.00", "1600.00"),
                        ("E2", "2025-06-15", "80", "1800.00", "1440.00"),
                        ("TOTAL", "", "160", "3800.00", "3040.00")])
    assert [r["employee_id"] for r in table.records] == ["E1", "E2"]
    assert table.control_total == D("3800.00")          # gross, not doubled


def test_rrrrr2_an_inventory_total_ties_on_extended_cost_not_unit_cost():
    table = _normalize("Inventory_listing",
                       ["Stock Number", "Quantity", "Unit Cost", "Cost"],
                       [("KV-1", "10", "5.00", "50.00"),
                        ("KV-2", "4", "25.00", "100.00"),
                        ("TOTAL", "14", "", "150.00")])
    assert [r["stock_number"] for r in table.records] == ["KV-1", "KV-2"]
    assert table.control_total == D("150.00")           # extended cost, not unit cost


# ================================================ fifth re-review (all measures tie)
def test_rereview5_one_tying_measure_cannot_hide_another_that_contradicts():
    table = _normalize("Payroll_register",
                       ["Employee ID", "Pay Date", "Hours", "Gross", "Net"],
                       [("E1", "2025-06-15", "80", "2000.00", "1600.00"),
                        ("E2", "2025-06-15", "80", "1800.00", "1440.00"),
                        ("TOTAL", "", "160", "3800.00", "9999.00")])   # net contradicts
    assert [r["employee_id"] for r in table.records] == ["E1", "E2"]   # never loaded
    [gap] = table.diagnostics["total_rows_not_tying"]
    assert any("net shows 9999.00, rows above sum to 3040.00" in g for g in gap["gaps"])


def test_rereview5_a_zero_bucket_does_not_mask_another_bucket():
    table = _normalize("AR_listing", ["Customer", "Current", "31 - 60", "Balance"],
                       [("C1", "100.00", "0", "100.00"),
                        ("C2", "50.00", "0", "50.00"),
                        ("TOTAL", "999.00", "0", "150.00")])        # current contradicts
    assert len(table.records) == 2
    assert table.diagnostics["total_rows_not_tying"]


def test_rereview5_a_fully_tying_total_is_accepted():
    table = _normalize("Payroll_register",
                       ["Employee ID", "Pay Date", "Hours", "Gross", "Net"],
                       [("E1", "2025-06-15", "80", "2000.00", "1600.00"),
                        ("TOTAL", "", "80", "2000.00", "1600.00")])
    assert len(table.records) == 1 and table.diagnostics["total_rows_not_tying"] == []


# ================================================ sixth re-review
PAY = ["Employee ID", "Pay Date", "Hours", "Gross", "Net"]


def test_rereview6_an_unreadable_total_amount_is_named_not_ignored():
    table = _normalize("Payroll_register", PAY,
                       [("E1", "2025-06-15", "80", "2000", "1600"),
                        ("E2", "2025-06-15", "80", "1800", "1440"),
                        ("TOTAL", "", "160", "3,8O0", "3040")])
    assert len(table.records) == 2
    [held] = table.diagnostics["total_rows_not_tying"]
    assert any("gross shows '3,8O0', not a number" in g for g in held["gaps"])


def test_rereview6_a_sparse_record_named_total_is_held_for_review_not_called_a_total():
    table = _normalize("AR_listing", ["Customer", "Balance"], [("Total Cycling", "100.00")])
    [reject] = table.rejects
    assert reject["reason"].startswith("held for review")
    assert "real record named like a total" in reject["reason"]


def test_rereview6_a_grand_total_is_compared_over_all_rows():
    table = _normalize("Payroll_register", PAY,
                       [("E1", "2025-06-15", "80", "100", "80"),
                        ("E2", "2025-06-15", "0", "100", "80"),
                        ("Total for Dept A", "", "80", "200", "160"),
                        ("E3", "2025-06-15", "80", "100", "80"),
                        ("GRAND TOTAL", "", "160", "999", "240")])
    [held] = table.diagnostics["total_rows_not_tying"]
    assert held["basis"] == "over all rows"
    assert held["gaps"] == ["gross shows 999, rows above sum to 300"]
