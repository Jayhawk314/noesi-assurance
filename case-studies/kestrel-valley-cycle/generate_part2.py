# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Kestrel Valley, part 2 of the full case: payroll, property and equipment,
debt and equity, accruals and prepaids.

Every file ties to what is already frozen: the trial balances (generate.py)
and part 1's journal (paydays, the racking purchase, the line-of-credit
payments, the insurance premium, the fee accrual). The payroll register,
asset register and client schedules come from a payroll provider and the
client's spreadsheets, not QuickBooks; their layouts are modeled.

The key (instructor/answer_key_part2.json) is computed here in plain Decimal
arithmetic, imports nothing from Noesi, and is committed before any run.

    python case-studies/kestrel-valley-cycle/generate_part2.py
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import generate as g
from generate_payables import CUR, MONTHS, PE, PRI, bal, spread, workday

D, m, ZERO = Decimal, g.m, Decimal("0")
FY_START = date(2025, 7, 1)
CLIENT, AUDITOR = g.CLIENT, g.AUDITOR
PAYDAYS = [workday(y, mo, d) for y, mo in MONTHS for d in (15, 28)]


# ================================================================== payroll
EMPLOYEES = [  # id, name, status, hire, termination, bank account, address, weight
    ("E01", "Jo Kestrel", "active", "2015-03-01", "", "BK-10442", "9 Lindley Pl Bozeman MT 59715", 9),
    ("E02", "Ray Okafor", "active", "2017-06-12", "", "BK-20871", "31 Olive St Bozeman MT 59715", 6),
    ("E03", "Tess Hollis", "active", "2018-02-05", "", "BK-33019", "88 Babcock St Bozeman MT 59715", 5),
    ("E04", "Luis Varga", "active", "2019-09-16", "", "BK-40225", "5 Tracy Ave Bozeman MT 59715", 5),
    ("E05", "Mina Soto", "active", "2020-01-06", "", "BK-51990", "140 Durston Rd Bozeman MT 59715", 5),
    ("E06", "Carl Brandt", "active", "2020-08-03", "", "BK-60318", "22 Kagy Blvd Bozeman MT 59715", 5),
    ("E07", "Dana Merritt", "active", "2021-04-19", "", "BK-70455", "414 S Willson Ave Bozeman MT 59715", 6),
    ("E08", "Owen Pike", "active", "2021-11-01", "", "BK-81127", "63 Grand Ave Bozeman MT 59715", 4),
    ("E09", "Nell Farris", "active", "2022-03-14", "", "BK-33019", "12 Story St Bozeman MT 59715", 4),
    ("E10", "Gabe Lund", "active", "2022-07-25", "", "BK-10877", "7 Hoffman Dr Bozeman MT 59715", 4),
    ("E11", "Ivy Chen", "active", "2023-05-08", "", "BK-11904", "300 Fowler Ln Bozeman MT 59715", 4),
    ("E12", "Hank Duvall", "terminated", "2019-04-01", "2026-02-13", "BK-12603", "19 Aspen St Bozeman MT 59715", 4),
    ("E13", "Rosa Quint", "active", "2024-02-19", "", "BK-13370", "45 Cottonwood Rd Bozeman MT 59715", 4),
    ("E14", "Theo Marsh", "active", "2024-09-09", "", "BK-14029", "8 Bridger Dr Bozeman MT 59715", 4),
]
GHOST = ("E16", 3)             # paid every payday, not on the employee master
WITHHOLDING = D("0.18")


def payroll(key):
    wages = bal(CUR, "60100")
    per_day = spread(wages, [1] * 24)          # the journal's gross wages per payday
    master = {e[0]: e for e in EMPLOYEES}
    rows = []
    for n, (day, total) in enumerate(zip(PAYDAYS, per_day)):
        paid = [e for e in EMPLOYEES
                if not e[4] or day <= date.fromisoformat(e[4]) + timedelta(days=30)]
        people = [(e[0], e[7]) for e in paid] + [GHOST]
        grosses = spread(total, [w for _, w in people])
        for (emp, _), gross in zip(people, grosses):
            withheld = m(gross * WITHHOLDING)
            net = gross - withheld
            rows.append([emp, day, gross, withheld, net, f"DD-{n + 1:02d}-{emp}"])
    # one net pay keyed 100 high
    bad = next(r for r in rows if r[0] == "E05" and r[1].month == 10)
    bad[4] += m("100.00")
    terminated = master["E12"]
    late = [r for r in rows if r[0] == "E12" and r[1] > date(2026, 2, 13) + timedelta(days=15)]
    key["payroll"] = {
        "register_gross": str(sum(r[2] for r in rows)), "tb_wages_60100": str(wages),
        "difference": str(sum(r[2] for r in rows) - wages),
        "ghost_employee": {"id": GHOST[0], "payments": sum(1 for r in rows if r[0] == GHOST[0]),
                           "net_paid": str(sum(r[4] for r in rows if r[0] == GHOST[0]))},
        "paid_after_termination": {"id": "E12", "terminated": terminated[4],
                                   "grace_days": 15,
                                   "payments_beyond_grace": [str(r[1]) for r in late]},
        "shared_bank_account": ["E03", "E09"],
        "net_pay_error": {"id": "E05", "date": str(bad[1]), "over_by": "100.00"},
        "bookkeeper_address_is_a_vendor_address": {"employee": "E07 Dana Merritt",
                                                   "vendor": "DM Consulting"},
    }
    g.write_csv(CLIENT / "payroll_register_FY2026.csv",
                ["Employee ID", "Check Date", "Gross Pay", "Taxes Withheld", "Net Pay",
                 "Check Number"],
                [(r[0], r[1].isoformat(), r[2], r[3], r[4], r[5]) for r in rows])
    g.write_csv(CLIENT / "employee_master.csv",
                ["Employee ID", "Name", "Status", "Hire Date", "Termination Date",
                 "Direct Deposit Account", "Home Address"],
                [e[:7] for e in EMPLOYEES])


# ================================================================== PP&E
def months_between(a: date, b: date) -> int:
    return (b.year * 12 + b.month) - (a.year * 12 + a.month) + 1


def full_month(cost, salvage, life, acquired, start, end):
    """Straight line, full month in the month acquired: depreciation in
    [start, end] and accumulated to end."""
    monthly = (cost - salvage) / (life * 12)
    first, last = acquired, acquired.replace(year=acquired.year + life) - timedelta(days=1)
    def months(to):
        if to < first:
            return 0
        return min(months_between(first, to), life * 12)
    period = months(end) - (months(start - timedelta(days=1)) if start > first else 0)
    return m(monthly * period), m(monthly * months(end))


def ppe(key):
    assets = [  # id, description, acquired, cost, life, salvage
        ["FA-01", "Warehouse racking", date(2025, 8, 12), m("14500"), 10, ZERO],
        ["FA-02", "Forklift", date(2021, 3, 15), m("32000"), 10, ZERO],
        ["FA-03", "Delivery van", date(2022, 9, 1), m("42000"), 7, ZERO],
        ["FA-04", "Steel shelving", date(2019, 7, 1), m("28000"), 5, ZERO],
        ["FA-05", "Computers", date(2023, 1, 10), m("12800"), 3, ZERO],
        ["FA-06", "Office furniture", date(2020, 5, 1), m("9500"), 7, ZERO],
    ]
    cost_end = -(-bal(CUR, "15000"))
    lease_cost = cost_end - sum(a[3] for a in assets)
    target_dep = bal(CUR, "64000")
    target_acc = -bal(CUR, "15900")
    rows, dep_sum, acc_sum = [], ZERO, ZERO
    for a in assets:
        dep, acc = full_month(a[3], a[5], a[4], a[2], FY_START, PE)
        rows.append(a + [dep, acc])
    overstated = m("300.00")
    for r in rows:
        if r[0] == "FA-06":
            r[6] += overstated
            r[7] += overstated
    dep_sum = sum(r[6] for r in rows)
    acc_sum = sum(r[7] for r in rows)
    # the leasehold improvements carry the remainder (salvage set so its
    # straight-line depreciation is exact)
    lease_dep = target_dep - dep_sum
    life = 15
    salvage = lease_cost - lease_dep * life
    lease_acc = target_acc - acc_sum
    assert ZERO < lease_dep and ZERO <= salvage < lease_cost, (lease_dep, salvage)
    assert ZERO < lease_acc <= lease_cost - salvage, lease_acc
    rows.append(["FA-07", "Leasehold improvements", date(2018, 7, 1), lease_cost, life,
                 salvage, lease_dep, lease_acc])
    assert sum(r[3] for r in rows) == cost_end
    assert sum(r[6] for r in rows) == target_dep and sum(r[7] for r in rows) == target_acc
    g.write_csv(CLIENT / "fixed_asset_register.csv",
                ["Asset ID", "Description", "Placed in Service", "Cost", "Useful Life",
                 "Salvage Value", "Method", "Current Year Depreciation",
                 "Accumulated Depreciation"],
                [(r[0], r[1], r[2].isoformat(), r[3], r[4], r[5], "SL", r[6], r[7])
                 for r in rows])
    g.write_csv(AUDITOR / "additions_vouching.csv",
                ["Asset ID", "Invoice Amount", "Capitalize", "Document"],
                [("FA-01", m("14500"), "yes", "Rocky Mountain Racking inv 7731")])
    key["ppe"] = {
        "beginning_cost": str(-(-bal(PRI, "15000"))), "additions": "14500.00",
        "disposals": "0.00", "ending_cost": str(cost_end),
        "depreciation_register": str(target_dep), "accumulated": str(target_acc),
        "convention": "full_month",
        "depreciation_differs": {"asset": "FA-06", "recorded": str(rows[5][6]),
                                 "recomputed": str(rows[5][6] - overstated),
                                 "difference": str(overstated)},
        "leasehold_salvage": str(salvage),
        "additions_vouched": "FA-01 in full; no exceptions",
    }


# ================================================================== debt, equity
def debt_equity(key):
    begin, end = -bal(PRI, "23000"), -bal(CUR, "23000")
    interest = bal(CUR, "69000")
    rate = D("0.075")
    expected = m((begin + end) / 2 * rate)
    g.write_csv(CLIENT / "debt_schedule.csv",
                ["Loan", "Lender", "Beginning Balance", "Advances", "Principal Payments",
                 "Ending Balance", "Interest Rate", "Interest Expense"],
                [("LOC-2208", "First Prairie Bank", begin, m("0"), begin - end, end,
                  "7.5%", interest)])
    # Covenant: current ratio at least 1.20 (the auditor's reading of the agreement)
    current = ["10100", "10200", "10300", "10900", "11000", "11900", "12100", "13000"]
    liabilities = ["20000", "21000", "22000", "23000"]
    ca = abs(sum(bal(CUR, n) for n in current))
    cl = abs(sum(bal(CUR, n) for n in liabilities))
    ratio = (ca / cl).quantize(D("0.0001"), rounding=ROUND_HALF_UP)
    g.write_csv(AUDITOR / "covenants.csv",
                ["Covenant", "Numerator Accounts", "Denominator Accounts", "Operator",
                 "Threshold"],
                [("Current ratio", ", ".join(current), ", ".join(liabilities), ">=",
                  "1.20")])
    capital = -bal(CUR, "30100")
    re_begin, re_end = -bal(PRI, "32000"), -bal(CUR, "32000")
    prior_ni = -sum(bal(PRI, n) for n in (x[0] for x in g.TB) if n[0] in "456")
    closed_dist = bal(PRI, "31000")
    assert re_begin + prior_ni - closed_dist == re_end
    g.write_csv(CLIENT / "equity_rollforward.csv",
                ["Component", "Account", "Beginning", "Additions", "Reductions", "Ending"],
                [("Members' capital", "30100", capital, m("5000"), m("0"), m("65000")),
                 ("Retained earnings", "32000", re_begin, prior_ni, closed_dist, re_end)])
    key["debt_equity"] = {
        "loan": {"beginning": str(begin), "repaid": str(begin - end), "ending": str(end),
                 "interest_recorded": str(interest), "rate": "7.5%",
                 "interest_expected_avg_balance": str(expected),
                 "interest_difference_pct": str(((interest - expected) / expected * 100)
                                                .quantize(D("0.1")))},
        "covenant_current_ratio": {"current_assets": str(ca), "current_liabilities": str(cl),
                                   "ratio": str(ratio), "minimum": "1.20",
                                   "breached": ratio < D("1.20")},
        "equity": {"members_capital": "schedule adds a 5,000 contribution the ledger "
                                      "does not have: foots (60,000 + 5,000 = 65,000) "
                                      "but does not tie (TB 60,000.00)",
                   "retained_earnings": "foots and ties"},
    }


# ================================================================== accruals
def accruals(key):
    ins_total, ins_start, ins_end = m("26710"), date(2025, 10, 1), date(2026, 9, 30)
    days = (ins_end - ins_start).days + 1
    ins_expected = m(ins_total * (ins_end - PE).days / days)
    ins_recorded = m("7000.00")
    software = -(-bal(CUR, "13000")) - ins_recorded
    fee_total, fee_start, fee_end = m("18000"), date(2026, 4, 1), date(2026, 9, 30)
    fdays = (fee_end - fee_start).days + 1
    fee_expected = m(fee_total * ((PE - fee_start).days + 1) / fdays)
    accrued_end, accrued_begin = -bal(CUR, "21000"), -bal(PRI, "21000")
    fee_end_bal = accrued_end - m("30760")
    fee_begin = accrued_begin - m("30760")
    prepaid_begin = bal(PRI, "13000")
    rows = [
        ("Insurance premium", "prepaid", "13000", prepaid_begin, ins_total,
         prepaid_begin + ins_total - ins_recorded, ins_recorded, ins_total,
         ins_start.isoformat(), ins_end.isoformat(), ""),
        ("Software and dues", "prepaid", "13000", m("0"), software, m("0"), software,
         "", "", "", ""),
        ("Accrued payroll", "accrued expense", "21000", m("30760"), m("0"), m("0"),
         m("30760"), "", "", "", ""),
        ("Audit fee", "accrued expense", "21000", fee_begin, fee_end_bal - fee_begin,
         m("0"), fee_end_bal, fee_total, fee_start.isoformat(), fee_end.isoformat(),
         m("0")),
    ]
    g.write_csv(CLIENT / "accruals_prepaids_schedule.csv",
                ["Item", "Type", "Account", "Beginning", "Additions", "Reductions",
                 "Ending", "Contract Amount", "Service Start", "Service End",
                 "Billed to Date"], rows)
    assert ins_recorded + software == bal(CUR, "13000")
    assert m("30760") + fee_end_bal == accrued_end
    key["accruals"] = {
        "ties": {"13000": str(bal(CUR, "13000")), "21000": str(accrued_end)},
        "insurance_recompute": {"recorded": str(ins_recorded),
                                "expected": str(ins_expected),
                                "difference": str(ins_recorded - ins_expected)},
        "audit_fee_recompute": {"recorded": str(fee_end_bal), "expected": str(fee_expected),
                                "difference": str(fee_end_bal - fee_expected)},
        "not_recomputed": ["Software and dues", "Accrued payroll"],
        "stale": "Accrued payroll unchanged all year (30,760): ask why",
    }


def main():
    key = {"case_part": "2 of 3: payroll, PP&E, debt and equity, accruals",
           "period": {"start": FY_START.isoformat(), "end": PE.isoformat()},
           "policies": {"payroll_expense_accounts": "60100",
                        "payroll_final_pay_days": "15", "ppe_cost_accounts": "15000",
                        "ppe_accumulated_depreciation_accounts": "15900",
                        "ppe_depreciation_convention": "full_month",
                        "ppe_depreciation_accounts": "64000", "debt_accounts": "23000",
                        "debt_interest_tolerance_pct": "10",
                        "debt_interest_accounts": "69000"}}
    payroll(key)
    ppe(key)
    debt_equity(key)
    accruals(key)
    (g.INSTRUCTOR / "answer_key_part2.json").write_text(
        json.dumps(key, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(key, indent=1, default=str)[:3000])


if __name__ == "__main__":
    main()
