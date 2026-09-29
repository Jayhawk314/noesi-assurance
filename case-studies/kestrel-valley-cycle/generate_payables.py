# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Kestrel Valley, part 1 of the full case: payables and the journal.

Builds the client's QuickBooks Online payables exports (Vendor Contact List,
Transaction List by Vendor, Bill Payment List, Unpaid Bills) in the layouts
of the real exports in tests/fixtures/quickbooks/, and a full-year Journal
report, all consistent with what generate.py already froze:

- the journal rolls every account from the prior-year trial balance to the
  current one (retained earnings takes the prior year's automatic close);
- June's checking activity is exactly the June bank reconciliation;
- the unpaid bills total the trial balance's Accounts Payable.

The answer key (instructor/answer_key_payables.json) is computed here with
plain Decimal arithmetic and imports nothing from Noesi. Run generate.py
first; this script reads its trial balances.

    python case-studies/kestrel-valley-cycle/generate_payables.py
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal

import openpyxl

import generate as g

D, m, ZERO = Decimal, g.m, Decimal("0")
FY_START, PE = date(2025, 7, 1), date(2026, 6, 30)
HOLIDAYS = {date(2025, 7, 4), date(2025, 9, 1), date(2025, 11, 27), date(2025, 12, 25),
            date(2026, 1, 1), date(2026, 5, 25)}
BOOKKEEPER, OWNER = "Dana Merritt", "Jo Kestrel"
MONTHS = [(2025, mo) for mo in range(7, 13)] + [(2026, mo) for mo in range(1, 7)]


def workday(y, mo, d):
    """The given day, moved forward past weekends and holidays."""
    day = date(y, mo, min(d, 28))
    while day.weekday() >= 5 or day in HOLIDAYS:
        day += timedelta(days=1)
    return day


def spread(total: Decimal, weights: list) -> list[Decimal]:
    """Split total by weights into cents; the last share takes the rounding."""
    w = [D(str(x)) for x in weights]
    parts = [m(total * x / sum(w)) for x in w[:-1]]
    return parts + [m(total) - sum(parts)]


# ------------------------------------------------------------------ inputs
def read_tb(name):
    ws = openpyxl.load_workbook(g.QBO / name).active
    out = {}
    for r in list(ws.iter_rows(values_only=True))[5:]:
        if r[0] and str(r[0])[:1].isdigit():
            out[r[0]] = m(r[1] or 0) - m(r[2] or 0)
    return out


CUR = read_tb("Trial_Balance_2026-06-30.xlsx")
PRI = read_tb("Trial_Balance_2025-06-30.xlsx")
ACCTS = {n: f"{n} {name}" for n, name, *_ in g.TB}
A = lambda n: ACCTS[n]


def bal(tb, n):
    return tb.get(A(n), ZERO)


# ------------------------------------------------------------------ vendors
VENDORS = [  # name, phone, email, contact, address, account #
    ("Moraine Cycle Components", "Phone:(406) 555-0142 ", "orders@morainecycle.com",
     "Lena  Voss", "220 Industrial Way Missoula MT 59808", "MC-7781"),
    ("Moraine Cycle Components, Inc.", "Phone:(406) 555-0142 ", "",
     "", "220 Industrial Way Missoula MT 59808", ""),
    ("Summit Tire Import", "Phone:(208) 555-0199 ", "ar@summittire.com",
     "Raj  Patel", "18 Harbor Rd Boise ID 83702", "ST-4410"),
    ("Kinetic Drivetrain Co.", "Phone:(303) 555-0167 ", "billing@kineticdt.com",
     "Maria  Lund", "5500 Brighton Blvd Denver CO 80216", "KD-2093"),
    ("Granite Peak Properties", "Phone:(406) 555-0110 ", "", "Tom  Beck",
     "12 Main St Bozeman MT 59715", "UNIT-4"),
    ("Northwestern Energy", "Phone:(888) 555-0100 ", "", "", "PO Box 9 Butte MT 59701",
     "556120"),
    ("Big Hole Insurance", "Phone:(406) 555-0133 ", "", "Ann  Cole",
     "70 W Park St Butte MT 59701", "BH-18830"),
    ("Velo Freight Lines", "Phone:(406) 555-0177 ", "ops@velofreight.com", "",
     "900 Frontage Rd Belgrade MT 59714", "VF-331"),
    ("Big Timber Office Supply", "", "", "", "3 McLeod St Big Timber MT 59011", ""),
    ("Alder & Finch CPAs", "Phone:(406) 555-0188 ", "", "Sam  Alder",
     "401 E Mendenhall St Bozeman MT 59715", ""),
    ("Tri-County Tool Rental", "", "", "", "77 Frontage Rd Belgrade MT 59714", ""),
    ("Hyalite Fabrication", "Phone:(406) 555-0121 ", "", "", "15 Rouse Ave Bozeman MT 59715",
     ""),
    ("DM Consulting", "", "", "", "414 S Willson Ave Bozeman MT 59715", ""),
    ("First Prairie Bank", "Phone:(406) 555-0101 ", "", "",
     "1 Main St Bozeman MT 59715", "LOC-2208"),
    ("Rocky Mountain Racking", "", "", "", "88 Gold Ave Billings MT 59101", ""),
    ("Idaho State Tax Commission", "", "", "", "PO Box 36 Boise ID 83722", ""),
]
DM_HOME = "414 S Willson Ave Bozeman MT 59715"   # Dana Merritt's home (part 2 payroll)


# ------------------------------------------------------------------ bills
class Book:
    def __init__(self):
        self.tx = []          # dicts: date, type, num, name, memo, lines, created, by
        self.pos = []         # purchase orders (non-posting)

    def add(self, when, kind, num, name, memo, lines, created=None, by=BOOKKEEPER):
        assert sum(a for _, a in lines) == 0, (kind, num, lines)
        self.tx.append({"date": when, "type": kind, "num": num, "name": name,
                        "memo": memo, "lines": lines, "created": created or when,
                        "by": by})


def build():
    b = Book()
    key = {}

    # ---- targets (debit-positive activity for the year)
    act = {n: bal(CUR, n) - bal(PRI, n) for n in ACCTS}
    for n in ACCTS:                      # income-statement accounts closed last year
        if n[0] in "456":
            act[n] = bal(CUR, n)
    closing_distributions = bal(PRI, "31000")          # prior distributions, a debit
    # distributions account: closed to RE on 7/1, then this year's paid
    paid_distributions = bal(CUR, "31000")

    # ---- inventory purchases: bills from three suppliers, monthly
    purchases = act["12100"] + act["50000"] + act["51000"]
    duplicate = m("18432.50")
    genuine = purchases - duplicate
    shares = {"Moraine Cycle Components": D("0.5"), "Summit Tire Import": D("0.3"),
              "Kinetic Drivetrain Co.": D("0.2")}
    bills = []   # (vendor, date, num, amount, account, memo)
    names = list(shares)
    vendor_totals = spread(genuine, [shares[v] for v in names])
    seasonal = [7, 7, 6, 5, 4, 5, 6, 8, 10, 12, 11, 9]
    po_no = 1001
    for vendor, total in zip(names, vendor_totals):
        prefix = {"Moraine Cycle Components": "MC", "Summit Tire Import": "ST",
                  "Kinetic Drivetrain Co.": "KD"}[vendor]
        for i, (amount, (y, mo)) in enumerate(zip(spread(total, seasonal), MONTHS)):
            when = workday(y, mo, 3 + i % 5)
            num = f"{prefix}-{24000 + po_no}"
            po_amount = amount
            if vendor == "Summit Tire Import" and (y, mo) == (2026, 3):
                po_amount = m(amount / D("1.12"))          # billed 12% over the PO
                key["po_overrun"] = {"vendor": vendor, "po": str(po_no),
                                     "po_amount": str(po_amount), "bill": num,
                                     "bill_amount": str(amount)}
            b.pos.append((vendor, when - timedelta(days=12), str(po_no), po_amount))
            bills.append((vendor, when, num, amount, "12100", f"PO {po_no}"))
            po_no += 1
    # the duplicate: Moraine's March invoice entered again under the look-alike vendor
    original = next(x for x in bills if x[0] == "Moraine Cycle Components"
                    and x[1].month == 3)
    dup_amount = original[3]
    duplicate_bill = ("Moraine Cycle Components, Inc.", workday(2026, 3, 17),
                      original[2], duplicate, "12100", "")
    # shift the difference so purchases stay exact
    fix = dup_amount - duplicate
    bills[bills.index(original)] = original[:3] + (dup_amount,) + original[4:]
    bills.append(duplicate_bill)
    key["duplicate_bill"] = {"vendor": duplicate_bill[0], "twin_of": original[0],
                             "invoice": original[2], "original_amount": str(dup_amount),
                             "duplicate_amount": str(duplicate),
                             "original_date": original[1].isoformat(),
                             "duplicate_date": duplicate_bill[1].isoformat()}
    assert fix == dup_amount - duplicate

    # ---- expense bills
    def monthly(vendor, account, total, day, memo, num_fmt, skip_num=()):
        for i, (amount, (y, mo)) in enumerate(zip(spread(total, [1] * 12), MONTHS)):
            num = "" if i in skip_num else num_fmt.format(i=i + 1, y=y, mo=mo)
            bills.append((vendor, workday(y, mo, day), num, amount, account, memo))

    monthly("Granite Peak Properties", "61000", act["61000"], 1, "Warehouse rent",
            "R-{y}{mo:02d}")
    # utility bills carry no invoice number twice (recipe quarantines them)
    monthly("Northwestern Energy", "62000", act["62000"], 12, "Electric and gas",
            "NWE-{y}{mo:02d}", skip_num=(4, 9))
    key["bills_without_number"] = [
        {"vendor": x[0], "date": x[1].isoformat(), "amount": str(x[3])}
        for x in bills if x[0] == "Northwestern Energy" and not x[2]]
    # insurance: one annual premium billed to prepaid, amortized monthly
    premium = act["63000"] + act["13000"]
    bills.append(("Big Hole Insurance", workday(2025, 7, 1), "BH-26-001", premium,
                  "13000", "Annual liability and property premium"))
    manual_reclass = m("612.00")
    tool_rental = m("3100.00")
    monthly("Velo Freight Lines", "66000", act["66000"] - manual_reclass - tool_rental, 20,
            "Freight out", "VF-{i:03d}")
    # tool rental (the uncleared June check 4421) is delivery equipment: freight
    split = [m("2450.00"), m("2475.00"), m("2400.00")]
    monthly("Big Timber Office Supply", "67000",
            act["67000"] + manual_reclass - sum(split), 8, "Office supplies",
            "BT-{i:04d}")
    bills.append(("Tri-County Tool Rental", workday(2026, 6, 1), "TC-8812", tool_rental,
                  "66000", "Delivery equipment rental"))
    for d, amount, num in zip((3, 4, 6), split, ("HF-301", "HF-302", "HF-303")):
        bills.append(("Hyalite Fabrication", date(2025, 11, d), num, amount, "67000",
                      "Display fixtures"))
    key["split_bills"] = {"vendor": "Hyalite Fabrication", "approval_limit": "2500.00",
                          "bills": [str(x) for x in split], "total": str(sum(split))}
    accrued_fees = -act["21000"]                     # year-end accrual by journal entry
    consulting = m("4500.00")                        # DM Consulting checks, no bills
    fees = act["68000"] - accrued_fees - consulting
    june_fee = m("1870.00")                          # paid short by check 4425
    fee_bills = spread(fees - june_fee, [3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]) + [june_fee]
    for i, (amount, (y, mo)) in enumerate(zip(fee_bills, MONTHS)):
        num = f"AF-{2025 + (mo < 7)}-{i + 1:02d}"
        when = date(2026, 6, 26) if (y, mo) == (2026, 6) else workday(y, mo, 5)
        bills.append(("Alder & Finch CPAs", when, num, amount, "68000", "Accounting"))
    assert all(x[3] > 0 for x in bills), [x for x in bills if x[3] <= 0]

    # ---- payments: by vendor, June fixed by the bank reconciliation
    june_checks = {  # num: (vendor, date, amount) from generate.py's reconciliation
        c[2]: c for c in g.CLEARED_CHECKS + g.UNCLEARED_CHECKS if c[2]}
    begin_ap = {"Moraine Cycle Components": m("121400.00"),
                "Summit Tire Import": m("72380.41"), "Kinetic Drivetrain Co.": m("39610.25"),
                "Velo Freight Lines": m("7890.00"), "Northwestern Energy": ZERO,
                "Big Timber Office Supply": m("625.00")}
    begin_ap["Granite Peak Properties"] = -bal(PRI, "20000") - sum(begin_ap.values())
    assert begin_ap["Granite Peak Properties"] >= 0
    # year-end open bills per vendor (sum = TB Accounts Payable)
    end_ap = {"Summit Tire Import": None, "Kinetic Drivetrain Co.": None,
              "Moraine Cycle Components": None, "Alder & Finch CPAs": m("90.00"),
              "Tri-County Tool Rental": ZERO, "Velo Freight Lines": None}
    ap_end = -bal(CUR, "20000")
    last = {v: [x for x in bills if x[0] == v and x[1].month in (5, 6)]
            for v in ("Summit Tire Import", "Kinetic Drivetrain Co.", "Velo Freight Lines")}
    end_ap["Velo Freight Lines"] = sum(x[3] for x in last["Velo Freight Lines"]
                                       if x[1].month == 6)
    end_ap["Summit Tire Import"] = sum(x[3] for x in last["Summit Tire Import"]
                                       if x[1].month == 6)
    end_ap["Kinetic Drivetrain Co."] = sum(x[3] for x in last["Kinetic Drivetrain Co."]
                                           if x[1].month == 6)
    end_ap["Moraine Cycle Components"] = ap_end - sum(v for k, v in end_ap.items()
                                                      if k != "Moraine Cycle Components")
    assert end_ap["Moraine Cycle Components"] > 0, end_ap

    payments = []   # (vendor, date, num, amount)
    billed = {}
    for v, *_rest in bills:
        billed[v] = billed.get(v, ZERO) + _rest[2]
    for vendor in sorted(billed):
        due = begin_ap.get(vendor, ZERO) + billed[vendor] - end_ap.get(vendor, ZERO)
        fixed = [(c[2], c[0], c[4]) for c in june_checks.values() if c[3] == vendor]
        # (num, date, amount): the June checks as the reconciliation lists them
        june = [(n, date(2026, int(d[:2]), int(d[3:5])), m(a)) for n, d, a in fixed]
        rest = due - sum(a for *_, a in june)
        if vendor in ("Hyalite Fabrication",):
            for d, amount in zip((14, 14, 14), split):
                payments.append((vendor, date(2025, 11, d), None, amount))
            continue
        if vendor == "Moraine Cycle Components, Inc.":
            payments.append((vendor, workday(2026, 4, 2), None, duplicate))
            continue
        months = MONTHS[:11]
        parts = spread(rest, [1] * len(months)) if rest else []
        for amount, (y, mo) in zip(parts, months):
            if amount:
                payments.append((vendor, workday(y, mo, 18), None, amount))
        for n, d, a in june:
            payments.append((vendor, d, n, a))
    assert all(p[3] > 0 for p in payments), [p for p in payments if p[3] <= 0]
    alder_june = [p for p in payments if p[0] == "Alder & Finch CPAs" and p[2] == "4425"]
    assert alder_june and alder_june[0][3] == m("1780.00")

    # ---- post bills and payments to the journal
    for vendor, when, num, amount, account, memo in sorted(bills, key=lambda x: x[1]):
        b.add(when, "Bill", num, vendor, memo, [(account, amount), ("20000", -amount)])
    for vendor, when, num, amount in sorted(payments, key=lambda x: x[1]):
        b.add(when, "Bill Payment (Check)", num, vendor, "", [("20000", amount),
                                                               ("10100", -amount)])
    # checks paid without a bill (not in the bill payment list)
    for mo, amount in ((9, "1500.00"), (12, "1500.00"), (3, "1500.00")):
        y = 2025 if mo >= 7 else 2026
        b.add(workday(y, mo, 22), "Check", None, "DM Consulting",
              "Consulting", [("68000", m(amount)), ("10100", -m(amount))])
    key["checks_without_bills"] = {"vendor": "DM Consulting", "total": "4500.00",
                                   "address_matches": "the bookkeeper's home address"}

    # ---- sales, returns, collections, sales tax
    customers = [c[0] for c in g.AGING]
    sales = -act["40000"]
    tax_collected = m("118436.20")
    returns = act["40500"]
    write_offs = act["11900"] + act["65000"]           # allowance debits
    collections = sales + tax_collected - returns - write_offs - act["11000"]
    month_sales = spread(sales, seasonal)
    month_tax = spread(tax_collected, seasonal)
    inv_no = 88001
    june_deposits = [m(d[4]) for d in g.CLEARED_DEPOSITS + g.UNCLEARED_DEPOSITS]
    for (y, mo), s_amt, t_amt in zip(MONTHS, month_sales, month_tax):
        for j, (s_part, t_part) in enumerate(zip(spread(s_amt, [1] * 5),
                                                 spread(t_amt, [1] * 5))):
            who = customers[(inv_no + j) % len(customers)]
            b.add(workday(y, mo, 4 + j * 5), "Invoice", str(inv_no), who, "",
                  [("11000", s_part + t_part), ("40000", -s_part), ("22000", -t_part)])
            inv_no += 1
    for i, (amount, (y, mo)) in enumerate(zip(spread(returns, [1] * 12), MONTHS)):
        b.add(workday(y, mo, 15), "Credit Memo", f"CM-{501 + i}",
              customers[i % len(customers)], "Returned goods",
              [("40500", amount), ("11000", -amount)])
    ridgeback = m("3150.00")
    b.add(workday(2026, 1, 20), "Journal Entry", "1031", "",
          "Write off uncollectible accounts",
          [("11900", write_offs - ridgeback), ("11000", -(write_offs - ridgeback))])
    b.add(date(2026, 6, 30), "Journal Entry", "1066", "Ridgeback Cycles",
          "Write off Ridgeback Cycles", [("11900", ridgeback), ("11000", -ridgeback)],
          created=date(2026, 7, 10))
    b.add(date(2026, 6, 30), "Journal Entry", "1064", "", "Bad debt provision",
          [("65000", act["65000"]), ("11900", -act["65000"])])
    col_months = spread(collections - sum(june_deposits), [1] * 11)
    for (y, mo), amount in zip(MONTHS[:11], col_months):
        for k, part in enumerate(spread(amount, [1] * 4)):
            b.add(workday(y, mo, 6 + k * 7), "Deposit", "", "", "Customer receipts",
                  [("10100", part), ("11000", -part)])
    for d, amount in zip(g.CLEARED_DEPOSITS + g.UNCLEARED_DEPOSITS, june_deposits):
        when = date(2026, int(d[0][:2]), int(d[0][3:5]))
        b.add(when, "Deposit", "", "", "Customer receipts",
              [("10100", amount), ("11000", -amount)])
    remit = tax_collected + act["22000"]
    for i, (amount, (y, mo)) in enumerate(zip(spread(remit, [1] * 11), MONTHS[:11])):
        b.add(workday(y, mo, 25), "Check", None,
              "Idaho State Tax Commission", "Sales tax",
              [("22000", amount), ("10100", -amount)])

    # ---- inventory relief, shrinkage, depreciation, prepaid, accruals
    for (y, mo), amount in zip(MONTHS, spread(act["50000"], seasonal)):
        b.add(date(y, mo, 28) if date(y, mo, 28).weekday() < 5 else workday(y, mo, 26),
              "Inventory Qty Adjust", "", "", "Cost of goods sold",
              [("50000", amount), ("12100", -amount)])
    b.add(date(2026, 6, 30), "Journal Entry", "1065", "", "Physical count adjustment",
          [("51000", act["51000"]), ("12100", -act["51000"])])
    for i, ((y, mo), amount) in enumerate(zip(MONTHS, spread(act["64000"], [1] * 12))):
        b.add(workday(y, mo, 27), "Journal Entry", f"{1001 + i}", "", "Depreciation",
              [("64000", amount), ("15900", -amount)])
    for i, ((y, mo), amount) in enumerate(zip(MONTHS, spread(act["63000"], [1] * 12))):
        b.add(workday(y, mo, 27), "Journal Entry", f"{1013 + i}", "",
              "Insurance amortization", [("63000", amount), ("13000", -amount)])
    b.add(date(2026, 6, 30), "Journal Entry", "1063", "", "Accrue year-end fees",
          [("68000", accrued_fees), ("21000", -accrued_fees)])
    # freight/office reclass with no description
    b.add(workday(2026, 2, 10), "Journal Entry", "1052", "", "",
          [("66000", manual_reclass), ("67000", -manual_reclass)])
    key["no_description_entry"] = "1052"

    # ---- payroll, transfers, the kiting deposit
    wages, taxes = act["60100"], act["60200"]
    paydays = [workday(y, mo, d) for y, mo in MONTHS for d in (15, 28)]
    for when, w, t in zip(paydays, spread(wages, [1] * 24), spread(taxes, [1] * 24)):
        b.add(when, "Payroll Check", "", "Staff payroll", "Payroll",
              [("60100", w), ("60200", t), ("10200", -(w + t))])
    t0701 = m("25000.00")
    b.add(date(2026, 6, 30), "Deposit", "", "Checking", "Transfer from checking",
          [("10200", t0701), ("10900", -t0701)])
    transfers = act["10200"] + wages + taxes - t0701
    june_transfers = [m("38500.00"), m("40000.00")]
    for (y, mo), amount in zip(MONTHS[:11],
                               spread(transfers - sum(june_transfers), [1] * 11)):
        b.add(workday(y, mo, 14), "Transfer", "", "", "Payroll funding",
              [("10200", amount), ("10100", -amount)])
    for when, amount in zip((date(2026, 6, 15), date(2026, 6, 30)), june_transfers):
        b.add(when, "Transfer", "", "", "Payroll funding",
              [("10200", amount), ("10100", -amount)])

    # ---- debt, equipment, distributions, closing
    interest = act["69000"]
    june_interest = m("1125.00")
    for (y, mo), amount in zip(MONTHS[:11], spread(interest - june_interest, [1] * 11)):
        b.add(workday(y, mo, 24), "Check", None, "First Prairie Bank",
              "Line of credit interest", [("69000", amount), ("10100", -amount)])
    b.add(date(2026, 6, 24), "Check", "4410", "First Prairie Bank",
          "Line of credit interest", [("69000", june_interest), ("10100", -june_interest)])
    b.add(workday(2025, 10, 1), "Check", None, "First Prairie Bank",
          "Line of credit principal", [("23000", act["23000"]), ("10100", -act["23000"])])
    b.add(workday(2025, 8, 12), "Check", None, "Rocky Mountain Racking",
          "Warehouse racking", [("15000", act["15000"]), ("10100", -act["15000"])])
    owner_je = m("25000.00")
    b.add(date(2026, 3, 14), "Journal Entry", "1047", "", "Owner draw",
          [("31000", owner_je), ("10100", -owner_je)], by=OWNER)
    key["owner_entry"] = {"num": "1047", "date": "2026-03-14", "weekday": "Saturday",
                          "amount": "25000.00", "by": OWNER}
    for (y, mo), amount in zip(MONTHS[:11],
                               spread(paid_distributions - owner_je, [1] * 11)):
        b.add(workday(y, mo, 10), "Check", None, "Members",
              "Member distribution", [("31000", amount), ("10100", -amount)])
    b.add(workday(2025, 7, 1), "Journal Entry", "1000", "", "Close prior-year distributions",
          [("32000", closing_distributions), ("31000", -closing_distributions)])

    number_checks(b)
    return b, key, act, bills, payments, begin_ap, end_ap


def number_checks(b: Book):
    """Checks written before June carry numbers in date order below June's
    first reconciled check (4391); June's keep the reconciliation's numbers."""
    pending = sorted((t for t in b.tx if t["num"] is None),
                     key=lambda t: (t["date"], t["name"]))
    for n, t in enumerate(pending, start=4001):
        t["num"] = str(n)
    assert 4001 + len(pending) <= 4391, len(pending)
    assert all(t["date"] < date(2026, 6, 1) for t in pending)


# ------------------------------------------------------------------ outputs
def main():
    b, key, act, bills, payments, begin_ap, end_ap = build()
    activity = {}
    for t in b.tx:
        if t["date"] > PE:
            continue
        for n, amount in t["lines"]:
            activity[n] = activity.get(n, ZERO) + amount
    gaps = {n: activity.get(n, ZERO) - act[n] for n in act
            if n not in ("32000",) and activity.get(n, ZERO) != act[n]}
    print(json.dumps({k: str(v) for k, v in gaps.items()}, indent=1))


if __name__ == "__main__":
    main()
