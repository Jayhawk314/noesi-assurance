# Kestrel Valley Cycle Supply — second test case (QuickBooks-shaped)

A fabricated audit of a bicycle-parts distributor that keeps its books in
QuickBooks Online, for the year ended **June 30, 2026**. It exists to test the
cycle procedures on data shaped the way a small client actually hands it over,
not the way a textbook lays it out.

Everything here is fictional, and the case was written independently of any
purchased practice case. `generate.py` builds every file and the answer key
with plain Decimal arithmetic. It imports nothing from Noesi, so the key says
what a correct audit concludes, not what the engine does.
`instructor/check_key.py` re-reads the written files and re-derives the main
figures by a second path.

```
python case-studies/kestrel-valley-cycle/generate.py
python case-studies/kestrel-valley-cycle/instructor/check_key.py
```

## The client

Kestrel Valley Cycle Supply, LLC sells parts to about twenty independent bike
shops. Most orders ship direct from its suppliers (drop-ship), so its
warehouse stock is small compared with its sales. That is why inventory
turnover is very high, which is itself a question for inquiry. The bookkeeper,
Dana Merritt, runs QuickBooks Online and reconciles the two bank accounts
monthly. The LLC is a pass-through entity: members take distributions, and
there is no income tax provision.

Net revenue is 4,225,320 and pretax income 327,827.50. Materiality is
**15,000** (about 4.6% of pretax income), and clearly trivial is 750.

## Scope

Cycles switched on: **planning, receivables, cash, inventory, completion**.
Payables and controls are out of scope; Harborline covers payables.

## Files

| File | Source | Shape |
|---|---|---|
| `data/quickbooks/Trial_Balance_2026-06-30.xlsx` | client, QBO | Trial Balance: account ("10100 Checking - First Prairie") in column A with a blank header, then **Debit** and **Credit**; TOTAL row |
| `data/quickbooks/Trial_Balance_2025-06-30.xlsx` | client, QBO | same report run as of the prior year end (comparatives come as a second export) |
| `data/quickbooks/AR_Aging_Summary.xlsx` | client, QBO | customer **name** in column A (no customer number), buckets **Current, 1 - 30, 31 - 60, 61 - 90, 91 and over**, Total; zeros are blank |
| `data/quickbooks/Inventory_Valuation_Summary.xlsx` | client, QBO | category header rows, indented item names, **SKU, Qty, Asset Value, Calc. Avg**, "Total <category>" rows |
| `data/quickbooks/Checking_Reconciliation.xlsx`, `Payroll_Checking_Reconciliation.xlsx` | client, QBO | Reconciliation Report: summary block, then cleared and **uncleared** detail sections (DATE, TYPE, REF NO., PAYEE, AMOUNT (USD)) |
| `data/client/count_tags_2026-06-30.csv` | client count | one row per tag; **several tags per SKU**; one VOID tag; one SKU hand-written in lower case with a trailing space |
| `data/bank/first_prairie_…csv` | bank | cutoff statement 07/01–07/15, signed amounts, check number column |
| `data/auditor/*.csv` | engagement team | line mapping for the trial balance, confirmations, pricing tests, interbank transfer schedule, performance materiality, adjusting entries, uncorrected misstatements |

**About the QuickBooks shapes.** The real exports in `tests/fixtures/quickbooks/`
cover payables reports only. The five QBO files here follow those exports'
conventions: one sheet named `Sheet1`, company / title / date lines, a blank
row, the header, a timestamp footer, and "Total" rows. Their column layouts
follow QuickBooks Online's standard reports. Two differences from a real
export:

- Total rows hold plain numbers where QuickBooks writes a formula with a
  cached value.
- These layouts have not been checked against a real export of the same four
  reports.

Exporting those four reports from the same QBO sandbox would settle both.

## Policies (approved by the partner)

| Policy | Value |
|---|---|
| materiality (engagement record) | 15,000 |
| pm_allocation_multiple | 2.0 |
| ar_tolerable_misstatement | 9,000 |
| inventory_tolerable_misstatement | 9,000 |
| analytics_threshold_pct / _amount | 10 / 15,000 |
| ar_allowance_rates | Current 1%, 1–30 2%, 31–60 5%, 61–90 15%, 91+ 40% |
| dit_max_days | 3 |
| period_end (engagement record) | 2026-06-30 |

## What is planted

Twelve items. `instructor/ANSWER-KEY.md` has the figures and
`instructor/answer_key.json` the full key.

1. **A/R aging ≠ trial balance by 3,150.00.** The aging was exported before a
   6/30-dated write-off was entered. This is not a misstatement; the aging must
   be re-run.
2. **Customer credit balance** −1,840.00 (Summit Loop Racing), not
   reclassified.
3. **Allowance short** by 1,427.38 against the approved aging rates (AJE-2).
4. **Confirmation, key item:** Big Sky priced above contract, 2,250.00. A
   timing difference and a customer error must *not* count as misstatements.
5. **Confirmation, sample:** freight double-billed, 620.00, projected to
   833.73.
6. **Count short** 10 units of KV-CHN-11 across two tags (AJE-3).
7. **Listed, not counted:** KV-HUB-DT, shipped but not relieved, 850.00.
8. **Counted, not listed:** KV-TUBE-29P, which is consignment stock and
   correctly excluded.
9. **Pricing:** net 195.00 overstated in the sample, projected 330.78.
10. **Outstanding check 4421** (3,100.00) has not cleared by 07/15; follow up.
    **Check 4425** is on the reconciliation at 1,780 but cleared at 1,870
    (90.00).
11. **Deposit in transit** 12,650.00 took 7 days to clear, against a policy of
    3.
12. **Kiting-shaped transfer T-0701:** 25,000 received in the books on 06/30,
    disbursed in the books on 07/01. Cash is counted twice (AJE-1).

Also planted: the performance materiality allocations total 33,000, against a
cap of 30,000.

## How the Noesi run is judged

The engine runs **unchanged**. For each procedure, the run is compared with
the key:

- Where the engine gets the key's answer, it is recorded as agreeing.
- Where it cannot read a file, reads it wrongly, or reaches a different
  conclusion, that is a break. Each break goes into
  `instructor/NOESI-RUN-FINDINGS.md` with the file, the step, what happened,
  and what the key says.

Fixes come afterwards, as separate engine changes, each approved first. The
key is never edited to match the engine. If the key itself turns out to be
wrong, the correction is its own commit with the reason given.

## Part 1 of the full case: payables and the journal

```
python case-studies/kestrel-valley-cycle/payables_outputs.py
```

This builds five more QuickBooks files. Four follow the layouts of the real
exports in `tests/fixtures/quickbooks/`: `Vendor_Contact_List`,
`Transaction_List_by_Vendor` (POs, bills, bill payments, checks),
`Bill_Payment_List` and `Unpaid_Bills`. The fifth, a full-year `Journal`
report, uses a modeled layout, with Create date and Created by as added
columns.

They are consistent with the frozen files:
- The journal rolls every account from the prior-year trial balance to the
  current one.
- June's checking activity is exactly the June bank reconciliation.
- The unpaid bills total the trial balance's Accounts Payable (287,640.18).

The key is `instructor/answer_key_payables.json`.

Planted items:
- A duplicate bill (18,432.50), paid through a look-alike vendor (the twin
  "Moraine Cycle Components, Inc.").
- Three bills split under a 2,500 approval limit.
- 4,500 in checks to DM Consulting with no bills; the vendor's address is
  the bookkeeper's home address.
- Two utility bills with no invoice number.
- A bill 12% over its purchase order.
- Check 4425 keyed 90 short, leaving 90 open.
- Journal entries:
  - JE 1066 was entered after period end.
  - JE 1047 is a round 25,000 Saturday entry by the owner, who is not an
    authorized user.
  - JE 1052 has no description.

Three things are not testable from QuickBooks Online exports:
- The three-way match: there are no receiving records.
- Segregation of duties: there is no approver.
- Customer-level balances: the journal's are not built to match the aging.

Parts 2 (payroll, PP&E, debt and equity, accruals) and 3 (estimates, related
parties, completion) follow.
