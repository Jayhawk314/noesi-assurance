# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Debt and equity: schedule rollforward and interest reasonableness, loan
covenants from the trial balance, and the equity rollforward.

The debt schedule and equity rollforward are client schedules; the covenant
sheet is the auditor's reading of the loan agreement (which accounts make
up each measure, the limit, and its direction). The engine does the
arithmetic and ties; it does not read agreements.
"""

from __future__ import annotations

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


def covenants(tables: dict, policies: dict):
    pid = "debt.covenants"
    tb = _tb(tables)
    findings, measured = [], []
    rows = records(tables, COVENANTS)
    for row in rows:
        name = text(row.get("covenant")) or f"row-{row.get('source_row')}"
        key = key_text(name)
        src = [source_ref(COVENANTS, row, "covenant")]
        num, den = _accounts(row.get("numerator_accounts")), _accounts(
            row.get("denominator_accounts"))
        op = text(row.get("operator")).lower()
        limit = dec(row.get("threshold"))
        missing = sorted({a for a in num + den if a not in tb})
        if not num or op not in _OPERATORS or limit is None or missing:
            why = (f"accounts not on the trial balance: {', '.join(missing)}" if missing
                   else "the covenant needs numerator accounts, an operator (>=, <=) "
                        "and a limit")
            findings.append(receipt(pid, (key, "not_measurable"), "AMBIGUOUS",
                                    f"covenant {name}: {why}",
                                    {"finding_class": "REFUSAL", "cycle": "debt_equity",
                                     "source_rows": src}))
            continue
        numerator = abs(sum((_signed(tb[a]) or ZERO for a in num), ZERO))
        if den:
            denominator = abs(sum((_signed(tb[a]) or ZERO for a in den), ZERO))
            if denominator == 0:
                findings.append(receipt(pid, (key, "not_measurable"), "AMBIGUOUS",
                                        f"covenant {name}: the denominator is zero",
                                        {"finding_class": "REFUSAL",
                                         "cycle": "debt_equity", "source_rows": src}))
                continue
            value = (numerator / denominator).quantize(Decimal("0.0001"))
        else:
            value = money(numerator)
        measured.append({"covenant": name, "value": value, "operator": op,
                         "limit": limit})
        if not _OPERATORS[op](value, limit):
            findings.append(receipt(
                pid, (key, "breached"), "CLASH",
                f"covenant {name}: measured {value} against a limit of {op} {limit} — "
                "breached. Is there a waiver? If not, the debt may be due on demand "
                "(current), which also bears on going concern",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "debt_equity",
                 "assertion": "classification", "value": value, "limit": limit,
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
