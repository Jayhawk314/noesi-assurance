# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Revenue: sales cutoff and credit memos after period end, planted errors."""

from datetime import date
from decimal import Decimal as D

from procedures_cycles.engines import execute_procedure

PE = "2025-12-31"


def inv(number, dated, shipped, amount, doc="BOL"):
    return {"invoice_number": number, "invoice_date": date.fromisoformat(dated),
            "ship_date": date.fromisoformat(shipped) if shipped else None,
            "amount": D(amount), "customer": "C1",
            "shipping_document": f"{doc}-{number}" if doc else ""}


INVOICES = [
    inv("100", "2025-12-20", "2025-12-19", "4000.00"),          # clean
    inv("101", "2025-12-30", "2026-01-04", "12500.00"),         # invoiced before shipment
    inv("102", "2026-01-02", "2025-12-29", "3300.00"),          # shipped before invoicing
    inv("103", "2025-12-15", None, "2750.00", doc=""),          # no shipping evidence
    inv("104", "2025-11-02", None, "900.00", doc="BOL"),        # document, date missing
    inv("105", "2026-01-05", "2026-01-05", "800.00"),           # next period, clean
]


def keys(findings):
    return {(f.key[1], f.key[2]) for f in findings}


def test_sales_cutoff_finds_both_directions_and_unshipped_sales():
    findings, stats = execute_procedure("rev.sales_cutoff", {"Sales_invoices": INVOICES},
                                        {"period_end": PE})
    assert keys(findings) == {("101", "invoiced_before_shipment"),
                              ("102", "shipped_before_invoicing"),
                              ("103", "no_shipping_evidence"),
                              # a shipping document without a date: untestable
                              ("104", "no_ship_date")}
    assert stats["overstated_cutoff"] == "12500.00"
    assert stats["understated_cutoff"] == "3300.00"


MEMOS = [
    {"memo_number": "CM1", "memo_date": date(2026, 1, 8), "invoice_number": "101",
     "amount": D("-12500.00")},                                  # reverses a 2025 sale
    {"memo_number": "CM2", "memo_date": date(2026, 1, 9), "invoice_number": "105",
     "amount": D("200.00")},                                     # reverses a 2026 sale
    {"memo_number": "CM3", "memo_date": date(2026, 1, 10), "invoice_number": "999",
     "amount": D("640.00")},                                     # no such invoice
    {"memo_number": "CM4", "memo_date": date(2025, 12, 10), "invoice_number": "100",
     "amount": D("150.00")},                                     # in the period
    {"memo_number": "CM5", "memo_date": date(2026, 3, 1), "invoice_number": "100",
     "amount": D("75.00")},                                      # outside a 30-day window
]


def test_credit_memos_after_period_end_reverse_period_sales_or_match_nothing():
    tables = {"Credit_memos": MEMOS, "Sales_invoices": INVOICES}
    findings, stats = execute_procedure("rev.credit_memos_after_period_end", tables,
                                        {"period_end": PE, "rev_credit_memo_days": "30"})
    assert keys(findings) == {("cm1", "reverses_period_sale"),
                              ("cm3", "no_matching_invoice")}
    assert stats["reversing_period_sales"] == "12500.00"
    # without a window every later memo is considered
    findings, _ = execute_procedure("rev.credit_memos_after_period_end", tables,
                                    {"period_end": PE})
    assert ("cm5", "reverses_period_sale") in keys(findings)


def test_new_role_hints_leave_existing_filename_guesses_alone():
    from procedures_ap.ingest import infer_role
    from procedures_cycles.roles import register_roles
    register_roles()
    assert infer_role("invoices.csv") == "Vouchers"            # payables, as before
    assert infer_role("journal entries.csv") == "GL"           # as before
    assert infer_role("sales invoices.csv") == "Sales_invoices"
    assert infer_role("credit memos.xlsx") == "Credit_memos"
    assert infer_role("je listing.csv") == "Journal_entries"
