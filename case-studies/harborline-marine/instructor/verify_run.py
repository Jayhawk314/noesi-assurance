# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Re-run the Harborline case end to end and print what the engine finds.

Loads ``data/`` through WorkbenchService with three principals (partner,
preparer, reviewer — separation of duties makes a single-principal run
impossible), sets the split-payment threshold as an approved engagement
policy, runs every procedure coverage reports executable, and prints the
findings grouped by procedure so they can be reconciled line by line against
``ANSWER-KEY.md``.

Run with the project venv:

    .venv\\Scripts\\python case-studies\\harborline-marine\\instructor\\verify_run.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

CASE = Path(__file__).resolve().parent.parent
DATA = CASE / "data"

ROLES = {
    "vendors.csv": "Vendors",
    "employees.csv": "Employees",
    "purchase_orders.csv": "Purchase_orders",
    "goods_receipts.csv": "Goods_receipts",
    "vouchers.csv": "Vouchers",
    "payments.csv": "Payments",
    "bank.csv": "Bank",
    "gl.csv": "GL",
    "ap_control_balance.csv": "AP_control_balance",
    "value_flows.csv": "Value_flows",
}

PARTNER, PREPARER, REVIEWER = (
    "instructor-partner", "instructor-preparer", "instructor-reviewer")


def main() -> int:
    from assurance_application.service import WorkbenchService
    from assurance_artifacts.signing import LocalKeyStore
    from assurance_artifacts.vault import ArtifactVault
    from assurance_persistence.database import connect, migrate
    from assurance_persistence.legacy_import import ensure_tenant

    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        conn = connect(root / "control.db")
        migrate(conn)
        tenant = ensure_tenant(conn, "harborline-verify")
        service = WorkbenchService(
            conn, ArtifactVault(root / "vault"), tenant,
            keystore=LocalKeyStore(root / "keys"))

        eid = service.create_engagement(
            PARTNER, "Harborline Marine Group", "2026-12-31")["engagement_id"]
        service.assign_team(PARTNER, eid, PREPARER, "preparer")
        service.assign_team(PARTNER, eid, REVIEWER, "reviewer")

        print("== Ingestion ==")
        for filename, role in ROLES.items():
            artifact = service.store_source(
                PREPARER, eid, content=(DATA / filename).read_bytes(),
                media_type="text/csv", original_name=filename)
            proposal = service.propose_source_mapping(
                PREPARER, eid, role=role,
                artifact_id=artifact["artifact_id"])
            service.approve_source_mapping(REVIEWER, eid, proposal["spec_id"])
            recon = service.normalize_source(
                PREPARER, eid, proposal["spec_id"])["reconciliation"]
            print(f"  {role:<20} loaded {recon['rows_loaded']:>4}  "
                  f"rejected {recon['rows_rejected']:>2}  "
                  f"refused {proposal['refused_fields'] or '—'}")

        print("\n== Coverage before the split threshold is approved ==")
        before = service.coverage(eid)
        print("  " + ", ".join(f"{k}={v}" for k, v in
                               sorted(before["summary"].items())))

        service.update_workflow(
            PARTNER, eid, "policy",
            {"name": "split_threshold", "value": "10000"})
        # The planted cluster spans nine days; same-day-only review (the
        # window's default) is deliberately silent about it.
        service.update_workflow(
            PARTNER, eid, "policy",
            {"name": "split_window_days", "value": "9"})

        coverage = service.coverage(eid)
        print("\n== Coverage with the approved policy ==")
        print("  " + ", ".join(f"{k}={v}" for k, v in
                               sorted(coverage["summary"].items())))
        for row in coverage["procedures"]:
            print(f"  {row['procedure_id']:<30} {row['status']}")

        print("\n== Runs ==")
        runnable = sorted(row["procedure_id"]
                          for row in coverage["procedures"]
                          if row["status"] == "executable")
        for procedure_id in runnable:
            run = service.run_procedure(
                PREPARER, eid, procedure_id=procedure_id)
            marker = "OK " if run["status"] == "completed" else "ERR"
            print(f"  {marker} {procedure_id:<30} findings "
                  f"{run['findings']:>3}  {run['error'] or ''}")

        print("\n== Findings by procedure ==")
        by_procedure: dict[str, list[dict]] = {}
        for item in service.findings(eid):
            by_procedure.setdefault(item["procedure_id"], []).append(item)
        for procedure_id in sorted(by_procedure):
            items = by_procedure[procedure_id]
            print(f"\n  {procedure_id} — {len(items)}")
            for item in items:
                verdict = item["verdict"]
                print(f"    [{verdict['verdict']:<7}] {verdict['reason']}")
        total = sum(len(v) for v in by_procedure.values())
        print(f"\n== Total findings: {total} ==")
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
