# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Run Noesi, unchanged, on Kestrel parts 2 and 3 and print what it finds,
for comparison with answer_key_part2.json and answer_key_part3.json.

Client and auditor CSVs load through ordinary mappings as delivered. The
trial balance is the hand-prepared one from run_noesi.py (pass B), because
the QuickBooks export does not load yet (K8); that is stated, not hidden.

    .venv\\Scripts\\python case-studies\\kestrel-valley-cycle\\instructor\\run_parts23.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_noesi  # noqa: E402  (the pass-B trial balance and aging preparation)

CASE = Path(__file__).resolve().parent.parent
DATA = CASE / "data"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
P, R, S = "kv-partner", "kv-preparer", "kv-reviewer"
K2 = json.loads((CASE / "instructor" / "answer_key_part2.json").read_text(encoding="utf-8"))
K3 = json.loads((CASE / "instructor" / "answer_key_part3.json").read_text(encoding="utf-8"))

LOADS = [  # name, role, source (path under data/, or a callable), media
    ("trial_balance_prepared.csv", "Trial_balance", run_noesi.prep_trial_balance, "csv"),
    ("ar_aging_prepared.csv", "AR_listing", run_noesi.prep_aging, "csv"),
    ("payroll_register_FY2026.csv", "Payroll_register", "client/payroll_register_FY2026.csv", "csv"),
    ("employee_master.csv", "Payroll_master", "client/employee_master.csv", "csv"),
    ("fixed_asset_register.csv", "Fixed_assets", "client/fixed_asset_register.csv", "csv"),
    ("additions_vouching.csv", "Additions_vouching", "auditor/additions_vouching.csv", "csv"),
    ("debt_schedule.csv", "Debt_schedule", "client/debt_schedule.csv", "csv"),
    ("covenants.csv", "Covenants", "auditor/covenants.csv", "csv"),
    ("equity_rollforward.csv", "Equity_rollforward", "client/equity_rollforward.csv", "csv"),
    ("accruals_prepaids_schedule.csv", "Accrual_schedule",
     "client/accruals_prepaids_schedule.csv", "csv"),
    ("prior_year_estimates.csv", "Estimates", "client/prior_year_estimates.csv", "csv"),
    ("related_parties.csv", "Related_parties", "client/related_parties.csv", "csv"),
    ("Journal_2026-07.xlsx", "Journal_entries", "quickbooks/Journal_2026-07.xlsx", "xlsx"),
    ("representation_letter.csv", "Representations", "auditor/representation_letter.csv", "csv"),
    ("uncorrected_misstatements_final.csv", "Misstatements",
     "auditor/uncorrected_misstatements_final.csv", "csv"),
]
CYCLES = ["payroll", "ppe", "debt_equity", "accruals", "estimates", "completion",
          "journal_entries"]


def main() -> int:
    from assurance_application.service import WorkbenchService
    from assurance_artifacts.vault import ArtifactVault
    from assurance_persistence.database import connect, migrate
    from assurance_persistence.legacy_import import ensure_tenant

    policies = {**K2["policies"], **K3["policies"]}
    with tempfile.TemporaryDirectory() as scratch:
        root = Path(scratch)
        conn = connect(root / "control.db")
        migrate(conn)
        svc = WorkbenchService(conn, ArtifactVault(root / "vault"),
                               ensure_tenant(conn, "kv23"))
        eid = svc.create_engagement(P, "Kestrel Valley", "2026-06-30")["engagement_id"]
        svc.assign_team(P, eid, R, "preparer")
        svc.assign_team(P, eid, S, "reviewer")
        svc.update_workflow(P, eid, "materiality", {"amount": 15000, "basis": "pretax",
                                                    "rationale": "~4.6% of pretax"})
        svc.update_workflow(P, eid, "cycles", {"cycles": CYCLES})
        svc.update_workflow(P, eid, "period", {"start": "2025-07-01"})
        print("== Loads ==")
        for name, role, source, kind in LOADS:
            content = source() if callable(source) else (DATA / source).read_bytes()
            try:
                art = svc.store_source(R, eid, content=content,
                                       media_type=XLSX if kind == "xlsx" else "text/csv",
                                       original_name=name)
                prop = svc.propose_source_mapping(R, eid, role=role,
                                                  artifact_id=art["artifact_id"])
                svc.approve_source_mapping(S, eid, prop["spec_id"])
                rec = svc.normalize_source(R, eid, prop["spec_id"])["reconciliation"]
                print(f"  {role:<20} loaded {rec['rows_loaded']:>4} set aside "
                      f"{rec['rows_rejected']:>4}  refused {prop['refused_fields']}")
            except Exception as exc:
                print(f"  {role:<20} ERROR {type(exc).__name__}: {exc}")
        for name, value in policies.items():
            try:
                svc.update_workflow(P, eid, "policy", {"name": name, "value": value})
            except Exception as exc:
                print(f"  policy {name}: ERROR {exc}")
        cov = svc.coverage(eid)
        print("\n== Runs ==")
        for row in cov["procedures"]:
            if row["procedure_id"].startswith(("ap.", "cash.", "gl.", "forensic.")) \
                    and row["procedure_id"] != "ap.duplicate_bills":
                continue
            if row["status"] != "executable":
                print(f"  {row['status']:<9} {row['procedure_id']:<38} "
                      f"{row.get('missing_fields') or row.get('missing_policies') or ''}")
                continue
            run = svc.run_procedure(R, eid, procedure_id=row["procedure_id"])
            print(f"  {run['status']:<9} {row['procedure_id']:<38} findings "
                  f"{run['findings']:>3}  {run['error'] or ''}")
        print("\n== Findings ==")
        for f in svc.findings(eid):
            v = f["verdict"]
            print(f"  {f['procedure_id']:<36} [{v['verdict']:<9}] "
                  f"{' · '.join(str(k) for k in v['key'][1:])[:60]}")
        print("\n== Draft opinion ==")
        op = svc.draft_opinion(eid)
        print(json.dumps({k: op[k] for k in ("status", "proposed_opinion", "basis",
                                             "decisions_required", "misstatements",
                                             "missing_representations")}, indent=1))
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
