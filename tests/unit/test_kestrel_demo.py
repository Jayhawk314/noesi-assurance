# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The Workbench demo is the Kestrel Valley case: loaded and run through the
real service path, idempotent, and landing on the key's draft opinion."""

from pathlib import Path

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant

CASE = Path(__file__).resolve().parents[2] / "case-studies" / "kestrel-valley-cycle"


@pytest.mark.skipif(not CASE.is_dir(), reason="case data not in tree")
def test_kestrel_demo_seeds_runs_and_is_idempotent(tmp_path):
    from workbench_api.demo import seed_kestrel
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    svc = WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "d"))
    first = seed_kestrel(svc, "partner-1")
    assert first["seeded"] and first["refused"] == []
    assert first["procedures_run"] >= 25
    again = seed_kestrel(svc, "partner-1")
    assert again == {"engagement_id": first["engagement_id"], "seeded": False}
    assert len(svc.list_engagements()) == 1
    opinion = svc.draft_opinion(first["engagement_id"])
    assert opinion["proposed_opinion"] == "disclaimer"
    assert opinion["missing_representations"] == ["related_parties"]
    conn.close()
