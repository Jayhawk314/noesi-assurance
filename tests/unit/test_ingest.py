# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Ingestion: mapping proposal shadow-diffed against the golden, plus the
reviewed-transformation and quarantine semantics the prototype lacked."""

import csv
import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from assurance_domain.lifecycle import SeparationOfDutiesError
from procedures_ap.ingest import (
    approve_mapping, infer_role, normalize_table, parse_decimal,
    propose_mapping,
)

BUNDLES = Path(__file__).resolve().parent.parent / "golden" / "bundles"


def _golden_case():
    golden = json.loads(
        (BUNDLES / "ingest_mapping.json").read_text(encoding="utf-8"))
    # Hash raw bytes exactly as the prototype reader did (CRLF preserved).
    raw = (BUNDLES / golden["input_file"]).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8-sig", errors="replace")
    rows = list(csv.DictReader(text.splitlines()))
    headers = list(rows[0].keys())
    return golden, rows, headers, sha


def _approved(rows, headers, sha):
    spec = propose_mapping("Payments", headers, source_sha256=sha,
                           proposed_by="preparer-1")
    return approve_mapping(spec, approved_by="reviewer-1")


# ------------------------------------------------------------------- shadow

def test_mapping_proposal_matches_golden():
    golden, rows, headers, sha = _golden_case()
    spec = propose_mapping("Payments", headers, source_sha256=sha)
    assert spec.column_map == golden["table"]["column_map"]
    assert list(spec.unmapped_headers) == golden["table"]["unmapped_headers"]
    assert list(spec.refused_fields) == golden["table"]["refused_fields"]
    assert sha == golden["table"]["sha256"]


def test_normalized_records_match_golden_through_the_float_projection():
    golden, rows, headers, sha = _golden_case()
    table = normalize_table(rows, _approved(rows, headers, sha),
                            source_file="ingest_input_payments.csv")
    assert not table.rejects
    projected = []
    for record in table.records:
        row = {}
        for key, value in record.items():
            if isinstance(value, Decimal):
                row[key] = float(value)
            elif isinstance(value, date):
                row[key] = value.isoformat()
            else:
                row[key] = value
        projected.append(row)
    assert projected == golden["records"]
    assert float(table.control_total) == golden["table"]["control_total"]


# ------------------------------------------------------- reviewed transforms

def test_unapproved_spec_cannot_normalize():
    _, rows, headers, sha = _golden_case()
    spec = propose_mapping("Payments", headers, source_sha256=sha,
                           proposed_by="preparer-1")
    with pytest.raises(ValueError, match="approved mapping spec"):
        normalize_table(rows, spec)


def test_proposer_cannot_approve_their_own_mapping():
    _, rows, headers, sha = _golden_case()
    spec = propose_mapping("Payments", headers, source_sha256=sha,
                           proposed_by="preparer-1")
    with pytest.raises(SeparationOfDutiesError):
        approve_mapping(spec, approved_by="preparer-1")


# ------------------------------------------------------ quarantine semantics

def test_rows_with_blank_required_keys_are_quarantined_with_reasons():
    _, rows, headers, sha = _golden_case()
    rows = [dict(r) for r in rows]
    rows[1]["Check No"] = "   "  # payment_number becomes blank
    table = normalize_table(rows, _approved(rows, headers, sha))
    assert len(table.records) == 2
    assert len(table.rejects) == 1
    reject = table.rejects[0]
    assert reject["source_row"] == 3
    assert "payment_number" in reject["reason"]
    assert reject["raw"]["Invoice Number"] == "INV-2"
    # The rejected row's amount is excluded from the control total.
    assert table.control_total == Decimal("349.49")


def test_duplicate_keys_and_null_amounts_are_diagnosed_not_dropped():
    _, rows, headers, sha = _golden_case()
    rows = [dict(r) for r in rows]
    rows[2]["Check No"] = "1001"        # duplicate payment number
    rows[2]["Paid Amount"] = "n/a"      # unparseable amount
    table = normalize_table(rows, _approved(rows, headers, sha))
    assert len(table.records) == 3      # diagnosed, not silently dropped
    assert table.diagnostics["duplicate_keys"] == ["1001"]
    assert table.diagnostics["duplicate_key_rows"] == 2
    assert table.diagnostics["null_amount_rows"] == 1


def test_reconciliation_receipt_carries_counts_and_digest():
    _, rows, headers, sha = _golden_case()
    table = normalize_table(rows, _approved(rows, headers, sha),
                            source_file="payments.csv")
    receipt = table.reconciliation()
    assert receipt["rows_in"] == 3
    assert receipt["rows_loaded"] == 3
    assert receipt["rows_rejected"] == 0
    assert receipt["control_total"] == "1599.99"
    assert len(receipt["output_digest"]) == 64
    # Deterministic: same rows + same spec -> same digest.
    again = normalize_table(rows, _approved(rows, headers, sha),
                            source_file="payments.csv")
    assert again.output_digest == table.output_digest


# ------------------------------------------------------------ parsing edges

def test_accounting_text_parses_exactly():
    assert parse_decimal("(1,250.50)") == Decimal("-1250.50")
    assert parse_decimal("$99.10") == Decimal("99.10")
    assert parse_decimal("-") is None
    assert parse_decimal("") is None
    assert parse_decimal("0.30") == Decimal("0.30")  # no float drift


def test_engine_view_projects_decimals_to_floats():
    _, rows, headers, sha = _golden_case()
    table = normalize_table(rows, _approved(rows, headers, sha))
    view = table.engine_view()
    assert isinstance(view.records[0]["payment_amount"], float)
    assert isinstance(table.records[0]["payment_amount"], Decimal)


# ------------------------------------------------- filename role inference

def test_harborline_filenames_all_infer_their_role():
    expected = {
        "vendors.csv": "Vendors", "employees.csv": "Employees",
        "purchase_orders.csv": "Purchase_orders",
        "goods_receipts.csv": "Goods_receipts", "vouchers.csv": "Vouchers",
        "payments.csv": "Payments", "bank.csv": "Bank", "gl.csv": "GL",
        "ap_control_balance.csv": "AP_control_balance",
        "value_flows.csv": "Value_flows",
    }
    assert {name: infer_role(name) for name in expected} == expected


def test_inference_survives_client_naming_noise():
    assert infer_role("Harborline_Bank_Statement_Dec2026.csv") == "Bank"
    assert infer_role("2026 AP Invoices (final).csv") == "Vouchers"
    assert infer_role("check_register_q4.csv") == "Payments"
    assert infer_role("C:/exports/general ledger FY26.csv") == "GL"
    # A compound name binds to what the file *is*, not what it mentions.
    assert infer_role("vendor_payments.csv") == "Payments"


def test_inference_refuses_to_guess():
    assert infer_role("data.csv") is None            # no hint at all
    assert infer_role("") is None
    assert infer_role("q4_export_v2.csv") is None    # naming noise only
