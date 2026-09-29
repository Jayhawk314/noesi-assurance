# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Accruals and prepaids: schedule rollforward to the ledger, and a time-
proportion recompute of each item with a contract amount and service period.

The schedule is the client's. Time proportion (days) is the recompute used
for prepaid insurance, rent, subscriptions and accrued service contracts;
items that are measured another way (usage, estimates) are listed as not
recomputed rather than forced into it. The search for accruals that were
never recorded is the payables cycle's unrecorded-liabilities search.
"""

from __future__ import annotations

from decimal import Decimal

from procedures_cycles.common import (
    ZERO, dec, day, key_text, money, policy_date, receipt, records, source_ref, text,
)
from procedures_cycles.statements import _signed

SCHEDULE = "Accrual_schedule"


def _kind(row: dict) -> str | None:
    kind = text(row.get("kind")).lower()
    if kind.startswith("prepaid") or kind in ("prepayment", "deferred expense"):
        return "prepaid"
    if kind.startswith("accru") or kind in ("accrued liability", "accrued expense"):
        return "accrual"
    return None


def rollforward(tables: dict, policies: dict):
    pid = "accruals.rollforward"
    rows = records(tables, SCHEDULE)
    tb = {key_text(r.get("account")): r for r in records(tables, "Trial_balance")}
    findings = []
    by_account: dict[str, dict] = {}
    for row in rows:
        item = key_text(row.get("item"))
        src = [source_ref(SCHEDULE, row, "item")]
        kind = _kind(row)
        if kind is None:
            findings.append(receipt(
                pid, (item, "kind_unknown"), "AMBIGUOUS",
                f"{item}: kind {text(row.get('kind'))!r} is neither prepaid nor accrual",
                {"finding_class": "REFUSAL", "cycle": "accruals", "source_rows": src}))
            continue
        begin, end = money(row.get("beginning")), money(row.get("ending"))
        adds, less = money(row.get("additions")), money(row.get("reductions"))
        if begin + adds - less != end:
            findings.append(receipt(
                pid, (item, "does_not_foot"), "CLASH",
                f"{item}: {begin} + {adds} - {less} = {begin + adds - less}, but the "
                f"schedule shows {end}", {"finding_class": "PROVED_EXCEPTION",
                                          "cycle": "accruals", "source_rows": src},
                begin + adds - less - end))
        elif begin and not adds and not less:
            # A balance nobody touched all year is a question, not an error:
            # is it still owed (or still unexpired), and why no activity?
            findings.append(receipt(
                pid, (item, "unchanged"), "TENSION",
                f"{item}: {end} at both ends of the period with no additions or "
                "reductions — ask why, and whether it is still valid",
                {"finding_class": "CONJECTURE", "cycle": "accruals", "source_rows": src,
                 "limits": "no activity is a lead for inquiry, not a misstatement"}))
        account = key_text(row.get("account"))
        if account:
            group = by_account.setdefault(account, {"kind": kind, "begin": ZERO,
                                                    "end": ZERO})
            group["begin"] += begin
            group["end"] += end
    for account, group in sorted(by_account.items()):
        if not tb:
            break
        if account not in tb:
            findings.append(receipt(
                pid, (account, "account_not_on_trial_balance"), "AMBIGUOUS",
                f"account {account} on the schedule is not on the trial balance",
                {"finding_class": "REFUSAL", "cycle": "accruals"}))
            continue
        sign = 1 if group["kind"] == "prepaid" else -1     # accruals are credits
        for label, total, field in (("ending", group["end"], "balance"),
                                    ("beginning", group["begin"], "prior_balance")):
            value = _signed(tb[account], field)
            if value is None:
                continue
            ledger = money(value) * sign
            if ledger != total:
                findings.append(receipt(
                    pid, (account, f"{label}_to_ledger"), "CLASH",
                    f"account {account}: {label} {total} per the schedule, {ledger} per "
                    f"the trial balance (difference {total - ledger})",
                    {"finding_class": "PROVED_EXCEPTION", "cycle": "accruals",
                     "schedule": total, "ledger": ledger}, total - ledger))
    stats = {"population": len(rows), "accounts": sorted(by_account),
             "not_performed": ({} if tb else
                               {"ties_to_ledger": "no trial balance is loaded"}),
             "exceptions": len(findings)}
    return findings, stats


def recompute(tables: dict, policies: dict):
    pid = "accruals.recompute"
    pe = policy_date(policies, "period_end")
    tolerance = dec(policies.get("accruals_rounding_tolerance")) or Decimal("1.00")
    rows = records(tables, SCHEDULE)
    findings, not_recomputed = [], []
    for row in rows:
        item = key_text(row.get("item"))
        kind = _kind(row)
        total = dec(row.get("total_amount"))
        start, finish = day(row.get("service_start")), day(row.get("service_end"))
        if kind is None or total is None or start is None or finish is None \
                or finish < start:
            not_recomputed.append(item)
            continue
        days = (finish - start).days + 1
        elapsed = min(max((pe - start).days + 1, 0), days)
        if kind == "prepaid":
            expected = money(total * (days - elapsed) / days)
            basis = f"{days - elapsed} of {days} days unexpired at {pe}"
        else:
            billed = money(row.get("billed_to_date"))
            expected = money(total * elapsed / days) - billed
            basis = (f"{elapsed} of {days} days earned by {pe}"
                     + (f", less {billed} billed" if billed else ""))
        recorded = money(row.get("ending"))
        gap = recorded - expected
        if abs(gap) > tolerance:
            findings.append(receipt(
                pid, (item, "recompute_differs"), "CLASH",
                f"{item}: the schedule carries {recorded}; {total} over {basis} gives "
                f"{expected} (difference {gap})",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "accruals",
                 "kind": kind, "recorded": recorded, "recomputed": expected,
                 "source_rows": [source_ref(SCHEDULE, row, "item")]}, gap))
    stats = {"population": len(rows), "rounding_tolerance": tolerance,
             "not_recomputed": not_recomputed, "exceptions": len(findings)}
    return findings, stats
