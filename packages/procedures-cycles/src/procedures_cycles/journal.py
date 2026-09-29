# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Journal entry testing (AU-C 240): selection by risk characteristics, and
the completeness of the population the selection was made from.

The executors select; they do not conclude. A selected entry is a lead for
inquiry and vouching. Every judgment threshold (what counts as a round
amount, who may post, how seldom is "seldom used") is the auditor's policy.
A test whose data or policy is missing is reported as *not performed*, with
the reason, never skipped in silence.
"""

from __future__ import annotations

from decimal import Decimal

from procedures_cycles.common import (
    ZERO, dec, day, key_text, money, period_bounds, receipt, records, source_ref, text,
)
from procedures_cycles.statements import _signed

ROLE = "Journal_entries"


def _line_amount(row: dict) -> Decimal | None:
    """Debit-positive amount of one journal line: a signed amount, or debit − credit."""
    amount = dec(row.get("amount"))
    if amount is not None:
        return amount
    debit, credit = dec(row.get("debit")), dec(row.get("credit"))
    if debit is None and credit is None:
        return None
    return (debit or ZERO) - (credit or ZERO)


def _entries(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(key_text(row.get("entry_id")), []).append(row)
    return grouped


def _csv_policy(policies: dict, name: str) -> list[str] | None:
    raw = text(policies.get(name))
    if not raw:
        return None
    return [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]


def journal_entry_testing(tables: dict, policies: dict):
    pid = "je.journal_entry_testing"
    start, pe = period_bounds(policies)
    rows = records(tables, ROLE)
    entries = _entries(rows)
    findings: list = []
    counts: dict[str, int] = {}
    not_performed: dict[str, str] = {}
    has = lambda field: any(text(r.get(field)) for r in rows)

    def lead(entry_id, test, verdict, reason, evidence, amount=None, cls="CONJECTURE"):
        counts[test] = counts.get(test, 0) + 1
        findings.append(receipt(pid, (entry_id, test), verdict, reason,
                                {"finding_class": cls, "cycle": "journal_entries",
                                 "test": test, **evidence}, amount))

    # Judgments that switch tests on. Absent ones are reported, not assumed.
    threshold = dec(policies.get("je_round_amount_threshold"))
    unit = dec(policies.get("je_round_unit")) or Decimal("1000")
    authorized = _csv_policy(policies, "je_authorized_users")
    seldom_max = dec(policies.get("je_seldom_used_max"))
    holidays = {d for d in (day(h) for h in (_csv_policy(policies, "je_holidays") or []))
                if d is not None}
    if threshold is None:
        not_performed["round_amount"] = "policy je_round_amount_threshold is not set"
    if not has("posted_date"):
        not_performed["posted_after_period_end"] = (
            "the listing has no posted (entered) date, only the entry date")
    if not has("posted_by"):
        not_performed["unauthorized_user"] = "the listing has no posted-by user"
        not_performed["self_approved"] = "the listing has no posted-by user"
    elif authorized is None:
        not_performed["unauthorized_user"] = "policy je_authorized_users is not set"
    if not has("approved_by"):
        not_performed.setdefault("self_approved", "the listing has no approver")
    if seldom_max is None:
        not_performed["seldom_used_account"] = "policy je_seldom_used_max is not set"
    if not has("description"):
        not_performed["no_description"] = "the listing has no description column"

    entry_dates = {entry_id: min((d for d in (day(line.get("entry_date")) for line in lines)
                                  if d), default=None)
                   for entry_id, lines in entries.items()}

    # "Seldom used" is measured within the period tested. An entry from the
    # next period (loaded for subsequent-events work) must not make a rare
    # in-period account look common.
    account_use: dict[str, set[str]] = {}
    for entry_id, lines in entries.items():
        dated = entry_dates[entry_id]
        if dated is not None and not start <= dated <= pe:
            continue
        for line in lines:
            account_use.setdefault(key_text(line.get("account")), set()).add(entry_id)

    tested = after_period = before_period = 0
    for entry_id, lines in sorted(entries.items()):
        src = [source_ref(ROLE, line, "entry_id") for line in lines]
        amounts = [_line_amount(line) for line in lines]
        dated = entry_dates[entry_id]
        if dated is not None and dated > pe:
            after_period += 1                # next period's entry: not in this population
            continue
        if dated is not None and dated < start:
            before_period += 1               # an earlier period's entry
            continue
        tested += 1
        base = {"entry_date": dated, "lines": len(lines), "source_rows": src}
        if any(a is None for a in amounts):
            lead(entry_id, "no_amount", "AMBIGUOUS",
                 f"entry {entry_id}: a line has no amount; it cannot be footed",
                 base, cls="REFUSAL")
            continue
        net = sum(amounts, ZERO)
        debits = sum((a for a in amounts if a > 0), ZERO)
        base["debits"] = debits
        if net != 0:
            lead(entry_id, "unbalanced", "CLASH",
                 f"entry {entry_id}: debits and credits differ by {net}", base,
                 net, cls="PROVED_EXCEPTION")
        posted = max((d for d in (day(line.get("posted_date")) for line in lines) if d),
                     default=None)
        if posted is not None and dated is not None and dated <= pe < posted:
            lead(entry_id, "posted_after_period_end", "TENSION",
                 f"entry {entry_id}: dated {dated} but entered {posted}, after period end "
                 f"{pe} — a post-closing entry; inquire and vouch", base, debits)
        when = posted or dated
        if when is not None and (when.weekday() >= 5 or when in holidays):
            lead(entry_id, "weekend_or_holiday", "TENSION",
                 f"entry {entry_id}: entered on {when:%A} {when}"
                 + (" (a holiday)" if when in holidays else ""), base, debits)
        if threshold is not None and debits >= threshold and debits % unit == 0:
            lead(entry_id, "round_amount", "TENSION",
                 f"entry {entry_id}: {debits} is a round amount (a multiple of {unit}) "
                 f"at or above {threshold}", base, debits)
        users = {text(line.get("posted_by")) for line in lines if text(line.get("posted_by"))}
        if authorized is not None and users:
            outside = sorted(u for u in users
                             if u.lower() not in {a.lower() for a in authorized})
            if outside:
                lead(entry_id, "unauthorized_user", "TENSION",
                     f"entry {entry_id}: posted by {', '.join(outside)}, not on the "
                     "authorized list", {**base, "users": outside}, debits)
        approvers = {text(line.get("approved_by")).lower() for line in lines
                     if text(line.get("approved_by"))}
        if users and approvers and {u.lower() for u in users} & approvers:
            lead(entry_id, "self_approved", "TENSION",
                 f"entry {entry_id}: approved by the same user who posted it", base, debits)
        if seldom_max is not None:
            rare = sorted(a for a in {key_text(line.get("account")) for line in lines}
                          if len(account_use.get(a, ())) <= seldom_max)
            if rare:
                lead(entry_id, "seldom_used_account", "TENSION",
                     f"entry {entry_id}: posts to seldom-used account(s) {', '.join(rare)} "
                     f"(used by {int(seldom_max)} or fewer entries)",
                     {**base, "accounts": rare}, debits)
        if "no_description" not in not_performed and not any(
                text(line.get("description")) for line in lines):
            lead(entry_id, "no_description", "TENSION",
                 f"entry {entry_id}: no description on any line", base, debits)

    all_tests = ("unbalanced", "posted_after_period_end", "weekend_or_holiday",
                 "round_amount", "unauthorized_user", "self_approved",
                 "seldom_used_account", "no_description")
    stats = {"population": tested, "entries": len(entries), "lines": len(rows),
             "dated_after_period_end": after_period, "period_end": pe,
             "dated_before_period_start": before_period, "period_start": start,
             "tests_performed": [t for t in all_tests if t not in not_performed],
             "not_performed": not_performed, "selected_by_test": counts,
             "round_unit": unit, "exceptions": len(findings)}
    return findings, stats


def population_completeness(tables: dict, policies: dict):
    pid = "je.population_completeness"
    start, pe = period_bounds(policies)
    activity: dict[str, Decimal] = {}
    missing_amount = outside = 0
    for line in records(tables, ROLE):
        dated = day(line.get("entry_date"))
        if dated is not None and not start <= dated <= pe:
            outside += 1
            continue
        amount = _line_amount(line)
        if amount is None:
            missing_amount += 1
            continue
        account = key_text(line.get("account"))
        activity[account] = activity.get(account, ZERO) + amount
    current: dict[str, Decimal] = {}
    prior: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for row in records(tables, "Trial_balance"):
        account = key_text(row.get("account"))
        current[account] = current.get(account, ZERO) + (_signed(row) or ZERO)
        prior[account] = prior.get(account, ZERO) + (_signed(row, "prior_balance") or ZERO)
        names[account] = text(row.get("description"))

    findings = []
    rolled, closed, unexplained = [], [], {}
    for account in sorted(set(current) | set(activity)):
        cur, pri, act = (current.get(account, ZERO), prior.get(account, ZERO),
                         activity.get(account, ZERO))
        if account not in current:
            findings.append(receipt(
                pid, (account, "not_on_trial_balance"), "ORPHAN",
                f"account {account}: journal activity {money(act)} but the account is "
                "not on the trial balance", {"finding_class": "EXPECTED_BUT_MISSING",
                                             "cycle": "journal_entries", "activity": act},
                act))
            continue
        if money(pri + act) == money(cur):
            rolled.append(account)
        elif pri != 0 and money(act) == money(cur):
            closed.append(account)           # an income-statement account that closed
        else:
            unexplained[account] = money(cur - pri - act)
    # The prior year's closed balances went to one equity account (retained
    # earnings); that account's gap is exactly their total.
    closing = sum((prior[a] for a in closed), ZERO)
    closed_to = next((a for a, gap in unexplained.items() if gap == money(closing)), None)
    if closed_to is not None:
        del unexplained[closed_to]
    for account, gap in unexplained.items():
        findings.append(receipt(
            pid, (account, "does_not_roll_forward"), "CLASH",
            f"account {account} {names.get(account, '')}: prior {money(prior[account])} "
            f"+ journal activity {money(activity.get(account, ZERO))} does not reach the "
            f"trial balance {money(current[account])} (difference {gap}) — entries are "
            "missing from the listing, or the listing is not the one the ledger holds",
            {"finding_class": "PROVED_EXCEPTION", "cycle": "journal_entries",
             "prior": prior[account], "activity": activity.get(account, ZERO),
             "current": current[account], "difference": gap}, gap))
    stats = {"population": len(current), "accounts_rolled_forward": len(rolled),
             "income_statement_accounts_closed": closed, "closed_to": closed_to,
             "prior_year_closing_amount": money(closing),
             "lines_without_amount": missing_amount,
             "lines_outside_period": outside, "period_start": start,
             "exceptions": len(findings)}
    return findings, stats
