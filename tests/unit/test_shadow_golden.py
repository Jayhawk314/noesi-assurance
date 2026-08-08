# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Shadow mode: the v2 port diffed against the Phase 0 golden bundles.

Contracts and coverage must match the prototype exactly (after the
documented D1 normalization); engine receipts must match bit-for-bit,
receipt_id included. See docs/architecture/PHASE2_DIVERGENCES.md.
"""

import json
from pathlib import Path

import pytest

from procedures_ap.contracts import PROCEDURES
from procedures_ap.coverage import (
    apply_evidence_lifecycle, apply_selections, compile_coverage,
)
from procedures_ap.engines import execute_procedure

BUNDLES = Path(__file__).resolve().parent.parent / "golden" / "bundles"


def _load(name: str) -> dict:
    return json.loads((BUNDLES / name).read_text(encoding="utf-8"))


def _normalize_d1(obj):
    """Golden compile-time 'completed' becomes 'not_run' (divergence D1)."""
    if isinstance(obj, dict):
        return {key: ("not_run" if key == "execution_status" and value == "completed"
                      else _normalize_d1(value))
                for key, value in obj.items()}
    if isinstance(obj, list):
        return [_normalize_d1(item) for item in obj]
    return obj


# ---------------------------------------------------------------- contracts

def test_contracts_match_golden_exactly():
    golden = _load("contracts.json")
    assert [c.to_dict() for c in PROCEDURES] == golden["contracts"]


# ----------------------------------------------------------------- coverage

@pytest.mark.parametrize("bundle", [
    "coverage_full.json", "coverage_partial.json", "coverage_empty.json",
])
def test_coverage_compilation_matches_golden(bundle):
    golden = _load(bundle)
    compiled = compile_coverage(golden["inventory"],
                                policies=golden.get("policies") or None)
    assert compiled == _normalize_d1(golden["coverage"])


def test_selection_overlay_matches_golden():
    golden = _load("coverage_selection_overlay.json")
    base = _load("coverage_partial.json")
    compiled = apply_selections(
        compile_coverage(base["inventory"]), golden["selections"])
    assert compiled == _normalize_d1(golden["coverage"])


def test_evidence_lifecycle_overlay_matches_golden():
    golden = _load("coverage_evidence_lifecycle.json")
    base = _load("coverage_partial.json")
    compiled = apply_evidence_lifecycle(
        apply_selections(compile_coverage(base["inventory"]), {}),
        golden["records"])
    assert compiled == _normalize_d1(golden["coverage"])


# ------------------------------------------------------------------ engines

@pytest.mark.parametrize("bundle", [
    "executor_ap_three_way_receipt_match.json",
    "executor_ap_subledger_gl_balance_tie.json",
    "executor_ap_split_payment_review.json",
    "executor_cash_bank_clearing.json",
    "executor_gl_payment_posting.json",
    "executor_forensic_closed_value_flow.json",
])
def test_engine_receipts_match_golden_bit_for_bit(bundle):
    golden = _load(bundle)
    findings, summary = execute_procedure(
        golden["procedure_id"], golden["tables"], golden["policies"])
    assert summary == golden["summary"]
    produced = [item.to_dict() for item in findings]
    assert produced == golden["findings"], (
        "receipt drift — every field including receipt_id must match")


def test_refusals_match_golden_messages():
    golden = _load("executor_refusals.json")
    split_tables = _load("executor_ap_split_payment_review.json")["tables"]

    with pytest.raises(ValueError) as excinfo:
        execute_procedure("ap.split_payment_review", split_tables, {})
    assert str(excinfo.value) == golden["split_threshold_missing"]["message"]

    # Phase 0 probed with ap.payment_voucher_reference, which had no executor
    # then. That procedure runs now, so the probe uses an id that can never be
    # registered; the frozen refusal message is unchanged.
    with pytest.raises(ValueError) as excinfo:
        execute_procedure("ap.never_registered_probe", {}, {})
    assert str(excinfo.value) == \
        golden["unregistered_incremental_procedure"]["message"]


def test_closed_value_flow_runs_on_the_owned_structural_adapter():
    # D2 resolved: the round-trip engine runs without vendored KOMPOSOS.
    golden = _load("executor_forensic_closed_value_flow.json")
    findings, _ = execute_procedure(
        "forensic.closed_value_flow", golden["tables"], {})
    assert findings, "the golden round trip must still be detected"
