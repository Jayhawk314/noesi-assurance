# Noesi run findings — Kestrel Valley (engine unchanged)

**Run:** 2026-09-26. The engine is as of `da6a96c`, with no engine changes.
The key was frozen at `ba56586`.

**Reproduce:** `.venv\Scripts\python case-studies\kestrel-valley-cycle\instructor\run_noesi.py A`
(or `B`).

- **Pass A** loads the files as delivered: QuickBooks exports, the count CSV,
  the bank CSV and the auditor CSVs.
- **Pass B** loads the same figures after hand preparation (`prep_*` in
  `run_noesi.py`):
  - columns renamed;
  - debit − credit → balance, with the line and prior year joined in;
  - the reconciliation report flattened to one row per item;
  - bank amounts unsigned.

  No figures were changed.

Severity:
- **High:** a wrong or silently incomplete result.
- **Medium:** a false exception, or a correct one that is missing.
- **Low:** friction or noise.

## Scoreboard

| Procedure | Pass A (as delivered) | Pass B (prepared) | Against the key |
|---|---|---|---|
| planning.performance_materiality | runs | runs | **agrees** (33,000 vs 30,000 cap) |
| fs.trial_balance_analytics | refused | runs | foots ✓; movements agree under AND (K9); **ratios missing** (K8) |
| ar.listing_tie | refused | **errors** (K5) | not tested |
| ar.confirmations_nonstatistical | refused | runs | same conclusion; projection 867.28 vs 833.73 (K12) |
| cash.bank_reconciliation | refused | runs | 4421 ✓, 4425 ✓, slow DIT ✓; **3 false follow-ups** (K10, K11) |
| cash.interbank_transfers | refused | runs | T-0701 kiting 25,000 ✓; **T-0630 false exception** (K10) |
| inventory.count_listing_trace | refused | runs | both orphans ✓; **per-tag, not per-SKU** (K6); 18 description notes (K7) |
| inventory.pricing_projection | refused | runs | **agrees** (330.78) |
| fs.adjusted_trial_balance | refused | runs | adjusted balances **agree**; pretax shown as 0 (K8) |
| completion.uncorrected_misstatements | runs | runs | totals **agree**; 6 false tensions (K13) |

In pass A, 2 of 10 cycle procedures ran and 8 were refused. In pass B, 9 of
10 ran.

The refusals are honest: coverage names the missing fields and nothing
reports "completed". The real problems are the silent ones below (K1–K4).

## Findings

### Silent mis-reads (as delivered)

**K1. High: the A/R aging's TOTAL row loads as a customer.** In pass A,
`AR_Aging_Summary.xlsx` loaded 21 rows, and the control total shows
**529,767.40**, twice the true 264,883.70. It stayed blocked only because
column A has a blank header and did not map to a customer. A reviewer who maps
column A would get a doubled listing. The key says 264,883.70 from 20
customers.

**K2. High: a QuickBooks Reconciliation Report is mis-read.**
- The suggested header row is row 20, the *cleared* checks section. Only those
  9 rows load, and QuickBooks' TYPE ("Check", "Bill Payment") maps to
  `item_type`.
- The summary block and both *uncleared* sections are ignored.
- Cleared items are not reconciling items, so a mapped amount would have fed
  the wrong population into the procedure.
- The key needs statement 239,107.60, register 188,700.95, 6 uncleared
  payments and 2 uncleared deposits.

**K3. High: the latest file of a role silently replaces the earlier one.**
Procedures read one dataset per role, the latest (`service.py:420`):
- A second reconciliation (payroll) replaces checking.
- A prior-year trial balance loaded after the current one replaces it.
- In pass A both happened, and nothing said so at run time.

Two bank accounts and comparative trial balances are normal for small
clients.

**K4. Medium: a dataset with no mapped fields still "loads".** The trial
balance shows `loaded 33 rejected 0` with an empty column map. Coverage then
blocks, which is correct, but the load report reads as a success.

### Shape breaks (the ones §3 of CYCLES-ROLLOUT expected, now confirmed)

**K5. Medium: the aging is fixed at four buckets.**
- The QuickBooks buckets "1 - 30" and "91 and over" are left unmapped.
- `ar_allowance_rates` with five rates is **accepted when set** and fails only
  at run time. The whole `ar.listing_tie` then errors, so the tie-out and the
  credit balance go untested as well.
- Key: allowance required 5,627.38, short 1,427.38; difference 3,150.00;
  Summit Loop −1,840.00.

**K6. Medium: count tags are compared one by one, not summed per SKU.**
- Six SKUs with several tags each raise a "duplicate" CLASH.
- Their quantities are compared tag against listing, which gives 5 false
  quantity differences.
- KV-CHN-11 shows 150 vs 240 when the key says 230 vs 240 (10 short, 171.00).
- The void tag (blank SKU) is rejected, which is acceptable.
- The lower-case SKU with a trailing space was matched correctly.

**K7. Low: count descriptions are compared with listing descriptions.** There
are 18 TENSIONs ("Carbon bar" vs "Carbon Handlebar 780mm"). Count tags use
shorthand, and a SKU match is the identity.

**K8. Medium: the statement-line vocabulary is fixed.** A lead-schedule label
such as "Accounts receivable", "Accounts payable", "Revenue" or "Operating
expenses" is not recognised:
- 28 of 32 accounts are left out as "unclassified". This is honest, but every
  ratio is blank.
- `fs.adjusted_trial_balance` reports pretax income as 0.00, and
  `ar.listing_tie` would read receivables as 0.
- Key: current ratio 1.13, gross margin 27.7%, pretax 327,827.50.

A mapping step (label → engine line) is needed.

**K9. Low (spec ambiguity, not an engine error): the movement threshold
semantics.** The engine flags a movement only when it is over 10% **and** over
15,000; the key assumed **or**. Under AND, the engine's 9 flags match the key
exactly. Sales (+374,240, 9.6%) is flagged only under OR. The contract should
state which rule applies. The key is left unchanged and this note records the
difference.

**K10. Medium: items without a check number cannot be matched.**
Reconciliation items and transfers are matched by reference only:
- The 40,000 online transfer (no reference) cleared on 07/01, but it is
  reported as "did not clear".
- `cash.interbank_transfers` says T-0630 "should be an outstanding check and
  is not", yet it is on the reconciliation as an uncleared transfer.

Real exports have no shared key (the transfer IDs are the auditor's), so
matching needs amount + date. The key says no exception for either.

**K11. Medium: no cutoff statement for an account reads as "did not clear".**
Only the checking cutoff statement was provided, yet payroll checks PR-2231
and PR-2236 are reported as "did not clear on the cutoff statement". The
honest statement is "no cutoff statement for account payroll".

**K12. Low: the confirmation projection population.** The engine projects
over 33,862.30; the key uses 32,552.30.
- The difference (1,310.00) is Ridgeback (3,150, written off after the aging
  export) plus Summit Loop (−1,840, a credit balance).
- Excluding credit balances from the sampled population is textbook practice.
  Ridgeback is an input issue that K1/K5 hide.
- The conclusion is the same: below tolerable 9,000.

**K13. Medium: "Likely" is read as an aggregate.** The misstatements file's
`Likely` column holds the projected amount *beyond* the identified amount; the
engine reads it as the total.
- The result is 6 false "likely below identified" tensions.
- The "remaining" headroom uses 349.51 as likely, where the aggregate is
  6,194.51.
- The totals by statement line still agree with the key.

The column's meaning should be chosen on mapping, not assumed.

### Synonym gaps (low, each blocks a procedure in pass A)

| Header in the file | Role and field | Result |
|---|---|---|
| (blank), Debit, Credit | Trial_balance account / balance | refused |
| (blank) customer name | AR_listing customer_number | refused |
| Asset Value, Calc. Avg | Inventory_listing cost / unit_cost | refused |
| Item SKU, Qty Counted, Tag # | Inventory_count stock_number / quantity | refused |
| Item SKU | Pricing_tests stock_number | refused |
| Posting Date, Check or Slip #; no account column | Cutoff_statement | refused |
| Transfer, Disbursed per Books, … | Transfers | refused |
| Account "10100 Checking - First Prairie" | Adjusting_entries vs a TB keyed by number | untested |

The bank CSV's signed amounts (checks negative) were not tested; pass B
unsigned them.

### Also seen

**K14. Low: payables-only procedures show in a cycles-only scope.** The 11 AP
procedures stay in coverage as `blocked=11` although payables is not in scope.
A partner reads "11 blocked" on an engagement that never meant to run them.

**Known open items, confirmed here:**
- The SAD and SUM summaries still disagree (CYCLES-ROLLOUT §6).
- Inventory turnover now has prior-year input, but only through the prepared
  file (K3, K8).

## What agrees with the key

- **Performance materiality:** agrees.
- **Pricing projection:** 330.78, agrees.
- **Adjusted balances:** every changed account agrees.
- **Misstatement totals by line:** current assets −2,514.51, current
  liabilities +1,840.00, income −4,354.51.
- **Trial balance:** the 2026 figures foot at 5,024,465.93.
- **Reconciliations:** both re-foot.
- **Cash exceptions found:**
  - check 4421 not cleared;
  - check 4425 cleared 90 over;
  - the 12,650 deposit in transit took 7 days;
  - kiting on T-0701 (25,000).
- **Confirmations:** both client misstatements found; timing and customer
  error correctly not counted.
- **Count ↔ listing:** both orphans found (KV-HUB-DT, KV-TUBE-29P).

## Proposed engine changes (for approval; none made)

1. **QuickBooks recipes** for the Trial Balance, A/R Aging Summary, Inventory
   Valuation Summary and Reconciliation Report. These cover K1, K2, K4 and
   most synonym gaps. Build them the way the payables recipes are built: skip
   title, total and category rows, and read report sections by name.
2. **Several files per role** where the role is naturally plural (bank
   reconciliations, cutoff statements, a prior-year TB), or refuse a second
   file loudly (K3).
3. **Aging buckets by name, any number,** and validate
   `ar_allowance_rates` against the aging when the policy is set (K5).
4. **Sum count tags per SKU before comparing;** treat description differences
   as information, not tension (K6, K7).
5. **A line-mapping step:** the auditor's labels mapped to engine lines,
   reviewed like a column mapping (K8).
6. **Match references, then amount + date,** for items with no reference; say
   "no cutoff statement" for an account without one (K10, K11).
7. **State the movement rule (AND/OR) as a policy;** choose the "Likely"
   convention on mapping; hide out-of-scope AP rows from cycle-only coverage
   (K9, K13, K14).

## Status after the run (the findings above are left as recorded)

| Finding | Status | Commit |
|---|---|---|
| K3 second file silently replaces the first | fixed: a load must say replace or add; added files are read together; runs record the datasets read | `94ecaa7` |
| K1 total row loads as a record | fixed: a tying total row is set aside with its reason | `2ca4081` |
| K2 multi-section report read as one table | fixed: refused with the repeated heading rows named | `afe4454` |
| K4–K14 | open; the QuickBooks fitting comes after the missing audit areas | — |

Pass A now refuses the payroll reconciliation and the prior-year trial
balance unless told to replace or add (K3). It also refuses both
reconciliation reports (K2), and it would set aside the aging's TOTAL row
(K1). These three fixes have not yet had an independent review.
