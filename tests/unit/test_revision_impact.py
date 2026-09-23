# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Revised evidence: a newer client file and everything it reaches."""

import json
from pathlib import Path

import pytest

from assurance_application.impact import (
    compare_findings, diff_records, sad_effect, significance, thresholds,
)
from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from procedures_ap.contracts import PROCEDURES
from workbench_api.demo import DEMO_PREPARER, DEMO_REVIEWER, seed_demo

CASE = Path(__file__).resolve().parents[2] / "case-studies" / "harborline-marine"
LIMITS = thresholds(420000)


def test_significance_places_changes_against_derived_thresholds():
    assert significance(0, LIMITS) == "none"
    assert significance(-1081.33, LIMITS) == "below_trivial"
    assert significance(21619.99, LIMITS) == "above_trivial"
    assert significance(400000, LIMITS) == "above_performance"
    # No materiality set: never silently call a change immaterial.
    assert significance(5, thresholds(0)) == "above_trivial"


def test_diff_records_matches_on_key_and_reports_duplicates():
    old = [{"voucher_number": "A", "voucher_amount": 100.0},
           {"voucher_number": "B", "voucher_amount": 50.0}]
    new = [{"voucher_number": "A", "voucher_amount": 90.0},
           {"voucher_number": "C", "voucher_amount": 30.0},
           {"voucher_number": "C", "voucher_amount": 30.0}]
    diff = diff_records(old, new, ("voucher_number",), LIMITS)
    assert [row["key"] for row in diff["added"]] == ["C"]
    assert [row["key"] for row in diff["removed"]] == ["B"]
    assert diff["changed"][0]["amount_change"] == -10.0
    assert diff["duplicate_keys"] == ["C"]
    assert diff["net_amount_change"] == -30.0


def test_compare_findings_names_the_action_not_a_conclusion():
    old = {"gone": {"domain": "d", "key": ["gone"], "score": 500.0},
           "moved": {"domain": "d", "key": ["moved"], "score": 100.0},
           "same": {"domain": "d", "key": ["same"], "score": 7.0}}
    new = {"moved": {"domain": "d", "key": ["moved"], "score": 150.0},
           "same": {"domain": "d", "key": ["same"], "score": 7.0},
           "fresh": {"domain": "d", "key": ["fresh"], "score": 20.0}}
    dispositions = {"gone": {"status": "unadjusted", "concurred_by": "rev"},
                    "moved": {"status": "cleared", "concurred_by": ""}}
    cards = {c["finding_uid"]: c
             for c in compare_findings(old, new, dispositions, LIMITS)}
    assert set(cards) == {"gone", "moved", "fresh"}  # "same" is untouched
    assert cards["gone"]["action"] == "revisit_disposition"
    assert "voids the reviewer's concurrence" in cards["gone"]["what_it_means"]
    assert cards["moved"]["action"] == "reassess_disposition"
    assert cards["fresh"]["action"] == "dispose"
    assert sad_effect(list(cards.values())) == {"unadjusted": -500.0,
                                               "adjusted": 0.0}


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    tenant = ensure_tenant(conn, "impact")
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), tenant)
    conn.close()


def _load_revision(service, eid):
    content = (CASE / "revision" / "vouchers_revised.csv").read_bytes()
    artifact = service.store_source(
        DEMO_PREPARER, eid, content=content, media_type="text/csv",
        original_name="vouchers_revised.csv")
    spec_id = service.propose_source_mappings(
        DEMO_PREPARER, eid,
        [{"artifact_id": artifact["artifact_id"]}])["results"][0]["spec_id"]
    service.approve_source_mappings(DEMO_REVIEWER, eid, [spec_id])
    service.normalize_sources(DEMO_PREPARER, eid, [spec_id])


@pytest.mark.skipif(not (CASE / "revision" / "vouchers_revised.csv").is_file(),
                    reason="case data not in tree")
def test_harborline_revised_vouchers_reach_runs_findings_and_judgments(service):
    eid = seed_demo(service, "local:partner")["engagement_id"]
    service.update_workflow("local:partner", eid, "materiality",
                            {"amount": "420000"})
    for contract in PROCEDURES:
        service.run_procedure(DEMO_PREPARER, eid,
                              procedure_id=contract.procedure_id)
    assert service.revision_impact(eid)["summary"]["stale_runs"] == 0

    findings = service.findings(eid)

    def uid(procedure, key):
        return next(f["finding_uid"] for f in findings
                    if f["procedure_id"] == procedure
                    and key in json.dumps(f["verdict"]["key"]))
    receipt_gap = uid("ap.three_way_receipt_match", "VCH-2026-0009")
    orphan_payment = uid("ap.payment_voucher_reference", "PAY-2026-0013")
    service.set_disposition(DEMO_PREPARER, eid, finding_uid=receipt_gap,
                            status="unadjusted", note="exceeds receipts")
    service.set_disposition(DEMO_PREPARER, eid, finding_uid=orphan_payment,
                            status="follow_up", note="voucher requested")
    runs_before = len(service.runs(eid))

    _load_revision(service, eid)
    report = service.revision_impact(eid)

    # Read-only: the report never records a run.
    assert len(service.runs(eid)) == runs_before
    (revision,) = report["revisions"]
    assert revision["role"] == "Vouchers"
    assert [row["key"] for row in revision["diff"]["added"]] == ["VCH-2026-9338"]
    assert {row["key"] for row in revision["diff"]["changed"]} == {
        "VCH-2026-0009", "VCH-2026-0030"}
    # Only procedures that read Vouchers go stale.
    assert {run["procedure_id"] for run in report["stale_runs"]} == {
        "ap.document_chain", "ap.payment_voucher_reference",
        "ap.three_way_receipt_match", "ap.voucher_po_reference"}
    cards = {card["finding_uid"]: card for card in report["cards"]}
    assert cards[receipt_gap]["action"] == "revisit_disposition"
    assert cards[orphan_payment]["action"] == "revisit_disposition"
    new = [c for c in cards.values() if c["change"] == "new_after_revision"]
    assert [c["key"] for c in new] == [["document_chain", "PAY-2026-0009"]]
    assert report["summary"]["sad_effect"]["unadjusted"] == -1081.33
