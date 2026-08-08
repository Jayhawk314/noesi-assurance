# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The big shadow: the full Rockwood engagement diffed against the golden.

Hydrates the captured parsed tables (dates restored from explicit markers),
runs the ported unified AP audit, and compares against the prototype's
39-verdict report. Receipts must match bit-for-bit; the only normalizations
are the documented divergences D1 (no completed-at-compile) and D6 (owned
additive-quantale label).
"""

import gzip
import json
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from procedures_ap.unified import unified_ap_audit

BUNDLES = Path(__file__).resolve().parent.parent / "golden" / "bundles"
TABLES_GZ = BUNDLES / "rockwood_tables.json.gz"

pytestmark = pytest.mark.skipif(
    not TABLES_GZ.exists(),
    reason="rockwood_tables.json.gz not captured; run capture_rockwood_tables.py")


def _hydrate(value):
    if isinstance(value, dict):
        if set(value) == {"$date"}:
            return date.fromisoformat(value["$date"])
        if set(value) == {"$datetime"}:
            return datetime.fromisoformat(value["$datetime"])
        return {key: _hydrate(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_hydrate(item) for item in value]
    return value


def _normalize(obj):
    """Documented divergences only: D1 execution_status, D6 algebra label."""
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            if key == "execution_status" and value == "completed":
                out[key] = "not_run"  # D1
            elif key == "exposure_algebra" and value == "komposos_additive_quantale":
                out[key] = "additive_quantale"  # D6
            else:
                out[key] = _normalize(value)
        return out
    if isinstance(obj, list):
        return [_normalize(item) for item in obj]
    return obj


@pytest.fixture(scope="module")
def produced_and_golden():
    with gzip.open(TABLES_GZ, "rt", encoding="utf-8") as fh:
        payload = json.load(fh)
    tables = {
        name: SimpleNamespace(
            records=[_hydrate(record) for record in t["records"]],
            refused_fields=t["refused_fields"],
            column_map=t["column_map"],
            control_total=t["control_total"],
            source_file=t["source_file"])
        for name, t in payload["tables"].items()
    }
    produced = unified_ap_audit(tables, company="Rockwood").to_dict()
    golden = _normalize(json.loads(
        (BUNDLES / "rockwood_unified.json").read_text(encoding="utf-8"))["report"])
    return produced, golden


def test_summary_matches(produced_and_golden):
    produced, golden = produced_and_golden
    assert produced["company"] == golden["company"]
    assert produced["fye"] == golden["fye"]
    assert produced["summary"] == golden["summary"]


def test_every_receipt_matches_bit_for_bit(produced_and_golden):
    produced, golden = produced_and_golden
    mine = produced["verdicts"]
    theirs = golden["verdicts"]
    assert len(mine) == len(theirs)
    for index, (a, b) in enumerate(zip(mine, theirs)):
        assert a == b, (
            f"verdict {index} drifted "
            f"(policy {b['verdict']['policy']}, key {b['verdict']['key']})")


def test_refusals_match(produced_and_golden):
    produced, golden = produced_and_golden
    assert produced["refusals"] == golden["refusals"]


def test_process_view_and_coverage_match(produced_and_golden):
    produced, golden = produced_and_golden
    assert produced["process_view"] == golden["process_view"]
    assert produced["coverage"] == golden["coverage"]


def test_research_ranking_matches(produced_and_golden):
    produced, golden = produced_and_golden
    assert produced["research_ranking"] == golden["research_ranking"]


def test_procedure_coverage_matches(produced_and_golden):
    produced, golden = produced_and_golden
    assert produced["procedure_coverage"] == golden["procedure_coverage"]


def test_whole_report_matches(produced_and_golden):
    produced, golden = produced_and_golden
    assert produced == golden
