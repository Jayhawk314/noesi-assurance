# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The working paper before the lock: a draft, marked as one, never signed or
journaled as an export. After the lock it is the signed one, as before."""

import pytest

from assurance_application.service import AuthorizationError, WorkbenchService
from assurance_artifacts.signing import LocalKeyStore
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant


@pytest.fixture()
def svc(tmp_path):
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "o"),
                           keystore=LocalKeyStore(tmp_path / "keys"))
    conn.close()


def _exports(svc):
    return svc._conn.execute(
        "SELECT COUNT(*) FROM domain_event WHERE event_type = 'export.packet'").fetchone()[0]


def test_an_open_engagement_gives_a_marked_draft_and_no_export(svc):
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    svc.assign_team("pa", eid, "rev", "reviewer")
    html = svc.workpaper_html("rev", eid)
    assert "DRAFT — not locked, not signed." in html
    assert "<title>DRAFT working paper" in html
    assert "Lock signed by" not in html and "signature" not in html.lower()
    assert _exports(svc) == 0
    packet = svc.draft_packet("rev", eid)
    assert packet["draft"] is True and packet["lock"] is None and "seal" not in packet
    with pytest.raises(AuthorizationError):
        svc.workpaper_html("stranger", eid)


def test_a_locked_engagement_still_gives_the_signed_working_paper(svc):
    eid = svc.create_engagement("pa", "Zenith", "2025-06-30")["engagement_id"]
    svc.update_workflow("pa", eid, "materiality", {"amount": 10000.0})
    svc.update_workflow("pa", eid, "no_data_assertion",
                        {"asserted": True, "reason": "unit fixture, no client data"})
    assert svc.lock("pa", eid, expected_version=1)["locked"] is True
    html = svc.workpaper_html("pa", eid)
    assert "Lock signed by" in html and "DRAFT" not in html
    assert _exports(svc) == 1
