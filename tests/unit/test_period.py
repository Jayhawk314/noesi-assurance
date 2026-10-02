# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The engagement's period start: set by the partner, used by the procedures
instead of assuming twelve months (a first year, a changed year end)."""

from datetime import date
from decimal import Decimal as D

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from procedures_cycles.engines import execute_procedure

# A nine-month first year: 2025-04-01 to 2025-12-31.
SHORT = {"period_end": "2025-12-31", "period_start": "2025-04-01"}


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    svc = WorkbenchService(conn, ArtifactVault(tmp_path / "vault"),
                           ensure_tenant(conn, "period"))
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    yield svc, eid
    conn.close()


def test_the_partner_records_the_period_start_and_procedures_receive_it(service):
    svc, eid = service
    document, _ = svc.workflow_document(eid)
    assert "period_start" not in svc._engagement_policies(eid, document)
    svc.update_workflow("pa", eid, "period", {"start": "2025-04-01"})
    document, _ = svc.workflow_document(eid)
    assert svc._engagement_policies(eid, document)["period_start"] == "2025-04-01"
    svc.update_workflow("pa", eid, "period", {"start": ""})        # cleared
    document, _ = svc.workflow_document(eid)
    assert "period_start" not in svc._engagement_policies(eid, document)


@pytest.mark.parametrize("start, message", [
    ("2026-01-01", "must be before the period end"),
    ("2023-12-01", "more than 24 months"),
    ("April 2025", "is not a date"),
    # review 2026-09-28, F5: trailing text was truncated away and accepted
    ("2025-04-01garbage", "is not a date"),
    ("2025-04-01T99:99:99", "is not a date"),
])
def test_an_impossible_period_start_is_refused(service, start, message):
    svc, eid = service
    with pytest.raises(ValueError, match=message):
        svc.update_workflow("pa", eid, "period", {"start": start})


def test_the_period_start_is_never_set_as_a_policy(service):
    svc, eid = service
    with pytest.raises(ValueError, match="engagement record"):
        svc.update_workflow("pa", eid, "policy",
                            {"name": "period_start", "value": "2025-04-01"})


def test_payroll_counts_only_the_short_periods_pay():
    register = [{"employee_id": "E1", "pay_date": date(2025, m, 15), "gross": D("1000")}
                for m in range(1, 13)]
    tb = [{"account": "6100", "balance": D("9000")}]
    tables = {"Payroll_register": register, "Trial_balance": tb}
    findings, stats = execute_procedure(
        "payroll.register_to_ledger", tables,
        {**SHORT, "payroll_expense_accounts": "6100"})
    # April-December: nine payments of 1000
    assert stats["register_gross"] == "9000.00" and findings == []
    assert stats["payments_outside_period"] == 3


def test_ppe_uses_the_short_period_for_additions_and_depreciation():
    assets = [
        # acquired before the short period began: not an addition
        {"asset_id": "A1", "cost": D("1200"), "acquired_date": date(2025, 2, 1),
         "useful_life_years": "1", "depreciation_expense": D("900.00"), "method": "SL"},
        # an addition; full month: April-December = 9 months of 1200/year
        {"asset_id": "A2", "cost": D("1200"), "acquired_date": date(2025, 4, 1),
         "useful_life_years": "1", "depreciation_expense": D("900.00"), "method": "SL"},
    ]
    vouched = [{"asset_id": "A2", "vouched_amount": D("1200"), "capitalize": "yes"}]
    _, stats = execute_procedure("ppe.additions_vouching",
                                 {"Fixed_assets": assets, "Additions_vouching": vouched},
                                 SHORT)
    assert stats["additions_value"] == "1200.00"          # A2 only
    findings, _ = execute_procedure(
        "ppe.depreciation_recompute", {"Fixed_assets": assets},
        {**SHORT, "ppe_depreciation_convention": "full_month"})
    # A1: February-January life, the period holds April-December = 9 months = 900
    assert findings == []


def test_journal_entries_before_the_period_start_are_outside_the_population():
    def line(entry, dated, account, amount):
        return {"entry_id": entry, "account": account, "entry_date": dated,
                "debit": amount if amount > 0 else None,
                "credit": -amount if amount < 0 else None}
    journal = [line("E1", date(2025, 2, 11), "6000", D("50")),
               line("E1", date(2025, 2, 11), "2000", D("-40")),        # unbalanced, but earlier
               line("E2", date(2025, 5, 13), "6000", D("75")),
               line("E2", date(2025, 5, 13), "2000", D("-75"))]
    findings, stats = execute_procedure("je.journal_entry_testing",
                                        {"Journal_entries": journal}, SHORT)
    assert findings == []
    assert stats["dated_before_period_start"] == 1 and stats["population"] == 1
