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
    assert by_code["PROCEDURE_RESULTS_STALE"]["items"] == [
        "completion.uncorrected_misstatements", "forensic.benford_first_digit"]
