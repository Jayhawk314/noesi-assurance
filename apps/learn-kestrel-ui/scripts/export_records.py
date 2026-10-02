# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Write the case records the documents, trace and Excel pages show
(src/learn/kestrel-records.json).

Every figure on those pages is read here from the Kestrel case files, as the
client and the team gave them; nothing is typed by hand. The answers the
pages check against come from kestrel-key.json (scripts/export_key.py).

    .venv\\Scripts\\python apps\\learn-kestrel-ui\\scripts\\export_records.py
"""

from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[2] / "case-studies" / "kestrel-valley-cycle" / "data"
OUT = HERE.parent / "src" / "learn" / "kestrel-records.json"


def money(value) -> str:
    return f"{Decimal(str(value)):.2f}"


def sheet(name: str) -> list[tuple]:
    return list(openpyxl.load_workbook(DATA / "quickbooks" / f"{name}.xlsx").active
                .iter_rows(values_only=True))


def table(path: str) -> list[dict]:
    with open(DATA / path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def by_vendor(name: str) -> list[dict]:
    """Transaction List by Vendor, one dict per transaction, vendor carried down."""
    out, vendor, header = [], None, None
    for r in sheet(name):
        if header is None:
            header = r if r[1] == "Date" else None
            continue
        if r[0] and not str(r[0]).startswith("Total"):
            vendor = r[0]
        if r[1] and vendor:
            out.append({"vendor": vendor, "date": r[1], "type": r[3], "num": r[4],
                        "memo": r[6] or "", "account": r[7], "split": r[8] or "",
                        "amount": money(r[9])})
    return out


def reconciliation(name: str) -> dict:
    rows = sheet(name)
    head = rows[:rows.index(next(r for r in rows if r[0] == "Details"))]
    summary = {r[0]: money(r[4]) for r in head if r[0] and r[4] is not None
               and isinstance(r[4], (int, float))}
    section, uncleared = None, []
    for r in rows:
        if r[0] and str(r[0]).startswith("Uncleared") and "(" in str(r[0]):
            section = r[0]
        elif r[0] == "Total":
            section = None
        elif section and r[0] and r[0] != "DATE" and isinstance(r[4], (int, float)):
            uncleared.append({"section": section.split(" as of")[0], "date": r[0],
                              "type": r[1], "ref": r[2] or "", "payee": r[3],
                              "amount": money(r[4])})
    return {"title": rows[1][0], "reconciled": [rows[3][0], rows[4][0]],
            "summary": summary, "uncleared": uncleared}


def main() -> None:
    tlbv = by_vendor("Transaction_List_by_Vendor")
    vendors = [dict(zip(("name", "phone", "email", "contact", "address", "account"), r))
               for r in sheet("Vendor_Contact_List")[4:] if r[0] and r[0] != "Vendor"
               and r[0] == r[0].strip()]
    tb = [{"account": r[0], "debit": money(r[1]) if r[1] is not None else "",
           "credit": money(r[2]) if r[2] is not None else ""}
          for r in sheet("Trial_Balance_2026-06-30")[5:] if r[0] and (r[1] or r[2])]
    july = []
    for r in sheet("Journal_2026-07")[5:]:
        if r[6]:
            july.append({"date": r[1] or "", "type": r[2] or "", "num": r[3] or "",
                         "name": r[4] or "", "memo": r[5] or "", "account": r[6],
                         "debit": money(r[7]) if r[7] is not None else "",
                         "credit": money(r[8]) if r[8] is not None else ""})
    register = table("client/payroll_register_FY2026.csv")
    master = table("client/employee_master.csv")
    e16 = [r for r in register if r["Employee ID"] == "E16"]
    # The duplicated invoice MC-25009, its PO (1009), and the payment of each
    # bill: Moraine's 3/18 check and the look-alike vendor's 4/2 check. Found
    # by date, since check numbers moved when the case's checks were made
    # sequential (roadmap D10, 2 Oct 2026).
    moraine = [t for t in tlbv if t["vendor"].startswith("Moraine")
               and ("25009" in str(t["num"]) or t["num"] == "1009"
                    or (t["type"].startswith("Bill Payment")
                        and t["date"] in ("03/18/2026", "04/02/2026")))]
    assert sum(t["type"].startswith("Bill Payment") for t in moraine) == 2, moraine
    records = {
        "source": "Kestrel case files (case-studies/kestrel-valley-cycle/data); do not edit, "
                  "re-run scripts/export_records.py",
        "company": sheet("Trial_Balance_2026-06-30")[0][0],
        "vendors": vendors,
        "moraine": moraine,
        "hyalite": [t for t in tlbv if t["vendor"] == "Hyalite Fabrication" and t["type"] == "Bill"],
        "dm_checks": [t for t in tlbv if t["vendor"] == "DM Consulting"],
        "trial_balance": tb,
        "tb_total": [money(x) for x in next(r for r in sheet("Trial_Balance_2026-06-30")
                                           if r[0] == "TOTAL")[1:3]],
        "checking": reconciliation("Checking_Reconciliation"),
        "unpaid_alder": [dict(zip(("date", "type", "num", "due", "past_due", "amount", "open"),
                                  (r[1], r[2], r[3], r[4], r[5], money(r[6]), money(r[7]))))
                         for r in sheet("Unpaid_Bills")
                         if r[1] and r[3] and str(r[3]).startswith("AF-")],
        "je_1071": [x for x in july if x["memo"].startswith("Settle")],
        "representations": table("auditor/representation_letter.csv"),
        "misstatements": table("auditor/uncorrected_misstatements_final.csv"),
        "fa_06": next(r for r in table("client/fixed_asset_register.csv") if r["Asset ID"] == "FA-06"),
        "e07": next(r for r in master if r["Employee ID"] == "E07"),
        "master_ids": [r["Employee ID"] for r in master],
        "e16": {"payments": len(e16), "first": e16[0]["Check Date"], "last": e16[-1]["Check Date"],
                "gross": money(sum(Decimal(r["Gross Pay"]) for r in e16)),
                "net": money(sum(Decimal(r["Net Pay"]) for r in e16)),
                "sample": e16[:2]},
        "register_rows": len(register),
        "estimates": table("client/prior_year_estimates.csv"),
    }
    OUT.write_text(json.dumps(records, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
