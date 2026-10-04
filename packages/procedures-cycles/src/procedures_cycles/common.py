# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Shared helpers for cycle executors: receipts, parsing, policy reading.

Executors take canonical tables (role -> list of records) and the
engagement's approved policies, and return (receipts, stats) — the same
contract the AP executors honor, so the job runner, findings, review and
lock treat both alike.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from assurance_domain.money import fnum
from assurance_domain.receipts import Receipt, content_hash

CENT = Decimal("0.01")
ZERO = Decimal("0")


class PolicyError(ValueError):
    """A required judgment (policy) is missing or unusable."""


def records(tables: dict, role: str) -> list[dict]:
    from procedures_ap.readlog import note_role
    note_role(role)
    table = tables.get(role)
    if table is None:
        return []
    return list(getattr(table, "records", table) or ())


def dec(value) -> Decimal | None:
    """Exact Decimal from a record value (Decimal, number or accounting text)."""
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return Decimal(repr(value))
    s = str(value).strip()
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace("$", "").replace(",", "").replace("%", "").strip()
    try:
        d = Decimal(s)
    except InvalidOperation:
        return None
    if not d.is_finite():
        return None
    return -d if neg else d


def money(value) -> Decimal:
    d = dec(value)
    return (d if d is not None else ZERO).quantize(CENT)


def day(value) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and len(value) >= 10:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def strict_day(value) -> date | None:
    """A date given as a date or as exactly YYYY-MM-DD; anything else is None
    (trailing text is not truncated away)."""
    if isinstance(value, date):
        return value
    s = str(value or "").strip()
    if len(s) != 10 or s[4] != "-" or s[7] != "-":
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def text(value) -> str:
    return str(value or "").strip()


def key_text(value) -> str:
    """Normalize an identifier: '3246', '3246.0' and ' 3246 ' compare equal."""
    s = text(value)
    d = dec(s)
    if d is not None and d == d.to_integral_value() and "e" not in s.lower():
        return str(int(d))
    return s.lower()


def policy_decimal(policies: dict, name: str) -> Decimal:
    value = dec(policies.get(name))
    if value is None:
        raise PolicyError(f"policy {name!r} is not set; it is the auditor's decision")
    return value


def policy_rate(policies: dict, name: str) -> float:
    """A rate policy given as a fraction (0.1) or a percent (10 or '10%')."""
    raw = policies.get(name)
    value = dec(raw)
    if value is None:
        raise PolicyError(f"policy {name!r} is not set; it is the auditor's decision")
    as_text = str(raw)
    if value >= 1 or as_text.strip().endswith("%"):
        value = value / 100
    return float(value)


def policy_date(policies: dict, name: str) -> date:
    value = day(policies.get(name))
    if value is None:
        raise PolicyError(f"policy {name!r} is not set or is not a date")
    return value


def period_start(pe: date) -> date:
    """The day after the same date a year earlier: a twelve-month period."""
    try:
        return pe.replace(year=pe.year - 1) + timedelta(days=1)
    except ValueError:                       # 29 February
        return pe.replace(year=pe.year - 1, day=28) + timedelta(days=1)


def period_bounds(policies: dict) -> tuple[date, date]:
    """The engagement's period: its recorded start (workflow section 'period'),
    or twelve months ending at period end when no start is recorded."""
    pe = policy_date(policies, "period_end")
    start = day(policies.get("period_start"))
    return (start or period_start(pe)), pe


def report_window(policies: dict) -> tuple[date, date]:
    """Period end and report date, the subsequent period's bounds. The report
    date is required and must follow period end: without it the window is
    undefined, and an earlier one is impossible."""
    pe = policy_date(policies, "period_end")
    raw = policies.get("report_date")
    rd = strict_day(raw)
    if raw not in (None, "") and rd is None:
        raise PolicyError(f"report date {raw!r} is not a date (YYYY-MM-DD exactly)")
    if rd is None:
        raise PolicyError("policy 'report_date' is not set (the date of the auditor's "
                          "report; it bounds the subsequent period and dates the "
                          "representation letter)")
    if rd <= pe:
        raise PolicyError(f"report date {rd} must follow the period end {pe}")
    return pe, rd


def source_ref(role: str, record: dict, key: str) -> dict:
    return {"table": role, "row": record.get("source_row"),
            "record_id": text(record.get(key)) or f"row-{record.get('source_row')}",
            "content_hash": record.get("source_hash") or content_hash(
                {k: str(v) for k, v in record.items()})}


def receipt(procedure_id: str, key: tuple, verdict: str, reason: str,
            evidence: dict, score: Decimal | None = None) -> Receipt:
    """A procedure-run receipt in the same envelope the AP executors emit."""
    sources = (("approved_evidence",) if verdict == "ORPHAN"
               else ("approved_evidence", "procedure_contract"))
    return Receipt(
        domain="audit_procedure_run", key=(procedure_id, *[str(k) for k in key]),
        verdict=verdict, policy=f"{procedure_id}.v1", sources=sources,
        score=fnum(abs(score)) if score is not None else None,
        reason=reason, evidence=jsonable(evidence))


def jsonable(value):
    """Decimals and dates become strings so the receipt seal is canonical JSON."""
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return round(value, 10)
    return value
