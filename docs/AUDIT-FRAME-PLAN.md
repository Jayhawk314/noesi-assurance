# Audit frame: what exists, what is missing, and the order to fill it

Written 2026-09-28, after K1–K3. The goal is to make the whole audit exist
end to end at a thin level **before** deepening any one area or fitting more
QuickBooks shapes (K4–K14 wait until after this).

## What exists

| Stage | What Noesi does today |
|---|---|
| Engagement | create, team roles with separation of duties, materiality, cycles in scope |
| Evidence | upload → mapping → reviewer approval → normalize; digests; replace/add (K3) |
| Planning | trial balance analytics, performance materiality check |
| Risk | risk register at the assertion level, linked to procedures |
| Controls | attribute evaluation (sampling results) |
| Payables | 11 procedures (deep) + search for unrecorded liabilities |
| Receivables | listing tie + allowance, confirmations (3 methods) |
| Cash | bank reconciliation re-performance, interbank transfers |
| Inventory | count ↔ listing, pricing projection |
| Completion | adjusted TB, summary of uncorrected misstatements, completion **checkboxes** (subsequent events, going concern, representations, final analytics, evidence sufficiency, engagement review), findings-open gate, signed lock |

## What is missing, in build order

Each area gets **one or two thin procedures first**, with a contract, an
executor, tests on synthetic data, and an honest "limitations" line. Later
passes add depth.

1. **Journal entry testing** (AU-C 240, required on every audit).
   - Checks: entries that don't balance; entries posted after period end
     but dated in the period; weekend and holiday postings; round amounts
     above a threshold; users not on the authorized list; seldom-used
     accounts; blank descriptions.
   - Completeness: journal activity per account rolls the prior trial
     balance forward to the current one.
2. **Revenue** (occurrence, cutoff).
   - Sales cutoff: shipments near year end against invoice dates.
   - Credit memos issued after year end.
   - Invoice ↔ shipping document ↔ customer master.
3. **Payroll.**
   - Payroll register to the ledger.
   - Terminated employees paid.
   - Employees sharing a bank account or address.
   - Gross-to-net recompute.
4. **Property and equipment.**
   - Rollforward: beginning + additions − disposals = ending.
   - Depreciation recompute.
   - A sample of additions vouched.
5. **Debt and equity.**
   - Debt rollforward.
   - Interest recompute from the rate.
   - Covenant ratios from the trial balance.
   - Equity rollforward.
6. **Accruals and prepaids:** rollforward and recompute.
7. **Estimates and related parties.**
   - Retrospective review of last year's estimates.
   - The related-party list matched to vendors and customers.
8. **Completion, as procedures instead of checkboxes.**
   - Subsequent events: disbursements and receipts after year end.
   - Going-concern indicators from the ratios.
   - A representation letter checklist.
9. **Reporting (built, `a5c57f5`):** a draft opinion, with its basis, from the readiness state:
   uncorrected misstatements against materiality, and scope limitations.

## Rules for every area

- The engine stays generic. Case-specific shorthand goes in adapters.
- Test on synthetic data, Harborline or Kestrel. Never use Oceanview content.
- Findings are leads (TENSION / CLASH / ORPHAN), not conclusions. Judgment
  thresholds are policies the partner approves, never hard-coded.
- Every batch gets an independent review before anything is pushed.
- Harborline must still give 11 procedures and 52 findings.

## Limitations of what is built, by kind (recorded 2026-09-28)

**Outside any software (stated, never faked).** These are observation and
confirmation, reading contracts (title passage, covenant definitions,
waivers), judgments (lives, estimates, allowances), and inquiry of
management. Noesi says it did not do them. The completion procedures give
each one a place for the auditor's own recorded conclusion.

**Partly fixable: the depth pass, first item.** The related-party blind spot
is the one to fix first. Management's list cannot find a party it omits,
but the data can show the signs of one:
- A vendor sharing an address, bank account or tax ID with an employee.
  The Vendors role has to carry those fields first.
- Near-identical names, reusing the similarity logic from Harborline's
  vendor look-alikes.

**Engineering shortcuts: the rest of the depth pass.** None of these gives
a wrong answer today; each says what it did not do.
- Depreciation: declining balance and tax tables.
- Additions: sample selection and projection, reusing `sampling.py`.
- Journal entries: Benford, description keywords, entries by senior
  management.
- Revenue: sales against a customer master.
- Covenants: adjusted and trailing measures.
- Payroll tax recompute: left out on purpose, because it is
  jurisdiction-specific.

**Fixed:**
- Engagement period start (`9fa7429`).
- Cycle findings placed in their own area in the unified view (`7bb63ab`).

## After the frame

1. QuickBooks fitting (K4–K14) and recipes.
2. The Workbench cycles/policies screen.
3. Demo data, then lessons, then videos (as in CYCLES-ROLLOUT.md).
