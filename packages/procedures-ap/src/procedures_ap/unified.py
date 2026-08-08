# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""One engagement, every layer, mapped to the traditional audit process.

Port of the prototype's connector: tags every receipt with cycle x assertion
x phase x class and organizes findings the way an auditor files an
engagement — planning, risk assessment, controls, substantive testing by
cycle, and completion — with scope limitations (refusals) first-class.

It adds no detection. Tags are an overlay keyed by receipt_id, never written
back into the evidence, so each finding's content-addressed seal is
preserved. Assertion tagging is a review aid, not an audit opinion.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from assurance_domain.receipts import Receipt

AUDIT_PHASES = (
    "risk_assessment",
    "controls",
    "substantive",
    "completion",
    "scope",
)

_STRUCTURAL_CLASSES = {"STRUCTURAL_ANOMALY", "EXPECTED_BUT_MISSING", "CONJECTURE"}


def _cycle_of(v: Receipt) -> str:
    pol, dom = v.policy, v.domain
    if pol.startswith("audit."):
        return pol.split(".", 1)[1]
    if pol.startswith("fs."):
        return "financial_statements"
    if pol.startswith("gl."):
        je = any(tok in pol for tok in ("je", "foots", "benford"))
        return "journal_entries" if je else "financial_statements"
    if pol.startswith("closure."):
        return "cash" if "bank" in pol else "financial_statements"
    if dom == "client_gl_structural":
        return "journal_entries"
    if pol.startswith(("rockwood.", "ap.", "acl.")) or dom in (
        "rockwood", "rockwood_structural", "ap_forensics", "rockwood_acl_baseline"
    ):
        return "payables"
    return "unassigned"


def _class_of(v: Receipt) -> str:
    """Normalize to {exception, risk, control, structural, coherence_pass, refusal}."""
    pol = v.policy
    fc = v.evidence.get("finding_class", "")
    kind = v.evidence.get("kind", "")
    check = v.evidence.get("check", "")
    reason = (v.reason or "").lower()

    if fc == "REFUSAL" or (pol.startswith("fs.") and v.verdict == "ORPHAN"):
        return "refusal"
    if fc == "COMPOSES" or v.verdict == "AGREE":
        return "coherence_pass"
    if check == "segregation_of_duties" or "creator and approver" in reason \
            or "created and approved by" in reason:
        return "control"
    if kind == "risk" or "benford" in pol or "je_risk" in pol \
            or "analytical" in pol or "risk" in v.evidence.get("policy", ""):
        return "risk"
    if fc in _STRUCTURAL_CLASSES or "structural" in pol \
            or v.domain.endswith("_structural"):
        return "structural"
    return "exception"


def _phase_of(cls: str, v: Receipt, cycle: str) -> str:
    if cls == "refusal":
        return "scope"
    if v.policy.startswith("fs.") or cycle == "financial_statements":
        return "completion"
    if cls == "risk":
        return "risk_assessment"
    if cls == "control":
        return "controls"
    return "substantive"


def _assertion_of(cls: str, v: Receipt) -> str:
    """Best-effort financial-statement assertion (a review aid, not an opinion)."""
    pol, key = v.policy, str(v.key).lower()
    reason = (v.reason or "").lower()
    fc = v.evidence.get("finding_class", "")
    if cls == "control":
        return "authorization"
    if cls == "risk":
        return "occurrence"
    if fc == "EXPECTED_BUT_MISSING" or "missing" in reason or "no observed" in reason:
        return "occurrence"
    if "twin" in key or "twin" in reason or "round_trip" in key or "cycle" in key \
            or "duplicate" in reason or "duplicate" in key:
        return "occurrence"
    if any(tok in pol for tok in ("overbill", "foots", "balance")) \
            or "amount" in reason or "differ" in reason:
        return "accuracy_valuation"
    return "unspecified"


def classify_verdict(v: Receipt) -> dict:
    """Tag a verdict with cycle x assertion x phase x class (non-mutating)."""
    cls = _class_of(v)
    cycle = _cycle_of(v)
    return {
        "cycle": cycle,
        "class": cls,
        "phase": _phase_of(cls, v, cycle),
        "assertion": _assertion_of(cls, v),
    }


@dataclass
class UnifiedReport:
    company: str
    fye: str
    tagged: list[dict] = field(default_factory=list)
    refusals: list[dict] = field(default_factory=list)
    research_ranking: dict | None = None
    procedure_coverage: dict | None = None

    def process_view(self) -> dict:
        """Phases (in order) -> cycle -> class -> [receipt_ids]."""
        view: dict[str, dict] = {phase: {} for phase in AUDIT_PHASES}
        for item in self.tagged:
            t = item["tags"]
            cyc = view[t["phase"]].setdefault(t["cycle"], {})
            cyc.setdefault(t["class"], []).append(item["receipt_id"])
        for ref in self.refusals:
            cyc = view["scope"].setdefault(ref.get("cycle", "unassigned"), {})
            cyc.setdefault("refusal", []).append(
                ref.get("procedure") or ref.get("check") or "refused")
        return {phase: cycles for phase, cycles in view.items() if cycles}

    def coverage(self) -> dict:
        """Per cycle: counts by class and which phases were touched."""
        cov: dict[str, dict] = {}
        for item in self.tagged:
            t = item["tags"]
            c = cov.setdefault(t["cycle"], {"classes": {}, "phases": set()})
            c["classes"][t["class"]] = c["classes"].get(t["class"], 0) + 1
            c["phases"].add(t["phase"])
        return {cyc: {"classes": c["classes"], "phases": sorted(c["phases"])}
                for cyc, c in cov.items()}

    def summary(self) -> dict:
        by_class: dict[str, int] = {}
        by_phase: dict[str, int] = {}
        for item in self.tagged:
            t = item["tags"]
            by_class[t["class"]] = by_class.get(t["class"], 0) + 1
            by_phase[t["phase"]] = by_phase.get(t["phase"], 0) + 1
        return {
            "verdicts": len(self.tagged),
            "refusals": len(self.refusals),
            "by_class": by_class,
            "by_phase": by_phase,
            "cycles": sorted({i["tags"]["cycle"] for i in self.tagged}),
        }

    def to_dict(self) -> dict:
        return {
            "company": self.company,
            "fye": self.fye,
            "summary": self.summary(),
            "process_view": self.process_view(),
            "coverage": self.coverage(),
            "verdicts": self.tagged,
            "refusals": self.refusals,
            "research_ranking": self.research_ranking,
            "procedure_coverage": self.procedure_coverage,
        }


def unify(verdicts: list[Receipt], refusals: list[dict] | None = None,
          company: str = "engagement", fye: str = "") -> UnifiedReport:
    """Tag and organize any set of verdicts into the audit-process shape."""
    tagged = [
        {"receipt_id": v.receipt_id, "tags": classify_verdict(v),
         "verdict": v.to_dict()}
        for v in verdicts
    ]
    return UnifiedReport(company, fye, tagged, list(refusals or ()))


def unified_ap_audit(tables: dict, company: str = "client",
                     fye: str = "") -> UnifiedReport:
    """Run the AP layers (referential + recovery + structural) into one report."""
    from procedures_ap.coverage import compile_coverage, inventory_from_tables
    from procedures_ap.ranking import rank_research_queue
    from procedures_ap.rockwood import ap_recovery, referential_integrity
    from procedures_ap.structural import run_structural_audit

    ri = referential_integrity(tables)
    ap = ap_recovery(tables)
    structural = run_structural_audit(tables)
    triage, fusion = structural["triage"], structural["fusion"]

    verdicts = (
        list(ri["findings"]) + list(ap["findings"]) + list(structural["findings"])
        + list(triage.research) + list(fusion.fused)
    )
    cleared = triage.cleared_receipt()
    if cleared is not None:
        verdicts.append(cleared)

    refusals = list(structural["refusals"]) + [
        {**r, "cycle": "payables"} for r in ap.get("checks_refused", [])
    ]
    report = unify(verdicts, refusals, company, fye)
    report.research_ranking = rank_research_queue(structural).to_dict()
    report.procedure_coverage = compile_coverage(inventory_from_tables(tables))
    return report
