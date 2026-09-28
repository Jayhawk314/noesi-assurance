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
    # A mapped column is not the same as a value on every row: a blank
    # required value must not turn into a zero or a skipped row (review
    # 2026-09-28, F2). Rows missing one are set aside, named, and not tested.
    tables, incomplete, excluded = _drop_incomplete_rows(procedure_id, contract, tables)
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
        findings = incomplete + findings
        return findings, {
            "population": 0, "refused_empty_roles": empty_roles,
            "excluded_incomplete_rows": excluded, "exceptions": len(findings),
        }
    findings, stats = executor(tables, policies or {})
    if incomplete:
        findings = incomplete + list(findings)
        stats = {**stats, "excluded_incomplete_rows": excluded,
                 "exceptions": stats.get("exceptions", 0) + len(incomplete)}
    # The run summary is sealed as canonical JSON: Decimals and dates as text.
    return findings, jsonable(stats)


# Required fields whose blank value the procedure itself reports, more
# precisely than an incomplete-row refusal would: no shipping evidence; an
# item measured another way listed as not recomputed; an unclassified or
# unanswered confirmation refused as such; an inspection concluded by
# reference rather than by date; an estimate not yet resolved.
# A confirmation's classification may be blank when there is no difference;
# the executor refuses an unclassified difference. Its confirmed value may
# not: a blank one would enter the projection as zero (re-review RR2).
_CONFIRMATIONS = frozenset({"classification"})
VALUE_OPTIONAL: dict[str, frozenset[str]] = {
    "ar.confirmations_nonstatistical": _CONFIRMATIONS,
    "ar.confirmations_mus": _CONFIRMATIONS,
    "ar.confirmations_difference": _CONFIRMATIONS,
    "ap.unrecorded_liabilities_search": frozenset({"liability_date"}),
    "estimates.retrospective_review": frozenset({"prior_estimate", "outcome"}),
    "rev.sales_cutoff": frozenset({"ship_date"}),
    "accruals.recompute": frozenset({"total_amount", "service_start", "service_end"}),
    "ppe.depreciation_recompute": frozenset({"useful_life_years",
                                             "depreciation_expense"}),
}


def _blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _drop_incomplete_rows(procedure_id: str, contract, tables: dict):
    tables = dict(tables)
    findings, excluded = [], {}
    optional = VALUE_OPTIONAL.get(procedure_id, frozenset())
    for role, fields in contract.required_fields.items():
        needed = [f for f in fields if f not in optional]
        keep, bad = [], []
        for row in records(tables, role):
            (bad if any(_blank(row.get(f)) for f in needed) else keep).append(row)
        if not bad:
            continue
        tables[role] = keep
        excluded[role] = len(bad)
        missing = sorted({f for row in bad for f in needed if _blank(row.get(f))})
        findings.append(receipt(
            procedure_id, ("incomplete_rows", role), "AMBIGUOUS",
            f"{len(bad)} {role} row(s) have no value for {', '.join(missing)}; they "
            "were not tested. Supply the values or record why the gap is accepted",
            {"finding_class": "REFUSAL", "cycle": SCOPE_OF[procedure_id],
             "role": role, "fields": missing,
             "rows": [row.get("source_row") for row in bad[:50]]}))
    return tables, findings, excluded
