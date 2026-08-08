# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Artifact intake: stage, register, promote — in that order, atomically.

The ordering is the point (assessment P0): bytes are staged and hashed
first, the database accepts the manifest inside one command transaction,
and only then are the bytes promoted into the write-once store. A failed
registration discards the staged bytes; a crash between commit and
promotion is safe because promotion is idempotent by content and can be
retried from the staged file.
"""

from __future__ import annotations

import sqlite3
from typing import BinaryIO, Iterable

from assurance_domain.commands import Command
from assurance_persistence.spine import CommandOutcome, run_command

from assurance_artifacts.vault import ArtifactVault, StagedArtifact


def store_artifact(conn: sqlite3.Connection, vault: ArtifactVault, *,
                   command: Command, engagement_id: str,
                   source: BinaryIO | Iterable[bytes], media_type: str,
                   original_name: str, provenance: str = "",
                   retention_class: str = "engagement") -> CommandOutcome:
    """Stage bytes, register the manifest transactionally, then promote."""
    staged: StagedArtifact = vault.stage(
        source, media_type=media_type, original_name=original_name)

    def handler(uow) -> dict:
        artifact_id = uow.artifacts.register(
            engagement_id, sha256=staged.sha256, size_bytes=staged.size_bytes,
            media_type=staged.media_type, original_name=staged.original_name,
            provenance=provenance, retention_class=retention_class)
        return {"artifact_id": artifact_id, "sha256": staged.sha256,
                "size_bytes": staged.size_bytes}

    try:
        outcome = run_command(conn, command, handler)
    except BaseException:
        vault.discard(staged)
        raise
    if outcome.replayed:
        # The manifest already exists from a previous run; the staged copy
        # is redundant (promotion already happened or can be retried there).
        vault.discard(staged)
        return outcome
    vault.promote(staged)
    return outcome


def retire_artifact(conn: sqlite3.Connection, vault: ArtifactVault, *,
                    command: Command, artifact_id: str,
                    reason: str) -> CommandOutcome:
    """Tombstone the manifest, then remove the bytes. Never the reverse."""
    def handler(uow) -> dict:
        row = uow.artifacts.get(artifact_id)
        uow.artifacts.retire(artifact_id, reason)
        return {"artifact_id": artifact_id, "sha256": row["sha256"]}

    outcome = run_command(conn, command, handler)
    if not outcome.replayed:
        vault.remove_blob(outcome.result["sha256"])
    return outcome
