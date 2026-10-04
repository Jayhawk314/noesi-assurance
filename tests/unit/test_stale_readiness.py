"""A blocked current population cannot make an old result look current."""

from assurance_domain.readiness import readiness


def test_blocked_and_excluded_procedures_still_report_stale_results():
    coverage = {"procedures": [
        {"procedure_id": "completion.uncorrected_misstatements",
         "status": "blocked", "selected": True, "execution_status": "stale"},
        {"procedure_id": "forensic.benford_first_digit",
         "status": "partial", "selected": False, "execution_status": "stale"},
    ], "evidence_requests": []}
    report = {"company": "Invented Company", "fye": "2025-12-31",
              "procedure_coverage": coverage}
    engagement = {"materiality": {"amount": "1000"},
                  "procedures": {"forensic.benford_first_digit": {
                      "selected": False, "rationale": "Not used in this invented scope"}}}
    blockers = readiness(report, engagement, {})["blockers"]
    by_code = {b["code"]: b for b in blockers}
    assert by_code["SELECTED_PROCEDURES_BLOCKED"]["items"] == [
        "completion.uncorrected_misstatements"]
    # Left out with a reason, a stale result no longer blocks: a procedure that
    # can no longer run could never clear it (review 3 Oct). Its findings still
    # need dispositions under open findings.
    assert by_code["PROCEDURE_RESULTS_STALE"]["items"] == [
        "completion.uncorrected_misstatements"]


def test_a_left_out_procedure_the_opinion_reads_still_blocks_when_stale():
    # The draft opinion reads these procedures' latest results even when left out.
    ids = ["completion.uncorrected_misstatements", "completion.going_concern_indicators",
           "completion.representation_letter", "debt.covenants"]
    coverage = {"procedures": [
        {"procedure_id": pid, "status": "partial", "selected": False,
         "execution_status": "stale"} for pid in ids], "evidence_requests": []}
    report = {"company": "Invented Company", "fye": "2025-12-31",
              "procedure_coverage": coverage}
    engagement = {"materiality": {"amount": "1000"},
                  "procedures": {pid: {"selected": False, "rationale": "Left out in this invented scope"}
                                 for pid in ids}}
    by_code = {b["code"]: b for b in readiness(report, engagement, {})["blockers"]}
    assert sorted(by_code["PROCEDURE_RESULTS_STALE"]["items"]) == sorted(ids)
