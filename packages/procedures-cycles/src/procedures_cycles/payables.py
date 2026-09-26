# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""ap.unrecorded_liabilities_search — search for unrecorded liabilities.

Inputs:
- Vouchers: the year-end accounts payable listing (what the client says it owed);
- Payments: disbursements made after year-end (the subsequent check register);
- Disbursement_inspection (auditor evidence): for each inspected payment
  line, the date the liability arose per the receiving report or service
  invoice, and the amount owed at that date.

The engine:
1. selects disbursements — every check whose total exceeds the approved
   threshold, plus a systematic selection (every k-th remaining check from
   a start) when those policies are set — so the selection is reproducible;
2. for each inspected line decides where it belongs: a liability that arose
   on or before period end must be on the listing at the right amount; one
   that arose after must not be;
3. reports selected disbursements not yet inspected, and payments whose
   amount differs from the listed voucher, as open leads.

An inspection row may carry, instead of a date, a recorded conclusion of
"no misstatement" from the team member who did the work; it counts as
inspected (concluded_by_reference) and is not re-evaluated.

It cannot see liabilities that were never paid after year-end; the
contract's limitations say so.
"""

from __future__ import annotations

from decimal import Decimal

from procedures_cycles import sampling
from procedures_cycles.common import (
    ZERO, dec, day, key_text, money, policy_date, policy_decimal, receipt, records,
    source_ref, text,
)


NO_MISSTATEMENT = {"no misstatement", "no exception", "no exceptions", "properly included",
                   "properly excluded", "ok"}


def _check_of(payment: dict) -> str:
    check = text(payment.get("check_number"))
    return check or text(payment.get("payment_number"))


def select_disbursements(payments: list[dict], threshold: Decimal,
                         interval: int | None, start: int | None,
                         limit: int | None = None) -> dict:
    """Check-level selection: all above threshold, then every k-th of the rest."""
    checks: dict[str, Decimal] = {}
    order: list[str] = []
    for p in payments:
        check = _check_of(p)
        if check not in checks:
            checks[check] = ZERO
            order.append(check)
        checks[check] += money(p.get("payment_amount"))
    above = [c for c in order if checks[c] > threshold]
    rest = [c for c in order if checks[c] <= threshold]
    systematic: list[str] = []
    if interval and start and rest:
        positions = sampling.systematic_selection(len(rest), interval, start, limit=limit)
        systematic = [rest[i - 1] for i in positions]
    return {"check_totals": checks, "above_threshold": above,
            "systematic": systematic, "remaining_population": len(rest)}


def unrecorded_liabilities_search(tables: dict, policies: dict):
    pid = "ap.unrecorded_liabilities_search"
    period_end = policy_date(policies, "period_end")
    threshold = policy_decimal(policies, "search_threshold")
    interval = dec(policies.get("search_interval"))
    start = dec(policies.get("search_start"))
    limit = dec(policies.get("search_systematic_count"))
    listing = {key_text(v.get("voucher_number")): v for v in records(tables, "Vouchers")}
    payments = records(tables, "Payments")
    inspections = {key_text(i.get("payment_number")): i
                   for i in records(tables, "Disbursement_inspection")}
    selection = select_disbursements(payments, threshold,
                                     int(interval) if interval else None,
                                     int(start) if start else None,
                                     int(limit) if limit else None)
    selected = set(selection["above_threshold"]) | set(selection["systematic"])
    findings = []
    outcomes = {"properly_included": 0, "properly_excluded": 0, "unrecorded": 0,
                "improperly_included": 0, "amount_difference": 0,
                "concluded_by_reference": 0}
    inspected_checks: set[str] = set()
    net = ZERO  # overstatement positive
    for p in payments:
        pnum = key_text(p.get("payment_number"))
        vnum = key_text(p.get("voucher_number"))
        paid = money(p.get("payment_amount"))
        listed = listing.get(vnum)
        inspection = inspections.get(pnum)
        ref = [source_ref("Payments", p, "payment_number")]
        if inspection is None:
            if listed is not None and money(listed.get("voucher_amount")) != paid:
                diff = money(listed.get("voucher_amount")) - paid
                findings.append(receipt(
                    pid, (pnum, "paid_differs_from_listed"), "TENSION",
                    f"payment {pnum} pays voucher {vnum} {paid}; the year-end listing "
                    f"carries {money(listed.get('voucher_amount'))}",
                    {"finding_class": "CONJECTURE", "cycle": "payables",
                     "difference": diff, "source_rows": ref,
                     "limits": "a discount, partial payment or listing error; inspect"},
                    diff))
            continue
        inspected_checks.add(_check_of(p))
        arose = day(inspection.get("liability_date"))
        owed = dec(inspection.get("liability_amount"))
        owed = paid if owed is None else owed
        if arose is None:
            conclusion = text(inspection.get("conclusion")).lower()
            if conclusion.replace("_", " ") in NO_MISSTATEMENT:
                # Inspected and concluded by a team member whose workpaper
                # records the result but not the date: relied on, not re-derived.
                outcomes["concluded_by_reference"] += 1
                continue
            findings.append(receipt(pid, (pnum, "no_liability_date"), "AMBIGUOUS",
                                    f"payment {pnum}: inspection records neither the date "
                                    "the liability arose nor a no-misstatement conclusion",
                                    {"finding_class": "REFUSAL", "cycle": "payables"}))
            continue
        evidence = {"cycle": "payables", "voucher_number": vnum, "paid": paid,
                    "liability_date": arose, "liability_amount": owed,
                    "document": text(inspection.get("document")),
                    "period_end": period_end, "source_rows": ref}
        if arose <= period_end:
            if listed is None:
                outcomes["unrecorded"] += 1
                net -= owed
                findings.append(receipt(
                    pid, (pnum, "unrecorded"), "CLASH",
                    f"payment {pnum}: liability of {owed} arose {arose}, on or before "
                    f"period end, but voucher {vnum or '—'} is not on the year-end listing "
                    "— accounts payable understated",
                    {**evidence, "finding_class": "PROVED_EXCEPTION",
                     "direction": "understatement"}, owed))
            else:
                listed_amount = money(listed.get("voucher_amount"))
                if listed_amount != owed:
                    outcomes["amount_difference"] += 1
                    diff = listed_amount - owed
                    net += diff
                    findings.append(receipt(
                        pid, (pnum, "listed_amount_differs"), "CLASH",
                        f"payment {pnum}: voucher {vnum} listed at {listed_amount}, amount "
                        f"owed at period end {owed}",
                        {**evidence, "finding_class": "PROVED_EXCEPTION",
                         "listed_amount": listed_amount, "difference": diff}, diff))
                else:
                    outcomes["properly_included"] += 1
        else:
            if listed is not None:
                outcomes["improperly_included"] += 1
                listed_amount = money(listed.get("voucher_amount"))
                net += listed_amount
                findings.append(receipt(
                    pid, (pnum, "improperly_included"), "CLASH",
                    f"payment {pnum}: the liability arose {arose}, after period end, yet "
                    f"voucher {vnum} is on the year-end listing — accounts payable "
                    "overstated",
                    {**evidence, "finding_class": "PROVED_EXCEPTION",
                     "direction": "overstatement"}, listed_amount))
            else:
                outcomes["properly_excluded"] += 1
    for check in sorted(selected - inspected_checks):
        findings.append(receipt(
            pid, (check, "selected_not_inspected"), "TENSION",
            f"disbursement {check} ({selection['check_totals'][check]}) was selected for "
            "the search but no inspection result is recorded",
            {"finding_class": "CONJECTURE", "cycle": "payables",
             "limits": "the search is incomplete until every selected item is inspected"}))
    stats = {"population": len(payments), "checks": len(selection["check_totals"]),
             "selected_above_threshold": selection["above_threshold"],
             "selected_systematic": selection["systematic"],
             "inspected_checks": sorted(inspected_checks),
             "outcomes": outcomes, "net_misstatement": net,
             "listed_vouchers": len(listing),
             "exceptions": len(findings)}
    return findings, stats
