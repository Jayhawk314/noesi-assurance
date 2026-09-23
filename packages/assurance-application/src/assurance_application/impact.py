# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Revised-evidence impact: what a newer client file touches downstream.

Real engagements receive corrected files mid-audit. The workbench already
serves the newest dataset per role and freezes every run's input digests, so
the question "which of my runs, findings, judgments and SAD lines rested on
the old file?" is answerable from the record — nothing here is inferred.

This module is pure: it compares records and finding sets handed to it and
returns plain dicts. The service gathers the inputs (digest-verified) and
re-executes stale procedures in memory only; an impact report never writes
a run, a disposition, or a journal entry. Acting on it is the auditor's
separate, journaled decision.

Ported in spirit from the portfolio's economic-decision-memory (dependency
traversal with explicit standing) and economic-revision-monitor (vintage diff
with materiality policy), re-keyed to audit objects: file version -> run ->
finding -> disposition -> SAD / sign-off.
"""

from __future__ import annotations

from decimal import Decimal

from assurance_domain.money import fnum, parse_amount
from assurance_domain.sad import PERFORMANCE_PCT, TRIVIAL_PCT

# Fields that carry money in a normalized record, by precedence.
_AMOUNT_FIELDS = ("voucher_amount", "payment_amount", "po_amount", "amount",
                  "received_amount", "subledger_balance", "gl_balance")

# How rows of each canonical role are matched across file versions.
KEY_FIELDS: dict[str, tuple[str, ...]] = {
    "Vendors": ("vendor_number",),
    "Employees": ("employee_number",),
    "Purchase_orders": ("po_number",),
    "Goods_receipts": ("receipt_number",),
    "Vouchers": ("voucher_number",),
    "Payments": ("payment_number",),
    "Bank": ("bank_txn_id",),
    "GL": ("gl_entry_id",),
    "AP_control_balance": ("period_end",),
    "Value_flows": ("source_entity", "target_entity"),
}

_SIGNIFICANCE_ORDER =("none", "below_trivial", "above_trivial",
                       "above_performance")


def thresholds(materiality) -> dict:
    """Clearly-trivial and performance materiality derived like the SAD."""
    overall = parse_amount(materiality) or Decimal("0")
    return {"materiality": overall,
            "clearly_trivial": TRIVIAL_PCT * overall,
            "performance": PERFORMANCE_PCT * overall}


def significance(amount, limits: dict) -> str:
    """Place an absolute dollar change against the engagement's thresholds.

    With no materiality set, any nonzero change is reported as
    ``above_trivial`` rather than silently called immaterial.
    """
    magnitude = abs(parse_amount(amount) or Decimal("0"))
    if magnitude == 0:
        return "none"
    if not limits["materiality"]:
        return "above_trivial"
    if magnitude > limits["performance"]:
        return "above_performance"
    if magnitude > limits["clearly_trivial"]:
        return "above_trivial"
    return "below_trivial"


def _worst(levels) -> str:
    return max(levels, key=_SIGNIFICANCE_ORDER.index, default="none")


def _record_amount(record: dict):
    for field in _AMOUNT_FIELDS:
        if record.get(field) is not None:
            return parse_amount(record[field])
    return None


def _key(record: dict, key_fields: tuple[str, ...]) -> str:
    return "|".join(str(record.get(field, "")) for field in key_fields)


def diff_records(old: list[dict], new: list[dict],
                 key_fields: tuple[str, ...], limits: dict) -> dict:
    """Row-level difference between two versions of one client file.

    Rows are matched on the role's key fields. Duplicate keys are reported
    rather than silently collapsed, because a duplicated voucher number is
    itself an audit fact.
    """
    def index(rows):
        out: dict[str, dict] = {}
        dupes: list[str] = []
        for row in rows:
            key = _key(row, key_fields)
            if key in out:
                dupes.append(key)
            out[key] = row
        return out, dupes

    before, dupes_before = index(old)
    after, dupes_after = index(new)
    added, removed, changed = [], [], []
    for key in sorted(after.keys() - before.keys()):
        amount = _record_amount(after[key])
        added.append({"key": key, "amount": fnum(amount) if amount is not None
                      else None,
                      "significance": significance(amount or 0, limits)})
    for key in sorted(before.keys() - after.keys()):
        amount = _record_amount(before[key])
        removed.append({"key": key, "amount": fnum(amount)
                        if amount is not None else None,
                        "significance": significance(amount or 0, limits)})
    for key in sorted(before.keys() & after.keys()):
        old_row, new_row = before[key], after[key]
        fields = sorted(field for field in set(old_row) | set(new_row)
                        if old_row.get(field) != new_row.get(field))
        if not fields:
            continue
        old_amount, new_amount = _record_amount(old_row), _record_amount(new_row)
        delta = ((new_amount or Decimal("0")) - (old_amount or Decimal("0"))
                 if old_amount is not None or new_amount is not None
                 else Decimal("0"))
        changed.append({
            "key": key,
            "fields": [{"field": field, "before": old_row.get(field),
                        "after": new_row.get(field)} for field in fields],
            "amount_change": fnum(delta),
            "significance": significance(delta, limits),
        })
    net = sum((parse_amount(item["amount"]) or Decimal("0") for item in added),
              Decimal("0")) - sum(
        (parse_amount(item["amount"]) or Decimal("0") for item in removed),
        Decimal("0")) + sum(
        (parse_amount(item["amount_change"]) or Decimal("0")
         for item in changed), Decimal("0"))
    return {
        "key_fields": list(key_fields),
        "rows_before": len(old), "rows_after": len(new),
        "added": added, "removed": removed, "changed": changed,
        "duplicate_keys": sorted(set(dupes_before) | set(dupes_after)),
        "net_amount_change": fnum(net),
        "significance": _worst([item["significance"]
                                for item in added + removed + changed]),
    }


def _score(verdict: dict):
    score = verdict.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return None
    return parse_amount(score)


def compare_findings(old: dict[str, dict], new: dict[str, dict],
                     dispositions: dict[str, dict], limits: dict) -> list[dict]:
    """One impact card per finding whose standing changes on reperformance.

    ``old`` and ``new`` map finding_uid -> verdict. Findings present in both
    with the same amount are not cards: the rerun leaves them as they were.
    Each card states the object, what changed, and the review action implied —
    never a conclusion about misstatement.
    """
    cards = []
    for uid in sorted(old.keys() | new.keys()):
        before, after = old.get(uid), new.get(uid)
        disposition = dispositions.get(uid)
        disposed = bool(disposition and disposition.get("status"))
        concurred = bool(disposition and disposition.get("concurred_by"))
        old_score = _score(before) if before else None
        new_score = _score(after) if after else None
        if before and after:
            if old_score == new_score:
                continue
            change = "amount_changed"
            delta = (new_score or Decimal("0")) - (old_score or Decimal("0"))
        elif before:
            change = "resolved_by_revision"
            delta = -(old_score or Decimal("0"))
        else:
            change = "new_after_revision"
            delta = new_score or Decimal("0")

        if change == "new_after_revision":
            action = "dispose"
            meaning = ("The revised file raises an exception that did not "
                       "exist before. It needs a disposition like any other.")
        elif not disposed:
            action = "none_after_rerun" if change == "resolved_by_revision" \
                else "dispose"
            meaning = ("No judgment was recorded on this finding yet; "
                       "rerunning the procedure brings it up to date."
                       if change == "resolved_by_revision" else
                       "The amount moved before anyone judged it; dispose "
                       "it on the revised figure.")
        elif change == "resolved_by_revision":
            action = "revisit_disposition"
            meaning = (f"You recorded '{disposition['status']}' on an "
                       "exception the revised file no longer shows. Record "
                       "why it went away (a correction by the client is "
                       "itself evidence) before relying on the rerun.")
        else:
            action = "reassess_disposition"
            meaning = (f"You recorded '{disposition['status']}' on "
                       f"{fnum(old_score) if old_score is not None else 'no amount'}"
                       f"; the revised file puts it at "
                       f"{fnum(new_score) if new_score is not None else 'no amount'}. "
                       "The judgment may still hold, but it was made on "
                       "different numbers.")
        if disposed and concurred and action in ("revisit_disposition",
                                                 "reassess_disposition"):
            meaning += (" Changing the disposition voids the reviewer's "
                        "concurrence, so it will need a second look.")

        verdict = after or before
        cards.append({
            "finding_uid": uid,
            "domain": verdict.get("domain"),
            "key": verdict.get("key"),
            "reason": verdict.get("reason", ""),
            "change": change,
            "amount_before": fnum(old_score) if old_score is not None else None,
            "amount_after": fnum(new_score) if new_score is not None else None,
            "amount_change": fnum(delta),
            "significance": significance(delta, limits),
            "disposition": (disposition or {}).get("status", "undisposed"),
            "concurred": concurred,
            "action": action,
            "what_it_means": meaning,
        })
    return cards


def sad_effect(cards: list[dict]) -> dict:
    """How the SAD's unadjusted and adjusted totals would move.

    Only findings already carried as unadjusted/adjusted differences move a
    total; everything else first needs a judgment.
    """
    moves = {"unadjusted": Decimal("0"), "adjusted": Decimal("0")}
    for card in cards:
        if card["disposition"] in moves:
            moves[card["disposition"]] += abs(
                parse_amount(card["amount_after"]) or Decimal("0")) - abs(
                parse_amount(card["amount_before"]) or Decimal("0"))
    return {status: fnum(value) for status, value in moves.items()}
