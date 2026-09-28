# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Versioned cycle procedure contracts.

Same ``ProcedureContract`` shape as the eleven AP contracts, so coverage,
evidence requests, jobs and the lock treat them alike. Each belongs to a
*scope*: an engagement sees a scope's contracts only after its partner puts
that cycle in the engagement (workflow section ``cycles``). With no scope
recorded, coverage is exactly the AP-only coverage it always was.

``period_end`` and ``materiality`` are supplied by the engagement record
(its period end and its approved materiality), not typed in again.
"""

from __future__ import annotations

from procedures_ap.contracts import ProcedureContract

SCOPES = ("planning", "controls", "journal_entries", "receivables", "payables", "cash",
          "inventory", "completion")

CYCLE_PROCEDURES: tuple[ProcedureContract, ...] = (
    ProcedureContract(
        "fs.trial_balance_analytics", "Trial balance analytics",
        "Foot the trial balance, compute standard ratios for both years, and flag "
        "movements above the approved threshold for explanation.",
        "planning", ("completeness", "accuracy", "valuation"),
        {"Trial_balance": ("account", "balance", "line")},
        evidence_source="client working trial balance with auditor line classification",
        denominator_role="Trial_balance",
        limitations="A ratio or movement is a question for inquiry, not evidence of "
                    "misstatement. Movement flags need analytics_threshold_pct.",
    ),
    ProcedureContract(
        "planning.performance_materiality", "Performance materiality allocation",
        "Check allocated performance materiality against the approved multiple of "
        "overall materiality.",
        "planning", ("accuracy",),
        {"Performance_materiality": ("account", "performance_materiality")},
        required_policies=("materiality", "pm_allocation_multiple"),
        evidence_source="auditor planning workpaper",
        denominator_role="Performance_materiality",
        limitations="Checks arithmetic and ceilings only; the allocation is judgment.",
    ),
    ProcedureContract(
        "controls.attribute_evaluation", "Tests of controls: attribute evaluation",
        "Compute CUER (statistical) or SER plus judged sampling risk (nonstatistical) "
        "for each attribute and compare it with the tolerable exception rate.",
        "controls", ("occurrence", "accuracy", "classification", "cutoff"),
        {"Attribute_tests": ("attribute", "sample_size", "deviations", "tolerable_rate")},
        evidence_source="auditor attribute-testing results",
        denominator_role="Attribute_tests",
        limitations="The deviations counted are the auditor's findings; each deviation "
                    "needs qualitative evaluation the rate cannot give.",
    ),
    ProcedureContract(
        "je.journal_entry_testing", "Journal entry testing",
        "Select journal entries with fraud-risk characteristics — unbalanced, posted "
        "after period end, weekend or holiday, round amounts, unauthorized or self-"
        "approving users, seldom-used accounts, no description — for inquiry and "
        "vouching.",
        "journal_entries", ("occurrence", "completeness", "accuracy", "cutoff",
                            "authorization"),
        {"Journal_entries": ("entry_id", "account", "entry_date")},
        required_policies=("period_end",),
        evidence_source="the client's complete journal entry listing for the period, "
                        "extracted from the accounting system",
        denominator_role="Journal_entries",
        limitations="A selected entry is a lead for inquiry and vouching, not a "
                    "misstatement. Tests whose data or policy is missing are reported "
                    "as not performed. Pair with population completeness.",
    ),
    ProcedureContract(
        "je.population_completeness", "Journal entry population completeness",
        "Roll each account's prior-year balance forward with the period's journal "
        "activity to the current trial balance, so the entries tested are the whole "
        "population.",
        "journal_entries", ("completeness",),
        {"Journal_entries": ("entry_id", "account", "entry_date"),
         "Trial_balance": ("account", "balance", "prior_balance")},
        required_policies=("period_end",),
        evidence_source="the journal entry listing and the client's trial balance "
                        "with prior-year balances",
        denominator_role="Trial_balance",
        limitations="Cannot see entries dated before the period began. An account whose "
                    "balance equals the period's activity is treated as an income-"
                    "statement account that closed; one equity account may take the "
                    "prior year's closing.",
    ),
    ProcedureContract(
        "ar.listing_tie", "AR listing to general ledger",
        "Tie the aged AR listing to the trial balance, test the aging's arithmetic, and "
        "recompute the allowance from the aging when rates are approved.",
        "receivables", ("completeness", "accuracy", "valuation"),
        {"AR_listing": ("customer_number", "balance"),
         "Trial_balance": ("account", "balance", "line")},
        evidence_source="client aged receivables listing and trial balance",
        denominator_role="AR_listing",
    ),
    ProcedureContract(
        "ar.confirmations_nonstatistical", "AR confirmations: nonstatistical evaluation",
        "Project client misstatements found in confirmations to the untested stratum "
        "and compare with tolerable misstatement.",
        "receivables", ("existence", "accuracy"),
        {"AR_listing": ("customer_number", "balance"),
         "Confirmations": ("customer_number", "confirmed_value", "classification")},
        required_policies=("ar_tolerable_misstatement",),
        evidence_source="confirmation replies received directly by the auditor",
        denominator_role="AR_listing",
        default_selected=False,
        limitations="Unclassified differences are refused. Sampling risk is judged.",
    ),
    ProcedureContract(
        "ar.confirmations_mus", "AR confirmations: monetary-unit sampling evaluation",
        "Compute the upper misstatement limit from confirmation taintings and compare "
        "with tolerable misstatement.",
        "receivables", ("existence", "accuracy"),
        {"AR_listing": ("customer_number", "balance"),
         "Confirmations": ("customer_number", "confirmed_value", "classification")},
        required_policies=("ar_tolerable_misstatement", "ar_risk_incorrect_acceptance",
                           "mus_interval"),
        evidence_source="confirmation replies received directly by the auditor",
        denominator_role="AR_listing",
        default_selected=False,
        limitations="Overstatement bound only; understatements are listed separately.",
    ),
    ProcedureContract(
        "ar.confirmations_difference", "AR confirmations: difference estimation",
        "Estimate total misstatement and its confidence limits from confirmation "
        "differences and compare with tolerable misstatement.",
        "receivables", ("existence", "accuracy"),
        {"AR_listing": ("customer_number", "balance"),
         "Confirmations": ("customer_number", "confirmed_value", "classification")},
        required_policies=("ar_tolerable_misstatement", "ar_risk_incorrect_acceptance"),
        evidence_source="confirmation replies received directly by the auditor",
        denominator_role="AR_listing",
        default_selected=False,
        limitations="Valid only for a random sample; few differences make the "
                    "normal approximation weak.",
    ),
    ProcedureContract(
        "ap.unrecorded_liabilities_search", "Search for unrecorded liabilities",
        "Select subsequent disbursements, and for each inspected one test whether the "
        "liability belonged on the year-end payables listing.",
        "payables", ("completeness", "cutoff", "accuracy"),
        {"Vouchers": ("voucher_number", "voucher_amount"),
         "Payments": ("payment_number", "voucher_number", "payment_amount"),
         "Disbursement_inspection": ("payment_number", "liability_date")},
        required_policies=("period_end", "search_threshold"),
        evidence_source="subsequent check register; receiving reports and invoices "
                        "inspected by the auditor",
        policy_version="v1",
        denominator_role="Payments",
        limitations="Cannot see liabilities never paid after year-end; unpaid invoices, "
                    "vendor statements and receiving records are separate searches.",
    ),
    ProcedureContract(
        "cash.bank_reconciliation", "Bank reconciliation re-performance",
        "Re-foot each bank reconciliation and test outstanding checks and deposits in "
        "transit against the cutoff bank statement.",
        "cash", ("existence", "accuracy", "cutoff"),
        {"Bank_reconciliation": ("account", "item_type", "amount"),
         "Cutoff_statement": ("account", "reference", "amount")},
        required_policies=("period_end",),
        evidence_source="client reconciliation; cutoff statement received directly "
                        "from the bank",
        denominator_role="Bank_reconciliation",
    ),
    ProcedureContract(
        "cash.interbank_transfers", "Interbank transfers (kiting)",
        "Test each transfer's book and bank dates against period end and the "
        "reconciliations.",
        "cash", ("existence", "cutoff"),
        {"Transfers": ("transfer_id", "amount", "from_account", "to_account",
                       "disbursed_books", "disbursed_bank", "received_books",
                       "received_bank"),
         "Bank_reconciliation": ("account", "item_type", "amount")},
        required_policies=("period_end",),
        evidence_source="interbank transfer schedule traced to books and bank",
        denominator_role="Transfers",
        limitations="Covers the transfers scheduled; an omitted transfer is invisible "
                    "to it.",
    ),
    ProcedureContract(
        "inventory.count_listing_trace", "Count ↔ final listing, both directions",
        "Trace every counted item to the final listing (completeness) and every listed "
        "item to the count (existence), comparing identifying details.",
        "inventory", ("existence", "completeness", "accuracy"),
        {"Inventory_listing": ("stock_number",), "Inventory_count": ("stock_number",)},
        evidence_source="final inventory listing; count records from an observed count",
        denominator_role="Inventory_listing",
        limitations="Relies on count records from a count the auditor observed; it does "
                    "not replace observation.",
    ),
    ProcedureContract(
        "inventory.pricing_projection", "Inventory pricing test projection",
        "Project the net pricing misstatement found in the sample to the listing and "
        "compare with tolerable misstatement.",
        "inventory", ("valuation", "accuracy"),
        {"Inventory_listing": ("stock_number", "cost"),
         "Pricing_tests": ("stock_number", "recorded_cost", "audited_cost")},
        required_policies=("inventory_tolerable_misstatement",),
        evidence_source="vendor invoices inspected by the auditor",
        denominator_role="Inventory_listing",
        limitations="Ratio projection; obsolescence and net realizable value are "
                    "separate judgments.",
    ),
    ProcedureContract(
        "fs.adjusted_trial_balance", "Adjusted trial balance",
        "Check that proposed adjusting entries balance, apply them to the trial "
        "balance, and re-foot.",
        "completion", ("accuracy", "presentation"),
        {"Trial_balance": ("account", "balance"),
         "Adjusting_entries": ("entry_id", "account")},
        evidence_source="proposed adjusting entries agreed with the client",
        denominator_role="Trial_balance",
        limitations="Income tax is not recomputed.",
    ),
    ProcedureContract(
        "completion.uncorrected_misstatements", "Summary of uncorrected misstatements",
        "Total uncorrected misstatements by statement line and compare each total with "
        "materiality.",
        "completion", ("accuracy", "presentation"),
        {"Misstatements": ("description", "identified")},
        required_policies=("materiality",),
        evidence_source="auditor summary of uncorrected misstatements",
        denominator_role="Misstatements",
        limitations="Reports what remains for further misstatement; the opinion is "
                    "the partner's decision.",
    ),
)

SCOPE_OF: dict[str, str] = {
    "fs.trial_balance_analytics": "planning",
    "planning.performance_materiality": "planning",
    "controls.attribute_evaluation": "controls",
    "je.journal_entry_testing": "journal_entries",
    "je.population_completeness": "journal_entries",
    "ar.listing_tie": "receivables",
    "ar.confirmations_nonstatistical": "receivables",
    "ar.confirmations_mus": "receivables",
    "ar.confirmations_difference": "receivables",
    "ap.unrecorded_liabilities_search": "payables",
    "cash.bank_reconciliation": "cash",
    "cash.interbank_transfers": "cash",
    "inventory.count_listing_trace": "inventory",
    "inventory.pricing_projection": "inventory",
    "fs.adjusted_trial_balance": "completion",
    "completion.uncorrected_misstatements": "completion",
}

CYCLE_CONTRACTS_BY_ID = {c.procedure_id: c for c in CYCLE_PROCEDURES}

# Policies a team may set that no cycle contract requires.
OPTIONAL_POLICIES: tuple[str, ...] = (
    "analytics_threshold_pct", "analytics_threshold_amount", "ar_confidence_factor",
    "ar_expected_misstatement", "ar_estimated_sd", "ar_risk_incorrect_rejection",
    "search_interval", "search_start", "search_systematic_count",
    "pricing_sample_value", "ar_allowance_rates",
    "dit_max_days",
    "je_round_amount_threshold", "je_round_unit", "je_authorized_users",
    "je_seldom_used_max", "je_holidays",
)

# Supplied from the engagement record rather than typed as policies.
ENGAGEMENT_POLICIES: tuple[str, ...] = ("period_end", "materiality")


def contracts_for_scope(scope) -> tuple[ProcedureContract, ...]:
    """The cycle contracts an engagement with this scope should see."""
    wanted = {s for s in (scope or ()) if s in SCOPES}
    return tuple(c for c in CYCLE_PROCEDURES if SCOPE_OF[c.procedure_id] in wanted)


# Every assertion a risk may be recorded against: the AP contracts' set plus
# the cycles'. Mirrors the risk register's CHECK constraint (migration 8).
REGISTER_ASSERTIONS: tuple[str, ...] = (
    "occurrence", "existence", "completeness", "accuracy", "valuation", "cutoff",
    "classification", "presentation", "rights", "authorization")


def procedures_for_assertion_all(assertion: str) -> list[str]:
    """AP and cycle procedures whose contract addresses this assertion."""
    from procedures_ap.contracts import procedures_for_assertion
    return procedures_for_assertion(assertion) + [
        c.procedure_id for c in CYCLE_PROCEDURES if assertion in c.assertions]


# Which cycle(s) each optional policy serves, so a policy for a cycle that is
# not in scope can be refused instead of stored as an inert decision.
_OPTIONAL_POLICY_SCOPES: dict[str, set[str]] = {
    "analytics_threshold_pct": {"planning"}, "analytics_threshold_amount": {"planning"},
    "ar_confidence_factor": {"receivables"}, "ar_expected_misstatement": {"receivables"},
    "ar_estimated_sd": {"receivables"}, "ar_risk_incorrect_rejection": {"receivables"},
    "ar_allowance_rates": {"receivables"}, "search_interval": {"payables"},
    "search_start": {"payables"}, "search_systematic_count": {"payables"},
    "pricing_sample_value": {"inventory"}, "dit_max_days": {"cash"},
    "je_round_amount_threshold": {"journal_entries"}, "je_round_unit": {"journal_entries"},
    "je_authorized_users": {"journal_entries"}, "je_seldom_used_max": {"journal_entries"},
    "je_holidays": {"journal_entries"},
}


def policy_scopes(name: str) -> set[str]:
    """The cycles whose procedures use this policy (empty: not a cycle policy)."""
    owners = {SCOPE_OF[c.procedure_id] for c in CYCLE_PROCEDURES
              if name in c.required_policies}
    return owners | _OPTIONAL_POLICY_SCOPES.get(name, set())
