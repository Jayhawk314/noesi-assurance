# Copyright (c) 2026 Jayhawk314. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Verify the Phase 0 golden bundles match their manifest digests.

This is a tamper/consistency check only: it proves the bundles on disk are
the ones the capture script wrote, not that their content is accurate.
"""

import gzip
import hashlib
import json
from pathlib import Path

BUNDLES = Path(__file__).resolve().parent.parent / "golden" / "bundles"


def _read_bundle(name: str) -> dict:
    """Load a bundle; large bundles are stored gzipped (.gz beside the name)."""
    raw = BUNDLES / name
    if raw.exists():
        return json.loads(raw.read_text(encoding="utf-8"))
    with gzip.open(BUNDLES / (name + ".gz"), "rt", encoding="utf-8") as fh:
        return json.load(fh)


def _digest(obj) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_manifest_exists_and_covers_bundles():
    manifest = json.loads((BUNDLES / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["bundles"], "manifest lists no bundles"
    names = {entry["file"] for entry in manifest["bundles"]}
    # Every core Phase 0 artifact is present.
    expected = {
        "contracts.json", "coverage_full.json", "coverage_partial.json",
        "coverage_empty.json", "coverage_selection_overlay.json",
        "coverage_evidence_lifecycle.json", "executor_refusals.json",
        "ingest_mapping.json", "sad_summary.json", "readiness_blank.json",
        "rockwood_unified.json", "defect_disposition_collision.json",
        "pins.json",
    }
    assert expected <= names, f"missing bundles: {expected - names}"


def test_bundle_digests_match_manifest():
    manifest = json.loads((BUNDLES / "MANIFEST.json").read_text(encoding="utf-8"))
    for entry in manifest["bundles"]:
        payload = _read_bundle(entry["file"])
        assert _digest(payload) == entry["sha256"], \
            f"{entry['file']} does not match its manifest digest"


def test_contracts_bundle_has_eleven_procedures():
    contracts = json.loads((BUNDLES / "contracts.json").read_text(encoding="utf-8"))
    assert len(contracts["contracts"]) == 11
    ids = {c["procedure_id"] for c in contracts["contracts"]}
    assert "ap.split_payment_review" in ids
    assert "forensic.closed_value_flow" in ids


def test_collision_defect_is_recorded():
    defect = json.loads(
        (BUNDLES / "defect_disposition_collision.json").read_text(encoding="utf-8"))
    # The defect must remain documented as real until the port fixes identity.
    assert defect["collision"] is True
    assert defect["engagement_ids"]["fy2024"] != defect["engagement_ids"]["fy2025"]
