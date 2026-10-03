# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Accounting estimates (retrospective review) and related parties (matching).

A retrospective review (AU-C 540) compares last year's estimates with how
they turned out. A miss is not an error in last year's statements; misses
that all lean one way are an indicator of management bias, which is the
point of the review.

Related-party matching checks management's list against the counterparties
in the engagement's data. A match is a lead for disclosure, approval and
terms; a related party absent from the list is what the matching cannot see
(it finds only names, addresses and accounts that coincide).
"""

from __future__ import annotations

import re
from decimal import Decimal

from procedures_cycles.common import (
    ZERO, PolicyError, dec, key_text, money, receipt, records, source_ref, text,
)

ESTIMATES, PARTIES = "Estimates", "Related_parties"
_SUFFIXES = {"inc", "incorporated", "llc", "l l c", "co", "company", "corp",
             "corporation", "ltd", "limited", "lp", "llp", "pc", "pllc", "the"}


def retrospective_review(tables: dict, policies: dict):
    pid = "estimates.retrospective_review"
    raw = dec(policies.get("estimates_hindsight_pct"))
    if raw is None:
        raise PolicyError("policy 'estimates_hindsight_pct' is not set; how far an "
                          "outcome may differ from the estimate is the auditor's call")
    threshold = raw / 100 if raw >= 1 else raw
    min_count = int(dec(policies.get("estimates_bias_min_count")) or 3)
    findings, directions = [], []
    rows = records(tables, ESTIMATES)
    for row in rows:
        name = text(row.get("estimate")) or f"row-{row.get('source_row')}"
        key = key_text(name)
        prior, outcome = dec(row.get("prior_estimate")), dec(row.get("outcome"))
        src = [source_ref(ESTIMATES, row, "estimate")]
        if prior is None or outcome is None:
            findings.append(receipt(pid, (key, "not_resolved"), "AMBIGUOUS",
                                    f"{name}: no prior estimate or outcome to compare",
                                    {"finding_class": "REFUSAL", "cycle": "estimates",
                                     "source_rows": src}))
            continue
        miss = money(outcome - prior)
        if miss != 0:
            directions.append((name, 1 if miss > 0 else -1))
        share = abs(miss) / abs(prior) if prior else None
        if share is None and miss != 0 or share is not None and share > threshold:
            findings.append(receipt(
                pid, (key, "outcome_differs"), "TENSION",
                f"{name}: estimated {money(prior)}, turned out {money(outcome)} "
                f"(off by {miss}"
                + (f", {share * 100:.1f}%" if share is not None else "")
                + f") — beyond {threshold * 100:.1f}%. Does this year's method "
                  "reflect what was learned?",
                {"finding_class": "CONJECTURE", "cycle": "estimates",
                 "prior": prior, "outcome": outcome, "miss": miss, "source_rows": src},
                miss))
    signs = {d for _, d in directions}
    if len(directions) >= min_count and len(signs) == 1:
        way = "above" if signs == {1} else "below"
        findings.append(receipt(
            pid, ("all_estimates", "one_direction"), "TENSION",
            f"all {len(directions)} estimates that missed came out {way} what was "
            "estimated — an indicator of management bias (AU-C 540); consider it with "
            "this year's estimates",
            {"finding_class": "CONJECTURE", "cycle": "estimates",
             "estimates": [n for n, _ in directions], "direction": way}))
    stats = {"population": len(rows), "hindsight_threshold": threshold,
             "bias_min_count": min_count, "misses": len(directions),
             "exceptions": len(findings)}
    return findings, stats


def _name(value) -> str:
    words = re.sub(r"[^a-z0-9 ]", " ", text(value).lower().replace("&", " and ")).split()
    return " ".join(w for w in words if w not in _SUFFIXES)


def _norm(value) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", text(value).lower()).split())


def related_party_matching(tables: dict, policies: dict):
    pid = "related_parties.matching"
    parties = records(tables, PARTIES)
    # (role, name field, id field, amount source) for each counterparty list present
    payments: dict[str, Decimal] = {}
    for p in records(tables, "Payments"):
        vid = key_text(p.get("vendor_number"))
        payments[vid] = payments.get(vid, ZERO) + money(p.get("payment_amount"))
    sales: dict[str, Decimal] = {}
    for s in records(tables, "Sales_invoices"):
        sales[_name(s.get("customer"))] = sales.get(_name(s.get("customer")), ZERO) + \
            money(s.get("amount"))
    counterparties = []
    for v in records(tables, "Vendors"):
        vid = key_text(v.get("vendor_number"))
        counterparties.append(("vendor", text(v.get("vendor_name")) or vid, vid,
                               payments.get(vid), "paid", v, "Vendors", "vendor_number"))
    for c in records(tables, "AR_listing"):
        cname = text(c.get("customer_name")) or text(c.get("customer_number"))
        counterparties.append(("customer", cname, key_text(c.get("customer_number")),
                               money(c.get("balance")), "owing at period end", c,
                               "AR_listing", "customer_number"))
    known = {_name(c[1]) for c in counterparties if c[0] == "customer"}
    for name, total in sorted(sales.items()):
        if name and name not in known:
            counterparties.append(("customer", name, name, total, "invoiced", {},
                                   "Sales_invoices", "customer"))
    employees = records(tables, "Payroll_master")
    findings = []
    if not counterparties and not employees:
        findings.append(receipt(
            pid, ("no_counterparties",), "AMBIGUOUS",
            "there are no vendors, customers, sales or employees loaded to match the "
            "related-party list against", {"finding_class": "REFUSAL",
                                           "cycle": "estimates"}))
    matched = 0
    for party in parties:
        pname = text(party.get("party_name"))
        pkey = _name(pname)
        src = [source_ref(PARTIES, party, "party_name")]
        relationship = text(party.get("relationship"))
        hits = [c for c in counterparties if pkey and _name(c[1]) == pkey]
        for kind, cname, cid, amount, verb, record, role, id_field in hits:
            matched += 1
            findings.append(receipt(
                pid, (key_text(pname), kind, cid), "TENSION",
                f"related party {pname}"
                + (f" ({relationship})" if relationship else "")
                + f" is a {kind} ({cname})"
                + (f": {amount} {verb}" if amount is not None else "")
                + " — confirm the transactions are approved, on stated terms and "
                  "disclosed",
                {"finding_class": "CONJECTURE", "cycle": "estimates", "counterparty":
                 cname, "role": role, "amount": amount,
                 "source_rows": src + ([source_ref(role, record, id_field)]
                                       if record else [])}, amount))
        for field in ("address", "bank_account"):
            value = _norm(party.get(field))
            if not value:
                continue
            for emp in employees:
                if _norm(emp.get(field)) == value:
                    matched += 1
                    eid = key_text(emp.get("employee_id"))
                    findings.append(receipt(
                        pid, (key_text(pname), f"employee_{field}", eid), "TENSION",
                        f"related party {pname} shares "
                        f"{'an' if field[0] in 'aeiou' else 'a'} {field.replace('_', ' ')} with "
                        f"employee {eid} — a family member on the payroll? Confirm the "
                        "role and pay are real and disclosed",
                        {"finding_class": "CONJECTURE", "cycle": "estimates",
                         "employee": eid, "source_rows": src + [
                             source_ref("Payroll_master", emp, "employee_id")]}))
    stats = {"population": len(parties), "counterparties": len(counterparties),
             "employees": len(employees), "matches": matched,
             "exceptions": len(findings)}
    return findings, stats
