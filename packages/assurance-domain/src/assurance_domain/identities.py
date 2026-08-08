# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Opaque engagement-scoped identifiers.

The root isolation defect in the noesi-cpa prototype was human-readable keys:
finding IDs formed as ``company|domain|key`` (no fiscal period) and a global
dispositions store. Here, every persisted object carries opaque UUIDs, and
human-readable company/period are attributes, never keys.
"""

from __future__ import annotations

import uuid
from typing import NewType

TenantId = NewType("TenantId", str)
EngagementId = NewType("EngagementId", str)
EngagementVersionId = NewType("EngagementVersionId", str)
PrincipalId = NewType("PrincipalId", str)
ArtifactId = NewType("ArtifactId", str)
ProcedureRunId = NewType("ProcedureRunId", str)
FindingId = NewType("FindingId", str)


def new_id() -> str:
    """Mint an opaque identifier. UUIDv4, no semantic content."""
    return str(uuid.uuid4())
