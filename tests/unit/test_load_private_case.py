# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The private case in "load teaching case": offered only where its own loader
is installed, and loaded by that loader. Uses a stand-in loader, never the case."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "workbench-api"))

from workbench_api import demo  # noqa: E402

STAND_IN = (
    "CLIENT, PERIOD = 'Private Case Co', '2020-12-31'\n"
    "def load(svc, partner):\n"
    "    eid = svc.create_engagement(partner, CLIENT, PERIOD)['engagement_id']\n"
    "    return {'engagement_id': eid, 'seeded': True}\n")


@pytest.fixture
def svc(tmp_path):
    from assurance_application.service import WorkbenchService
    from assurance_artifacts.vault import ArtifactVault
    from assurance_persistence.database import connect, migrate
    from assurance_persistence.legacy_import import ensure_tenant
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "o"))
    conn.close()


def test_the_private_case_is_offered_only_when_its_loader_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(demo, "_oceanview_loader", lambda: tmp_path / "absent.py")
    assert "oceanview" not in [c["case"] for c in demo.available_cases()]
    with pytest.raises(KeyError):
        demo.load_case(None, "oceanview", "pa")


def test_the_private_case_loads_through_its_own_loader(svc, tmp_path, monkeypatch):
    stand_in = tmp_path / "load_workbench.py"
    stand_in.write_text(STAND_IN, encoding="utf-8")
    monkeypatch.setattr(demo, "_oceanview_loader", lambda: stand_in)
    assert "oceanview" in [c["case"] for c in demo.available_cases()]
    out = demo.load_case(svc, "oceanview", "pa")
    assert out["seeded"] is True
    assert [e["client_name"] for e in svc.list_engagements()] == ["Private Case Co"]
    # archived, it comes back instead of loading a second copy (the name and
    # year end are read from the private loader, never from this repository)
    svc.archive_engagement("pa", out["engagement_id"], reason="practice run, file it")
    again = demo.load_case(svc, "oceanview", "pa")
    assert again == {"engagement_id": out["engagement_id"], "seeded": False, "restored": True}
