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

    Disbursement checks (bill payments and checks with no bill) and payroll
    checks are separate runs, and each bank account is its own run: two
    accounts numbering 1001-1050 and 5001-5020 are two runs, not 3,950
    missing checks. A gap is a number never seen between the first and last
    check of a run: voided, issued outside the records loaded, or missing.
    A number reused for a different payee or date is a second check under
    one number. One check paying several bills appears on several rows with
    the same payee and date, and is not a reuse. Checks with no number are
    counted, not tested.
    """
    pid = "forensic.check_number_sequence"
    # The Journal holds every check that moved the books (its completeness is
    # proved by je.population_completeness); the payment records may hold
    # only bill payments. Each check is one transaction however many lines.
    journal = _journal_checks(records(tables, "Journal_entries"))
    numbered = {item[0] for item in journal if item[2] is not None}
    # item: (kind, account, number, role, row, payee, date, amount, key field)
    items: list[tuple] = []
    sources = {}
    if "disbursements" in numbered:
        sources["disbursements"] = "Journal"
        items += [i for i in journal if i[0] == "disbursements"]
    else:
        sources["disbursements"] = "payment records"
        for role in ("Payments", "Direct_payments"):
            for row in records(tables, role):
                raw = row.get("check_number") if role == "Payments" else None
                if not text(raw):
                    raw = row.get("payment_number")
                items.append(("disbursements", key_text(row.get("bank_account")),
                              _check_number(raw), role, row,
                              key_text(row.get("vendor_number")),
                              day(row.get("payment_date")),
                              money(row.get("payment_amount")), "payment_number"))
    if "payroll" in numbered:
        sources["payroll"] = "Journal"
        items += [i for i in journal if i[0] == "payroll"]
    else:
        sources["payroll"] = "payroll register"
        for row in records(tables, "Payroll_register"):
            items.append(("payroll", key_text(row.get("bank_account")),
                          _check_number(row.get("check_number")), "Payroll_register",
                          row, key_text(row.get("employee_id")),
                          day(row.get("pay_date")), money(row.get("net")),
                          "employee_id"))

    runs: dict[tuple[str, str], list[tuple]] = {}
    for item in items:
        runs.setdefault((item[0], item[1]), []).append(item)
    accounts_of: dict[str, set[str]] = {}
    for kind, account in runs:
        accounts_of.setdefault(kind, set()).add(account)

    findings, stats = [], {"sequences": {}}
    for (kind, account), run in sorted(runs.items()):
        # One account (or none named): the run keeps its plain name.
        sequence = (f"{kind}, account {account or '(none named)'}"
                    if len(accounts_of[kind]) > 1 else kind)
        seen: dict[int, list[tuple]] = {}
        for item in run:
            if item[2] is not None:
                seen.setdefault(item[2], []).append(item)
        not_numbered = sum(1 for item in run if item[2] is None)
        if not seen:
            stats["sequences"][sequence] = {"rows": len(run), "numbered": 0,
                                            "not_numbered": not_numbered}
            continue
        numbers = sorted(seen)
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
                 "sequence": sequence, "account": account or None,
                 "first_missing": start, "last_missing": end, "count": count,
                 "source_rows": [source_ref(i[3], i[4], i[8])
                                 for i in seen[start - 1] + seen[end + 1]]}))
        reused = 0
        for number in numbers:
            uses = {(i[5], i[6]) for i in seen[number]}
            if len(uses) > 1:
                reused += 1
                findings.append(receipt(
                    pid, (sequence, str(number), "reused"), "CLASH",
                    f"{sequence} check {number} appears for "
                    + "; ".join(f"{p or '(no payee)'} on {w or '(no date)'}"
                                for p, w in sorted(uses, key=str))
                    + ": two checks under one number, or a record changed after it "
                      "was issued",
                    {"finding_class": "PROVED_EXCEPTION", "cycle": "forensic",
                     "sequence": sequence, "account": account or None,
                     "check": number, "uses": sorted([p, str(w)] for p, w in uses),
                     "source_rows": [source_ref(i[3], i[4], i[8])
                                     for i in seen[number]]},
                    sum((i[7] for i in seen[number]), Decimal("0"))))
        stats["sequences"][sequence] = {
            "rows": len(run), "numbered": len(run) - not_numbered,
            "not_numbered": not_numbered, "first": numbers[0], "last": numbers[-1],
            "distinct_checks": len(numbers),
            "missing_numbers": sum(e - s + 1 for s, e in missing),
            "gaps": len(missing), "reused_numbers": reused}
    stats["disbursements_from"] = sources["disbursements"]
    stats["payroll_from"] = sources["payroll"]
    stats["population"] = sum(s["rows"] for s in stats["sequences"].values())
    stats["exceptions"] = len(findings)
    return findings, stats


def _journal_checks(rows: list[dict]) -> list[tuple]:
    """Each check in the Journal once, as (kind, bank account, number, role,
    row, payee, date, amount, key field). The payee field is the entry id,
    which names the transaction.

    The bank account is the credited account that the most checks credit:
    every check credits its bank, while a negative line on one check (a
    vendor credit, a refund) credits an account few others touch, and can
    be larger than the bank credit (review 2026-10-02 fixes check, C1).
    Between accounts credited equally often, the larger credit wins."""
    entries: dict[str, list[dict]] = {}
    for row in rows:
        if _check_kind(row.get("source")):
            entries.setdefault(key_text(row.get("entry_id")), []).append(row)
    credited: dict[str, int] = {}
    for lines in entries.values():
        for account in {key_text(r.get("account")) for r in lines
                        if money(r.get("credit")) > 0}:
            credited[account] = credited.get(account, 0) + 1
    out = []
    for entry_id, lines in entries.items():
        credits: dict[str, tuple[Decimal, dict]] = {}
        for r in lines:
            if money(r.get("credit")) > 0:
                account = key_text(r.get("account"))
                total, first = credits.get(account, (Decimal("0"), r))
                credits[account] = (total + money(r.get("credit")), first)
        if credits:
            account = max(credits, key=lambda a: (credited[a], credits[a][0]))
            amount, bank = credits[account]
        else:
            amount, bank = Decimal("0"), lines[0]
        number = next((_check_number(r.get("document_number")) for r in lines
                       if text(r.get("document_number"))), None)
        out.append((_check_kind(lines[0].get("source")),
                    key_text(bank.get("account")) if credits else "",
                    number, "Journal_entries", bank, entry_id,
                    day(lines[0].get("entry_date")), amount, "entry_id"))
    return out


def _check_kind(source) -> str | None:
    """'disbursements' or 'payroll' for a transaction type naming a check
    ("Check", "Bill Payment (Check)", "Cheque", "Payroll Check", "Paycheck"),
    as accounting systems print them; None for anything else."""
    words = text(source).lower()
    if "check" not in words and "cheque" not in words:
        return None
    if "payroll" in words or "paycheck" in words or "pay check" in words:
        return "payroll"
    return "disbursements"


# --------------------------------------------------- vendors and employees

def _digits(value) -> str:
    return "".join(c for c in text(value) if c.isdigit())


def _masked(value) -> bool:
    """A number shown only in part (****4821, XXXX4821): its visible digits
    are shared by many accounts, so it is not compared (review L2)."""
    raw = text(value)
    return "*" in raw or "xxx" in raw.lower() or "•" in raw


def _phone(value) -> str:
    """The digits compared for a phone: the last seven, so 555-1234 and
    (415) 555-1234 meet; a number with no area code cannot be told apart
    from one in another area, so the match stays a lead (review L2)."""
    return _digits(value)[-7:]


def _employee_name(row: dict) -> str:
    """The full name, or first and last name joined when the master splits
    them (review L2: split names were skipped without saying so)."""
    return text(row.get("name")) or " ".join(
        p for p in (text(row.get("first_name")), text(row.get("last_name"))) if p)


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
    masked = 0
    for field, label, normalize, minimum in (
            ("bank_account", "bank account", _digits, 4),
            ("phone", "phone number", _phone, 7),
            ("tax_id", "tax ID", _digits, 9)):
        on_vendors = any(text(v.get(field)) for v in vendors)
        on_employees = any(text(e.get(field)) for e in employees)
        if not (on_vendors and on_employees):
            not_compared.append(field)
            continue
        compared.append(field)

        def usable(row):
            nonlocal masked
            if field != "phone" and _masked(row.get(field)):
                masked += 1
                return ""
            value = normalize(row.get(field))
            return value if len(value) >= minimum else ""
        by_value: dict[str, list[dict]] = {}
        for e in employees:
            value = usable(e)
            if value:
                by_value.setdefault(value, []).append(e)
        for v in vendors:
            value = usable(v)
            for e in by_value.get(value, []) if value else []:
                vendor = text(v.get("vendor_name")) or text(v.get("vendor_number"))
                emp = key_text(e.get("employee_id"))
                findings.append(receipt(
                    pid, (emp, key_text(vendor), f"shared_{field}"), "TENSION",
                    f"vendor {vendor} has the same {label} as employee {emp} "
                    f"({_employee_name(e)}). Does the employee own or control it? "
                    "Check what it was paid and whether it is a disclosed related party",
                    {"finding_class": "CONJECTURE", "cycle": "forensic",
                     "employee": emp, "vendor": vendor, "field": field,
                     "source_rows": [source_ref("Vendors", v, "vendor_number"),
                                     source_ref("Payroll_master", e, "employee_id")]}))
    names = [(e, _words(_employee_name(e))) for e in employees]
    unnamed = sum(1 for _, n in names if not n)
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
                        f"({_employee_name(e)}). The same person, a relative, or a "
                        "coincidence? Ask, and check what it was paid",
                        {"finding_class": "CONJECTURE", "cycle": "forensic",
                         "employee": emp, "vendor": vendor, "field": "name",
                         "source_rows": [source_ref("Vendors", v, "vendor_number"),
                                         source_ref("Payroll_master", e, "employee_id")]}))
    else:
        not_compared.append("name")
    stats = {"population": len(vendors), "employees": len(employees),
             "fields_compared": compared, "fields_not_compared": not_compared,
             # Said, not skipped in silence (review L2):
             "masked_numbers_not_compared": masked,
             "employees_without_a_name": unnamed,
             "exceptions": len(findings)}
    return findings, stats


# ------------------------------------------------- self-approved payments

def _person(value) -> str:
    return " ".join(text(value).lower().split())


def self_approved_payments(tables: dict, policies: dict):
    """Payments approved (or signed) by the person who prepared them, and
    payments with no approver recorded, from an approval or signature log.

    The log is separate evidence from the payment register: a bill-pay
    approval report, or the signers the auditor read off the bank's
    paid-check images. Names compare as written, ignoring case and spacing.
    """
    pid = "forensic.self_approved_payments"
    rows = records(tables, "Payment_approvals")
    findings = []
    by_person: dict[str, list[dict]] = {}
    no_approver = 0
    for row in rows:
        number = key_text(row.get("payment_number"))
        preparer, approver = _person(row.get("prepared_by")), _person(row.get("approved_by"))
        amount = money(row.get("payment_amount"))
        payee = text(row.get("payee")) or "(no payee)"
        if not approver:
            no_approver += 1
            findings.append(receipt(
                pid, (number, "no_approver"), "ORPHAN",
                f"payment {number} to {payee} ({amount}) has no approver or signer "
                "recorded. Who authorized it?",
                {"finding_class": "EXPECTED_BUT_MISSING", "cycle": "forensic",
                 "payment": number, "prepared_by": text(row.get("prepared_by")),
                 "source_rows": [source_ref("Payment_approvals", row, "payment_number")]},
                amount))
        elif preparer and preparer == approver:
            by_person.setdefault(preparer, []).append(row)
            findings.append(receipt(
                pid, (number, "self_approved"), "CLASH",
                f"payment {number} to {payee} ({amount}) was prepared and approved by "
                f"the same person, {text(row.get('approved_by'))}. One person both "
                "raising and authorizing a payment is the opening for a false one: "
                "inspect its support and what it paid for",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "forensic",
                 "payment": number, "person": text(row.get("approved_by")),
                 "payee": payee, "date": str(day(row.get("payment_date")) or ""),
                 "source_rows": [source_ref("Payment_approvals", row, "payment_number")]},
                amount))
    stats = {"population": len(rows), "self_approved": sum(len(v) for v in by_person.values()),
             "no_approver": no_approver,
             "self_approved_by": {p: len(v) for p, v in sorted(by_person.items())},
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


def _debit_side(row: dict) -> Decimal | None:
    """A journal line's amount counted once: its debit, or a positive signed
    amount. Every entry balances, so counting credits too would put each
    amount in the test twice and double the apparent evidence."""
    debit = dec(row.get("debit"))
    if debit is not None and debit > 0:
        return debit
    amount = dec(row.get("amount"))
    if debit is None and amount is not None and amount > 0:
        return amount
    return None


def benford_first_digit(tables: dict, policies: dict):
    """First-digit test on each population of amounts loaded: journal debit
    lines, bills, and payments, each tested apart.

    A population smaller than ``benford_min_population`` (the auditor's
    choice) is not tested, and said so. Conformity is judged by the mean
    absolute deviation against Nigrini's published bands, and only
    marginal conformity or nonconformity is a finding. The per-digit z-test
    is not used to raise findings: with nine digits tested at once, about one
    population in five that conforms well would show some digit "in excess"
    by chance, and with large populations the z-test flags trivial
    differences (Nigrini, 2012). The digits in excess are named, so the
    auditor knows which amounts to look at. Nonconformity says where amounts
    are not what natural processes produce (invented figures, amounts kept
    under a limit); it proves nothing alone.
    """
    pid = "forensic.benford_first_digit"
    minimum = dec(policies.get("benford_min_population"))
    if minimum is None:
        raise PolicyError("policy 'benford_min_population' is not set; it is the "
                          "auditor's decision")
    populations = {
        "journal lines": [_debit_side(r) for r in records(tables, "Journal_entries")],
        "bills": [dec(r.get("voucher_amount")) for r in records(tables, "Vouchers")],
        "payments": [dec(r.get("payment_amount")) for r in records(tables, "Payments")],
    }
    findings, results = [], {}
    for name, amounts in populations.items():
        if not amounts:
            continue
        digits = [d for d in (_first_digit(a) for a in amounts if a is not None)
                  if d is not None]
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
        if band in ("nonconformity", "marginally acceptable conformity"):
            findings.append(receipt(
                pid, (name, "first_digit"),
                "TENSION" if band == "nonconformity" else "AMBIGUOUS",
                f"{name}: first digits show {band} with Benford's law (MAD {mad}, "
                f"{n} amounts)"
                + (". More amounts than expected start with "
                   + ", ".join(f"{e['digit']} ({e['count']} against {e['expected']})"
                               for e in excess) if excess else "")
                + ". A lead, not evidence of error: many honest populations do not "
                  "follow Benford's law (fixed fees, prices, recurring amounts, "
                  "amounts under a ceiling). Look at the amounts behind the excess "
                  "digits and ask what produced them",
                {"finding_class": "CONJECTURE", "cycle": "forensic", "population": name,
                 **results[name]}))
    # The population is what was tested: a population below the minimum was
    # read but not tested, and is counted apart so "N items" never reads as
    # N amounts tested (fixes check C2).
    stats = {"population": sum(r["amounts"] for r in results.values() if r["tested"]),
             "amounts_not_tested": sum(r["amounts"] for r in results.values()
                                       if not r["tested"]),
             "populations": results, "exceptions": len(findings)}
    return findings, stats
