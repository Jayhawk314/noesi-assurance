"""Evidence packet sealing and offline verification.

``seal_packet`` computes the packet digest over everything except the seal
block itself. ``verify_packet`` needs no database, vault, or key store —
only the packet — and reports each claim separately instead of one flag:

1. every finding receipt re-hashes to its recorded receipt_id;
2. every run's result digest re-derives from its recorded content;
3. the lock manifest re-hashes to the digest the lock signature covers;
4. the lock signature verifies with the public key carried in the packet;
5. every superseded lock in the amendment history re-hashes and its
   signature verifies the same way (v3);
6. the export signature verifies likewise over the packet digest;
7. the packet digest itself re-derives.

What none of this proves (stated in the packet): source authenticity,
extraction completeness, or trusted time.
"""

from __future__ import annotations

import hashlib
import json

from assurance_artifacts.signing import verify_signature

# v3: adds "lock_history" — superseded locks carried whole (manifest,
# signature, unlock reason/who/when) per AU-C 230's record of changes after
# file assembly. Absent or empty history verifies vacuously, so v2 packets
# still verify.
PACKET_VERSION = "noesi-evidence-packet-v3"

PACKET_LIMITS = (
    "Digests make this packet tamper-evident and the signatures prove which "
    "principal's device key approved which byte set. Nothing here "
    "authenticates the client's source documents, proves extraction "
    "completeness, or provides trusted time; external anchoring is a "
    "firm-profile control."
)


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def packet_digest(packet: dict) -> str:
    body = {key: value for key, value in packet.items() if key != "seal"}
    return _sha(_canonical(body))


def seal_packet(packet: dict, *, exporter: str, key_id: str,
                public_key_pem: str, signature_hex: str,
                algorithm: str) -> dict:
    packet["seal"] = {
        "packet_digest": packet_digest(packet),
        "exporter": exporter,
        "key_id": key_id,
        "algorithm": algorithm,
        "public_key_pem": public_key_pem,
        "signature_hex": signature_hex,
    }
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
    receipt_failures = []
    run_seal_failures = []
    for run in packet.get("runs", []):
        for finding in run.get("findings", []):
            if _receipt_id_of(finding) != finding.get("receipt_id"):
                receipt_failures.append(finding.get("receipt_id", "missing"))
        if _result_digest_of(run) != run.get("result_digest"):
            run_seal_failures.append(run.get("run_id"))

    lock = packet.get("lock", {})
    manifest_digest = _sha(_canonical(lock.get("manifest", {})))
    manifest_ok = manifest_digest == lock.get("digest")
    lock_signature = lock.get("signature") or {}
    lock_signature_ok = verify_signature(
        lock_signature.get("public_key_pem", ""),
        lock.get("digest", ""),
        lock_signature.get("signature_hex", ""))

    history_failures = []
    for item in packet.get("lock_history", []):
        item_signature = item.get("signature") or {}
        item_ok = (
            _sha(_canonical(item.get("manifest", {}))) == item.get("digest")
            and verify_signature(item_signature.get("public_key_pem", ""),
                                 item.get("digest", ""),
                                 item_signature.get("signature_hex", "")))
        if not item_ok:
            history_failures.append(item.get("sequence"))

    seal = packet.get("seal") or {}
    digest_ok = packet_digest(packet) == seal.get("packet_digest")
    export_signature_ok = verify_signature(
        seal.get("public_key_pem", ""),
        seal.get("packet_digest", ""),
        seal.get("signature_hex", ""))

    checks = {
        "finding_receipts_ok": not receipt_failures,
        "run_seals_ok": not run_seal_failures,
        "lock_manifest_ok": manifest_ok,
        "lock_signature_ok": lock_signature_ok,
        "lock_history_ok": not history_failures,
        "packet_digest_ok": digest_ok,
        "export_signature_ok": export_signature_ok,
    }
    return {
        **checks,
        "verified": all(checks.values()),
        "receipt_failures": receipt_failures,
        "run_seal_failures": run_seal_failures,
        "lock_history_failures": history_failures,
        "limits": packet.get("limits", ""),
    }
