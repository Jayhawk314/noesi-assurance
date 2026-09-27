# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Run Noesi, unchanged, on the Kestrel Valley case and print what happens.

Pass A loads the files exactly as delivered. Pass B loads the same figures
after the Excel preparation a preparer would do by hand (see ``prep_*``),
so a procedure's logic can be judged apart from whether it can read the
QuickBooks shape. Nothing here changes the engine; every error is printed,
not hidden, and compared with ANSWER-KEY.md in NOESI-RUN-FINDINGS.md.

    .venv\\Scripts\\python case-studies\\kestrel-valley-cycle\\instructor\\run_noesi.py [A|B]
"""

from __future__ import annotations

import csv
import io
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

import openpyxl

CASE = Path(__file__).resolve().parent.parent
DATA = CASE / "data"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PARTNER, PREPARER, REVIEWER = "kv-partner", "kv-preparer", "kv-reviewer"

AS_DELIVERED = [  # (file, role)
    ("quickbooks/Trial_Balance_2026-06-30.xlsx", "Trial_balance"),
    ("quickbooks/Trial_Balance_2025-06-30.xlsx", "Trial_balance"),
    ("quickbooks/AR_Aging_Summary.xlsx", "AR_listing"),
    ("quickbooks/Inventory_Valuation_Summary.xlsx", "Inventory_listing"),
    ("client/count_tags_2026-06-30.csv", "Inventory_count"),
    ("quickbooks/Checking_Reconciliation.xlsx", "Bank_reconciliation"),
    ("quickbooks/Payroll_Checking_Reconciliation.xlsx", "Bank_reconciliation"),
    ("bank/first_prairie_xxxx2208_2026-07-01_to_2026-07-15.csv", "Cutoff_statement"),
    ("auditor/confirmations.csv", "Confirmations"),
    ("auditor/pricing_tests.csv", "Pricing_tests"),
    ("auditor/interbank_transfers.csv", "Transfers"),
    ("auditor/performance_materiality.csv", "Performance_materiality"),
    ("auditor/adjusting_entries.csv", "Adjusting_entries"),
    ("auditor/uncorrected_misstatements.csv", "Misstatements"),
]

POLICIES = {  # the partner's approved values, as README.md states them
    "pm_allocation_multiple": "2.0",
    "ar_tolerable_misstatement": "9000",
    "inventory_tolerable_misstatement": "9000",
    "analytics_threshold_pct": "10",
    "analytics_threshold_amount": "15000",
    "ar_allowance_rates": "0.01,0.02,0.05,0.15,0.40",
    "dit_max_days": "3",
}
CYCLES = ["planning", "receivables", "cash", "inventory", "completion"]


# ---------------------------------------------------------------- pass B prep
def _sheet(name):
    return list(openpyxl.load_workbook(DATA / "quickbooks" / name)
                .active.iter_rows(values_only=True))


def _csv(header, rows) -> bytes:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(header)
    w.writerows(rows)
    return out.getvalue().encode("utf-8")


def _read_csv(rel):
    with (DATA / rel).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def prep_trial_balance() -> bytes:
    """One row per account: number, name, signed balance (Debit - Credit),
    prior-year balance from the second export, the auditor's lead line."""
    lines = {r["Account"]: r["Lead Schedule Line"]
             for r in _read_csv("auditor/tb_line_mapping.csv")}

    def balances(name):
        out = {}
        for r in _sheet(name)[5:]:
            if r[0] and r[0][:1].isdigit():
                out[r[0]] = Decimal(str(r[1] or 0)) - Decimal(str(r[2] or 0))
        return out
    cur = balances("Trial_Balance_2026-06-30.xlsx")
    pri = balances("Trial_Balance_2025-06-30.xlsx")
    rows = []
    for acct, line in lines.items():
        number, name = acct.split(" ", 1)
        rows.append((number, name, f"{cur.get(acct, 0):.2f}", f"{pri.get(acct, 0):.2f}",
                     line))
    return _csv(["Account", "Description", "Balance", "Prior Balance", "Line"], rows)


def prep_aging() -> bytes:
    """Customer rows only (no TOTAL); five QuickBooks buckets kept by name."""
    rows = [r for r in _sheet("AR_Aging_Summary.xlsx")[5:]
            if r[0] and r[0] != "TOTAL" and r[6] is not None]
    return _csv(["Customer", "Current", "1 - 30", "31 - 60", "61 - 90", "91 and over",
                 "Balance"],
                [(r[0], *[f"{Decimal(str(v or 0)):.2f}" for v in r[1:7]]) for r in rows])


def prep_inventory() -> bytes:
    """Item rows only: SKU, description, qty, unit cost, extended cost."""
    rows = [r for r in _sheet("Inventory_Valuation_Summary.xlsx")[5:] if r[1]]
    return _csv(["Stock Number", "Description", "Quantity", "Unit Cost", "Cost"],
                [(r[1], r[0].strip(), r[2], f"{r[4]:.4f}", f"{Decimal(str(r[3])):.2f}")
                 for r in rows])


def prep_count() -> bytes:
    """The count tags as delivered, only the columns renamed."""
    rows = _read_csv("client/count_tags_2026-06-30.csv")
    return _csv(["Stock Number", "Description", "Quantity", "Tag"],
                [(r["Item SKU"], r["Description"], r["Qty Counted"], r["Tag #"])
                 for r in rows])


def prep_reconciliation() -> bytes:
    """One row per reconciling item, both accounts, item types spelled out."""
    out = []
    for name, account in (("Checking_Reconciliation.xlsx", "checking"),
                          ("Payroll_Checking_Reconciliation.xlsx", "payroll")):
        rows = _sheet(name)
        section = None
        for r in rows:
            label = r[0] or ""
            if label == "Statement ending balance":
                out.append((account, "bank balance", "", f"{r[4]:.2f}", "2026-06-30"))
            elif label.startswith("Register balance"):
                out.append((account, "book balance", "", f"{r[4]:.2f}", "2026-06-30"))
            elif label.startswith("Uncleared checks"):
                section = "outstanding check"
            elif label.startswith("Uncleared deposits"):
                section = "deposit in transit"
            elif label in ("Total", "Additional Information") or not label:
                if label == "Total":
                    section = None
            elif section and label[:2].isdigit():
                m, d, y = label.split("/")
                out.append((account, section, r[2] or r[1], f"{abs(r[4]):.2f}",
                            f"{y}-{m}-{d}"))
    return _csv(["Account", "Item Type", "Reference", "Amount", "Date"], out)


def prep_cutoff() -> bytes:
    """Bank rows with the account named and the amount unsigned."""
    rows = _read_csv("bank/first_prairie_xxxx2208_2026-07-01_to_2026-07-15.csv")
    out = []
    for r in rows:
        m, d, y = r["Posting Date"].split("/")
        kind = "check" if r["Check or Slip #"] else (
            "deposit" if Decimal(r["Amount"]) > 0 else "transfer")
        out.append(("checking", r["Check or Slip #"], kind,
                    f"{abs(Decimal(r['Amount'])):.2f}", f"{y}-{m}-{d}"))
    return _csv(["Account", "Reference", "Type", "Amount", "Cleared Date"], out)


def prep_transfers() -> bytes:
    rows = _read_csv("auditor/interbank_transfers.csv")
    iso = lambda s: f"{s[6:]}-{s[:2]}-{s[3:5]}"
    acct = {"Checking": "checking", "Payroll Checking": "payroll"}
    return _csv(["Transfer ID", "Amount", "From Account", "To Account",
                 "Disbursed Books", "Disbursed Bank", "Received Books", "Received Bank"],
                [(r["Transfer"], r["Amount"], acct[r["From Account"]],
                  acct[r["To Account"]], iso(r["Disbursed per Books"]),
                  iso(r["Disbursed per Bank"]), iso(r["Received per Books"]),
                  iso(r["Received per Bank"])) for r in rows])


def prep_adjusting_entries() -> bytes:
    """Account number only, to match the prepared trial balance."""
    rows = _read_csv("auditor/adjusting_entries.csv")
    return _csv(["Entry", "Account", "Debit", "Credit", "Description"],
                [(r["Entry"], r["Account"].split(" ", 1)[0], r["Debit"], r["Credit"],
                  r["Description"]) for r in rows])


def prep_pricing() -> bytes:
    """The auditor's pricing sheet with the SKU column renamed."""
    rows = _read_csv("auditor/pricing_tests.csv")
    return _csv(["Stock Number", "Recorded Cost", "Audited Cost"],
                [(r["Item SKU"], r["Recorded Cost"], r["Audited Cost"]) for r in rows])


PREPARED = [  # (label, role, builder or delivered file)
    ("trial_balance_prepared.csv", "Trial_balance", prep_trial_balance),
    ("ar_aging_prepared.csv", "AR_listing", prep_aging),
    ("inventory_listing_prepared.csv", "Inventory_listing", prep_inventory),
    ("inventory_count_prepared.csv", "Inventory_count", prep_count),
    ("bank_reconciliation_prepared.csv", "Bank_reconciliation", prep_reconciliation),
    ("cutoff_statement_prepared.csv", "Cutoff_statement", prep_cutoff),
    ("transfers_prepared.csv", "Transfers", prep_transfers),
    ("adjusting_entries_prepared.csv", "Adjusting_entries", prep_adjusting_entries),
    ("confirmations.csv", "Confirmations", "auditor/confirmations.csv"),
    ("pricing_tests_prepared.csv", "Pricing_tests", prep_pricing),
    ("performance_materiality.csv", "Performance_materiality",
     "auditor/performance_materiality.csv"),
    ("uncorrected_misstatements.csv", "Misstatements",
     "auditor/uncorrected_misstatements.csv"),
]


# ---------------------------------------------------------------- the run
def run(pass_name: str) -> int:
    from assurance_application.service import WorkbenchService
    from assurance_artifacts.signing import LocalKeyStore
    from assurance_artifacts.vault import ArtifactVault
    from assurance_persistence.database import connect, migrate
    from assurance_persistence.legacy_import import ensure_tenant

    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        conn = connect(root / "control.db")
        migrate(conn)
        service = WorkbenchService(conn, ArtifactVault(root / "vault"),
                                   ensure_tenant(conn, "kestrel-verify"),
                                   keystore=LocalKeyStore(root / "keys"))
        eid = service.create_engagement(PARTNER, "Kestrel Valley Cycle Supply",
                                        "2026-06-30")["engagement_id"]
        service.assign_team(PARTNER, eid, PREPARER, "preparer")
        service.assign_team(PARTNER, eid, REVIEWER, "reviewer")
        service.update_workflow(PARTNER, eid, "materiality",
                                {"amount": 15000, "basis": "pretax income",
                                 "rationale": "about 4.6% of pretax income"})
        service.update_workflow(PARTNER, eid, "cycles", {"cycles": CYCLES})

        if pass_name == "A":
            items = [(rel, role, (DATA / rel).read_bytes(),
                      XLSX if rel.endswith(".xlsx") else "text/csv")
                     for rel, role in AS_DELIVERED]
        else:
            items = [(label, role,
                      src() if callable(src) else (DATA / src).read_bytes(), "text/csv")
                     for label, role, src in PREPARED]

        print(f"== Pass {pass_name}: ingestion ==")
        for name, role, content, media in items:
            print(f"\n  {name} -> {role}")
            try:
                art = service.store_source(PREPARER, eid, content=content,
                                           media_type=media,
                                           original_name=Path(name).name)
                prop = service.propose_source_mapping(PREPARER, eid, role=role,
                                                      artifact_id=art["artifact_id"])
                print(f"    header row {(prop['extraction'] or {}).get('header_row', '-')}"
                      f"  map {prop['column_map']}")
                if prop["unmapped_headers"]:
                    print(f"    unmapped {prop['unmapped_headers']}")
                if prop["refused_fields"]:
                    print(f"    refused {prop['refused_fields']}")
                service.approve_source_mapping(REVIEWER, eid, prop["spec_id"])
                rec = service.normalize_source(PREPARER, eid,
                                               prop["spec_id"])["reconciliation"]
                print(f"    loaded {rec['rows_loaded']} rejected {rec['rows_rejected']}"
                      f"  {({k: v for k, v in rec.items() if k not in ('rows_loaded', 'rows_rejected')})}")
            except Exception as exc:  # recorded, not hidden
                print(f"    ERROR {type(exc).__name__}: {exc}")

        print("\n== Policies ==")
        for name, value in POLICIES.items():
            try:
                service.update_workflow(PARTNER, eid, "policy",
                                        {"name": name, "value": value})
                print(f"  set {name}={value}")
            except Exception as exc:
                print(f"  ERROR {name}: {exc}")

        coverage = service.coverage(eid)
        print("\n== Coverage ==")
        print("  " + ", ".join(f"{k}={v}" for k, v in sorted(coverage["summary"].items())))
        for row in coverage["procedures"]:
            extra = {k: row[k] for k in ("missing", "missing_roles", "missing_policies",
                                         "reason") if row.get(k)}
            print(f"  {row['procedure_id']:<38} {row['status']:<13} {extra or ''}")

        print("\n== Runs ==")
        for row in coverage["procedures"]:
            if row["status"] not in ("executable", "partial"):
                continue
            pid = row["procedure_id"]
            try:
                r = service.run_procedure(PREPARER, eid, procedure_id=pid)
                print(f"  {r['status']:<9} {pid:<38} findings {r['findings']:>3}  "
                      f"{r['summary']}  {r['error'] or ''}")
            except Exception as exc:
                print(f"  RAISED    {pid:<38} {type(exc).__name__}: {exc}")

        print("\n== Findings ==")
        by_pid: dict[str, list] = {}
        for f in service.findings(eid):
            by_pid.setdefault(f["procedure_id"], []).append(f)
        for pid in sorted(by_pid):
            print(f"\n  {pid} — {len(by_pid[pid])}")
            for f in by_pid[pid]:
                v = f["verdict"]
                key = " · ".join(str(p) for p in v["key"][1:]) or str(v["key"][0])
                print(f"    [{v['verdict']:<9}] {key:<32} {v['reason']}")
        print(f"\n== Total findings: {sum(len(v) for v in by_pid.values())} ==")
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(run((sys.argv[1:] or ["A"])[0].upper()))
