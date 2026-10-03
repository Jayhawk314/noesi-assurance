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


def _check(entry, number, source, account, amount, date="2026-01-05"):
    """One check in the Journal: the expense debit and the bank credit."""
    return [{"entry_id": entry, "line": "1", "source": source, "document_number": number,
             "entry_date": date, "account": "60000", "debit": amount, "credit": "",
             "source_row": 2},
            {"entry_id": entry, "line": "2", "source": source, "document_number": number,
             "entry_date": date, "account": account, "debit": "", "credit": amount,
             "source_row": 3}]


def test_each_bank_account_and_payroll_is_its_own_check_run():
    # Review 2026-10-02 M1: two accounts numbered 1001-1003 and 5001-5002 are
    # two runs, not 3,997 missing checks; payroll checks are not
    # disbursements; a check with no number is counted, not dropped.
    journal = []
    for n in (1001, 1002, 1004):
        journal += _check(f"op {n}", str(n), "Check", "10100", "50")
    for n in (5001, 5002):
        journal += _check(f"sav {n}", str(n), "Bill Payment (Check)", "10300", "70")
    for n in (2001, 2002):
        journal += _check(f"pay {n}", str(n), "Payroll Check", "10200", "900")
    journal += _check("pay EFT", "", "Paycheck", "10200", "800")
    findings, stats = forensic.check_number_sequence({"Journal_entries": journal}, {})
    assert _keys(findings) == [("disbursements, account 10100", "1003", "gap")]
    assert findings[0].evidence["account"] == "10100"
    seq = stats["sequences"]
    assert set(seq) == {"disbursements, account 10100",
                        "disbursements, account 10300", "payroll"}
    assert (seq["payroll"]["first"], seq["payroll"]["last"],
            seq["payroll"]["not_numbered"]) == (2001, 2002, 1)
    assert stats["payroll_from"] == "Journal"
    # The bank credit, not the first line, is the check's amount.
    reused, _ = forensic.check_number_sequence(
        {"Journal_entries": _check("a", "7", "Check", "10100", "40")
         + _check("b", "7", "Check", "10100", "60", date="2026-02-01")}, {})
    assert reused[0].score == 100.0


def test_payroll_comes_from_the_register_when_the_journal_numbers_none():
    journal = _check("op 1", "1001", "Check", "10100", "50") + \
        _check("pay 1", "", "Payroll Check", "10200", "900")
    payroll = [{"employee_id": "E1", "pay_date": "2026-01-15", "net": "900",
                "check_number": "501", "source_row": 2},
               {"employee_id": "E2", "pay_date": "2026-01-15", "net": "800",
                "check_number": "503", "source_row": 3}]
    findings, stats = forensic.check_number_sequence(
        {"Journal_entries": journal, "Payroll_register": payroll}, {})
    assert _keys(findings) == [("payroll", "502", "gap")]
    assert stats["payroll_from"] == "payroll register"


def test_benford_counts_each_journal_amount_once():
    # Review 2026-10-02 M2: a balanced entry's debit and credit are one amount.
    lines = []
    for row in _benford_amounts(2000):
        lines += [row, {"debit": "", "credit": row["debit"], "source_row": 0}]
    _, stats = forensic.benford_first_digit(
        {"Journal_entries": lines}, {"benford_min_population": "1000"})
    assert stats["populations"]["journal lines"]["amounts"] == \
        len(_benford_amounts(2000))


def test_a_close_conforming_population_is_not_a_finding_for_one_digit():
    # Review 2026-10-02 M2: with nine digits tested, one "in excess" by the
    # z-test is common in data that conforms; the MAD decides. The digit is
    # still named in the results.
    rows = _benford_amounts(20000)
    moved = 300   # 1.5% of the amounts moved from 9 to 1
    nines = [i for i, r in enumerate(rows) if str(r["debit"]).startswith("9")][:moved]
    for i in nines:
        rows[i] = {"debit": Decimal("125.00"), "credit": "", "source_row": i}
    findings, stats = forensic.benford_first_digit(
        {"Journal_entries": rows}, {"benford_min_population": "1000"})
    result = stats["populations"]["journal lines"]
    assert result["conformity"] == "close conformity"
    assert [e["digit"] for e in result["digits_in_excess"]] == [1]
    assert findings == []


def test_a_negative_line_bigger_than_the_bank_credit_does_not_move_the_check():
    # Fixes check C1: check 2006 credits 700 to a vendor-credit account and
    # 300 to the bank; it stays in the bank's run, with no false gap.
    journal = []
    for n in range(2001, 2008):
        if n == 2006:
            journal += [
                {"entry_id": "c2006", "source": "Check", "document_number": "2006",
                 "entry_date": "2026-01-05", "account": "60000", "debit": "1000",
                 "credit": "", "source_row": 2},
                {"entry_id": "c2006", "source": "Check", "document_number": "2006",
                 "entry_date": "2026-01-05", "account": "1400 Vendor credit",
                 "debit": "", "credit": "700", "source_row": 3},
                {"entry_id": "c2006", "source": "Check", "document_number": "2006",
                 "entry_date": "2026-01-05", "account": "10100", "debit": "",
                 "credit": "300", "source_row": 4}]
        else:
            journal += _check(f"c{n}", str(n), "Check", "10100", "50")
    findings, stats = forensic.check_number_sequence({"Journal_entries": journal}, {})
    assert findings == []
    assert list(stats["sequences"]) == ["disbursements"]
    assert stats["sequences"]["disbursements"]["distinct_checks"] == 7


def test_benford_population_counts_only_amounts_tested():
    # Fixes check C2: a population below the minimum is read, not tested.
    findings, stats = forensic.benford_first_digit(
        {"Journal_entries": _benford_amounts(100)}, {"benford_min_population": "1000"})
    assert stats["population"] == 0
    assert stats["amounts_not_tested"] == len(_benford_amounts(100))


# ---------------------------------------------- self-approved payments (E3)

def test_self_approved_payments_and_missing_approvers():
    log = [
        {"payment_number": "501", "payee": "Acme", "payment_amount": "900",
         "prepared_by": "Pat Lee", "approved_by": "Sam Ortiz", "source_row": 2},
        {"payment_number": "502", "payee": "Pat Lee Services", "payment_amount": "1,500",
         "prepared_by": "Pat Lee", "approved_by": "  pat  LEE ", "source_row": 3},
        {"payment_number": "503", "payee": "Bolt", "payment_amount": "40",
         "prepared_by": "Pat Lee", "approved_by": "", "source_row": 4},
    ]
    findings, stats = forensic.self_approved_payments({"Payment_approvals": log}, {})
    assert _keys(findings) == [("502", "self_approved"), ("503", "no_approver")]
    assert stats["population"] == 3 and stats["self_approved"] == 1
    assert stats["no_approver"] == 1 and stats["self_approved_by"] == {"pat lee": 1}


def test_a_clean_approval_log_raises_nothing():
    log = [{"payment_number": str(n), "prepared_by": "Pat Lee", "approved_by": "Sam Ortiz",
            "payment_amount": "10", "source_row": n} for n in range(2, 12)]
    findings, stats = forensic.self_approved_payments({"Payment_approvals": log}, {})
    assert findings == [] and stats["population"] == 10


# ------------------------------------- the value-flow company (review 2 Oct)

def test_a_round_trip_needs_every_leg_in_the_value_flows():
    """The client's own payment does not join the flows (it ends at a vendor
    node), so a round trip is found when the flow schedule holds every leg,
    and the Rockwood case's name no longer appears in any run (2 Oct 2026)."""
    from procedures_ap.engines import execute_procedure
    # Amounts as the Workbench hands them to AP procedures (engine_view: floats).
    payments = [{"payment_number": "P1", "vendor_number": "Cove Ltd",
                 "payment_amount": 5000.0, "payment_date": "2026-05-01"}]
    back = {"flow_id": "F2", "source_entity": "Cove Ltd", "target_entity": "Acme Co",
            "amount": 4990.0, "flow_date": "2026-05-09"}
    found, _ = execute_procedure("forensic.closed_value_flow",
                                 {"Payments": payments, "Value_flows": [back]}, {})
    assert found == []
    out = {"flow_id": "F1", "source_entity": "Acme Co", "target_entity": "Cove Ltd",
           "amount": 5000.0, "flow_date": "2026-05-01"}
    found, stats = execute_procedure("forensic.closed_value_flow",
                                     {"Payments": payments, "Value_flows": [out, back]}, {})
    assert len(found) == 1 and stats["cycles"] == 1
    assert "Rockwood" not in str(found[0].evidence)


def test_vendor_employee_masked_numbers_short_phones_and_split_names():
    # Review 2026-10-02 L2.
    vendors = [
        {"vendor_number": "V1", "vendor_name": "Alpha", "bank_account": "****4821",
         "phone": "555-1234", "source_row": 2},
        {"vendor_number": "V2", "vendor_name": "Ann Lee Design", "bank_account": "",
         "phone": "", "source_row": 3},
    ]
    employees = [
        {"employee_id": "E1", "name": "Bo Diaz", "bank_account": "XXXX4821",
         "phone": "(415) 555-1234", "source_row": 2},
        {"employee_id": "E3", "first_name": "Ann", "last_name": "Lee",
         "bank_account": "", "phone": "", "source_row": 3},
        {"employee_id": "E4", "bank_account": "", "phone": "", "source_row": 4},
    ]
    findings, stats = forensic.vendor_employee_match(
        {"Vendors": vendors, "Payroll_master": employees}, {})
    assert sorted(_keys(findings)) == [
        ("e1", "alpha", "shared_phone"),             # 555-1234 meets (415) 555-1234
        ("e3", "ann lee design", "name_in_vendor_name"),   # first + last joined
    ]
    assert stats["masked_numbers_not_compared"] == 2     # neither ****4821 nor XXXX4821
    assert stats["employees_without_a_name"] == 1
