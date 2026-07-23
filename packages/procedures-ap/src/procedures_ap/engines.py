"""Deterministic AP procedure engines, ported from noesi-cpa on Decimal money.

Arithmetic is Decimal end to end; floats appear only at the receipt
serialization boundary (``fnum``) so v2 receipts stay bit-compatible with the
float-era goldens. The Phase 2 shadow tests assert receipt_id equality
against the Phase 0 bundles.

``forensic.closed_value_flow`` is deferred: its round-trip engine depends on
the vendored KOMPOSOS structural code, which ships later as an explicitly
owned adapter (divergence D2). It refuses rather than pretends.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from assurance_domain.money import fnum, parse_amount, sum_amounts
from assurance_domain.receipts import Receipt, content_hash

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


def split_payment_review(tables: dict, threshold) -> tuple[list[Receipt], dict]:
    threshold = parse_amount(threshold)
    if threshold is None or threshold <= 0:
        raise ValueError("split_threshold must be a positive number")
    groups = defaultdict(list)
    payments = _records(tables, "Payments")
    for row in payments:
        amount = parse_amount(row.get("payment_amount"))
        if amount is not None and 0 < amount < threshold:
            groups[(str(row.get("vendor_number") or ""),
                    str(row.get("payment_date") or ""))].append(row)
    findings = []
    for (vendor, day), rows in groups.items():
        total = sum_amounts(parse_amount(r.get("payment_amount")) for r in rows)
        if len(rows) > 1 and total >= threshold:
            ids = [str(row.get("payment_number") or "") for row in rows]
            findings.append(_run_verdict(
                "ap.split_payment_review", (vendor, day), "TENSION",
                f"{len(rows)} payments to vendor {vendor} on {day} total "
                f"{fnum(total)} around threshold {fnum(threshold)}",
                {"finding_class": "STRUCTURAL_ANOMALY", "cycle": "payables",
                 "payment_numbers": ids, "total": fnum(total),
                 "threshold": fnum(threshold),
                 "limits": "a cluster is a review lead; business purpose and approval evidence decide it"},
                total))
    return findings, {"population": len(payments), "exceptions": len(findings),
                      "threshold": fnum(threshold)}


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


def execute_procedure(procedure_id: str, tables: dict,
                      policies: dict | None = None) -> tuple[list[Receipt], dict]:
    """Execute one registered procedure over canonical tables."""
    policies = policies or {}
    if procedure_id in ("cash.bank_clearing", "gl.payment_posting"):
        result = bank_gl_closure(tables)
        prefix = "closure.bank" if procedure_id == "cash.bank_clearing" else "closure.gl"
        findings = [item for item in result["findings"]
                    if item.policy.startswith(prefix)]
        return findings, {**result["stats"], "exceptions": len(findings)}
    if procedure_id == "ap.three_way_receipt_match":
        return three_way_receipt_match(tables)
    if procedure_id == "ap.subledger_gl_balance_tie":
        return subledger_gl_balance_tie(tables)
    if procedure_id == "ap.split_payment_review":
        return split_payment_review(tables, policies.get("split_threshold"))
    if procedure_id == "forensic.closed_value_flow":
        raise ValueError(
            "forensic.closed_value_flow requires the structural adapter, "
            "which is not yet ported; the procedure is refused, not faked")
    raise ValueError("no incremental executor is registered for this procedure")
