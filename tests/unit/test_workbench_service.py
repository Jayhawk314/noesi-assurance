"""The six screens as one journey: engagement -> sources -> coverage ->
runs -> SAD/readiness -> lock, with server-side authorization throughout."""

import pytest

from assurance_application.service import AuthorizationError, WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_domain.lifecycle import SeparationOfDutiesError
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
    from assurance_artifacts.signing import LocalKeyStore
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    tenant = ensure_tenant(conn, "firm")
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), tenant,
                           keystore=LocalKeyStore(tmp_path / "keys"))
    conn.close()


@pytest.fixture()
def engagement(service):
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    service.assign_team(ALICE, eid, BOB, "preparer")
    service.assign_team(ALICE, eid, CAROL, "reviewer")
    return eid


def _ingest(service, eid, content, name, role):
    artifact = service.store_source(
        BOB, eid, content=content, media_type="text/csv", original_name=name)
    proposal = service.propose_source_mapping(
        BOB, eid, role=role, artifact_id=artifact["artifact_id"])
    service.approve_source_mapping(CAROL, eid, proposal["spec_id"])
    return service.normalize_source(BOB, eid, proposal["spec_id"])


def test_engagement_creator_becomes_partner_and_assigns_team(service):
    eid = service.create_engagement(ALICE, "Acme", "2025-12-31")["engagement_id"]
    service.assign_team(ALICE, eid, BOB, "preparer")
    team = service.team(eid)
    assert {(m["principal_id"], m["role"]) for m in team} == {
        (ALICE, "partner"), (BOB, "preparer")}
    with pytest.raises(AuthorizationError):
        service.assign_team(BOB, eid, CAROL, "reviewer")


def test_source_to_normalized_dataset_with_review_gate(service, engagement):
    result = _ingest(service, engagement, PAYMENTS_CSV, "payments.csv",
                     "Payments")
    recon = result["reconciliation"]
    assert recon["rows_loaded"] == 3
    assert recon["control_total"] == "13000.00"
    # No creator/approver/check columns in this export — refused, not guessed.
    assert recon["refused_fields"] == ["created_by", "approved_by",
                                       "check_number"]


def test_unassigned_principals_cannot_touch_sources(service, engagement):
    with pytest.raises(AuthorizationError):
        service.store_source("principal-stranger", engagement,
                             content=PAYMENTS_CSV, media_type="text/csv",
                             original_name="x.csv")
    with pytest.raises(AuthorizationError):
        service.propose_source_mapping(CAROL, engagement, role="Payments",
                                       artifact_id="whatever")


def test_coverage_reflects_normalized_datasets(service, engagement):
    _ingest(service, engagement, PAYMENTS_CSV, "payments.csv", "Payments")
    coverage = service.coverage(engagement)
    by_id = {row["procedure_id"]: row for row in coverage["procedures"]}
    split = by_id["ap.split_payment_review"]
    assert split["status"] == "partial"          # threshold policy missing
    assert split["missing_policies"] == ["split_threshold"]
    assert by_id["ap.subledger_gl_balance_tie"]["status"] == "blocked"
    assert coverage["summary"]["total"] == 11


def test_run_review_approve_lifecycle_with_separation(service, engagement):
    _ingest(service, engagement, PAYMENTS_CSV, "payments.csv", "Payments")
    run = service.run_procedure(
        BOB, engagement, procedure_id="ap.split_payment_review",
        policies={"split_threshold": "10000"})
    assert run["status"] == "completed"
    assert run["findings"] == 1

    with pytest.raises(AuthorizationError):   # executor cannot review
        service.review_run(BOB, engagement, run["run_id"],
                           target="reviewed", expected_version=1)
    reviewed = service.review_run(CAROL, engagement, run["run_id"],
                                  target="reviewed", expected_version=1)
    # Even with partner authority, the reviewing principal cannot approve
    # their own review — separation fires after the role gate.
    service.assign_team(ALICE, engagement, CAROL, "partner")
    with pytest.raises(SeparationOfDutiesError):
        service.review_run(CAROL, engagement, run["run_id"],
                           target="approved",
                           expected_version=reviewed["version"])
    approved = service.review_run(ALICE, engagement, run["run_id"],
                                  target="approved",
                                  expected_version=reviewed["version"])
    assert approved["status"] == "approved"


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
    sad = service.sad(engagement, materiality=10000.0)
    assert sad["total_unadjusted"] == 5000.0
    assert sad["conclusion"] == "immaterial"
    assert sad["candidates"] == 1  # the split cluster is a lead, not a SAD item


def test_readiness_gates_a_partially_worked_engagement(service, engagement):
    _ingest(service, engagement, PAYMENTS_CSV, "payments.csv", "Payments")
    state = service.readiness(engagement)
    codes = {b["code"] for b in state["blockers"]}
    assert "MATERIALITY_NOT_SET" in codes
    assert "SELECTED_PROCEDURES_BLOCKED" in codes
    assert state["ready"] is False
    locked = service.lock(ALICE, engagement, expected_version=1)
    assert locked["locked"] is False
    assert locked["blockers"]


def test_green_engagement_locks_and_lock_requires_partner(service):
    eid = service.create_engagement(ALICE, "Zenith", "2025-06-30")["engagement_id"]
    service.update_workflow(ALICE, eid, "materiality",
                            {"amount": 10000.0, "basis": "revenue"})
    for stage in ("risk_assessment", "controls"):
        service.update_workflow(ALICE, eid, "stage",
                                {"name": stage, "status": "complete"})
    from assurance_domain.readiness import COMPLETION_CHECKS
    for check in COMPLETION_CHECKS:
        service.update_workflow(ALICE, eid, "completion",
                                {"name": check, "done": True,
                                 "note": "performed"})
    state = service.readiness(eid)
    assert state["ready"] is True
    assert state["report_implication"] == "unmodified_opinion_candidate"

    service.assign_team(ALICE, eid, BOB, "preparer")
    with pytest.raises(AuthorizationError):
        service.lock(BOB, eid, expected_version=1)
    locked = service.lock(ALICE, eid, expected_version=1)
    assert locked["locked"] is True
    assert service.list_engagements()[-1]["status"] == "locked"


def test_dataset_rebuild_is_digest_verified(service, engagement, tmp_path):
    _ingest(service, engagement, PAYMENTS_CSV, "payments.csv", "Payments")
    # Corrupt the vault blob; coverage must refuse, not serve silently.
    sha = service._conn.execute("SELECT sha256 FROM artifact").fetchone()["sha256"]
    blob = service._vault._blob_path(sha)
    blob.write_bytes(PAYMENTS_CSV.replace(b"6000.00", b"9999.99"))
    with pytest.raises(Exception):
        service.coverage(engagement)
