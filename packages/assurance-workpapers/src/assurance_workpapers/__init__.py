# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The engagement record as a JSON packet, and the working paper rendered
from it.

Every conclusion in the packet resolves to sealed receipts and run
manifests, and the packet carries its own digests, so anyone can reperform
the integrity checks with nothing but the packet and ``verify_packet``.
Nothing is signed: Noesi supplements an audit; it does not approve one.
"""
