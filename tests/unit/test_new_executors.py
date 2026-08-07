"""The five executors added after Phase 0, and the coverage reconciliation
that keeps "executable" honest: a contract with no registered executor must
never compile as runnable, no matter how complete the data is."""

from datetime import date

import pytest

from procedures_ap.contracts import PROCEDURES, ProcedureContract
from procedures_ap.coverage import (
    apply_evidence_lifecycle, apply_selections, compile_coverage,
)
from procedures_ap.engines import execute_procedure, registered_procedures


# ------------------------------------------------- coverage reconciliation

def test_every_contract_has_a_registered_executor():
    contracted = {c.procedure_id for c in PROCEDURES}
    assert contracted <= registered_procedures(), (
        "a contract without an executor would compile as unsupported; "
        "either register the executor or retire the contract")


def _future_contract() -> ProcedureContract:
    return ProcedureContract(
        "ap.future_procedure", "Future procedure",
        "A contract shipped ahead of its executor.",
        "payables", ("occurrence",),
        {"Payments": ("payment_number",)})


def test_contract_without_executor_is_unsupported_not_executable():
    inventory = {"Payments": {"fields": ["payment_number"], "rows": 3}}
    coverage = compile_coverage(inventory, contracts=(_future_contract(),))
    row = coverage["procedures"][0]
    assert row["status"] == "unsupported"
    assert "unsupported_reason" in row
    assert coverage["summary"]["unsupported"] == 1
    assert coverage["summary"].get("executable", 0) == 0
    # No evidence request can unlock a procedure the build cannot run.
    assert coverage["evidence_requests"] == []


def test_unsupported_outranks_missing_data():
    coverage = compile_coverage({}, contracts=(_future_contract(),))
    assert coverage["procedures"][0]["status"] == "unsupported"


def test_evidence_lifecycle_never_promotes_unsupported():
    inventory = {"Payments": {"fields": ["payment_number"], "rows": 3}}
    coverage = apply_evidence_lifecycle(
        apply_selections(
            compile_coverage(inventory, contracts=(_future_contract(),)), {}),
        {})
    row = coverage["procedures"][0]
    assert row["status"] == "unsupported"
    assert row["execution_status"] == "not_run"


def test_unregistered_procedure_still_refuses_at_execution():
    with pytest.raises(ValueError, match="no incremental executor"):
        execute_procedure("ap.future_procedure", {}, {})


# --------------------------------------------- ap.payment_voucher_reference

def test_payment_voucher_reference_flags_missing_and_blank_references():
    tables = {
        "Payments": [
            {"payment_number": "P1", "voucher_number": "V1",
             "payment_amount": "100.00"},
            {"payment_number": "P2", "voucher_number": "V9",
             "payment_amount": "250.00"},
            {"payment_number": "P3", "voucher_number": "",
             "payment_amount": "75.00"},
        ],
        "Vouchers": [{"voucher_number": "V1"}],
    }
    findings, summary = execute_procedure(
        "ap.payment_voucher_reference", tables, {})
    assert summary == {"population": 3, "exceptions": 2}
    by_key = {f.key[-1]: f for f in findings}
    assert set(by_key) == {"P2", "P3"}
    assert all(f.verdict == "ORPHAN" for f in findings)
    assert "absent from the voucher population" in by_key["P2"].reason
    assert "records no voucher reference" in by_key["P3"].reason


# -------------------------------------------------- ap.voucher_po_reference

def test_voucher_po_reference_flags_unreachable_pos_not_non_po_spend():
    tables = {
        "Vouchers": [
            {"voucher_number": "V1", "po_number": "PO1",
             "voucher_amount": "100.00"},
            {"voucher_number": "V2", "po_number": "PO9",
             "voucher_amount": "40.00"},
            {"voucher_number": "V3", "po_number": "",
             "voucher_amount": "60.00"},
        ],
        "Purchase_orders": [{"po_number": "PO1"}],
    }
    findings, summary = execute_procedure("ap.voucher_po_reference", tables, {})
    assert summary == {"population": 3, "without_po_reference": 1,
                       "exceptions": 1}
    assert [f.key[-1] for f in findings] == ["V2"]
    assert findings[0].verdict == "ORPHAN"


# ------------------------------------------------- ap.segregation_of_duties

def test_segregation_of_duties_reports_self_approval_and_evidence_gaps():
    tables = {
        "Payments": [
            {"payment_number": "P1", "created_by": "E1", "approved_by": "E2",
             "payment_amount": "10.00"},
            {"payment_number": "P2", "created_by": "E1", "approved_by": "E1",
             "payment_amount": "20.00"},
            {"payment_number": "P3", "created_by": "E1", "approved_by": "",
             "payment_amount": "30.00"},
        ],
    }
    findings, summary = execute_procedure(
        "ap.segregation_of_duties", tables, {})
    assert summary == {"population": 3, "approvals_observed": 2,
                       "self_approved": 1, "exceptions": 2}
    verdicts = {f.key[-1]: f.verdict for f in findings}
    assert verdicts == {"P2": "CLASH", "P3": "ORPHAN"}
    clash = next(f for f in findings if f.key[-1] == "P2")
    assert "created and approved by the same actor" in clash.reason
    assert clash.evidence["check"] == "segregation_of_duties"


# ----------------------------------------------- ap.vendor_relational_twins

def test_vendor_twins_finds_identity_variants_and_ignores_distinct_names():
    tables = {
        "Vendors": [
            {"vendor_number": "V1", "vendor_name": "Harbor Marine Supply LLC"},
            {"vendor_number": "V2",
             "vendor_name": "Harbour Marine Supply, L.L.C."},
            {"vendor_number": "V3", "vendor_name": "Nautical Parts Inc"},
            {"vendor_number": "V4", "vendor_name": "Nautical Parts, Inc."},
            {"vendor_number": "V5", "vendor_name": "Chesapeake Rigging Ltd"},
        ],
    }
    findings, summary = execute_procedure(
        "ap.vendor_relational_twins", tables, {})
    pairs = {tuple(f.evidence["vendors"]) for f in findings}
    assert pairs == {("V1", "V2"), ("V3", "V4")}
    assert summary["population"] == 5
    assert summary["identity_pairs"] == 2
    assert summary["exceptions"] == 2
    assert all(f.verdict == "TENSION" for f in findings)
    assert all(f.policy == "ap.vendor_relational_twins.v1" for f in findings)


# ------------------------------------------------ ap.split_payment_review

SPLIT_TABLES = {
    "Payments": [
        {"payment_number": f"P{i}", "vendor_number": "V1",
         "payment_amount": "9800.00", "payment_date": f"2026-09-{14 + i * 2}"}
        for i in range(5)
    ],
}


def test_split_review_same_day_default_misses_multi_day_structuring():
    findings, summary = execute_procedure(
        "ap.split_payment_review", SPLIT_TABLES,
        {"split_threshold": "10000"})
    assert findings == []
    assert "window_days" not in summary


def test_split_review_window_clusters_across_days():
    findings, summary = execute_procedure(
        "ap.split_payment_review", SPLIT_TABLES,
        {"split_threshold": "10000", "split_window_days": "9"})
    assert summary["window_days"] == 9
    assert len(findings) == 1
    finding = findings[0]
    assert finding.verdict == "TENSION"
    assert "between 2026-09-14 and 2026-09-22" in finding.reason
    assert finding.evidence["payment_numbers"] == [
        "P0", "P1", "P2", "P3", "P4"]
    assert finding.evidence["total"] == 49000.0


def test_split_review_window_rejects_nonsense():
    with pytest.raises(ValueError, match="split_window_days"):
        execute_procedure(
            "ap.split_payment_review", SPLIT_TABLES,
            {"split_threshold": "10000", "split_window_days": "sideways"})


# ------------------------------------------------------- ap.document_chain

def test_document_chain_runs_with_generic_receipts_not_rockwood_ones():
    tables = {
        "Purchase_orders": [
            {"po_number": "PO1", "vendor_number": "V1", "po_amount": 100.0,
             "po_date": date(2026, 1, 5)},
        ],
        "Vouchers": [
            {"voucher_number": "VCH1", "po_number": "PO1",
             "vendor_number": "V1", "voucher_amount": 100.0,
             "voucher_date": date(2026, 1, 10)},
        ],
        "Payments": [
            {"payment_number": "P1", "voucher_number": "VCH1",
             "vendor_number": "V1", "payment_amount": 150.0,
             "payment_date": date(2026, 1, 20)},
            {"payment_number": "P2", "voucher_number": "VCH-GONE",
             "vendor_number": "V1", "payment_amount": 50.0,
             "payment_date": date(2026, 1, 21)},
        ],
    }
    findings, summary = execute_procedure("ap.document_chain", tables, {})
    assert summary["population"] == 2
    assert summary["exceptions"] == len(findings) == 2
    assert {f.policy for f in findings} == {"ap.document_chain.v1"}
    assert {f.domain for f in findings} == {"audit_procedure_run"}
    reasons = " | ".join(f.reason for f in findings)
    assert "amount difference" in reasons
    assert "references no observed voucher" in reasons
    # The Rockwood-specific scope note must not leak into generic runs.
    assert all("Rockwood" not in str(f.evidence) for f in findings)
