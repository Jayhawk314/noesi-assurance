# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Summary of Audit Differences: the auditor's judgment aggregated.

Port of the prototype's disposition/SAD semantics on Decimal arithmetic
(floats only at the fnum boundary). Finding identity prefers an explicit
engagement-scoped ``finding_uid`` (v2); the legacy ``engagement|domain|key``
composition survives only as a migration fallback so shadow tests and
imported rows keep their identities.

Honest limits (unchanged from the prototype, per the assessment's P2): the
SAD aggregates magnitudes; it does not yet bifurcate income-statement vs
balance-sheet effect, over/understatement direction, or sampling projection.
It is an AP pilot summary until methodology review expands it.
"""

from __future__ import annotations

from decimal import Decimal

from assurance_domain.money import fnum, parse_amount

STATUSES = ("undisposed", "cleared", "unadjusted", "adjusted", "waived", "follow_up")

TRIVIAL_PCT = Decimal("0.05")      # clearly-trivial threshold = 5% of materiality
PERFORMANCE_PCT = Decimal("0.75")  # performance materiality = 75% of materiality

_CENT = Decimal("0.01")


def finding_id(row: dict) -> str:
    """Stable identity a disposition sticks to across re-runs.

    Prefers the engagement-scoped ``finding_uid``; falls back to the legacy
    composition for migrated rows.
    """
    uid = row.get("finding_uid")
    if uid:
        return str(uid)
    return f"{row['engagement']}|{row['domain']}|{row['key']}"


def apply_dispositions(rows: list[dict], dispositions: dict) -> list[dict]:
    """Attach each finding's recorded disposition (and note) to its row."""
    for row in rows:
        record = dispositions.get(finding_id(row), {})
        row["disposition"] = record.get("status", "undisposed")
        row["note"] = record.get("note", "")
    return rows


def _is_candidate(row: dict) -> bool:
    """Only factual dollar exceptions belong on the SAD.

    An ORPHAN often means missing evidence, not a booked misstatement.
    """
    if not isinstance(row.get("score"), (int, float)) \
            or isinstance(row.get("score"), bool):
        return False
    evidence = row.get("evidence", {}) or {}
    audit_class = row.get("audit_class")
    if audit_class:
        return (audit_class == "exception"
                and row.get("verdict") in ("CLASH", "ORPHAN"))
    finding_class = evidence.get("finding_class")
    if finding_class:
        return finding_class == "PROVED_EXCEPTION"
    kind = evidence.get("kind")
    if kind:
        return kind == "exception"
    return row.get("verdict") == "CLASH"


def _quantized(value: Decimal) -> Decimal:
    return value.quantize(_CENT)


def requires_concurrence(row: dict, clearly_trivial) -> bool:
    """Does this finding's disposition need a second person's concurrence?

    A disposed factual dollar exception above the clearly-trivial threshold
    is a significant judgment (AU-C 220): the disposition is a proposal
    until someone other than the proposer concurs. Below the threshold —
    or for findings with no dollar magnitude — a single judgment stands,
    exactly as clearly-trivial items stay off the SAD.
    """
    if not _is_candidate(row):
        return False
    ctt = parse_amount(clearly_trivial) or Decimal("0")
    magnitude = abs(parse_amount(row.get("score")) or Decimal("0"))
    return magnitude > ctt


def summary_of_differences(rows: list[dict], *, materiality) -> dict:
    """Aggregate unadjusted misstatements and conclude against materiality."""
    overall = parse_amount(materiality) or Decimal("0")
    ctt = _quantized(TRIVIAL_PCT * overall) if overall else Decimal("0")
    performance = _quantized(PERFORMANCE_PCT * overall) if overall else None

    def lines_for(status: str) -> list[dict]:
        # One SAD line per misstatement (finding id); rows sharing an id sum.
        groups: dict[str, dict] = {}
        for row in rows:
            if not (_is_candidate(row) and row.get("disposition") == status):
                continue
            fid = finding_id(row)
            group = groups.setdefault(fid, {
                "finding_id": fid, "engagement": row["engagement"],
                "account": (row.get("evidence", {}) or {}).get(
                    "account", row["domain"]),
                "reason": row["reason"], "_amount": Decimal("0")})
            group["_amount"] += abs(parse_amount(row["score"]) or Decimal("0"))
        out = []
        for group in sorted(groups.values(), key=lambda x: -x["_amount"]):
            amount = _quantized(group.pop("_amount"))
            out.append({**group, "amount": fnum(amount)})
        return out

    unadjusted = lines_for("unadjusted")
    adjusted = lines_for("adjusted")
    total_unadjusted = _quantized(sum(
        (parse_amount(x["amount"]) for x in unadjusted), Decimal("0")))
    total_adjusted = _quantized(sum(
        (parse_amount(x["amount"]) for x in adjusted), Decimal("0")))

    # Count unique candidate misstatements (by id), not raw rows.
    cand_status: dict[str, str] = {}
    review_status: dict[str, str] = {}
    for row in rows:
        if _is_candidate(row):
            cand_status[finding_id(row)] = row.get("disposition", "undisposed")
        if (row.get("audit_class") in ("exception", "structural")
                and row.get("verdict") != "AGREE"):
            review_status[finding_id(row)] = row.get("disposition", "undisposed")
    candidates = list(cand_status)
    disposed = sum(1 for s in cand_status.values() if s != "undisposed")
    open_count = sum(1 for s in cand_status.values()
                     if s in ("undisposed", "follow_up"))
    review_open_count = sum(1 for s in review_status.values()
                            if s in ("undisposed", "follow_up"))

    invalid_waivers = []
    for row in rows:
        if not (_is_candidate(row) and row.get("disposition") == "waived"):
            continue
        magnitude = abs(parse_amount(row["score"]) or Decimal("0"))
        if magnitude > ctt:
            invalid_waivers.append(finding_id(row))
    invalid_waivers = sorted(set(invalid_waivers))

    conclusion = None
    if overall and not open_count and not invalid_waivers:
        conclusion = ("immaterial" if total_unadjusted < overall else "material")

    return {
        "overall_materiality": fnum(overall),
        "performance_materiality": fnum(performance),
        "clearly_trivial": fnum(ctt),
        "unadjusted": sorted(unadjusted, key=lambda x: -x["amount"]),
        "adjusted_count": len(adjusted),
        "total_unadjusted": fnum(total_unadjusted),
        "total_adjusted": fnum(total_adjusted),
        "candidates": len(candidates),
        "disposed": disposed,
        "undisposed": len(candidates) - disposed,
        "open_count": open_count,
        "review_items": len(review_status),
        "review_open_count": review_open_count,
        "invalid_waiver_count": len(invalid_waivers),
        "invalid_waivers": invalid_waivers,
        "conclusion": conclusion,
    }
