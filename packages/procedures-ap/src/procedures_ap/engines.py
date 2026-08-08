# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Deterministic AP procedure engines, ported from noesi-cpa on Decimal money.

Arithmetic is Decimal end to end; floats appear only at the receipt
serialization boundary (``fnum``) so v2 receipts stay bit-compatible with the
float-era goldens. The Phase 2 shadow tests assert receipt_id equality
against the Phase 0 bundles.

``forensic.closed_value_flow`` runs on the ported structural layer
(``procedures_ap.structural`` + ``structural_adapters``) — the vendored
KOMPOSOS dependency is gone (divergence D2, resolved).
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from decimal import Decimal
from difflib import SequenceMatcher
from itertools import combinations
from typing import Callable

from assurance_domain.money import fnum, parse_amount, sum_amounts
from assurance_domain.receipts import Receipt

from procedures_ap.structural import content_hash  # date-aware, legacy-parity

ENGINE_VERSION = "noesi-procedures-ap-v2"

_TOLERANCE = Decimal("0.02")
_CENT = Decimal("0.01")


def _records(tables: dict, role: str) -> list[dict]:
    table = tables.get(role)
    return list(getattr(table, "records", table) or ()) if table is not None else []


def _run_verdict(procedure_id: str, key: tuple, verdict: str, reason: str,
                 evidence: dict, score: Decimal | None = None) -> Receipt:
    sources = (("approved_evidence",) if verdict == "ORPHAN"
               else ("approved_evidence", "procedure_contract"))
    return Receipt(
        domain="audit_procedure_run", key=(procedure_id, *key), verdict=verdict,
        policy=f"{procedure_id}.v1", sources=sources,
        score=fnum(score), reason=reason, evidence=evidence)


def _source_ref(table: str, row: int, record: dict, key: str) -> dict:
    return {"table": table, "row": row,
            "record_id": str(record.get(key) or f"row-{row}"),
            "content_hash": content_hash(record)}


def _period(value) -> str | None:
    if isinstance(value, date):
        return f"{value.year:04d}-{value.month:02d}"
    if isinstance(value, str) and len(value) >= 7:
        try:
            return _period(date.fromisoformat(value[:10]))
        except ValueError:
            return None
    return None


def three_way_receipt_match(tables: dict) -> tuple[list[Receipt], dict]:
    receipts_by_po = defaultdict(list)
    for row in _records(tables, "Goods_receipts"):
        receipts_by_po[str(row.get("po_number") or "")].append(row)
    findings = []
    vouchers = _records(tables, "Vouchers")
    for voucher in vouchers:
        vnum = str(voucher.get("voucher_number") or "")
        po = str(voucher.get("po_number") or "")
        matched = receipts_by_po.get(po, [])
        billed = parse_amount(voucher.get("voucher_amount"))
        received = sum_amounts(parse_amount(r.get("received_amount"))
                               for r in matched)
        if not matched:
            findings.append(_run_verdict(
                "ap.three_way_receipt_match", (vnum,), "ORPHAN",
                f"voucher {vnum} references PO {po} with no observed goods receipt",
                {"finding_class": "EXPECTED_BUT_MISSING", "cycle": "payables",
                 "voucher_number": vnum, "po_number": po,
                 "source_hash": voucher.get("source_hash"),
                 "limits": "absence may be timing, services, or an incomplete receiving export"},
                billed))
        elif billed is not None and received + max(_CENT, _TOLERANCE * abs(billed)) < billed:
            findings.append(_run_verdict(
                "ap.three_way_receipt_match", (vnum,), "CLASH",
                f"voucher {vnum} amount {fnum(billed)} exceeds observed receipts {fnum(received)}",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "payables",
                 "voucher_number": vnum, "po_number": po,
                 "voucher_amount": fnum(billed), "received_amount": fnum(received),
                 "limits": "quantity, service, partial-delivery and unit-of-measure terms require review"},
                billed - received))
    return findings, {"population": len(vouchers), "exceptions": len(findings)}


def subledger_gl_balance_tie(tables: dict) -> tuple[list[Receipt], dict]:
    rows = _records(tables, "AP_control_balance")
    findings = []
    for index, row in enumerate(rows, 1):
        subledger = parse_amount(row.get("subledger_balance"))
        gl = parse_amount(row.get("gl_balance"))
        if subledger is None or gl is None:
            continue
        difference = subledger - gl
        if abs(difference) > _CENT:
            findings.append(_run_verdict(
                "ap.subledger_gl_balance_tie",
                (str(row.get("period_end") or index),), "CLASH",
                f"AP subledger {fnum(subledger)} does not tie to GL control {fnum(gl)}",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "financial_statements",
                 "subledger_balance": fnum(subledger), "gl_balance": fnum(gl),
                 "difference": fnum(difference), "source_hash": row.get("source_hash")},
                abs(difference)))
    return findings, {"population": len(rows), "exceptions": len(findings)}


def _day(value) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and len(value) >= 10:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def split_payment_review(tables: dict, threshold,
                         window_days=0) -> tuple[list[Receipt], dict]:
    """Sub-threshold payment clusters per vendor.

    ``window_days`` is an explicit audit parameter (policy
    ``split_window_days``): 0 keeps the original same-day grouping the Phase 0
    goldens froze; N > 0 clusters payments whose dates span at most N days,
    because structuring rarely lands on one day. The tool never picks a
    window silently — a same-day-only run is documented in the summary.
    """
    threshold = parse_amount(threshold)
    if threshold is None or threshold <= 0:
        raise ValueError("split_threshold must be a positive number")
    try:
        window_days = int(str(window_days or 0).strip() or 0)
        if window_days < 0:
            raise ValueError
    except ValueError:
        raise ValueError(
            "split_window_days must be zero or a positive integer") from None

    payments = _records(tables, "Payments")
    findings = []

    def flag(vendor: str, rows: list[dict], first: str, last: str) -> None:
        total = sum_amounts(parse_amount(r.get("payment_amount"))
                            for r in rows)
        if len(rows) <= 1 or total < threshold:
            return
        ids = [str(row.get("payment_number") or "") for row in rows]
        when = (f"on {first}" if first == last
                else f"between {first} and {last}")
        key = first if first == last else f"{first}..{last}"
        evidence = {"finding_class": "STRUCTURAL_ANOMALY", "cycle": "payables",
                    "payment_numbers": ids, "total": fnum(total),
                    "threshold": fnum(threshold),
                    "limits": "a cluster is a review lead; business purpose "
                              "and approval evidence decide it"}
        if window_days:
            evidence["window_days"] = window_days
        findings.append(_run_verdict(
            "ap.split_payment_review", (vendor, key), "TENSION",
            f"{len(rows)} payments to vendor {vendor} {when} total "
            f"{fnum(total)} around threshold {fnum(threshold)}",
            evidence, total))

    if window_days == 0:
        groups = defaultdict(list)
        for row in payments:
            amount = parse_amount(row.get("payment_amount"))
            if amount is not None and 0 < amount < threshold:
                groups[(str(row.get("vendor_number") or ""),
                        str(row.get("payment_date") or ""))].append(row)
        for (vendor, day), rows in groups.items():
            flag(vendor, rows, day, day)
    else:
        by_vendor: dict[str, list[tuple[date, dict]]] = defaultdict(list)
        for row in payments:
            amount = parse_amount(row.get("payment_amount"))
            day = _day(row.get("payment_date"))
            if amount is not None and 0 < amount < threshold and day:
                by_vendor[str(row.get("vendor_number") or "")].append(
                    (day, row))
        for vendor, dated in by_vendor.items():
            dated.sort(key=lambda item: (
                item[0], str(item[1].get("payment_number") or "")))
            cluster: list[tuple[date, dict]] = []
            for day, row in dated:
                if cluster and (day - cluster[0][0]).days > window_days:
                    flag(vendor, [r for _, r in cluster],
                         str(cluster[0][0]), str(cluster[-1][0]))
                    cluster = []
                cluster.append((day, row))
            if cluster:
                flag(vendor, [r for _, r in cluster],
                     str(cluster[0][0]), str(cluster[-1][0]))

    summary = {"population": len(payments), "exceptions": len(findings),
               "threshold": fnum(threshold)}
    if window_days:
        summary["window_days"] = window_days
    return findings, summary


def payment_voucher_reference(tables: dict) -> tuple[list[Receipt], dict]:
    vouchers = {str(row.get("voucher_number") or "")
                for row in _records(tables, "Vouchers")} - {""}
    payments = _records(tables, "Payments")
    findings = []
    for payment in payments:
        pnum = str(payment.get("payment_number") or "")
        vnum = str(payment.get("voucher_number") or "")
        if vnum in vouchers:
            continue
        reason = (f"payment {pnum} records no voucher reference" if not vnum
                  else f"payment {pnum} cites voucher {vnum}, which is absent "
                       "from the voucher population")
        findings.append(_run_verdict(
            "ap.payment_voucher_reference", (pnum,), "ORPHAN", reason,
            {"finding_class": "EXPECTED_BUT_MISSING", "cycle": "payables",
             "payment_number": pnum, "voucher_number": vnum or None,
             "source_hash": payment.get("source_hash"),
             "limits": "what absence proves depends on the completeness of "
                       "the voucher export; a period boundary or a partial "
                       "extract can explain a missing reference"},
            parse_amount(payment.get("payment_amount"))))
    return findings, {"population": len(payments), "exceptions": len(findings)}


def voucher_po_reference(tables: dict) -> tuple[list[Receipt], dict]:
    pos = {str(row.get("po_number") or "")
           for row in _records(tables, "Purchase_orders")} - {""}
    vouchers = _records(tables, "Vouchers")
    findings = []
    without_reference = 0
    for voucher in vouchers:
        vnum = str(voucher.get("voucher_number") or "")
        po = str(voucher.get("po_number") or "")
        if not po:
            # Non-PO spend (utilities, rent, services) is a population fact,
            # not a row exception; it is reported in the summary instead.
            without_reference += 1
            continue
        if po in pos:
            continue
        findings.append(_run_verdict(
            "ap.voucher_po_reference", (vnum,), "ORPHAN",
            f"voucher {vnum} cites purchase order {po}, which is absent "
            "from the purchase-order population",
            {"finding_class": "EXPECTED_BUT_MISSING", "cycle": "payables",
             "voucher_number": vnum, "po_number": po,
             "source_hash": voucher.get("source_hash"),
             "limits": "an unreachable PO may be a keying error, an "
                       "incomplete PO export, or unauthorized purchasing; "
                       "which one is the auditor's determination"},
            parse_amount(voucher.get("voucher_amount"))))
    return findings, {"population": len(vouchers),
                      "without_po_reference": without_reference,
                      "exceptions": len(findings)}


def segregation_of_duties(tables: dict) -> tuple[list[Receipt], dict]:
    payments = _records(tables, "Payments")
    findings = []
    observed = self_approved = 0
    for payment in payments:
        pnum = str(payment.get("payment_number") or "")
        creator = str(payment.get("created_by") or "").strip()
        approver = str(payment.get("approved_by") or "").strip()
        amount = parse_amount(payment.get("payment_amount"))
        if not creator or not approver:
            missing = "creator" if not creator else "approver"
            findings.append(_run_verdict(
                "ap.segregation_of_duties", (pnum,), "ORPHAN",
                f"payment {pnum} has no observed {missing}",
                {"finding_class": "EXPECTED_BUT_MISSING", "cycle": "payables",
                 "check": "segregation_of_duties", "payment_number": pnum,
                 "created_by": creator or None, "approved_by": approver or None,
                 "source_hash": payment.get("source_hash"),
                 "limits": "a blank workflow field is an evidence gap, not a "
                           "proved control failure"},
                amount))
            continue
        observed += 1
        if creator == approver:
            self_approved += 1
            findings.append(_run_verdict(
                "ap.segregation_of_duties", (pnum,), "CLASH",
                f"payment {pnum} was created and approved by the same "
                f"actor {creator}",
                {"finding_class": "CONTROL_OBSERVATION", "cycle": "payables",
                 "check": "segregation_of_duties", "payment_number": pnum,
                 "created_by": creator, "approved_by": approver,
                 "source_hash": payment.get("source_hash"),
                 "limits": "field semantics and compensating controls require "
                           "auditor evaluation before concluding the control "
                           "failed"},
                amount))
    return findings, {"population": len(payments),
                      "approvals_observed": observed,
                      "self_approved": self_approved,
                      "exceptions": len(findings)}


_NAME_NOISE = frozenset({
    "llc", "llp", "lp", "inc", "incorporated", "co", "corp", "corporation",
    "company", "ltd", "limited", "the",
})
_NAME_SIMILARITY = 0.85


def _identity_key(name: str) -> str:
    text = re.sub(r"[^a-z0-9 ]+", " ", name.lower().replace("&", " and "))
    return " ".join(t for t in text.split() if t not in _NAME_NOISE)


def vendor_relational_twins(tables: dict) -> tuple[list[Receipt], dict]:
    """Identity twins from the vendor master; relationship twins from activity."""
    from procedures_ap.structural import relational_twin_findings

    vendors = [row for row in _records(tables, "Vendors")
               if row.get("vendor_number")]
    profiles = [(str(row["vendor_number"]),
                 str(row.get("vendor_name") or ""),
                 _identity_key(str(row.get("vendor_name") or "")))
                for row in vendors]
    findings = []
    for (num_a, name_a, key_a), (num_b, name_b, key_b) in combinations(
            profiles, 2):
        if not key_a or not key_b:
            continue
        matcher = SequenceMatcher(None, key_a, key_b)
        if (matcher.real_quick_ratio() < _NAME_SIMILARITY
                or matcher.quick_ratio() < _NAME_SIMILARITY):
            continue
        similarity = matcher.ratio()
        if similarity < _NAME_SIMILARITY:
            continue
        findings.append(_run_verdict(
            "ap.vendor_relational_twins", ("identity", num_a, num_b),
            "TENSION",
            f"vendors {num_a} and {num_b} have near-identical observed "
            f"identities {name_a!r} and {name_b!r}",
            {"finding_class": "STRUCTURAL_ANOMALY", "cycle": "payables",
             "vendors": [num_a, num_b], "vendor_names": [name_a, name_b],
             "name_similarity": round(similarity, 4),
             "limits": "a structural twin is an investigation lead, not "
                       "proof of duplication or fraud"},
            Decimal(str(round(similarity, 4)))))
    relationship, twin_stats, refusals = relational_twin_findings(
        tables, domain="audit_procedure_run",
        policy="ap.vendor_relational_twins.v1")
    combined = findings + relationship
    stats = {"population": len(vendors),
             "identity_pairs": len(findings),
             "relationship_candidates": twin_stats.get("candidates", 0),
             "relationship_findings": len(relationship),
             "exceptions": len(combined)}
    if refusals:
        stats["refusals"] = refusals
    return combined, stats


def document_chain(tables: dict) -> tuple[list[Receipt], dict]:
    from procedures_ap.structural import document_chain_findings
    findings, stats = document_chain_findings(
        tables, float(_TOLERANCE), domain="audit_procedure_run",
        policy="ap.document_chain.v1",
        gl_scope_note="GL posting coherence is tested by gl.payment_posting, "
                      "not by this procedure.",
        gl_path_node="gl:OUT_OF_SCOPE")
    return findings, {**stats, "exceptions": len(findings)}


def _closure_verdict(key, verdict, policy, sources, score: Decimal | None,
                     reason, finding_class, evidence, cycle) -> Receipt:
    return Receipt(
        domain="rockwood_closure", key=key, verdict=verdict, policy=policy,
        sources=sources, score=fnum(score), reason=reason,
        evidence={"finding_class": finding_class, "cycle": cycle, **evidence})


def bank_gl_closure(tables: dict, *,
                    amount_tolerance: Decimal = _TOLERANCE) -> dict:
    """Reconcile payment -> bank and payment -> GL where the data supports it."""
    payments = _records(tables, "Payments")
    bank = _records(tables, "Bank")
    gl = _records(tables, "GL")
    has_bank, has_gl = bool(bank), bool(gl)

    findings: list[Receipt] = []
    refusals: list[dict] = []
    if not has_bank:
        refusals.append({"finding_class": "REFUSAL", "procedure": "bank_clearing",
                         "reason": "no bank / cash-disbursements feed provided; "
                                   "payment-to-bank clearing cannot be tested",
                         "cycle": "cash"})
    if not has_gl:
        refusals.append({"finding_class": "REFUSAL", "procedure": "gl_posting",
                         "reason": "no general-ledger file provided; payment-to-GL "
                                   "posting and period cannot be tested",
                         "cycle": "financial_statements"})
    # The subledger-to-GL balance tie needs AP-control account balances, not
    # the flow data here; refuse rather than fake it.
    refusals.append({"finding_class": "REFUSAL",
                     "procedure": "subledger_gl_balance_tie",
                     "reason": "AP subledger-to-GL control-account balance tie "
                               "needs period-end control balances, not supplied",
                     "cycle": "financial_statements"})

    bank_by_payment: dict[str, tuple[int, dict]] = {}
    for idx, b in enumerate(bank, 1):
        pn = str(b.get("payment_number") or "")
        if pn:
            bank_by_payment[pn] = (idx, b)
    gl_by_ref: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    for idx, row in enumerate(gl, 1):
        ref = str(row.get("reference") or "")
        if ref:
            gl_by_ref[ref].append((idx, row))

    bank_matched = gl_matched = clearing_exceptions = posting_exceptions = 0
    for i, payment in enumerate(payments, 1):
        pnum = str(payment.get("payment_number") or "")
        if not pnum:
            continue
        paid = parse_amount(payment.get("payment_amount"), quantize=True)
        vnum = str(payment.get("voucher_number") or "")
        pay_ref = _source_ref("Payments", i, payment, "payment_number")

        if has_bank:
            match = bank_by_payment.get(pnum)
            if match is None:
                clearing_exceptions += 1
                findings.append(_closure_verdict(
                    ("bank_clearing", pnum), "ORPHAN", "closure.bank_clearing_v1",
                    (f"Payments:{i}",), paid,
                    f"payment {pnum} does not appear in the bank feed — not cleared",
                    "EXPECTED_BUT_MISSING",
                    {"graph_path": [f"payment:{pnum}", "bank:MISSING"],
                     "source_rows": [pay_ref],
                     "limits": "a payment absent from the bank feed may be uncleared, "
                               "timing, or a data gap — it requires review, not an "
                               "allegation."}, "cash"))
            else:
                bank_matched += 1
                bidx, b = match
                bank_amt = parse_amount(b.get("amount"), quantize=True)
                if paid is not None and bank_amt not in (None, 0) and (
                        abs(paid - bank_amt) / abs(bank_amt) > amount_tolerance):
                    clearing_exceptions += 1
                    findings.append(_closure_verdict(
                        ("bank_clearing", pnum), "CLASH", "closure.bank_clearing_v1",
                        (f"Payments:{i}", "Bank"), paid,
                        f"payment {pnum} {fnum(paid)} does not match bank {fnum(bank_amt)}",
                        "PROVED_EXCEPTION",
                        {"payment_amount": fnum(paid), "bank_amount": fnum(bank_amt),
                         "source_rows": [pay_ref, _source_ref("Bank", bidx, b, "bank_txn_id")],
                         "limits": "an amount difference between payment and bank is a "
                                   "reconciliation exception to investigate."}, "cash"))

        if has_gl:
            entries = gl_by_ref.get(pnum) or gl_by_ref.get(vnum)
            if not entries:
                posting_exceptions += 1
                findings.append(_closure_verdict(
                    ("gl_posting", pnum), "ORPHAN", "closure.gl_posting_v1",
                    (f"Payments:{i}",), paid,
                    f"payment {pnum} is not posted to the general ledger",
                    "EXPECTED_BUT_MISSING",
                    {"graph_path": [f"payment:{pnum}", "gl:MISSING"],
                     "source_rows": [pay_ref],
                     "limits": "a payment with no GL posting is an evidence gap to "
                               "resolve, not a proved misstatement."},
                    "financial_statements"))
                continue
            gidx, gentry = entries[0]
            gref = _source_ref("GL", gidx, gentry, "gl_entry_id")
            g_period = _period(gentry.get("gl_date"))
            p_period = _period(payment.get("payment_date"))
            gl_amounts = [parse_amount(e.get("amount"), quantize=True)
                          for _, e in entries]
            if g_period and p_period and g_period != p_period:
                posting_exceptions += 1
                findings.append(_closure_verdict(
                    ("gl_period", pnum), "CLASH", "closure.gl_period_v1",
                    (f"Payments:{i}", "GL"), paid,
                    f"payment {pnum} paid in {p_period} but posted to GL in {g_period}",
                    "PROVED_EXCEPTION",
                    {"payment_period": p_period, "gl_period": g_period,
                     "source_rows": [pay_ref, gref],
                     "limits": "a period difference is a cutoff exception to review."},
                    "financial_statements"))
            elif paid is not None and not any(
                    amount is not None
                    and abs(abs(amount) - paid) <= max(_CENT, amount_tolerance * paid)
                    for amount in gl_amounts):
                posting_exceptions += 1
                findings.append(_closure_verdict(
                    ("gl_amount", pnum), "CLASH", "closure.gl_posting_v1",
                    (f"Payments:{i}", "GL"), paid,
                    f"payment {pnum} {fnum(paid)} has no GL line matching the amount",
                    "PROVED_EXCEPTION",
                    {"payment_amount": fnum(paid),
                     "gl_amounts": [fnum(amount) for amount in gl_amounts],
                     "source_rows": [pay_ref, gref],
                     "limits": "a GL posting whose amount does not tie to the payment "
                               "is a reconciliation exception."},
                    "financial_statements"))
            else:
                gl_matched += 1

    orphan_bank = 0
    if has_bank:
        recorded = {str(p.get("payment_number")) for p in payments}
        for j, b in enumerate(bank, 1):
            bpn = str(b.get("payment_number") or "")
            if bpn and bpn not in recorded:
                orphan_bank += 1
                findings.append(_closure_verdict(
                    ("bank_unrecorded", bpn or f"row-{j}"), "ORPHAN",
                    "closure.bank_unrecorded_v1", ("Bank",),
                    parse_amount(b.get("amount"), quantize=True),
                    f"bank disbursement {bpn} has no recorded payment",
                    "EXPECTED_BUT_MISSING",
                    {"graph_path": [f"bank:{bpn}", "payment:MISSING"],
                     "source_rows": [_source_ref("Bank", j, b, "bank_txn_id")],
                     "limits": "an outflow with no recorded payment is a completeness "
                               "concern to investigate."}, "cash"))

    population = len(payments)
    stats = {
        "population": population,
        "bank_present": has_bank, "gl_present": has_gl,
        "bank_matched": bank_matched, "gl_matched": gl_matched,
        "clearing_exceptions": clearing_exceptions,
        "posting_exceptions": posting_exceptions,
        "unrecorded_bank_outflows": orphan_bank,
        "closed_to_gl_pct": round(100 * gl_matched / population, 3)
        if population and has_gl else None,
    }
    return {"findings": findings, "stats": stats, "refusals": refusals}


def _closure_slice(prefix: str):
    def run(tables: dict, policies: dict) -> tuple[list[Receipt], dict]:
        result = bank_gl_closure(tables)
        findings = [item for item in result["findings"]
                    if item.policy.startswith(prefix)]
        return findings, {**result["stats"], "exceptions": len(findings)}
    return run


def _closed_value_flow(tables: dict, policies: dict) -> tuple[list[Receipt], dict]:
    from procedures_ap.structural import (
        build_rockwood_accounting_graph,
        directed_round_trip_findings,
    )
    findings, stats = directed_round_trip_findings(
        build_rockwood_accounting_graph(tables), 0.02)
    return findings, {"population": len(_records(tables, "Value_flows")),
                      "exceptions": len(findings), **stats}


# The single source of truth for what this build can actually run. Coverage
# compilation reconciles contracts against this registry: a contract with no
# entry here reports "unsupported", never "executable".
EXECUTORS: dict[str, Callable[[dict, dict], tuple[list[Receipt], dict]]] = {
    "cash.bank_clearing": _closure_slice("closure.bank"),
    "gl.payment_posting": _closure_slice("closure.gl"),
    "ap.three_way_receipt_match": lambda tables, policies:
        three_way_receipt_match(tables),
    "ap.subledger_gl_balance_tie": lambda tables, policies:
        subledger_gl_balance_tie(tables),
    "ap.split_payment_review": lambda tables, policies:
        split_payment_review(tables, policies.get("split_threshold"),
                             policies.get("split_window_days") or 0),
    "forensic.closed_value_flow": _closed_value_flow,
    "ap.payment_voucher_reference": lambda tables, policies:
        payment_voucher_reference(tables),
    "ap.voucher_po_reference": lambda tables, policies:
        voucher_po_reference(tables),
    "ap.segregation_of_duties": lambda tables, policies:
        segregation_of_duties(tables),
    "ap.vendor_relational_twins": lambda tables, policies:
        vendor_relational_twins(tables),
    "ap.document_chain": lambda tables, policies: document_chain(tables),
}


def registered_procedures() -> frozenset[str]:
    return frozenset(EXECUTORS)


def execute_procedure(procedure_id: str, tables: dict,
                      policies: dict | None = None) -> tuple[list[Receipt], dict]:
    """Execute one registered procedure over canonical tables."""
    executor = EXECUTORS.get(procedure_id)
    if executor is None:
        raise ValueError("no incremental executor is registered for this procedure")
    return executor(tables, policies or {})
