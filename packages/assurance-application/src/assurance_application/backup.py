# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Backup and restore of a Workbench data folder: control DB and vault together.

A backup is one zip file:

    manifest.json                 — what the backup holds, with every digest
    control.db                    — a consistent snapshot (SQLite backup API)
    vault/blobs/ab/cd/<sha256>    — every file a live record names

The database and the vault only mean something together: an artifact row
names its bytes by sha256, and every dataset is re-read from those bytes. So
a backup holds exactly the files the snapshot's records name, and a restore
refuses unless the vault and the database match exactly: every file hashes
to its name, every file the records name is there, and no file is there that
no record names (a vault from another store).

What this does not prove: the manifest is not signed. It catches a damaged
or mismatched backup, not a deliberate forgery of the whole zip.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import uuid
import zipfile
from pathlib import Path

from assurance_persistence.database import MIGRATIONS, utcnow
from assurance_persistence.spine import verify_journal

FORMAT = "noesi-backup/1"
_CHUNK = 1024 * 1024
_BLOB_NAME = re.compile(r"^vault/blobs/([0-9a-f]{2})/([0-9a-f]{2})/([0-9a-f]{64})$")
_KNOWN_SCHEMA = max(version for version, _name, _sql in MIGRATIONS)


class BackupRefused(RuntimeError):
    """The backup or restore was refused; ``problems`` says why, in plain words."""

    def __init__(self, problems: list[str]):
        self.problems = list(problems)
        super().__init__("; ".join(self.problems))


def _blob_entry(sha256: str) -> str:
    return f"vault/blobs/{sha256[:2]}/{sha256[2:4]}/{sha256}"


def _record_facts(db_path: Path) -> dict:
    """What a database file says about itself: schema, records, journal."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        check = conn.execute("PRAGMA integrity_check").fetchone()[0]
        has_schema = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' "
            "AND name = 'schema_migrations'").fetchone()
        if check != "ok" or not has_schema:
            return {"integrity": check, "schema_version": None}
        schema = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        shas = {row[0] for row in conn.execute(
            "SELECT sha256 FROM artifact WHERE state = 'promoted'")}
        engagements = conn.execute("SELECT COUNT(*) FROM engagement").fetchone()[0]
        journal = verify_journal(conn)
    finally:
        conn.close()
    return {"integrity": check, "schema_version": schema, "shas": shas,
            "engagements": engagements, "journal": journal}


def _snapshot(db_path: Path, out: Path) -> None:
    """Copy the live database through SQLite's backup API (safe while the
    Workbench runs) into one self-contained file."""
    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(out))
    try:
        src.backup(dst)
        dst.execute("PRAGMA journal_mode = DELETE")
    finally:
        dst.close()
        src.close()


def _hash_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---------------------------------------------------------------- create

def create_backup(data_dir: str | Path, dest: str | Path) -> dict:
    """Write a backup of ``data_dir`` to the new file ``dest``, then verify it.

    Refuses rather than write a backup that could not be restored: the live
    vault must hold every file its records name, each hashing to its name.
    Files no record names (an upload still in progress, leftovers) are left
    out and counted in the report.
    """
    data_dir, dest = Path(data_dir), Path(dest)
    db_path = data_dir / "control.db"
    blobs_root = data_dir / "vault" / "blobs"
    if not db_path.is_file():
        raise BackupRefused([f"no control database at {db_path}"])
    if dest.exists():
        raise BackupRefused([f"{dest} already exists; a backup never overwrites a file"])
    dest.parent.mkdir(parents=True, exist_ok=True)

    part = dest.with_name(dest.name + ".part")
    with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
        snap = Path(tmp) / "control.db"
        _snapshot(db_path, snap)
        facts = _record_facts(snap)
        if facts["integrity"] != "ok" or facts["schema_version"] is None:
            raise BackupRefused([f"the live database fails its integrity check: {facts['integrity']}"])

        problems = []
        for sha in sorted(facts["shas"]):
            blob = blobs_root / sha[:2] / sha[2:4] / sha
            if not blob.is_file():
                problems.append(f"the records name file {sha[:12]}…, which the live vault does not hold")
        if problems:
            raise BackupRefused(problems + [
                "the live store is already incomplete; a backup of it could not be restored"])

        blobs = []
        try:
            with zipfile.ZipFile(part, "w", compression=zipfile.ZIP_DEFLATED,
                                 allowZip64=True) as zf:
                zf.write(snap, "control.db")
                for sha in sorted(facts["shas"]):
                    blob = blobs_root / sha[:2] / sha[2:4] / sha
                    digest, size = hashlib.sha256(), 0
                    with blob.open("rb") as src, \
                            zf.open(_blob_entry(sha), "w", force_zip64=True) as out:
                        for chunk in iter(lambda: src.read(_CHUNK), b""):
                            digest.update(chunk)
                            size += len(chunk)
                            out.write(chunk)
                    if digest.hexdigest() != sha:
                        problems.append(f"live vault file {sha[:12]}… no longer hashes to its name")
                    blobs.append({"sha256": sha, "size_bytes": size})
                if problems:
                    raise BackupRefused(problems + [
                        "the live vault is damaged; a backup of it could not be restored"])
                left_out = sum(1 for p in blobs_root.rglob("*")
                               if p.is_file() and p.name not in facts["shas"]) \
                    if blobs_root.is_dir() else 0
                manifest = {
                    "format": FORMAT,
                    "created_at": utcnow(),
                    "source": str(data_dir),
                    "schema_version": facts["schema_version"],
                    "control_db": {"sha256": _hash_path(snap), "size_bytes": snap.stat().st_size},
                    "blobs": blobs,
                    "engagements": facts["engagements"],
                    "journal": facts["journal"],
                    "left_out_files_no_record_names": left_out,
                }
                zf.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
        except BaseException:
            part.unlink(missing_ok=True)
            raise

    try:
        report = verify_backup(part)
    except BaseException:
        part.unlink(missing_ok=True)
        raise
    os.replace(part, dest)
    report["file"] = str(dest)
    report["left_out_files_no_record_names"] = manifest["left_out_files_no_record_names"]
    return report


# ---------------------------------------------------------------- check

def _unpack_and_check(backup: Path, into: Path) -> dict:
    """Extract ``backup`` into the empty folder ``into`` as a data folder
    (control.db, vault/blobs/…) and check it; raise BackupRefused on any
    mismatch. Every problem found is reported, not only the first."""
    try:
        zf = zipfile.ZipFile(backup)
    except (zipfile.BadZipFile, OSError) as exc:
        raise BackupRefused([f"{backup} is not a readable backup file: {exc}"]) from exc

    problems: list[str] = []
    with zf:
        names = zf.namelist()
        if len(set(names)) != len(names):
            problems.append("the backup lists the same entry twice")
        unexpected = [n for n in names
                      if n not in ("manifest.json", "control.db") and not _BLOB_NAME.match(n)]
        for name in unexpected:
            problems.append(f"unexpected entry in the backup: {name!r}")
        bad_prefix = [n for n in names if (m := _BLOB_NAME.match(n))
                      and not m.group(3).startswith(m.group(1) + m.group(2))]
        for name in bad_prefix:
            problems.append(f"vault entry filed under the wrong folder: {name!r}")
        if "manifest.json" not in names or "control.db" not in names:
            problems.append("the backup has no manifest or no control database")
        if problems:
            raise BackupRefused(problems)

        try:
            manifest = json.loads(zf.read("manifest.json"))
        except ValueError as exc:
            raise BackupRefused([f"the manifest cannot be read: {exc}"]) from exc
        if manifest.get("format") != FORMAT:
            raise BackupRefused([f"unknown backup format {manifest.get('format')!r}; "
                                 f"this software reads {FORMAT}"])

        db_path = into / "control.db"
        with zf.open("control.db") as src, db_path.open("wb") as out:
            shutil.copyfileobj(src, out, _CHUNK)
        if _hash_path(db_path) != manifest["control_db"]["sha256"]:
            problems.append("the control database does not match the digest the manifest "
                            "recorded: it is not the database this backup was made with")

        in_zip = set()
        for name in names:
            m = _BLOB_NAME.match(name)
            if not m:
                continue
            sha = m.group(3)
            target = into / "vault" / "blobs" / sha[:2] / sha[2:4] / sha
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            with zf.open(name) as src, target.open("wb") as out:
                for chunk in iter(lambda: src.read(_CHUNK), b""):
                    digest.update(chunk)
                    out.write(chunk)
            if digest.hexdigest() != sha:
                problems.append(f"vault file {sha[:12]}… does not hash to its name (damaged)")
            in_zip.add(sha)

    listed = {b["sha256"] for b in manifest.get("blobs", [])}
    for sha in sorted(listed - in_zip):
        problems.append(f"the manifest lists vault file {sha[:12]}…, which the backup does not hold")
    for sha in sorted(in_zip - listed):
        problems.append(f"the backup holds vault file {sha[:12]}…, which the manifest does not list")

    facts = _record_facts(db_path)
    if facts["integrity"] != "ok" or facts["schema_version"] is None:
        problems.append(f"the control database fails its integrity check: {facts['integrity']}")
        raise BackupRefused(problems)
    if facts["schema_version"] > _KNOWN_SCHEMA:
        problems.append(f"the backup was made by newer software (schema {facts['schema_version']}, "
                        f"this software knows up to {_KNOWN_SCHEMA})")
    for sha in sorted(facts["shas"] - in_zip):
        problems.append(f"the records name file {sha[:12]}…, which the backup's vault does not hold")
    for sha in sorted(in_zip - facts["shas"]):
        problems.append(f"the backup's vault holds file {sha[:12]}…, which no record names: "
                        "the vault is not this database's vault")
    if problems:
        raise BackupRefused(problems)

    return {
        "format": manifest["format"],
        "created_at": manifest.get("created_at"),
        "schema_version": facts["schema_version"],
        "engagements": facts["engagements"],
        "files": len(in_zip),
        "journal": facts["journal"],
    }


def verify_backup(backup: str | Path) -> dict:
    """Check a backup completely without restoring it."""
    backup = Path(backup)
    with tempfile.TemporaryDirectory() as tmp:
        return _unpack_and_check(backup, Path(tmp))


# --------------------------------------------------------------- restore

def restore_backup(backup: str | Path, data_dir: str | Path) -> dict:
    """Restore ``backup`` into ``data_dir``, which must not exist or be empty.

    Nothing lands in ``data_dir`` unless every check passes: the backup is
    unpacked and checked in a staging folder beside it, then moved in whole.
    A restore never overwrites an existing store.
    """
    backup, data_dir = Path(backup), Path(data_dir)
    if data_dir.exists() and (not data_dir.is_dir() or any(data_dir.iterdir())):
        raise BackupRefused([f"{data_dir} is not empty; restore into a new folder and "
                             "start the Workbench with --data pointing at it"])
    data_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = data_dir.parent / f".{data_dir.name}.restoring-{uuid.uuid4().hex[:8]}"
    staging.mkdir()
    try:
        report = _unpack_and_check(backup, staging)
        (staging / "vault" / "quarantine").mkdir(parents=True, exist_ok=True)
        (staging / "vault" / "blobs").mkdir(parents=True, exist_ok=True)
        if data_dir.exists():
            data_dir.rmdir()
        os.replace(staging, data_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    report["restored_to"] = str(data_dir)
    return report
