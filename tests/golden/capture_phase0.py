# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Phase 0 golden capture: freeze current noesi-cpa audit behavior.

Run with the noesi-cpa virtualenv, from the noesi-cpa checkout root (the
vendored KOMPOSOS import path requires that layout):

    cd C:/Users/JAMES/github/noesi-cpa
    .venv/Scripts/python.exe C:/Users/JAMES/github/noesi-assurance/tests/golden/capture_phase0.py

Outputs land in tests/golden/bundles/ next to this script. The bundles document
current behavior — they do not bless its accuracy. Every bundle is
self-contained: inputs are stored beside outputs so the port can replay them.

Captured, per RECOMMENDED_NOESI_CPA_ARCHITECTURE.md Phase 0:
  * the eleven procedure contracts and their source digest;
  * coverage compilation (full / partial / empty inventories), selection
    overlay, and the evidence-lifecycle unlock path — refusal behavior included;
  * deterministic executor goldens for the six incremental procedures,
    including the split-threshold refusal;
  * ingestion mapping metadata for a synthetic CSV (synonyms, refused
    headers, control total, row hashes);
  * SAD aggregation and readiness-gate blockers;
  * the Rockwood end-to-end unified report, with a determinism check;
  * the same-company/different-period disposition-collision defect;
  * dependency and source digests (pins).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BUNDLES = Path(__file__).resolve().parent / "bundles"
CPA_ROOT = Path(r"C:\Users\JAMES\github\noesi-cpa")


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str)


def digest(obj) -> str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def write_bundle(name: str, payload: dict) -> dict:
    path = BUNDLES / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False,
                               default=str), encoding="utf-8")
    return {"file": name, "sha256": digest(payload)}


def verdicts_to_dicts(findings) -> list[dict]:
    return [v.to_dict() for v in findings]


# ---------------------------------------------------------------- inventories

FULL_INVENTORY = {
    "Vendors": {"fields": ["vendor_number", "vendor_name"], "rows": 5,
                "control_total": None, "source_file": "vendors.csv"},
    "Employees": {"fields": ["employee_number", "employee_name"], "rows": 3,
                  "control_total": None, "source_file": "employees.csv"},
    "Purchase_orders": {"fields": ["po_number", "vendor_number", "po_amount",
                                   "po_date"], "rows": 4,
                        "control_total": 4000.0, "source_file": "po.csv"},
    "Vouchers": {"fields": ["voucher_number", "po_number", "vendor_number",
                            "voucher_amount", "voucher_date"], "rows": 4,
                 "control_total": 4000.0, "source_file": "vouchers.csv"},
    "Payments": {"fields": ["payment_number", "voucher_number", "vendor_number",
                            "payment_amount", "payment_date", "created_by",
                            "approved_by"], "rows": 4,
                 "control_total": 4000.0, "source_file": "payments.csv"},
    "Bank": {"fields": ["bank_txn_id", "payment_number", "amount", "bank_date"],
             "rows": 4, "control_total": 4000.0, "source_file": "bank.csv"},
    "GL": {"fields": ["gl_entry_id", "reference", "amount", "gl_date"],
           "rows": 4, "control_total": 4000.0, "source_file": "gl.csv"},
    "AP_control_balance": {"fields": ["period_end", "subledger_balance",
                                      "gl_balance"], "rows": 1,
                           "control_total": None, "source_file": "recon.csv"},
    "Goods_receipts": {"fields": ["receipt_number", "po_number",
                                  "received_amount"], "rows": 4,
                       "control_total": None, "source_file": "receipts.csv"},
    "Value_flows": {"fields": ["source_entity", "target_entity", "amount",
                               "flow_date"], "rows": 6,
                    "control_total": 6000.0, "source_file": "flows.csv"},
}

# Payments lacks approval fields; Vouchers lacks po_number; Bank/GL/receipts/
# flows/control-balance absent entirely. Exercises partial and blocked states.
PARTIAL_INVENTORY = {
    "Vendors": {"fields": ["vendor_number", "vendor_name"], "rows": 5,
                "control_total": None, "source_file": "vendors.csv"},
    "Purchase_orders": {"fields": ["po_number", "vendor_number", "po_amount",
                                   "po_date"], "rows": 4,
                        "control_total": 4000.0, "source_file": "po.csv"},
    "Vouchers": {"fields": ["voucher_number", "vendor_number", "voucher_amount",
                            "voucher_date"], "rows": 4,
                 "control_total": 4000.0, "source_file": "vouchers.csv"},
    "Payments": {"fields": ["payment_number", "voucher_number", "vendor_number",
                            "payment_amount", "payment_date"], "rows": 4,
                 "control_total": 4000.0, "source_file": "payments.csv"},
}


# ------------------------------------------------------------ executor inputs

EXECUTOR_CASES = {
    "ap.three_way_receipt_match": {
        "tables": {
            "Vouchers": [
                {"voucher_number": "V1", "po_number": "PO1", "voucher_amount": 100.0},
                {"voucher_number": "V2", "po_number": "PO2", "voucher_amount": 80.0},
                {"voucher_number": "V3", "po_number": "PO3", "voucher_amount": 50.0},
            ],
            "Goods_receipts": [
                {"receipt_number": "R1", "po_number": "PO1", "received_amount": 60.0},
                {"receipt_number": "R2", "po_number": "PO3", "received_amount": 50.0},
            ],
        },
        "policies": {},
    },
    "ap.subledger_gl_balance_tie": {
        "tables": {
            "AP_control_balance": [
                {"period_end": "2025-12-31", "subledger_balance": 125000.0,
                 "gl_balance": 120000.0},
                {"period_end": "2025-11-30", "subledger_balance": 90000.0,
                 "gl_balance": 90000.0},
            ],
        },
        "policies": {},
    },
    "ap.split_payment_review": {
        "tables": {
            "Payments": [
                {"payment_number": "P1", "vendor_number": "V1",
                 "payment_amount": 6000.0, "payment_date": "2025-03-01"},
                {"payment_number": "P2", "vendor_number": "V1",
                 "payment_amount": 5000.0, "payment_date": "2025-03-01"},
                {"payment_number": "P3", "vendor_number": "V2",
                 "payment_amount": 2000.0, "payment_date": "2025-03-01"},
            ],
        },
        "policies": {"split_threshold": "10000"},
    },
    "cash.bank_clearing": {
        "tables": {
            "Payments": [
                {"payment_number": "P1", "payment_amount": 500.0,
                 "payment_date": "2025-06-01"},
                {"payment_number": "P2", "payment_amount": 750.0,
                 "payment_date": "2025-06-02"},
            ],
            "Bank": [
                {"bank_txn_id": "B1", "payment_number": "P1", "amount": 500.0,
                 "bank_date": "2025-06-03"},
            ],
        },
        "policies": {},
    },
    "gl.payment_posting": {
        "tables": {
            "Payments": [
                {"payment_number": "P1", "voucher_number": "V1",
                 "payment_amount": 500.0, "payment_date": "2025-06-01"},
                {"payment_number": "P2", "voucher_number": "V2",
                 "payment_amount": 750.0, "payment_date": "2025-06-02"},
            ],
            "GL": [
                {"gl_entry_id": "G1", "reference": "P1", "amount": 500.0,
                 "gl_date": "2025-06-01"},
            ],
        },
        "policies": {},
    },
    "forensic.closed_value_flow": {
        "tables": {
            "Value_flows": [
                {"source_entity": "Company", "target_entity": "VendorA",
                 "amount": 1000.0, "flow_date": "2025-01-10"},
                {"source_entity": "VendorA", "target_entity": "Company",
                 "amount": 995.0, "flow_date": "2025-01-20"},
                {"source_entity": "Company", "target_entity": "VendorB",
                 "amount": 400.0, "flow_date": "2025-02-01"},
            ],
        },
        "policies": {},
    },
}

SYNTH_PAYMENTS_CSV = (
    "Check No,Invoice Number,Supplier ID,Paid Amount,Check Date,"
    "Entered By,Approver,Branch Memo\n"
    "1001,INV-1,V10,250.00,2025-04-01,pat,quinn,april run\n"
    "1002,INV-2,V11,1250.50,2025-04-02,pat,pat,april run\n"
    "1003,INV-3,V10,99.49,2025-04-03,ryu,quinn,april run\n"
)


def main() -> int:
    if not (CPA_ROOT / "noesis" / "audit").is_dir():
        print(f"noesi-cpa not found at {CPA_ROOT}", file=sys.stderr)
        return 1
    sys.path.insert(0, str(CPA_ROOT))
    BUNDLES.mkdir(parents=True, exist_ok=True)
    manifest_entries = []

    from noesis.audit import disposition, workflow
    from noesis.audit.disposition import summary_of_differences
    from noesis.audit.engagement_ingest import ingest_table
    from noesis.audit.procedure_execution import ENGINE_VERSION, execute_procedure
    from noesis.audit.procedures import (
        PROCEDURES,
        SCHEMA_VERSION,
        apply_evidence_lifecycle,
        apply_selections,
        compile_coverage,
    )

    # -- 1. contracts ------------------------------------------------------
    procedures_src = (CPA_ROOT / "noesis" / "audit" / "procedures.py").read_bytes()
    manifest_entries.append(write_bundle("contracts.json", {
        "schema_version": SCHEMA_VERSION,
        "engine_version": ENGINE_VERSION,
        "procedures_py_sha256": hashlib.sha256(procedures_src).hexdigest(),
        "contracts": [c.to_dict() for c in PROCEDURES],
    }))

    # -- 2. coverage compilation ------------------------------------------
    full = compile_coverage(FULL_INVENTORY, policies={"split_threshold": "10000"})
    partial = compile_coverage(PARTIAL_INVENTORY)
    empty = compile_coverage({})
    manifest_entries.append(write_bundle("coverage_full.json", {
        "inventory": FULL_INVENTORY,
        "policies": {"split_threshold": "10000"}, "coverage": full}))
    manifest_entries.append(write_bundle("coverage_partial.json", {
        "inventory": PARTIAL_INVENTORY, "policies": {}, "coverage": partial}))
    manifest_entries.append(write_bundle("coverage_empty.json", {
        "inventory": {}, "policies": {}, "coverage": empty}))

    # -- 3. selection overlay ---------------------------------------------
    selections = {"forensic.closed_value_flow": {
        "selected": False, "rationale": "out of scope for this engagement"}}
    manifest_entries.append(write_bundle("coverage_selection_overlay.json", {
        "base": "coverage_partial.json", "selections": selections,
        "coverage": apply_selections(partial, selections)}))

    # -- 4. evidence lifecycle overlay ------------------------------------
    # Fulfil the Vouchers.po_number field request (validated + approved);
    # leave a dataset request merely "received" to show it does not unlock.
    selected = apply_selections(partial, {})
    records = {}
    for request in selected["evidence_requests"]:
        if request["kind"] == "field" and request["item"] == "Vouchers.po_number":
            records[request["request_id"]] = {
                "status": "validated", "review_status": "approved",
                "evidence": [{"name": "vouchers_with_po.csv",
                              "sha256": "0" * 64, "stored_path": "unused"}]}
        elif request["kind"] == "dataset" and request["item"] == "Bank":
            records[request["request_id"]] = {
                "status": "received", "review_status": "not_reviewed",
                "evidence": [{"name": "bank.csv", "sha256": "1" * 64,
                              "stored_path": "unused"}]}
    manifest_entries.append(write_bundle("coverage_evidence_lifecycle.json", {
        "base": "coverage_partial.json", "records": records,
        "coverage": apply_evidence_lifecycle(selected, records)}))

    # -- 5. incremental executor goldens ----------------------------------
    for pid, case in EXECUTOR_CASES.items():
        findings, summary = execute_procedure(pid, case["tables"], case["policies"])
        name = "executor_" + pid.replace(".", "_") + ".json"
        manifest_entries.append(write_bundle(name, {
            "procedure_id": pid, "engine_version": ENGINE_VERSION,
            "tables": case["tables"], "policies": case["policies"],
            "summary": summary, "findings": verdicts_to_dicts(findings)}))

    # Refusal: split-payment review without an approved threshold.
    try:
        execute_procedure("ap.split_payment_review",
                          EXECUTOR_CASES["ap.split_payment_review"]["tables"], {})
        refusal = {"raised": False}
    except ValueError as exc:
        refusal = {"raised": True, "type": "ValueError", "message": str(exc)}
    # Unregistered procedure refusal. Phase 0 probed with
    # ap.payment_voucher_reference; that procedure gained an executor later,
    # so a re-capture must probe with an id that stays unregistered to
    # reproduce the same bundle bytes.
    try:
        execute_procedure("ap.never_registered_probe", {}, {})
        unregistered = {"raised": False}
    except ValueError as exc:
        unregistered = {"raised": True, "type": "ValueError", "message": str(exc)}
    manifest_entries.append(write_bundle("executor_refusals.json", {
        "split_threshold_missing": refusal,
        "unregistered_incremental_procedure": unregistered}))

    # -- 6. ingestion mapping ---------------------------------------------
    synth = BUNDLES / "ingest_input_payments.csv"
    synth.write_text(SYNTH_PAYMENTS_CSV, encoding="utf-8")
    table = ingest_table("Payments", str(synth))
    manifest_entries.append(write_bundle("ingest_mapping.json", {
        "role": "Payments", "input_file": "ingest_input_payments.csv",
        "input_sha256": hashlib.sha256(SYNTH_PAYMENTS_CSV.encode()).hexdigest(),
        "table": {
            attr: getattr(table, attr)
            for attr in ("source_file", "sha256", "rows_in", "column_map",
                         "unmapped_headers", "refused_fields", "control_total")
            if hasattr(table, attr)},
        "records": list(getattr(table, "records", []))}))

    # -- 7. SAD aggregation ------------------------------------------------
    sad_rows = [
        {"engagement": "Acme", "domain": "audit_procedure_run",
         "key": ["ap.subledger_gl_balance_tie", "2025-12-31"], "verdict": "CLASH",
         "score": 5000.0, "reason": "subledger does not tie to GL control",
         "evidence": {"finding_class": "PROVED_EXCEPTION"},
         "disposition": "unadjusted"},
        {"engagement": "Acme", "domain": "audit_procedure_run",
         "key": ["ap.three_way_receipt_match", "V2"], "verdict": "CLASH",
         "score": 300.0, "reason": "billed exceeds received",
         "evidence": {"finding_class": "PROVED_EXCEPTION"},
         "disposition": "adjusted"},
        {"engagement": "Acme", "domain": "audit_procedure_run",
         "key": ["ap.three_way_receipt_match", "V9"], "verdict": "CLASH",
         "score": 900.0, "reason": "billed exceeds received",
         "evidence": {"finding_class": "PROVED_EXCEPTION"},
         "disposition": "waived"},  # above clearly-trivial -> invalid waiver
        {"engagement": "Acme", "domain": "audit_procedure_run",
         "key": ["ap.split_payment_review", "V1", "2025-03-01"],
         "verdict": "TENSION", "score": 11000.0,
         "reason": "cluster below threshold",
         "evidence": {"finding_class": "STRUCTURAL_ANOMALY"},
         "disposition": "cleared"},  # not a SAD candidate: structural
    ]
    manifest_entries.append(write_bundle("sad_summary.json", {
        "rows": sad_rows, "materiality": 10000.0,
        "summary": summary_of_differences(
            [dict(r) for r in sad_rows], materiality=10000.0)}))

    # -- 8. readiness gates ------------------------------------------------
    blank_report = {"company": "Acme", "fye": "2025-12-31", "verdicts": [],
                    "procedure_coverage": partial}
    engagement = workflow.get_engagement(
        {"schema_version": workflow.SCHEMA_VERSION, "engagements": {}},
        blank_report)
    sad = summary_of_differences([], materiality=0.0)
    manifest_entries.append(write_bundle("readiness_blank.json", {
        "report": {"company": "Acme", "fye": "2025-12-31",
                   "procedure_coverage": "coverage_partial.json"},
        "readiness": workflow.readiness(blank_report, engagement, sad)}))

    # -- 9. Rockwood end-to-end, with determinism check --------------------
    from noesis.audit.rockwood import read_tables
    from noesis.audit.unified import unified_ap_audit
    acl = CPA_ROOT / "data/external/audit/acl_sample/extracted/ACL_Rockwood/ACL_Rockwood.ACL"
    first = unified_ap_audit(read_tables(str(acl)), company="Rockwood").to_dict()
    second = unified_ap_audit(read_tables(str(acl)), company="Rockwood").to_dict()
    deterministic = canonical(first) == canonical(second)
    manifest_entries.append(write_bundle("rockwood_unified.json", {
        "source": str(acl.relative_to(CPA_ROOT)),
        "deterministic_across_runs": deterministic,
        "report": first}))
    if not deterministic:
        print("WARNING: Rockwood unified report is not run-deterministic",
              file=sys.stderr)

    # -- 10. disposition-collision defect ---------------------------------
    verdict_row = {"verdict": {"domain": "audit_procedure_run",
                               "key": ["ap.subledger_gl_balance_tie", "2025-12-31"]}}
    fy2024 = {"company": "Acme", "fye": "2024-12-31"}
    fy2025 = {"company": "Acme", "fye": "2025-12-31"}
    manifest_entries.append(write_bundle("defect_disposition_collision.json", {
        "description": (
            "Same company, different fiscal periods: workflow engagement IDs "
            "differ, but disposition finding IDs are identical, so a shared "
            "dispositions.json cross-contaminates periods."),
        "engagement_ids": {"fy2024": workflow.engagement_id(fy2024),
                           "fy2025": workflow.engagement_id(fy2025)},
        "finding_ids": {
            "fy2024": workflow._finding_id(fy2024, verdict_row),
            "fy2025": workflow._finding_id(fy2025, verdict_row)},
        "collision": (workflow._finding_id(fy2024, verdict_row)
                      == workflow._finding_id(fy2025, verdict_row)),
        "disposition_finding_id_source": "noesis/audit/disposition.py:37",
        "non_transactional_writes": (
            "workflow.save() and disposition.save() are separate whole-file "
            "JSON writes (workflow.py:105, disposition.py:49); trail append is "
            "a third write. No transaction spans them; a crash between writes "
            "leaves inconsistent state, and concurrent HTTP threads can "
            "interleave read-modify-write cycles."),
    }))

    # -- 11. pins ----------------------------------------------------------
    freeze = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True, text=True, cwd=str(CPA_ROOT))
    audit_dir = CPA_ROOT / "noesis" / "audit"
    source_digests = {
        f"noesis/audit/{p.name}": hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(audit_dir.glob("*.py"))}
    seam = CPA_ROOT / "noesis" / "seam" / "verdict.py"
    source_digests["noesis/seam/verdict.py"] = hashlib.sha256(
        seam.read_bytes()).hexdigest()
    git_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
        cwd=str(CPA_ROOT))
    manifest_entries.append(write_bundle("pins.json", {
        "python": sys.version,
        "noesi_cpa_git_head": (git_head.stdout.strip()
                               if git_head.returncode == 0 else "not a git repo"),
        "pip_freeze": sorted(line for line in freeze.stdout.splitlines() if line),
        "source_sha256": source_digests}))

    # -- manifest ----------------------------------------------------------
    (BUNDLES / "MANIFEST.json").write_text(json.dumps({
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "capture_script": "capture_phase0.py",
        "purpose": ("Freeze current noesi-cpa behavior before the port. "
                    "Documents behavior; does not bless accuracy."),
        "bundles": manifest_entries,
    }, indent=2), encoding="utf-8")

    print(f"wrote {len(manifest_entries)} bundles to {BUNDLES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
