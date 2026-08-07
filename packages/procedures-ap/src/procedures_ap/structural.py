"""Structural coherence over evidential accounting graphs, ported from noesi-cpa.

The composition/twin/round-trip screening layer. Arithmetic stays float here
for receipt parity with the prototype (divergence D7): everything this module
emits is a lead or control observation routed to human review, never a SAD
candidate. Deterministic monetary procedures live in ``engines`` on Decimal.

The KOMPOSOS runtime dependency is gone: composition reachability and path
counts come from ``structural_adapters.graph`` (owned, audited port).
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from itertools import combinations
from typing import Iterable, Literal

from assurance_domain.receipts import Receipt
from structural_adapters.graph import CompositionIndex, Edge

FindingClass = Literal[
    "PROVED_EXCEPTION", "CONTROL_OBSERVATION", "STRUCTURAL_ANOMALY",
    "EXPECTED_BUT_MISSING", "CONJECTURE", "REFUSAL",
]

_LEGITIMATE_FLOWS = {
    "reversal", "correction", "intercompany", "intercompany_settlement",
    "shared_service_settlement",
}


def _jsonable(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def content_hash(record: dict) -> str:
    payload = json.dumps(
        _jsonable(record), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class EvidenceRef:
    table: str
    row: int
    record_id: str
    content_hash: str

    def to_dict(self) -> dict:
        return {"table": self.table, "row": self.row,
                "record_id": self.record_id, "content_hash": self.content_hash}


@dataclass(frozen=True)
class AccountingNode:
    id: str
    kind: str
    attributes: dict
    evidence: EvidenceRef


@dataclass(frozen=True)
class AccountingEdge:
    source: str
    target: str
    relation: str
    edge_kind: Literal["reference", "value_flow", "control"]
    amount: float | None = None
    occurred_on: date | None = None
    confidence: float = 1.0
    evidence: tuple[EvidenceRef, ...] = ()
    metadata: dict = field(default_factory=dict)


@dataclass
class AccountingGraph:
    """Graph that preserves parallel economic flows and their evidence."""

    nodes: dict[str, AccountingNode] = field(default_factory=dict)
    edges: list[AccountingEdge] = field(default_factory=list)

    def add_node(self, node: AccountingNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: AccountingEdge) -> None:
        self.edges.append(edge)


def _records(tables: dict, name: str) -> list[dict]:
    table = tables.get(name)
    return list(getattr(table, "records", table) or ()) if table is not None else []


def _number(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(float(value), 2)


def _id(kind: str, value: object) -> str:
    return f"{kind}:{value}"


def _ref(table: str, row: int, record: dict, key: str) -> EvidenceRef:
    return EvidenceRef(
        table, row, str(record.get(key) or f"row-{row}"), content_hash(record))


def _control_edges(graph: AccountingGraph, record: dict, document: str,
                   ref: EvidenceRef) -> None:
    for actor_field, relation in (("created_by", "created"),
                                  ("approved_by", "approved")):
        actor = record.get(actor_field)
        when = record.get(actor_field.replace("_by", "_on"))
        if actor:
            graph.add_edge(AccountingEdge(
                _id("employee", actor), document, relation, "control",
                occurred_on=when if isinstance(when, date) else None,
                evidence=(ref,)))


def build_rockwood_accounting_graph(tables: dict) -> AccountingGraph:
    """Map every AP row, not a sample, with reference/value separation."""
    graph = AccountingGraph()
    company_ref = EvidenceRef(
        "engagement", 0, "Rockwood", content_hash({"company": "Rockwood"}))
    graph.add_node(AccountingNode(
        "entity:Rockwood", "entity", {"name": "Rockwood"}, company_ref))

    specs = (
        ("Vendors", "vendor", "vendor_number"),
        ("Employees", "employee", "employee_number"),
        ("Purchase_orders", "po", "po_number"),
        ("Vouchers", "voucher", "voucher_number"),
        ("Payments", "payment", "payment_number"),
    )
    refs = {}
    for table, kind, key in specs:
        for row_no, record in enumerate(_records(tables, table), 1):
            value = record.get(key)
            if value in (None, ""):
                continue
            ref = _ref(table, row_no, record, key)
            refs[(table, str(value))] = ref
            graph.add_node(AccountingNode(
                _id(kind, value), kind, _jsonable(record), ref))

    for row_no, po in enumerate(_records(tables, "Purchase_orders"), 1):
        number = po.get("po_number")
        if not number:
            continue
        ref = refs.get(("Purchase_orders", str(number))) or _ref(
            "Purchase_orders", row_no, po, "po_number")
        graph.add_edge(AccountingEdge(
            _id("po", number), _id("vendor", po.get("vendor_number")),
            "ordered_from", "reference", _number(po.get("po_amount")),
            po.get("po_date") if isinstance(po.get("po_date"), date) else None,
            evidence=(ref,)))
        _control_edges(graph, po, _id("po", number), ref)

    for row_no, voucher in enumerate(_records(tables, "Vouchers"), 1):
        number = voucher.get("voucher_number")
        if not number:
            continue
        ref = refs.get(("Vouchers", str(number))) or _ref(
            "Vouchers", row_no, voucher, "voucher_number")
        node = _id("voucher", number)
        graph.add_edge(AccountingEdge(
            _id("po", voucher.get("po_number")), node, "documented_by",
            "reference", _number(voucher.get("voucher_amount")),
            voucher.get("voucher_date")
            if isinstance(voucher.get("voucher_date"), date) else None,
            evidence=(ref,)))
        graph.add_edge(AccountingEdge(
            node, _id("vendor", voucher.get("vendor_number")), "billed_by",
            "reference", _number(voucher.get("voucher_amount")),
            voucher.get("voucher_date")
            if isinstance(voucher.get("voucher_date"), date) else None,
            evidence=(ref,)))
        _control_edges(graph, voucher, node, ref)

    for row_no, payment in enumerate(_records(tables, "Payments"), 1):
        number = payment.get("payment_number")
        if not number:
            continue
        ref = refs.get(("Payments", str(number))) or _ref(
            "Payments", row_no, payment, "payment_number")
        node = _id("payment", number)
        graph.add_edge(AccountingEdge(
            _id("voucher", payment.get("voucher_number")), node, "settled_by",
            "reference", _number(payment.get("payment_amount")),
            payment.get("payment_date")
            if isinstance(payment.get("payment_date"), date) else None,
            evidence=(ref,)))
        graph.add_edge(AccountingEdge(
            "entity:Rockwood", _id("vendor", payment.get("vendor_number")),
            "cash_outflow", "value_flow", _number(payment.get("payment_amount")),
            payment.get("payment_date")
            if isinstance(payment.get("payment_date"), date) else None,
            evidence=(ref,),
            metadata={"payment_number": number}))
        _control_edges(graph, payment, node, ref)

    for row_no, flow in enumerate(_records(tables, "Value_flows"), 1):
        source = flow.get("source_entity")
        target = flow.get("target_entity")
        if not source or not target:
            continue
        ref = _ref("Value_flows", row_no, flow, "flow_id")
        for entity in (str(source), str(target)):
            entity_id = _id("entity", entity)
            if entity_id not in graph.nodes:
                graph.add_node(AccountingNode(
                    entity_id, "entity", {"name": entity}, ref))
        graph.add_edge(AccountingEdge(
            _id("entity", source), _id("entity", target),
            str(flow.get("relation") or "transfer"), "value_flow",
            _number(flow.get("amount")),
            flow.get("flow_date")
            if isinstance(flow.get("flow_date"), date) else None,
            evidence=(ref,),
            metadata={"flow_type": flow.get("flow_type", "")}))
    return graph


def _receipt(key: tuple, classification: FindingClass, sources: Iterable[str],
             score: float | None, reason: str, mechanism: str, evidence: dict,
             verdict: str = "TENSION", *,
             domain: str = "rockwood_structural",
             policy: str = "rockwood.structural_coherence_v1") -> Receipt:
    source_tuple = tuple(dict.fromkeys(sources))
    if verdict in {"AGREE", "TENSION", "CLASH"} and len(source_tuple) < 2:
        source_tuple += ("accounting_policy",)
    return Receipt(
        domain=domain, key=key, verdict=verdict,
        policy=policy, sources=source_tuple,
        score=score, reason=reason,
        evidence={"finding_class": classification, "mechanism": mechanism,
                  **_jsonable(evidence)})


_ROCKWOOD_GL_NOTE = ("Rockwood has no GL table; payment-to-GL coherence "
                     "is explicitly refused.")


def document_chain_findings(tables: dict, amount_tolerance: float = 0.02, *,
                            domain: str = "rockwood_structural",
                            policy: str = "rockwood.structural_coherence_v1",
                            gl_scope_note: str = _ROCKWOOD_GL_NOTE,
                            gl_path_node: str = "gl:UNAVAILABLE",
                            ) -> tuple[list[Receipt], dict]:
    """Cheap full-population AP triage; only nonzero-energy chains escalate."""
    pos = {str(row["po_number"]): row
           for row in _records(tables, "Purchase_orders") if row.get("po_number")}
    vouchers = {str(row["voucher_number"]): row
                for row in _records(tables, "Vouchers")
                if row.get("voucher_number")}
    ref_maps = {}
    for table, key in (("Purchase_orders", "po_number"),
                       ("Vouchers", "voucher_number"),
                       ("Payments", "payment_number")):
        ref_maps[table] = {
            str(row[key]): _ref(table, i, row, key)
            for i, row in enumerate(_records(tables, table), 1)
            if row.get(key)}

    findings = []
    control_findings = []
    payments = _records(tables, "Payments")
    approvals_observed = sum(
        1 for payment in payments
        if payment.get("created_by") and payment.get("approved_by"))
    self_approved = sum(
        1 for payment in payments
        if payment.get("created_by")
        and payment.get("created_by") == payment.get("approved_by"))
    self_approval_rate = self_approved / len(payments) if payments else 0.0
    # A pervasive failure is not discriminating row triage, but it is still a
    # control-level observation. One population conclusion, not thousands of
    # duplicate row flags.
    if approvals_observed and self_approved:
        control_findings.append(_receipt(
            ("control", "segregation_of_duties", "payment_approval"),
            "CONTROL_OBSERVATION",
            ("Payments", "control_policy"),
            None,
            (f"{self_approved:,} of {approvals_observed:,} payments with observed "
             f"creator/approver fields ({self_approved / approvals_observed:.1%}) "
             "were created and approved by the same actor"),
            "population_control_test",
            {"check": "segregation_of_duties",
             "control_objective": "payment creation and approval are separated",
             "population": len(payments),
             "approvals_observed": approvals_observed,
             "self_approved": self_approved,
             "self_approval_rate": round(self_approved / approvals_observed, 4),
             "limits": (
                 "This is an observed population exception rate. The auditor "
                 "must determine whether the fields represent real approval "
                 "events, whether compensating controls exist, and whether "
                 "control reliance is appropriate.")},
            domain=domain, policy=policy))
    self_approval_is_discriminating = 0 < self_approval_rate <= 0.10
    for payment in payments:
        voucher = vouchers.get(str(payment.get("voucher_number")))
        po = pos.get(str(voucher.get("po_number"))) if voucher else None
        energy, reasons = 0.0, []
        if voucher is None:
            energy, reasons = 1.0, ["payment references no observed voucher"]
        elif po is None:
            energy, reasons = 0.9, ["voucher references no observed purchase order"]

        if voucher:
            paid = _number(payment.get("payment_amount"))
            billed = _number(voucher.get("voucher_amount"))
            if paid is not None and billed not in (None, 0):
                difference = abs(paid - billed) / abs(billed)
                if difference > amount_tolerance:
                    energy += min(0.8, 0.4 + difference)
                    reasons.append(
                        f"payment/voucher amount difference {difference:.1%}")

        ordered_dates = [
            (po or {}).get("po_date"),
            (voucher or {}).get("voucher_date"),
            payment.get("payment_date"),
        ]
        observed_dates = [d for d in ordered_dates if isinstance(d, date)]
        if observed_dates != sorted(observed_dates):
            energy += 0.7
            reasons.append("dates do not follow PO -> voucher -> payment order")
        if (payment.get("created_by")
                and payment.get("created_by") == payment.get("approved_by")
                and self_approval_is_discriminating):
            energy += 0.5
            reasons.append("payment creator and approver are the same actor")
        if energy < 0.4:
            continue

        refs = []
        if po:
            refs.append(ref_maps["Purchase_orders"][str(po["po_number"])])
        if voucher:
            refs.append(ref_maps["Vouchers"][str(voucher["voucher_number"])])
        if payment.get("payment_number"):
            refs.append(ref_maps["Payments"][str(payment["payment_number"])])
        missing = voucher is None or po is None
        source_names = [f"{ref.table}:{ref.row}" for ref in refs]
        if missing:
            source_names = source_names[-1:] or ["Payments"]
        findings.append(_receipt(
            ("document_chain", str(payment.get("payment_number") or "unknown")),
            "EXPECTED_BUT_MISSING" if missing else "STRUCTURAL_ANOMALY",
            source_names,
            _number(payment.get("payment_amount")),
            "; ".join(reasons),
            "accounting_chain_energy",
            {"energy": round(min(1.0, energy), 3),
             "graph_path": [
                 _id("po", po.get("po_number")) if po else "po:MISSING",
                 _id("voucher", voucher.get("voucher_number"))
                 if voucher else "voucher:MISSING",
                 _id("payment", payment.get("payment_number")),
                 gl_path_node],
             "source_rows": [ref.to_dict() for ref in refs],
             "limits": gl_scope_note},
            "ORPHAN" if missing else "TENSION",
            domain=domain, policy=policy))

    population = len(payments)
    return control_findings + findings, {
        "population": population,
        "escalated": len(findings),
        "control_observations": len(control_findings),
        "self_approval_rate": round(self_approval_rate, 4),
        "self_approval_used_for_routing": self_approval_is_discriminating,
        "escalated_pct": round(100 * len(findings) / population, 3)
        if population else 0.0,
    }


def _vendor_profiles(tables: dict,
                     ) -> tuple[dict[str, set[str]], dict[str, list[EvidenceRef]]]:
    profiles, refs = defaultdict(set), defaultdict(list)
    for table, pk, amount_key, date_key in (
            ("Purchase_orders", "po_number", "po_amount", "po_date"),
            ("Vouchers", "voucher_number", "voucher_amount", "voucher_date"),
            ("Payments", "payment_number", "payment_amount", "payment_date")):
        for row_no, record in enumerate(_records(tables, table), 1):
            vendor = record.get("vendor_number")
            if not vendor:
                continue
            vendor = str(vendor)
            amount = _number(record.get(amount_key))
            when = record.get(date_key)
            profiles[vendor].add(f"kind:{table}")
            if amount is not None:
                profiles[vendor].add(f"amount:{amount:.2f}")
            if isinstance(when, date):
                profiles[vendor].add(f"month:{when.year:04d}-{when.month:02d}")
            for actor_key in ("created_by", "approved_by"):
                if record.get(actor_key):
                    profiles[vendor].add(f"{actor_key}:{record[actor_key]}")
            refs[vendor].append(_ref(table, row_no, record, pk))
    return profiles, refs


def relational_twin_findings(tables: dict, threshold: float = 0.9,
                             max_escalations: int = 500, *,
                             domain: str = "rockwood_structural",
                             policy: str = "rockwood.structural_coherence_v1",
                             ) -> tuple[list[Receipt], dict, list[dict]]:
    """Compare cheap candidates with audit-scoped Hom fingerprints."""
    profiles, refs = _vendor_profiles(tables)
    buckets = defaultdict(list)
    for vendor, features in profiles.items():
        amounts = sorted(f for f in features if f.startswith("amount:"))
        actors = sorted(f for f in features
                        if f.startswith(("created_by:", "approved_by:")))
        if amounts and actors and len(features) >= 4:
            buckets[content_hash(
                {"amounts": amounts, "actors": actors})].append(vendor)
    candidates = [
        pair for group in buckets.values() if len(group) > 1
        for pair in combinations(sorted(group), 2)]
    refusals = []
    selected = candidates[:max_escalations]
    if len(candidates) > max_escalations:
        refusals.append({
            "finding_class": "REFUSAL", "procedure": "relational_twins",
            "reason": (f"{len(candidates)} candidates exceed escalation cap "
                       f"{max_escalations}")})
    if not selected:
        return [], {"population": len(profiles), "candidates": 0,
                    "escalated": 0}, refusals

    # The prototype loaded the vendored KOMPOSOS category here; the owned
    # CompositionIndex answers the same feature-path evidence counts.
    role = "audit_role:vendor_profile"
    category = CompositionIndex()
    category.add_object(role)
    vendors = sorted({vendor for pair in selected for vendor in pair})
    for vendor in vendors:
        vendor_id = _id("vendor", vendor)
        category.add_object(vendor_id)
        for feature in sorted(profiles[vendor]):
            feature_id = f"feature:{feature}"
            category.add_edge(Edge(
                vendor_id, feature_id, "has_observed_role", 1.0, "rockwood"))
            category.add_edge(Edge(
                feature_id, role, "witnesses_vendor_role", 1.0, "rockwood"))

    findings = []
    for left, right in selected:
        left_features, right_features = profiles[left], profiles[right]
        similarity = len(left_features & right_features) / len(
            left_features | right_features)
        if similarity < threshold:
            continue
        left_paths = category.path_count(_id("vendor", left), role, max_length=2)
        right_paths = category.path_count(_id("vendor", right), role, max_length=2)
        source_refs = refs[left][:3] + refs[right][:3]
        findings.append(_receipt(
            ("relational_twins", left, right),
            "STRUCTURAL_ANOMALY",
            [f"{ref.table}:{ref.row}" for ref in source_refs],
            round(similarity, 4),
            (f"Vendors {left} and {right} have {similarity:.1%} overlap "
             "in observed amount, timing, document, and control roles"),
            "audit_yoneda_fingerprint_on_komposos_category",
            {"vendors": [left, right],
             "yoneda_style_similarity": round(similarity, 4),
             "shared_features": sorted(left_features & right_features),
             "left_feature_paths": left_paths,
             "right_feature_paths": right_paths,
             "source_rows": [ref.to_dict() for ref in source_refs],
             "limits": ("Structural equivalence is an alias indicator, not "
                        "proof of common ownership or fraud.")},
            domain=domain, policy=policy))
    return findings, {
        "population": len(profiles), "candidates": len(candidates),
        "escalated": len(selected), "findings": len(findings)}, refusals


def _edge_dict(edge: AccountingEdge) -> dict:
    return {
        "source": edge.source, "target": edge.target,
        "relation": edge.relation, "amount": edge.amount,
        "occurred_on": edge.occurred_on.isoformat()
        if edge.occurred_on else None,
        "source_rows": [ref.to_dict() for ref in edge.evidence],
        "metadata": _jsonable(edge.metadata),
    }


def directed_round_trip_findings(graph: AccountingGraph,
                                 amount_tolerance: float = 0.02,
                                 max_days: int = 30, max_hops: int = 4,
                                 ) -> tuple[list[Receipt], dict]:
    """Find amount/time-coherent directed cycles without calling them fraud."""
    flows = [edge for edge in graph.edges
             if edge.edge_kind == "value_flow" and edge.amount is not None]
    outgoing = defaultdict(list)
    for edge in flows:
        outgoing[edge.source].append(edge)
    cycles, suppressed = {}, 0

    def walk(start: str, current: str, path: list[AccountingEdge],
             seen: set[str]) -> None:
        nonlocal suppressed
        if len(path) >= max_hops:
            return
        for edge in outgoing.get(current, ()):
            if (path and edge.occurred_on and path[-1].occurred_on
                    and edge.occurred_on < path[-1].occurred_on):
                continue
            if edge.target == start and path:
                cycle = path + [edge]
                amounts = [item.amount for item in cycle]
                if max(amounts) - min(amounts) > (
                        amount_tolerance * max(amounts)):
                    continue
                dates = [item.occurred_on for item in cycle if item.occurred_on]
                if dates and (max(dates) - min(dates)).days > max_days:
                    continue
                if any(str(item.metadata.get("flow_type", "")).lower()
                       in _LEGITIMATE_FLOWS for item in cycle):
                    suppressed += 1
                    continue
                key = tuple(sorted(
                    (item.source, item.target, str(item.amount),
                     str(item.occurred_on))
                    for item in cycle))
                cycles[key] = cycle
            elif edge.target not in seen:
                walk(start, edge.target, path + [edge], seen | {edge.target})

    for source in outgoing:
        walk(source, source, [], {source})

    findings = []
    for index, cycle in enumerate(cycles.values(), 1):
        refs = [ref for edge in cycle for ref in edge.evidence]
        findings.append(_receipt(
            ("directed_round_trip", index, cycle[0].source),
            "STRUCTURAL_ANOMALY",
            [f"{ref.table}:{ref.row}" for ref in refs],
            round(min(edge.amount for edge in cycle), 2),
            (f"Directed value returned to {cycle[0].source} through "
             f"{len(cycle)} amount- and time-consistent transfers"),
            "directed_cycle+amount_temporal_coherence",
            {"graph_path": [_edge_dict(edge) for edge in cycle],
             "amount_tolerance": amount_tolerance,
             "max_days": max_days,
             "source_rows": [ref.to_dict() for ref in refs],
             "limits": ("A coherent round trip is not fraud; business purpose "
                        "and intercompany explanations require review.")}))
    return findings, {
        "flow_edges": len(flows), "cycles": len(findings),
        "legitimate_suppressed": suppressed}


def run_structural_audit(tables: dict, amount_tolerance: float = 0.02,
                         twin_threshold: float = 0.9) -> dict:
    from procedures_ap.engines import bank_gl_closure
    from procedures_ap.fusion import fuse_structural_findings
    from procedures_ap.triage import triage_disbursements

    graph = build_rockwood_accounting_graph(tables)
    triage = triage_disbursements(tables, amount_tolerance)
    chains, chain_route = document_chain_findings(tables, amount_tolerance)
    twins, twin_route, refusals = relational_twin_findings(
        tables, twin_threshold)
    cycles, cycle_stats = directed_round_trip_findings(graph, amount_tolerance)
    closure = bank_gl_closure(tables)
    refusals.extend(closure["refusals"])
    refusals.append({
        "finding_class": "REFUSAL",
        "procedure": "closed_population_round_trip_conclusion",
        "reason": ("AP outflows are observed but no counterparty-to-company "
                   "receipt flow")})
    result = {
        "graph": graph,
        "findings": chains + twins + cycles + closure["findings"],
        "refusals": refusals + triage.refusals,
        "routing": {"document_chains": chain_route,
                    "relational_twins": twin_route},
        "cycles": cycle_stats,
        "triage": triage,
        "closure": closure["stats"],
        "graph_stats": {"nodes": len(graph.nodes), "edges": len(graph.edges)},
    }
    fusion = fuse_structural_findings(result)
    result["fusion"] = fusion
    result["refusals"] = result["refusals"] + fusion.refusals
    return result
