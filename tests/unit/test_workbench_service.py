# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The six screens as one journey: engagement -> sources -> coverage ->
runs -> SAD/readiness -> export, with one user throughout."""

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant

PAYMENTS_CSV = (
    "Payment No,Invoice No,Vendor No,Amount,Payment Date\n"
    "P1,I1,V1,6000.00,2025-03-01\n"
    "P2,I2,V1,5000.00,2025-03-01\n"
    "P3,I3,V2,2000.00,2025-03-01\n"
).encode("utf-8")

BALANCES_CSV = (
    "Period End,Subledger Balance,GL Balance\n"
    "2025-12-31,125000.00,120000.00\n"
).encode("utf-8")

ALICE, BOB, CAROL = "principal-alice", "principal-bob", "principal-carol"


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    tenant = ensure_tenant(conn, "firm")
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), tenant)
    conn.close()


@pytest.fixture()
def engagement(service):
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    return eid


def _ingest(service, eid, content, name, role):
    artifact = service.store_source(
        BOB, eid, content=content, media_type="text/csv", original_name=name)
    proposal = service.confirm_source_mapping(
        BOB, eid, role=role, artifact_id=artifact["artifact_id"])
    return service.normalize_source(BOB, eid, proposal["spec_id"])


def test_the_engagement_creator_is_its_one_user_on_record(service):
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    assert [(m["principal_id"], m["role"]) for m in service.team(eid)] == [
        (ALICE, "partner")]
    assert not hasattr(service, "assign_team")


def test_one_user_maps_confirms_and_loads_a_file(service):
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    artifact = service.store_source(ALICE, eid, content=PAYMENTS_CSV,
                                    media_type="text/csv", original_name="p.csv")
    spec = service.confirm_source_mapping(ALICE, eid, role="Payments",
                                          artifact_id=artifact["artifact_id"])
    assert spec["status"] == "approved"
    row = service._conn.execute(
        "SELECT status, proposed_by, approved_by FROM mapping_spec").fetchone()
    assert tuple(row) == ("approved", ALICE, ALICE)
    loaded = service.normalize_source(ALICE, eid, spec["spec_id"])
    assert loaded["reconciliation"]["rows_loaded"] == 3


def test_source_to_normalized_dataset(service, engagement):
    result = _ingest(service, engagement, PAYMENTS_CSV, "payments.csv",
                     "Payments")
    recon = result["reconciliation"]
    assert recon["rows_loaded"] == 3
    assert recon["control_total"] == "13000.00"
    # No creator/approver/check columns in this export — refused, not guessed.
    assert recon["refused_fields"] == ["created_by", "approved_by",
                                       "check_number"]


def test_unreadable_workbooks_are_refused_at_mapping_with_instructions(
        service, engagement):
    # .xlsx is read (tests/unit/test_xlsx_ingest.py); a damaged workbook and
    # a legacy binary .xls are refused with what to do instead.
    damaged = service.store_source(
        BOB, engagement, content=b"PK\x03\x04" + b"\x00" * 64,
        media_type="application/vnd.openxmlformats-officedocument"
                   ".spreadsheetml.sheet",
        original_name="payments.xlsx")
    with pytest.raises(ValueError, match="damaged"):
        service.confirm_source_mapping(
            BOB, engagement, role="Payments",
            artifact_id=damaged["artifact_id"])
    legacy = service.store_source(
        BOB, engagement, content=b"\xd0\xcf\x11\xe0" + b"\x00" * 64,
        media_type="application/vnd.ms-excel", original_name="payments.xls")
    with pytest.raises(ValueError, match=r"save it as \.xlsx"):
        service.confirm_source_mapping(
            BOB, engagement, role="Payments",
            artifact_id=legacy["artifact_id"])


def test_coverage_reflects_normalized_datasets(service, engagement):
    _ingest(service, engagement, PAYMENTS_CSV, "payments.csv", "Payments")
    coverage = service.coverage(engagement)
    by_id = {row["procedure_id"]: row for row in coverage["procedures"]}
    split = by_id["ap.split_payment_review"]
    assert split["status"] == "partial"          # threshold policy missing
    assert split["missing_policies"] == ["split_threshold"]
    assert by_id["ap.subledger_gl_balance_tie"]["status"] == "blocked"
    assert coverage["summary"]["total"] == 11


def test_a_completed_run_needs_no_sign_off(service, engagement):
    # Supplement, not audit software (1 Oct 2026): a run is completed or an
    # error; no review or approval follows, and none is recorded.
    _ingest(service, engagement, PAYMENTS_CSV, "payments.csv", "Payments")
    run = service.run_procedure(
        BOB, engagement, procedure_id="ap.split_payment_review",
        policies={"split_threshold": "10000"})
    assert run["status"] == "completed"
    assert run["findings"] == 1
    assert not hasattr(service, "review_run")
    [listed] = service.runs(engagement)
    assert listed["status"] == "completed" and listed["executed_by"] == BOB
    assert "reviewed_by" not in listed and "approved_by" not in listed


def test_workflow_policy_reaches_runs_without_per_run_override(service,
                                                               engagement):
    _ingest(service, engagement, PAYMENTS_CSV, "payments.csv", "Payments")
    service.update_workflow(ALICE, engagement, "policy",
                            {"name": "split_threshold", "value": "10000"})
    coverage = service.coverage(engagement)
    split = next(row for row in coverage["procedures"]
                 if row["procedure_id"] == "ap.split_payment_review")
    assert split["status"] == "executable"
    # The run inherits the approved engagement policy; no request-body value.
    run = service.run_procedure(
        BOB, engagement, procedure_id="ap.split_payment_review")
    assert run["status"] == "completed"
    assert run["findings"] == 1
    # A per-run value still overrides the document.
    run = service.run_procedure(
        BOB, engagement, procedure_id="ap.split_payment_review",
        policies={"split_threshold": "100000"})
    assert run["status"] == "completed"


def test_error_runs_are_recorded_not_hidden(service, engagement):
    _ingest(service, engagement, PAYMENTS_CSV, "payments.csv", "Payments")
    run = service.run_procedure(
        BOB, engagement, procedure_id="ap.split_payment_review", policies={})
    assert run["status"] == "error"
    assert "split_threshold" in run["error"]
    assert service.runs(engagement)[0]["status"] == "error"


def test_findings_dispositions_and_sad(service, engagement):
    _ingest(service, engagement, PAYMENTS_CSV, "payments.csv", "Payments")
    _ingest(service, engagement, BALANCES_CSV, "recon.csv",
            "AP_control_balance")
    service.run_procedure(BOB, engagement,
                          procedure_id="ap.split_payment_review",
                          policies={"split_threshold": "10000"})
    service.run_procedure(BOB, engagement,
                          procedure_id="ap.subledger_gl_balance_tie")
    findings = service.findings(engagement)
    assert len(findings) == 2
    tie = next(f for f in findings
               if f["procedure_id"] == "ap.subledger_gl_balance_tie")
    assert tie["verdict"]["verdict"] == "CLASH"
    assert tie["disposition"]["status"] == "undisposed"

    service.set_disposition(BOB, engagement,
                            finding_uid=tie["finding_uid"],
                            status="unadjusted", note="client declines")
    # $5,000 is above clearly-trivial ($500 at this materiality); the
    # auditor's disposition stands as recorded, with no concurrence step.
    sad = service.sad(engagement, materiality=10000.0)
    assert sad["total_unadjusted"] == 5000.0
    assert sad["candidates"] == 1  # the split cluster is a lead, not a SAD item
    assert sad["conclusion"] == "immaterial"
    assert "concurrence_pending" not in sad


# ------------------------------------------------- dispositions stand alone

# ------------------------------------------------- disposition concurrence

def _tie_finding(service, engagement):
    _ingest(service, engagement, PAYMENTS_CSV, "payments.csv", "Payments")
    _ingest(service, engagement, BALANCES_CSV, "recon.csv",
            "AP_control_balance")
    service.run_procedure(BOB, engagement,
                          procedure_id="ap.subledger_gl_balance_tie")
    return next(f for f in service.findings(engagement)
                if f["procedure_id"] == "ap.subledger_gl_balance_tie")


def test_a_disposition_above_clearly_trivial_stands_without_concurrence(
        service, engagement):
    service.update_workflow(ALICE, engagement, "materiality",
                            {"amount": 10000.0, "basis": "revenue"})
    tie = _tie_finding(service, engagement)
    assert "requires_concurrence" not in tie
    service.set_disposition(BOB, engagement, finding_uid=tie["finding_uid"],
                            status="unadjusted", note="client declines")
    codes = {b["code"] for b in service.readiness(engagement)["blockers"]}
    assert "DISPOSITIONS_AWAITING_CONCURRENCE" not in codes
    assert not hasattr(service, "concur_disposition")
    refreshed = next(f for f in service.findings(engagement)
                     if f["finding_uid"] == tie["finding_uid"])
    assert refreshed["disposition"]["status"] == "unadjusted"
    assert refreshed["disposition"]["proposed_by"] == BOB


SCHEDULE_CSV = (
    b"Description,Identified,Likely,Current Assets,Noncurrent Assets,"
    b"Current Liabilities,Noncurrent Liabilities,Income Before Taxes\n"
    b"Invoice priced above contract,6000.00,0.00,-6000.00,0,0,0,-6000.00\n"
    b"Pricing sample projected,1000.00,5000.00,-5000.00,0,0,0,-5000.00\n")


def test_the_sad_carries_the_misstatement_schedule(service, engagement):
    # B2: one summary. Nothing is disposed, so the SAD alone would say
    # "immaterial"; the schedule's current assets and income (-11,000 each)
    # reach materiality (10,000), so the summary cannot.
    from decimal import Decimal
    service.update_workflow(ALICE, engagement, "materiality",
                            {"amount": 10000.0, "basis": "revenue"})
    service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["completion"]})
    assert service.sad(engagement)["schedule"] is None
    _ingest(service, engagement, SCHEDULE_CSV, "schedule.csv", "Misstatements")
    service.run_procedure(BOB, engagement,
                          procedure_id="completion.uncorrected_misstatements")
    sad = service.sad(engagement)
    assert sad["schedule"]["material_lines"] == ["current_assets", "income_before_taxes"]
    assert Decimal(sad["schedule"]["lines"]["current_assets"]) == Decimal("-11000")
    assert sad["conclusion"] == "material"
    # The schedule's "reaches materiality" is an evaluation, not one more
    # misstatement: disposed as unadjusted, it adds nothing to the SAD total.
    material = next(f for f in service.findings(engagement)
                    if f["verdict"]["key"][1] == "material")
    service.set_disposition(BOB, engagement, finding_uid=material["finding_uid"],
                            status="unadjusted", note="on the schedule")
    sad = service.sad(engagement)
    assert sad["total_unadjusted"] == 0.0 and sad["candidates"] == 0


def test_failed_latest_completion_rerun_marks_old_sad_schedule_historical(
        service, engagement, monkeypatch):
    import assurance_application.service as service_module

    service.update_workflow(ALICE, engagement, "materiality",
                            {"amount": 10000.0, "basis": "revenue"})
    service.update_workflow(ALICE, engagement, "cycles", {"cycles": ["completion"]})
    _ingest(service, engagement, SCHEDULE_CSV, "schedule.csv", "Misstatements")
    first = service.run_procedure(
        BOB, engagement, procedure_id="completion.uncorrected_misstatements")
    assert first["status"] == "completed"
    assert service.sad(engagement)["conclusion"] == "material"

    def fail(*_args):
        raise ValueError("invented runner failure")

    with monkeypatch.context() as patch:
        patch.setattr(service_module, "execute_procedure", fail)
        failed = service.run_procedure(
            BOB, engagement, procedure_id="completion.uncorrected_misstatements")
    assert failed["status"] == "error"
    assert service.sad(engagement)["schedule"] is not None  # old schedule retained
    assert service.runs(engagement)[0]["stale_reasons"] == ["latest rerun failed"]
    blockers = {b["code"]: b for b in service.readiness(engagement)["blockers"]}
    assert blockers["PROCEDURE_RESULTS_STALE"]["items"] == [
        "completion.uncorrected_misstatements"]


def test_clearly_trivial_is_the_firms_policy(service, engagement):
    # B1: the firm sets clearly trivial; 2% of $200,000 materiality is $4,000.
    service.update_workflow(ALICE, engagement, "materiality",
                            {"amount": 200000.0, "basis": "assets"})
    for bad in ("0", "100", "x", "-3"):
        with pytest.raises(ValueError, match="clearly_trivial_pct"):
            service.update_workflow(ALICE, engagement, "policy",
                                    {"name": "clearly_trivial_pct", "value": bad})
    service.update_workflow(ALICE, engagement, "policy",
                            {"name": "clearly_trivial_pct", "value": "2"})
    assert service.sad(engagement)["clearly_trivial"] == 4000.0
    assert "clearly_trivial_pct" in service.cycle_catalog()["general_policies"]


# ------------------------------------------- independent review follow-ups

def test_invalid_disposition_status_is_a_validation_error(service, engagement):
    """Review F1: a bad status value must not masquerade as a version
    conflict."""
    with pytest.raises(ValueError, match="disposition status"):
        service.set_disposition(BOB, engagement, finding_uid="x|1",
                                status="accepted_as_is")


def test_tampered_digest_raises_a_named_integrity_error(service, engagement):
    """Review F3: the refusal names the evidence chain, not a generic crash."""
    from assurance_application.service import EvidenceIntegrityError
    _ingest(service, engagement, PAYMENTS_CSV, "payments.csv", "Payments")
    service._conn.execute(
        "UPDATE normalized_dataset SET output_digest = 'tampered'")
    with pytest.raises(EvidenceIntegrityError, match="recorded digest"):
        service.coverage(engagement)


def test_one_engagement_cannot_confirm_or_load_anothers_file_or_mapping(service):
    # Review 2026-10-02 batch, M1: IDs from another engagement are refused as
    # not found, even when that engagement is archived.
    from assurance_domain.errors import NotFoundError
    a = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    b = service.create_engagement(ALICE, "Bolt", "2025-12-31")["engagement_id"]
    b_file = service.store_source(ALICE, b, content=PAYMENTS_CSV, media_type="text/csv",
                                  original_name="b_payments.csv")
    b_spec = service.confirm_source_mapping(ALICE, b, role="Payments",
                                            artifact_id=b_file["artifact_id"])
    service.archive_engagement(ALICE, b, reason="kept for the record only")
    with pytest.raises(NotFoundError):
        service.confirm_source_mapping(ALICE, a, role="Payments",
                                       artifact_id=b_file["artifact_id"])
    with pytest.raises(NotFoundError):
        service.normalize_source(ALICE, a, b_spec["spec_id"])
    with pytest.raises(NotFoundError):
        service.confirm_pending_mapping(ALICE, a, b_spec["spec_id"])
    assert service.sources(a)["datasets"] == []
