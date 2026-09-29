# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Run Noesi, unchanged, on Kestrel part 1 (payables and the journal) and
print what it finds, for comparison with answer_key_payables.json.

Files load the way a preparer would: QuickBooks recipes where Noesi has one,
an ordinary mapping otherwise. Every error is printed, never hidden.

    .venv\\Scripts\\python case-studies\\kestrel-valley-cycle\\instructor\\run_part1.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

CASE = Path(__file__).resolve().parent.parent
QBO = CASE / "data" / "quickbooks"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
P, R, S = "kv-partner", "kv-preparer", "kv-reviewer"

LOADS = [  # file, role, recipe or None, mode for a role that already has data
    ("Vendor_Contact_List.xlsx", "Vendors", "qbo.vendor_contact_list.vendors", None),
    ("Transaction_List_by_Vendor.xlsx", "Vouchers",
     "qbo.transaction_list_by_vendor.vouchers", None),
    ("Transaction_List_by_Vendor.xlsx", "Purchase_orders",
     "qbo.transaction_list_by_vendor.purchase_orders", None),
    ("Bill_Payment_List.xlsx", "Payments", "qbo.bill_payment_list.payments", None),
    ("Journal.xlsx", "Journal_entries", None, None),
]
POLICIES = {"split_threshold": "2500", "split_window_days": "7",
            "je_authorized_users": "Dana Merritt", "je_round_amount_threshold": "10000",
            "je_round_unit": "1000", "je_seldom_used_max": "1"}


def main() -> int:
    from assurance_application.service import WorkbenchService
    from assurance_artifacts.vault import ArtifactVault
    from assurance_persistence.database import connect, migrate
    from assurance_persistence.legacy_import import ensure_tenant

    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        conn = connect(root / "control.db")
        migrate(conn)
        svc = WorkbenchService(conn, ArtifactVault(root / "vault"),
                               ensure_tenant(conn, "kv1"))
        eid = svc.create_engagement(P, "Kestrel Valley", "2026-06-30")["engagement_id"]
        svc.assign_team(P, eid, R, "preparer")
        svc.assign_team(P, eid, S, "reviewer")
        svc.update_workflow(P, eid, "cycles", {"cycles": ["journal_entries"]})
        svc.update_workflow(P, eid, "period", {"start": "2025-07-01"})
        print("== Loads ==")
        for name, role, recipe, mode in LOADS:
            print(f"\n  {name} -> {role}" + (f" [{recipe}]" if recipe else ""))
            try:
                art = svc.store_source(R, eid, content=(QBO / name).read_bytes(),
                                       media_type=XLSX, original_name=name)
                prop = svc.propose_source_mapping(
                    R, eid, role=role, artifact_id=art["artifact_id"],
                    extraction={"recipe": recipe} if recipe else None)
                print(f"    map {prop['column_map']}")
                if prop["refused_fields"]:
                    print(f"    refused {prop['refused_fields']}")
                report = (prop.get("extraction") or {}).get("recipe_report") or {}
                if report.get("missing_required"):
                    print(f"    recipe: missing {report['missing_required']}")
                svc.approve_source_mapping(S, eid, prop["spec_id"])
                rec = svc.normalize_source(R, eid, prop["spec_id"], mode=mode)
                r = rec["reconciliation"]
                print(f"    loaded {r['rows_loaded']} set aside {r['rows_rejected']} "
                      f"control {r['control_total']}")
            except Exception as exc:
                print(f"    ERROR {type(exc).__name__}: {exc}")
        for name, value in POLICIES.items():
            try:
                svc.update_workflow(P, eid, "policy", {"name": name, "value": value})
            except Exception as exc:
                print(f"  policy {name}: ERROR {exc}")
        cov = svc.coverage(eid)
        print("\n== Coverage ==")
        for row in cov["procedures"]:
            print(f"  {row['procedure_id']:<36} {row['status']}")
        print("\n== Runs ==")
        for row in cov["procedures"]:
            if row["status"] != "executable":
                continue
            run = svc.run_procedure(R, eid, procedure_id=row["procedure_id"])
            print(f"  {run['status']:<9} {row['procedure_id']:<36} findings "
                  f"{run['findings']:>4}  {run['error'] or ''}")
        by: dict[str, dict[str, int]] = {}
        for f in svc.findings(eid):
            v = f["verdict"]
            test = str(v["key"][-1])
            by.setdefault(f["procedure_id"], {})
            by[f["procedure_id"]][test] = by[f["procedure_id"]].get(test, 0) + 1
        print("\n== Findings by procedure and kind ==")
        for pid, kinds in sorted(by.items()):
            print(f"  {pid}: {dict(sorted(kinds.items()))}")
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
