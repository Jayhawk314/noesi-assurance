# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Commands: the only way state changes enter the system.

Every command carries an opaque ``command_id`` (the idempotency key), the
acting principal, and its engagement scope. The persistence spine guarantees
that one command commits its domain change, append-only event, and outbox
record in a single transaction — or nothing at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Command:
    command_id: str
    tenant_id: str
    actor: str  # principal identifier; never a display name used for authorization
    kind: str
    engagement_id: str | None = None
    payload: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("command_id", "tenant_id", "actor", "kind"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"command.{name} must be non-empty")
