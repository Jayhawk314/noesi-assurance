# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Evidence vault: quarantine, write-once promotion, verified reads, retention."""

import io

import pytest

from assurance_artifacts.intake import retire_artifact, store_artifact
from assurance_artifacts.vault import (
    ArtifactVault, VaultIntegrityError, VaultPolicy, VaultPolicyError,
)
from assurance_domain.commands import Command
from assurance_domain.errors import ConflictError
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from assurance_persistence.spine import run_command

CONTENT = b"payment_number,amount\nP1,100.00\nP2,250.50\n"


@pytest.fixture()
def vault(tmp_path):
    return ArtifactVault(tmp_path / "vault")


@pytest.fixture()
def env(tmp_path, vault):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    tenant = ensure_tenant(conn, "firm")
    engagement = run_command(
        conn, Command("create-eng", tenant, "p1", "engagement.create"),
        lambda uow: {"id": uow.engagements.create("Acme", "2025-12-31")}
    ).result["id"]
    yield conn, vault, tenant, engagement
    conn.close()


def _cmd(tenant, cid, engagement_id=None):
    return Command(cid, tenant, "principal-1", "artifact.store",
                   engagement_id=engagement_id)


# ----------------------------------------------------------------- vault core

def test_stage_promote_read_roundtrip(vault):
    staged = vault.stage(io.BytesIO(CONTENT), media_type="text/csv",
                         original_name="payments.csv")
    assert staged.size_bytes == len(CONTENT)
    vault.promote(staged)
    assert vault.read_bytes(staged.sha256) == CONTENT
    assert not staged.path.exists()  # quarantine copy consumed


def test_tampered_blob_is_refused_on_read(vault):
    staged = vault.stage(io.BytesIO(CONTENT), media_type="text/csv",
                         original_name="payments.csv")
    path = vault.promote(staged)
    path.write_bytes(b"forged content")
    with pytest.raises(VaultIntegrityError, match="tampered"):
        vault.read_bytes(staged.sha256)


def test_oversize_upload_is_cut_off_mid_stream(tmp_path):
    vault = ArtifactVault(tmp_path / "v", VaultPolicy(max_bytes=10))
    with pytest.raises(VaultPolicyError, match="mid-stream"):
        vault.stage(io.BytesIO(CONTENT), media_type="text/csv",
                    original_name="big.csv")
    assert not list((tmp_path / "v" / "quarantine").iterdir())


def test_undeclared_media_type_is_refused(vault):
    with pytest.raises(VaultPolicyError, match="not accepted"):
        vault.stage(io.BytesIO(b"MZ..."), media_type="application/x-msdownload",
                    original_name="evil.exe")


def test_promotion_is_write_once_and_content_idempotent(vault):
    first = vault.stage(io.BytesIO(CONTENT), media_type="text/csv",
                        original_name="a.csv")
    vault.promote(first)
    second = vault.stage(io.BytesIO(CONTENT), media_type="text/csv",
                         original_name="b.csv")
    vault.promote(second)  # same content: no-op, no error
    assert vault.read_bytes(first.sha256) == CONTENT


# ------------------------------------------------------------ intake ordering

def test_store_artifact_registers_then_promotes(env):
    conn, vault, tenant, engagement = env
    outcome = store_artifact(
        conn, vault, command=_cmd(tenant, "store-1", engagement),
        engagement_id=engagement, source=io.BytesIO(CONTENT),
        media_type="text/csv", original_name="payments.csv",
        provenance="client email 2026-07-20")
    row = conn.execute("SELECT * FROM artifact").fetchone()
    assert row["artifact_id"] == outcome.result["artifact_id"]
    assert row["state"] == "promoted"
    assert vault.read_bytes(row["sha256"]) == CONTENT
    assert conn.execute(
        "SELECT COUNT(*) c FROM domain_event WHERE event_type = 'artifact.registered'"
    ).fetchone()["c"] == 1


def test_duplicate_content_in_one_engagement_conflicts_and_discards(env):
    conn, vault, tenant, engagement = env
    store_artifact(conn, vault, command=_cmd(tenant, "store-1", engagement),
                   engagement_id=engagement, source=io.BytesIO(CONTENT),
                   media_type="text/csv", original_name="payments.csv")
    with pytest.raises(ConflictError):
        store_artifact(conn, vault,
                       command=_cmd(tenant, "store-dup", engagement),
                       engagement_id=engagement, source=io.BytesIO(CONTENT),
                       media_type="text/csv", original_name="again.csv")
    # Registration rolled back; the staged duplicate was discarded.
    assert conn.execute("SELECT COUNT(*) c FROM artifact").fetchone()["c"] == 1
    assert not list((vault.root / "quarantine").iterdir())


def test_store_replay_is_side_effect_free(env):
    conn, vault, tenant, engagement = env
    first = store_artifact(
        conn, vault, command=_cmd(tenant, "same-cmd", engagement),
        engagement_id=engagement, source=io.BytesIO(CONTENT),
        media_type="text/csv", original_name="payments.csv")
    second = store_artifact(
        conn, vault, command=_cmd(tenant, "same-cmd", engagement),
        engagement_id=engagement, source=io.BytesIO(CONTENT),
        media_type="text/csv", original_name="payments.csv")
    assert second.replayed is True
    assert second.result == first.result
    assert conn.execute("SELECT COUNT(*) c FROM artifact").fetchone()["c"] == 1
    assert not list((vault.root / "quarantine").iterdir())


def test_retirement_tombstones_manifest_then_removes_bytes(env):
    conn, vault, tenant, engagement = env
    stored = store_artifact(
        conn, vault, command=_cmd(tenant, "store-1", engagement),
        engagement_id=engagement, source=io.BytesIO(CONTENT),
        media_type="text/csv", original_name="payments.csv")
    artifact_id = stored.result["artifact_id"]
    retire_artifact(conn, vault,
                    command=Command("retire-1", tenant, "p1", "artifact.retire"),
                    artifact_id=artifact_id, reason="client withdrew consent")
    row = conn.execute("SELECT * FROM artifact").fetchone()
    assert row["state"] == "retired"
    assert row["retire_reason"] == "client withdrew consent"
    assert not vault.has_blob(row["sha256"])
    # A second retirement is a conflict, not a silent no-op.
    with pytest.raises(ConflictError):
        retire_artifact(conn, vault,
                        command=Command("retire-2", tenant, "p1", "artifact.retire"),
                        artifact_id=artifact_id, reason="again")


# ------------------------------------------------- mapping spec + dataset rows

def test_mapping_approval_enforces_separation_server_side(env):
    conn, _, tenant, engagement = env
    from assurance_domain.lifecycle import SeparationOfDutiesError

    spec_id = run_command(
        conn, Command("propose-1", tenant, "preparer-1", "mapping.propose"),
        lambda uow: {"spec_id": uow.mappings.propose(
            engagement, role="Payments", spec={"column_map": {}},
            spec_digest="d" * 64, proposed_by="preparer-1")}
    ).result["spec_id"]

    with pytest.raises(SeparationOfDutiesError):
        run_command(
            conn, Command("approve-self", tenant, "preparer-1", "mapping.approve"),
            lambda uow: uow.mappings.approve(
                spec_id, approved_by="preparer-1") or {})

    run_command(
        conn, Command("approve-1", tenant, "reviewer-1", "mapping.approve"),
        lambda uow: uow.mappings.approve(spec_id, approved_by="reviewer-1") or {})
    row = conn.execute("SELECT status, approved_by FROM mapping_spec").fetchone()
    assert (row["status"], row["approved_by"]) == ("approved", "reviewer-1")


def test_dataset_receipt_is_recorded_with_events(env):
    conn, vault, tenant, engagement = env
    stored = store_artifact(
        conn, vault, command=_cmd(tenant, "store-1", engagement),
        engagement_id=engagement, source=io.BytesIO(CONTENT),
        media_type="text/csv", original_name="payments.csv")

    def handler(uow):
        spec_id = uow.mappings.propose(
            engagement, role="Payments", spec={}, spec_digest="d" * 64,
            proposed_by="preparer-1",
            artifact_id=stored.result["artifact_id"])
        uow.mappings.approve(spec_id, approved_by="reviewer-1")
        dataset_id = uow.datasets.record(
            engagement, role="Payments", mapping_spec_id=spec_id,
            artifact_id=stored.result["artifact_id"], rows_in=3,
            rows_loaded=2, rows_rejected=1, control_total="350.50",
            output_digest="e" * 64)
        return {"dataset_id": dataset_id}

    run_command(conn, Command("normalize-1", tenant, "preparer-1",
                              "dataset.normalize", engagement_id=engagement),
                handler)
    row = conn.execute("SELECT * FROM normalized_dataset").fetchone()
    assert (row["rows_in"], row["rows_loaded"], row["rows_rejected"]) == (3, 2, 1)
    assert row["control_total"] == "350.50"
