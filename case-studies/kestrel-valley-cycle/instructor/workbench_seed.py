# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Seed the Kestrel Valley case into a Workbench engagement — the Workbench
demo.

Everything goes through the real service path, as a team would do it: the
partner sets materiality, period, audit areas and settings; the preparer
uploads and maps each file; the reviewer approves each mapping; the
preparer loads the data and runs every executable procedure. The QuickBooks
exports go in raw through their recipes (trial balance, A/R aging, inventory
valuation, the Journal, the payables reports), built on real QuickBooks
Online exports. Files the Workbench cannot yet take raw (the bank
reconciliation reports, which QuickBooks gives only as PDF; the bank cutoff
statement; auditor schedules) go in hand-prepared, as in run_noesi.py pass B,
and say so in their provenance.
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


# (file or prepared label, role, prep function, QuickBooks recipe, load mode)
LOADS = [
    ("quickbooks/AR_Aging_Summary.xlsx", "AR_listing", None,
     "qbo.ar_aging_summary.ar_listing", None),
    ("quickbooks/Inventory_Valuation_Summary.xlsx", "Inventory_listing", None,
     "qbo.inventory_valuation_summary.inventory_listing", None),
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
    ("quickbooks/Transaction_List_by_Vendor.xlsx", "Direct_payments", None,
     "qbo.transaction_list_by_vendor.direct_payments", None),
    ("quickbooks/Journal.xlsx", "Journal_entries", None,
     "qbo.journal_created.journal_entries", None),
    ("quickbooks/Journal_2026-07.xlsx", "Journal_entries", None,
     "qbo.journal_created.journal_entries", "add"),
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

    # The trial balance: QuickBooks exports one date per report, so this
    # year's and last year's Trial Balance exports are built into one
    # schedule (Balance, Prior Balance), then mapped, approved and loaded.
    for label in ("quickbooks/Trial_Balance_2026-06-30.xlsx",
                  "quickbooks/Trial_Balance_2025-06-30.xlsx"):
        stored[label] = service.store_source(
            PREPARER, eid, content=(DATA / label).read_bytes(), media_type=XLSX,
            original_name=Path(label).name,
            provenance=f"Kestrel Valley case: {label}")["artifact_id"]
    built_tb = service.build_trial_balance(
        PREPARER, eid, current_artifact_id=stored["quickbooks/Trial_Balance_2026-06-30.xlsx"],
        prior_artifact_id=stored["quickbooks/Trial_Balance_2025-06-30.xlsx"])
    [item] = service.propose_source_mappings(
        PREPARER, eid, [{"artifact_id": built_tb["artifact_id"], "role": "Trial_balance"}]
    )["results"]
    service.approve_source_mapping(REVIEWER, eid, item["spec_id"])
    service.normalize_source(PREPARER, eid, item["spec_id"])

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

    # Map each account to a statement line, as the preparer would: a
    # QuickBooks trial balance carries no line, so the auditor's lead-schedule
    # mapping (auditor/tb_line_mapping.csv) gives each account's label and the
    # preparer confirms the line it suggests; the allowance account (labelled
    # "Accounts receivable") goes on the allowance line.
    from procedures_cycles.statements import suggest_line
    for row in run_noesi._read_csv("auditor/tb_line_mapping.csv"):
        line = suggest_line(row["Lead Schedule Line"])
        if line:
            service.update_workflow(PREPARER, eid, "line_mapping",
                                    {"account": row["Account"].split(" ", 1)[0],
                                     "line": line})
    service.update_workflow(PREPARER, eid, "line_mapping",
                            {"account": "11900", "line": "allowance"})

    # The A/P tie: Unpaid Bills (the subledger) against the trial balance's
    # Accounts Payable account (the ledger), built, reviewed and loaded like
    # any other schedule. Kestrel has no General Ledger export.
    service.update_workflow(partner, eid, "policy", {"name": "ap_control_accounts",
                                                     "value": "20000"})
    unpaid = service.store_source(
        PREPARER, eid, content=(DATA / "quickbooks/Unpaid_Bills.xlsx").read_bytes(),
        media_type=XLSX, original_name="Unpaid_Bills.xlsx",
        provenance="Kestrel Valley case: quickbooks/Unpaid_Bills.xlsx")["artifact_id"]
    built = service.build_ap_control_balance(PREPARER, eid, subledger_artifact_id=unpaid,
                                             ledger_artifact_id="trial_balance")
    [item] = service.propose_source_mappings(
        PREPARER, eid, [{"artifact_id": built["artifact_id"]}])["results"]
    service.approve_source_mapping(REVIEWER, eid, item["spec_id"])
    service.normalize_source(PREPARER, eid, item["spec_id"])

    # The three confirmation evaluations start left out: the auditor picks
    # one. Kestrel's team evaluates its confirmations nonstatistically (the
    # key's ar.confirmations_nonstatistical), so the partner includes that
    # method and records why the other two are not used.
    service.update_workflow(partner, eid, "procedure_selection", {
        "procedure_id": "ar.confirmations_nonstatistical", "selected": True})
    for pid in ("ar.confirmations_mus", "ar.confirmations_difference"):
        service.update_workflow(partner, eid, "procedure_selection", {
            "procedure_id": pid, "selected": False,
            "rationale": "the confirmations are evaluated nonstatistically; "
                         "this method is not the one chosen for the audit"})
    # The first-digit test starts left out (it needs the auditor's minimum
    # population). Kestrel's key has no lines for it yet (roadmap D10), so
    # the demo leaves it out and says so rather than show unchecked results.
    service.update_workflow(partner, eid, "procedure_selection", {
        "procedure_id": "forensic.benford_first_digit", "selected": False,
        "rationale": "not yet in the Kestrel answer key (roadmap D10); run it "
                     "by setting benford_min_population and including it"})

    runs = 0
    for row in service.coverage(eid)["procedures"]:
        if row["status"] == "executable" and row.get("selected", True):
            service.run_procedure(PREPARER, eid, procedure_id=row["procedure_id"])
            runs += 1
    return {"engagement_id": eid, "seeded": True, "procedures_run": runs,
            "refused": refused,
            "team": {"partner": partner, "preparer": PREPARER, "reviewer": REVIEWER}}
