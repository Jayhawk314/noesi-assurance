"""Whole-company referential integrity and AP recovery, ported from noesi-cpa.

The ACL binary reader is NOT ported — real clients export CSVs; the v2 input
boundary is parsed canonical tables (see the ``rockwood_tables.json.gz``
golden capture). Every join and check refuses explicitly when its tables or
key fields are absent.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from assurance_domain.receipts import Receipt

from procedures_ap.ap_checks import Record, duplicates, overbills, to_receipt


@dataclass(frozen=True)
class Join:
    """One foreign-key relationship the seam check enforces."""
    child: str
    child_key: str
    parent: str
    parent_key: str
    child_pk: str
    amount: str | None = None


# The referential-integrity seams the Rockwood-shaped schema supports.
JOINS = (
    Join("Invoices", "customer_number", "Customers", "customer_number", "invoice_number", "invoice_amount"),
    Join("Invoices", "so_number", "Sales_orders", "so_number", "invoice_number", "invoice_amount"),
    Join("Shipments", "customer_number", "Customers", "customer_number", "shipping_number", "items_shipped"),
    Join("Shipments", "so_number", "Sales_orders", "so_number", "shipping_number", "items_shipped"),
    Join("Sales_orders", "customer_number", "Customers", "customer_number", "so_number", "sales_order_amount"),
    Join("Payments", "vendor_number", "Vendors", "vendor_number", "payment_number", "payment_amount"),
    Join("Payments", "voucher_number", "Vouchers", "voucher_number", "payment_number", "payment_amount"),
    Join("Vouchers", "vendor_number", "Vendors", "vendor_number", "voucher_number", "voucher_amount"),
    Join("Vouchers", "po_number", "Purchase_orders", "po_number", "voucher_number", "voucher_amount"),
    Join("Purchase_orders", "vendor_number", "Vendors", "vendor_number", "po_number", "po_amount"),
    Join("Sales_orders_items", "inventory_number", "Inventory", "inventory_number", "so_number", "total_amount"),
    Join("Purchase_orders_items", "inventory_number", "Inventory", "inventory_number", "po_number", "unit_cost"),
    Join("Shipments_items", "inventory_number", "Inventory", "inventory_number", "shipping_number", "ship_quantity"),
    Join("Payroll_details", "employee_number", "Employees", "employee_number", "pay_period", "net_pay"),
)


def _score(x: object) -> float | None:
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    return round(abs(x), 2) if isfinite(x) else None


def orphan_verdicts(child_records: list[dict], parent_keys: set,
                    join: Join) -> list[Receipt]:
    """ORPHAN for every child row whose foreign key has no parent master."""
    out: list[Receipt] = []
    for r in child_records:
        fk = r.get(join.child_key)
        if fk is None or fk in parent_keys:
            continue
        out.append(Receipt(
            domain="rockwood",
            key=(f"{join.child}.{join.child_key}->{join.parent}",
                 r.get(join.child_pk) or "", fk),
            verdict="ORPHAN",
            policy="rockwood.referential_integrity_v1",
            sources=(join.child,),
            score=_score(r.get(join.amount)) if join.amount else None,
            reason=f"{join.child} {r.get(join.child_pk)} references "
                   f"{join.child_key}={fk} with no matching "
                   f"{join.parent}.{join.parent_key}",
            evidence={
                "child_table": join.child, "child_pk": r.get(join.child_pk),
                "foreign_key": join.child_key, "missing_value": fk,
                "parent_table": join.parent,
                "amount": r.get(join.amount) if join.amount else None,
                "parameters": {
                    "check": "referential_integrity",
                    "join": f"{join.child}.{join.child_key}->"
                            f"{join.parent}.{join.parent_key}",
                },
            }))
    return out


def referential_integrity(tables: dict) -> dict:
    """Run every supported join; refuse any whose table or key field is absent."""
    run, refused, findings = [], [], []
    for j in JOINS:
        child, parent = tables.get(j.child), tables.get(j.parent)
        if child is None or parent is None:
            refused.append({"join": f"{j.child}.{j.child_key}->{j.parent}",
                            "reason": "child or parent table not readable"})
            continue
        if j.child_key in child.refused_fields \
                or j.parent_key in parent.refused_fields:
            refused.append({"join": f"{j.child}.{j.child_key}->{j.parent}",
                            "reason": "key field is native-binary (refused by reader)"})
            continue
        parent_keys = {r[j.parent_key] for r in parent.records
                       if r.get(j.parent_key)}
        v = orphan_verdicts(list(child.records), parent_keys, j)
        run.append({"join": f"{j.child}.{j.child_key}->{j.parent}",
                    "child_rows": len(child.records), "orphans": len(v)})
        findings.extend(v)
    return {"joins_run": run, "joins_refused": refused, "findings": findings,
            "orphan_total": len(findings)}


def _payment_records(payments: list[dict]) -> tuple[list[Record], dict]:
    dated = [p for p in payments if hasattr(p.get("payment_date"), "toordinal")]
    origin = min((p["payment_date"] for p in dated), default=None)
    recs: list[Record] = []
    for i, p in enumerate(payments):
        amt, when = p.get("payment_amount"), p.get("payment_date")
        if not isinstance(amt, (int, float)) or amt <= 0:
            continue
        day = (when - origin).days if origin and hasattr(when, "toordinal") else 0
        recs.append(Record(id=i, vendor=p.get("vendor_number") or "",
                           invoice_no=p.get("voucher_number") or "",
                           amount=round(amt, 2), day=day))
    return recs, {"check": "duplicate_payment",
                  "key": "vendor+voucher_number+amount"}


def _voucher_po_records(vouchers: list[dict],
                        pos: list[dict]) -> tuple[list[Record], dict]:
    po_amt = {r["po_number"]: r.get("po_amount") for r in pos
              if r.get("po_number")}
    recs: list[Record] = []
    for i, v in enumerate(vouchers):
        amt = v.get("voucher_amount")
        pa = po_amt.get(v.get("po_number"))
        if not isinstance(amt, (int, float)) or not isinstance(pa, (int, float)):
            continue
        recs.append(Record(id=i, vendor=v.get("vendor_number") or "",
                           invoice_no=v.get("voucher_number") or "",
                           amount=round(amt, 2), day=0,
                           po_id=v.get("po_number"), po_amount=round(pa, 2)))
    return recs, {"check": "voucher_overbill",
                  "key": "voucher_amount vs po_amount"}


def _ap_verdict(finding, params: dict) -> Receipt:
    """Wrap one AP finding as a canonical receipt carrying its parameters."""
    v = to_receipt(finding)
    return Receipt(
        domain="rockwood", key=v.key, verdict=v.verdict, policy=v.policy,
        sources=v.sources, score=v.score, reason=v.reason,
        evidence={**v.evidence, "parameters": params})


def ap_recovery(tables: dict, *, overbill_tol: float = 0.02) -> dict:
    """Run the AP-recovery checks the corpus supports; refuse the rest."""
    payments = tables.get("Payments")
    vouchers = tables.get("Vouchers")
    pos = tables.get("Purchase_orders")
    ran, refused, findings = [], [], []

    if payments is not None:
        recs, params = _payment_records(list(payments.records))
        dup = duplicates(recs, canonical=True)
        findings += [_ap_verdict(f, params) for f in dup]
        ran.append({"check": "DUPLICATE (voucher-keyed)", "rows": len(recs),
                    "findings": len(dup)})
    else:
        refused.append({"check": "DUPLICATE",
                        "reason": "Payments table not readable"})

    if vouchers is not None and pos is not None:
        recs, params = _voucher_po_records(list(vouchers.records),
                                           list(pos.records))
        ob = overbills(recs, tol=overbill_tol)
        params = {**params, "overbill_tol": overbill_tol}
        findings += [_ap_verdict(f, params) for f in ob]
        ran.append({"check": "OVERBILL (voucher vs PO)", "rows": len(recs),
                    "findings": len(ob)})
    else:
        refused.append({"check": "OVERBILL",
                        "reason": "Vouchers or Purchase_orders not readable"})

    refused.append({"check": "SPLIT", "reason": "no payment-structuring threshold "
                    "in the corpus (Authorizations.limit is approval authority, not a split policy)"})
    refused.append({"check": "NO_PO / NO_RECEIPT",
                    "reason": "no PO or goods-receipt field on payments"})

    return {"checks_ran": ran, "checks_refused": refused, "findings": findings,
            "recovered": round(sum(v.score for v in findings
                                   if v.score is not None), 2)}
