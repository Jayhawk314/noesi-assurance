# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The engagement record as one JSON packet, and its offline check.

``seal_packet`` adds the packet's digest over everything except the seal
block itself. ``verify_packet`` needs no database or vault — only the
packet — and reports each claim separately instead of one flag:

1. every finding receipt re-hashes to its recorded receipt_id;
2. every run's result digest re-derives from its recorded content;
3. the record manifest re-hashes to the digest the packet carries;
4. the packet digest itself re-derives.

Nothing is signed (sign-offs were removed on 1 Oct 2026: Noesi supplements
an audit, it does not approve one). So the digests show the packet is
internally consistent — a corrupted or partly edited packet fails — but
anyone able to edit it can also recompute them. They do not prove who
produced it, that the client's source documents are authentic or complete,
or when it was made.
"""

from __future__ import annotations

import hashlib
import json

# v4 (1 Oct 2026): no lock and no signatures; the record manifest travels
# as "manifest" with its digest. Signed v3 packets from before are refused
# by this checker rather than half-verified.
PACKET_VERSION = "noesi-evidence-packet-v4"

PACKET_LIMITS = (
    "Digests make this packet internally consistent: a corrupted or partly "
    "edited packet fails the check. The packet is not signed, so anyone able "
    "to edit it can recompute the digests; it does not prove who produced "
    "it, that the client's source documents are authentic or complete, or "
    "when it was made."
)


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_digest(manifest: dict) -> str:
    return _sha(_canonical(manifest))


def packet_digest(packet: dict) -> str:
    body = {key: value for key, value in packet.items() if key != "seal"}
    return _sha(_canonical(body))


def seal_packet(packet: dict) -> dict:
    packet["seal"] = {"packet_digest": packet_digest(packet)}
    return packet


def _receipt_id_of(finding: dict) -> str:
    body = {key: value for key, value in finding.items()
            if key != "receipt_id"}
    return _sha(json.dumps(body, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False).encode("utf-8"))


def _result_digest_of(run: dict) -> str:
    payload = json.dumps({
        "job_id": run["job_id"], "status": run["status_at_execution"],
        "summary": run["summary"], "findings": run["findings"],
        "error": run["error"],
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return _sha(payload.encode("utf-8"))


def verify_packet(packet: dict) -> dict:
    """Reperform every integrity claim using only the packet's own content."""
    if packet.get("packet_version") != PACKET_VERSION:
        raise ValueError(
            f"packet version {packet.get('packet_version')!r} is not "
            f"{PACKET_VERSION!r}; signed packets from before 1 Oct 2026 are "
            "checked with the release that made them")
    receipt_failures = []
    run_seal_failures = []
    for run in packet.get("runs", []):
        for finding in run.get("findings", []):
            if _receipt_id_of(finding) != finding.get("receipt_id"):
                receipt_failures.append(finding.get("receipt_id", "missing"))
        if _result_digest_of(run) != run.get("result_digest"):
            run_seal_failures.append(run.get("run_id"))

    seal = packet.get("seal") or {}
    checks = {
        "finding_receipts_ok": not receipt_failures,
        "run_seals_ok": not run_seal_failures,
        "manifest_ok": manifest_digest(packet.get("manifest") or {})
        == packet.get("manifest_digest"),
        "packet_digest_ok": packet_digest(packet) == seal.get("packet_digest"),
    }
    return {
        **checks,
        "verified": all(checks.values()),
        "receipt_failures": receipt_failures,
        "run_seal_failures": run_seal_failures,
        "limits": packet.get("limits", ""),
    }
