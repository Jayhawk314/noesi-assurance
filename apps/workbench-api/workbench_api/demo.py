"""Seed a ready-to-explore demo engagement from the Harborline teaching case.

The seed goes through the real service path — three chairs, mapping review,
digest-verified normalization, approved policies — so the demo engagement is
indistinguishable from hand-loaded work. Procedures are deliberately *not*
run: pressing "run" and reading what the engine found (and refused) is the
part worth experiencing first-hand.
"""

from __future__ import annotations

from pathlib import Path

DEMO_CLIENT = "Harborline Marine Group (demo)"
DEMO_PERIOD = "2026-12-31"
DEMO_PREPARER = "demo-preparer"
DEMO_REVIEWER = "demo-reviewer"

ROLE_FILES = {
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

# Approved engagement policies: the client's $10,000 approval limit, and a
# nine-day split window (the engine's default of 0 tests same-day splits only).
DEMO_POLICIES = (("split_threshold", "10000"), ("split_window_days", "9"))


def default_case_dir() -> Path:
    """The in-repo Harborline data; absent in installed-package deployments."""
    return (Path(__file__).resolve().parents[3]
            / "case-studies" / "harborline-marine" / "data")


def seed_demo(service, partner: str,
              case_dir: Path | None = None) -> dict:
    """Idempotently create and load the demo engagement; return a summary."""
    case_dir = Path(case_dir) if case_dir else default_case_dir()
    missing = [name for name in ROLE_FILES if not (case_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"demo case data not found under {case_dir} "
            f"(missing {', '.join(sorted(missing))}); pass the "
            "case-studies/harborline-marine/data directory explicitly")

    existing = next(
        (e for e in service.list_engagements()
         if e["client_name"] == DEMO_CLIENT
         and e["period_end"] == DEMO_PERIOD), None)
    if existing:
        return {"engagement_id": existing["engagement_id"], "seeded": False}

    eid = service.create_engagement(
        partner, DEMO_CLIENT, DEMO_PERIOD)["engagement_id"]
    service.assign_team(partner, eid, DEMO_PREPARER, "preparer")
    service.assign_team(partner, eid, DEMO_REVIEWER, "reviewer")

    # Bulk path, one pass per chair: the preparer uploads everything and
    # batch-proposes with roles inferred from the filenames, the reviewer
    # batch-approves, the preparer batch-normalizes. The seed asserts every
    # inference landed on the answer key's role, so the demo doubles as an
    # end-to-end check of bulk loading against real case files.
    expected_role = {}
    for filename in ROLE_FILES:
        artifact = service.store_source(
            DEMO_PREPARER, eid, content=(case_dir / filename).read_bytes(),
            media_type="text/csv", original_name=filename,
            provenance=f"harborline-marine teaching case: {filename}")
        expected_role[artifact["artifact_id"]] = ROLE_FILES[filename]

    proposals = service.propose_source_mappings(
        DEMO_PREPARER, eid,
        [{"artifact_id": aid} for aid in expected_role])
    wrong = [r for r in proposals["results"]
             if r["status"] != "proposed"
             or r["role"] != expected_role[r["artifact_id"]]]
    if wrong:
        raise RuntimeError(f"demo seed: role inference went wrong: {wrong}")
    spec_ids = [r["spec_id"] for r in proposals["results"]]

    approvals = service.approve_source_mappings(DEMO_REVIEWER, eid, spec_ids)
    if approvals["approved"] != len(spec_ids):
        raise RuntimeError(f"demo seed: approval failed: {approvals}")

    normalized = service.normalize_sources(DEMO_PREPARER, eid, spec_ids)
    if normalized["normalized"] != len(spec_ids):
        raise RuntimeError(f"demo seed: normalization failed: {normalized}")
    loaded = {r["reconciliation"]["role"]: r["reconciliation"]["rows_loaded"]
              for r in normalized["results"]}

    for name, value in DEMO_POLICIES:
        service.update_workflow(partner, eid, "policy",
                                {"name": name, "value": value})

    return {"engagement_id": eid, "seeded": True, "rows_loaded": loaded,
            "team": {"partner": partner, "preparer": DEMO_PREPARER,
                     "reviewer": DEMO_REVIEWER}}
