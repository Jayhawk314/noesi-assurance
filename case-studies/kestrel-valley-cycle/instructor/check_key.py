# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Re-derive the main answer-key figures from the files on disk.

A second path to the same numbers: this reads the exported workbooks and
CSVs (not generate.py's constants) and checks them against answer_key.json.
It imports nothing from Noesi.

    python case-studies/kestrel-valley-cycle/instructor/check_key.py
"""

from __future__ import annotations

import csv
import json
from decimal import Decimal as D
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
KEY = json.loads((ROOT / "instructor" / "answer_key.json").read_text(encoding="utf-8"))
CENT = D("0.01")


def sheet(name):
    return list(openpyxl.load_workbook(ROOT / "data" / "quickbooks" / name)
                .active.iter_rows(values_only=True))


def num(v):
    return D(str(v)).quantize(CENT) if v not in (None, "") else D("0")


def rows_csv(*parts):
    with (ROOT / "data").joinpath(*parts).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check(label, got, want):
    ok = D(str(got)) == D(str(want))
    print(f"{'ok ' if ok else 'BAD'} {label}: {got} (key {want})")
    return ok


def main():
    results = []
    # Trial balance: foots; account lookup by leading number
    tb = {}
    for r in sheet("Trial_Balance_2026-06-30.xlsx")[5:]:
        if r[0] and r[0][:1].isdigit():
            tb[r[0].split(" ", 1)[0]] = num(r[1]) - num(r[2])
    results.append(check("TB nets to zero", sum(tb.values()), 0))

    # Aging: total, five buckets, allowance at approved rates
    rates = [D("0.01"), D("0.02"), D("0.05"), D("0.15"), D("0.40")]
    aging = [r for r in sheet("AR_Aging_Summary.xlsx")[5:] if r[0] and r[0] != "TOTAL"
             and r[6] is not None]
    total = sum(num(r[6]) for r in aging)
    results.append(check("aging total", total, KEY["ar.listing_tie"]["aging_total"]))
    results.append(check("aging - TB A/R", total - tb["11000"],
                         KEY["ar.listing_tie"]["difference"]))
    allowance = sum(sum(num(r[1 + i]) * rates[i] for i in range(5)) for r in aging
                    if num(r[6]) > 0 and r[0] != "Ridgeback Cycles").quantize(CENT)
    results.append(check("allowance required", allowance,
                         KEY["ar.listing_tie"]["allowance_required"]))
    loaded = sum(sum(num(r[1 + i]) * rates[i] for i in range(5)) for r in aging
                 if num(r[6]) > 0).quantize(CENT)
    results.append(check("allowance required, aging as loaded", loaded,
                         KEY["ar.listing_tie"]["as_loaded"]["allowance_required"]))
    net_ar = tb["11000"] + tb["11900"]
    revenue = -(tb["40000"] + tb["40500"])
    results.append(check("sales to year-end net receivables",
                         (revenue / net_ar).quantize(CENT),
                         KEY["fs.trial_balance_analytics"]["ratios"]["2026"]
                         ["sales_to_receivables"]))

    # Inventory: listing total, count by SKU (trimmed, upper-cased), differences
    listing = {r[1]: (int(r[2]), num(r[3]))
               for r in sheet("Inventory_Valuation_Summary.xlsx")[5:] if r[1]}
    inv_total = sum(v for _, v in listing.values())
    results.append(check("inventory total = TB", inv_total, tb["12100"]))
    counted = {}
    for r in rows_csv("client", "count_tags_2026-06-30.csv"):
        sku = r["Item SKU"].strip().upper()
        if sku:
            counted[sku] = counted.get(sku, 0) + int(r["Qty Counted"])
    diffs = sorted(s for s in listing if s in counted and counted[s] != listing[s][0])
    results.append(check("SKUs with quantity differences", len(diffs), 1))
    results.append(check("listed not counted", len(set(listing) - set(counted)), 1))
    results.append(check("counted not listed", len(set(counted) - set(listing)), 1))

    # Pricing projection
    pricing = rows_csv("auditor", "pricing_tests.csv")
    rec = sum(num(r["Recorded Cost"]) for r in pricing)
    aud = sum(num(r["Audited Cost"]) for r in pricing)
    results.append(check("pricing projection", ((rec - aud) / rec * inv_total)
                         .quantize(CENT),
                         KEY["inventory.pricing_projection"]["projected_to_listing"]))

    # Confirmations: ratio projection over the sample stratum
    conf = rows_csv("auditor", "confirmations.csv")
    by_name = {r[0]: num(r[6]) for r in aging}
    sample = [r for r in conf if r["Stratum"] == "sample"]
    key_names = {r["Customer"] for r in conf if r["Stratum"] == "key"}
    mis = sum(num(r["Client Misstatement"]) for r in sample
              if r["Classification"] == "client_misstatement")
    sbook = sum(num(r["Book Value"]) for r in sample)
    remainder = sum(v for n, v in by_name.items()
                    if n not in key_names and v > 0 and n != "Ridgeback Cycles")
    results.append(check("AR projected remainder", (mis / sbook * remainder).quantize(CENT),
                         KEY["ar.confirmations_nonstatistical"]["projected_remainder"]))
    loaded_remainder = sum(v for n, v in by_name.items() if n not in key_names and v > 0)
    results.append(check("AR projected remainder, aging as loaded",
                         (mis / sbook * loaded_remainder).quantize(CENT),
                         KEY["ar.confirmations_nonstatistical"]["as_loaded"]
                         ["projected_remainder"]))

    # Checking reconciliation: register balance = TB
    rec_rows = sheet("Checking_Reconciliation.xlsx")
    register = next(r[4] for r in rec_rows if r[0] and r[0].startswith("Register balance"))
    results.append(check("checking register = TB", num(register), tb["10100"]))

    # Adjusting entries balance
    aje = rows_csv("auditor", "adjusting_entries.csv")
    results.append(check("AJEs balance", sum(num(r["Debit"]) - num(r["Credit"])
                                             for r in aje), 0))

    # Uncorrected misstatements, income column
    sum_rows = rows_csv("auditor", "uncorrected_misstatements.csv")
    results.append(check("SUM income effect",
                         sum(num(r["Income Before Taxes"]) for r in sum_rows),
                         KEY["completion.uncorrected_misstatements"]["totals"]
                         ["income_before_taxes"]))

    print(f"\n{sum(results)}/{len(results)} checks agree")
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
