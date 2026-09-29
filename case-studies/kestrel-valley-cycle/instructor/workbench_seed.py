# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Seed the Kestrel Valley case into a Workbench engagement — the Workbench
demo.

Everything goes through the real service path, as a team would do it: the
partner sets materiality, period, audit areas and settings; the preparer
uploads and maps each file; the reviewer approves each mapping; the
preparer loads the data and runs every executable procedure. Files the
Workbench cannot yet take raw from QuickBooks (trial balance, aging,
reconciliation, inventory, the Journal; findings K1-K14 and J1-J4) go in
hand-prepared, as in run_noesi.py pass B, and say so in their provenance.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
DATA = CASE / "data"
sys.path.insert(0, str(HERE))
import run_noesi  # noqa: E402  (the pass-B preparations)

CLIENT = "Kestrel Valley Cycle Supply (demo)"
PERIOD_END = "2026-06-30"
PERIOD_START = "2025-07-01"
PREPARER, REVIEWER = "demo-preparer", "demo-reviewer"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
CYCLES = ["planning", "journal_entries", "receivables", "payables", "payroll", "cash",
          "inventory", "ppe", "debt_equity", "accruals", "estimates", "completion"]


def _policies() -> dict:
    k2 = json.loads((HERE / "answer_key_part2.json").read_text(encoding="utf-8"))
    k3 = json.loads((HERE / "answer_key_part3.json").read_text(encoding="utf-8"))
    kp = json.loads((HERE / "answer_key_payables.json").read_text(encoding="utf-8"))
    return {"pm_allocation_multiple": "2.0", "analytics_threshold_pct": "10",
            "analytics_threshold_amount": "15000", "analytics_threshold_rule": "or",
            "je_manual_sources": "Journal Entry",
            "je_holidays": kp["je_testing_policies"]["je_holidays"],
            "ar_tolerable_misstatement": "9000",
            "inventory_tolerable_misstatement": "9000", "dit_max_days": "3",
            "split_threshold": "2500", "split_window_days": "7",
            "je_authorized_users": "Dana Merritt", "je_round_amount_threshold": "10000",
            "je_round_unit": "1000", "je_seldom_used_max": "1",
            "ar_allowance_rates": run_noesi.POLICIES["ar_allowance_rates"],
            **k2["policies"], **k3["policies"]}


def prep_journal(name: str):
    """The QuickBooks Journal report, one row per line (J1-J4 in the run
    findings): date, type, Num and name print only on a transaction's first
    line, so they are carried down; an entry is identified as the key
    identifies it (date, type, Num, name), because Num alone is blank for
    deposits and transfers and repeats across types."""
    def prep() -> bytes:
        rows, entry, header_seen, line, occurrences = [], None, False, 0, {}
        for r in run_noesi._sheet(name):
            cells = list(r[1:11]) + [None] * (10 - len(r[1:11]))
            date, kind, num, who, memo, account, debit, credit, created, by = cells
            if not header_seen:
                header_seen = date == "Date"
                continue
            if date:  # a transaction's first line
                base_id = " ".join(x for x in (
                    f"{date[6:]}-{date[:2]}-{date[3:5]}", kind, num or "(no num)",
                    who or "") if x).strip()
                occurrence = occurrences.get(base_id, 0) + 1
                occurrences[base_id] = occurrence
                # QuickBooks can emit separate same-day deposits with no Num
                # or name. Preserve the familiar key for the first, and give
                # later occurrences a stable discriminator instead of merging
                # distinct entries in the journal engine.
                entry_id = base_id if occurrence == 1 else f"{base_id} [{occurrence}]"
                entry = {"id": entry_id,
                         "date": date, "kind": kind, "created": created, "by": by}
                line = 0
            if entry is None or not account:
                continue  # a transaction's total row, or the footer
            line += 1
            rows.append((entry["id"], line, entry["date"], entry["kind"],
                         str(account).split(" ", 1)[0], debit if debit is not None else "",
                         credit if credit is not None else "", entry["created"],
                         entry["by"], memo or ""))
        return run_noesi._csv(["Entry ID", "Line", "Entry Date", "Transaction Type",
                               "Account", "Debit", "Credit", "Posted Date", "Posted By",
                               "Description"], rows)
    return prep


# (file or prepared label, role, prep function, QuickBooks recipe, load mode)
LOADS = [
    ("trial_balance_prepared.csv", "Trial_balance", run_noesi.prep_trial_balance, None, None),
    ("ar_aging_prepared.csv", "AR_listing", run_noesi.prep_aging, None, None),
    ("inventory_listing_prepared.csv", "Inventory_listing", run_noesi.prep_inventory, None, None),
    ("inventory_count_prepared.csv", "Inventory_count", run_noesi.prep_count, None, None),
    ("bank_reconciliation_prepared.csv", "Bank_reconciliation",
     run_noesi.prep_reconciliation, None, None),
    ("cutoff_statement_prepared.csv", "Cutoff_statement", run_noesi.prep_cutoff, None, None),
    ("transfers_prepared.csv", "Transfers", run_noesi.prep_transfers, None, None),
    ("pricing_tests_prepared.csv", "Pricing_tests", run_noesi.prep_pricing, None, None),
    ("adjusting_entries_prepared.csv", "Adjusting_entries",
     run_noesi.prep_adjusting_entries, None, None),
    ("auditor/confirmations.csv", "Confirmations", None, None, None),
    ("auditor/performance_materiality.csv", "Performance_materiality", None, None, None),
    ("quickbooks/Vendor_Contact_List.xlsx", "Vendors", None,
     "qbo.vendor_contact_list.vendors", None),
    ("quickbooks/Transaction_List_by_Vendor.xlsx", "Vouchers", None,
     "qbo.transaction_list_by_vendor.vouchers", None),
    ("quickbooks/Transaction_List_by_Vendor.xlsx", "Purchase_orders", None,
     "qbo.transaction_list_by_vendor.purchase_orders", None),
    ("quickbooks/Bill_Payment_List.xlsx", "Payments", None,
     "qbo.bill_payment_list.payments", None),
    ("journal_prepared.csv", "Journal_entries", prep_journal("Journal.xlsx"), None, None),
    ("journal_2026-07_prepared.csv", "Journal_entries", prep_journal("Journal_2026-07.xlsx"),
     None, "add"),
    ("client/payroll_register_FY2026.csv", "Payroll_register", None, None, None),
    ("client/employee_master.csv", "Payroll_master", None, None, None),
    ("client/fixed_asset_register.csv", "Fixed_assets", None, None, None),
    ("auditor/additions_vouching.csv", "Additions_vouching", None, None, None),
    ("client/debt_schedule.csv", "Debt_schedule", None, None, None),
    ("auditor/covenants.csv", "Covenants", None, None, None),
    ("client/equity_rollforward.csv", "Equity_rollforward", None, None, None),
    ("client/accruals_prepaids_schedule.csv", "Accrual_schedule", None, None, None),
    ("client/prior_year_estimates.csv", "Estimates", None, None, None),
    ("client/related_parties.csv", "Related_parties", None, None, None),
    ("auditor/representation_letter.csv", "Representations", None, None, None),
    ("auditor/uncorrected_misstatements_final.csv", "Misstatements", None, None, None),
]


def seed(service, partner: str) -> dict:
    """Create, load and run the Kestrel demo engagement (idempotent)."""
    existing = next((e for e in service.list_engagements()
                     if e["client_name"] == CLIENT and e["period_end"] == PERIOD_END),
                    None)
    if existing:
        return {"engagement_id": existing["engagement_id"], "seeded": False}
    eid = service.create_engagement(partner, CLIENT, PERIOD_END)["engagement_id"]
    service.assign_team(partner, eid, PREPARER, "preparer")
    service.assign_team(partner, eid, REVIEWER, "reviewer")
    service.update_workflow(partner, eid, "materiality", {
        "amount": 15000, "basis": "pretax income", "rationale": "about 4.6% of pretax income"})
    service.update_workflow(partner, eid, "period", {"start": PERIOD_START})
    service.update_workflow(partner, eid, "cycles", {"cycles": CYCLES})
    for name, value in _policies().items():
        service.update_workflow(partner, eid, "policy", {"name": name, "value": value})

    stored: dict[str, str] = {}
    refused = []
    for label, role, prep, recipe, mode in LOADS:
        try:
            if label not in stored:
                content = prep() if prep else (DATA / label).read_bytes()
                stored[label] = service.store_source(
                    PREPARER, eid, content=content,
                    media_type=XLSX if label.endswith(".xlsx") else "text/csv",
                    original_name=Path(label).name,
                    provenance=("Kestrel Valley case, prepared by hand from the "
                                "QuickBooks export" if prep else
                                f"Kestrel Valley case: {label}"))["artifact_id"]
            spec = service.propose_source_mapping(
                PREPARER, eid, role=role, artifact_id=stored[label],
                extraction={"recipe": recipe} if recipe else None)
            service.approve_source_mapping(REVIEWER, eid, spec["spec_id"])
            service.normalize_source(PREPARER, eid, spec["spec_id"], mode=mode)
        except (ValueError, KeyError) as exc:
            refused.append({"file": label, "role": role, "reason": str(exc)})

    # Map the client's own lead-schedule labels to statement lines, as the
    # preparer would: confirm each suggestion, and file the allowance
    # account (labelled "Accounts receivable") on the allowance line.
    for item in service.trial_balance_lines(eid)["labels"]:
        if not item["recognized"] and item["suggestion"]:
            service.update_workflow(PREPARER, eid, "line_mapping",
                                    {"label": item["label"], "line": item["suggestion"]})
    service.update_workflow(PREPARER, eid, "line_mapping",
                            {"account": "11900", "line": "allowance"})

    runs = 0
    for row in service.coverage(eid)["procedures"]:
        if row["status"] == "executable":
            service.run_procedure(PREPARER, eid, procedure_id=row["procedure_id"])
            runs += 1
    return {"engagement_id": eid, "seeded": True, "procedures_run": runs,
            "refused": refused,
            "team": {"partner": partner, "preparer": PREPARER, "reviewer": REVIEWER}}
