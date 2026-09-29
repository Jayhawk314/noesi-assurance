# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Planning and completion over the trial balance.

- fs.trial_balance_analytics: foot the TB, compute standard ratios for the
  current and prior year, and flag account movements above an approved
  threshold as items the auditor must explain. It never calls a movement a
  misstatement.
- planning.performance_materiality: check that allocated performance
  materiality stays within the approved multiple of overall materiality.
- fs.adjusted_trial_balance: check each proposed adjusting entry balances,
  apply the entries, and re-foot (debits = credits, net income).
- completion.uncorrected_misstatements: total the summary of uncorrected
  misstatements by column and compare each total to materiality.

Trial-balance convention: ``balance`` is unsigned with ``side`` DR/CR (or a
signed balance with no side, debit positive). ``line`` is the auditor's
financial-statement classification, one of LINES.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from procedures_cycles.common import (
    CENT, ZERO, PolicyError, dec, key_text, money, policy_decimal, policy_rate,
    receipt, records, source_ref, text,
)

LINES = (
    "cash", "receivables", "allowance", "inventory", "other_current_assets",
    "noncurrent_assets", "current_liabilities", "noncurrent_liabilities", "equity",
    "sales", "sales_returns", "cost_of_sales", "operating_expense", "other_income",
    "other_expense", "income_tax",
)
_CREDIT_NORMAL = {"allowance", "current_liabilities", "noncurrent_liabilities", "equity",
                  "sales", "other_income"}

# Words in a client's own lead-schedule label that suggest one of LINES.
# A suggestion only: the preparer confirms every mapping (finding K8).
_LINE_HINTS: tuple[tuple[str, str], ...] = (
    ("allowance", "allowance"), ("doubtful", "allowance"),
    ("sales return", "sales_returns"), ("returns and allowances", "sales_returns"),
    ("cost of", "cost_of_sales"), ("cogs", "cost_of_sales"),
    ("receivable", "receivables"), ("cash", "cash"), ("bank", "cash"),
    ("inventor", "inventory"), ("prepaid", "other_current_assets"),
    ("other current asset", "other_current_assets"),
    ("property", "noncurrent_assets"), ("equipment", "noncurrent_assets"),
    ("fixed asset", "noncurrent_assets"), ("intangible", "noncurrent_assets"),
    ("long-term debt", "noncurrent_liabilities"), ("long term debt", "noncurrent_liabilities"),
    ("notes payable - long", "noncurrent_liabilities"),
    ("payable", "current_liabilities"), ("accrued", "current_liabilities"),
    ("line of credit", "current_liabilities"), ("current liabilit", "current_liabilities"),
    ("equity", "equity"), ("capital", "equity"), ("retained", "equity"),
    ("revenue", "sales"), ("sales", "sales"), ("income tax", "income_tax"),
    ("other income", "other_income"), ("interest income", "other_income"),
    ("interest expense", "other_expense"), ("other expense", "other_expense"),
    ("expense", "operating_expense"),
)


def suggest_line(label: str) -> str | None:
    """A likely statement line for a client's own label, or None."""
    words = text(label).lower()
    if words in LINES:
        return words
    return next((line for hint, line in _LINE_HINTS if hint in words), None)


def apply_line_mapping(rows: list[dict], mapping: dict) -> list[dict]:
    """Trial balance rows with their line translated by the engagement's
    mapping: an account-specific entry ("account:11900") first, then the
    label ("label:accounts receivable"). Rows already on a recognized line,
    or not mapped, keep their line; the originals are never changed."""
    if not mapping:
        return rows
    out = []
    for row in rows:
        label = text(row.get("line")).lower()
        target = (mapping.get(f"account:{key_text(row.get('account'))}")
                  or mapping.get(f"label:{label}"))
        out.append({**row, "line": target} if target else row)
    return out
_INCOME = {"sales", "sales_returns", "cost_of_sales", "operating_expense", "other_income",
           "other_expense", "income_tax"}


def _signed(record: dict, field: str = "balance") -> Decimal | None:
    """Debit-positive signed amount."""
    amount = dec(record.get(field))
    if amount is None:
        return None
    side = text(record.get("side")).lower()
    if side.startswith("cr"):
        return -abs(amount)
    if side.startswith("dr"):
        return abs(amount)
    return amount


def _totals(rows: list[dict], field: str) -> dict[str, Decimal]:
    """Natural-sign totals per line (credit-normal lines shown positive)."""
    out = {line: ZERO for line in LINES}
    for row in rows:
        line = text(row.get("line")).lower()
        amount = _signed(row, field)
        if line in out and amount is not None:
            out[line] += -amount if line in _CREDIT_NORMAL else amount
    return out


def ratios(t: dict[str, Decimal], prior: dict[str, Decimal] | None = None) -> dict:
    """Standard liquidity, performance and solvency ratios from line totals."""
    def div(a, b):
        return None if not b else (Decimal(a) / Decimal(b))

    net_receivables = t["receivables"] - t["allowance"]
    current_assets = (t["cash"] + net_receivables + t["inventory"]
                      + t["other_current_assets"])
    total_assets = current_assets + t["noncurrent_assets"]
    current_liabilities = t["current_liabilities"]
    total_liabilities = current_liabilities + t["noncurrent_liabilities"]
    net_sales = t["sales"] - t["sales_returns"]
    gross_profit = net_sales - t["cost_of_sales"]
    income_before_taxes = (gross_profit - t["operating_expense"] + t["other_income"]
                           - t["other_expense"])
    equity = t["equity"] + (income_before_taxes - t["income_tax"])  # books still open
    average_inventory = ((t["inventory"] + prior["inventory"]) / 2) if prior else None
    out = {
        "current_ratio": div(current_assets, current_liabilities),
        # Quick assets are cash and receivables (AICPA analytical procedures
        # guide): prepaids and other current assets are not.
        "quick_ratio": div(t["cash"] + net_receivables, current_liabilities),
        "sales_to_receivables": div(net_sales, net_receivables),
        "days_sales_in_receivables": (div(net_receivables * 365, net_sales)),
        "inventory_turnover": div(t["cost_of_sales"], average_inventory)
        if average_inventory else None,
        "gross_margin": div(gross_profit, net_sales),
        "ibt_to_equity": div(income_before_taxes, equity),
        "ibt_to_total_assets": div(income_before_taxes, total_assets),
        "sales_to_long_term_assets": div(net_sales, t["noncurrent_assets"]),
        "sales_to_total_assets": div(net_sales, total_assets),
        "sales_to_working_capital": div(net_sales, current_assets - current_liabilities),
        "equity_to_total_assets": div(equity, total_assets),
        "long_term_assets_to_equity": div(t["noncurrent_assets"], equity),
        "current_liabilities_to_equity": div(current_liabilities, equity),
        "total_liabilities_to_equity": div(total_liabilities, equity),
    }
    figures = {"current_assets": current_assets, "total_assets": total_assets,
               "net_sales": net_sales, "gross_profit": gross_profit,
               "income_before_taxes": income_before_taxes, "equity": equity,
               "total_liabilities": total_liabilities}
    return {"ratios": {k: (v.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                           if v is not None else None) for k, v in out.items()},
            "figures": {k: v.quantize(CENT) for k, v in figures.items()}}


def trial_balance_analytics(tables: dict, policies: dict):
    pid = "fs.trial_balance_analytics"
    rows = records(tables, "Trial_balance")
    findings = []
    debits = sum((a for r in rows if (a := _signed(r)) is not None and a > 0), ZERO)
    credits = -sum((a for r in rows if (a := _signed(r)) is not None and a < 0), ZERO)
    if debits != credits:
        findings.append(receipt(pid, ("tb_out_of_balance",), "CLASH",
                                f"trial balance does not foot: debits {debits} vs "
                                f"credits {credits}",
                                {"finding_class": "PROVED_EXCEPTION", "cycle": "planning",
                                 "debits": debits, "credits": credits},
                                debits - credits))
    unclassified = [text(r.get("account")) for r in rows
                    if text(r.get("line")).lower() not in LINES]
    for account in unclassified:
        findings.append(receipt(pid, ("unclassified", account), "AMBIGUOUS",
                                f"account {account} has no recognized statement line; "
                                "it is left out of every ratio",
                                {"finding_class": "REFUSAL", "cycle": "planning",
                                 "allowed_lines": list(LINES)}))
    current = _totals(rows, "balance")
    has_prior = any(dec(r.get("prior_balance")) is not None for r in rows)
    prior = _totals(rows, "prior_balance") if has_prior else None
    now = ratios(current, prior)
    before = ratios(prior) if prior else None

    threshold = None
    if policies.get("analytics_threshold_pct") not in (None, ""):
        threshold = Decimal(repr(policy_rate(policies, "analytics_threshold_pct")))
    floor = dec(policies.get("analytics_threshold_amount")) or ZERO
    # K9: whether a movement must pass both thresholds or either is the
    # auditor's rule, stated with the result; unset, both (the stricter).
    rule = text(policies.get("analytics_threshold_rule")).lower() or "and"
    if rule not in ("and", "or"):
        raise PolicyError("analytics_threshold_rule must be 'and' or 'or'")
    movements = []
    if prior is not None:
        for r in rows:
            cy, py = _signed(r, "balance"), _signed(r, "prior_balance")
            if cy is None or py is None:
                continue
            change = cy - py
            pct = (change / abs(py)) if py else None
            movements.append({"account": text(r.get("account")),
                              "description": text(r.get("description")),
                              "current": cy, "prior": py, "change": change,
                              "pct_change": pct.quantize(Decimal("0.0001"))
                              if pct is not None else None})
            if threshold is None:
                continue
            big_pct = pct is None or abs(pct) >= threshold
            big_amount = abs(change) >= floor
            if rule == "or" and not floor:
                big_amount = False           # no amount threshold set: it adds nothing
            if change != 0 and ((big_pct and big_amount) if rule == "and"
                                else (big_pct or big_amount)):
                findings.append(receipt(
                    pid, ("movement", text(r.get("account"))), "TENSION",
                    f"account {text(r.get('account'))} {text(r.get('description'))} moved "
                    f"{change} ({'new' if pct is None else f'{pct:.1%}'}) — obtain and "
                    "corroborate an explanation",
                    {"finding_class": "CONJECTURE", "kind": "risk", "cycle": "planning",
                     "current": cy, "prior": py, "change": change,
                     "source_rows": [source_ref("Trial_balance", r, "account")],
                     "limits": "an unusual movement is a question for inquiry, "
                               "not a misstatement"}))
    stats = {"population": len(rows), "debits": debits, "credits": credits,
             "line_totals": {k: v for k, v in current.items()},
             "current": now, "prior": before, "threshold_rule": rule,
             "ratio_change": {k: (now["ratios"][k] - before["ratios"][k])
                              if before and now["ratios"][k] is not None
                              and before["ratios"][k] is not None else None
                              for k in now["ratios"]},
             "movements": movements, "unclassified_accounts": unclassified,
             "threshold_pct": threshold, "exceptions": len(findings)}
    return findings, stats


def performance_materiality(tables: dict, policies: dict):
    pid = "planning.performance_materiality"
    materiality = policy_decimal(policies, "materiality")
    multiple = policy_decimal(policies, "pm_allocation_multiple")
    rows = records(tables, "Performance_materiality")
    allocated = sum((money(r.get("performance_materiality")) for r in rows), ZERO)
    ceiling = (materiality * multiple).quantize(CENT)
    missing = [text(r.get("account")) for r in rows
               if dec(r.get("performance_materiality")) is None]
    findings = []
    if allocated > ceiling:
        findings.append(receipt(pid, ("over_allocated",), "CLASH",
                                f"allocated performance materiality {allocated} exceeds "
                                f"{multiple} × materiality = {ceiling}",
                                {"finding_class": "PROVED_EXCEPTION", "cycle": "planning",
                                 "allocated": allocated, "ceiling": ceiling},
                                allocated - ceiling))
    for account in missing:
        findings.append(receipt(pid, ("unallocated", account), "AMBIGUOUS",
                                f"{account} has no performance materiality allocated",
                                {"finding_class": "REFUSAL", "cycle": "planning"}))
    over_single = [text(r.get("account")) for r in rows
                   if money(r.get("performance_materiality")) > materiality]
    for account in over_single:
        findings.append(receipt(pid, ("above_materiality", account), "CLASH",
                                f"{account} performance materiality exceeds overall "
                                f"materiality {materiality}",
                                {"finding_class": "PROVED_EXCEPTION", "cycle": "planning"}))
    return findings, {"population": len(rows), "allocated": allocated,
                      "ceiling": ceiling, "headroom": ceiling - allocated,
                      "materiality": materiality, "multiple": multiple,
                      "exceptions": len(findings)}


def adjusted_trial_balance(tables: dict, policies: dict):
    pid = "fs.adjusted_trial_balance"
    tb = records(tables, "Trial_balance")
    entries = records(tables, "Adjusting_entries")
    findings = []
    by_account = {key_text(r.get("account")): r for r in tb}
    adjustments: dict[str, Decimal] = {}
    grouped: dict[str, list[dict]] = {}
    for e in entries:
        grouped.setdefault(text(e.get("entry_id")), []).append(e)
    for entry_id, lines in grouped.items():
        dr = sum((money(x.get("debit")) for x in lines), ZERO)
        cr = sum((money(x.get("credit")) for x in lines), ZERO)
        if dr != cr:
            findings.append(receipt(pid, ("unbalanced_entry", entry_id), "CLASH",
                                    f"adjusting entry {entry_id} does not balance: "
                                    f"debits {dr}, credits {cr}",
                                    {"finding_class": "PROVED_EXCEPTION",
                                     "cycle": "completion"}, dr - cr))
            continue
        for x in lines:
            account = key_text(x.get("account"))
            if account not in by_account:
                findings.append(receipt(pid, ("unknown_account", entry_id, account),
                                        "ORPHAN",
                                        f"entry {entry_id} posts to account {account}, "
                                        "which is not on the trial balance",
                                        {"finding_class": "EXPECTED_BUT_MISSING",
                                         "cycle": "completion"}))
                continue
            adjustments[account] = adjustments.get(account, ZERO) + \
                money(x.get("debit")) - money(x.get("credit"))
    adjusted_rows = []
    for account, row in by_account.items():
        before = _signed(row) or ZERO
        after = before + adjustments.get(account, ZERO)
        adjusted_rows.append({**row, "balance": after, "side": ""})
    debits = sum((r["balance"] for r in adjusted_rows if r["balance"] > 0), ZERO)
    credits = -sum((r["balance"] for r in adjusted_rows if r["balance"] < 0), ZERO)
    if debits != credits:
        findings.append(receipt(pid, ("adjusted_tb_out_of_balance",), "CLASH",
                                f"adjusted trial balance does not foot: {debits} vs {credits}",
                                {"finding_class": "PROVED_EXCEPTION", "cycle": "completion"},
                                debits - credits))
    before_fig = ratios(_totals(tb, "balance"))["figures"]
    after_fig = ratios(_totals(adjusted_rows, "balance"))["figures"]
    return findings, {
        "population": len(tb), "entries": len(grouped),
        "adjustments": {a: v for a, v in sorted(adjustments.items())},
        "adjusted_debits": debits, "adjusted_credits": credits,
        "income_before_taxes": {"unadjusted": before_fig["income_before_taxes"],
                                "adjusted": after_fig["income_before_taxes"]},
        "net_income_note": "income tax is not recomputed; adjust it by entry if needed",
        "adjusted_balances": {a: r["balance"] for a, r in sorted(
            ((key_text(r.get("account")), r) for r in adjusted_rows))},
        "exceptions": len(findings)}


SUM_COLUMNS = ("identified", "likely", "current_assets", "noncurrent_assets",
               "current_liabilities", "noncurrent_liabilities", "income_before_taxes")


LIKELY_BASES = ("total", "beyond_identified")


def _basis_shown_by(row: dict) -> str | None:
    """Which reading of "likely" the row's statement-line columns bear out:
    the largest line effect equals likely (total) or identified + likely
    (beyond identified). None when the row cannot tell them apart."""
    identified, likely = money(row.get("identified")), money(row.get("likely"))
    effect = max((abs(money(row.get(c))) for c in SUM_COLUMNS[2:]), default=ZERO)
    if not likely or not identified or not effect:
        return None
    as_total, as_beyond = effect == abs(likely), effect == abs(identified + likely)
    return "total" if as_total and not as_beyond else (
        "beyond_identified" if as_beyond and not as_total else None)


def uncorrected_misstatements(tables: dict, policies: dict):
    pid = "completion.uncorrected_misstatements"
    materiality = policy_decimal(policies, "materiality")
    rows = records(tables, "Misstatements")
    findings = []
    # "Likely" is either the whole likely misstatement or the projection
    # beyond the identified amount; summaries use both. The partner's
    # setting decides; failing that, the rows' own line columns may show it.
    chosen = text(policies.get("misstatement_likely_basis")).lower()
    if chosen and chosen not in LIKELY_BASES:
        raise PolicyError("misstatement_likely_basis must be 'total' or "
                          "'beyond_identified'")
    # Descriptions need not be unique. Keep every row's evidence so two rows
    # called (for example) "projection" cannot overwrite one another and hide
    # a conflict about what Likely means.
    shown = [(text(r.get("description")), b)
             for r in rows if (b := _basis_shown_by(r))]
    shown_bases = {b for _, b in shown}
    if chosen:
        basis, basis_source = chosen, "policy"
        for description, b in sorted(set(shown)):
            if b != chosen:
                findings.append(receipt(
                    pid, ("likely_basis_contradicted", description), "TENSION",
                    f"'{description}': its statement-line amounts read likely as "
                    f"{b.replace('_', ' ')}, not {chosen.replace('_', ' ')} as set",
                    {"finding_class": "CONJECTURE", "cycle": "completion"}))
    elif len(shown_bases) == 1:
        basis, basis_source = next(iter(shown_bases)), "statement-line columns"
    else:
        basis, basis_source = "total", "assumed"
        if any(money(r.get("likely")) for r in rows):
            findings.append(receipt(
                pid, ("likely_basis_unknown",), "AMBIGUOUS",
                "the summary does not show whether 'likely' is the whole likely "
                "misstatement or the amount beyond identified; it was read as the "
                "whole — set misstatement_likely_basis",
                {"finding_class": "CONJECTURE", "cycle": "completion"}))
    if basis == "beyond_identified":
        rows = [{**r, "likely": money(r.get("identified")) + money(r.get("likely"))}
                for r in rows]
    totals = {c: sum((money(r.get(c)) for r in rows), ZERO) for c in SUM_COLUMNS}
    remaining = {c: (materiality - abs(v)).quantize(CENT) for c, v in totals.items()}
    for column in SUM_COLUMNS[2:]:
        if abs(totals[column]) >= materiality:
            findings.append(receipt(
                pid, ("material", column), "CLASH",
                f"uncorrected misstatements in {column.replace('_', ' ')} total "
                f"{totals[column]}, at or above materiality {materiality}",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "completion",
                 "total": totals[column], "materiality": materiality,
                 "limits": "the opinion decision remains the partner's"},
                totals[column]))
    # Whether the remaining amount is adequate is the auditor's judgment; the
    # engine reports it (stats.remaining) and draws no line of its own.
    for r in rows:
        identified, likely = dec(r.get("identified")), dec(r.get("likely"))
        if identified is not None and likely is not None and abs(likely) < abs(identified):
            findings.append(receipt(
                pid, ("likely_below_identified", text(r.get("description"))), "TENSION",
                f"'{text(r.get('description'))}': likely misstatement {likely} is smaller "
                f"than the identified {identified}",
                {"finding_class": "CONJECTURE", "cycle": "completion",
                 "source_rows": [source_ref("Misstatements", r, "description")]}))
    return findings, {"population": len(rows), "materiality": materiality,
                      "totals": totals, "remaining": remaining,
                      "likely_basis": basis, "likely_basis_source": basis_source,
                      "exceptions": len(findings)}


__all__ = ["LINES", "ratios", "trial_balance_analytics", "performance_materiality",
           "adjusted_trial_balance", "uncorrected_misstatements", "PolicyError"]
