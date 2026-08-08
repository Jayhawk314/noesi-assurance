# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Immutable evidence vault and artifact intake.

Bytes are staged into quarantine (streamed, hashed, size- and type-policed),
registered in the control database, and only then promoted into the
content-addressed write-once store. Production evidence is never served from
an arbitrary filesystem path, and every read re-verifies the digest.

Pilot scoping (see docs/architecture/PHASE3_NOTES.md): encryption at rest,
malware scanning, and source-system connectors are deferred past the
design-partner pilot; quarantine/promote, digest verification, write-once,
and explicit retention are not.
"""
