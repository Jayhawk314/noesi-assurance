"""Two-batch structural triage over the whole disbursement population.

Composition logic sorts every payment into CLEARED (the PO -> voucher ->
payment composite closes and coheres) or RESEARCH (it does not close, or
closes but does not commute). The composition oracle is the owned
``CompositionIndex.reachable_from`` — the same multi-source BFS the prototype
bridge ran; no vendored runtime remains.

RESEARCH is a queue, not a verdict; CLEARED is "structurally coherent", not
"audited clean".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from assurance_domain.receipts import Receipt
from structural_adapters.graph import CompositionIndex, Edge

from procedures_ap.structural import (
    EvidenceRef, _id, _number, _records, _ref, content_hash,
)


def _coherence_issues(po: dict, voucher: dict, payment: dict,
                      amount_tolerance: float) -> list[str]:
    """Audit-owned check that the closed composite commutes (amounts/dates)."""
    reasons: list[str] = []
    ordered = _number(po.get("po_amount"))
    billed = _number(voucher.get("voucher_amount"))
    paid = _number(payment.get("payment_amount"))
    if billed not in (None, 0) and paid is not None:
        diff = abs(paid - billed) / abs(billed)
        if diff > amount_tolerance:
            reasons.append(f"payment vs voucher amount differs {diff:.1%}")
    if ordered not in (None, 0) and billed is not None:
        diff = abs(billed - ordered) / abs(ordered)
        if diff > amount_tolerance:
            reasons.append(f"voucher vs purchase-order amount differs {diff:.1%}")
    dates = [po.get("po_date"), voucher.get("voucher_date"),
             payment.get("payment_date")]
    observed = [d for d in dates if isinstance(d, date)]
    if observed != sorted(observed):
        reasons.append("dates do not follow PO -> voucher -> payment order")
    return reasons


@dataclass
class TriageResult:
    """The population split into two sealed batches by composition logic."""

    population: int
    cleared: list[dict] = field(default_factory=list)
    research: list[Receipt] = field(default_factory=list)
    refusals: list[dict] = field(default_factory=list)
    komposos_invoked: bool = False

    @property
    def cleared_seal(self) -> str:
        return content_hash(
            {"cleared": sorted(item["composition"] for item in self.cleared)})

    @property
    def batch_receipt(self) -> str:
        return content_hash({
            "population": self.population,
            "cleared": sorted(item["composition"] for item in self.cleared),
            "research": sorted(list(v.key) for v in self.research),
            "komposos_invoked": self.komposos_invoked,
        })

    @property
    def stats(self) -> dict:
        cleared, research = len(self.cleared), len(self.research)
        triaged = cleared + research
        return {
            "population": self.population,
            "cleared": cleared,
            "research": research,
            "research_pct": round(100 * research / self.population, 3)
            if self.population else 0.0,
            "coverage_pct": round(100 * triaged / self.population, 3)
            if self.population else 0.0,
            "komposos_invoked": self.komposos_invoked,
        }

    def cleared_receipt(self) -> Receipt | None:
        """One sealed AGREE receipt attesting the CLEARED batch as a whole."""
        if not self.cleared:
            return None
        return Receipt(
            domain="rockwood_structural",
            key=("triage_cleared_batch",),
            verdict="AGREE",
            policy="rockwood.structural_triage_v1",
            sources=("Purchase_orders", "Vouchers", "Payments"),
            score=float(len(self.cleared)),
            reason=(f"{len(self.cleared)} disbursement compositions close and "
                    "cohere (PO -> voucher -> payment composes; amounts and "
                    "dates commute)"),
            evidence={
                "finding_class": "COMPOSES",
                "mechanism": "komposos_categorical_composition_find_paths",
                "cleared_count": len(self.cleared),
                "cleared_seal": self.cleared_seal,
                "compositions": sorted(
                    item["composition"] for item in self.cleared),
                "limits": ("'Closes and coheres' is structural coherence, not "
                           "an audit opinion; it is not proof the disbursement "
                           "is proper."),
            })

    def to_dict(self) -> dict:
        cleared_receipt = self.cleared_receipt()
        return {
            "stats": self.stats,
            "batch_receipt": self.batch_receipt,
            "cleared_seal": self.cleared_seal,
            "cleared_batch_receipt": cleared_receipt.to_dict()
            if cleared_receipt else None,
            "research": [v.to_dict() for v in self.research],
            "refusals": self.refusals,
        }


def _research_verdict(finding_class: str, verdict: str, key: tuple,
                      reason: str, refs: list[EvidenceRef],
                      score: float | None, graph_path: list[str],
                      entity: str) -> Receipt:
    sources = tuple(dict.fromkeys(f"{r.table}:{r.row}" for r in refs))
    if verdict == "ORPHAN":
        sources = sources[-1:] or ("Payments",)
    elif len(sources) < 2:
        sources = sources + ("accounting_policy",)
    return Receipt(
        domain="rockwood_structural", key=key, verdict=verdict,
        policy="rockwood.structural_triage_v1", sources=sources,
        score=score, reason=reason,
        evidence={
            "finding_class": finding_class,
            "mechanism": "komposos_categorical_composition_find_paths",
            "entity": entity,
            "graph_path": graph_path,
            "source_rows": [r.to_dict() for r in refs],
            "limits": ("A composition that does not close or cohere is a "
                       "research item, not a proved exception or an allegation "
                       "of fraud."),
        })


def triage_disbursements(tables: dict, amount_tolerance: float = 0.02,
                         max_hops: int = 3) -> TriageResult:
    """Sort the disbursement population into CLEARED vs RESEARCH."""
    payments = _records(tables, "Payments")
    population = len(payments)

    ref_maps: dict[str, dict[str, EvidenceRef]] = {}
    for table, key in (("Purchase_orders", "po_number"),
                       ("Vouchers", "voucher_number"),
                       ("Payments", "payment_number")):
        ref_maps[table] = {
            str(row[key]): _ref(table, i, row, key)
            for i, row in enumerate(_records(tables, table), 1)
            if row.get(key)}

    pos = {str(r["po_number"]): r for r in _records(tables, "Purchase_orders")
           if r.get("po_number")}
    vouchers = {str(r["voucher_number"]): r
                for r in _records(tables, "Vouchers")
                if r.get("voucher_number")}

    result = TriageResult(population=population)
    category = CompositionIndex()
    result.komposos_invoked = True

    # Build the composition graph from *resolved* referential links only, so
    # a missing link is a missing morphism and reachability genuinely decides
    # whether the composite closes.
    for voucher_no, voucher in vouchers.items():
        po_no = str(voucher.get("po_number") or "")
        if po_no in pos:
            category.add_edge(Edge(
                _id("po", po_no), _id("voucher", voucher_no),
                "documented_by", 1.0, "rockwood"))
    for payment in payments:
        voucher_no = str(payment.get("voucher_number") or "")
        pnum = str(payment.get("payment_number") or "")
        if voucher_no in vouchers and pnum:
            category.add_edge(Edge(
                _id("voucher", voucher_no), _id("payment", pnum),
                "settled_by", 1.0, "rockwood"))

    po_nodes = {_id("po", n) for n in pos}
    closed = category.reachable_from(po_nodes, max_length=max_hops)

    for payment in payments:
        pnum = str(payment.get("payment_number") or "")
        payment_id = _id("payment", pnum)
        vendor_id = _id("vendor", payment.get("vendor_number") or "UNKNOWN")
        payment_ref = ref_maps["Payments"].get(pnum) or _ref(
            "Payments", 0, payment, "payment_number")
        voucher = vouchers.get(str(payment.get("voucher_number") or ""))
        po = pos.get(str(voucher.get("po_number") or "")) if voucher else None

        if voucher is None or po is None:
            missing = "voucher" if voucher is None else "purchase order"
            result.research.append(_research_verdict(
                "EXPECTED_BUT_MISSING", "ORPHAN",
                ("triage_disbursement", pnum),
                f"payment {pnum} references no observed {missing}; the "
                "PO -> voucher -> payment composite cannot close",
                [payment_ref],
                _number(payment.get("payment_amount")),
                [_id("po", po.get("po_number")) if po else "po:MISSING",
                 _id("voucher", voucher.get("voucher_number"))
                 if voucher else "voucher:MISSING",
                 payment_id],
                vendor_id))
            continue

        po_id = _id("po", str(po.get("po_number")))
        composite_weight = closed.get(payment_id)
        refs = [
            ref_maps["Purchase_orders"][str(po["po_number"])],
            ref_maps["Vouchers"][str(voucher["voucher_number"])],
            payment_ref,
        ]
        composition = f"{po['po_number']}->{voucher['voucher_number']}->{pnum}"
        if composite_weight is None:
            result.research.append(_research_verdict(
                "EXPECTED_BUT_MISSING", "ORPHAN",
                ("triage_disbursement", pnum),
                f"no categorical composite links {po_id} to {payment_id}",
                [payment_ref],
                _number(payment.get("payment_amount")),
                [po_id, _id("voucher", voucher["voucher_number"]), payment_id],
                vendor_id))
            continue

        reasons = _coherence_issues(po, voucher, payment, amount_tolerance)
        if reasons:
            result.research.append(_research_verdict(
                "STRUCTURAL_ANOMALY", "CLASH",
                ("triage_disbursement", pnum),
                "; ".join(reasons),
                refs,
                _number(payment.get("payment_amount")),
                [po_id, _id("voucher", voucher["voucher_number"]), payment_id],
                vendor_id))
            continue

        result.cleared.append({
            "composition": composition,
            "payment": pnum,
            "entity": vendor_id,
            "composite_confidence": round(float(composite_weight), 4),
            "source_rows": [r.to_dict() for r in refs],
        })

    return result
