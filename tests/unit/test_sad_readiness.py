# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""SAD and readiness: shadow-diffed against goldens, plus v2 semantics."""

import json
from pathlib import Path

from assurance_domain.readiness import blank_engagement, readiness, scope_id
from assurance_domain.sad import finding_id, summary_of_differences
from procedures_ap.coverage import compile_coverage

BUNDLES = Path(__file__).resolve().parent.parent / "golden" / "bundles"


def _load(name: str) -> dict:
    return json.loads((BUNDLES / name).read_text(encoding="utf-8"))


# ------------------------------------------------------------------- shadow

def test_sad_summary_matches_golden_exactly():
    golden = _load("sad_summary.json")
    rows = [dict(row) for row in golden["rows"]]
    produced = summary_of_differences(rows, materiality=golden["materiality"])
    assert produced == golden["summary"]


def test_readiness_matches_golden_exactly():
    golden = _load("readiness_blank.json")
    partial = _load("coverage_partial.json")["coverage"]  # legacy-shaped input
    report = {"company": "Acme", "fye": "2025-12-31", "verdicts": [],
              "procedure_coverage": partial}
    produced = readiness(report, blank_engagement(report),
                         summary_of_differences([], materiality=0.0))
    assert produced == golden["readiness"]


# --------------------------------------------------- D1 consequence surfaces

def test_v2_coverage_makes_unrun_executables_block_completion():
    """With D1 coverage, executable-but-never-run procedures gate completion.

    The prototype's "completed at compile" defect hid this blocker; the same
    engagement state now honestly reports the pending runs.
    """
    golden = _load("coverage_partial.json")
    v2_coverage = compile_coverage(golden["inventory"])
    report = {"company": "Acme", "fye": "2025-12-31", "verdicts": [],
              "procedure_coverage": v2_coverage}
    produced = readiness(report, blank_engagement(report),
                         summary_of_differences([], materiality=0.0))
    codes = {blocker["code"] for blocker in produced["blockers"]}
    assert "SELECTED_PROCEDURES_PENDING_RUN" in codes
    pending = next(b for b in produced["blockers"]
                   if b["code"] == "SELECTED_PROCEDURES_PENDING_RUN")
    executable = [row["procedure_id"] for row in v2_coverage["procedures"]
                  if row["status"] == "executable"]
    assert pending["items"] == executable


# -------------------------------------------------------------- v2 identity

def test_finding_identity_prefers_engagement_scoped_uid():
    legacy_row = {"engagement": "Acme", "domain": "audit_procedure_run",
                  "key": ["tie", "x"]}
    v2_row = {**legacy_row, "finding_uid": "f-7c1a"}
    assert finding_id(legacy_row) == "Acme|audit_procedure_run|['tie', 'x']"
    assert finding_id(v2_row) == "f-7c1a"


def test_sad_groups_by_uid_when_present():
    rows = [
        {"engagement": "Acme", "domain": "d", "key": ["a"], "verdict": "CLASH",
         "score": 100.0, "reason": "r", "finding_uid": "f-1",
         "evidence": {"finding_class": "PROVED_EXCEPTION"},
         "disposition": "unadjusted"},
        {"engagement": "Acme", "domain": "d", "key": ["b"], "verdict": "CLASH",
         "score": 50.0, "reason": "r", "finding_uid": "f-1",
         "evidence": {"finding_class": "PROVED_EXCEPTION"},
         "disposition": "unadjusted"},
    ]
    summary = summary_of_differences(rows, materiality=10000.0)
    assert len(summary["unadjusted"]) == 1  # same uid -> one SAD line
    assert summary["unadjusted"][0]["amount"] == 150.0


# ------------------------------------------------------- implication ladder

def _green_engagement(report):
    engagement = blank_engagement(report)
    engagement["materiality"]["amount"] = 10000.0
    for stage in engagement["stages"].values():
        stage["status"] = "complete"
    for check in engagement["completion"].values():
        check["done"] = True
        check["note"] = "performed"
    return engagement


def test_clean_engagement_is_an_unmodified_opinion_candidate():
    report = {"company": "Acme", "fye": "2025-12-31", "verdicts": [],
              "refusals": []}
    sad = summary_of_differences([], materiality=10000.0)
    produced = readiness(report, _green_engagement(report), sad)
    assert produced["ready"] is True
    assert produced["report_implication"] == "unmodified_opinion_candidate"


def test_scope_limitation_forces_qualification_consideration():
    refusal = {"procedure": "bank_clearing", "reason": "no bank feed",
               "cycle": "cash"}
    report = {"company": "Acme", "fye": "2025-12-31", "verdicts": [],
              "refusals": [refusal]}
    engagement = _green_engagement(report)
    engagement["scope"][scope_id(refusal)] = {"status": "scope_limitation"}
    sad = summary_of_differences([], materiality=10000.0)
    produced = readiness(report, engagement, sad)
    assert produced["ready"] is True
    assert produced["report_implication"] == "qualified_or_disclaimer_consideration"
    assert produced["scope_limitations"] == 1


def test_material_unadjusted_total_forces_adverse_consideration():
    rows = [{"engagement": "Acme", "domain": "d", "key": ["a"],
             "verdict": "CLASH", "score": 15000.0, "reason": "big",
             "evidence": {"finding_class": "PROVED_EXCEPTION"},
             "disposition": "unadjusted"}]
    report = {"company": "Acme", "fye": "2025-12-31", "verdicts": [],
              "refusals": []}
    sad = summary_of_differences(rows, materiality=10000.0)
    assert sad["conclusion"] == "material"
    produced = readiness(report, _green_engagement(report), sad)
    assert produced["ready"] is True
    assert produced["report_implication"] == "qualified_or_adverse_consideration"


def test_broken_trail_blocks_readiness():
    report = {"company": "Acme", "fye": "2025-12-31", "verdicts": [],
              "refusals": []}
    sad = summary_of_differences([], materiality=10000.0)
    produced = readiness(report, _green_engagement(report), sad,
                         trail_status={"ok": False})
    assert produced["ready"] is False
    assert {"code": "DECISION_TRAIL_BROKEN", "count": 1} in produced["blockers"]
