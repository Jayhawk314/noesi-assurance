"""P0 2.3: backup and restore of the control DB and vault together (invented data)."""
import hashlib
import json
import zipfile

import pytest

from assurance_application.backup import (BackupRefused, create_backup, restore_backup,
                                          verify_backup)


def _service(data):
    from assurance_application.service import WorkbenchService
    from assurance_artifacts.vault import ArtifactVault
    from assurance_persistence.database import connect, migrate
    from assurance_persistence.legacy_import import ensure_tenant
    data.mkdir(parents=True, exist_ok=True)
    conn = connect(data / "control.db")
    migrate(conn)
    return WorkbenchService(conn, ArtifactVault(data / "vault"), ensure_tenant(conn, "local"))


def _store(data, client="Invented Co", files=(b"a,b\n1,2\n", b"x,y\n3,4\n")):
    svc = _service(data)
    eid = svc.create_engagement("me", client, "2025-12-31")["engagement_id"]
    for i, content in enumerate(files):
        svc.store_source("me", eid, content=content, media_type="text/csv",
                         original_name=f"f{i}.csv", provenance="invented")
    svc._conn.close()
    return eid


def _rewrite(src, dst, change):
    """Copy a backup zip, letting ``change(name, bytes)`` edit or drop entries."""
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
        for name in zin.namelist():
            out = change(name, zin.read(name))
            if out is not None:
                zout.writestr(*out) if isinstance(out, tuple) else zout.writestr(name, out)


def test_round_trip_restores_the_engagement_and_every_file(tmp_path):
    eid = _store(tmp_path / "live")
    report = create_backup(tmp_path / "live", tmp_path / "b.zip")
    assert report["files"] == 2 and report["engagements"] == 1 and report["journal"]["ok"]
    restored = restore_backup(tmp_path / "b.zip", tmp_path / "new")
    assert restored["files"] == 2
    svc = _service(tmp_path / "new")
    assert [e["engagement_id"] for e in svc.list_engagements()] == [eid]
    shas = [r[0] for r in svc._conn.execute("SELECT sha256 FROM artifact")]
    assert sorted(svc._vault.read_bytes(s) for s in shas) == [b"a,b\n1,2\n", b"x,y\n3,4\n"]


def test_a_vault_from_another_store_is_refused(tmp_path):
    _store(tmp_path / "a")
    _store(tmp_path / "b", client="Other Co", files=(b"q,r\n9,9\n",))
    create_backup(tmp_path / "a", tmp_path / "a.zip")
    create_backup(tmp_path / "b", tmp_path / "b.zip")
    with zipfile.ZipFile(tmp_path / "b.zip") as zb:
        other = {n: zb.read(n) for n in zb.namelist() if n.startswith("vault/")}
        other_manifest = json.loads(zb.read("manifest.json"))

    def swap(name, data):  # a's database with b's vault, manifest made consistent
        if name.startswith("vault/"):
            return None
        if name == "manifest.json":
            m = json.loads(data)
            m["blobs"] = other_manifest["blobs"]
            return json.dumps(m)
        return data
    _rewrite(tmp_path / "a.zip", tmp_path / "mixed.zip", swap)
    with zipfile.ZipFile(tmp_path / "mixed.zip", "a") as z:
        for n, d in other.items():
            z.writestr(n, d)
    with pytest.raises(BackupRefused) as err:
        restore_backup(tmp_path / "mixed.zip", tmp_path / "new")
    assert any("does not hold" in p for p in err.value.problems)
    assert any("no record names" in p for p in err.value.problems)
    assert not (tmp_path / "new").exists()
    assert not list(tmp_path.glob(".new.restoring-*"))


def test_a_missing_vault_file_is_refused(tmp_path):
    _store(tmp_path / "live")
    create_backup(tmp_path / "live", tmp_path / "b.zip")
    dropped = []

    def drop_one(name, data):
        if name.startswith("vault/") and not dropped:
            dropped.append(name)
            return None
        return data
    _rewrite(tmp_path / "b.zip", tmp_path / "bad.zip", drop_one)
    with pytest.raises(BackupRefused):
        restore_backup(tmp_path / "bad.zip", tmp_path / "new")
    assert not (tmp_path / "new").exists()


def test_a_damaged_vault_file_is_refused(tmp_path):
    _store(tmp_path / "live")
    create_backup(tmp_path / "live", tmp_path / "b.zip")
    _rewrite(tmp_path / "b.zip", tmp_path / "bad.zip",
             lambda n, d: d + b"tampered" if n.startswith("vault/") else d)
    with pytest.raises(BackupRefused) as err:
        verify_backup(tmp_path / "bad.zip")
    assert any("does not hash to its name" in p for p in err.value.problems)


def test_a_swapped_database_is_refused(tmp_path):
    _store(tmp_path / "a")
    _store(tmp_path / "b", client="Other Co")
    create_backup(tmp_path / "a", tmp_path / "a.zip")
    create_backup(tmp_path / "b", tmp_path / "b.zip")
    with zipfile.ZipFile(tmp_path / "b.zip") as zb:
        other_db = zb.read("control.db")
    _rewrite(tmp_path / "a.zip", tmp_path / "bad.zip",
             lambda n, d: other_db if n == "control.db" else d)
    with pytest.raises(BackupRefused) as err:
        verify_backup(tmp_path / "bad.zip")
    assert any("not the database this backup was made with" in p for p in err.value.problems)


def test_an_entry_outside_the_layout_is_refused(tmp_path):
    _store(tmp_path / "live")
    create_backup(tmp_path / "live", tmp_path / "b.zip")
    _rewrite(tmp_path / "b.zip", tmp_path / "bad.zip", lambda n, d: d)
    with zipfile.ZipFile(tmp_path / "bad.zip", "a") as z:
        z.writestr("../escape.txt", b"x")
    with pytest.raises(BackupRefused) as err:
        restore_backup(tmp_path / "bad.zip", tmp_path / "new")
    assert any("unexpected entry" in p for p in err.value.problems)
    assert not (tmp_path / "escape.txt").exists()


def test_restore_never_overwrites_an_existing_store(tmp_path):
    _store(tmp_path / "live")
    create_backup(tmp_path / "live", tmp_path / "b.zip")
    before = (tmp_path / "live" / "control.db").read_bytes()
    with pytest.raises(BackupRefused):
        restore_backup(tmp_path / "b.zip", tmp_path / "live")
    assert (tmp_path / "live" / "control.db").read_bytes() == before


def test_backup_refuses_a_live_store_already_missing_a_file(tmp_path):
    _store(tmp_path / "live")
    blob = next(p for p in (tmp_path / "live" / "vault" / "blobs").rglob("*") if p.is_file())
    blob.unlink()
    with pytest.raises(BackupRefused):
        create_backup(tmp_path / "live", tmp_path / "b.zip")
    assert not (tmp_path / "b.zip").exists()
    assert not (tmp_path / "b.zip.part").exists()


def test_backup_never_overwrites_and_leaves_out_unnamed_files(tmp_path):
    _store(tmp_path / "live")
    stray = tmp_path / "live" / "vault" / "blobs" / "00" / "00" / ("0" * 64)
    stray.parent.mkdir(parents=True)
    stray.write_bytes(b"leftover")
    report = create_backup(tmp_path / "live", tmp_path / "b.zip")
    assert report["files"] == 2 and report["left_out_files_no_record_names"] == 1
    with pytest.raises(BackupRefused):
        create_backup(tmp_path / "live", tmp_path / "b.zip")


@pytest.mark.parametrize("manifest", [[], {}, {"format": "noesi-backup/1"}])
def test_a_malformed_manifest_is_a_named_refusal(tmp_path, manifest):
    _store(tmp_path / "live")
    create_backup(tmp_path / "live", tmp_path / "b.zip")
    _rewrite(tmp_path / "b.zip", tmp_path / "bad.zip",
             lambda n, d: json.dumps(manifest) if n == "manifest.json" else d)
    with pytest.raises(BackupRefused) as err:
        verify_backup(tmp_path / "bad.zip")
    assert err.value.problems


def test_backup_does_not_overwrite_a_sibling_partial_file(tmp_path):
    _store(tmp_path / "live")
    partial = tmp_path / "b.zip.part"
    partial.write_bytes(b"belongs to another operation")
    create_backup(tmp_path / "live", tmp_path / "b.zip")
    assert partial.read_bytes() == b"belongs to another operation"


def test_an_unreadable_database_is_a_named_refusal(tmp_path):
    _store(tmp_path / "live")
    create_backup(tmp_path / "live", tmp_path / "b.zip")
    damaged = b"not a sqlite database"

    def replace_database(name, data):
        if name == "control.db":
            return damaged
        if name == "manifest.json":
            manifest = json.loads(data)
            manifest["control_db"] = {
                "sha256": hashlib.sha256(damaged).hexdigest(),
                "size_bytes": len(damaged),
            }
            return json.dumps(manifest)
        return data

    _rewrite(tmp_path / "b.zip", tmp_path / "bad.zip", replace_database)
    with pytest.raises(BackupRefused) as err:
        verify_backup(tmp_path / "bad.zip")
    assert any("database cannot be read" in p for p in err.value.problems)


def test_backup_cli_creates_verifies_and_restores(tmp_path, capsys):
    from workbench_api.backup import main

    live, backup, restored = tmp_path / "live", tmp_path / "backup.zip", tmp_path / "new"
    eid = _store(live)
    assert main(["create", "--data", str(live), "--to", str(backup)]) == 0
    created = json.loads(capsys.readouterr().out)
    assert created["files"] == 2 and created["engagements"] == 1

    assert main(["verify", str(backup)]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["journal"]["ok"] is True

    assert main(["restore", str(backup), "--data", str(restored)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["restored_to"] == str(restored)
    svc = _service(restored)
    assert [e["engagement_id"] for e in svc.list_engagements()] == [eid]
    svc._conn.close()


def test_backup_cli_prints_every_refusal_problem_and_exits_one(tmp_path, capsys):
    from workbench_api.backup import main

    _store(tmp_path / "live")
    create_backup(tmp_path / "live", tmp_path / "backup.zip")
    assert main(["restore", str(tmp_path / "backup.zip"),
                 "--data", str(tmp_path / "live")]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "backup operation refused" in output.err
    assert "not empty" in output.err
