# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Dempster-Shafer fusion of structural detectors, per entity.

Adding detector scores would be the exact antipattern the product warns
against — "multiple heuristics convert a conjecture into an exception".
Dempster's rule instead combines reliability-discounted belief masses into a
belief/plausibility interval and a conflict degree; high conflict surfaces as
AMBIGUOUS, and fusion is capped so it can never emit a proved exception.

The math is the owned ``structural_adapters.dempster_shafer`` port (was:
vendored KOMPOSOS through sys.path). Operation order matches the prototype
so fused receipts hash identically.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from assurance_domain.receipts import Receipt
from structural_adapters.dempster_shafer import MassFunction, combine, discount

from procedures_ap.structural import _jsonable

_CONCERN = frozenset({"CONCERN"})
_BENIGN = frozenset({"BENIGN"})
_FRAME = frozenset({"CONCERN", "BENIGN"})

# Per-detector prior: (concern_mass or None -> use the finding's own score,
# reliability discount). Deliberately conservative and documented, not tuned.
_PRIOR: dict[str, tuple[float | None, float]] = {
    "relational_twins": (None, 0.5),
    "directed_round_trip": (0.7, 0.6),
    "triage_orphan": (0.85, 0.9),
    "triage_clash": (0.7, 0.85),
}

_CONFLICT_AMBIGUOUS = 0.10


@dataclass(frozen=True)
class DetectorSignal:
    """One detector's evidence about one entity."""

    detector: str
    entity: str
    concern_mass: float
    reliability: float
    finding_key: tuple
    receipt_id: str
    reason: str
    polarity: str = "concern"  # "concern" | "benign"


def collect_signals(structural_result: dict) -> list[DetectorSignal]:
    """Map structural findings to per-entity detector signals.

    The chain signal comes from triage (sealed, composition-based) and NOT
    also from document_chain findings — they observe the same broken chains,
    and fusing both would double-count correlated evidence.
    """
    signals: list[DetectorSignal] = []

    for finding in structural_result.get("findings", []):
        ev = finding.evidence
        mechanism = ev.get("mechanism", "")
        if mechanism == "audit_yoneda_fingerprint_on_komposos_category":
            concern, rel = _PRIOR["relational_twins"]
            score = float(finding.score or 0.0)
            for vendor in ev.get("vendors", []):
                signals.append(DetectorSignal(
                    "relational_twins", _vendor_id(vendor),
                    score, rel, finding.key, finding.receipt_id,
                    f"relational twin (similarity {score:.2f})"))
        elif mechanism.startswith("directed_cycle"):
            concern, rel = _PRIOR["directed_round_trip"]
            for entity in _cycle_entities(ev.get("graph_path", [])):
                signals.append(DetectorSignal(
                    "directed_round_trip", entity, concern, rel,
                    finding.key, finding.receipt_id,
                    "value returns through an amount/time-coherent cycle"))

    triage = structural_result.get("triage")
    for finding in getattr(triage, "research", []) if triage else []:
        ev = finding.evidence
        entity = ev.get("entity")
        if not entity:
            continue
        which = "triage_orphan" if finding.verdict == "ORPHAN" else "triage_clash"
        concern, rel = _PRIOR[which]
        signals.append(DetectorSignal(
            which, entity, concern, rel, finding.key, finding.receipt_id,
            finding.reason))

    # Exculpatory (benign) evidence: an entity whose *other* disbursements
    # compose cleanly — this is what lets fusion register conflict.
    cleared_by_entity: dict[str, int] = {}
    for item in getattr(triage, "cleared", []) if triage else []:
        entity = item.get("entity")
        if entity:
            cleared_by_entity[entity] = cleared_by_entity.get(entity, 0) + 1
    for entity, count in cleared_by_entity.items():
        benign_mass = min(0.6, 0.2 + 0.02 * count)
        signals.append(DetectorSignal(
            "cleared_coherence", entity, benign_mass, 0.5,
            ("triage_cleared", entity), "",
            f"{count} disbursement(s) compose and cohere cleanly",
            polarity="benign"))

    return signals


def _vendor_id(vendor: str) -> str:
    return vendor if str(vendor).startswith("vendor:") else f"vendor:{vendor}"


def _cycle_entities(graph_path: list) -> list[str]:
    entities: list[str] = []
    for edge in graph_path:
        for role in ("source", "target"):
            value = edge.get(role) if isinstance(edge, dict) else None
            if isinstance(value, str) and value.startswith("entity:"):
                entities.append(value)
    return list(dict.fromkeys(entities))


def _fuse_one(entity: str, signals: list[DetectorSignal]) -> dict:
    """Combine one entity's signals via Dempster's rule; report conflict."""
    masses = []
    for sig in signals:
        focal = _CONCERN if sig.polarity == "concern" else _BENIGN
        m = MassFunction(masses={
            focal: sig.concern_mass, _FRAME: 1.0 - sig.concern_mass})
        masses.append(discount(m, sig.reliability))

    fused = masses[0]
    conflicts: list[float] = []
    for m in masses[1:]:
        fused, k = combine(fused, m)
        conflicts.append(k)

    bel = fused.belief(_CONCERN)
    pl = fused.plausibility(_CONCERN)
    max_conflict = max(conflicts) if conflicts else 0.0
    return {
        "entity": entity,
        "belief": round(bel, 4),
        "plausibility": round(pl, 4),
        "uncertainty": round(pl - bel, 4),
        "max_conflict": round(max_conflict, 4),
        "pignistic": round(fused.pignistic_probability("CONCERN"), 4),
    }


def _fused_verdict(scores: dict, signals: list[DetectorSignal]) -> Receipt:
    detectors = sorted({s.detector for s in signals})
    high_conflict = scores["max_conflict"] >= _CONFLICT_AMBIGUOUS
    if scores["belief"] >= 0.5:
        verdict, finding_class = "TENSION", "STRUCTURAL_ANOMALY"
        context = (
            f"; contradicting clean-history context present "
            f"(conflict {scores['max_conflict']:.2f})" if high_conflict else "")
        reason = (
            f"{len(detectors)} structural detectors corroborate a concern about "
            f"{scores['entity']} (belief {scores['belief']:.2f}, plausibility "
            f"{scores['plausibility']:.2f}){context}")
    elif high_conflict:
        verdict, finding_class = "AMBIGUOUS", "CONJECTURE"
        reason = (
            f"{len(detectors)} detectors implicate {scores['entity']} but "
            f"materially disagree (conflict {scores['max_conflict']:.2f}) with no "
            f"decisive belief (belief {scores['belief']:.2f}); inconclusive")
    else:
        verdict, finding_class = "TENSION", "CONJECTURE"
        reason = (
            f"{len(detectors)} detectors weakly implicate {scores['entity']} "
            f"(belief {scores['belief']:.2f}); combined evidence is suggestive, "
            "not sufficient")
    return Receipt(
        domain="rockwood_structural",
        key=("fused_entity", scores["entity"]),
        verdict=verdict,
        policy="rockwood.structural_fusion_v1",
        sources=tuple(detectors),
        score=scores["belief"],
        reason=reason,
        evidence={
            "finding_class": finding_class,
            "mechanism": "komposos_dempster_shafer_combine",
            "entity": scores["entity"],
            "belief": scores["belief"],
            "plausibility": scores["plausibility"],
            "uncertainty": scores["uncertainty"],
            "conflict": scores["max_conflict"],
            "pignistic_concern": scores["pignistic"],
            "contributing_detectors": [
                {"detector": s.detector, "reliability": s.reliability,
                 "reason": s.reason, "finding_key": list(s.finding_key),
                 "receipt_id": s.receipt_id}
                for s in signals
            ],
            "limits": (
                "Dempster-Shafer fusion combines structural indicators into a "
                "belief interval; it is capped at STRUCTURAL_ANOMALY and can "
                "never emit a proved exception. Detectors are treated as "
                "independent, which is an approximation."),
        })


@dataclass
class FusionResult:
    fused: list[Receipt] = field(default_factory=list)
    refusals: list[dict] = field(default_factory=list)
    per_entity: list[dict] = field(default_factory=list)
    komposos_invoked: bool = False

    @property
    def stats(self) -> dict:
        return {
            "entities_fused": len(self.fused),
            "ambiguous": sum(1 for v in self.fused if v.verdict == "AMBIGUOUS"),
            "komposos_invoked": self.komposos_invoked,
        }

    def to_dict(self) -> dict:
        return {
            "stats": self.stats,
            "fused": [v.to_dict() for v in self.fused],
            "per_entity": _jsonable(self.per_entity),
            "refusals": self.refusals,
        }


def fuse_structural_findings(structural_result: dict) -> FusionResult:
    """Fuse per-entity evidence from >=2 distinct detectors."""
    result = FusionResult()
    signals = collect_signals(structural_result)

    by_entity: dict[str, list[DetectorSignal]] = {}
    for sig in signals:
        by_entity.setdefault(sig.entity, []).append(sig)
    multi = {entity: sigs for entity, sigs in by_entity.items()
             if len({s.detector for s in sigs}) >= 2}
    if not multi:
        return result

    result.komposos_invoked = True
    for entity in sorted(multi):
        sigs = multi[entity]
        scores = _fuse_one(entity, sigs)
        result.per_entity.append(scores)
        result.fused.append(_fused_verdict(scores, sigs))
    return result
