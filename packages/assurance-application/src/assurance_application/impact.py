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

import json
from decimal import Decimal

from assurance_domain.money import fnum, parse_amount
from assurance_domain.sad import PERFORMANCE_PCT, TRIVIAL_PCT

# Fields that carry money in a normalized record, by precedence.
_AMOUNT_FIELDS = ("voucher_amount", "payment_amount", "po_amount", "amount",
                  "received_amount", "subledger_balance", "gl_balance")

# The money a row of each cycle record type carries. "debit-credit" means the
# row's signed amount is its debit less its credit (when it has no amount).
# A row with none of its type's fields has no dollar measure: its changes
# are "not_measured", never "none".
ROLE_AMOUNT_FIELDS: dict[str, tuple[str, ...]] = {
    "Trial_balance": ("balance",),
    "AR_listing": ("balance",),
    "Confirmations": ("confirmed_value",),
    "Inventory_listing": ("cost",),
    "Pricing_tests": ("recorded_cost",),
    "Bank_reconciliation": ("amount",),
    "Cutoff_statement": ("amount",),
    "Transfers": ("amount",),
    "Direct_payments": ("payment_amount",),
    "Payroll_register": ("gross",),
    "Fixed_assets": ("cost",),
    "Debt_schedule": ("ending_balance",),
    "Equity_rollforward": ("ending",),
    "Accrual_schedule": ("ending",),
    "Misstatements": ("identified",),
    "Performance_materiality": ("performance_materiality",),
    "Journal_entries": ("amount", "debit-credit"),
    "Adjusting_entries": ("amount", "debit-credit"),
    "Sales_invoices": ("amount",),
    "Credit_memos": ("amount",),
}

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
    # the cycle record types (Kestrel and any case built like it)
    "Trial_balance": ("account",),
    "Journal_entries": ("entry_id", "line"),
    "Adjusting_entries": ("entry_id", "account"),
    "AR_listing": ("customer_number",),
    "Confirmations": ("customer_number",),
    "Inventory_listing": ("stock_number",),
    "Inventory_count": ("tag_number",),
    "Pricing_tests": ("stock_number",),
    # No id of their own: account, kind and reference identify the item;
    # the date and amount are what a corrected file changes.
    "Bank_reconciliation": ("account", "item_type", "reference"),
    "Cutoff_statement": ("account", "item_type", "reference"),
    "Transfers": ("transfer_id",),
    "Direct_payments": ("payment_number",),
    "Payroll_master": ("employee_id",),
    "Payroll_register": ("check_number",),
    "Fixed_assets": ("asset_id",),
    "Additions_vouching": ("asset_id",),
    "Debt_schedule": ("loan_id",),
    "Covenants": ("covenant",),
    "Equity_rollforward": ("component",),
    "Accrual_schedule": ("item",),
    "Estimates": ("estimate",),
    "Related_parties": ("party_name",),
    "Representations": ("code",),
    "Misstatements": ("reference", "description"),
    "Performance_materiality": ("account",),
}

_SIGNIFICANCE_ORDER = ("none", "below_trivial", "not_measured",
                       "above_trivial", "above_performance")


def thresholds(materiality, trivial_pct: Decimal = TRIVIAL_PCT,
               performance_pct: Decimal = PERFORMANCE_PCT) -> dict:
    """Clearly-trivial and performance materiality derived like the SAD."""
    overall = parse_amount(materiality) or Decimal("0")
    return {"materiality": overall,
            "clearly_trivial": trivial_pct * overall,
            "performance": performance_pct * overall}


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


def _record_amount(record: dict, role: str | None = None):
    for field in ROLE_AMOUNT_FIELDS.get(role or "", _AMOUNT_FIELDS):
        if field == "debit-credit":
            debit = parse_amount(record.get("debit"))
            credit = parse_amount(record.get("credit"))
            if debit is not None or credit is not None:
                return (debit or Decimal("0")) - (credit or Decimal("0"))
        elif record.get(field) not in (None, ""):
            return parse_amount(record[field])
    return None


def _measure(amount, limits: dict) -> str:
    """Significance of a row with a dollar measure; one without is unmeasured."""
    return "not_measured" if amount is None else significance(amount, limits)


def _key(record: dict, key_fields: tuple[str, ...]) -> str:
    return "|".join(str(record.get(field, "")) for field in key_fields)


# Where a row came from, not what it says: two copies of the same line in
# different files differ here, so they are left out of the content match.
_LOCATION_FIELDS = ("source_hash", "source_row", "source_file")


def _diff_by_content(old: list[dict], new: list[dict], limits: dict,
                     role: str | None = None) -> dict:
    """Rows matched as whole rows, for record types with no key field.

    Without a key there is no honest way to say a row "changed", so a changed
    row shows as one removed and one added; identical rows cancel out, counted
    as many times as they occur.
    """
    from collections import Counter

    def content(row):
        return json.dumps({k: v for k, v in row.items() if k not in _LOCATION_FIELDS},
                          sort_keys=True, default=str)
    before, after = Counter(map(content, old)), Counter(map(content, new))
    rows = {content(r): r for r in list(old) + list(new)}

    def entries(counter):
        out = []
        for c, n in sorted(counter.items()):
            amount = _record_amount(rows[c], role)
            for _ in range(n):
                out.append({"key": _describe(rows[c]),
                            "amount": fnum(amount) if amount is not None else None,
                            "significance": _measure(amount, limits)})
        return out
    added, removed = entries(after - before), entries(before - after)
    net = sum((parse_amount(i["amount"]) or Decimal("0") for i in added), Decimal("0")) - sum(
        (parse_amount(i["amount"]) or Decimal("0") for i in removed), Decimal("0"))
    return {"key_fields": ["whole row"], "rows_before": len(old), "rows_after": len(new),
            "added": added, "removed": removed, "changed": [], "duplicate_keys": [],
            "net_amount_change": fnum(net),
            "significance": _worst([i["significance"] for i in added + removed])}


def _describe(row: dict) -> str:
    """A short, readable label for a keyless row."""
    parts = [str(v) for k, v in row.items() if k not in _LOCATION_FIELDS and v not in (None, "")]
    return " · ".join(parts[:5])


def diff_records(old: list[dict], new: list[dict],
                 key_fields: tuple[str, ...], limits: dict,
                 role: str | None = None) -> dict:
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

    if not key_fields:
        return _diff_by_content(old, new, limits, role)
    # A key shared by several rows cannot say which old row became which new
    # one. Those rows are compared whole (a change shows as removed + added),
    # never dropped: keeping one row per key would hide the others' changes.
    from collections import Counter
    rows_before, rows_after = len(old), len(new)
    counts = [Counter(_key(r, key_fields) for r in rows) for rows in (old, new)]
    shared = {k for c in counts for k, n in c.items() if n > 1}
    loose = _diff_by_content([r for r in old if _key(r, key_fields) in shared],
                             [r for r in new if _key(r, key_fields) in shared],
                             limits, role) if shared else None
    old = [r for r in old if _key(r, key_fields) not in shared]
    new = [r for r in new if _key(r, key_fields) not in shared]
    before, dupes_before = index(old)
    after, dupes_after = index(new)
    dupes_before, dupes_after = sorted(shared), []
    added, removed, changed = ([], [], []) if loose is None else (
        list(loose["added"]), list(loose["removed"]), [])
    for key in sorted(after.keys() - before.keys()):
        amount = _record_amount(after[key], role)
        added.append({"key": key, "amount": fnum(amount) if amount is not None
                      else None,
                      "significance": _measure(amount, limits)})
    for key in sorted(before.keys() - after.keys()):
        amount = _record_amount(before[key], role)
        removed.append({"key": key, "amount": fnum(amount)
                        if amount is not None else None,
                        "significance": _measure(amount, limits)})
    for key in sorted(before.keys() & after.keys()):
        old_row, new_row = before[key], after[key]
        # Where the row came from (file fingerprint, row number) is not what it
        # says: a moved or re-exported row with the same content is unchanged.
        fields = sorted(field for field in set(old_row) | set(new_row)
                        if field not in _LOCATION_FIELDS
                        and old_row.get(field) != new_row.get(field))
        if not fields:
            continue
        old_amount = _record_amount(old_row, role)
        new_amount = _record_amount(new_row, role)
        measured = old_amount is not None or new_amount is not None
        delta = ((new_amount or Decimal("0")) - (old_amount or Decimal("0"))
                 if measured else Decimal("0"))
        # A row with no money field: the dollar test cannot see the change,
        # so it is "not_measured", never "none".
        level = significance(delta, limits) if measured else "not_measured"
        changed.append({
            "key": key,
            "fields": [{"field": field, "before": old_row.get(field),
                        "after": new_row.get(field)} for field in fields],
            "amount_change": fnum(delta) if measured else None,
            "significance": level,
        })
    net = sum((parse_amount(item["amount"]) or Decimal("0") for item in added),
              Decimal("0")) - sum(
        (parse_amount(item["amount"]) or Decimal("0") for item in removed),
        Decimal("0")) + sum(
        (parse_amount(item["amount_change"]) or Decimal("0")
         for item in changed), Decimal("0"))
    return {
        "key_fields": list(key_fields),
        "rows_before": rows_before, "rows_after": rows_after,
        "added": added, "removed": removed, "changed": changed,
        # compared whole rather than by key (see above); listed so it shows
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
