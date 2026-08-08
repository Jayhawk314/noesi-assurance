# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Content-addressed finding receipts.

A faithful port of the prototype's SeamVerdict envelope — field names,
validation rules, canonical serialization, and schema version are kept
identical so a v2 engine producing the same finding yields the *same
receipt_id* as the prototype. That bit-for-bit equality is what the Phase 2
shadow tests assert against the golden bundles.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field

SCHEMA_VERSION = "noesis-seam-verdict-v1"

VERDICTS = ("AGREE", "TENSION", "CLASH", "ORPHAN", "AMBIGUOUS", "ERROR")
_PAIRED = {"AGREE", "TENSION", "CLASH"}


@dataclass(frozen=True)
class Receipt:
    """One domain-owned decision with enough evidence to audit it."""

    domain: str
    key: tuple
    verdict: str
    policy: str
    sources: tuple[str, ...]
    score: float | None = None
    reason: str = ""
    evidence: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.domain.strip():
            raise ValueError("domain must be non-empty")
        if not isinstance(self.key, tuple) or not self.key:
            raise ValueError("key must be a non-empty tuple")
        if self.verdict not in VERDICTS:
            raise ValueError(f"unknown verdict: {self.verdict!r}")
        if not self.policy.strip():
            raise ValueError("policy must identify the domain checker")
        if len(set(self.sources)) != len(self.sources):
            raise ValueError("sources must be distinct")
        if self.verdict in _PAIRED and len(self.sources) < 2:
            raise ValueError(f"{self.verdict} requires at least two sources")
        if self.verdict == "ORPHAN" and len(self.sources) != 1:
            raise ValueError("ORPHAN requires exactly one observed source")
        if self.score is not None and (
                not math.isfinite(self.score) or self.score < 0):
            raise ValueError("score must be finite and non-negative")
        try:
            json.dumps(self.evidence, sort_keys=True, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("evidence must be finite JSON data") from exc

    @property
    def receipt_id(self) -> str:
        payload = json.dumps(
            self.to_dict(include_receipt_id=False), sort_keys=True,
            separators=(",", ":"), ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def to_dict(self, *, include_receipt_id: bool = True) -> dict:
        out = {
            "schema_version": SCHEMA_VERSION,
            "domain": self.domain,
            "key": list(self.key),
            "verdict": self.verdict,
            "policy": self.policy,
            "sources": list(self.sources),
            "score": self.score,
            "reason": self.reason,
            "evidence": self.evidence,
        }
        if include_receipt_id:
            out["receipt_id"] = self.receipt_id
        return out


def content_hash(record: dict) -> str:
    """SHA-256 of a canonical JSON record; fails closed on non-JSON input."""
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
