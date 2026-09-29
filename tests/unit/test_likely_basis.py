# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""What "likely" means on a summary of uncorrected misstatements (K13): the
whole likely misstatement, or the projection beyond the identified amount.
The partner's setting decides; otherwise the rows' statement-line columns
may show it; otherwise the engine says it could not tell."""

from decimal import Decimal as D

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from procedures_cycles.engines import execute_procedure

BEYOND = [  # likely is the projection beyond identified; lines carry the sum
    {"description": "pricing", "identified": D("2250"), "likely": D("0"),
     "current_assets": D("-2250"), "income_before_taxes": D("-2250")},
    {"description": "freight", "identified": D("620"), "likely": D("213.73"),
     "current_assets": D("-833.73"), "income_before_taxes": D("-833.73")},
]
AS_TOTAL = [{"description": "freight", "identified": D("620"), "likely": D("833.73"),
             "current_assets": D("-833.73"), "income_before_taxes": D("-833.73")}]
NO_LINES = [{"description": "freight", "identified": D("620"), "likely": D("213.73")}]


def run(rows, **policies):
    return execute_procedure("completion.uncorrected_misstatements",
                             {"Misstatements": rows}, {"materiality": "15000", **policies})


def keys(findings):
    return {f.key[1:] for f in findings}


def test_the_line_columns_show_likely_is_beyond_identified():
    findings, stats = run(BEYOND)
    assert stats["likely_basis"] == "beyond_identified"
    assert stats["likely_basis_source"] == "statement-line columns"
    assert stats["totals"]["likely"] == "3083.73"  # 2250 + 833.73, not 213.73
    assert not any(k[0] == "likely_below_identified" for k in keys(findings))


def test_the_line_columns_show_likely_is_the_total():
    findings, stats = run(AS_TOTAL)
    assert stats["likely_basis"] == "total" and stats["totals"]["likely"] == "833.73"
    assert findings == []


def test_a_setting_the_rows_contradict_is_flagged():
    findings, stats = run(BEYOND, misstatement_likely_basis="total")
    assert stats["likely_basis_source"] == "policy"
    assert ("likely_basis_contradicted", "freight") in keys(findings)


def test_without_setting_or_evidence_the_engine_says_it_could_not_tell():
    findings, stats = run(NO_LINES)
    assert stats["likely_basis_source"] == "assumed"
    assert ("likely_basis_unknown",) in keys(findings)
    findings, stats = run(NO_LINES, misstatement_likely_basis="beyond_identified")
    assert stats["totals"]["likely"] == "833.73" and findings == []


def test_the_setting_is_checked_when_set(tmp_path):
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    svc = WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "m"))
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    svc.update_workflow("pa", eid, "cycles", {"cycles": ["completion"]})
    with pytest.raises(ValueError, match="'total' or 'beyond_identified'"):
        svc.update_workflow("pa", eid, "policy",
                            {"name": "misstatement_likely_basis", "value": "aggregate"})
    svc.update_workflow("pa", eid, "policy",
                        {"name": "misstatement_likely_basis", "value": "beyond_identified"})
    conn.close()
