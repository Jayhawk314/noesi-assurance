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

from procedures_cycles import (
    accruals, cash, completion, controls, debt_equity, estimates, inventory, journal,
    payables, payroll, ppe, receivables, revenue, statements,
)
from procedures_cycles.common import jsonable, receipt, records
from procedures_cycles.contracts import CYCLE_CONTRACTS_BY_ID, SCOPE_OF

# Results changed after the independent-review fixes (empty-role refusals,
# customer-grain A/R populations, and line-complete disbursement inspection).
# Preserve that boundary in every sealed job manifest.
ENGINE_VERSION = "cycles-v2"

EXECUTORS: dict[str, Callable[[dict, dict], tuple[list[Receipt], dict]]] = {
    "fs.trial_balance_analytics": statements.trial_balance_analytics,
    "planning.performance_materiality": statements.performance_materiality,
    "controls.attribute_evaluation": controls.attribute_evaluation,
    "je.journal_entry_testing": journal.journal_entry_testing,
    "je.population_completeness": journal.population_completeness,
    "ar.listing_tie": receivables.listing_tie,
    "rev.sales_cutoff": revenue.sales_cutoff,
    "rev.credit_memos_after_period_end": revenue.credit_memos_after_period_end,
    "ar.confirmations_nonstatistical": receivables.confirmations_nonstatistical,
    "ar.confirmations_mus": receivables.confirmations_mus,
    "ar.confirmations_difference": receivables.confirmations_difference,
    "ap.unrecorded_liabilities_search": payables.unrecorded_liabilities_search,
    "payroll.register_tests": payroll.register_tests,
    "payroll.register_to_ledger": payroll.register_to_ledger,
    "cash.bank_reconciliation": cash.bank_reconciliation,
    "cash.interbank_transfers": cash.interbank_transfers,
    "inventory.count_listing_trace": inventory.count_listing_trace,
    "inventory.pricing_projection": inventory.pricing_projection,
    "ppe.rollforward": ppe.rollforward,
    "ppe.depreciation_recompute": ppe.depreciation_recompute,
    "ppe.additions_vouching": ppe.additions_vouching,
    "debt.rollforward_and_interest": debt_equity.rollforward_and_interest,
    "debt.covenants": debt_equity.covenants,
    "equity.rollforward": debt_equity.equity_rollforward,
    "accruals.rollforward": accruals.rollforward,
    "accruals.recompute": accruals.recompute,
    "estimates.retrospective_review": estimates.retrospective_review,
    "related_parties.matching": estimates.related_party_matching,
    "fs.adjusted_trial_balance": statements.adjusted_trial_balance,
    "completion.uncorrected_misstatements": statements.uncorrected_misstatements,
    "completion.subsequent_events": completion.subsequent_events,
    "completion.going_concern_indicators": completion.going_concern_indicators,
    "completion.representation_letter": completion.representation_letter,
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
    contract = CYCLE_CONTRACTS_BY_ID[procedure_id]
    empty_roles = [role for role in contract.required_fields
                   if not records(tables, role)]
    if empty_roles:
        findings = [
            receipt(
                procedure_id, ("empty_population", role), "AMBIGUOUS",
                f"{role} contains no accepted records; the procedure refuses to "
                "treat an empty or fully rejected file as a tested population",
                {"finding_class": "REFUSAL", "cycle": SCOPE_OF[procedure_id],
                 "role": role},
            )
            for role in empty_roles
        ]
        return findings, {
            "population": 0, "refused_empty_roles": empty_roles,
            "exceptions": len(findings),
        }
    findings, stats = executor(tables, policies or {})
    # The run summary is sealed as canonical JSON: Decimals and dates as text.
    return findings, jsonable(stats)
