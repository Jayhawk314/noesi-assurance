# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The draft opinion: the proposal the evidence points to, and the decisions
left to the partner. Pure-function tests on invented engagement states, plus
one through the workbench."""

from assurance_domain.opinion import draft_opinion

READY = {"ready": True, "blockers": []}
SAD = {"total_unadjusted": 0.0}


def finding(procedure, key, verdict, cls="PROVED_EXCEPTION", status="undisposed"):
    return {"procedure_id": procedure, "disposition": {"status": status},
            "verdict": {"key": [procedure, *key], "verdict": verdict,
                        "evidence": {"finding_class": cls}}}


def summary(income="0", assets="0"):
    return {"summary": {"totals": {"identified": "0", "likely": "0",
                                   "income_before_taxes": income,
                                   "current_assets": assets}}}


def opinion(findings=(), run=None, completion=None, readiness=READY, materiality=15000):
    return draft_opinion(readiness=readiness, sad=SAD, findings=list(findings),
                         misstatement_run=run, materiality=materiality,
                         completion=completion or {})


def test_clean_engagement_points_to_an_unmodified_opinion():
    out = opinion(run=summary("-4354.51", "-2514.51"))
    assert out["proposed_opinion"] == "unmodified"
    assert out["status"] == "draft_for_partner"
    assert out["misstatements"]["amount"] == "4354.51"
    assert "summary of uncorrected misstatements" in out["misstatements"]["source"]


def test_misstatements_above_materiality_leave_pervasiveness_to_the_partner():
    out = opinion(run=summary("-22000"))
    assert out["proposed_opinion"] == "qualified_or_adverse"
    assert [d["decision"] for d in out["decisions_required"]] == [
        "pervasiveness_of_misstatement"]
    assert out["status"] == "not_ready"          # a decision is still open


def test_missing_representations_point_to_a_disclaimer():
    rep = finding("completion.representation_letter", ["related_parties", "not_obtained"],
                  "CLASH")
    out = opinion([rep], run=summary("-100"))
    assert out["proposed_opinion"] == "disclaimer"
    assert out["missing_representations"] == ["related_parties"]


def test_an_open_scope_limitation_is_not_ignored_but_a_resolved_one_is():
    gap = finding("completion.subsequent_events", ["no_subsequent_records"], "AMBIGUOUS",
                  cls="REFUSAL")
    assert opinion([gap], run=summary())["proposed_opinion"] == "qualified_or_disclaimer"
    resolved = dict(gap, disposition={"status": "cleared"})
    assert opinion([resolved], run=summary())["proposed_opinion"] == "unmodified"


def test_going_concern_indicators_need_the_partners_recorded_conclusion():
    gc = finding("completion.going_concern_indicators", ["net_loss"], "TENSION",
                 cls="CONJECTURE")
    out = opinion([gc], run=summary())
    assert out["status"] == "not_ready"
    assert out["decisions_required"][0]["decision"] == "going_concern_conclusion"
    concluded = opinion([gc], run=summary(), completion={
        "going_concern": {"done": True, "note": "no substantial doubt: new financing"}})
    assert concluded["status"] == "draft_for_partner"
    assert any("going-concern conclusion recorded" in r for r in concluded["basis"])


def test_without_a_summary_the_sad_is_used_and_named():
    out = draft_opinion(readiness=READY, sad={"total_unadjusted": 20000.0}, findings=[],
                        misstatement_run=None, materiality=15000, completion={})
    assert out["proposed_opinion"] == "qualified_or_adverse"
    assert out["misstatements"]["source"].startswith("SAD")


def test_readiness_blockers_keep_it_a_draft():
    out = opinion(run=summary(), readiness={"ready": False,
                                            "blockers": [{"code": "FINDINGS_OPEN"}]})
    assert out["status"] == "not_ready"
    assert out["readiness_blockers"] == [{"code": "FINDINGS_OPEN"}]


def test_the_workbench_serves_a_draft_opinion(tmp_path):
    from assurance_application.service import WorkbenchService
    from assurance_artifacts.vault import ArtifactVault
    from assurance_persistence.database import connect, migrate
    from assurance_persistence.legacy_import import ensure_tenant
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    svc = WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "o"))
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    out = svc.draft_opinion(eid)
    assert out["status"] == "not_ready"              # nothing done yet
    assert out["proposed_opinion"] in ("unmodified", "qualified_or_adverse")
    conn.close()


def test_letter_problems_are_not_missing_representations():
    undated = finding("completion.representation_letter",
                      ["letter", "not_dated_report_date"], "CLASH")
    out = opinion([undated], run=summary())
    assert out["missing_representations"] == []
    assert out["proposed_opinion"] == "unmodified"
    assert [d["decision"] for d in out["decisions_required"]] == [
        "correct_the_representation_letter"]


def test_a_breached_covenant_calls_for_a_going_concern_conclusion():
    breach = finding("debt.covenants", ["current ratio", "breached"], "CLASH")
    out = opinion([breach], run=summary())
    assert out["going_concern_indicators"] == ["covenant_breached: current ratio"]
    assert out["decisions_required"][0]["decision"] == "going_concern_conclusion"


# ------------------------------------------------ final review (2026-09-29)
def test_final_f2_a_scope_limitation_does_not_hide_a_material_misstatement():
    gap = finding("completion.subsequent_events", ["no_subsequent_records"], "AMBIGUOUS",
                  cls="REFUSAL")
    out = opinion([gap], run=summary("0", "-20000"))
    assert out["proposed_opinion"] == "qualified_adverse_or_disclaimer"
    assert {d["decision"] for d in out["decisions_required"]} == {
        "pervasiveness_of_scope_limitation", "pervasiveness_of_misstatement"}


def test_final_f3_a_misstatement_equal_to_materiality_is_material():
    out = opinion(run=summary("-15000"))
    assert out["proposed_opinion"] == "qualified_or_adverse"
    assert not any("below materiality" in r for r in out["basis"])


# ------------------------------------------------ the partner's decisions
def test_recorded_decisions_settle_the_opinion():
    gap = finding("completion.subsequent_events", ["no_subsequent_records"], "AMBIGUOUS",
                  cls="REFUSAL")
    both = [gap]
    run = summary("0", "-20000")
    assert opinion(both, run=run)["opinion"] is None          # judgments still open
    rec = {"pervasiveness_of_scope_limitation": {"answer": "not_pervasive"},
           "pervasiveness_of_misstatement": {"answer": "not_pervasive"}}
    out = draft_opinion(readiness=READY, sad=SAD, findings=both, misstatement_run=run,
                        materiality=15000, completion={}, recorded=rec)
    assert out["opinion"] == "qualified" and out["decisions_required"] == []
    rec["pervasiveness_of_misstatement"] = {"answer": "pervasive"}
    out = draft_opinion(readiness=READY, sad=SAD, findings=both, misstatement_run=run,
                        materiality=15000, completion={}, recorded=rec)
    assert out["opinion"] == "adverse"
    rec["pervasiveness_of_scope_limitation"] = {"answer": "pervasive"}
    out = draft_opinion(readiness=READY, sad=SAD, findings=both, misstatement_run=run,
                        materiality=15000, completion={}, recorded=rec)
    assert out["opinion"] == "disclaimer"


def test_going_concern_answers():
    gc = finding("completion.going_concern_indicators", ["net_loss"], "TENSION",
                 cls="CONJECTURE")
    disclosed = draft_opinion(readiness=READY, sad=SAD, findings=[gc],
                              misstatement_run=summary(), materiality=15000,
                              completion={}, recorded={"going_concern_conclusion": {
                                  "answer": "substantial_doubt_disclosed"}})
    assert disclosed["opinion"] == "unmodified" and disclosed["going_concern_section"]
    undisclosed = draft_opinion(readiness=READY, sad=SAD, findings=[gc],
                                misstatement_run=summary(), materiality=15000,
                                completion={}, recorded={"going_concern_conclusion": {
                                    "answer": "substantial_doubt_not_disclosed"}})
    assert undisclosed["proposed_opinion"] == "qualified_or_adverse"
    assert [d["decision"] for d in undisclosed["decisions_required"]] == [
        "pervasiveness_of_misstatement"]


def test_a_decision_is_recorded_with_a_reason(tmp_path):
    import pytest as _pytest
    from assurance_application.service import WorkbenchService
    from assurance_artifacts.vault import ArtifactVault
    from assurance_persistence.database import connect, migrate
    from assurance_persistence.legacy_import import ensure_tenant
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    svc = WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "o"))
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    decide = {"decision": "pervasiveness_of_misstatement", "answer": "not_pervasive",
              "note": "confined to inventory; statements usable"}
    with _pytest.raises(ValueError, match="reason"):
        svc.update_workflow("pa", eid, "opinion_decision", {**decide, "note": "ok"})
    with _pytest.raises(ValueError, match="takes one of"):
        svc.update_workflow("pa", eid, "opinion_decision", {**decide, "answer": "maybe"})
    svc.update_workflow("pa", eid, "opinion_decision", decide)
    recorded = svc.draft_opinion(eid)["recorded_decisions"]
    assert recorded["pervasiveness_of_misstatement"]["decided_by"] == "pa"
    conn.close()
