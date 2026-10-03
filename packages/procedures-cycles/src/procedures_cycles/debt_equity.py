# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Debt and equity: schedule rollforward and interest reasonableness, loan
covenants from the trial balance, and the equity rollforward.

The debt schedule and equity rollforward are client schedules; the covenant
sheet is the auditor's reading of the loan agreement (which accounts make
up each measure, the limit, and its direction). The engine does the
arithmetic and ties; it does not read agreements.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from procedures_cycles.common import (
    ZERO, PolicyError, dec, key_text, money, policy_date, receipt, records, source_ref,
    text,
)
from procedures_cycles.statements import _signed

DEBT, COVENANTS, EQUITY = "Debt_schedule", "Covenants", "Equity_rollforward"


def _accounts(raw) -> list[str]:
    return [key_text(a) for a in text(raw).replace(";", ",").split(",") if a.strip()]


def _tb(tables: dict) -> dict[str, dict]:
    return {key_text(r.get("account")): r for r in records(tables, "Trial_balance")}


def _rate(value) -> Decimal | None:
    """An annual rate given as a fraction (0.065) or a percent (6.5 or '6.5%')."""
    d = dec(value)
    if d is None:
        return None
    return d / 100 if d >= 1 or str(value).strip().endswith("%") else d


def rollforward_and_interest(tables: dict, policies: dict):
    pid = "debt.rollforward_and_interest"
    policy_date(policies, "period_end")
    debt_accounts = _accounts(policies.get("debt_accounts"))
    if not debt_accounts:
        raise PolicyError("policy 'debt_accounts' is not set; name the trial balance "
                          "accounts that carry the loans")
    tolerance = dec(policies.get("debt_interest_tolerance_pct"))
    tolerance = tolerance / 100 if tolerance is not None and tolerance >= 1 else tolerance
    findings = []
    begin_total = end_total = interest_total = ZERO
    not_performed = {}
    if tolerance is None:
        not_performed["interest"] = "policy debt_interest_tolerance_pct is not set"
    loans = records(tables, DEBT)
    for loan in loans:
        lid = key_text(loan.get("loan_id"))
        src = [source_ref(DEBT, loan, "loan_id")]
        begin, end = money(loan.get("beginning_balance")), money(loan.get("ending_balance"))
        borrowed, repaid = money(loan.get("borrowings")), money(loan.get("repayments"))
        begin_total += begin
        end_total += end
        interest_total += money(loan.get("interest_expense"))
        if begin + borrowed - repaid != end:
            gap = begin + borrowed - repaid - end
            findings.append(receipt(
                pid, (lid, "does_not_foot"), "CLASH",
                f"loan {lid}: {begin} + borrowings {borrowed} - repayments {repaid} = "
                f"{begin + borrowed - repaid}, but the schedule shows {end}",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "debt_equity",
                 "source_rows": src}, gap))
        rate, recorded = _rate(loan.get("interest_rate")), dec(loan.get("interest_expense"))
        if tolerance is not None and rate is not None and recorded is not None:
            expected = money((begin + end) / 2 * rate)
            if expected and abs(money(recorded) - expected) > abs(expected) * tolerance:
                findings.append(receipt(
                    pid, (lid, "interest_unexpected"), "TENSION",
                    f"loan {lid}: average balance {money((begin + end) / 2)} at "
                    f"{rate * 100:.3f}% suggests about {expected} interest; the schedule "
                    f"records {money(recorded)} — more than {tolerance * 100:.1f}% apart",
                    {"finding_class": "CONJECTURE", "cycle": "debt_equity",
                     "expected": expected, "recorded": recorded, "source_rows": src},
                    money(recorded) - expected))
    tb = _tb(tables)

    def tie(label, total, accounts, field):
        present = [a for a in accounts if a in tb]
        if len(present) != len(accounts):
            missing = sorted(set(accounts) - set(present))
            findings.append(receipt(
                pid, (label, "accounts_not_on_trial_balance"), "AMBIGUOUS",
                f"account(s) {', '.join(missing)} named for {label.replace('_', ' ')} "
                "are not on the trial balance",
                {"finding_class": "REFUSAL", "cycle": "debt_equity"}))
        values = [_signed(tb[a], field) for a in present]
        if not present or any(v is None for v in values):
            return None
        ledger = -money(sum(values, ZERO))          # credit balances, shown positive
        if ledger != total:
            findings.append(receipt(
                pid, (label, "schedule_to_ledger"), "CLASH",
                f"{label.replace('_', ' ')}: the debt schedule gives {total}, the trial "
                f"balance {ledger} (difference {total - ledger})",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "debt_equity",
                 "schedule": total, "ledger": ledger}, total - ledger))
        return ledger

    tie("ending_debt", end_total, debt_accounts, "balance")
    if any(tb[a].get("prior_balance") not in (None, "") for a in debt_accounts if a in tb):
        tie("beginning_debt", begin_total, debt_accounts, "prior_balance")
    interest_accounts = _accounts(policies.get("debt_interest_accounts"))
    if interest_accounts:
        ledger = money(sum((_signed(tb[a]) or ZERO for a in interest_accounts if a in tb),
                           ZERO))
        if ledger != interest_total:
            findings.append(receipt(
                pid, ("interest_expense", "schedule_to_ledger"), "CLASH",
                f"interest expense: the schedule totals {interest_total}, the trial "
                f"balance {ledger}", {"finding_class": "PROVED_EXCEPTION",
                                      "cycle": "debt_equity"}, interest_total - ledger))
    stats = {"population": len(loans), "beginning_debt": begin_total,
             "ending_debt": end_total, "interest_expense": interest_total,
             "interest_tolerance": tolerance, "not_performed": not_performed,
             "exceptions": len(findings)}
    return findings, stats


_OPERATORS = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
              ">": lambda a, b: a > b, "<": lambda a, b: a < b,
              "min": lambda a, b: a >= b, "max": lambda a, b: a <= b}


_TRAILING = ("ttm", "trailing", "trailing twelve months", "ltm", "last twelve months",
             "rolling")


def _adjustments(tables: dict) -> dict[str, Decimal] | None:
    """Debit-positive net of the adjusting entries per account, or None when
    none are loaded."""
    entries = records(tables, "Adjusting_entries")
    if not entries:
        return None
    out: dict[str, Decimal] = {}
    for e in entries:
        account = key_text(e.get("account"))
        out[account] = out.get(account, ZERO) + money(e.get("debit")) - money(e.get("credit"))
    return out


def _measure(num, den, balance, add_num: Decimal, add_den: Decimal):
    """(value, denominator) with the agreement's add-backs; None if the
    denominator is zero."""
    numerator = abs(sum((balance(a) for a in num), ZERO)) + add_num
    if not den:
        return money(numerator), None
    denominator = abs(sum((balance(a) for a in den), ZERO)) + add_den
    if denominator == 0:
        return None, ZERO
    return (numerator / denominator).quantize(Decimal("0.0001")), denominator


def covenants(tables: dict, policies: dict):
    """Each covenant measured from the trial balance, with the agreement's
    add-backs (numerator/denominator adjustments), and, when adjusting
    entries are loaded, again on the adjusted balances (depth pass, 2 Oct
    2026): a covenant that passes before the audit adjustments and fails
    after them, or the reverse, is a finding. A trailing-twelve-month
    covenant is measured only when the period is twelve months; quarterly
    figures are not in an annual trial balance."""
    pid = "debt.covenants"
    tb = _tb(tables)
    adjusting = _adjustments(tables)
    findings, measured = [], []
    rows = records(tables, COVENANTS)
    months, twelve = None, False
    if policies.get("period_start") and policies.get("period_end"):
        s, e = policy_date(policies, "period_start"), policy_date(policies, "period_end")
        months = (e.year - s.year) * 12 + e.month - s.month + 1
        # A real twelve months, day to day: the day after the end is the
        # start's anniversary (review 2026-10-02 depth, Codex 5: 31 Jan to
        # 1 Dec touches twelve month names but is 305 days).
        after = e + timedelta(days=1)
        twelve = (after.year, after.month, after.day) == (s.year + 1, s.month, s.day)
    for row in rows:
        name = text(row.get("covenant")) or f"row-{row.get('source_row')}"
        key = key_text(name)
        src = [source_ref(COVENANTS, row, "covenant")]
        num, den = _accounts(row.get("numerator_accounts")), _accounts(
            row.get("denominator_accounts"))
        op = text(row.get("operator")).lower()
        limit = dec(row.get("threshold"))
        missing = sorted({a for a in num + den if a not in tb})
        basis = text(row.get("basis")).lower()
        trailing = any(t in basis for t in _TRAILING)
        why = ""
        if missing:
            why = f"accounts not on the trial balance: {', '.join(missing)}"
        elif not num or op not in _OPERATORS or limit is None:
            why = "the covenant needs numerator accounts, an operator (>=, <=) and a limit"
        elif trailing and not twelve:
            why = ("it is measured on a trailing twelve months, and the period here is "
                   f"{f'not twelve months ({months} calendar months touched)' if months else 'not dated (period start unset)'}: "
                   "an annual trial balance does not give quarterly figures")
        elif (money(row.get("numerator_adjustment")) or money(row.get(
                "denominator_adjustment"))) and not text(row.get("adjustment_note")):
            why = ("an add-back is entered with no note: say which clause of the "
                   "agreement allows it (review 2026-10-02 depth, Codex 4)")
        if why:
            findings.append(receipt(pid, (key, "not_measurable"), "AMBIGUOUS",
                                    f"covenant {name}: {why}",
                                    {"finding_class": "REFUSAL", "cycle": "debt_equity",
                                     "source_rows": src}))
            continue
        add_num = money(row.get("numerator_adjustment"))
        add_den = money(row.get("denominator_adjustment"))
        value, denominator = _measure(num, den, lambda a: _signed(tb[a]) or ZERO,
                                      add_num, add_den)
        if value is None:
            findings.append(receipt(pid, (key, "not_measurable"), "AMBIGUOUS",
                                    f"covenant {name}: the denominator is zero",
                                    {"finding_class": "REFUSAL",
                                     "cycle": "debt_equity", "source_rows": src}))
            continue
        entry = {"covenant": name, "value": value, "operator": op, "limit": limit}
        if add_num or add_den:
            entry["agreement_adjustments"] = {
                "numerator": add_num, "denominator": add_den,
                "note": text(row.get("adjustment_note"))}
        if trailing:
            entry["basis"] = "trailing twelve months = the twelve-month period"
        adjusted = None
        if adjusting is not None:
            adjusted, _ = _measure(
                num, den, lambda a: (_signed(tb[a]) or ZERO) + adjusting.get(a, ZERO),
                add_num, add_den)
            entry["adjusted_value"] = adjusted
            if adjusted is None:
                # Codex 2: the adjustments take the denominator to zero.
                findings.append(receipt(
                    pid, (key, "adjusted_not_measurable"), "AMBIGUOUS",
                    f"covenant {name}: {value} before the audit adjustments; after them "
                    "the denominator is zero, so compliance on the adjusted figures "
                    "cannot be measured", {"finding_class": "REFUSAL",
                                           "cycle": "debt_equity", "source_rows": src}))
        measured.append(entry)
        passes = _OPERATORS[op](value, limit)
        if adjusted is not None and _OPERATORS[op](adjusted, limit) != passes:
            findings.append(receipt(
                pid, (key, "adjustments_change_compliance"), "CLASH",
                f"covenant {name}: {value} before the audit adjustments "
                f"({'meets' if passes else 'breaches'} {op} {limit}), {adjusted} after them "
                f"({'breaches' if passes else 'meets'} it). The adjustments decide "
                "compliance: discuss them with management, and consider the lender",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "debt_equity",
                 "assertion": "classification", "value": value, "adjusted_value": adjusted,
                 "limit": limit, "source_rows": src}))
        # The breach follows the adjusted figures when they are measured, and
        # says which basis it describes (Codex 3: a breach the adjustments
        # cure was still reported unconditionally).
        final, on = (adjusted, "after the audit adjustments") if adjusted is not None \
            else (value, "on the trial balance as loaded")
        if not _OPERATORS[op](final, limit):
            findings.append(receipt(
                pid, (key, "breached"), "CLASH",
                f"covenant {name}: measured {final} {on} against a limit of {op} {limit} "
                "— breached. Is there a waiver? If not, the debt may be due on demand "
                "(current), which also bears on going concern",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "debt_equity",
                 "assertion": "classification", "value": value,
                 "adjusted_value": adjusted, "limit": limit, "basis": on,
                 "source_rows": src}))
    stats = {"population": len(rows), "measured": measured, "exceptions": len(findings)}
    return findings, stats


def equity_rollforward(tables: dict, policies: dict):
    pid = "equity.rollforward"
    tb = _tb(tables)
    findings = []
    rows = records(tables, EQUITY)
    for row in rows:
        name = text(row.get("component")) or f"row-{row.get('source_row')}"
        key = key_text(name)
        src = [source_ref(EQUITY, row, "component")]
        begin, end = money(row.get("beginning")), money(row.get("ending"))
        adds, less = money(row.get("additions")), money(row.get("reductions"))
        if begin + adds - less != end:
            findings.append(receipt(
                pid, (key, "does_not_foot"), "CLASH",
                f"{name}: {begin} + {adds} - {less} = {begin + adds - less}, but the "
                f"rollforward shows {end}",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "debt_equity",
                 "source_rows": src}, begin + adds - less - end))
        accounts = _accounts(row.get("account")) if tb else []
        present = [a for a in accounts if a in tb]
        if accounts and len(present) != len(accounts):
            findings.append(receipt(
                pid, (key, "accounts_not_on_trial_balance"), "AMBIGUOUS",
                f"{name}: account(s) {', '.join(sorted(set(accounts) - set(present)))} "
                "are not on the trial balance",
                {"finding_class": "REFUSAL", "cycle": "debt_equity", "source_rows": src}))
            continue
        for label, total, field in (("ending", end, "balance"),
                                    ("beginning", begin, "prior_balance")):
            values = [_signed(tb[a], field) for a in present]
            if not present or any(v is None for v in values):
                continue
            ledger = -money(sum(values, ZERO))      # equity is credit: shown positive
            if ledger != total:
                findings.append(receipt(
                    pid, (key, f"{label}_to_ledger"), "CLASH",
                    f"{name}: {label} {total} per the rollforward, {ledger} per the trial "
                    f"balance", {"finding_class": "PROVED_EXCEPTION",
                                 "cycle": "debt_equity", "source_rows": src},
                    total - ledger))
    stats = {"population": len(rows), "exceptions": len(findings),
             "not_performed": ({} if tb else
                               {"ties_to_ledger": "no trial balance is loaded"})}
    return findings, stats
