# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Every setting an auditor can make, in plain words: a label, what it means,
and what kind of value it takes. The Scope & Policies screen shows this beside
the setting's code, so nobody has to guess what "dit max days" means or whether
a number is dollars, a percent or days. A test holds that every setting the
screen can show has an entry here."""

from __future__ import annotations

AMOUNT, PERCENT, DAYS, COUNT, ACCOUNTS, NAMES, DATE, DATES, CHOICE, RATE, SOURCES = (
    "amount ($)", "percent", "days", "count", "account numbers, comma-separated",
    "names, comma-separated", "date (YYYY-MM-DD)", "dates, comma-separated",
    "one of the choices shown", "multiple", "transaction types, comma-separated")

# name -> (label, kind of value, what it means)
POLICY_TEXT: dict[str, tuple[str, str, str]] = {
    # engagement-wide
    "clearly_trivial_pct": (
        "Clearly trivial, as a percent of materiality", PERCENT,
        "Misstatements below this share of materiality are clearly trivial and are "
        "not accumulated. 5% when left empty."),
    "performance_materiality_pct": (
        "Performance materiality, as a percent of materiality", PERCENT,
        "Overall performance materiality is this share of materiality; firms commonly "
        "use 50% to 75%. 75% when left empty."),
    # planning
    "pm_allocation_multiple": (
        "Allowed total of performance-materiality allocations", RATE,
        "The allocations across accounts may add up to this many times overall "
        "materiality (for example 2.0); above it the allocation is flagged."),
    "analytics_threshold_amount": (
        "Analytics: movement worth explaining ($)", AMOUNT,
        "An account whose balance moved by at least this amount from last year is "
        "flagged for an explanation."),
    "analytics_threshold_pct": (
        "Analytics: movement worth explaining (%)", PERCENT,
        "An account whose balance moved by at least this percent from last year is "
        "flagged for an explanation."),
    "analytics_threshold_rule": (
        "Analytics: flag when both limits are passed, or either", CHOICE,
        "'and': flag only when the movement passes both the amount and the percent; "
        "'or': flag when it passes either. 'and' when left empty."),
    # journal entries
    "je_authorized_users": (
        "People allowed to post journal entries", NAMES,
        "An entry created by anyone else is flagged."),
    "je_holidays": (
        "Holidays", DATES,
        "Entries dated on these days (or on a weekend) are flagged."),
    "je_manual_sources": (
        "Which transaction types count as manual entries", SOURCES,
        "Only entries of these types are tested as manual journal entries (for "
        "QuickBooks, usually 'Journal Entry')."),
    "je_round_amount_threshold": (
        "Round-amount test: smallest amount tested ($)", AMOUNT,
        "Round amounts at or above this are flagged."),
    "je_round_unit": (
        "Round-amount test: what counts as round ($)", AMOUNT,
        "An amount that is an exact multiple of this (for example 1000) is round."),
    "je_seldom_used_max": (
        "Seldom-used account: most uses in the year", COUNT,
        "An entry to an account used this many times or fewer in the year is flagged."),
    # revenue and receivables
    "ar_tolerable_misstatement": (
        "Receivables: tolerable misstatement ($)", AMOUNT,
        "The most misstatement in receivables the auditor can accept; projected "
        "misstatement is compared with it."),
    "ar_risk_incorrect_acceptance": (
        "Receivables sampling: risk of incorrect acceptance", PERCENT,
        "The risk the auditor accepts of concluding the balance is fairly stated when "
        "it is not (for example 5%). Needed by monetary-unit sampling and difference "
        "estimation."),
    "mus_interval": (
        "Monetary-unit sampling: sampling interval ($)", AMOUNT,
        "Every this-many dollars of the balance, one item is selected."),
    "ar_allowance_rates": (
        "Allowance rates by age", "percents, comma-separated",
        "The share of each aging bucket expected to go uncollected, in order: current, "
        "1-30, 31-60, 61-90, over 90 days (for example 0.01,0.02,0.05,0.15,0.40)."),
    "ar_confidence_factor": (
        "Monetary-unit sampling: confidence factor", RATE,
        "The factor for the chosen risk of incorrect acceptance (from the sampling "
        "table); used to size the upper misstatement limit."),
    "ar_estimated_sd": (
        "Difference estimation: expected standard deviation ($)", AMOUNT,
        "The expected spread of the differences, per item."),
    "ar_expected_misstatement": (
        "Receivables sampling: expected misstatement ($)", AMOUNT,
        "The misstatement the auditor expects to find before sampling."),
    "ar_risk_incorrect_rejection": (
        "Difference estimation: risk of incorrect rejection", PERCENT,
        "The risk the auditor accepts of concluding the balance is misstated when "
        "it is not."),
    "rev_credit_memo_days": (
        "Credit memos after year end: days to look", DAYS,
        "Credit memos issued within this many days after year end are examined for "
        "sales that should not have been recorded."),
    # payables
    "search_threshold": (
        "Unrecorded liabilities search: examine every payment above ($)", AMOUNT,
        "Every payment after year end above this amount is examined."),
    "search_interval": (
        "Unrecorded liabilities search: pick every nth smaller payment", COUNT,
        "Of the payments at or below the threshold, every nth is picked."),
    "search_start": (
        "Unrecorded liabilities search: start at payment number", COUNT,
        "The random start for picking every nth smaller payment."),
    "search_systematic_count": (
        "Unrecorded liabilities search: most smaller payments to pick", COUNT,
        "The largest number of smaller payments picked."),
    "ap_control_accounts": (
        "Accounts payable control accounts in the trial balance", ACCOUNTS,
        "When no General Ledger export is loaded, the A/P tie takes the ledger side "
        "from these trial-balance accounts (their credit balance)."),
    # payroll
    "payroll_expense_accounts": (
        "Wage accounts in the ledger", ACCOUNTS,
        "The register's gross pay is tied to the total of these accounts."),
    "payroll_final_pay_days": (
        "Final pay: days allowed after leaving", DAYS,
        "A payment to someone who left is flagged only if it comes later than this "
        "many days after their termination date."),
    # forensic
    "benford_min_population": (
        "First-digit test: fewest amounts to test", COUNT,
        "A population with fewer amounts of 10 or more than this is not tested. "
        "Nigrini suggests at least 1,000; below a few hundred the test says little."),
    # cash
    "dit_max_days": (
        "Deposits in transit: most days to reach the bank", DAYS,
        "A deposit in transit that reaches the bank more than this many days after "
        "the date it was recorded is flagged (receipts cutoff)."),
    # inventory
    "inventory_tolerable_misstatement": (
        "Inventory: tolerable misstatement ($)", AMOUNT,
        "The most misstatement in inventory the auditor can accept; the projected "
        "pricing error is compared with it."),
    "pricing_sample_value": (
        "Inventory pricing: value of the sample tested ($)", AMOUNT,
        "Set this when only the exceptions were entered; otherwise the sample value "
        "is taken from the pricing-test rows."),
    # property and equipment
    "ppe_cost_accounts": (
        "Property and equipment: cost accounts", ACCOUNTS,
        "The asset register's cost is tied to these ledger accounts."),
    "ppe_depreciation_convention": (
        "Depreciation convention", CHOICE,
        "How the first and last year are counted: 'full_month' or 'half_year'."),
    "ppe_accumulated_depreciation_accounts": (
        "Accumulated depreciation accounts", ACCOUNTS,
        "The register's accumulated depreciation is tied to these ledger accounts."),
    "ppe_depreciation_accounts": (
        "Depreciation expense accounts", ACCOUNTS,
        "The year's recomputed depreciation is tied to these ledger accounts."),
    "ppe_rounding_tolerance": (
        "Depreciation: rounding allowed ($)", AMOUNT,
        "Differences up to this amount are treated as rounding. $1.00 when left empty."),
    "ppe_vouch_threshold": (
        "Additions: vouch every addition from ($)", AMOUNT,
        "An addition at or above this amount that was not vouched is flagged."),
    # debt and equity
    "debt_accounts": (
        "Debt accounts in the ledger", ACCOUNTS,
        "The debt schedule's ending balances are tied to these accounts."),
    "debt_interest_accounts": (
        "Interest expense accounts", ACCOUNTS,
        "Recorded interest is taken from these accounts."),
    "debt_interest_tolerance_pct": (
        "Interest test: difference allowed (%)", PERCENT,
        "Recorded interest within this percent of the estimate (average balance "
        "times rate) is reasonable."),
    # accruals
    "accruals_rounding_tolerance": (
        "Accruals: rounding allowed ($)", AMOUNT,
        "Differences up to this amount are treated as rounding. $1.00 when left empty."),
    # estimates
    "estimates_hindsight_pct": (
        "Last year's estimates: miss worth noting (%)", PERCENT,
        "A prior-year estimate that missed the actual outcome by more than this "
        "percent is flagged."),
    "estimates_bias_min_count": (
        "Estimates: misses in one direction that suggest bias", COUNT,
        "When at least this many estimates all missed the same way, possible bias is "
        "flagged. 3 when left empty."),
    # completion
    "report_date": (
        "Date of the auditor's report", DATE,
        "Subsequent events run to this date, and the representation letter should "
        "be dated on it."),
    "se_threshold": (
        "Subsequent events: smallest amount listed ($)", AMOUNT,
        "Transactions after year end at or above this amount are listed for review."),
    "gc_current_ratio_floor": (
        "Going concern: lowest acceptable current ratio", RATE,
        "A current ratio below this (for example a loan covenant's 1.20) is a "
        "going-concern indicator."),
    "rep_signers": (
        "Who must sign the representation letter", NAMES,
        "The letter is checked for these signatures."),
    "misstatement_likely_basis": (
        "How the misstatement schedule's 'likely' column is read", CHOICE,
        "'total': likely already includes the identified misstatement; "
        "'beyond_identified': likely is added to it."),
}


def policy_text(name: str) -> dict:
    """The label, kind of value and meaning of one setting (empty if unknown)."""
    label, kind, meaning = POLICY_TEXT.get(name, ("", "", ""))
    return {"label": label, "kind": kind, "meaning": meaning}
