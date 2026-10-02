# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Forensic tests on invented records: check-number gaps and reuse, vendors
that match an employee, and the first-digit (Benford) test."""

import math
from decimal import Decimal

import pytest

from procedures_cycles import forensic
from procedures_cycles.common import PolicyError


def _keys(findings):
    return [tuple(f.key[1:]) for f in findings]


def test_gaps_and_reused_numbers_in_each_check_run():
    payments = [  # one check paying two bills is two rows, same payee and date
        {"payment_number": "1001", "vendor_number": "Acme", "payment_date": "2026-01-05",
         "payment_amount": "100", "source_row": 2},
        {"payment_number": "1002", "vendor_number": "Bolt", "payment_date": "2026-01-06",
         "payment_amount": "50", "source_row": 3},
        {"payment_number": "1002", "vendor_number": "Bolt", "payment_date": "2026-01-06",
         "payment_amount": "25", "source_row": 4},
        {"payment_number": "1006", "vendor_number": "Cord", "payment_date": "2026-01-09",
         "payment_amount": "70", "source_row": 5},
        {"payment_number": "EFT-7", "vendor_number": "Dune", "payment_date": "2026-01-09",
         "payment_amount": "10", "source_row": 6},
    ]
    direct = [{"payment_number": "1006", "vendor_number": "Edge",
               "payment_date": "2026-01-10", "payment_amount": "30", "source_row": 2},
              {"payment_number": "1007", "vendor_number": "Fern",
               "payment_date": "2026-01-11", "payment_amount": "30", "source_row": 3}]
    payroll = [{"employee_id": "E1", "pay_date": "2026-01-15", "net": "900",
                "check_number": "501", "source_row": 2},
               {"employee_id": "E2", "pay_date": "2026-01-15", "net": "800",
                "check_number": "503", "source_row": 3}]
    findings, stats = forensic.check_number_sequence(
        {"Payments": payments, "Direct_payments": direct, "Payroll_register": payroll}, {})
    assert _keys(findings) == [
        ("disbursements", "1003-1005", "gap"),
        ("disbursements", "1006", "reused"),
        ("payroll", "502", "gap"),
    ]
    reused = findings[1]
    assert reused.verdict == "CLASH" and reused.evidence["uses"] == [
        ["cord", "2026-01-09"], ["edge", "2026-01-10"]]
    d = stats["sequences"]["disbursements"]
    assert (d["first"], d["last"], d["missing_numbers"], d["not_numbered"]) == \
        (1001, 1007, 3, 1)


def test_vendors_matching_an_employee_by_bank_phone_tax_id_or_name():
    vendors = [
        {"vendor_number": "V1", "vendor_name": "DM Consulting LLC",
         "bank_account": "0044-1234-99", "phone": "(406) 555-0101", "source_row": 2},
        {"vendor_number": "V2", "vendor_name": "Dana Merritt Services",
         "bank_account": "", "phone": "406.555.0199", "source_row": 3},
        {"vendor_number": "V3", "vendor_name": "Granite Peak Properties",
         "bank_account": "77665544", "phone": "", "source_row": 4},
    ]
    employees = [
        {"employee_id": "E07", "name": "Dana Merritt", "bank_account": "0044123499",
         "phone": "406-555-0199", "source_row": 2},
        {"employee_id": "E08", "name": "Lee", "bank_account": "", "phone": "",
         "source_row": 3},
    ]
    findings, stats = forensic.vendor_employee_match(
        {"Vendors": vendors, "Payroll_master": employees}, {})
    assert sorted(_keys(findings)) == [
        ("e07", "dana merritt services", "name_in_vendor_name"),
        ("e07", "dana merritt services", "shared_phone"),
        ("e07", "dm consulting llc", "shared_bank_account"),
    ]
    # Neither side has a tax ID: said, not skipped in silence. A one-word
    # name ("Lee") is too weak to match on.
    assert stats["fields_not_compared"] == ["tax_id"]
    assert set(stats["fields_compared"]) == {"bank_account", "phone", "name"}


def _benford_amounts(n, shift=None):
    """n amounts whose first digits follow Benford's law exactly (rounded);
    with ``shift``, 15% of them moved to start with that digit."""
    out = []
    for d in range(1, 10):
        out += [Decimal(f"{d}25.00")] * round(n * math.log10(1 + 1 / d))
    if shift:
        moved = int(len(out) * 0.15)
        out = out[moved:] + [Decimal(f"{shift}90.00")] * moved
    return [{"debit": a, "credit": "", "source_row": i} for i, a in enumerate(out)]


def test_benford_conformity_and_the_digits_in_excess():
    natural, _ = forensic.benford_first_digit(
        {"Journal_entries": _benford_amounts(2000)}, {"benford_min_population": "1000"})
    assert natural == []
    shifted, stats = forensic.benford_first_digit(
        {"Journal_entries": _benford_amounts(2000, shift=9)},
        {"benford_min_population": "1000"})
    assert _keys(shifted) == [("journal lines", "first_digit")]
    result = stats["populations"]["journal lines"]
    assert result["conformity"] == "nonconformity"
    assert [e["digit"] for e in result["digits_in_excess"]] == [9]


def test_benford_refuses_a_small_population_and_needs_the_minimum_set():
    small = _benford_amounts(100) + [{"debit": "4.00", "credit": "", "source_row": 0}]
    findings, stats = forensic.benford_first_digit(
        {"Journal_entries": small}, {"benford_min_population": "1000"})
    assert _keys(findings) == [("journal lines", "not_performed")]
    assert findings[0].evidence["finding_class"] == "REFUSAL"
    assert stats["populations"]["journal lines"]["tested"] is False
    with pytest.raises(PolicyError, match="benford_min_population"):
        forensic.benford_first_digit({"Journal_entries": small}, {})


def test_the_journal_is_the_check_population_when_it_numbers_its_checks():
    # Payment records may hold only bill payments; the Journal holds every
    # check. One check is one transaction however many lines it has.
    journal = [
        {"entry_id": "2026-01-05 Check 2001 Acme", "line": "1", "source": "Check",
         "document_number": "2001", "entry_date": "2026-01-05", "credit": "", "source_row": 2},
        {"entry_id": "2026-01-05 Check 2001 Acme", "line": "2", "source": "Check",
         "document_number": "2001", "entry_date": "2026-01-05", "credit": "40", "source_row": 3},
        {"entry_id": "2026-01-06 Bill Payment (Check) 2002 Bolt", "line": "1",
         "source": "Bill Payment (Check)", "document_number": "2002",
         "entry_date": "2026-01-06", "credit": "60", "source_row": 4},
        {"entry_id": "2026-01-08 Check 2002 Cord", "line": "1", "source": "Check",
         "document_number": "2002", "entry_date": "2026-01-08", "credit": "9", "source_row": 5},
        {"entry_id": "2026-01-09 Invoice 2004 Dune", "line": "1", "source": "Invoice",
         "document_number": "2004", "entry_date": "2026-01-09", "credit": "", "source_row": 6},
        {"entry_id": "2026-01-10 Check 2005 Edge", "line": "1", "source": "Check",
         "document_number": "2005", "entry_date": "2026-01-10", "credit": "5", "source_row": 7},
    ]
    payments = [{"payment_number": "2002", "vendor_number": "Bolt",
                 "payment_date": "2026-01-06", "payment_amount": "60", "source_row": 2}]
    findings, stats = forensic.check_number_sequence(
        {"Journal_entries": journal, "Payments": payments}, {})
    assert stats["disbursements_from"] == "Journal"
    assert _keys(findings) == [("disbursements", "2003-2004", "gap"),
                               ("disbursements", "2002", "reused")]
    assert stats["sequences"]["disbursements"]["distinct_checks"] == 3
