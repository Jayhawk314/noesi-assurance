# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The engagement entity: the root isolation boundary.

``client_name`` and ``period_end`` are human-readable attributes. Identity is
the opaque ``engagement_id`` — renaming a client can never fork state, and two
periods of the same client can never share it.
"""

from __future__ import annotations

from dataclasses import dataclass

STATUSES = ("open", "locked", "archived")


@dataclass(frozen=True)
class Engagement:
    engagement_id: str
    tenant_id: str
    client_name: str
    period_end: str
    status: str = "open"
    version: int = 1

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"unknown engagement status {self.status!r}")
        if not self.client_name.strip():
            raise ValueError("client_name must be non-empty")
        if not self.period_end.strip():
            raise ValueError("period_end must be non-empty")
