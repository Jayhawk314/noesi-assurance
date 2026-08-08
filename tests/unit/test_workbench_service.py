# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
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


def test_excel_uploads_are_refused_at_mapping_with_instructions(service,
                                                                engagement):
    artifact = service.store_source(
        BOB, engagement, content=b"PK\x03\x04" + b"\x00" * 64,
        media_type="application/vnd.openxmlformats-officedocument"
                   ".spreadsheetml.sheet",
        original_name="payments.xlsx")
    with pytest.raises(ValueError, match="Excel workbook"):
        service.propose_source_mapping(
            BOB, engagement, role="Payments",
            artifact_id=artifact["artifact_id"])


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
    # $5,000 is far above clearly-trivial ($500 at this materiality): the
    # disposition is a proposal, and the SAD refuses to conclude over it.
    sad = service.sad(engagement, materiality=10000.0)
    assert sad["total_unadjusted"] == 5000.0
    assert sad["concurrence_pending"] == [tie["finding_uid"]]
    assert sad["conclusion"] is None
    assert sad["candidates"] == 1  # the split cluster is a lead, not a SAD item

    service.concur_disposition(CAROL, engagement,
                               finding_uid=tie["finding_uid"],
                               expected_version=1)
    sad = service.sad(engagement, materiality=10000.0)
    assert sad["concurrence_pending_count"] == 0
    assert sad["conclusion"] == "immaterial"


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


# --------------------------------------------------------------- bulk loading

def test_bulk_loading_is_one_pass_per_chair_with_inference(service, engagement):
    ids = []
    for name, content in (("payments.csv", PAYMENTS_CSV),
                          ("ap_control_balance.csv", BALANCES_CSV)):
        artifact = service.store_source(
            BOB, engagement, content=content, media_type="text/csv",
            original_name=name)
        ids.append(artifact["artifact_id"])

    # The inventory suggests roles; the suggestion is not a mapping.
    inventory = service.sources(engagement)
    assert [a["inferred_role"] for a in inventory["artifacts"]] == [
        "Payments", "AP_control_balance"]

    # Preparer pass: one batch, roles inferred from filenames.
    proposals = service.propose_source_mappings(
        BOB, engagement, [{"artifact_id": aid} for aid in ids])
    assert proposals["proposed"] == 2 and proposals["errors"] == 0
    assert [r["role"] for r in proposals["results"]] == [
        "Payments", "AP_control_balance"]
    spec_ids = [r["spec_id"] for r in proposals["results"]]

    # Repeating the batch skips, so 'propose all' is idempotent.
    again = service.propose_source_mappings(
        BOB, engagement, [{"artifact_id": aid} for aid in ids])
    assert again["skipped"] == 2 and again["proposed"] == 0

    # The reviewer gate still stands: the preparer cannot batch-approve.
    with pytest.raises(AuthorizationError):
        service.approve_source_mappings(BOB, engagement, spec_ids)

    # Normalizing before approval fails per item, batching or not.
    early = service.normalize_sources(BOB, engagement, spec_ids)
    assert early["errors"] == 2

    # Reviewer pass, then preparer pass.
    approvals = service.approve_source_mappings(CAROL, engagement, spec_ids)
    assert approvals["approved"] == 2 and approvals["errors"] == 0

    normalized = service.normalize_sources(BOB, engagement, spec_ids)
    assert normalized["normalized"] == 2 and normalized["errors"] == 0
    recon = {r["reconciliation"]["role"]: r["reconciliation"]
             for r in normalized["results"]}
    assert recon["Payments"]["rows_loaded"] == 3
    assert recon["Payments"]["control_total"] == "13000.00"

    # Re-normalizing skips instead of minting duplicate receipts.
    again = service.normalize_sources(BOB, engagement, spec_ids)
    assert again["skipped"] == 2 and again["normalized"] == 0


def test_bulk_proposal_reports_per_item_without_blocking_the_rest(
        service, engagement):
    good = service.store_source(
        BOB, engagement, content=PAYMENTS_CSV, media_type="text/csv",
        original_name="payments.csv")["artifact_id"]
    unnamed = service.store_source(
        BOB, engagement, content=BALANCES_CSV, media_type="text/csv",
        original_name="export_final_v2.csv")["artifact_id"]

    outcome = service.propose_source_mappings(
        BOB, engagement,
        [{"artifact_id": good},
         {"artifact_id": unnamed},                       # nothing inferable
         {"artifact_id": "no-such-artifact"}])
    assert outcome["proposed"] == 1 and outcome["errors"] == 2
    by_id = {r["artifact_id"]: r for r in outcome["results"]}
    assert by_id[good]["status"] == "proposed"
    assert "choose the role explicitly" in by_id[unnamed]["error"]
    assert by_id["no-such-artifact"]["status"] == "error"

    # An uninferable file loads fine once the preparer names the role.
    named = service.propose_source_mappings(
        BOB, engagement,
        [{"artifact_id": unnamed, "role": "AP_control_balance"}])
    assert named["proposed"] == 1


def test_bulk_approval_enforces_separation_per_item(service, engagement):
    # Dana holds both chairs; the batch approves Bob's spec but refuses the
    # one Dana proposed — separation is judged item by item.
    service.assign_team(ALICE, engagement, "principal-dana", "preparer")
    service.assign_team(ALICE, engagement, "principal-dana", "reviewer")
    bobs = service.store_source(
        BOB, engagement, content=PAYMENTS_CSV, media_type="text/csv",
        original_name="payments.csv")["artifact_id"]
    danas = service.store_source(
        "principal-dana", engagement, content=BALANCES_CSV,
        media_type="text/csv",
        original_name="ap_control_balance.csv")["artifact_id"]
    specs = [
        service.propose_source_mapping(
            BOB, engagement, role="Payments",
            artifact_id=bobs)["spec_id"],
        service.propose_source_mapping(
            "principal-dana", engagement, role="AP_control_balance",
            artifact_id=danas)["spec_id"],
    ]
    outcome = service.approve_source_mappings(
        "principal-dana", engagement, specs)
    assert outcome["approved"] == 1 and outcome["errors"] == 1
    assert outcome["results"][0]["status"] == "approved"
    assert outcome["results"][1]["status"] == "error"


# ------------------------------------------------- disposition concurrence

def _tie_finding(service, engagement):
    _ingest(service, engagement, PAYMENTS_CSV, "payments.csv", "Payments")
    _ingest(service, engagement, BALANCES_CSV, "recon.csv",
            "AP_control_balance")
    service.run_procedure(BOB, engagement,
                          procedure_id="ap.subledger_gl_balance_tie")
    return next(f for f in service.findings(engagement)
                if f["procedure_id"] == "ap.subledger_gl_balance_tie")


def test_disposition_concurrence_mirrors_the_review_gates(service, engagement):
    service.update_workflow(ALICE, engagement, "materiality",
                            {"amount": 10000.0, "basis": "revenue"})
    tie = _tie_finding(service, engagement)
    service.set_disposition(BOB, engagement, finding_uid=tie["finding_uid"],
                            status="unadjusted", note="client declines")

    # The preparer proposed; the preparer cannot concur — not for lack of
    # a role, but because it is their own judgment.
    with pytest.raises(AuthorizationError):
        service.concur_disposition(BOB, engagement,
                                   finding_uid=tie["finding_uid"],
                                   expected_version=1)
    service.assign_team(ALICE, engagement, BOB, "reviewer")
    with pytest.raises(SeparationOfDutiesError):
        service.concur_disposition(BOB, engagement,
                                   finding_uid=tie["finding_uid"],
                                   expected_version=1)

    state = service.readiness(engagement)
    pending = next(b for b in state["blockers"]
                   if b["code"] == "DISPOSITIONS_AWAITING_CONCURRENCE")
    assert pending["items"] == [tie["finding_uid"]]

    outcome = service.concur_disposition(CAROL, engagement,
                                         finding_uid=tie["finding_uid"],
                                         expected_version=1)
    assert outcome["concurred_by"] == CAROL
    codes = {b["code"] for b in service.readiness(engagement)["blockers"]}
    assert "DISPOSITIONS_AWAITING_CONCURRENCE" not in codes

    # A changed judgment voids the old concurrence: re-set, and the
    # finding is awaiting concurrence again.
    service.set_disposition(BOB, engagement, finding_uid=tie["finding_uid"],
                            status="adjusted", note="client booked it",
                            expected_version=2)
    refreshed = next(f for f in service.findings(engagement)
                     if f["finding_uid"] == tie["finding_uid"])
    assert refreshed["awaiting_concurrence"] is True
    assert refreshed["disposition"]["concurred_by"] == ""


def test_below_clearly_trivial_needs_no_concurrence(service, engagement):
    # $5,000 misstatement under a $200,000 materiality: clearly trivial
    # territory ($10,000); one person's judgment stands alone.
    service.update_workflow(ALICE, engagement, "materiality",
                            {"amount": 200000.0, "basis": "assets"})
    tie = _tie_finding(service, engagement)
    assert tie["requires_concurrence"] is False
    service.set_disposition(BOB, engagement, finding_uid=tie["finding_uid"],
                            status="unadjusted", note="clearly trivial")
    sad = service.sad(engagement)
    assert sad["concurrence_pending_count"] == 0
    assert sad["conclusion"] == "immaterial"
