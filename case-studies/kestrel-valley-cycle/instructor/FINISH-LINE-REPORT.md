# Kestrel finish-line check

*Written by `finish_line_check.py` (ROADMAP step 0). It seeds the Workbench demo through the real service path, as `--demo` does, and compares each Learn module with `answer_key*.json`. Do not edit by hand; re-run the script.*

**141 match, 5 differ, 7 not in Noesi** (30 procedures run).

| # | Module | Match | Differ | Not in Noesi |
|---|---|---|---|---|
| 1 | Engagement setup | 5 | 0 | 0 |
| 2 | Planning | 18 | 0 | 1 |
| 3 | Journal entries | 13 | 0 | 0 |
| 4 | Revenue and receivables | 11 | 4 | 0 |
| 5 | Payables | 12 | 0 | 3 |
| 6 | Cash | 12 | 0 | 0 |
| 7 | Inventory | 10 | 0 | 0 |
| 8 | Payroll | 7 | 0 | 1 |
| 9 | Property and equipment | 8 | 0 | 0 |
| 10 | Debt, equity, accruals | 10 | 0 | 1 |
| 11 | Estimates and related parties | 5 | 0 | 0 |
| 12 | Completion | 25 | 1 | 1 |
| 13 | The opinion | 5 | 0 | 0 |

## 1. Engagement setup

Matches: materiality; period start; period end; team: partner, preparer, reviewer; every file loads (none refused).

## 2. Planning

Matches: PM allocated; PM cap (2.0 x materiality); PM over the cap by; trial balance foots; trial balance debits; movements flagged (10% or 15,000); 2026 current ratio; 2026 quick ratio; 2026 gross margin %; 2026 net revenue; 2026 pretax income; 2025 current ratio; 2025 quick ratio; 2025 gross margin %; 2025 net revenue; 2025 pretax income; 2026 cost of sales; 2026 inventory turnover (average inventory).

- **not in Noesi: 2026 A/R turnover on average gross A/R.** Key 15.94; Workbench —. Why: the engine reports sales to year-end net receivables (16.4069), the AICPA guide's ratio, not a turnover on average gross A/R.

## 3. Journal entries

Matches: transactions in the Journal; lines in the Journal; posted after period end: entries; weekend or holiday: entries; round amount: entries; unauthorized user: entries; seldom used account: entries; no description: count; manual entries without a description; seldom-used accounts; every account rolls forward; closed to; prior-year closing amount.

## 4. Revenue and receivables

Matches: aging total; A/R per trial balance; aging to ledger difference found; credit balance: Summit Loop Racing; allowance recorded; key items; sample items; key-item misstatement; misstatements counted (timing and customer error left out); sample book value; below tolerable.

- **differs: allowance required.** Key 5627.38; Workbench 6887.38. Why: the aging still carries Ridgeback Cycles' 3,150.00, written off after it was run; the key recomputes after the write-off (a re-run aging), the Workbench on the aging as loaded (3,150.00 x 40% = 1,260.00).

- **differs: remainder book value.** Key 32552.30; Workbench 35702.30. Why: the aging still carries Ridgeback Cycles' 3,150.00, written off after it was run; the key recomputes after the write-off (a re-run aging), the Workbench on the aging as loaded.

- **differs: projected misstatement.** Key 833.73; Workbench 914.41. Why: the aging still carries Ridgeback Cycles' 3,150.00, written off after it was run; the key recomputes after the write-off (a re-run aging), the Workbench on the aging as loaded.

- **differs: total likely misstatement.** Key 3083.73; Workbench 3164.41. Why: the aging still carries Ridgeback Cycles' 3,150.00, written off after it was run; the key recomputes after the write-off (a re-run aging), the Workbench on the aging as loaded.

## 5. Payables

Matches: vendors; vendor twins; bills (loaded + set aside); bills without a number (set aside at load); bill payments; bill payments total; duplicate bill MC-25009; split bills: Hyalite total; short payment on check 4425 (left open); three-way match not testable; segregation of duties not testable; duplicate's misstatement.

- **not in Noesi: PO overrun: Summit Tire PO 1021.** Key True; Workbench —. Why: QuickBooks' Transaction List by Vendor carries no PO link on a bill (the PO number is only in the memo), so voucher-to-PO tests are partial (partial); roadmap C.

- **not in Noesi: checks without bills: DM Consulting 4,500.** Key True; Workbench —. Why: no procedure tests direct checks to vendors that never billed; the Payments loaded are bill payments only (parking lot: depth pass).

- **not in Noesi: A/P subledger ties to the ledger.** Key 0.00; Workbench —. Why: the A/P control schedule is built from Unpaid Bills and a General Ledger export; Kestrel has a trial balance, not a General Ledger export (blocked); roadmap C.

## 6. Cash

Matches: checking: statement ending; checking: book balance; checking: reconciliation refoots; payroll: statement ending; payroll: book balance; payroll: reconciliation refoots; check 4421 did not clear by 07-15; check 4425 cleared at another amount; deposits in transit cleared slowly; transfer T-0615; transfer T-0630; transfer T-0701.

## 7. Inventory

Matches: listing total; tags (loaded + void set aside); void tags set aside; quantity differences; listed, not counted; counted, not listed; pricing sample recorded; net overstatement in sample; items with differences; projected to the listing.

## 8. Payroll

Matches: register gross; wages per ledger; difference; ghost employee E16: payments; paid after termination: E12; shared bank account: E03, E09; net pay error: E05.

- **not in Noesi: bookkeeper's address is a vendor's (DM Consulting).** Key True; Workbench —. Why: no procedure compares employee and vendor addresses (parking lot: depth pass, 'vendor sharing an address with an employee').

## 9. Property and equipment

Matches: beginning cost; additions; disposals; ending cost; accumulated; depreciation per register; FA-06 depreciation differs by; additions vouched in full, no exceptions.

## 10. Debt, equity, accruals

Matches: loan beginning; loan ending; interest within tolerance (4.8% < 10%); current-ratio covenant breached; members' capital does not tie; retained earnings ties; accruals and prepaids tie to the ledger; insurance premium recompute differs by; audit fee recompute differs by; not recomputed.

- **not in Noesi: stale accrual: Accrued payroll unchanged all year.** Key accrued payroll; Workbench —. Why: the rollforward tests that each item foots and ties; it does not point out a balance with no activity all year.

## 11. Estimates and related parties

Matches: estimates missed beyond 20%; bias indicator (all missed one way); related party: Summit Loop Racing is a customer; related party: Jo Kestrel on the payroll (E01); DM Consulting not findable by matching management's list.

## 12. Completion

Matches: subsequent-event lead: JE 1071 settlement 30000.00; subsequent-event lead: check 4429 25000.00; subsequent-event lead: payroll funding transfer 40000.00; subsequent-event lead: deposit 33580.90; subsequent-event lead: deposit 27904.15; representation missing; letter not dated the report date; uncorrected misstatements: Current Assets; uncorrected misstatements: Noncurrent Assets; uncorrected misstatements: Current Liabilities; uncorrected misstatements: Noncurrent Liabilities; uncorrected misstatements: Income Before Taxes; above materiality on Current Assets; going concern: working capital; going concern: net income; going concern: equity; going concern: current ratio; going-concern indicator: current ratio below floor; adjusting entries balance; adjusted 10100 Checking - First Prairie; adjusted 10900 Transfers Clearing; adjusted 11900 Allowance for Doubtful Accounts; adjusted 12100 Inventory Asset; adjusted 51000 Inventory Shrinkage; adjusted 65000 Bad Debt Expense.

- **not in Noesi: unrecorded liability: check 4433.** Key 6100.00; Workbench —. Why: the search needs payments linked to bills and the auditor's inspection results (blocked); the July check is below the subsequent-events threshold.

- **differs: summary of misstatements agrees with the procedure.** Key 15650.37; Workbench 0.00. Why: the summary of uncorrected misstatements (SAD) totals only findings the team has disposed as misstatements, none yet, while the procedure reads the misstatement schedule; roadmap B2.

## 13. The opinion

Matches: proposed opinion; basis: related-parties representation not provided; basis: misstatements above materiality on current assets; decision: going-concern conclusion (incl. covenant breach); decision: re-date the representation letter.
