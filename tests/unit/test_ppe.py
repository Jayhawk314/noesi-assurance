# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Property and equipment: rollforward, depreciation recompute, additions vouching.

Year ends 2025-12-31 (period 2025-01-01 to 2025-12-31). Figures are worked by
hand in the comments.
"""

from datetime import date
from decimal import Decimal as D

import pytest

from procedures_cycles.common import PolicyError
from procedures_cycles.engines import execute_procedure

PE = "2025-12-31"


def asset(aid, cost, acquired, life, dep, accum, *, disposed=None, method="SL",
          salvage="0"):
    return {"asset_id": aid, "cost": D(cost), "acquired_date": date.fromisoformat(acquired),
            "useful_life_years": life, "depreciation_expense": D(dep),
            "accumulated_depreciation": D(accum), "salvage_value": D(salvage),
            "method": method,
            "disposal_date": date.fromisoformat(disposed) if disposed else None}


REGISTER = [
    # 12000/5 = 2400 a year; Jan 2022-Dec 2025 = 48 months -> 9600
    asset("A1", "12000", "2022-01-15", "5", "2400.00", "9600.00"),
    # addition: Apr-Dec = 9 months of 1200 -> 900
    asset("A2", "6000", "2025-04-10", "5", "900.00", "900.00"),
    # life ends Feb 2025: Jan-Feb = 2 months of 600 -> 100; recorded 600;
    # accumulated 3100 exceeds cost 3000
    asset("A3", "3000", "2020-03-01", "5", "600.00", "3100.00"),
    # disposed Jul 2025: Jan-Jun = 6 months of 800 -> 400
    asset("A4", "8000", "2019-06-01", "10", "400.00", "5200.00", disposed="2025-07-20"),
    # double declining addition: 2500 x 2/5 x 4/12 (Sep-Dec) = 333.33; recorded 300
    asset("A5", "2500", "2025-09-01", "5", "300.00", "300.00", method="DDB"),
    # acquired the last day of the prior year: a full 2025 -> 1000
    asset("A6", "4000", "2024-12-31", "4", "1000.00", "1083.33"),
]
# beginning 12000+3000+8000+4000 = 27000; additions 6000+2500 = 8500;
# disposals 8000; ending 27500; accumulated (held) 9600+900+3100+300+1083.33
TB = [{"account": "1500", "balance": D("27500.00"), "prior_balance": D("27000.00")},
      {"account": "1590", "balance": D("-14983.33"), "prior_balance": D("-11000.00")},
      {"account": "6400", "balance": D("5600.00")}]
ROLL = {"period_end": PE, "ppe_cost_accounts": "1500",
        "ppe_accumulated_depreciation_accounts": "1590"}


def keys(findings):
    return {tuple(f.key[1:]) for f in findings}


def test_rollforward_ties_register_to_ledger():
    findings, stats = execute_procedure(
        "ppe.rollforward", {"Fixed_assets": REGISTER, "Trial_balance": TB}, ROLL)
    assert findings == []
    assert (stats["beginning_cost"], stats["additions"], stats["disposals"],
            stats["ending_cost"]) == ("27000.00", "8500.00", "8000.00", "27500.00")
    assert stats["accumulated_depreciation"] == "14983.33"


def test_rollforward_names_the_side_that_does_not_tie():
    tb = [dict(TB[0], balance=D("28000.00")), TB[1]]
    findings, _ = execute_procedure(
        "ppe.rollforward", {"Fixed_assets": REGISTER, "Trial_balance": tb}, ROLL)
    assert keys(findings) == {("ending_cost", "register_to_ledger")}
    assert "difference -500.00" in findings[0].reason


def test_rollforward_needs_the_cost_accounts_named():
    with pytest.raises(PolicyError, match="ppe_cost_accounts"):
        execute_procedure("ppe.rollforward",
                          {"Fixed_assets": REGISTER, "Trial_balance": TB},
                          {"period_end": PE})


def test_full_month_depreciation_recompute():
    findings, stats = execute_procedure(
        "ppe.depreciation_recompute", {"Fixed_assets": REGISTER, "Trial_balance": TB},
        {"period_end": PE, "ppe_depreciation_convention": "full_month",
         "ppe_depreciation_accounts": "6400"})
    assert keys(findings) == {("a3", "depreciation_differs"),
                              ("a3", "depreciated_below_salvage"),
                              ("a5", "depreciation_differs")}
    assert stats["not_recomputed"] == []
    assert "declining balance at 2x" in next(
        f.reason for f in findings if f.key[1:] == ("a5", "depreciation_differs"))
    # register 2400+900+600+400+300+1000 = 5600 = ledger
    assert stats["register_total"] == "5600.00"
    assert "difference 500.00" in next(
        f.reason for f in findings if f.key[2] == "depreciation_differs")


def test_half_year_convention():
    register = [
        asset("B1", "10000", "2025-03-01", "5", "1000.00", "1000.00"),   # year 0: half
        asset("B2", "10000", "2020-06-01", "5", "1000.00", "10000.00"),  # year 5: last half
        asset("B3", "10000", "2019-06-01", "5", "0.00", "10000.00"),     # beyond life
        asset("B4", "10000", "2022-02-01", "5", "1000.00", "7000.00",    # disposal year
              disposed="2025-05-01"),
        asset("B5", "10000", "2023-07-01", "5", "1500.00", "6500.00"),   # full 2000
    ]
    findings, stats = execute_procedure(
        "ppe.depreciation_recompute", {"Fixed_assets": register},
        {"period_end": PE, "ppe_depreciation_convention": "half_year"})
    assert keys(findings) == {("b5", "depreciation_differs")}
    assert stats["recomputed_total"] == "5000.00"   # 1000+1000+0+1000+2000


def test_the_convention_is_the_clients_policy_not_assumed():
    with pytest.raises(PolicyError, match="ppe_depreciation_convention"):
        execute_procedure("ppe.depreciation_recompute", {"Fixed_assets": REGISTER},
                          {"period_end": PE})


def test_additions_vouching():
    register = REGISTER + [asset("A7", "15000", "2025-11-01", "7", "357.14", "357.14")]
    vouching = [
        {"asset_id": "A2", "vouched_amount": D("6000.00"), "capitalize": "yes"},
        {"asset_id": "A5", "vouched_amount": D("2300.00"), "capitalize": "no",
         "document": "roof repair invoice"},
        {"asset_id": "A1", "vouched_amount": D("12000.00"), "capitalize": "yes"},
    ]
    findings, stats = execute_procedure(
        "ppe.additions_vouching", {"Fixed_assets": register, "Additions_vouching": vouching},
        {"period_end": PE, "ppe_vouch_threshold": "10000"})
    assert keys(findings) == {("a5", "cost_differs"), ("a5", "should_be_expensed"),
                              ("a1", "vouched_but_not_an_addition"),
                              ("a7", "not_vouched_above_threshold")}
    assert stats["additions_value"] == "23500.00"   # 6000 + 2500 + 15000
    assert stats["unvouched_value"] == "15000.00"


def test_declining_balance_on_the_opening_book_value():
    # Depth pass (2 Oct 2026). Life 5, double declining = 40% a year.
    register = [
        # held all year: opening book value 10000 - (6400 - 1440) = 5040 -> 2016;
        # recorded 1440 (the year-3 figure on 3600): differs by -576
        asset("C1", "10000", "2022-01-01", "5", "1440.00", "6400.00", method="DDB"),
        # near the end: opening value 1296 - 0 salvage... floor at salvage 1000:
        # 40% of 1296 = 518.40, but only 296 is left above salvage
        asset("C2", "10000", "2020-01-01", "5", "296.00", "9000.00", method="DDB",
              salvage="1000"),
        # 150% declining, acquired 1 Jul (full month: 6/12): 8000 x 0.3 x 0.5 = 1200
        asset("C3", "8000", "2025-07-01", "5", "1200.00", "1200.00",
              method="150% declining balance"),
        # plain "declining balance" with no factor set: not recomputed
        asset("C4", "5000", "2024-01-01", "5", "800.00", "2800.00",
              method="declining balance"),
    ]
    policies = {"period_end": PE, "ppe_depreciation_convention": "full_month"}
    findings, stats = execute_procedure(
        "ppe.depreciation_recompute", {"Fixed_assets": register}, policies)
    assert keys(findings) == {("c1", "depreciation_differs")}
    assert "gives 2016.00 (difference -576.00)" in findings[0].reason
    assert stats["not_recomputed"] == ["c4"]
    # with the auditor's factor (2), C4: opening 5000 - (2800 - 800) = 3000 -> 1200
    findings, stats = execute_procedure(
        "ppe.depreciation_recompute", {"Fixed_assets": register},
        {**policies, "ppe_declining_balance_factor": "2"})
    assert keys(findings) == {("c1", "depreciation_differs"), ("c4", "depreciation_differs")}
    assert stats["not_recomputed"] == []


def test_declining_balance_half_year_disposal():
    # disposed during the year, half-year convention: 0.5 x 40% x opening 6000 = 1200
    register = [asset("D1", "10000", "2023-01-01", "5", "1200.00", "5200.00",
                      method="double declining", disposed="2025-06-30")]
    findings, stats = execute_procedure(
        "ppe.depreciation_recompute", {"Fixed_assets": register},
        {"period_end": PE, "ppe_depreciation_convention": "half_year"})
    assert findings == [] and stats["recomputed_total"] == "1200.00"


def test_declining_balance_refuses_a_bad_factor_and_a_cleared_disposal():
    # Review 2026-10-02 batch, L2 and L3.
    plain = [asset("E1", "10000", "2024-01-01", "5", "2400.00", "6400.00",
                   method="declining balance")]
    base = {"period_end": PE, "ppe_depreciation_convention": "full_month"}
    for typed in ("200%", "2"):           # opening 10000 - 4000 = 6000 -> 2400
        findings, stats = execute_procedure(
            "ppe.depreciation_recompute", {"Fixed_assets": plain},
            {**base, "ppe_declining_balance_factor": typed})
        assert findings == [] and stats["recomputed_total"] == "2400.00", typed
    with pytest.raises(PolicyError, match="between 1 and 3"):
        execute_procedure("ppe.depreciation_recompute", {"Fixed_assets": plain},
                          {**base, "ppe_declining_balance_factor": "200"})
    # sold mid-year, accumulated depreciation cleared to 0 on the sale
    sold = [asset("E2", "10000", "2024-01-01", "5", "600.00", "0.00", method="DDB",
                  disposed="2025-06-30", salvage="1000")]
    findings, stats = execute_procedure(
        "ppe.depreciation_recompute", {"Fixed_assets": sold}, base)
    assert findings == [] and stats["not_recomputed"] == ["e2"]


def test_additions_projection_key_items_and_the_sample():
    # Depth pass (2 Oct 2026), worked by hand. Threshold 10000.
    #   K1 20000, vouched to 19500: key item, misstatement 500 (in full)
    #   S1  2000, vouched in full; S2 3000, vouched to 2700: sample 5000, misstated 300
    #   U1  5000, not vouched: stratum below the threshold is 10000
    #   projected 300 x 10000 / 5000 = 600; likely 500 + 600 = 1100
    register = [asset(a, c, "2025-03-01", "5", "0.00", "0.00")
                for a, c in (("K1", "20000"), ("S1", "2000"), ("S2", "3000"), ("U1", "5000"))]
    vouching = [{"asset_id": "K1", "vouched_amount": D("19500.00"), "capitalize": "yes"},
                {"asset_id": "S1", "vouched_amount": D("2000.00"), "capitalize": "yes"},
                {"asset_id": "S2", "vouched_amount": D("2700.00"), "capitalize": "yes"}]
    tables = {"Fixed_assets": register, "Additions_vouching": vouching}
    base = {"period_end": PE, "ppe_vouch_threshold": "10000"}
    findings, stats = execute_procedure("ppe.additions_vouching", tables,
                                        {**base, "ppe_tolerable_misstatement": "1000"})
    p = stats["projection"]
    assert (p["key_misstatement"], p["sample_value"], p["sample_misstatement"],
            p["stratum_value"], p["projected"], p["likely_misstatement"]) == (
        "500.00", "5000.00", "300.00", "10000.00", "600.00", "1100.00")
    assert ("additions", "likely_misstatement_reaches_tolerable") in keys(findings)
    findings, stats = execute_procedure("ppe.additions_vouching", tables,
                                        {**base, "ppe_tolerable_misstatement": "2000"})
    assert ("additions", "likely_misstatement_reaches_tolerable") not in keys(findings)
    assert stats["projection"]["allowance_for_sampling_risk"] == "900.00"
    # no tolerable set: shown, not compared
    findings, stats = execute_procedure("ppe.additions_vouching", tables, base)
    assert stats["projection"]["tolerable"] is None
    assert ("additions", "likely_misstatement_reaches_tolerable") not in keys(findings)
