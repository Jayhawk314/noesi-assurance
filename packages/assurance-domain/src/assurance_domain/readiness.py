# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Completion readiness: the gates that decide whether an engagement can close.

Faithful port of the prototype's readiness derivation — blocker codes,
ordering, and the report-implication ladder are unchanged and shadow-tested
against the Phase 0 golden. One consequence of divergence D1 surfaces here
deliberately: with v2 coverage, executable-but-never-run procedures now
raise ``SELECTED_PROCEDURES_PENDING_RUN``, a real gate the prototype's
"completed at compile" defect used to mask.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal

from assurance_domain.money import parse_amount

COMPLETION_CHECKS = (
    "final_analytical_review",
    "subsequent_events",
    "going_concern",
    "management_representations",
    "evidence_sufficiency",
    "engagement_review",
)


def scope_id(item: dict) -> str:
    """Stable identity for a refusal/scope item without mutating the item."""
    payload = json.dumps(item, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, default=str).encode("utf-8")
    return "scope|" + hashlib.sha256(payload).hexdigest()[:20]


def legacy_report_finding_id(report: dict, item: dict) -> str:
    """Legacy report-scoped finding identity (company-based, no period).

    Kept only because engagement risk/control assessments are keyed by it in
    migrated workflow documents. New assessments must key by engagement-scoped
    finding UID; this helper is not for new identities.
    """
    verdict = item["verdict"]
    key = " · ".join(str(x) for x in verdict.get("key", []))
    return f"{report['company']}|{verdict['domain']}|{key}"


def blank_engagement(report: dict) -> dict:
    """The empty engagement workflow document (legacy-shape, Phase 1 payload)."""
    return {
        "company": report.get("company", "engagement"),
        "fye": report.get("fye", ""),
        "materiality": {"amount": 0.0, "basis": "", "rationale": ""},
        "stages": {
            "risk_assessment": {"status": "not_started", "note": ""},
            "controls": {"status": "not_started", "note": ""},
        },
        "risks": {},
        "controls": {},
        "procedures": {},
        "procedure_runs": {},
        "procedure_run_history": {},
        "procedure_run_reviews": {},
        "rerun_requests": {},
        "evidence_requests": {},
        "team": {"preparer": "", "reviewer": "", "engagement_partner": ""},
        "data_approvals": {},
        "workpaper_lock": {"status": "unlocked"},
        "lock_history": [],
        "scope": {},
        "completion": {
            name: {"done": False, "note": "", "evidence": []}
            for name in COMPLETION_CHECKS
        },
    }


def _phase_items(report: dict, phase: str) -> list[dict]:
    return [item for item in report.get("verdicts", [])
            if item.get("tags", {}).get("phase") == phase]


def readiness(report: dict, engagement: dict, sad: dict,
              trail_status: dict | None = None,
              procedure_coverage: dict | None = None,
              review_sources: list[dict] | None = None) -> dict:
    """Derive completion readiness and possible reporting implications."""
    blockers: list[dict] = []

    materiality = engagement.get("materiality", {})
    amount = parse_amount(materiality.get("amount")) or Decimal("0")
    if amount <= 0:
        blockers.append({"code": "MATERIALITY_NOT_SET", "count": 1})

    for phase in ("risk_assessment", "controls"):
        stage = engagement.get("stages", {}).get(phase, {})
        if stage.get("status") != "complete":
            blockers.append({"code": f"{phase.upper()}_NOT_COMPLETE", "count": 1})

    risk_items = _phase_items(report, "risk_assessment")
    risk_ids = [legacy_report_finding_id(report, item) for item in risk_items]
    risk_ids.extend(
        fid for fid, record in engagement.get("risks", {}).items()
        if record.get("manual") and not record.get("archived")
        and fid not in risk_ids
    )
    unassessed_risks = []
    missing_responses = []
    missing_procedure_links = []
    have_procedure_contracts = bool(
        (report.get("procedure_coverage") or {}).get("procedures"))
    if have_procedure_contracts:
        team = engagement.get("team", {})
        missing_team = [role for role in ("preparer", "reviewer")
                        if not team.get(role)]
        if missing_team:
            blockers.append({"code": "TEAM_ASSIGNMENTS_INCOMPLETE",
                             "count": len(missing_team), "items": missing_team})
    for fid in risk_ids:
        assessment = engagement.get("risks", {}).get(fid, {})
        level = assessment.get("level", "unassessed")
        if level == "unassessed":
            unassessed_risks.append(fid)
        if level in ("high", "significant") and not assessment.get("response"):
            missing_responses.append(fid)
        if (have_procedure_contracts and level in ("high", "significant")
                and not assessment.get("procedure_ids")):
            missing_procedure_links.append(fid)
    if unassessed_risks:
        blockers.append({"code": "RISKS_UNASSESSED", "count": len(unassessed_risks)})
    if missing_responses:
        blockers.append({"code": "HIGH_RISKS_WITHOUT_RESPONSE",
                         "count": len(missing_responses)})
    if missing_procedure_links:
        blockers.append({"code": "HIGH_RISKS_WITHOUT_PROCEDURE",
                         "count": len(missing_procedure_links)})

    control_items = _phase_items(report, "controls")
    control_ids = [legacy_report_finding_id(report, item)
                   for item in control_items]
    control_ids.extend(
        fid for fid, record in engagement.get("controls", {}).items()
        if record.get("manual") and not record.get("archived")
        and fid not in control_ids
    )
    unassessed_controls = []
    invalid_reliance = []
    for fid in control_ids:
        assessment = engagement.get("controls", {}).get(fid, {})
        if assessment.get("design", "unassessed") == "unassessed" or \
                assessment.get("implementation", "unassessed") == "unassessed":
            unassessed_controls.append(fid)
        if assessment.get("reliance") and (
            assessment.get("design") != "effective"
            or assessment.get("implementation") != "implemented"
            or assessment.get("operating_effectiveness") != "effective"
        ):
            invalid_reliance.append(fid)
    if unassessed_controls:
        blockers.append({"code": "CONTROLS_UNASSESSED",
                         "count": len(unassessed_controls)})
    if invalid_reliance:
        blockers.append({"code": "CONTROL_RELIANCE_UNSUPPORTED",
                         "count": len(invalid_reliance)})

    procedure_coverage = (procedure_coverage
                          if procedure_coverage is not None
                          else report.get("procedure_coverage") or {})
    selected_blocked = []
    selected_partial = []
    selected_pending_run = []
    procedure_review_pending = []
    unjustified_exclusions = []
    for procedure in procedure_coverage.get("procedures", []):
        decision = engagement.get("procedures", {}).get(
            procedure.get("procedure_id"), {})
        selected = decision.get("selected", procedure.get("selected", True))
        if not selected:
            if not decision.get("rationale"):
                unjustified_exclusions.append(procedure.get("procedure_id"))
            continue
        if procedure.get("status") == "blocked":
            selected_blocked.append(procedure.get("procedure_id"))
        elif procedure.get("status") == "partial":
            selected_partial.append(procedure.get("procedure_id"))
        elif procedure.get("execution_status") in ("ready_to_run", "not_run", "error"):
            selected_pending_run.append(procedure.get("procedure_id"))
        run = procedure.get("procedure_run")
        if (run and run.get("status") == "completed"
                and run.get("review_status") != "approved"):
            procedure_review_pending.append(procedure.get("procedure_id"))
    if selected_blocked:
        blockers.append({"code": "SELECTED_PROCEDURES_BLOCKED",
                         "count": len(selected_blocked),
                         "items": selected_blocked})
    if selected_partial:
        blockers.append({"code": "SELECTED_PROCEDURES_PARTIAL",
                         "count": len(selected_partial),
                         "items": selected_partial})
    if selected_pending_run:
        blockers.append({"code": "SELECTED_PROCEDURES_PENDING_RUN",
                         "count": len(selected_pending_run),
                         "items": selected_pending_run})
    if procedure_review_pending:
        blockers.append({"code": "PROCEDURE_RUN_REVIEW_PENDING",
                         "count": len(procedure_review_pending),
                         "items": procedure_review_pending})
    if unjustified_exclusions:
        blockers.append({"code": "PROCEDURE_EXCLUSIONS_WITHOUT_RATIONALE",
                         "count": len(unjustified_exclusions),
                         "items": unjustified_exclusions})

    # A data-less engagement skips every procedure gate above, so a lock
    # could attest to no substantive work without anyone saying so. When
    # the application layer marks the assertion required (dataset count is
    # its fact, not this function's), the partner's explicit statement —
    # "no data-dependent procedures apply, because…" — is a gate like any
    # other. Legacy documents never carry the key and are unaffected.
    assertion = engagement.get("no_data_assertion") or {}
    if assertion.get("required") and not assertion.get("asserted"):
        blockers.append({"code": "NO_DATA_WITHOUT_PARTNER_ASSERTION",
                         "count": 1})

    evidence_review_pending = [
        item.get("request_id")
        for item in procedure_coverage.get("evidence_requests", [])
        if item.get("status") in ("received", "validated")
        and not item.get("fulfilled")
    ]
    if evidence_review_pending:
        blockers.append({"code": "EVIDENCE_REVIEW_PENDING",
                         "count": len(evidence_review_pending),
                         "items": evidence_review_pending})

    extraction_pending = []
    transformation_pending = []
    for source in review_sources or []:
        approval = source.get("current", {})
        if approval.get("extraction_result") != "approved":
            extraction_pending.append(source.get("source_id"))
        if (source.get("requires_transformation_approval")
                and approval.get("transformation_result") != "approved"):
            transformation_pending.append(source.get("source_id"))
    if extraction_pending:
        blockers.append({"code": "EXTRACTION_APPROVAL_PENDING",
                         "count": len(extraction_pending),
                         "items": extraction_pending})
    if transformation_pending:
        blockers.append({"code": "TRANSFORMATION_APPROVAL_PENDING",
                         "count": len(transformation_pending),
                         "items": transformation_pending})

    open_misstatements = int(sad.get("open_count") or sad.get("undisposed") or 0)
    if open_misstatements:
        blockers.append({"code": "MISSTATEMENTS_UNRESOLVED",
                         "count": open_misstatements})
    review_open = int(sad.get("review_open_count") or 0)
    if review_open:
        blockers.append({"code": "SUBSTANTIVE_ITEMS_UNRESOLVED",
                         "count": review_open})
    if sad.get("invalid_waiver_count"):
        blockers.append({"code": "WAIVERS_ABOVE_TRIVIAL_THRESHOLD",
                         "count": sad["invalid_waiver_count"]})
    # Above-trivial dispositions are proposals until a second person
    # concurs (AU-C 220). The count arrives on the sad dict from the
    # application layer, which knows who proposed and who concurred;
    # legacy sad dicts without the key are unaffected.
    if sad.get("concurrence_pending_count"):
        blockers.append({"code": "DISPOSITIONS_AWAITING_CONCURRENCE",
                         "count": sad["concurrence_pending_count"],
                         "items": list(sad.get("concurrence_pending", []))})

    unresolved_scope = 0
    limitations = 0
    for item in report.get("refusals", []):
        decision = engagement.get("scope", {}).get(scope_id(item), {})
        status = decision.get("status", "unresolved")
        unresolved_scope += status == "unresolved"
        limitations += status == "scope_limitation"
    if unresolved_scope:
        blockers.append({"code": "SCOPE_ITEMS_UNRESOLVED",
                         "count": unresolved_scope})

    completion = engagement.get("completion", {})
    incomplete_checks = [
        name for name in COMPLETION_CHECKS
        if not completion.get(name, {}).get("done", False)
    ]
    unsupported_checks = [
        name for name in COMPLETION_CHECKS
        if completion.get(name, {}).get("done", False)
        and not completion.get(name, {}).get("note")
        and not completion.get(name, {}).get("evidence")
    ]
    if incomplete_checks:
        blockers.append({"code": "COMPLETION_PROCEDURES_INCOMPLETE",
                         "count": len(incomplete_checks),
                         "items": incomplete_checks})
    if unsupported_checks:
        blockers.append({"code": "COMPLETION_EVIDENCE_MISSING",
                         "count": len(unsupported_checks),
                         "items": unsupported_checks})

    if trail_status is not None and not trail_status.get("ok", False):
        blockers.append({"code": "DECISION_TRAIL_BROKEN", "count": 1})

    ready = not blockers
    if not ready:
        implication = "not_ready"
    elif limitations:
        implication = "qualified_or_disclaimer_consideration"
    elif sad.get("conclusion") == "material":
        implication = "qualified_or_adverse_consideration"
    else:
        implication = "unmodified_opinion_candidate"

    return {
        "ready": ready,
        "status": "ready_for_auditor_evaluation" if ready else "not_ready",
        "report_implication": implication,
        "blockers": blockers,
        "risk_items": len(risk_ids),
        "control_items": len(control_ids),
        "procedure_items": len(procedure_coverage.get("procedures", [])),
        "review_sources": len(review_sources or []),
        "workpaper_locked": engagement.get("workpaper_lock", {}).get(
            "status") == "locked",
        "scope_items": len(report.get("refusals", [])),
        "scope_limitations": limitations,
        "completion_done": sum(
            1 for name in COMPLETION_CHECKS
            if completion.get(name, {}).get("done", False)),
        "completion_total": len(COMPLETION_CHECKS),
    }
