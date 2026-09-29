# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""A draft of the auditor's opinion, with its basis — never the opinion.

The engine gathers what the engagement holds and proposes the opinion the
standards point to; every judgment it cannot make (whether an effect is
pervasive, whether substantial doubt exists) is returned as a decision the
partner must record. The proposal follows the standards' ladder:

- required written representations not provided -> disclaimer (AU-C 580);
- a scope limitation still open -> qualified or disclaimer (AU-C 705),
  pervasiveness judged by the partner;
- uncorrected misstatements above materiality -> qualified or adverse
  (AU-C 705), pervasiveness judged by the partner;
- otherwise -> unmodified (AU-C 700);
- going-concern indicators -> the partner's conclusion must be recorded
  before any opinion; substantial doubt adds a going-concern section
  (AU-C 570), it does not by itself modify the opinion.

Misstatements: the auditor's summary of uncorrected misstatements (signed,
projected, by statement line) is used when it has been run; otherwise the
SAD built from findings. The source is always named, so the two summaries
cannot disagree silently.
"""

from __future__ import annotations

from decimal import Decimal

_OPEN = ("undisposed", "follow_up")


def _open(finding: dict) -> bool:
    return (finding.get("disposition") or {}).get("status", "undisposed") in _OPEN


def draft_opinion(*, readiness: dict, sad: dict, findings: list[dict],
                  misstatement_run: dict | None, materiality: float,
                  completion: dict) -> dict:
    reasons, decisions = [], []
    m = Decimal(str(materiality or 0))

    # --- written representations (AU-C 580)
    reps = [f for f in findings if f["procedure_id"] == "completion.representation_letter"
            and f["verdict"]["verdict"] == "CLASH" and _open(f)]
    # A missing representation is not the same as a letter problem (dating,
    # signature): the first points to a disclaimer, the second must be
    # corrected before the report is dated (Kestrel parts 2-3, C1).
    missing_reps = sorted({str(f["verdict"]["key"][1]) for f in reps
                           if str(f["verdict"]["key"][-1]) == "not_obtained"})
    letter_issues = sorted({str(f["verdict"]["key"][-1]) for f in reps
                            if str(f["verdict"]["key"][1]) == "letter"})
    if letter_issues:
        decisions.append({"decision": "correct_the_representation_letter",
                          "why": f"the letter has: {', '.join(letter_issues)}; it must "
                                 "be signed and dated as of the report date"})

    # --- scope limitations: refusals nobody has resolved
    refusals = [f for f in findings if _open(f) and
                (f["verdict"].get("evidence") or {}).get("finding_class") == "REFUSAL"]

    # --- uncorrected misstatements: one figure, with its source named
    if misstatement_run is not None:
        totals = (misstatement_run.get("summary") or {}).get("totals") or {}
        lines = {k: abs(Decimal(str(v))) for k, v in totals.items()
                 if k not in ("identified", "likely") and v not in (None, "")}
        largest_line, largest = max(lines.items(), key=lambda kv: kv[1],
                                    default=("", Decimal("0")))
        misstatement = {"source": "summary of uncorrected misstatements "
                                  "(completion.uncorrected_misstatements)",
                        "largest_line": largest_line, "amount": str(largest)}
    else:
        largest = Decimal(str(sad.get("total_unadjusted") or 0))
        misstatement = {"source": "SAD from dispositioned findings (no summary of "
                                  "uncorrected misstatements has been run)",
                        "largest_line": "total", "amount": str(largest)}
    # At materiality counts as material, as the completion procedure itself
    # judges it (final review F3).
    material = bool(m) and largest >= m

    # --- going concern (AU-C 570)
    indicators = sorted({str(f["verdict"]["key"][1]) for f in findings
                         if f["procedure_id"] == "completion.going_concern_indicators"
                         and f["verdict"]["verdict"] == "TENSION"})
    # A breached loan covenant is itself a going-concern indicator (AU-C 570):
    # the debt may be due on demand (Kestrel parts 2-3, C3).
    indicators += sorted({f"covenant_breached: {f['verdict']['key'][1]}" for f in findings
                          if f["procedure_id"] == "debt.covenants"
                          and f["verdict"]["verdict"] == "CLASH" and _open(f)})
    gc_check = completion.get("going_concern") or {}
    gc_concluded = bool(gc_check.get("done")) and bool(gc_check.get("note"))
    if indicators and not gc_concluded:
        decisions.append({
            "decision": "going_concern_conclusion",
            "why": f"indicators present ({', '.join(indicators)}); record whether "
                   "substantial doubt exists (completion check 'going_concern', with "
                   "a note) before an opinion"})

    # --- the proposal: every cause of modification is evaluated, none hides
    # another (final review F2); missing representations still lead.
    if refusals:
        reasons.append(f"{len(refusals)} scope limitation(s) still open: work the "
                       "engine could not perform on the evidence given")
        decisions.append({"decision": "pervasiveness_of_scope_limitation",
                          "why": "qualified if the possible effects are material but "
                                 "not pervasive, disclaimer if pervasive (AU-C 705)"})
    if material:
        reasons.append(f"uncorrected misstatements of {largest} on "
                       f"{misstatement['largest_line']} reach materiality {m}")
        decisions.append({"decision": "pervasiveness_of_misstatement",
                          "why": "qualified if material but not pervasive, adverse if "
                                 "pervasive (AU-C 705)"})
    if missing_reps:
        proposal = "disclaimer"
        reasons.insert(0, f"required written representations not provided: "
                          f"{', '.join(missing_reps)} (AU-C 580 requires a disclaimer "
                          "or withdrawal)")
    elif refusals and material:
        proposal = "qualified_adverse_or_disclaimer"
    elif refusals:
        proposal = "qualified_or_disclaimer"
    elif material:
        proposal = "qualified_or_adverse"
    else:
        proposal = "unmodified"
        reasons.append(f"uncorrected misstatements ({largest}) are below materiality "
                       f"({m}); no open scope limitation; representations obtained")
    if indicators and gc_concluded:
        reasons.append("going-concern conclusion recorded: "
                       f"{gc_check.get('note')}; if substantial doubt exists, the report "
                       "adds a going-concern section (AU-C 570)")

    ready = bool(readiness.get("ready")) and not decisions
    return {
        "status": "draft_for_partner" if ready else "not_ready",
        "proposed_opinion": proposal,
        "basis": reasons,
        "decisions_required": decisions,
        "readiness_blockers": readiness.get("blockers", []),
        "misstatements": misstatement,
        "materiality": str(m),
        "open_scope_limitations": len(refusals),
        "missing_representations": missing_reps,
        "going_concern_indicators": indicators,
        "note": "A draft for the engagement partner. The opinion, and every "
                "judgment listed under decisions_required, is the partner's.",
    }
