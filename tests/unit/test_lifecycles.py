"""State machines: every run walks one lifecycle; review separation holds."""

import pytest

from assurance_domain.lifecycle import (
    InvalidTransition, SeparationOfDutiesError, advance, require_separation,
)


def test_full_procedure_run_lifecycle_is_legal():
    state = "planned"
    for target in ("executable", "queued", "running", "completed",
                   "reviewed", "approved"):
        state = advance("procedure_run", state, target)
    assert state == "approved"


def test_field_presence_can_never_mean_completed():
    # The prototype's P1 defect: executable jumped straight to completed.
    with pytest.raises(InvalidTransition):
        advance("procedure_run", "executable", "completed")
    with pytest.raises(InvalidTransition):
        advance("procedure_run", "planned", "completed")


def test_error_runs_can_be_requeued_but_approved_is_terminal():
    assert advance("procedure_run", "error", "queued") == "queued"
    with pytest.raises(InvalidTransition):
        advance("procedure_run", "approved", "queued")


def test_evidence_upload_is_not_validation():
    assert advance("evidence", "received", "validated") == "validated"
    with pytest.raises(InvalidTransition):
        advance("evidence", "open", "validated")
    with pytest.raises(InvalidTransition):
        advance("evidence", "requested", "validated")


def test_rejected_evidence_can_be_resubmitted():
    assert advance("evidence", "rejected", "received") == "received"


def test_preparer_cannot_approve_own_work():
    require_separation(prepared_by="principal-1", approved_by="principal-2")
    with pytest.raises(SeparationOfDutiesError):
        require_separation(prepared_by="principal-1", approved_by="principal-1")
    with pytest.raises(SeparationOfDutiesError):
        require_separation(prepared_by="", approved_by="principal-2")
