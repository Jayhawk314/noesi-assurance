# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Revenue (sales and collection cycle): cutoff and occurrence leads.

Shipping dates and shipping document numbers come from the client's
shipping records; the engine compares them with invoice dates. A sale
recorded before its goods left is an overstatement at period end; one
shipped before period end but invoiced after is an understatement. Whether
title passed at shipment is a contract question the auditor answers.
"""

from __future__ import annotations

from datetime import timedelta

from procedures_cycles.common import (
    ZERO, dec, day, key_text, money, policy_date, receipt, records, source_ref, text,
)


def sales_cutoff(tables: dict, policies: dict):
    pid = "rev.sales_cutoff"
    pe = policy_date(policies, "period_end")
    findings = []
    over = under = ZERO
    unshipped = 0
    no_ship_date = 0
    invoices = records(tables, "Sales_invoices")
    for inv in invoices:
        number = key_text(inv.get("invoice_number"))
        amount = money(inv.get("amount"))
        invoiced, shipped = day(inv.get("invoice_date")), day(inv.get("ship_date"))
        base = {"cycle": "receivables", "amount": amount, "invoice_date": invoiced,
                "ship_date": shipped, "customer": text(inv.get("customer")),
                "source_rows": [source_ref("Sales_invoices", inv, "invoice_number")]}
        if invoiced is None:
            findings.append(receipt(pid, (number, "no_invoice_date"), "AMBIGUOUS",
                                    f"invoice {number}: no invoice date; cutoff untestable",
                                    {**base, "finding_class": "REFUSAL"}))
            continue
        if shipped is None:
            no_ship_date += 1
            if invoiced <= pe and not text(inv.get("shipping_document")):
                unshipped += 1
                findings.append(receipt(
                    pid, (number, "no_shipping_evidence"), "TENSION",
                    f"invoice {number} ({amount}, {invoiced}): no shipping date or "
                    "document — did the sale occur? Vouch to shipping records",
                    {**base, "finding_class": "CONJECTURE", "assertion": "occurrence"},
                    amount))
            continue
        if invoiced <= pe < shipped:
            over += amount
            findings.append(receipt(
                pid, (number, "invoiced_before_shipment"), "CLASH",
                f"invoice {number}: invoiced {invoiced}, in the period, but shipped "
                f"{shipped}, after period end — revenue and receivables overstated by "
                f"{amount} unless title passed earlier",
                {**base, "finding_class": "PROVED_EXCEPTION", "assertion": "cutoff",
                 "direction": "overstatement"}, amount))
        elif shipped <= pe < invoiced:
            under += amount
            findings.append(receipt(
                pid, (number, "shipped_before_invoicing"), "CLASH",
                f"invoice {number}: shipped {shipped}, in the period, but invoiced "
                f"{invoiced}, after period end — revenue and receivables understated "
                f"by {amount}",
                {**base, "finding_class": "PROVED_EXCEPTION", "assertion": "cutoff",
                 "direction": "understatement"}, amount))
    stats = {"population": len(invoices), "period_end": pe,
             "overstated_cutoff": over, "understated_cutoff": under,
             "invoices_without_shipping_evidence": unshipped,
             "invoices_without_ship_date": no_ship_date,
             "exceptions": len(findings)}
    return findings, stats


def credit_memos_after_period_end(tables: dict, policies: dict):
    pid = "rev.credit_memos_after_period_end"
    pe = policy_date(policies, "period_end")
    window = dec(policies.get("rev_credit_memo_days"))
    end = pe + timedelta(days=int(window)) if window is not None else None
    invoices = {key_text(i.get("invoice_number")): i
                for i in records(tables, "Sales_invoices")}
    memos = records(tables, "Credit_memos")
    findings = []
    reversed_total = ZERO
    considered = 0
    for memo in memos:
        number = key_text(memo.get("memo_number"))
        dated = day(memo.get("memo_date"))
        amount = money(memo.get("amount")).copy_abs()
        base = {"cycle": "receivables", "amount": amount, "memo_date": dated,
                "source_rows": [source_ref("Credit_memos", memo, "memo_number")]}
        if dated is None or dated <= pe or (end is not None and dated > end):
            continue
        considered += 1
        ref = key_text(memo.get("invoice_number"))
        invoice = invoices.get(ref) if ref else None
        if invoice is None:
            findings.append(receipt(
                pid, (number, "no_matching_invoice"), "ORPHAN",
                f"credit memo {number} ({amount}, {dated}) names "
                f"{('invoice ' + ref) if ref else 'no invoice'}, which is not in the "
                "sales listing — what did it reverse?",
                {**base, "finding_class": "EXPECTED_BUT_MISSING", "invoice": ref},
                amount))
            continue
        invoiced = day(invoice.get("invoice_date"))
        if invoiced is not None and invoiced <= pe:
            reversed_total += amount
            findings.append(receipt(
                pid, (number, "reverses_period_sale"), "TENSION",
                f"credit memo {number}, dated {dated} after period end, reverses "
                f"{amount} of invoice {ref} dated {invoiced} — was the sale real, or "
                "a return that belongs in the period (a returns allowance)?",
                {**base, "finding_class": "CONJECTURE", "assertion": "occurrence",
                 "invoice": ref, "invoice_date": invoiced}, amount))
    stats = {"population": len(memos), "after_period_end": considered,
             "window_days": int(window) if window is not None else None,
             "reversing_period_sales": reversed_total,
             "exceptions": len(findings)}
    return findings, stats
