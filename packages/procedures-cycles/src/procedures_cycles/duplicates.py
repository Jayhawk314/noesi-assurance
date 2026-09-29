# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Duplicate bills: the same vendor invoice recorded more than once.

A bill entered twice is usually paid twice, and often under a second vendor
record (a look-alike that the vendor-twins procedure flags on its own). The
invoice number is compared by its letters and digits only, since the same
invoice is keyed "MC-24017", "MC 24017" or "mc24017". Whether a pair is a
real duplicate, and whether it was paid twice, is the auditor's to confirm
against the vendor's statement.
"""

from __future__ import annotations

import re

from procedures_cycles.common import money, receipt, records, source_ref, text

ROLE = "Vouchers"


def _invoice_key(value) -> str:
    return re.sub(r"[^a-z0-9]", "", text(value).lower())


def duplicate_bills(tables: dict, policies: dict):
    pid = "ap.duplicate_bills"
    groups: dict[str, list[dict]] = {}
    for bill in records(tables, ROLE):
        key = _invoice_key(bill.get("invoice_number"))
        if key:
            groups.setdefault(key, []).append(bill)
    findings, duplicated = [], 0
    for key, bills in sorted(groups.items()):
        if len(bills) < 2:
            continue
        vendors = sorted({text(b.get("vendor_number")) for b in bills})
        amounts = sorted({money(b.get("voucher_amount")) for b in bills})
        shown = ", ".join(f"{text(b.get('vendor_number'))} {money(b.get('voucher_amount'))}"
                          f" on {text(b.get('voucher_date')) or 'no date'}" for b in bills)
        evidence = {"finding_class": "PROVED_EXCEPTION" if len(amounts) == 1
                    else "CONJECTURE", "cycle": "payables", "invoice": key,
                    "vendors": vendors, "amounts": amounts,
                    "source_rows": [source_ref(ROLE, b, "voucher_number") for b in bills]}
        if len(amounts) == 1:
            extra = money(amounts[0]) * (len(bills) - 1)
            duplicated += 1
            findings.append(receipt(
                pid, (key, "same_invoice_same_amount"), "CLASH",
                f"invoice {text(bills[0].get('invoice_number'))} is recorded "
                f"{len(bills)} times for the same amount ({shown})"
                + (" under different vendor records" if len(vendors) > 1 else "")
                + f" — {extra} likely recorded twice; confirm with the vendor and "
                  "check whether it was paid twice", evidence, extra))
        else:
            findings.append(receipt(
                pid, (key, "same_invoice_different_amounts"), "TENSION",
                f"invoice {text(bills[0].get('invoice_number'))} appears {len(bills)} "
                f"times with different amounts ({shown}) — a correction, a partial "
                "bill, or a duplicate?", evidence))
    stats = {"population": len(records(tables, ROLE)),
             "invoice_numbers": len(groups), "likely_duplicates": duplicated,
             "exceptions": len(findings)}
    return findings, stats


def _vendor_key(value) -> str:
    return " ".join(text(value).lower().split())


def payments_without_bills(tables: dict, policies: dict):
    """Vendors paid directly who never sent a bill in the period."""
    pid = "ap.payments_without_bills"
    billed = {_vendor_key(b.get("vendor_number")) for b in records(tables, ROLE)}
    paid: dict[str, list[dict]] = {}
    payments = records(tables, "Direct_payments")
    for p in payments:
        vendor = _vendor_key(p.get("vendor_number"))
        if vendor:
            paid.setdefault(vendor, []).append(p)
    findings = []
    for vendor, rows in sorted(paid.items()):
        if vendor in billed:
            continue
        total = sum((money(p.get("payment_amount")) for p in rows), money(0))
        name = text(rows[0].get("vendor_number"))
        findings.append(receipt(
            pid, (vendor, "paid_without_bills"), "TENSION",
            f"{name} was paid {total} in {len(rows)} direct payment(s) and sent no "
            "bill in the period — what was bought, who approved it, and is the vendor "
            "real?",
            {"finding_class": "CONJECTURE", "cycle": "payables", "vendor": name,
             "total": total, "payments": len(rows),
             "source_rows": [source_ref("Direct_payments", p, "payment_number")
                             for p in rows],
             "limits": "rent, loans and utilities are often paid without a bill"},
            total))
    return findings, {"population": len(payments), "vendors_paid": len(paid),
                      "vendors_without_bills": len(findings),
                      "exceptions": len(findings)}
