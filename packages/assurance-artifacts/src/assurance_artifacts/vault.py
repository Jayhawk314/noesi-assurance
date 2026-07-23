"""Content-addressed write-once artifact vault with quarantine staging.

Layout under the vault root:

    quarantine/<uuid>.part   — bytes being staged (streamed + hashed)
    blobs/ab/cd/<sha256>     — promoted immutable content

Staging enforces the size and media-type policy while streaming (an
over-limit upload is cut off mid-stream, never fully buffered). Promotion is
write-once: an existing blob is verified byte-identical, never overwritten.
Reads re-verify the digest — a tampered blob raises instead of returning.
Retirement removes bytes explicitly; the manifest row (database) keeps the
tombstone.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable

_CHUNK = 1024 * 1024

DEFAULT_ALLOWED_MEDIA_TYPES = frozenset({
    "text/csv",
    "text/plain",
    "application/json",
    "application/pdf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
})


class VaultPolicyError(ValueError):
    """The upload violates the vault's declared intake policy."""


class VaultIntegrityError(RuntimeError):
    """Stored bytes no longer match their recorded digest."""


@dataclass(frozen=True)
class VaultPolicy:
    max_bytes: int = 200 * 1024 * 1024
    allowed_media_types: frozenset = DEFAULT_ALLOWED_MEDIA_TYPES


@dataclass(frozen=True)
class StagedArtifact:
    path: Path
    sha256: str
    size_bytes: int
    media_type: str
    original_name: str


class ArtifactVault:
    def __init__(self, root: str | Path,
                 policy: VaultPolicy | None = None) -> None:
        self.root = Path(root)
        self.policy = policy or VaultPolicy()
        (self.root / "quarantine").mkdir(parents=True, exist_ok=True)
        (self.root / "blobs").mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------- staging

    def stage(self, source: BinaryIO | Iterable[bytes], *,
              media_type: str, original_name: str) -> StagedArtifact:
        """Stream bytes into quarantine, hashing and policing as they arrive."""
        if media_type not in self.policy.allowed_media_types:
            raise VaultPolicyError(
                f"media type {media_type!r} is not accepted; "
                f"allowed: {sorted(self.policy.allowed_media_types)}")
        part = self.root / "quarantine" / f"{uuid.uuid4()}.part"
        digest = hashlib.sha256()
        size = 0
        chunks = (iter(lambda: source.read(_CHUNK), b"")
                  if hasattr(source, "read") else iter(source))
        try:
            with part.open("wb") as out:
                for chunk in chunks:
                    size += len(chunk)
                    if size > self.policy.max_bytes:
                        raise VaultPolicyError(
                            f"upload exceeds the {self.policy.max_bytes}-byte "
                            "limit; staging aborted mid-stream")
                    digest.update(chunk)
                    out.write(chunk)
        except BaseException:
            part.unlink(missing_ok=True)
            raise
        return StagedArtifact(part, digest.hexdigest(), size,
                              media_type, original_name)

    def discard(self, staged: StagedArtifact) -> None:
        staged.path.unlink(missing_ok=True)

    # ----------------------------------------------------------- promotion

    def _blob_path(self, sha256: str) -> Path:
        return self.root / "blobs" / sha256[:2] / sha256[2:4] / sha256

    def promote(self, staged: StagedArtifact) -> Path:
        """Move staged bytes into the write-once store; idempotent by content."""
        target = self._blob_path(staged.sha256)
        if target.exists():
            # Write-once: same content is a no-op, different content at the
            # same address is corruption and must never be overwritten.
            existing = self._hash_file(target)
            if existing != staged.sha256:
                raise VaultIntegrityError(
                    f"blob at {staged.sha256} does not hash to its address")
            staged.path.unlink(missing_ok=True)
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged.path, target)
        return target

    # --------------------------------------------------------------- reads

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(_CHUNK), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def has_blob(self, sha256: str) -> bool:
        return self._blob_path(sha256).exists()

    def read_bytes(self, sha256: str) -> bytes:
        """Return blob content, re-verifying the digest before release."""
        path = self._blob_path(sha256)
        if not path.is_file():
            raise FileNotFoundError(f"no blob stored for {sha256}")
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != sha256:
            raise VaultIntegrityError(
                f"blob {sha256} hashes to {actual}; refusing to serve "
                "tampered evidence")
        return data

    # ----------------------------------------------------------- retention

    def remove_blob(self, sha256: str) -> bool:
        """Delete bytes for an explicitly retired artifact (tombstone stays
        in the manifest). Returns whether bytes existed."""
        path = self._blob_path(sha256)
        if path.exists():
            path.unlink()
            return True
        return False
