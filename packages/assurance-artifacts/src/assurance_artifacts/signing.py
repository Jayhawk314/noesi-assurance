# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Lock-manifest signing: Ed25519, device-bound local keys.

What a signature here proves — and only this: a principal holding this
device-bound key approved exactly this byte set at the time the local
signer recorded. It does not prove the accounting source was complete or
authentic, and it does not provide trusted time; external anchoring is the
firm-profile upgrade (see PHASE5_NOTES.md).

Keys are created on first use per principal, stored unencrypted-PEM under
the key-store root (the pilot assumes an OS-encrypted single-user disk;
key passphrases arrive with the firm profile). The key id is the SHA-256
of the public key's raw bytes, so verification material is self-identifying.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)

ALGORITHM = "ed25519"


@dataclass(frozen=True)
class SignerIdentity:
    principal_id: str
    key_id: str
    public_key_pem: str


class LocalKeyStore:
    """One Ed25519 key per principal, bound to this device."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, principal_id: str) -> Path:
        safe = hashlib.sha256(principal_id.encode("utf-8")).hexdigest()[:32]
        return self.root / f"{safe}.pem"

    def _load_or_create(self, principal_id: str) -> Ed25519PrivateKey:
        path = self._path(principal_id)
        if path.exists():
            return serialization.load_pem_private_key(
                path.read_bytes(), password=None)
        key = Ed25519PrivateKey.generate()
        path.write_bytes(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()))
        return key

    def identity(self, principal_id: str) -> SignerIdentity:
        key = self._load_or_create(principal_id)
        public = key.public_key()
        raw = public.public_bytes(serialization.Encoding.Raw,
                                  serialization.PublicFormat.Raw)
        pem = public.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo).decode("ascii")
        return SignerIdentity(
            principal_id=principal_id,
            key_id=hashlib.sha256(raw).hexdigest(),
            public_key_pem=pem)

    def sign(self, principal_id: str, digest_hex: str) -> str:
        """Sign a manifest digest; returns the signature as hex."""
        key = self._load_or_create(principal_id)
        return key.sign(digest_hex.encode("ascii")).hex()


def verify_signature(public_key_pem: str, digest_hex: str,
                     signature_hex: str) -> bool:
    """Verify with stored material only — no key store required."""
    try:
        public = serialization.load_pem_public_key(
            public_key_pem.encode("ascii"))
        if not isinstance(public, Ed25519PublicKey):
            return False
        public.verify(bytes.fromhex(signature_hex),
                      digest_hex.encode("ascii"))
        return True
    except Exception:  # noqa: BLE001 — any failure is "not verified"
        return False
