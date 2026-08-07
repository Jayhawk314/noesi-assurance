"""The --demo seed: real Harborline data through the real three-chair path."""

from pathlib import Path

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from workbench_api.demo import DEMO_CLIENT, default_case_dir, seed_demo

CASE_DATA = (Path(__file__).resolve().parent.parent.parent
             / "case-studies" / "harborline-marine" / "data")


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    tenant = ensure_tenant(conn, "demo")
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), tenant)
    conn.close()


@pytest.mark.skipif(not CASE_DATA.is_dir(), reason="case data not in tree")
def test_demo_seed_loads_everything_and_is_idempotent(service):
    outcome = seed_demo(service, "local:someone", case_dir=CASE_DATA)
    assert outcome["seeded"] is True
    assert outcome["rows_loaded"]["Payments"] == 123

    coverage = service.coverage(outcome["engagement_id"])
    assert coverage["summary"]["executable"] == 11

    engagements = service.list_engagements()
    assert [e["client_name"] for e in engagements] == [DEMO_CLIENT]

    again = seed_demo(service, "local:someone", case_dir=CASE_DATA)
    assert again["seeded"] is False
    assert again["engagement_id"] == outcome["engagement_id"]
    assert len(service.list_engagements()) == 1


def test_demo_seed_fails_closed_without_case_data(service, tmp_path):
    with pytest.raises(FileNotFoundError, match="demo case data"):
        seed_demo(service, "local:someone", case_dir=tmp_path / "nowhere")


def test_default_case_dir_points_into_the_repo_layout():
    assert default_case_dir().parts[-3:] == (
        "case-studies", "harborline-marine", "data")
