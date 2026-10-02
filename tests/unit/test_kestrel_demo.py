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
def test_the_journal_recipe_keeps_same_day_unnumbered_deposits_separate():
    # Two 6/30 deposits with no Num and no name would share one name; the
    # Journal export's own transaction IDs keep them two entries.
    from assurance_artifacts import xlsx
    from procedures_ap import quickbooks as qb
    content = (CASE / "data" / "quickbooks" / "Journal.xlsx").read_bytes()
    extraction, headers, rows = xlsx.extract(content)
    _, rows, _, report = qb.apply("qbo.journal_created.journal_entries", headers, rows,
                                  extraction["header_row"] + 1)
    assert report["totals_disagreeing"] == []
    import json
    journal = json.loads((CASE / "instructor" / "answer_key_payables.json")
                         .read_text(encoding="utf-8"))["journal"]
    entry_ids = {row["Entry"] for row in rows}
    assert len(entry_ids) == journal["transactions"] and len(rows) == journal["lines"]
    assert sum(row["Line"] == "1" for row in rows) == journal["transactions"]
    deposits = sorted(e for e in entry_ids if e.startswith("2026-06-30 Deposit (no num) [txn"))
    assert len(deposits) == 2


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
