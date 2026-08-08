# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Transactional persistence adapters.

One database transaction commits the command's domain change, append-only
event, projection update, and outbox record. Artifact bytes are staged,
hashed, and promoted only after the database accepts the manifest.

Pilot profile: SQLite, single-writer application process.
Firm profile (later): PostgreSQL behind the same repository ports.
"""
