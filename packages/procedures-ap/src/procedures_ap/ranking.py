"""Materiality-weighted ranking of the structural research queue.

An ordering overlay on findings already sealed — no new detector, no new
receipts. Exposure aggregates additively (dollars at risk); belief composes
multiplicatively (DS fused belief, or a discounted single-detector proxy);
risk = exposure x belief.

Divergence D6: the exposure fold is the owned additive implementation,
labelled ``additive_quantale`` (the prototype labelled the same fold
``komposos_additive_quantale`` after importing it from the vendored tree).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from procedures_ap.fusion import _PRIOR
from procedures_ap.structural import _jsonable

_VERDICT_DETECTOR = {"ORPHAN": "triage_orphan", "CLASH": "triage_clash"}

EXPOSURE_ALGEBRA = "additive_quantale"


def _fold_exposure(amounts: list[float]) -> tuple[float, str]:
    """Sum amounts through the additive quantale ([0, inf), +, 0)."""
    total = 0.0
    for a in amounts:
        total = total + a
    return round(total, 2), EXPOSURE_ALGEBRA


def _proxy_belief(verdicts: list[str]) -> float:
    """DS belief of a single reliability-discounted mass on {CONCERN}.

    Findings from the *same* detector are correlated, so take the max rather
    than inflating belief by pretending they are independent.
    """
    best = 0.0
    for verdict in verdicts:
        detector = _VERDICT_DETECTOR.get(verdict)
        if detector is None:
            continue
        concern, reliability = _PRIOR[detector]
        best = max(best, float(concern or 0.0) * float(reliability))
    return round(best, 4)


@dataclass
class RankedEntity:
    entity: str
    n_findings: int
    exposure: float
    belief: float
    belief_source: str          # "dempster_shafer" | "single_detector_proxy"
    risk_score: float           # exposure x belief — the ranking key
    verdicts: list[str]
    cleared_count: int
    receipt_ids: list[str]
    exposure_algebra: str
    individually_material: bool | None = None

    def to_dict(self) -> dict:
        return _jsonable(self.__dict__)


@dataclass
class RankingResult:
    ranked: list[RankedEntity] = field(default_factory=list)
    aggregate_exposure: float = 0.0
    materiality: float | None = None
    refusals: list[dict] = field(default_factory=list)

    @property
    def stats(self) -> dict:
        material = [r for r in self.ranked if r.individually_material]
        return {
            "entities": len(self.ranked),
            "aggregate_exposure": self.aggregate_exposure,
            "materiality": self.materiality,
            "individually_material": len(material) if self.materiality else None,
            "immaterial_in_isolation_aggregate": round(
                sum(r.exposure for r in self.ranked
                    if not r.individually_material), 2)
            if self.materiality else None,
        }

    def to_dict(self) -> dict:
        return {
            "stats": self.stats,
            "ranked": [r.to_dict() for r in self.ranked],
            "refusals": self.refusals,
        }


def rank_research_queue(structural_result: dict,
                        materiality: float | None = None) -> RankingResult:
    """Rank the research queue by believed dollars at risk."""
    result = RankingResult(materiality=materiality)
    triage = structural_result.get("triage")
    if triage is None:
        result.refusals.append({
            "finding_class": "REFUSAL",
            "procedure": "materiality_ranking",
            "reason": "no triage result to rank (structural engine did not run)",
        })
        return result

    fusion = structural_result.get("fusion")
    fused_belief = {pe["entity"]: pe["belief"]
                    for pe in getattr(fusion, "per_entity", []) or []}
    cleared_by_entity: dict[str, int] = {}
    for item in getattr(triage, "cleared", []) or []:
        entity = item.get("entity")
        if entity:
            cleared_by_entity[entity] = cleared_by_entity.get(entity, 0) + 1

    grouped: dict[str, list] = {}
    for verdict in getattr(triage, "research", []) or []:
        entity = verdict.evidence.get("entity")
        if entity:
            grouped.setdefault(entity, []).append(verdict)

    for entity, findings in grouped.items():
        amounts = [abs(float(v.score or 0.0)) for v in findings]
        exposure, algebra = _fold_exposure(amounts)
        verdicts = [v.verdict for v in findings]
        if entity in fused_belief:
            belief, source = fused_belief[entity], "dempster_shafer"
        else:
            belief, source = _proxy_belief(verdicts), "single_detector_proxy"
        result.ranked.append(RankedEntity(
            entity=entity,
            n_findings=len(findings),
            exposure=exposure,
            belief=belief,
            belief_source=source,
            risk_score=round(exposure * belief, 2),
            verdicts=verdicts,
            cleared_count=cleared_by_entity.get(entity, 0),
            receipt_ids=[v.receipt_id for v in findings],
            exposure_algebra=algebra,
            individually_material=(
                exposure >= materiality if materiality is not None else None),
        ))

    result.ranked.sort(key=lambda r: r.risk_score, reverse=True)
    result.aggregate_exposure = round(
        sum(r.exposure for r in result.ranked), 2)
    return result
