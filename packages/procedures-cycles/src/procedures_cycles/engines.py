# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Executor registry for the cycle procedures.

``execute_procedure`` dispatches to the AP registry first and then to this
one, so the job runner has a single entry point. The AP registry itself is
untouched: coverage for AP-only engagements still reconciles against it
alone.
"""

from __future__ import annotations

from typing import Callable

from assurance_domain.receipts import Receipt
from procedures_ap import engines as ap_engines

from procedures_cycles import cash, controls, inventory, payables, receivables, statements
from procedures_cycles.common import jsonable

ENGINE_VERSION = "cycles-v1"

EXECUTORS: dict[str, Callable[[dict, dict], tuple[list[Receipt], dict]]] = {
    "fs.trial_balance_analytics": statements.trial_balance_analytics,
    "planning.performance_materiality": statements.performance_materiality,
    "controls.attribute_evaluation": controls.attribute_evaluation,
    "ar.listing_tie": receivables.listing_tie,
    "ar.confirmations_nonstatistical": receivables.confirmations_nonstatistical,
    "ar.confirmations_mus": receivables.confirmations_mus,
    "ar.confirmations_difference": receivables.confirmations_difference,
    "ap.unrecorded_liabilities_search": payables.unrecorded_liabilities_search,
    "cash.bank_reconciliation": cash.bank_reconciliation,
    "cash.interbank_transfers": cash.interbank_transfers,
    "inventory.count_listing_trace": inventory.count_listing_trace,
    "inventory.pricing_projection": inventory.pricing_projection,
    "fs.adjusted_trial_balance": statements.adjusted_trial_balance,
    "completion.uncorrected_misstatements": statements.uncorrected_misstatements,
}


def registered_procedures() -> frozenset[str]:
    """AP executors plus cycle executors — what this build can run."""
    return ap_engines.registered_procedures() | frozenset(EXECUTORS)


def execute_procedure(procedure_id: str, tables: dict,
                      policies: dict | None = None) -> tuple[list[Receipt], dict]:
    if procedure_id in ap_engines.EXECUTORS:
        return ap_engines.execute_procedure(procedure_id, tables, policies)
    executor = EXECUTORS.get(procedure_id)
    if executor is None:
        raise ValueError("no incremental executor is registered for this procedure")
    findings, stats = executor(tables, policies or {})
    # The run summary is sealed as canonical JSON: Decimals and dates as text.
    return findings, jsonable(stats)
