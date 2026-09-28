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

SCOPES = ("planning", "controls", "journal_entries", "receivables", "payables", "payroll",
          "cash", "inventory", "ppe", "debt_equity", "accruals", "estimates",
          "completion")

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
        limitations="Lines dated outside the period are left out and counted. An "
                    "account whose "
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
        "rev.sales_cutoff", "Sales cutoff and shipping evidence",
        "Compare each invoice's date with its shipping date around period end, and "
        "list invoices with no shipping evidence.",
        "receivables", ("cutoff", "occurrence"),
        {"Sales_invoices": ("invoice_number", "invoice_date", "amount", "ship_date")},
        required_policies=("period_end",),
        evidence_source="client sales invoice listing with shipping dates and "
                        "documents from the shipping records",
        denominator_role="Sales_invoices",
        limitations="Assumes title passes at shipment; FOB destination, bill-and-hold "
                    "and consignment terms are the auditor's contract reading.",
    ),
    ProcedureContract(
        "rev.credit_memos_after_period_end", "Credit memos after period end",
        "List credit memos issued after period end that reverse invoices from the "
        "period, and credit memos that match no invoice.",
        "receivables", ("occurrence", "cutoff", "valuation"),
        {"Credit_memos": ("memo_number", "memo_date", "amount"),
         "Sales_invoices": ("invoice_number", "invoice_date")},
        required_policies=("period_end",),
        evidence_source="client credit memo register after period end and the sales "
                        "invoice listing",
        denominator_role="Credit_memos",
        limitations="Sees only memos issued by the date of the register; the window "
                    "(rev_credit_memo_days) is the auditor's choice.",
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
        "payroll.register_tests", "Payroll register tests",
        "Re-perform gross and net pay, and list people paid who are not on the "
        "employee master, paid after termination, paid twice on one date, or sharing "
        "a bank account or address.",
        "payroll", ("occurrence", "accuracy", "existence"),
        {"Payroll_register": ("employee_id", "pay_date", "gross", "net"),
         "Payroll_master": ("employee_id",)},
        evidence_source="client payroll register and HR employee master",
        denominator_role="Payroll_register",
        limitations="A lead is not a finding: a payment after termination may be a "
                    "final check (payroll_final_pay_days sets the grace). Payroll tax "
                    "rates are not recomputed.",
    ),
    ProcedureContract(
        "payroll.register_to_ledger", "Payroll register to ledger",
        "Compare the period's gross pay in the register with the trial balance "
        "accounts the auditor names as wage expense.",
        "payroll", ("completeness", "accuracy"),
        {"Payroll_register": ("employee_id", "pay_date", "gross"),
         "Trial_balance": ("account", "balance")},
        required_policies=("period_end", "payroll_expense_accounts"),
        evidence_source="client payroll register and trial balance",
        denominator_role="Payroll_register",
        limitations="Uses the engagement's period start, or twelve months ending at "
                    "period end when none is recorded. Accrued "
                    "wages at either end are a normal difference; the auditor "
                    "explains the rest.",
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
        "ppe.rollforward", "Property and equipment rollforward",
        "Roll the fixed-asset register from beginning cost through additions and "
        "disposals to ending cost, and tie ending cost and accumulated depreciation "
        "to the trial balance accounts the auditor names.",
        "ppe", ("existence", "completeness", "accuracy"),
        {"Fixed_assets": ("asset_id", "cost", "acquired_date"),
         "Trial_balance": ("account", "balance")},
        required_policies=("period_end", "ppe_cost_accounts"),
        evidence_source="client fixed-asset register and trial balance",
        denominator_role="Fixed_assets",
        limitations="Uses the engagement's period start, or twelve months when none "
                    "is recorded. Ties the register to the ledger; "
                    "that the assets exist is observation, and additions are vouched "
                    "separately.",
    ),
    ProcedureContract(
        "ppe.depreciation_recompute", "Depreciation recompute",
        "Recompute each asset's straight-line depreciation for the period under the "
        "client's convention and compare it with the register; flag assets "
        "depreciated below salvage.",
        "ppe", ("valuation", "accuracy"),
        {"Fixed_assets": ("asset_id", "cost", "acquired_date", "useful_life_years",
                          "depreciation_expense")},
        required_policies=("period_end", "ppe_depreciation_convention"),
        evidence_source="client fixed-asset register",
        denominator_role="Fixed_assets",
        limitations="Straight line only (full_month or half_year); other methods are "
                    "listed as not recomputed. Whether lives and salvage are "
                    "reasonable is the auditor's judgment.",
    ),
    ProcedureContract(
        "ppe.additions_vouching", "Additions vouching",
        "Compare the period's additions with the auditor's vouching: amounts that "
        "differ from the invoice, items that should have been expensed, unvouched "
        "additions above the threshold.",
        "ppe", ("existence", "accuracy", "classification"),
        {"Fixed_assets": ("asset_id", "cost", "acquired_date"),
         "Additions_vouching": ("asset_id",)},
        required_policies=("period_end",),
        evidence_source="invoices and approvals inspected by the auditor",
        denominator_role="Fixed_assets",
        limitations="Evaluates the vouching recorded; it does not select the sample "
                    "or project errors to the unvouched additions.",
    ),
    ProcedureContract(
        "debt.rollforward_and_interest", "Debt rollforward and interest",
        "Foot each loan from beginning balance through borrowings and repayments to "
        "ending balance, tie the schedule to the trial balance, and test interest "
        "against average balance times rate.",
        "debt_equity", ("completeness", "accuracy", "existence"),
        {"Debt_schedule": ("loan_id", "beginning_balance", "ending_balance"),
         "Trial_balance": ("account", "balance")},
        required_policies=("period_end", "debt_accounts"),
        evidence_source="client debt schedule, loan statements and trial balance",
        denominator_role="Debt_schedule",
        limitations="Interest is a reasonableness test (average balance x rate), run "
                    "only with debt_interest_tolerance_pct set. Confirming balances "
                    "with lenders is separate.",
    ),
    ProcedureContract(
        "debt.covenants", "Loan covenant compliance",
        "Measure each covenant from the trial balance accounts the auditor names and "
        "compare it with the limit in the loan agreement.",
        "debt_equity", ("classification", "presentation"),
        {"Covenants": ("covenant", "numerator_accounts", "operator", "threshold"),
         "Trial_balance": ("account", "balance")},
        evidence_source="the auditor's reading of the loan agreements",
        denominator_role="Covenants",
        limitations="Ratios are magnitudes of account sums; covenants defined on "
                    "adjusted or trailing figures need the auditor's own measure. A "
                    "breach may be waived: inspect the waiver.",
    ),
    ProcedureContract(
        "equity.rollforward", "Equity rollforward",
        "Foot each equity component from beginning through additions and reductions to "
        "ending, and tie both ends to the trial balance.",
        "debt_equity", ("completeness", "accuracy", "presentation"),
        {"Equity_rollforward": ("component", "beginning", "ending")},
        evidence_source="client statement of changes in equity and trial balance",
        denominator_role="Equity_rollforward",
        limitations="Ties need the component's account column and a trial balance; "
                    "board minutes and share registers are inspected separately.",
    ),
    ProcedureContract(
        "accruals.rollforward", "Accruals and prepaids rollforward",
        "Foot each accrual and prepaid from beginning through additions and reductions "
        "to ending, and tie the schedule to the trial balance account by account.",
        "accruals", ("completeness", "accuracy", "existence"),
        {"Accrual_schedule": ("item", "kind", "beginning", "ending")},
        evidence_source="client accruals and prepaids schedule and trial balance",
        denominator_role="Accrual_schedule",
        limitations="Ties need the account column and a trial balance. Accruals never "
                    "recorded are found by the unrecorded-liabilities search, not here.",
    ),
    ProcedureContract(
        "accruals.recompute", "Accruals and prepaids recompute",
        "Recompute each item with a contract amount and service period by time "
        "proportion: the unexpired share of a prepaid, the earned-but-unbilled share of "
        "an accrual.",
        "accruals", ("valuation", "accuracy", "cutoff"),
        {"Accrual_schedule": ("item", "kind", "ending", "total_amount", "service_start",
                              "service_end")},
        required_policies=("period_end",),
        evidence_source="contracts, policies and invoices behind the schedule",
        denominator_role="Accrual_schedule",
        limitations="Time proportion by days only; items measured by usage or estimate "
                    "are listed as not recomputed.",
    ),
    ProcedureContract(
        "estimates.retrospective_review", "Retrospective review of estimates",
        "Compare last year's accounting estimates with how they turned out, and flag "
        "misses beyond the threshold and misses that all lean one way.",
        "estimates", ("valuation",),
        {"Estimates": ("estimate", "prior_estimate", "outcome")},
        required_policies=("estimates_hindsight_pct",),
        evidence_source="prior-year estimates and their subsequent outcomes",
        denominator_role="Estimates",
        limitations="A miss is not an error in last year's statements. The bias "
                    "indicator needs estimates_bias_min_count misses (default 3); "
                    "this year's estimates still need their own testing.",
    ),
    ProcedureContract(
        "related_parties.matching", "Related-party matching",
        "Match management's related-party list against vendors, customers, sales and "
        "employees in the engagement's data.",
        "estimates", ("presentation", "occurrence"),
        {"Related_parties": ("party_name",)},
        evidence_source="management's related-party list and the engagement's "
                        "counterparty data",
        denominator_role="Related_parties",
        limitations="Finds coinciding names (legal suffixes ignored), addresses and "
                    "bank accounts only. A related party management did not list is "
                    "invisible to it; inquiry and public records are separate.",
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
    "rev.sales_cutoff": "receivables",
    "rev.credit_memos_after_period_end": "receivables",
    "ar.confirmations_nonstatistical": "receivables",
    "ar.confirmations_mus": "receivables",
    "ar.confirmations_difference": "receivables",
    "ap.unrecorded_liabilities_search": "payables",
    "payroll.register_tests": "payroll",
    "payroll.register_to_ledger": "payroll",
    "cash.bank_reconciliation": "cash",
    "cash.interbank_transfers": "cash",
    "inventory.count_listing_trace": "inventory",
    "inventory.pricing_projection": "inventory",
    "ppe.rollforward": "ppe",
    "ppe.depreciation_recompute": "ppe",
    "ppe.additions_vouching": "ppe",
    "debt.rollforward_and_interest": "debt_equity",
    "debt.covenants": "debt_equity",
    "equity.rollforward": "debt_equity",
    "accruals.rollforward": "accruals",
    "accruals.recompute": "accruals",
    "estimates.retrospective_review": "estimates",
    "related_parties.matching": "estimates",
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
    "je_seldom_used_max", "je_holidays", "rev_credit_memo_days",
    "payroll_final_pay_days", "ppe_accumulated_depreciation_accounts",
    "ppe_rounding_tolerance", "ppe_depreciation_accounts", "ppe_vouch_threshold",
    "debt_interest_tolerance_pct", "debt_interest_accounts",
    "accruals_rounding_tolerance", "estimates_bias_min_count",
)

# Supplied from the engagement record rather than typed as policies.
ENGAGEMENT_POLICIES: tuple[str, ...] = ("period_end", "period_start", "materiality")


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
    "je_holidays": {"journal_entries"}, "rev_credit_memo_days": {"receivables"},
    "payroll_final_pay_days": {"payroll"},
    "ppe_accumulated_depreciation_accounts": {"ppe"}, "ppe_rounding_tolerance": {"ppe"},
    "ppe_depreciation_accounts": {"ppe"}, "ppe_vouch_threshold": {"ppe"},
    "debt_interest_tolerance_pct": {"debt_equity"},
    "debt_interest_accounts": {"debt_equity"},
    "accruals_rounding_tolerance": {"accruals"},
    "estimates_bias_min_count": {"estimates"},
}


def policy_scopes(name: str) -> set[str]:
    """The cycles whose procedures use this policy (empty: not a cycle policy)."""
    owners = {SCOPE_OF[c.procedure_id] for c in CYCLE_PROCEDURES
              if name in c.required_policies}
    return owners | _OPTIONAL_POLICY_SCOPES.get(name, set())
