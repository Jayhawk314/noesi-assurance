# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Generate the Kestrel Valley Cycle Supply second test case.

A fabricated bicycle-parts distributor that keeps its books in QuickBooks
Online, year ended June 30, 2026. The client files are shaped like
QuickBooks exports (Trial Balance with Debit/Credit columns, A/R Aging
Summary with five buckets, Inventory Valuation Summary with quantity and
average cost, Reconciliation Report); the count tags, bank cutoff statement
and auditor workpapers are shaped the way those records usually arrive.

The answer key is computed here with plain Decimal arithmetic from the same
figures that are written to the files. This script imports nothing from
Noesi: the key states what a correct audit concludes, not what the engine
happens to do.

    python case-studies/kestrel-valley-cycle/generate.py

Deterministic: no randomness and pinned workbook dates, so a rerun
writes byte-identical files.
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent
QBO = ROOT / "data" / "quickbooks"
CLIENT = ROOT / "data" / "client"
BANK = ROOT / "data" / "bank"
AUDITOR = ROOT / "data" / "auditor"
INSTRUCTOR = ROOT / "instructor"

COMPANY = "Kestrel Valley Cycle Supply, LLC"
D = Decimal
CENT = D("0.01")


def m(x) -> Decimal:
    return D(str(x)).quantize(CENT, rounding=ROUND_HALF_UP)


# ------------------------------------------------------------------ policies
MATERIALITY = D("15000")            # approved: ~5% of pretax income
PM_MULTIPLE = D("2.0")              # cap on the sum of account allocations
AR_TOLERABLE = D("9000")
INVENTORY_TOLERABLE = D("9000")
ANALYTICS_PCT = D("10")
ANALYTICS_AMOUNT = D("15000")
DIT_MAX_DAYS = 3
ALLOWANCE_RATES = {"Current": D("0.01"), "1 - 30": D("0.02"), "31 - 60": D("0.05"),
                   "61 - 90": D("0.15"), "91 and over": D("0.40")}
BUCKETS = list(ALLOWANCE_RATES)
# The bucket captions as QuickBooks Online's A/R Aging Summary prints them.
AGING_CAPTIONS = ["CURRENT", "1 - 30", "31 - 60", "61 - 90", "91 AND OVER"]

# ------------------------------------------------------------------ A/R aging
# Exported 07/08/2026, before the client's 6/30-dated write-off of Ridgeback
# Cycles (JE 1066, entered 07/10/2026). The trial balance was exported after.
AGING = [  # customer, Current, 1-30, 31-60, 61-90, 91+
    ("Alpine Loop Bicycles", "18240.00", "6310.50", "", "", ""),
    ("Basalt Ridge Bike Co.", "7420.15", "1880.00", "", "", ""),
    ("Big Sky Pedal Co.", "31450.50", "14280.00", "2480.00", "", ""),
    ("Bitterroot Wheelworks", "5210.00", "", "1320.40", "", ""),
    ("Bridger Cyclery", "12640.80", "4410.00", "", "", ""),
    ("Cottonwood Spokes", "3180.25", "", "", "", ""),
    ("Crazy Mountain Cycles", "8930.00", "2215.60", "845.00", "", ""),
    ("Flathead Pedalworks", "", "", "", "2760.00", "1480.00"),
    ("Gallatin Gear Exchange", "22415.30", "9870.10", "", "", ""),
    ("Grizzly Trail Outfitters", "6108.40", "", "", "", ""),
    ("Hyalite Bike Shop", "9375.00", "3120.00", "1540.25", "", ""),
    ("Jackrabbit Cycle Works", "", "1965.00", "", "", "2140.00"),
    ("Madison Range Bicycle", "14892.65", "5210.00", "", "", ""),
    ("Paradise Valley Cycles", "4412.80", "1105.00", "", "", ""),
    ("Ridgeback Cycles", "", "", "", "", "3150.00"),
    ("Sawtooth Spoke & Chain", "10675.00", "", "2960.00", "1210.00", ""),
    ("Sourdough Bike Collective", "2870.45", "", "", "", ""),
    ("Spanish Peaks Pedal", "7715.20", "2490.00", "", "", ""),
    ("Summit Loop Racing", "-1840.00", "", "", "", ""),
    ("Yellowstone Velo", "19620.00", "7445.35", "1380.00", "", ""),
]
WRITE_OFF = ("Ridgeback Cycles", m("3150.00"))
# Confirmation sample from the customers below the key-item threshold.
SAMPLE = ["Bitterroot Wheelworks", "Cottonwood Spokes", "Grizzly Trail Outfitters",
          "Paradise Valley Cycles", "Sourdough Bike Collective"]


def aging_rows():
    rows = []
    for name, *vals in AGING:
        amounts = [m(v) if v else D("0") for v in vals]
        rows.append((name, amounts, sum(amounts)))
    return rows


# ------------------------------------------------------------------ inventory
# category, item name, SKU, qty, asset value
INVENTORY = [
    ("Drivetrain", "11-Speed Chain 116L", "KV-CHN-11", 240, "4104.00"),
    ("Drivetrain", "12-Speed Chain 126L", "KV-CHN-12", 118, "3068.00"),
    ("Drivetrain", "11-Speed Rear Derailleur", "KV-DER-11S", 42, "4620.00"),
    ("Drivetrain", "Cassette 11-34T", "KV-CAS-1134", 64, "3776.00"),
    ("Drivetrain", "Crankset 172.5mm", "KV-CRK-172", 21, "3654.00"),
    ("Drivetrain", "Bottom Bracket BSA", "KV-BB-BSA", 88, "1672.00"),
    ("Wheels & Tires", "Disc Hub, Rear", "KV-HUB-DT", 4, "850.00"),
    ("Wheels & Tires", "700x32 Tire", "KV-TIR-70032", 310, "6975.00"),
    ("Wheels & Tires", "29x2.4 Trail Tire", "KV-TIR-2924", 145, "6452.50"),
    ("Wheels & Tires", "29in Inner Tube", "KV-TUBE-29", 420, "2520.00"),
    ("Wheels & Tires", "700c Wheelset", "KV-WHL-700", 16, "6240.00"),
    ("Wheels & Tires", "Tubeless Sealant 1L", "KV-SEAL-1L", 96, "1488.00"),
    ("Components", "Disc Brake Pads", "KV-BRK-PAD", 380, "3230.00"),
    ("Components", "Hydraulic Brake Set", "KV-BRK-HYD", 26, "4498.00"),
    ("Components", "Lock-On Grips", "KV-GRP-LCK", 37, "612.40"),
    ("Components", "Carbon Handlebar 780mm", "KV-BAR-780", 19, "2185.00"),
    ("Components", "Dropper Post 150mm", "KV-DRP-150", 23, "4715.00"),
    ("Components", "Comp Saddle", "KV-SAD-CMP", 36, "1512.00"),
    ("Components", "Flat Pedals", "KV-PED-FLT", 74, "2442.00"),
    ("Components", "Stem 50mm", "KV-STM-50", 58, "1740.00"),
]

# Client count tags from the 06/30/2026 count the auditor observed.
# tag, SKU as written on the tag, description, location, qty, counter
COUNT_TAGS = [
    ("1001", "KV-CHN-11", "11sp chain", "Aisle A", 150, "DM"),
    ("1002", "KV-CHN-11", "11sp chain", "Overflow", 80, "DM"),
    ("1003", "KV-CHN-12", "12sp chain", "Aisle A", 118, "DM"),
    ("1004", "KV-DER-11S", "Rear derailleur", "Aisle A", 42, "DM"),
    ("1005", "KV-CAS-1134", "Cassette 11-34", "Aisle A", 40, "DM"),
    ("1006", "KV-CAS-1134", "Cassette 11-34", "Aisle B", 24, "JT"),
    ("1007", "KV-CRK-172", "Crankset", "Aisle B", 21, "JT"),
    ("1008", "KV-BB-BSA", "BB BSA", "Aisle B", 88, "JT"),
    ("1009", "KV-TIR-70032", "700x32 tire", "Rack 1", 200, "JT"),
    ("1010", "KV-TIR-70032", "700x32 tire", "Rack 2", 110, "RS"),
    ("1011", "KV-TIR-2924", "29x2.4 tire", "Rack 2", 145, "RS"),
    ("1012", "KV-TUBE-29", "29 tube", "Bin 4", 300, "RS"),
    ("1013", "KV-TUBE-29", "29 tube", "Bin 5", 120, "RS"),
    ("1014", "KV-WHL-700", "700c wheelset", "Rack 3", 16, "RS"),
    ("1015", "KV-SEAL-1L", "Sealant 1L", "Aisle C", 96, "DM"),
    ("1016", "kv-brk-pad ", "brake pads", "Aisle C", 250, "DM"),
    ("1017", "", "VOID", "", 0, "DM"),
    ("1018", "KV-BRK-PAD", "Brake pads", "Overflow", 130, "JT"),
    ("1019", "KV-BRK-HYD", "Hyd brake set", "Aisle C", 26, "JT"),
    ("1020", "KV-GRP-LCK", "Grips", "Aisle D", 37, "JT"),
    ("1021", "KV-BAR-780", "Carbon bar", "Aisle D", 19, "RS"),
    ("1022", "KV-DRP-150", "Dropper 150", "Aisle D", 23, "RS"),
    ("1023", "KV-SAD-CMP", "Saddle", "Aisle D", 36, "RS"),
    ("1024", "KV-PED-FLT", "Flat pedals", "Aisle E", 50, "DM"),
    ("1025", "KV-PED-FLT", "Flat pedals", "Overflow", 24, "DM"),
    ("1026", "KV-STM-50", "Stem 50", "Aisle E", 58, "DM"),
    ("1027", "KV-TUBE-29P", "29 tube presta (Moraine consignment)", "Cage", 36, "JT"),
]
CONSIGNED_UNIT_COST = D("7.25")     # Moraine invoice price; stock is Moraine's

# Auditor pricing test: sample items, extended cost per books vs per invoice.
PRICING = [  # SKU, qty, invoice unit cost
    ("KV-CHN-11", 240, "17.10"),
    ("KV-DER-11S", 42, "104.50"),    # recorded 110.00 average — overstated
    ("KV-TIR-70032", 310, "22.50"),
    ("KV-WHL-700", 16, "390.00"),
    ("KV-BRK-HYD", 26, "173.00"),
    ("KV-DRP-150", 23, "205.00"),
    ("KV-SAD-CMP", 36, "43.00"),     # recorded 42.00 average — understated
    ("KV-TIR-2924", 145, "44.50"),
]

# ------------------------------------------------------------------ cash
# Checking reconciliation, period ending 06/30/2026.
# June's checks run 4411-4426 in date order (renumbered 2 Oct 2026, roadmap
# D10: the earlier numbers skipped by accident). 4421 and 4425 kept the
# numbers the key names. 4422-4424 are missing on purpose: the planted gap
# in the check sequence (answer_key_part3.json "forensic").
REC_BEGIN = m("171904.88")
CLEARED_CHECKS = [  # date, type, ref, payee, amount
    ("06/02/2026", "Check", "4411", "Granite Peak Properties", "8750.00"),
    ("06/04/2026", "Bill Payment", "4412", "Moraine Cycle Components", "22140.60"),
    ("06/08/2026", "Check", "4413", "Northwestern Energy", "1284.33"),
    ("06/11/2026", "Bill Payment", "4414", "Velo Freight Lines", "3915.00"),
    ("06/15/2026", "Payroll Transfer", "", "Payroll Checking", "38500.00"),
    ("06/16/2026", "Bill Payment", "4415", "Summit Tire Import", "17480.25"),
    ("06/19/2026", "Check", "4416", "Big Hole Insurance", "4210.00"),
    ("06/22/2026", "Bill Payment", "4417", "Moraine Cycle Components", "15600.00"),
    ("06/24/2026", "Check", "4419", "First Prairie Bank - LOC interest", "1125.00"),
]
CLEARED_DEPOSITS = [
    ("06/03/2026", "Deposit", "", "Customer receipts", "41220.40"),
    ("06/09/2026", "Deposit", "", "Customer receipts", "36815.10"),
    ("06/16/2026", "Deposit", "", "Customer receipts", "44102.75"),
    ("06/23/2026", "Deposit", "", "Customer receipts", "39658.20"),
    ("06/29/2026", "Deposit", "", "Customer receipts", "18411.45"),
]
UNCLEARED_CHECKS = [
    ("06/22/2026", "Bill Payment", "4418", "Velo Freight Lines", "2480.00"),
    ("06/26/2026", "Check", "4420", "Granite Peak Properties", "8750.00"),
    ("06/27/2026", "Check", "4421", "Tri-County Tool Rental", "3100.00"),
    ("06/29/2026", "Check", "4425", "Alder & Finch CPAs", "1780.00"),
    ("06/30/2026", "Bill Payment", "4426", "Moraine Cycle Components", "11265.40"),
    ("06/30/2026", "Transfer", "", "Payroll Checking", "40000.00"),
]
UNCLEARED_DEPOSITS = [
    ("06/30/2026", "Deposit", "", "Customer receipts", "12650.00"),
    ("06/30/2026", "Deposit", "", "Customer receipts", "4318.75"),
]
# First Prairie Bank cutoff statement, 07/01-07/15/2026 (bank's own layout).
CUTOFF = [  # posting date, description, check/slip, signed amount
    ("07/01/2026", "CHECK 4420", "4420", "-8750.00"),
    ("07/01/2026", "ONLINE TRANSFER TO XXXX4471", "", "-40000.00"),
    ("07/01/2026", "DEPOSIT", "", "4318.75"),
    ("07/02/2026", "CHECK 4418", "4418", "-2480.00"),
    ("07/02/2026", "CHECK 4429", "4429", "-25000.00"),
    ("07/06/2026", "CHECK 4425", "4425", "-1870.00"),
    ("07/07/2026", "DEPOSIT", "", "12650.00"),
    ("07/08/2026", "DEPOSIT", "", "33580.90"),
    ("07/09/2026", "CHECK 4426", "4426", "-11265.40"),
    ("07/10/2026", "CHECK 4431", "4431", "-2215.00"),
    ("07/14/2026", "DEPOSIT", "", "27904.15"),
    ("07/15/2026", "CHECK 4433", "4433", "-6100.00"),
]
PAYROLL_REC_STATEMENT = m("51340.00")
PAYROLL_UNCLEARED = [("06/30/2026", "Paycheck", "PR-2231", "Staff payroll", "2410.00"),
                     ("06/30/2026", "Paycheck", "PR-2236", "Staff payroll", "2430.00")]
# Auditor's interbank transfer schedule (books from QuickBooks, bank from statements).
TRANSFERS = [  # id, amount, from, to, disbursed books, disbursed bank, received books, received bank
    ("T-0615", "38500.00", "Checking", "Payroll Checking",
     "06/15/2026", "06/15/2026", "06/15/2026", "06/15/2026"),
    ("T-0630", "40000.00", "Checking", "Payroll Checking",
     "06/30/2026", "07/01/2026", "06/30/2026", "06/30/2026"),
    ("T-0701", "25000.00", "Checking", "Payroll Checking",
     "07/01/2026", "07/02/2026", "06/30/2026", "06/30/2026"),
]

# ------------------------------------------------------------------ trial balance
# number, name, auditor line, current (signed, debit +), prior. None = computed.
TB = [
    ("10100", "Checking - First Prairie", "Cash", None, "151880.12"),
    ("10200", "Payroll Checking", "Cash", None, "8200.00"),
    ("10300", "Petty Cash", "Cash", "500.00", "500.00"),
    ("10900", "Transfers Clearing", "Other current assets", "-25000.00", "0.00"),
    ("11000", "Accounts Receivable (A/R)", "Accounts receivable", None, "268410.35"),
    ("11900", "Allowance for Doubtful Accounts", "Accounts receivable",
     "-4200.00", "-12800.00"),
    ("12100", "Inventory Asset", "Inventory", None, "58910.60"),
    ("13000", "Prepaid Expenses", "Other current assets", "18400.00", "16950.00"),
    ("15000", "Furniture and Equipment", "Property and equipment", "212800.00",
     "198300.00"),
    ("15900", "Accumulated Depreciation", "Property and equipment", "-96450.00",
     "-78200.00"),
    ("20000", "Accounts Payable (A/P)", "Accounts payable", "-287640.18", "-241905.66"),
    ("21000", "Accrued Liabilities", "Accrued liabilities", "-42315.00", "-38760.00"),
    ("22000", "Sales Tax Payable", "Accrued liabilities", "-9812.44", "-8977.10"),
    ("23000", "Line of Credit", "Line of credit", "-150000.00", "-200000.00"),
    ("30100", "Members' Capital", "Members' equity", "-60000.00", "-60000.00"),
    ("31000", "Members' Distributions", "Members' equity", None, None),
    ("32000", "Retained Earnings", "Members' equity", None, "-20000.00"),
    ("40000", "Sales", "Revenue", "-4286540.00", "-3912300.00"),
    ("40500", "Sales Returns and Allowances", "Revenue", "61220.00", "52410.00"),
    ("50000", "Cost of Goods Sold", "Cost of sales", "3050400.00", "2760150.00"),
    ("51000", "Inventory Shrinkage", "Cost of sales", "6240.00", "4880.00"),
    ("60100", "Wages and Salaries", "Operating expenses", "486300.00", "452800.00"),
    ("60200", "Payroll Taxes", "Operating expenses", "41335.50", "38488.00"),
    ("61000", "Rent Expense", "Operating expenses", "105000.00", "102000.00"),
    ("62000", "Utilities", "Operating expenses", "15412.00", "14870.00"),
    ("63000", "Insurance", "Operating expenses", "25260.00", "23110.00"),
    ("64000", "Depreciation Expense", "Operating expenses", "18250.00", "16400.00"),
    ("65000", "Bad Debt Expense", "Operating expenses", "7920.00", "6150.00"),
    ("66000", "Freight Out", "Operating expenses", "96480.00", "71230.00"),
    ("67000", "Office Supplies", "Operating expenses", "8745.00", "8120.00"),
    ("68000", "Professional Fees", "Operating expenses", "22400.00", "19800.00"),
    ("69000", "Interest Expense", "Interest expense", "13750.00", "15600.00"),
]


def build_tb(ar_total, inventory_total, checking_book, payroll_book):
    computed_current = {"10100": checking_book, "10200": payroll_book,
                        "11000": ar_total, "12100": inventory_total}
    current = {n: (m(c) if c is not None else computed_current.get(n))
               for n, _, _, c, _ in TB}
    prior = {n: (m(p) if p is not None else None) for n, _, _, _, p in TB}
    # Each year's distributions balance that year's trial balance; the
    # bookkeeper closes distributions and net income to retained earnings.
    prior["31000"] = -sum(v for k, v in prior.items() if k != "31000")
    income_accounts = [n for n, *_ in TB if n[0] in "456"]
    prior_net_income = -sum(prior[n] for n in income_accounts)
    assert D("0") < prior["31000"] < prior_net_income, prior["31000"]
    current["32000"] = prior["32000"] - prior_net_income + prior["31000"]
    current["31000"] = -sum(v for k, v in current.items() if k != "31000")
    assert D("0") < current["31000"] < D("400000"), current["31000"]
    return current, prior, prior_net_income


# ------------------------------------------------------------------ writers
def write_report(path, title, dateline, header, body, footer_basis=True,
                 stamp="Wednesday, July 15, 2026 10:42 AM GMTZ"):
    """QuickBooks Online export layout: company, title, date line, blank,
    header row, body, three blank rows, basis + timestamp footer.

    Checked against real QuickBooks Online exports (tests/fixtures/quickbooks/
    and kestrel_qbo/): the Excel title abbreviates the month ("As of Jun 30,
    2026"). One difference is kept on purpose: QuickBooks writes its totals as
    formulas with the computed value saved; openpyxl cannot save that value,
    so the totals here are the numbers themselves, which read the same."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"  # QuickBooks exports use one sheet named Sheet1
    width = len(header)
    for row in ([COMPANY], [title], [dateline], [None], header):
        ws.append(list(row) + [None] * (width - len(row)))
    for row in body:
        ws.append([float(v) if isinstance(v, Decimal) else v for v in row])
    for _ in range(3):
        ws.append([None] * width)
    ws.append([("Accrual Basis " if footer_basis else " ") + stamp]
              + [None] * (width - 1))
    for r in ws.iter_rows(min_row=6):
        for c in r:
            if isinstance(c.value, float):
                c.number_format = '"$"#,##0.00'
    path.parent.mkdir(parents=True, exist_ok=True)
    save(wb, path)


JOURNAL_HEADER = [None, "Transaction date", "Transaction type", "Num", "Name",
                  "Description", "Account Name", "Debit", "Credit", "Created on",
                  "Created by"]


def journal_body(txs, names, first_id):
    """QuickBooks Online Journal, customized to add Created on and Created by,
    as the real export lays it out (tests/fixtures/quickbooks/kestrel_qbo/
    journal_created_by.xlsx): each transaction's lines under a heading row
    holding its QuickBooks transaction ID, date, type, Num and name repeated
    on every line, Created on as a timestamp, then 'Total for <ID>' and a
    grand TOTAL. IDs count up in the order the transactions were entered;
    the report lists them by date. Returns the rows and the grand total."""
    ids = {id(t): first_id + i for i, t in enumerate(txs)}
    body, grand = [], D("0")
    for t in sorted(txs, key=lambda t: (t["date"], t["type"], str(t["num"] or ""),
                                       t["name"])):
        txn = ids[id(t)]
        body.append((str(txn),) + (None,) * 10)
        for n, amount in t["lines"]:
            body.append((None, t["date"].strftime("%m/%d/%Y"), t["type"], t["num"] or "",
                         t["name"] or "", t["memo"] or "", names[n],
                         amount if amount > 0 else None, -amount if amount < 0 else None,
                         t["created"].strftime("%m/%d/%Y") + " 10:15:00 AM", t["by"]))
        debits = sum(a for _, a in t["lines"] if a > 0)
        body.append((f"Total for {txn}",) + (None,) * 6 + (debits, debits, None, None))
        grand += debits
    body.append(("TOTAL",) + (None,) * 6 + (grand, grand, None, None))
    return body, grand


def fixed_dates(wb):
    """Pin workbook metadata so a rerun writes byte-identical files."""
    wb.properties.created = wb.properties.modified = datetime(2026, 7, 15, 10, 42)


def save(wb, path):
    """Save with pinned metadata and zip entry dates (byte-identical reruns)."""
    fixed_dates(wb)
    buf = io.BytesIO()
    wb.save(buf)
    out = io.BytesIO()
    with zipfile.ZipFile(buf) as src, zipfile.ZipFile(out, "w",
                                                      zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            fixed = zipfile.ZipInfo(info.filename, date_time=(2026, 7, 15, 10, 42, 0))
            fixed.compress_type = zipfile.ZIP_DEFLATED
            data = src.read(info.filename)
            if info.filename == "docProps/core.xml":  # openpyxl stamps "now"
                data = re.sub(rb"(<dcterms:modified[^>]*>)[^<]*",
                              rb"\g<1>2026-07-15T10:42:00Z", data)
            dst.writestr(fixed, data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out.getvalue())


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for row in rows:
            w.writerow([f"{v:.2f}" if isinstance(v, Decimal) else v for v in row])


def blank(v):
    return v if v else None


# ------------------------------------------------------------------ build
def main():
    key = {}

    # --- A/R aging ------------------------------------------------------
    rows = aging_rows()
    aging_total = sum(t for _, _, t in rows)
    bucket_totals = [sum(a[i] for _, a, _ in rows) for i in range(5)]
    body = [(name, *[blank(v) for v in amounts], total) for name, amounts, total in rows]
    body.append(("TOTAL", *bucket_totals, aging_total))
    write_report(QBO / "AR_Aging_Summary.xlsx", "A/R Aging Summary Report",
                 "As of Jun 30, 2026", ["", *AGING_CAPTIONS, "Total"], body,
                 footer_basis=False, stamp="Wednesday, July 8, 2026 04:17 PM GMTZ")
    ar_per_tb = aging_total - WRITE_OFF[1]

    # --- inventory ------------------------------------------------------
    # Items with no category, by name, as the real export lists them; the
    # TOTAL carries the overall average cost. (The layout with categories was
    # not seen in a real export, so the case does not use it.)
    inv = [(cat, name, sku, qty, m(val)) for cat, name, sku, qty, val in INVENTORY]
    inventory_total = sum(i[4] for i in inv)
    total_qty = sum(i[3] for i in inv)
    body = [(name, sku, qty, val, float(val / qty))
            for _, name, sku, qty, val in sorted(inv, key=lambda i: i[1])]
    body.append(("TOTAL", None, total_qty, inventory_total,
                 float(inventory_total / total_qty)))
    write_report(QBO / "Inventory_Valuation_Summary.xlsx", "Inventory Valuation Summary",
                 "As of Jun 30, 2026", ["", "SKU", "Qty", "Asset Value", "Calc. Avg"],
                 body)

    CLIENT.mkdir(parents=True, exist_ok=True)
    write_csv(CLIENT / "count_tags_2026-06-30.csv",
              ["Tag #", "Item SKU", "Description", "Location", "Qty Counted", "Counted By"],
              COUNT_TAGS)

    # --- cash -----------------------------------------------------------
    amt = lambda rows_: sum(m(r[4]) for r in rows_)
    statement_end = REC_BEGIN - amt(CLEARED_CHECKS) + amt(CLEARED_DEPOSITS)
    checking_book = statement_end - amt(UNCLEARED_CHECKS) + amt(UNCLEARED_DEPOSITS)
    payroll_book = PAYROLL_REC_STATEMENT - amt(PAYROLL_UNCLEARED)
    write_reconciliation("10100 Checking - First Prairie", REC_BEGIN, CLEARED_CHECKS,
                         CLEARED_DEPOSITS, UNCLEARED_CHECKS, UNCLEARED_DEPOSITS,
                         statement_end, checking_book, "Checking_Reconciliation.xlsx")
    write_reconciliation("10200 Payroll Checking", m("22840.00"),
                         [("06/15/2026", "Paycheck", "PR-2210", "Staff payroll", "37500.00"),
                          ("06/30/2026", "Paycheck", "PR-2229", "Staff payroll",
                           "37500.00")],
                         [("06/15/2026", "Transfer", "", "Checking", "38500.00"),
                          ("06/30/2026", "Transfer", "", "Checking", "40000.00"),
                          ("06/30/2026", "Deposit", "", "Checking", "25000.00")],
                         PAYROLL_UNCLEARED, [], PAYROLL_REC_STATEMENT, payroll_book,
                         "Payroll_Checking_Reconciliation.xlsx")
    payroll_check = m("22840.00") - m("75000.00") + m("103500.00")
    assert payroll_check == PAYROLL_REC_STATEMENT, payroll_check

    BANK.mkdir(parents=True, exist_ok=True)
    write_csv(BANK / "first_prairie_xxxx2208_2026-07-01_to_2026-07-15.csv",
              ["Posting Date", "Description", "Check or Slip #", "Amount"],
              [(d, desc, ref, m(a)) for d, desc, ref, a in CUTOFF])

    # --- trial balance --------------------------------------------------
    current, prior, prior_ni = build_tb(ar_per_tb, inventory_total, checking_book,
                                        payroll_book)
    for which, bal, dateline, stamp in (
            ("Trial_Balance_2026-06-30.xlsx", current, "As of Jun 30, 2026",
             "Wednesday, July 15, 2026 10:42 AM GMTZ"),
            ("Trial_Balance_2025-06-30.xlsx", prior, "As of Jun 30, 2025",
             "Wednesday, July 15, 2026 10:44 AM GMTZ")):
        body = []
        for n, name, *_ in TB:
            v = bal[n]
            if v == 0:
                continue
            body.append((f"{n} {name}", v if v > 0 else None, -v if v < 0 else None))
        debits = sum(v for v in bal.values() if v > 0)
        credits = -sum(v for v in bal.values() if v < 0)
        assert debits == credits, (which, debits, credits)
        body.append(("TOTAL", debits, credits))
        write_report(QBO / which, "Trial Balance", dateline, ["Account Name", "Debit", "Credit"],
                     body, stamp=stamp)
    write_csv(AUDITOR / "tb_line_mapping.csv", ["Account", "Lead Schedule Line"],
              [(f"{n} {name}", line) for n, name, line, *_ in TB])

    # --- auditor workpapers ----------------------------------------------
    write_auditor_files(rows, inv, current)

    key = answer_key(rows, aging_total, ar_per_tb, inv, inventory_total, statement_end,
                     checking_book, payroll_book, current, prior, prior_ni)
    INSTRUCTOR.mkdir(parents=True, exist_ok=True)
    (INSTRUCTOR / "answer_key.json").write_text(
        json.dumps(key, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(key["summary"], indent=2, default=str))


def write_reconciliation(account, begin, cleared_pay, cleared_dep, uncl_pay, uncl_dep,
                         statement_end, register, filename):
    """QuickBooks Online Reconciliation Report layout (summary then detail)."""
    amt = lambda rows_: sum(m(r[4]) for r in rows_)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    lines = [
        [COMPANY], [f"{account.split(' ', 1)[1]}, Period Ending 06/30/2026"],
        ["RECONCILIATION REPORT"], ["Reconciled on: 07/13/2026"],
        ["Reconciled by: Dana Merritt"],
        ["Any changes made to transactions after this date aren't included in this report."],
        [None],
        ["Summary", None, None, None, "USD"],
        ["Statement beginning balance", None, None, None, begin],
        [f"Checks and payments cleared ({len(cleared_pay)})", None, None, None,
         -amt(cleared_pay)],
        [f"Deposits and other credits cleared ({len(cleared_dep)})", None, None, None,
         amt(cleared_dep)],
        ["Statement ending balance", None, None, None, statement_end],
        [None],
        [f"Uncleared transactions as of 06/30/2026", None, None, None,
         amt(uncl_dep) - amt(uncl_pay)],
        ["Register balance as of 06/30/2026", None, None, None, register],
        [None], ["Details"], [None],
    ]
    def section(title, items, sign):
        lines.append([f"{title} ({len(items)})"])
        lines.append(["DATE", "TYPE", "REF NO.", "PAYEE", "AMOUNT (USD)"])
        for d, t, ref, payee, a in items:
            lines.append([d, t, ref, payee, sign * m(a)])
        lines.append(["Total", None, None, None, sign * amt(items)])
        lines.append([None])
    section("Checks and payments cleared", cleared_pay, -1)
    section("Deposits and other credits cleared", cleared_dep, 1)
    lines.append(["Additional Information"])
    lines.append([None])
    section("Uncleared checks and payments as of 06/30/2026", uncl_pay, -1)
    section("Uncleared deposits and other credits as of 06/30/2026", uncl_dep, 1)
    for row in lines:
        ws.append([float(v) if isinstance(v, Decimal) else v for v in row])
    assert begin - amt(cleared_pay) + amt(cleared_dep) == statement_end
    assert statement_end - amt(uncl_pay) + amt(uncl_dep) == register
    QBO.mkdir(parents=True, exist_ok=True)
    save(wb, QBO / filename)


def write_auditor_files(aging, inv, current):
    by_name = {name: total for name, _, total in aging}
    # Confirmations: key stratum = every customer >= AR tolerable misstatement;
    # sample stratum = six customers chosen from the rest.
    key_items = [n for n, t in by_name.items() if t >= AR_TOLERABLE]
    replies = {  # customer: (confirmed, classification, client misstatement, note)
        "Big Sky Pedal Co.": ("45960.50", "client_misstatement", "2250.00",
                              "invoice 88214 billed at list, contract price lower"),
        "Gallatin Gear Exchange": ("25885.40", "timing", "0",
                                   "check mailed 06/28, received 07/02"),
        "Yellowstone Velo": ("27345.35", "customer_error", "0",
                             "customer omitted invoice 88390; POD inspected"),
        "Bitterroot Wheelworks": ("5910.40", "client_misstatement", "620.00",
                                  "freight charged twice on invoice 88175"),
    }
    sample_items = SAMPLE
    rows = []
    for name in key_items + sample_items:
        book = by_name[name]
        conf, cls, mis, note = replies.get(name, (str(book), "no_difference", "0", ""))
        rows.append((name, "key" if name in key_items else "sample", book, m(conf),
                     m(mis), cls, note))
    write_csv(AUDITOR / "confirmations.csv",
              ["Customer", "Stratum", "Book Value", "Confirmed Value",
               "Client Misstatement", "Classification", "Note"], rows)

    inv_by_sku = {sku: (qty, val) for _, _, sku, qty, val in inv}
    write_csv(AUDITOR / "pricing_tests.csv",
              ["Item SKU", "Qty", "Recorded Cost", "Audited Cost", "Vendor Invoice"],
              [(sku, qty, inv_by_sku[sku][1], m(D(qty) * D(unit)), f"INV-{i + 5101}")
               for i, (sku, qty, unit) in enumerate(PRICING)])
    write_csv(AUDITOR / "interbank_transfers.csv",
              ["Transfer", "Amount", "From Account", "To Account",
               "Disbursed per Books", "Disbursed per Bank", "Received per Books",
               "Received per Bank"],
              [(t, m(a), *rest) for t, a, *rest in TRANSFERS])
    write_csv(AUDITOR / "performance_materiality.csv",
              ["Account", "Performance Materiality"],
              [("Cash", m("4500")), ("Accounts receivable", m("9000")),
               ("Inventory", m("9000")), ("Accounts payable", m("7500")),
               ("Accrued liabilities", m("3000"))])


def answer_key(aging, aging_total, ar_per_tb, inv, inventory_total, statement_end,
               checking_book, payroll_book, current, prior, prior_ni):
    s = lambda d: {k: str(v) for k, v in d.items()}
    key = {"case": COMPANY, "period_end": "2026-06-30", "materiality": str(MATERIALITY)}

    # Planning: performance materiality
    alloc = [m("4500"), m("9000"), m("9000"), m("7500"), m("3000")]
    cap = MATERIALITY * PM_MULTIPLE
    key["planning.performance_materiality"] = {
        "allocated_total": str(sum(alloc)), "cap": str(cap),
        "exceeds_cap_by": str(sum(alloc) - cap),
        "any_allocation_above_materiality": any(a > MATERIALITY for a in alloc),
        "conclusion": "allocations total 33,000 against a 30,000 cap (2.0 x 15,000): "
                      "over by 3,000; no single allocation exceeds materiality"}

    # Planning: analytics (movement flags; definitions stated)
    lines = {n: line for n, _, line, *_ in TB}
    names = {n: name for n, name, *_ in TB}
    movements = []
    for n in names:
        cur, pri = current[n], prior[n]
        change = cur - pri
        pct = None if pri == 0 else (abs(change) / abs(pri) * 100).quantize(D("0.1"))
        over_pct = pct is None and change != 0 or (pct is not None and pct > ANALYTICS_PCT)
        over_amt = abs(change) > ANALYTICS_AMOUNT
        if over_pct or over_amt:
            movements.append({"account": f"{n} {names[n]}", "current": str(cur),
                              "prior": str(pri), "change": str(change),
                              "pct": None if pct is None else str(pct),
                              "over_pct": over_pct, "over_amount": over_amt})
    by_line = lambda bal: {ln: sum(bal[n] for n in names if lines[n] == ln)
                           for ln in dict.fromkeys(lines.values())}
    ratios = {}
    for label, bal, ni in (("2026", current, None), ("2025", prior, prior_ni)):
        L = by_line(bal)
        ca = L["Cash"] + L["Accounts receivable"] + L["Inventory"] + L["Other current assets"]
        cl = -(L["Accounts payable"] + L["Accrued liabilities"] + L["Line of credit"])
        revenue = -L["Revenue"]
        cogs = L["Cost of sales"]
        ratios[label] = {
            "current_ratio": str((ca / cl).quantize(D("0.01"))),
            "quick_ratio": str(((L["Cash"] + L["Accounts receivable"]) / cl)
                               .quantize(D("0.01"))),
            "gross_margin_pct": str(((revenue - cogs) / revenue * 100).quantize(D("0.1"))),
            "net_revenue": str(revenue), "cost_of_sales": str(cogs),
            "pretax_income": str(revenue - cogs - L["Operating expenses"]
                                 - L["Interest expense"]),
        }
    ar_net = current["11000"] + current["11900"]
    inv_avg = (current["12100"] + prior["12100"]) / 2
    rev26 = D(ratios["2026"]["net_revenue"])
    cogs26 = D(ratios["2026"]["cost_of_sales"])
    ratios["2026"]["sales_to_receivables"] = str((rev26 / ar_net).quantize(D("0.01")))
    ratios["2026"]["inventory_turnover"] = str((cogs26 / inv_avg).quantize(D("0.01")))
    key["fs.trial_balance_analytics"] = {
        "tb_foots": True, "definitions": {
            "movement": "current minus prior per account; flagged when |pct| > 10 "
                        "(or prior is zero and current is not) or |change| > 15,000",
            "current_ratio": "(cash + AR net + inventory + other current assets) / "
                             "(AP + accrued + line of credit)",
            "sales_to_receivables": "net revenue / year-end net A/R (11000 less "
                                    "allowance 11900)",
            "inventory_turnover": "cost of sales / average inventory (needs prior year)"},
        "movements_flagged": movements, "ratios": ratios}

    # Receivables: listing tie, arithmetic, allowance, credit balances
    positive = [(n, a, t) for n, a, t in aging if t > 0 and n != WRITE_OFF[0]]
    required = sum(sum(a[i] * ALLOWANCE_RATES[BUCKETS[i]] for i in range(5))
                   for _, a, _ in positive)
    required = m(required)
    # The same method on the aging as exported (Ridgeback still on it): what
    # a learner reperforms from the file they load.
    as_loaded = m(sum(sum(a[i] * ALLOWANCE_RATES[BUCKETS[i]] for i in range(5))
                      for _, a, t in aging if t > 0))
    key["ar.listing_tie"] = {
        "figures_basis": "allowance figures are the re-run aging (after the Ridgeback "
                         "write-off), the corrected scenario; as_loaded is the aging "
                         "as exported",
        "aging_total": str(aging_total), "tb_accounts_receivable": str(ar_per_tb),
        "difference": str(aging_total - ar_per_tb),
        "difference_explained": "Ridgeback Cycles 3,150.00 written off by JE 1066, "
                                "dated 06/30, entered 07/10 after the aging was "
                                "exported on 07/08. Not a misstatement; obtain a "
                                "re-run aging.",
        "aging_foots": True,
        "credit_balances": [{"customer": "Summit Loop Racing", "amount": "-1840.00",
                             "note": "overpayment; reclassify to a liability"}],
        "allowance_required": str(required),
        "allowance_basis": "approved rates on each customer's five buckets, debit-"
                           "balance customers only, after the Ridgeback write-off",
        "allowance_recorded": str(-current["11900"]),
        "allowance_shortfall": str(required + current["11900"]),
        "as_loaded": {"allowance_required": str(as_loaded),
                      "allowance_shortfall": str(as_loaded + current["11900"]),
                      "basis": "the same rates on the aging as exported, Ridgeback "
                               "Cycles included"},
    }

    # Receivables: nonstatistical confirmations (textbook ratio projection)
    by_name = {n: t for n, _, t in aging}
    key_items = [n for n, t in by_name.items() if t >= AR_TOLERABLE]
    sample = SAMPLE
    assert not set(sample) & set(key_items)
    key_known = m("2250.00")
    sample_mis = m("620.00")
    sample_book = sum(by_name[n] for n in sample)
    # the population the sample represents: every debit-balance customer below
    # the key threshold, excluding the written-off account
    remainder = [n for n, t in by_name.items()
                 if n not in key_items and t > 0 and n != WRITE_OFF[0]]
    remainder_book = sum(by_name[n] for n in remainder)
    projected = m(sample_mis / sample_book * remainder_book)
    loaded_book = remainder_book + by_name[WRITE_OFF[0]]
    loaded_projected = m(sample_mis / sample_book * loaded_book)
    key["ar.confirmations_nonstatistical"] = {
        "figures_basis": "projection over the re-run aging (after the Ridgeback "
                         "write-off), the corrected scenario; as_loaded is over the "
                         "aging as exported",
        "key_items": key_items, "sample_items": sample,
        "key_known_misstatement": str(key_known),
        "sample_misstatement": str(sample_mis), "sample_book": str(sample_book),
        "remainder_book": str(remainder_book), "projected_remainder": str(projected),
        "total_likely": str(key_known + projected),
        "as_loaded": {"remainder_book": str(loaded_book),
                      "projected_remainder": str(loaded_projected),
                      "total_likely": str(key_known + loaded_projected)},
        "tolerable": str(AR_TOLERABLE),
        "conclusion": "below tolerable; timing (Gallatin) and customer error "
                      "(Yellowstone) are not misstatements"}

    # Inventory: count <-> listing both directions, quantities summed per SKU
    counted = {}
    for tag, sku, desc, loc, qty, who in COUNT_TAGS:
        k = sku.strip().upper()
        if not k:
            continue
        counted[k] = counted.get(k, 0) + qty
    listed = {sku: (qty, val) for _, _, sku, qty, val in inv}
    shortages, not_counted, not_listed = [], [], []
    for sku, (qty, val) in listed.items():
        c = counted.get(sku)
        if c is None:
            not_counted.append({"sku": sku, "listed_qty": qty, "value": str(val)})
        elif c != qty:
            avg = val / qty
            shortages.append({"sku": sku, "listed_qty": qty, "counted_qty": c,
                              "difference_qty": c - qty,
                              "value": str(m(avg * (c - qty)))})
    for sku, c in counted.items():
        if sku not in listed:
            not_listed.append({"sku": sku, "counted_qty": c,
                               "value_at_invoice": str(m(CONSIGNED_UNIT_COST * c))})
    key["inventory.count_listing_trace"] = {
        "listing_total": str(inventory_total), "tb_inventory": str(current["12100"]),
        "tags_total": len(COUNT_TAGS), "void_tags": ["1017"],
        "tag_1016_sku_written_lowercase_with_space": True,
        "quantity_differences": shortages, "listed_not_counted": not_counted,
        "counted_not_listed": not_listed,
        "explanations": {
            "KV-CHN-11": "10 chains short; client books shrinkage (AJE-3)",
            "KV-HUB-DT": "4 hubs shipped and invoiced 06/29, inventory not relieved: "
                         "uncorrected misstatement 850.00",
            "KV-TUBE-29P": "Moraine consignment stock, correctly excluded"}}

    # Inventory: pricing projection (ratio of net misstatement to sampled value)
    rec = sum(listed[sku][1] for sku, *_ in PRICING)
    aud = sum(m(D(q) * D(u)) for _, q, u in PRICING)
    net = rec - aud
    proj = m(net / rec * inventory_total)
    key["inventory.pricing_projection"] = {
        "sample_recorded": str(rec), "sample_audited": str(aud),
        "net_overstatement_in_sample": str(net),
        "items_with_differences": {"KV-DER-11S": "231.00 over",
                                   "KV-SAD-CMP": "36.00 under"},
        "projected_to_listing": str(proj), "tolerable": str(INVENTORY_TOLERABLE),
        "conclusion": "below tolerable"}

    # Cash: reconciliation and cutoff
    cleared = {ref: -m(a) for d, desc, ref, a in CUTOFF if ref}
    key["cash.bank_reconciliation"] = {
        "checking": {"statement_ending": str(statement_end),
                     "register_balance": str(checking_book),
                     "tb_balance": str(current["10100"]), "refoots": True},
        "payroll": {"statement_ending": str(PAYROLL_REC_STATEMENT),
                    "register_balance": str(payroll_book),
                    "tb_balance": str(current["10200"]), "refoots": True},
        "outstanding_check_not_cleared_by_07-15": [{"check": "4421",
                                                    "amount": "3100.00"}],
        "outstanding_check_amount_differs": [{"check": "4425", "per_rec": "1780.00",
                                              "per_bank": str(cleared["4425"]),
                                              "misstatement": "90.00"}],
        "deposits_in_transit": [
            {"amount": "12650.00", "cleared": "07/07/2026", "days": 7,
             "exceeds_dit_max_days": True},
            {"amount": "4318.75", "cleared": "07/01/2026", "days": 1,
             "exceeds_dit_max_days": False}],
        "transfer_outstanding_40000_clears_07-01": "proper outstanding item"}
    key["cash.interbank_transfers"] = {
        "T-0615": "no exception", "T-0630": "no exception: on the checking "
        "reconciliation as an uncleared transfer",
        "T-0701": "EXCEPTION: received per books 06/30, disbursed per books 07/01 - "
                  "cash counted twice at year end; overstated 25,000.00 (AJE-1)"}

    # Completion: adjusting entries and uncorrected misstatements
    shortage_value = -D(shortages[0]["value"]) if shortages else D("0")
    shortfall = required + current["11900"]
    ajes = [("AJE-1", "10900 Transfers Clearing", m("25000"), None,
             "Record 07/01 transfer disbursement at year end"),
            ("AJE-1", "10100 Checking - First Prairie", None, m("25000"),
             "Record 07/01 transfer disbursement at year end"),
            ("AJE-2", "65000 Bad Debt Expense", shortfall, None,
             "Increase allowance to aging-based estimate"),
            ("AJE-2", "11900 Allowance for Doubtful Accounts", None, shortfall,
             "Increase allowance to aging-based estimate"),
            ("AJE-3", "51000 Inventory Shrinkage", shortage_value, None,
             "Count shortage KV-CHN-11"),
            ("AJE-3", "12100 Inventory Asset", None, shortage_value,
             "Count shortage KV-CHN-11")]
    write_csv(AUDITOR / "adjusting_entries.csv",
              ["Entry", "Account", "Debit", "Credit", "Description"],
              [(e, a, dr if dr is not None else "", cr if cr is not None else "", d)
               for e, a, dr, cr, d in ajes])
    adjusted = dict(current)
    num = lambda a: a.split(" ", 1)[0]
    for _, a, dr, cr, _ in ajes:
        adjusted[num(a)] += (dr or D("0")) - (cr or D("0"))
    assert sum(adjusted.values()) == 0
    key["fs.adjusted_trial_balance"] = {
        "entries_balance": True,
        "changed_accounts": {f"{n} {names[n]}": {"unadjusted": str(current[n]),
                                                 "adjusted": str(adjusted[n])}
                             for n in names if adjusted[n] != current[n]},
        "adjusted_tb_foots": True}

    ar_likely = projected - sample_mis
    inv_likely = proj - net
    misstatements = [  # description, ref, identified, likely, CA, NCA, CL, NCL, IBT
        ("Big Sky invoice priced above contract", "AR-C", m("2250"), D("0"),
         m("-2250"), D("0"), D("0"), D("0"), m("-2250")),
        ("AR confirmation sample: freight double-billed, projected", "AR-C",
         sample_mis, ar_likely, -projected, D("0"), D("0"), D("0"), -projected),
        ("Inventory pricing test projection", "INV-P", net, inv_likely,
         -(net + inv_likely), D("0"), D("0"), D("0"), -(net + inv_likely)),
        ("Hubs shipped 06/29 not relieved from inventory", "INV-C", m("850"), D("0"),
         m("-850"), D("0"), D("0"), D("0"), m("-850")),
        ("Check 4425 recorded at 1,780, cleared at 1,870", "CASH-R", m("90"), D("0"),
         m("-90"), D("0"), D("0"), D("0"), m("-90")),
        ("Summit Loop credit balance not reclassified", "AR-L", m("1840"), D("0"),
         m("1840"), D("0"), m("1840"), D("0"), D("0")),
    ]
    write_csv(AUDITOR / "uncorrected_misstatements.csv",
              ["Description", "WP Reference", "Identified", "Likely",
               "Current Assets", "Noncurrent Assets", "Current Liabilities",
               "Noncurrent Liabilities", "Income Before Taxes"], misstatements)
    cols = ["current_assets", "noncurrent_assets", "current_liabilities",
            "noncurrent_liabilities", "income_before_taxes"]
    totals = {c: sum(r[4 + i] for r in misstatements) for i, c in enumerate(cols)}
    key["completion.uncorrected_misstatements"] = {
        "sign_convention": "effect on the reported balance if corrected: negative "
                           "means the balance is overstated now (assets and income "
                           "fall when corrected); liabilities positive means they "
                           "rise when corrected",
        "totals": s(totals),
        "largest_absolute": str(max(abs(v) for v in totals.values())),
        "materiality": str(MATERIALITY),
        "conclusion": "every line total is below materiality; the Summit Loop "
                      "reclass nets to zero in income"}

    key["summary"] = {
        "tb_2026_debits": str(sum(v for v in current.values() if v > 0)),
        "aging_total": str(aging_total), "ar_per_tb": str(ar_per_tb),
        "inventory_total": str(inventory_total), "checking_book": str(checking_book),
        "payroll_book": str(payroll_book), "allowance_required": str(required),
        "allowance_shortfall": str(shortfall), "ar_projected": str(projected),
        "inv_projected": str(proj), "sum_totals": s(totals),
        "pretax_2026": ratios["2026"]["pretax_income"],
        "distributions": str(current["31000"]),
    }
    return key


if __name__ == "__main__":
    main()
