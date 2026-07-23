"""AP-recovery detectors, ported from the prototype's noesis.ap package.

Screening-layer arithmetic stays float for receipt parity with the prototype
(divergence D7): these produce investigation leads, never SAD candidates
directly. ``canonical_invoice`` collapses formatting so ``INV-0045``,
``inv 45`` and ``INV000045`` share one identity while ``INV46`` stays
distinct.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from assurance_domain.receipts import Receipt

_NONALNUM = re.compile(r"[^0-9A-Za-z]")
_DIGITS = re.compile(r"\d+")

# A duplicate/split/overbill is a CLASH (records that cannot all be true);
# a missing PO or receipt is an ORPHAN (one observed side — investigate).
FINDING_VERDICT = {
    "DUPLICATE": "CLASH",
    "SPLIT": "CLASH",
    "OVERBILL": "CLASH",
    "NO_PO": "ORPHAN",
    "NO_RECEIPT": "ORPHAN",
}


@dataclass(frozen=True)
class Record:
    id: int
    vendor: str
    invoice_no: str
    amount: float
    day: int
    po_id: str | None = None
    po_amount: float | None = None
    received: bool = True


@dataclass(frozen=True)
class Finding:
    kind: str
    record_ids: tuple[int, ...]
    amount_at_risk: float
    detail: str = ""


def canonical_invoice(raw: str) -> str:
    """Collapse formatting so reformatted duplicates share one identity."""
    stripped = _NONALNUM.sub("", raw).upper()
    return _DIGITS.sub(lambda m: str(int(m.group())), stripped)


def duplicates(records: list[Record], *, canonical: bool = True) -> list[Finding]:
    """Same vendor + same invoice identity + same amount, paid more than once."""
    groups: dict[tuple, list[Record]] = defaultdict(list)
    for r in records:
        inv = canonical_invoice(r.invoice_no) if canonical else r.invoice_no
        groups[(r.vendor, inv, round(r.amount, 2))].append(r)
    out: list[Finding] = []
    for group in groups.values():
        if len(group) < 2:
            continue
        ids = tuple(r.id for r in group)
        extra = group[0].amount * (len(group) - 1)
        how = "reformatted or re-keyed" if canonical else "exact re-key"
        out.append(Finding("DUPLICATE", ids, round(extra, 2), how))
    return out


def overbills(records: list[Record], *, tol: float = 0.02) -> list[Finding]:
    """Invoice paid above its purchase order beyond tolerance."""
    out: list[Finding] = []
    for r in records:
        if r.po_amount is not None and r.amount > r.po_amount * (1 + tol):
            out.append(Finding("OVERBILL", (r.id,),
                               round(r.amount - r.po_amount, 2), "over PO"))
    return out


def to_receipt(finding: Finding) -> Receipt:
    """Map one AP finding into the canonical receipt envelope."""
    verdict = FINDING_VERDICT[finding.kind]
    if finding.kind == "OVERBILL":
        rid = finding.record_ids[0]
        sources = (f"invoice:{rid}", f"po:{rid}")
    elif verdict == "ORPHAN":
        sources = (f"invoice:{finding.record_ids[0]}",)
    else:
        sources = tuple(f"record:{rid}" for rid in finding.record_ids)
    return Receipt(
        domain="ap_recovery",
        key=(finding.kind, *finding.record_ids),
        verdict=verdict,
        policy=f"ap.{finding.kind.lower()}_v1",
        sources=sources,
        score=round(finding.amount_at_risk, 2),
        reason=finding.detail,
        evidence={
            "record_ids": list(finding.record_ids),
            "amount_at_risk": round(finding.amount_at_risk, 2),
        },
    )
