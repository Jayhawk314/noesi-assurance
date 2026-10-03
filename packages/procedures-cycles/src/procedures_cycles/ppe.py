# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Property and equipment: register rollforward to the ledger, depreciation
recompute, and additions vouching.

The fixed-asset register is the client's subledger. The depreciation
convention (full month, half year) is the client's accounting policy, which
the auditor records as a policy rather than the engine assuming one.
Straight line and declining balance are recomputed; other methods (units of
production, sum of the years' digits) are listed as not recomputed.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from procedures_cycles.common import (
    ZERO, PolicyError, dec, day, key_text, money, period_bounds, period_start,
    policy_date, receipt, records, source_ref, text,
)
from procedures_cycles.statements import _signed

REGISTER, VOUCHING = "Fixed_assets", "Additions_vouching"


def _accounts(policies: dict, name: str) -> list[str] | None:
    raw = text(policies.get(name))
    return [key_text(a) for a in raw.replace(";", ",").split(",") if a.strip()] or None


def _tb(tables: dict) -> dict[str, dict]:
    return {key_text(r.get("account")): r for r in records(tables, "Trial_balance")}


def rollforward(tables: dict, policies: dict):
    pid = "ppe.rollforward"
    start, pe = period_bounds(policies)
    cost_accounts = _accounts(policies, "ppe_cost_accounts")
    if cost_accounts is None:
        raise PolicyError("policy 'ppe_cost_accounts' is not set; name the trial "
                          "balance accounts that carry asset cost")
    accum_accounts = _accounts(policies, "ppe_accumulated_depreciation_accounts")
    beginning = additions = disposals = ending = accumulated = ZERO
    undated = []
    assets = records(tables, REGISTER)
    for asset in assets:
        cost = money(asset.get("cost"))
        acquired, disposed = day(asset.get("acquired_date")), day(asset.get("disposal_date"))
        if acquired is None:
            undated.append(key_text(asset.get("asset_id")))
            continue
        held_at_start = acquired < start and (disposed is None or disposed >= start)
        if held_at_start:
            beginning += cost
        elif start <= acquired <= pe:
            additions += cost
        if disposed is not None and start <= disposed <= pe and acquired <= pe:
            disposals += cost
        if acquired <= pe and (disposed is None or disposed > pe):
            ending += cost
            accumulated += money(asset.get("accumulated_depreciation"))
    findings = []
    if undated:
        findings.append(receipt(pid, ("undated_assets",), "AMBIGUOUS",
                                f"{len(undated)} asset(s) have no acquisition date and "
                                f"are left out: {', '.join(undated[:10])}",
                                {"finding_class": "REFUSAL", "cycle": "ppe",
                                 "assets": undated}))
    tb = _tb(tables)

    def tie(label, register_total, accounts, field, sign=1):
        missing = [a for a in accounts if a not in tb]
        if missing:
            findings.append(receipt(
                pid, (label, "accounts_not_on_trial_balance"), "AMBIGUOUS",
                f"account(s) {', '.join(missing)} named for {label.replace('_', ' ')} are "
                "not on the trial balance", {"finding_class": "REFUSAL", "cycle": "ppe"}))
        values = [_signed(tb[a], field) for a in accounts if a in tb]
        if any(v is None for v in values):
            return None
        ledger = money(sum(values, ZERO)) * sign
        gap = money(register_total - ledger)
        if gap != 0:
            findings.append(receipt(
                pid, (label, "register_to_ledger"), "CLASH",
                f"{label.replace('_', ' ')}: the register gives {money(register_total)}, "
                f"the trial balance {ledger} (difference {gap})",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "ppe",
                 "register": register_total, "ledger": ledger, "difference": gap}, gap))
        return ledger

    ledger_cost = tie("ending_cost", ending, cost_accounts, "balance")
    if any(tb[a].get("prior_balance") not in (None, "") for a in cost_accounts if a in tb):
        tie("beginning_cost", beginning, cost_accounts, "prior_balance")
    if accum_accounts:
        tie("accumulated_depreciation", accumulated, accum_accounts, "balance", sign=-1)
    arithmetic = money(beginning + additions - disposals - ending)
    stats = {"population": len(assets), "period_start": start, "period_end": pe,
             "beginning_cost": beginning, "additions": additions,
             "disposals": disposals, "ending_cost": ending,
             "rollforward_difference": arithmetic,
             "accumulated_depreciation": accumulated, "ledger_cost": ledger_cost,
             "exceptions": len(findings)}
    return findings, stats


def _years_back(pe: date, years: int) -> date:
    try:
        return pe.replace(year=pe.year - years)
    except ValueError:                       # 29 February
        return pe.replace(year=pe.year - years, day=28)


def _fiscal_index(d: date, start: date) -> int:
    """0 for the current period (from start), 1 for the twelve months before
    it, and so on."""
    if d >= start:
        return 0
    prior_end, i = start - timedelta(days=1), 1
    while d < period_start(_years_back(prior_end, i - 1)):
        i += 1
    return i


def _months(d: date) -> int:
    return d.year * 12 + d.month


def _period_depreciation(asset: dict, start: date, pe: date,
                         convention: str) -> Decimal | None:
    cost = money(asset.get("cost"))
    salvage = money(asset.get("salvage_value"))
    life = dec(asset.get("useful_life_years"))
    acquired, disposed = day(asset.get("acquired_date")), day(asset.get("disposal_date"))
    if life is None or life <= 0 or acquired is None or acquired > pe:
        return None
    annual = (cost - salvage) / life
    if convention == "full_month":
        first = _months(acquired)                          # month acquired counts
        last = first + int(life * 12) - 1                   # final month of life
        if disposed is not None:
            last = min(last, _months(disposed) - 1)         # month of disposal does not
        lo, hi = max(first, _months(start)), min(last, _months(pe))
        months = max(0, hi - lo + 1)
        return money(annual * months / 12)
    if convention == "half_year":
        k = _fiscal_index(acquired, start)                  # periods since acquisition
        if disposed is not None and disposed < start:
            return ZERO
        if k > life:
            return ZERO
        fraction = Decimal("0.5") if k == 0 or k == life else Decimal("1")
        if disposed is not None and start <= disposed <= pe and k > 0:
            fraction = Decimal("0.5")
        return money(annual * fraction)
    raise PolicyError(f"depreciation convention {convention!r} is not supported; "
                      "use full_month or half_year")


_STRAIGHT_LINE = ("sl", "straight line", "straightline")
_DECLINING = {"ddb": Decimal("2"), "double declining": Decimal("2"),
              "double declining balance": Decimal("2"), "200% declining balance": Decimal("2"),
              "200 db": Decimal("2"), "150% declining balance": Decimal("1.5"),
              "150 db": Decimal("1.5"), "150db": Decimal("1.5")}


def _declining_factor(method: str, policies: dict) -> Decimal | None:
    """The declining-balance factor a method names (double declining is 2,
    150% is 1.5); a plain "declining balance" takes the auditor's policy
    ppe_declining_balance_factor. None when neither says."""
    if method in _DECLINING:
        return _DECLINING[method]
    if method in ("db", "declining balance"):
        return dec(policies.get("ppe_declining_balance_factor"))
    return None


def _declining_balance(asset: dict, start: date, pe: date, convention: str,
                       factor: Decimal) -> Decimal | None:
    """The period's declining-balance depreciation: factor / life times the
    book value at the start of the period, never below salvage. The opening
    book value is cost less the opening accumulated depreciation, which is
    the register's ending accumulated depreciation less this period's
    recorded expense (so the recompute tests the rate and the base, not the
    rollforward). The year of acquisition and of disposal follow the
    convention: full months held, or half a year. No switch to straight line
    is made in later years (stated limit)."""
    cost, salvage = money(asset.get("cost")), money(asset.get("salvage_value"))
    life = dec(asset.get("useful_life_years"))
    acquired, disposed = day(asset.get("acquired_date")), day(asset.get("disposal_date"))
    ending_acc, expense = dec(asset.get("accumulated_depreciation")), dec(
        asset.get("depreciation_expense"))
    if (life is None or life <= 0 or acquired is None or acquired > pe
            or (disposed is not None and disposed < start)):
        return None
    if acquired >= start:
        base = cost
    elif ending_acc is None or expense is None:
        return None
    else:
        base = cost - (money(ending_acc) - money(expense))
    fraction = Decimal("1")
    if convention == "full_month":
        first = max(_months(acquired), _months(start))
        last = _months(pe) if disposed is None or disposed > pe else _months(disposed) - 1
        fraction = Decimal(max(0, last - first + 1)) / 12
    elif convention == "half_year":
        if acquired >= start or (disposed is not None and disposed <= pe):
            fraction = Decimal("0.5")
    else:
        raise PolicyError(f"depreciation convention {convention!r} is not supported; "
                          "use full_month or half_year")
    amount = base * factor / life * fraction
    return money(max(ZERO, min(amount, base - salvage)))


def depreciation_recompute(tables: dict, policies: dict):
    pid = "ppe.depreciation_recompute"
    start, pe = period_bounds(policies)
    convention = text(policies.get("ppe_depreciation_convention")).lower()
    if not convention:
        raise PolicyError("policy 'ppe_depreciation_convention' is not set "
                          "(full_month or half_year: the client's accounting policy)")
    tolerance = dec(policies.get("ppe_rounding_tolerance")) or Decimal("1.00")
    findings, not_recomputed = [], []
    recomputed_total = recorded_total = register_total = ZERO
    assets = records(tables, REGISTER)
    for asset in assets:
        aid = key_text(asset.get("asset_id"))
        register_total += money(asset.get("depreciation_expense"))
        method = text(asset.get("method")).lower().replace("-", " ")
        src = [source_ref(REGISTER, asset, "asset_id")]
        cost, salvage = money(asset.get("cost")), money(asset.get("salvage_value"))
        accumulated = dec(asset.get("accumulated_depreciation"))
        if accumulated is not None and money(accumulated) > cost - salvage:
            findings.append(receipt(
                pid, (aid, "depreciated_below_salvage"), "CLASH",
                f"asset {aid}: accumulated depreciation {money(accumulated)} exceeds cost "
                f"less salvage {cost - salvage}",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "ppe", "source_rows": src},
                money(accumulated) - (cost - salvage)))
        if method and method not in _STRAIGHT_LINE:
            factor = _declining_factor(method, policies)
            if factor is None or factor <= 0:
                not_recomputed.append(aid)
                continue
            expected = _declining_balance(asset, start, pe, convention, factor)
            basis = f"declining balance at {factor}x"
        else:
            expected = _period_depreciation(asset, start, pe, convention)
            basis = "straight line"
        recorded = dec(asset.get("depreciation_expense"))
        if expected is None or recorded is None:
            not_recomputed.append(aid)
            continue
        recomputed_total += expected
        recorded_total += money(recorded)
        gap = money(recorded) - expected
        if abs(gap) > tolerance:
            findings.append(receipt(
                pid, (aid, "depreciation_differs"), "CLASH",
                f"asset {aid}: the register records {money(recorded)} depreciation for "
                f"the period; {basis} ({convention.replace('_', ' ')}) gives "
                f"{expected} (difference {gap})",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "ppe", "recorded": recorded,
                 "recomputed": expected, "source_rows": src}, gap))
    accounts = _accounts(policies, "ppe_depreciation_accounts")
    ledger = None
    if accounts:
        tb = _tb(tables)
        ledger = money(sum((_signed(tb[a]) or ZERO for a in accounts if a in tb), ZERO))
        if abs(ledger - register_total) > tolerance:
            findings.append(receipt(
                pid, ("depreciation_expense", "register_to_ledger"), "CLASH",
                f"depreciation expense: the register totals {register_total}, the trial "
                f"balance {ledger}", {"finding_class": "PROVED_EXCEPTION", "cycle": "ppe",
                                      "register": register_total, "ledger": ledger},
                ledger - register_total))
    stats = {"population": len(assets), "convention": convention,
             "rounding_tolerance": tolerance, "recomputed_total": recomputed_total,
             "recorded_total": recorded_total, "register_total": register_total,
             "ledger_depreciation": ledger,
             "not_recomputed": not_recomputed, "exceptions": len(findings)}
    return findings, stats


def additions_vouching(tables: dict, policies: dict):
    pid = "ppe.additions_vouching"
    start, pe = period_bounds(policies)
    threshold = dec(policies.get("ppe_vouch_threshold"))
    additions = {key_text(a.get("asset_id")): a for a in records(tables, REGISTER)
                 if (d := day(a.get("acquired_date"))) is not None and start <= d <= pe}
    vouched = {}
    findings = []
    for v in records(tables, VOUCHING):
        aid = key_text(v.get("asset_id"))
        vouched[aid] = v
        src = [source_ref(VOUCHING, v, "asset_id")]
        asset = additions.get(aid)
        if asset is None:
            findings.append(receipt(
                pid, (aid, "vouched_but_not_an_addition"), "ORPHAN",
                f"asset {aid} was vouched but is not a period addition in the register",
                {"finding_class": "EXPECTED_BUT_MISSING", "cycle": "ppe",
                 "source_rows": src}))
            continue
        recorded = money(asset.get("cost"))
        support = dec(v.get("vouched_amount"))
        if support is not None and money(support) != recorded:
            findings.append(receipt(
                pid, (aid, "cost_differs"), "CLASH",
                f"addition {aid}: recorded at {recorded}, the invoice supports "
                f"{money(support)}", {"finding_class": "PROVED_EXCEPTION", "cycle": "ppe",
                                      "recorded": recorded, "supported": support,
                                      "source_rows": src}, recorded - money(support)))
        if text(v.get("capitalize")).lower() in ("no", "n", "false", "expense"):
            findings.append(receipt(
                pid, (aid, "should_be_expensed"), "CLASH",
                f"addition {aid} ({recorded}) is a repair or expense item, not an asset: "
                f"{text(v.get('document')) or 'per the auditor'}",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "ppe",
                 "assertion": "classification", "source_rows": src}, recorded))
    unvouched_value = ZERO
    for aid, asset in sorted(additions.items()):
        if aid in vouched:
            continue
        cost = money(asset.get("cost"))
        unvouched_value += cost
        if threshold is not None and cost >= threshold:
            findings.append(receipt(
                pid, (aid, "not_vouched_above_threshold"), "TENSION",
                f"addition {aid} ({cost}) is at or above {threshold} and was not vouched",
                {"finding_class": "EXPECTED_BUT_MISSING", "cycle": "ppe"}, cost))
    total = sum((money(a.get("cost")) for a in additions.values()), ZERO)
    stats = {"population": len(additions), "additions_value": total,
             "vouched": len([a for a in additions if a in vouched]),
             "unvouched_value": unvouched_value,
             "coverage": (str(((total - unvouched_value) / total).quantize(Decimal("0.0001")))
                          if total else None),
             "vouch_threshold": threshold, "exceptions": len(findings)}
    return findings, stats
