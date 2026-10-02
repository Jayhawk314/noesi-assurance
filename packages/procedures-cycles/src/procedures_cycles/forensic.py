# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Forensic tests on any client's records: the check-number sequence,
vendors who look like employees, and the first-digit (Benford) test.

Each produces leads for the auditor to follow up, never conclusions. Every
figure in a finding is counted from the rows loaded; nothing is estimated
and no threshold is chosen here that is the auditor's to choose.
"""

from __future__ import annotations

import math
from decimal import Decimal

from procedures_cycles.common import (
    PolicyError, dec, day, key_text, money, receipt, records, source_ref, text,
)

# ------------------------------------------------------------ check sequence


def _check_number(value) -> int | None:
    """A check number as an integer; EFTs, blanks and text references are None."""
    raw = text(value)
    return int(raw) if raw.isdigit() else None


def check_number_sequence(tables: dict, policies: dict):
    """Gaps and reused numbers in each run of check numbers.

    Disbursement checks (bill payments and checks with no bill) are one
    sequence; payroll checks, usually drawn on their own account, are
    another. A gap is a number never seen between the first and last check
    of a sequence: voided, issued outside the records loaded, or missing.
    A number reused for a different payee or date is a second check under
    one number. One check paying several bills appears on several rows with
    the same payee and date, and is not a reuse.
    """
    pid = "forensic.check_number_sequence"
    # The Journal holds every check that moved the books (its completeness is
    # proved by je.population_completeness); the payment records may hold
    # only bill payments. Each check is one transaction however many lines.
    journal_checks = [r for r in records(tables, "Journal_entries")
                      if _is_check(r.get("source")) and text(r.get("document_number"))]
    sources = {
        "disbursements": (("Payments", "check_number", "payment_number", "vendor_number",
                           "payment_date", "payment_amount"),
                          ("Direct_payments", None, "payment_number", "vendor_number",
                           "payment_date", "payment_amount")),
        "payroll": (("Payroll_register", "check_number", None, "employee_id",
                     "pay_date", "net"),),
    }
    if journal_checks:
        sources["disbursements"] = (("Journal_entries", "document_number", None,
                                     "entry_id", "entry_date", "credit"),)
    findings, stats = [], {"sequences": {}}
    for sequence, roles in sources.items():
        seen: dict[int, list[tuple[str, dict, str, object]]] = {}
        not_numbered = 0
        rows_read = 0
        for role, field, fallback, payee_field, date_field, _ in roles:
            rows = journal_checks if role == "Journal_entries" else records(tables, role)
            if role == "Journal_entries":   # one per transaction, not per line
                rows = list({key_text(r.get("entry_id")): r for r in rows}.values())
            for row in rows:
                rows_read += 1
                raw = row.get(field) if field else None
                if not text(raw) and fallback:
                    raw = row.get(fallback)
                number = _check_number(raw)
                if number is None:
                    not_numbered += 1
                    continue
                seen.setdefault(number, []).append(
                    (role, row, key_text(row.get(payee_field)), day(row.get(date_field))))
        if not seen:
            if rows_read:
                stats["sequences"][sequence] = {"rows": rows_read, "numbered": 0,
                                                "not_numbered": not_numbered}
            continue
        numbers = sorted(seen)
        first, last = numbers[0], numbers[-1]
        missing: list[tuple[int, int]] = []
        for low, high in zip(numbers, numbers[1:]):
            if high - low > 1:
                missing.append((low + 1, high - 1))
        for start, end in missing:
            count = end - start + 1
            span = str(start) if start == end else f"{start}-{end}"
            findings.append(receipt(
                pid, (sequence, span, "gap"), "TENSION",
                f"{sequence} checks: {'number' if count == 1 else f'{count} numbers'} "
                f"{span} not in the records, between check {start - 1} and check "
                f"{end + 1}. Voided, issued outside these records, or missing? Inspect "
                "the voided checks and the bank statements",
                {"finding_class": "EXPECTED_BUT_MISSING", "cycle": "forensic",
                 "sequence": sequence, "first_missing": start, "last_missing": end,
                 "count": count,
                 "source_rows": [source_ref(r[0], r[1], "payment_number")
                                 for r in seen[start - 1] + seen[end + 1]]}))
        reused = 0
        for number in numbers:
            uses = {(payee, when) for _, _, payee, when in seen[number]}
            if len(uses) > 1:
                reused += 1
                rows = seen[number]
                findings.append(receipt(
                    pid, (sequence, str(number), "reused"), "CLASH",
                    f"{sequence} check {number} appears for "
                    + "; ".join(f"{p or '(no payee)'} on {w or '(no date)'}"
                                for p, w in sorted(uses, key=str))
                    + ": two checks under one number, or a record changed after it "
                      "was issued",
                    {"finding_class": "PROVED_EXCEPTION", "cycle": "forensic",
                     "sequence": sequence, "check": number,
                     "uses": sorted([p, str(w)] for p, w in uses),
                     "source_rows": [source_ref(r[0], r[1], "payment_number")
                                     for r in rows]},
                    sum((money(r[1].get(f[5])) for r in rows
                         for f in roles if f[0] == r[0]), Decimal("0"))))
        stats["sequences"][sequence] = {
            "rows": rows_read, "numbered": sum(len(v) for v in seen.values()),
            "not_numbered": not_numbered, "first": first, "last": last,
            "distinct_checks": len(numbers),
            "missing_numbers": sum(e - s + 1 for s, e in missing),
            "gaps": len(missing), "reused_numbers": reused}
    stats["disbursements_from"] = ("Journal" if journal_checks
                                   else "payment records")
    stats["population"] = sum(s["rows"] for s in stats["sequences"].values())
    stats["exceptions"] = len(findings)
    return findings, stats


def _is_check(source) -> bool:
    """A transaction type naming a check ("Check", "Bill Payment (Check)",
    "Cheque"), as accounting systems print them."""
    words = text(source).lower()
    return "check" in words or "cheque" in words


# --------------------------------------------------- vendors and employees

def _digits(value) -> str:
    return "".join(c for c in text(value) if c.isdigit())


def _words(value) -> frozenset[str]:
    noise = {"inc", "llc", "ltd", "co", "corp", "company", "the", "and", "of",
             "consulting", "services", "service", "group"}
    cleaned = "".join(c if c.isalnum() else " " for c in text(value).lower())
    return frozenset(w for w in cleaned.split() if w not in noise and len(w) > 1)


def vendor_employee_match(tables: dict, policies: dict):
    """Vendors that share a bank account, phone number or tax ID with an
    employee, or whose name contains an employee's full name.

    Each is a lead: the employee may own or control the vendor, and be paid
    twice or through a shell. Addresses are compared in the payroll register
    tests. Fields not loaded on both sides are reported as not compared.
    """
    pid = "forensic.vendor_employee_match"
    vendors = records(tables, "Vendors")
    employees = records(tables, "Payroll_master")
    findings = []
    compared, not_compared = [], []
    for field, label, normalize, minimum in (
            ("bank_account", "bank account", _digits, 4),
            ("phone", "phone number", _digits, 7),
            ("tax_id", "tax ID", _digits, 9)):
        on_vendors = any(text(v.get(field)) for v in vendors)
        on_employees = any(text(e.get(field)) for e in employees)
        if not (on_vendors and on_employees):
            not_compared.append(field)
            continue
        compared.append(field)
        by_value: dict[str, list[dict]] = {}
        for e in employees:
            value = normalize(e.get(field))
            if len(value) >= minimum:
                by_value.setdefault(value, []).append(e)
        for v in vendors:
            value = normalize(v.get(field))
            for e in by_value.get(value, []) if len(value) >= minimum else []:
                vendor = text(v.get("vendor_name")) or text(v.get("vendor_number"))
                emp = key_text(e.get("employee_id"))
                findings.append(receipt(
                    pid, (emp, key_text(vendor), f"shared_{field}"), "TENSION",
                    f"vendor {vendor} has the same {label} as employee {emp} "
                    f"({text(e.get('name'))}). Does the employee own or control it? "
                    "Check what it was paid and whether it is a disclosed related party",
                    {"finding_class": "CONJECTURE", "cycle": "forensic",
                     "employee": emp, "vendor": vendor, "field": field,
                     "source_rows": [source_ref("Vendors", v, "vendor_number"),
                                     source_ref("Payroll_master", e, "employee_id")]}))
    names = [(e, _words(e.get("name"))) for e in employees]
    if any(n for _, n in names) and vendors:
        compared.append("name")
        for v in vendors:
            vendor = text(v.get("vendor_name")) or text(v.get("vendor_number"))
            vendor_words = _words(vendor)
            for e, words in names:
                if len(words) >= 2 and words <= vendor_words:
                    emp = key_text(e.get("employee_id"))
                    findings.append(receipt(
                        pid, (emp, key_text(vendor), "name_in_vendor_name"), "TENSION",
                        f"vendor {vendor} carries the name of employee {emp} "
                        f"({text(e.get('name'))}). The same person, a relative, or a "
                        "coincidence? Ask, and check what it was paid",
                        {"finding_class": "CONJECTURE", "cycle": "forensic",
                         "employee": emp, "vendor": vendor, "field": "name",
                         "source_rows": [source_ref("Vendors", v, "vendor_number"),
                                         source_ref("Payroll_master", e, "employee_id")]}))
    else:
        not_compared.append("name")
    stats = {"population": len(vendors), "employees": len(employees),
             "fields_compared": compared, "fields_not_compared": not_compared,
             "exceptions": len(findings)}
    return findings, stats


# ------------------------------------------------------------- first digit

# Nigrini, Benford's Law (2012), table 7.1: mean absolute deviation bands for
# the first-digit test. Published constants, not tuned on any case.
_MAD_BANDS = ((Decimal("0.006"), "close conformity"),
              (Decimal("0.012"), "acceptable conformity"),
              (Decimal("0.015"), "marginally acceptable conformity"))
_BENFORD = {d: math.log10(1 + 1 / d) for d in range(1, 10)}


def _first_digit(amount: Decimal) -> int | None:
    a = abs(amount)
    if a < 10:          # Nigrini: amounts under 10 are left out of the test
        return None
    return int(str(int(a))[0])


def benford_first_digit(tables: dict, policies: dict):
    """First-digit test on each population of amounts loaded: journal lines,
    bills, and payments, each tested apart.

    A population smaller than ``benford_min_population`` (the auditor's
    choice) is not tested, and said so. Nonconformity says where amounts
    are not what natural processes produce (invented figures, amounts kept
    under a limit); it proves nothing alone. The digits most in excess are
    named so the auditor can look at those amounts.
    """
    pid = "forensic.benford_first_digit"
    minimum = dec(policies.get("benford_min_population"))
    if minimum is None:
        raise PolicyError("policy 'benford_min_population' is not set; it is the "
                          "auditor's decision")
    populations = {
        "journal lines": [dec(r.get("debit")) or dec(r.get("credit"))
                          or dec(r.get("amount"))
                          for r in records(tables, "Journal_entries")],
        "bills": [dec(r.get("voucher_amount")) for r in records(tables, "Vouchers")],
        "payments": [dec(r.get("payment_amount")) for r in records(tables, "Payments")],
    }
    findings, results = [], {}
    for name, amounts in populations.items():
        digits = [d for d in (_first_digit(a) for a in amounts if a is not None)
                  if d is not None]
        if not amounts:
            continue
        n = len(digits)
        if n < minimum:
            results[name] = {"tested": False, "amounts": n, "minimum": int(minimum)}
            findings.append(receipt(
                pid, (name, "not_performed"), "AMBIGUOUS",
                f"{name}: {n} amounts of 10 or more, fewer than the "
                f"{int(minimum)} set as the minimum; the first-digit test was not run",
                {"finding_class": "REFUSAL", "cycle": "forensic", "population": name,
                 "amounts": n, "minimum": int(minimum)}))
            continue
        counts = {d: digits.count(d) for d in range(1, 10)}
        mad = Decimal(str(round(sum(abs(counts[d] / n - _BENFORD[d])
                                    for d in range(1, 10)) / 9, 6)))
        band = next((label for limit, label in _MAD_BANDS if mad <= limit),
                    "nonconformity")
        excess = []
        for d in range(1, 10):
            p = _BENFORD[d]
            z = (abs(counts[d] / n - p) - 1 / (2 * n)) / math.sqrt(p * (1 - p) / n)
            if counts[d] / n > p and z > 1.96:
                excess.append({"digit": d, "count": counts[d],
                               "expected": round(p * n, 1), "z": round(z, 2)})
        results[name] = {"tested": True, "amounts": n, "mad": str(mad),
                         "conformity": band, "counts": counts,
                         "digits_in_excess": excess}
        if band in ("nonconformity", "marginally acceptable conformity") or excess:
            findings.append(receipt(
                pid, (name, "first_digit"),
                "TENSION" if band == "nonconformity" else "AMBIGUOUS",
                f"{name}: first digits show {band} with Benford's law (MAD {mad}, "
                f"{n} amounts)"
                + (". More amounts than expected start with "
                   + ", ".join(f"{e['digit']} ({e['count']} against {e['expected']})"
                               for e in excess) if excess else "")
                + ". Look at the amounts behind the excess digits",
                {"finding_class": "CONJECTURE", "cycle": "forensic", "population": name,
                 **results[name]}))
    stats = {"population": sum(r["amounts"] for r in results.values()),
             "populations": results, "exceptions": len(findings)}
    return findings, stats
