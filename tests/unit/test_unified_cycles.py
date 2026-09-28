# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Cycle findings are placed in their own area in the unified view, not
"unassigned"; findings the older rules place keep their place."""

from datetime import date
from decimal import Decimal as D

from procedures_ap import unified
from procedures_cycles.common import receipt
from procedures_cycles.contracts import CYCLE_PROCEDURES, SCOPE_OF
from procedures_cycles.engines import execute_procedure


def test_every_cycle_procedure_lands_in_an_area():
    for contract in CYCLE_PROCEDURES:
        pid = contract.procedure_id
        tag = unified.classify_verdict(receipt(
            pid, ("x",), "TENSION", "r",
            {"finding_class": "CONJECTURE", "cycle": SCOPE_OF[pid]}))
        assert tag["cycle"] != "unassigned", pid
        if not pid.startswith(("fs.", "ap.")):
            assert tag["cycle"] == SCOPE_OF[pid], pid


def test_a_real_payroll_finding_is_tagged_payroll():
    findings, _ = execute_procedure(
        "payroll.register_tests",
        {"Payroll_register": [{"employee_id": "E9", "pay_date": date(2025, 6, 1),
                               "gross": D("100"), "net": D("80")}],
         "Payroll_master": [{"employee_id": "E1"}]}, {})
    assert {unified.classify_verdict(f)["cycle"] for f in findings} == {"payroll"}


def test_older_placements_are_unchanged():
    fs = receipt("fs.trial_balance_analytics", ("x",), "TENSION", "r",
                 {"finding_class": "CONJECTURE", "cycle": "planning"})
    assert unified.classify_verdict(fs)["cycle"] == "financial_statements"
    ap = receipt("ap.unrecorded_liabilities_search", ("x",), "TENSION", "r",
                 {"finding_class": "CONJECTURE", "cycle": "payables"})
    assert unified.classify_verdict(ap)["cycle"] == "payables"
