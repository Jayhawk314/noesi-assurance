# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The working paper: rendered from the record as it stands, at any time,
unsigned, and said to be so. Viewing it is not an export, so it is not
journaled as one; downloading the record is."""

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant


@pytest.fixture()
def svc(tmp_path):
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "o"))
    conn.close()


def _exports(svc):
    return svc._conn.execute(
        "SELECT COUNT(*) FROM domain_event WHERE event_type = 'export.record'").fetchone()[0]


def test_the_working_paper_says_it_is_unsigned_and_is_not_an_export(svc):
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    html = svc.workpaper_html("rev", eid)
    assert "<title>Working paper — Acme" in html
    assert "unsigned" in html and "sign-off are outside it" in html
    assert "Lock signed by" not in html and "DRAFT" not in html
    assert _exports(svc) == 0


def test_downloading_the_record_is_journaled_each_time(svc):
    eid = svc.create_engagement("pa", "Zenith", "2025-06-30")["engagement_id"]
    first = svc.export_record("pa", eid)
    svc.update_workflow("pa", eid, "materiality", {"amount": 10000.0})
    second = svc.export_record("pa", eid)
    assert _exports(svc) == 2
    assert first["seal"]["packet_digest"] != second["seal"]["packet_digest"]


def test_mappings_read_as_confirmed_by_the_one_user_not_approved(svc):
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    art = svc.store_source("pa", eid, content=(
        b"payment_number,vendor_id,payment_date,amount\n"
        b"P1,V1,2025-03-01,100.00\nP2,V2,2025-04-01,250.00\n"),
        media_type="text/csv", original_name="p.csv")
    spec = svc.confirm_source_mapping("pa", eid, role="Payments", artifact_id=art["artifact_id"])
    svc.normalize_source("pa", eid, spec["spec_id"])
    html = svc.workpaper_html("pa", eid)
    assert "Confirmed mappings and datasets" in html
    assert "<td>confirmed</td><td>pa</td>" in html
    assert "Approved" not in html and "Proposed by" not in html
