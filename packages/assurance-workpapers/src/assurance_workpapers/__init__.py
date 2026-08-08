# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Evidence packets and workpapers, built from frozen signed snapshots.

Never from live mutable rows: export refuses unless the lock verifies, and
every conclusion in the packet resolves to sealed receipts, run manifests,
review chains, and the signed lock manifest. The packet carries its own
verification material — digests, public keys, signatures — so a reviewer
can reperform the integrity checks in a clean environment with nothing but
the packet and this module's ``verify_packet``.
"""
