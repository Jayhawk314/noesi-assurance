# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Journal entry testing and population completeness on a planted listing."""

from datetime import date
from decimal import Decimal as D

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from procedures_cycles.engines import execute_procedure

PE = "2025-12-31"


def line(entry, account, amount, *, dated="2025-06-10", posted=None, by="ann",
         approved="bob", memo="monthly accrual"):
    debit, credit = (amount, None) if amount > 0 else (None, -amount)
    return {"entry_id": entry, "account": account, "debit": debit, "credit": credit,
            "entry_date": date.fromisoformat(dated),
            "posted_date": date.fromisoformat(posted or dated),
            "posted_by": by, "approved_by": approved, "description": memo}


# 2025-06-10 is a Tuesday; 2025-06-14 a Saturday.
JOURNAL = [
    line("E1", "6000", D("1250.00")), line("E1", "2100", D("-1250.00")),
    line("E2", "6000", D("900.00")), line("E2", "2100", D("-850.00")),       # unbalanced
    line("E3", "4000", D("-7300.00"), dated="2025-12-31", posted="2026-01-06"),
    line("E3", "1100", D("7300.00"), dated="2025-12-31", posted="2026-01-06"),
    line("E4", "6000", D("310.00"), dated="2025-06-14"),                      # Saturday
    line("E4", "2100", D("-310.00"), dated="2025-06-14"),
    line("E5", "6500", D("50000.00")), line("E5", "2100", D("-50000.00")),  # round
    line("E6", "6000", D("420.00"), by="zed"), line("E6", "2100", D("-420.00"), by="zed"),
    line("E7", "6000", D("615.00"), approved="ann"),                         # self-approved
    line("E7", "2100", D("-615.00"), approved="ann"),
    line("E8", "6000", D("88.00"), memo=""), line("E8", "2100", D("-88.00"), memo=""),
    line("E9", "6000", D("99.00"), dated="2026-01-03"),                       # next period
    line("E9", "2100", D("-99.00"), dated="2026-01-03"),
]
POLICIES = {"period_end": PE, "je_round_amount_threshold": "10000",
            "je_authorized_users": "ann, cara", "je_seldom_used_max": "1"}


def run(procedure, journal=JOURNAL, policies=POLICIES, tb=None):
    tables = {"Journal_entries": journal}
    if tb is not None:
        tables["Trial_balance"] = tb
    return execute_procedure(procedure, tables, policies)


def selected(findings):
    return {(f.key[1], f.key[2]) for f in findings}


def test_each_planted_characteristic_is_selected_and_nothing_else():
    findings, stats = run("je.journal_entry_testing")
    assert selected(findings) == {
        ("e2", "unbalanced"),
        ("e3", "posted_after_period_end"), ("e3", "seldom_used_account"),
        ("e4", "weekend_or_holiday"),
        ("e5", "round_amount"), ("e5", "seldom_used_account"),
        ("e6", "unauthorized_user"),
        ("e7", "self_approved"),
        ("e8", "no_description"),
    }
    assert stats["population"] == 8 and stats["dated_after_period_end"] == 1
    assert stats["not_performed"] == {}
    unbalanced = next(f for f in findings if f.key[2] == "unbalanced")
    assert unbalanced.verdict == "CLASH" and "differ by 50.00" in unbalanced.reason


def test_tests_without_their_data_or_policy_are_reported_not_performed():
    bare = [{k: v for k, v in row.items() if k in ("entry_id", "account", "debit",
                                                    "credit", "entry_date")}
            for row in JOURNAL]
    findings, stats = run("je.journal_entry_testing", bare, {"period_end": PE})
    assert set(stats["not_performed"]) == {
        "round_amount", "posted_after_period_end", "unauthorized_user",
        "self_approved", "seldom_used_account", "no_description"}
    # what can still be tested from the entry date alone still is
    assert selected(findings) == {("e2", "unbalanced"), ("e4", "weekend_or_holiday")}


def test_next_period_entries_do_not_make_an_account_look_common():
    # E5 is the only in-period entry to 6500; a next-period entry to 6500
    # (loaded for subsequent-events work) must not hide it.
    later = [line("E10", "6500", D("75.00"), dated="2026-01-05"),
             line("E10", "2100", D("-75.00"), dated="2026-01-05")]
    findings, stats = run("je.journal_entry_testing", JOURNAL + later)
    assert ("e5", "seldom_used_account") in selected(findings)
    assert stats["dated_after_period_end"] == 2


def test_holidays_are_the_auditors_list():
    findings, _ = run("je.journal_entry_testing",
                      policies={**POLICIES, "je_holidays": "2025-06-10"})
    assert ("e1", "weekend_or_holiday") in selected(findings)


# ------------------------------------------------ population completeness
def tb(**over):
    """Prior and current balances (debit positive); P&L closed to 3200."""
    rows = {  # account: (prior, current)
        "1100": (D("10000"), D("17300")),      # + E3
        "2100": (D("-5000"), D("-58533")),     # credits of E1, E2, E4-E8
        "3200": (D("-20000"), D("-24000")),    # retained earnings: + prior P&L (-4000)
        "4000": (D("-30000"), D("-7300")),     # revenue: current = activity
        "6000": (D("26000"), D("3533")),       # expenses: 1250+850+310+420+615+88
        "6500": (D("0"), D("50000")),
    }
    rows.update(over)
    return [{"account": a, "balance": c, "prior_balance": p} for a, (p, c) in rows.items()]


def test_a_complete_listing_rolls_every_account_forward():
    journal = [r for r in JOURNAL if r["entry_id"] != "E2"] + [
        line("E2", "6000", D("850.00")), line("E2", "2100", D("-850.00"))]
    findings, stats = run("je.population_completeness", journal, tb=tb())
    assert findings == []
    assert stats["closed_to"] == "3200"
    assert set(stats["income_statement_accounts_closed"]) == {"4000", "6000"}


def test_a_missing_entry_breaks_the_rollforward_of_its_accounts():
    journal = [r for r in JOURNAL if r["entry_id"] not in ("E2", "E5")] + [
        line("E2", "6000", D("850.00")), line("E2", "2100", D("-850.00"))]
    findings, _ = run("je.population_completeness", journal, tb=tb())
    assert {(f.key[1], f.verdict) for f in findings} == {
        ("6500", "CLASH"), ("2100", "CLASH")}


# ------------------------------------------------ through the workbench
CSV = (
    "Num,Date,Account,Debit,Credit,Memo,Created By\n"
    "J1,2025-06-10,6000,1250.00,,accrual,ann\n"
    "J1,2025-06-10,2100,,1250.00,accrual,ann\n"
    "J2,2025-06-14,6000,310.00,,weekend fix,ann\n"
    "J2,2025-06-14,2100,,310.00,weekend fix,ann\n"
).encode("utf-8")


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "control.db")
    migrate(conn)
    yield WorkbenchService(conn, ArtifactVault(tmp_path / "vault"),
                           ensure_tenant(conn, "je"))
    conn.close()


def test_journal_entry_scope_runs_from_a_plain_export(service):
    eid = service.create_engagement("pa", "Acme", PE)["engagement_id"]
    service.assign_team("pa", eid, "pr", "preparer")
    service.assign_team("pa", eid, "rv", "reviewer")
    service.update_workflow("pa", eid, "cycles", {"cycles": ["journal_entries"]})
    art = service.store_source("pr", eid, content=CSV, media_type="text/csv",
                               original_name="journal entries.csv")
    prop = service.propose_source_mapping("pr", eid, role="Journal_entries",
                                          artifact_id=art["artifact_id"])
    assert {"entry_id", "entry_date", "account", "debit", "credit", "description",
            "posted_by"} <= set(prop["column_map"])
    service.approve_source_mapping("rv", eid, prop["spec_id"])
    service.normalize_source("pr", eid, prop["spec_id"])
    rows = {r["procedure_id"]: r["status"] for r in service.coverage(eid)["procedures"]}
    assert rows["je.journal_entry_testing"] == "executable"
    assert rows["je.population_completeness"] == "blocked"   # no trial balance yet
    run_ = service.run_procedure("pr", eid, procedure_id="je.journal_entry_testing")
    assert run_["status"] == "completed" and run_["findings"] == 1   # the Saturday entry


def test_manual_sources_confine_no_description_to_manual_entries():
    typed = [dict(row, source="Journal Entry") for row in JOURNAL]
    invoice = [line("E20", "1100", D("64.00"), memo=""), line("E20", "4000", D("-64.00"), memo="")]
    unknown = [line("E21", "6000", D("12.00"), memo=""), line("E21", "2100", D("-12.00"), memo="")]
    listing = typed + [dict(r, source="Invoice") for r in invoice] + unknown
    policies = {**POLICIES, "je_manual_sources": "journal entry, general journal"}
    findings, stats = run("je.journal_entry_testing", listing, policies)
    flagged = {e for e, t in selected(findings) if t == "no_description"}
    # the manual entry and the one whose source is unknown; not the invoice
    assert flagged == {"e8", "e21"}
    assert stats["no_description_not_manual"] == 1
    # without the policy every entry is tested, as before
    findings, _ = run("je.journal_entry_testing", listing)
    assert {e for e, t in selected(findings) if t == "no_description"} == {"e8", "e20", "e21"}


def test_manual_sources_without_a_source_column_is_not_performed():
    findings, stats = run("je.journal_entry_testing",
                          policies={**POLICIES, "je_manual_sources": "Journal Entry"})
    assert "source" in stats["not_performed"]["no_description"]
    assert not any(t == "no_description" for _, t in selected(findings))
