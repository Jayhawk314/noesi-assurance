# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Worker protocol: frozen manifests, verified inputs, sealed results."""

import json
from pathlib import Path

import pytest

from assurance_domain.jobs import (
    InputMismatchError, build_manifest, run_job,
)
from procedures_ap.engines import ENGINE_VERSION, execute_procedure

BUNDLES = Path(__file__).resolve().parent.parent / "golden" / "bundles"


def _golden_case():
    bundle = json.loads(
        (BUNDLES / "executor_ap_three_way_receipt_match.json")
        .read_text(encoding="utf-8"))
    return bundle["tables"], bundle["findings"], bundle["summary"]


def _manifest(tables, policies=None):
    return build_manifest(
        procedure_id="ap.three_way_receipt_match", procedure_version="v1",
        engine_version=ENGINE_VERSION, tables=tables, policies=policies)


def test_job_ids_are_deterministic_and_content_addressed():
    tables, _, _ = _golden_case()
    assert _manifest(tables).job_id == _manifest(tables).job_id
    changed = {**tables, "Vouchers": tables["Vouchers"][:1]}
    assert _manifest(changed).job_id != _manifest(tables).job_id


def test_run_job_executes_against_verified_inputs(tmp_path):
    tables, golden_findings, golden_summary = _golden_case()
    bundle = run_job(_manifest(tables), tables, execute_procedure)
    assert bundle.status == "completed"
    assert bundle.summary == golden_summary
    assert list(bundle.findings) == golden_findings
    assert bundle.result_digest == run_job(
        _manifest(tables), tables, execute_procedure).result_digest


def test_run_job_refuses_tampered_inputs():
    tables, _, _ = _golden_case()
    manifest = _manifest(tables)
    tampered = json.loads(json.dumps(tables))
    tampered["Vouchers"][0]["voucher_amount"] = 999999.0
    with pytest.raises(InputMismatchError):
        run_job(manifest, tampered, execute_procedure)


def test_run_job_refuses_missing_and_extra_tables():
    tables, _, _ = _golden_case()
    manifest = _manifest(tables)
    with pytest.raises(InputMismatchError):
        run_job(manifest, {"Vouchers": tables["Vouchers"]}, execute_procedure)
    with pytest.raises(InputMismatchError):
        run_job(manifest, {**tables, "Sneaky": []}, execute_procedure)


def test_executor_refusal_becomes_an_error_bundle_not_a_crash():
    tables, _, _ = _golden_case()
    manifest = build_manifest(
        procedure_id="ap.split_payment_review", procedure_version="v1",
        engine_version=ENGINE_VERSION, tables=tables, policies={})
    bundle = run_job(manifest, tables, execute_procedure)
    assert bundle.status == "error"
    assert "split_threshold" in bundle.error
    assert bundle.findings == ()
