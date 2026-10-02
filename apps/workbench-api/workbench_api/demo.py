# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Seed a ready-to-explore demo engagement from the Harborline teaching case.

The seed goes through the real service path — one user, confirmed mappings,
digest-verified normalization, approved policies — so the demo engagement is
indistinguishable from hand-loaded work. Procedures are deliberately *not*
run: pressing "run" and reading what the engine found (and refused) is the
part worth experiencing first-hand.
"""

from __future__ import annotations

import sys
from pathlib import Path

DEMO_CLIENT = "Harborline Marine Group (demo)"
DEMO_PERIOD = "2026-12-31"

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


def kestrel_case_dir() -> Path:
    """The in-repo Kestrel Valley case; absent in installed-package deployments."""
    return (Path(__file__).resolve().parents[3]
            / "case-studies" / "kestrel-valley-cycle")


def seed_kestrel(service, partner: str) -> dict:
    """The Workbench demo: the full Kestrel Valley audit, loaded and run
    through the real service path (idempotent)."""
    seeder = kestrel_case_dir() / "instructor" / "workbench_seed.py"
    if not seeder.is_file():
        raise FileNotFoundError(
            f"the Kestrel Valley case is not present at {kestrel_case_dir()}; "
            "the demo needs the repository's case-studies folder")
    import importlib.util
    spec = importlib.util.spec_from_file_location("kestrel_workbench_seed", seeder)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.seed(service, partner)


def default_case_dir() -> Path:
    """The in-repo Harborline data; absent in installed-package deployments."""
    return (Path(__file__).resolve().parents[3]
            / "case-studies" / "harborline-marine" / "data")


def seed_demo(service, user: str,
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
        user, DEMO_CLIENT, DEMO_PERIOD)["engagement_id"]

    # Bulk path: upload everything, map and confirm with roles inferred from
    # the filenames, then load. The seed asserts every inference landed on
    # the answer key's role, so the demo doubles as an end-to-end check of
    # bulk loading against real case files.
    expected_role = {}
    for filename in ROLE_FILES:
        artifact = service.store_source(
            user, eid, content=(case_dir / filename).read_bytes(),
            media_type="text/csv", original_name=filename,
            provenance=f"harborline-marine teaching case: {filename}")
        expected_role[artifact["artifact_id"]] = ROLE_FILES[filename]

    mapped = service.confirm_source_mappings(
        user, eid, [{"artifact_id": aid} for aid in expected_role])
    wrong = [r for r in mapped["results"]
             if r["status"] != "confirmed"
             or r["role"] != expected_role[r["artifact_id"]]]
    if wrong:
        raise RuntimeError(f"demo seed: role inference went wrong: {wrong}")
    spec_ids = [r["spec_id"] for r in mapped["results"]]

    normalized = service.normalize_sources(user, eid, spec_ids)
    if normalized["normalized"] != len(spec_ids):
        raise RuntimeError(f"demo seed: normalization failed: {normalized}")
    loaded = {r["reconciliation"]["role"]: r["reconciliation"]["rows_loaded"]
              for r in normalized["results"]}

    for name, value in DEMO_POLICIES:
        service.update_workflow(user, eid, "policy",
                                {"name": name, "value": value})

    return {"engagement_id": eid, "seeded": True, "rows_loaded": loaded,
            "user": user}


# ------------------------------------------------------------------ load a case from the Workbench

CASES = {
    "kestrel": {"title": "Kestrel Valley Cycle Supply (FYE 2026-06-30)",
                "client": "Kestrel Valley Cycle Supply (demo)", "period_end": "2026-06-30",
                "present": lambda: (kestrel_case_dir() / "instructor" / "workbench_seed.py").is_file(),
                "load": seed_kestrel},
    "harborline": {"title": "Harborline Marine Group (FYE 2026-12-31)",
                   "client": DEMO_CLIENT, "period_end": DEMO_PERIOD,
                   "present": lambda: (default_case_dir() / "vendors.csv").is_file(),
                   "load": seed_demo},
    # Oceanview is a purchased case: its files and loader live only in the
    # git-ignored oceanview/ folder, so this entry appears only where the
    # case has been installed. Nothing of the case is in this repository.
    # Its client name and year end come from the private loader when used.
    "oceanview": {"title": "Oceanview Marine (private case)",
                  "client": None, "period_end": None,
                  "present": lambda: _oceanview_loader().is_file(),
                  "load": lambda service, partner: _load_oceanview(service, partner)},
}


def _oceanview_loader() -> Path:
    return Path(__file__).resolve().parents[3] / "oceanview" / "adapter" / "load_workbench.py"


def _oceanview_module():
    """The private case's own loader, imported from the git-ignored folder."""
    import importlib.util
    path = _oceanview_loader()
    adapter = str(path.parent)
    if adapter not in sys.path:
        sys.path.insert(0, adapter)          # its loader imports its siblings
    spec = importlib.util.spec_from_file_location("oceanview_load_workbench", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_oceanview(service, partner: str) -> dict:
    """Run the private case's own loader in this server's store."""
    return _oceanview_module().load(service, partner)


def available_cases() -> list[dict]:
    """The teaching cases this installation can load (their files are present)."""
    return [{"case": name, "title": c["title"]} for name, c in CASES.items() if c["present"]()]


def load_case(service, name: str, partner: str) -> dict:
    """Load a teaching case as a new engagement (or return the one already open)."""
    case = CASES.get(name)
    if case is None or not case["present"]():
        raise KeyError(f"case {name!r} is not available here")
    client, period_end = case["client"], case["period_end"]
    if name == "oceanview":                  # private: known only to its loader
        module = _oceanview_module()
        client, period_end = module.CLIENT, module.PERIOD
    # an archived copy comes back rather than blocking a new one
    archived = next((e for e in service.list_engagements(archived=True)
                     if e["client_name"] == client and e["period_end"] == period_end), None)
    if archived:
        service.restore_engagement(partner, archived["engagement_id"])
        return {"engagement_id": archived["engagement_id"], "seeded": False, "restored": True}
    return case["load"](service, partner)
