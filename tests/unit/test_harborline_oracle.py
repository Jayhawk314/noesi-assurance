# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""A reviewed case oracle: exact findings, cross-findings and designed silence."""

import json
import re
import csv
from decimal import Decimal
from pathlib import Path

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from procedures_ap.contracts import PROCEDURES
from workbench_api.demo import DEMO_PREPARER, seed_demo


CASE = Path(__file__).resolve().parents[2] / "case-studies" / "harborline-marine"
EXPECTED = json.loads((CASE / "instructor" / "EXPECTED-RUN.json").read_text(encoding="utf-8"))
PLANTED = json.loads((CASE / "instructor" / "PLANTED-EXCEPTIONS.json").read_text(encoding="utf-8"))


def test_every_planted_error_has_an_expected_outcome():
    assert len(PLANTED) == 40
    for item in PLANTED:
        procedure = item["procedure"]
        reference = item["reference"]
        if procedure == "ap.vendor_relational_twins":
            reference = reference.replace(" / ", "/")
        if procedure == "forensic.closed_value_flow":
            reference = "return_to_harborline"
        assert (reference in EXPECTED["findings"][procedure]
                or reference in EXPECTED["expected_silence"].get(procedure, [])), item

    # The deliberate silence must be a real difference in the case, and the
    # difference must fall within the declared 2% teaching tolerance.
    with (CASE / "data" / "payments.csv").open(newline="", encoding="utf-8") as handle:
        payment = next(row for row in csv.DictReader(handle)
                       if row["Payment Number"] == "PAY-2026-0025")
    with (CASE / "data" / "bank.csv").open(newline="", encoding="utf-8") as handle:
        bank = next(row for row in csv.DictReader(handle)
                    if row["Payment Number"] == "PAY-2026-0025")
    paid, cleared = Decimal(payment["Payment Amount"]), Decimal(bank["Amount"])
    assert Decimal("0") < abs(paid - cleared) / abs(cleared) < Decimal("0.02")


def _reference(procedure: str, verdict: dict) -> str:
    """Turn a domain key into a human case ID, without using reason wording."""
    key = " ".join(map(str, verdict["key"]))
    if procedure == "ap.document_chain" and "segregation_of_duties" in key:
        return "segregation_of_duties/payment_approval"
    if procedure == "forensic.closed_value_flow":
        assert "Harborline Marine Group" in verdict["reason"]
        return "return_to_harborline"
    if procedure == "ap.vendor_relational_twins":
        vendors = re.findall(r"V\d{4}", key)
        assert len(vendors) == 2, key
        return "/".join(vendors)
    for pattern in (r"PAY-2026-\d{4}", r"VCH-2026-\d{4}",
                    r"2026-12-31", r"V1042"):
        found = re.search(pattern, key)
        if found:
            return found.group()
    raise AssertionError(f"unrecognized {procedure} key: {key}")


def test_harborline_matches_every_reviewed_outcome(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    try:
        service = WorkbenchService(
            conn, ArtifactVault(tmp_path / "vault"), ensure_tenant(conn, "oracle"))
        eid = seed_demo(service, "local:oracle-partner")["engagement_id"]
        assert service.coverage(eid)["summary"]["executable"] == len(PROCEDURES)
        for contract in PROCEDURES:
            result = service.run_procedure(
                DEMO_PREPARER, eid, procedure_id=contract.procedure_id)
            assert result["status"] == "completed", result

        actual: dict[str, dict[str, str]] = {p: {} for p in EXPECTED["findings"]}
        for item in service.findings(eid):
            procedure = item["procedure_id"]
            verdict = item["verdict"]
            reference = _reference(procedure, verdict)
            assert reference not in actual[procedure], (procedure, reference)
            actual[procedure][reference] = verdict["verdict"]

        # Exact IDs and verdicts catch a missed item replaced by a new one,
        # even when each procedure and the overall run still have 52 findings.
        assert actual == EXPECTED["findings"]
        for procedure, references in EXPECTED["expected_silence"].items():
            assert all(reference not in actual[procedure] for reference in references)
        assert sum(map(len, actual.values())) == 52
    finally:
        conn.close()
