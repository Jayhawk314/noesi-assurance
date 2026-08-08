# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Append-only domain events.

An event records what a command changed: entity, type, before/after versions,
and a payload. Events are written in the same transaction as the state change
they describe; the journal is the authoritative history, projections derive
from it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DomainEvent:
    tenant_id: str
    engagement_id: str | None  # None only for tenant-level/legacy-global events
    command_id: str
    actor: str
    entity_type: str
    entity_id: str
    event_type: str
    before_version: int | None = None
    after_version: int | None = None
    payload: dict = field(default_factory=dict)
