# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Account-to-line mapping (K8): a client's own trial-balance labels mapped
to the statement lines procedures read, by label or by account."""

from decimal import Decimal as D

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from procedures_cycles.engines import execute_procedure
from procedures_cycles.statements import apply_line_mapping, suggest_line

TB = [  # a client's lead-schedule labels, none of them Noesi's own words
    {"account": "1000", "line": "Cash and equivalents", "balance": D("5000")},
    {"account": "1100", "line": "Accounts receivable", "balance": D("20000")},
    {"account": "1190", "line": "Accounts receivable", "balance": D("-1000")},
    {"account": "2000", "line": "Accounts payable", "balance": D("-40000")},
    {"account": "3000", "line": "Members' equity", "balance": D("-4000")},
    {"account": "4000", "line": "Revenue", "balance": D("-50000")},
    {"account": "6000", "line": "Operating expenses", "balance": D("70000")},
]


def test_suggestions_for_common_labels():
    assert suggest_line("Cash and equivalents") == "cash"
    assert suggest_line("Accounts receivable") == "receivables"
    assert suggest_line("Allowance for doubtful accounts") == "allowance"
    assert suggest_line("Cost of sales") == "cost_of_sales"
    assert suggest_line("Accounts payable") == "current_liabilities"
    assert suggest_line("Members' equity") == "equity"
    assert suggest_line("Revenue") == "sales"
    assert suggest_line("Operating expenses") == "operating_expense"
    assert suggest_line("Widgets") is None


def test_an_account_override_beats_its_label():
    mapping = {"label:accounts receivable": "receivables", "account:1190": "allowance"}
    lines = {r["account"]: r["line"] for r in apply_line_mapping(TB, mapping)}
    assert (lines["1100"], lines["1190"]) == ("receivables", "allowance")
    assert TB[2]["line"] == "Accounts receivable"          # originals untouched


def test_mapped_labels_let_going_concern_read_the_trial_balance():
    unmapped, _ = execute_procedure("completion.going_concern_indicators",
                                    {"Trial_balance": TB}, {})
    assert ("unclassified_accounts",) in {tuple(f.key[1:]) for f in unmapped}
    mapping = {"label:cash and equivalents": "cash",
               "label:accounts receivable": "receivables", "account:1190": "allowance",
               "label:accounts payable": "current_liabilities",
               "label:members' equity": "equity", "label:revenue": "sales",
               "label:operating expenses": "operating_expense"}
    import json
    mapped, stats = execute_procedure("completion.going_concern_indicators",
                                      {"Trial_balance": TB},
                                      {"line_mapping": json.dumps(mapping)})
    keys = {tuple(f.key[1:]) for f in mapped}
    assert ("unclassified_accounts",) not in keys
    # 5000 + 20000 - 1000 = 24000 against 40000: negative working capital;
    # 50000 - 70000: a loss
    assert {("negative_working_capital",), ("net_loss",)} <= keys


@pytest.fixture()
def service(tmp_path):
    conn = connect(tmp_path / "c.db")
    migrate(conn)
    svc = WorkbenchService(conn, ArtifactVault(tmp_path / "v"), ensure_tenant(conn, "m"))
    eid = svc.create_engagement("pa", "Acme", "2025-12-31")["engagement_id"]
    svc.assign_team("pa", eid, "pr", "preparer")
    svc.assign_team("pa", eid, "rv", "reviewer")
    yield svc, eid
    conn.close()


def test_the_workbench_lists_labels_records_mappings_and_passes_them_to_runs(service):
    svc, eid = service
    csv = ("Account,Description,Balance,Line\n"
           + "\n".join(f"{r['account']},x,{r['balance']},{r['line']}" for r in TB)
           ).encode("utf-8")
    art = svc.store_source("pr", eid, content=csv, media_type="text/csv",
                           original_name="trial_balance.csv")
    spec = svc.propose_source_mapping("pr", eid, role="Trial_balance",
                                      artifact_id=art["artifact_id"])
    svc.approve_source_mapping("rv", eid, spec["spec_id"])
    svc.normalize_source("pr", eid, spec["spec_id"])
    listing = svc.trial_balance_lines(eid)
    ar = next(i for i in listing["labels"] if i["label"] == "Accounts receivable")
    assert ar["suggestion"] == "receivables" and not ar["recognized"]
    svc.update_workflow("pr", eid, "line_mapping",
                        {"label": "Accounts receivable", "line": "receivables"})
    svc.update_workflow("pr", eid, "line_mapping", {"account": "1190", "line": "allowance"})
    with pytest.raises(ValueError, match="unknown statement line"):
        svc.update_workflow("pr", eid, "line_mapping", {"label": "Revenue", "line": "sales!"})
    listing = svc.trial_balance_lines(eid)
    assert listing["account_overrides"] == {"1190": "allowance"}
    document, _ = svc.workflow_document(eid)
    assert '"label:accounts receivable": "receivables"' in \
        svc._engagement_policies(eid, document)["line_mapping"]
