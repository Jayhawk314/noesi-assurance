# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Duplicate bills on invented data (independent of any case study)."""

from decimal import Decimal as D

from procedures_cycles.engines import execute_procedure


def bill(num, vendor, amount, dated="2025-03-03"):
    return {"voucher_number": num, "vendor_number": vendor,
            "voucher_amount": D(amount), "voucher_date": dated}


BILLS = [
    bill("A-100", "Acme Supply", "500.00"),
    bill("a 100", "Acme Supply Inc", "500.00", "2025-03-17"),  # same invoice, look-alike
    bill("B-7", "Birch Co", "80.00"),
    bill("B7", "Birch Co", "95.00"),                          # same number, other amount
    bill("C-1", "Cedar", "40.00"),
    bill("", "Cedar", "40.00"),                               # no number: not compared
]


def keys(findings):
    return {tuple(f.key[1:]) for f in findings}


def test_duplicate_bills_same_amount_and_different_amount():
    findings, stats = execute_procedure("ap.duplicate_bills", {"Vouchers": BILLS}, {})
    assert ("a100", "same_invoice_same_amount") in keys(findings)
    assert ("b7", "same_invoice_different_amounts") in keys(findings)
    clash = next(f for f in findings if f.key[2] == "same_invoice_same_amount")
    assert clash.verdict == "CLASH" and "under different vendor records" in clash.reason
    assert stats["likely_duplicates"] == 1


def test_no_duplicates_no_findings():
    findings, _ = execute_procedure("ap.duplicate_bills",
                                    {"Vouchers": [bill("X1", "V", "1"),
                                                  bill("X2", "V", "1")]}, {})
    assert findings == []
