# Answer key — Kestrel Valley Cycle Supply, year ended June 30, 2026

Every figure here comes from `answer_key.json`, which `generate.py` computes
with plain Decimal arithmetic. `check_key.py` re-derives the main figures from
the files on disk. Amounts are in dollars; "over" means the books show more
than they should.

## Planning

**Performance materiality.**
- Allocations: Cash 4,500, A/R 9,000, Inventory 9,000, A/P 7,500, Accrued
  3,000. Total **33,000**.
- The cap is 2.0 × 15,000 = **30,000**, so the allocations are **over by
  3,000**.
- No single allocation exceeds materiality.

**Trial balance analytics.**
- Both trial balances foot. The 2026 debits and credits are each
  5,024,465.93.
- Pretax income: 2026 327,827.50; 2025 326,292.00.

| | 2026 | 2025 |
|---|---|---|
| Current ratio | 1.13 | 1.00 |
| Quick ratio | 1.01 | 0.85 |
| Gross margin | 27.7% | 28.4% |
| Sales to receivables (net revenue / year-end net A/R) | 16.41 | — |
| Inventory turnover (cost of sales / avg inventory) | 48.80 | — |

Accounts that move by more than 10% or more than 15,000 are listed in the JSON
(`movements_flagged`). Those that matter to the audit:
- Payroll Checking +38,300: the 06/30 transfers.
- Transfers Clearing −25,000: new, and a credit balance in an asset.
- Allowance −8,600 (−67%): the allowance fell while receivables stayed flat,
  which points to the shortfall in A/R below.
- Freight Out +25,250 (+35%).
- Inventory Shrinkage +27.9%.

Inventory turnover of 48.8 is a question for inquiry; the answer is drop-ship.

## Receivables

**A/R listing to trial balance.**
- The aging totals **264,883.70** and the TB A/R is **261,733.70**, a
  difference of **3,150.00**.
- The difference is Ridgeback Cycles, written off by JE 1066 (dated 06/30,
  entered 07/10), after the aging was exported on 07/08. Not a misstatement.
  Obtain a re-run aging.
- The aging foots across and down.
- **Credit balance:** Summit Loop Racing −1,840.00, an overpayment. Reclassify
  it to a liability.
- **Allowance:**
  - Required at the approved rates: **5,627.38**. This covers debit-balance
    customers only, bucket by bucket, excluding Ridgeback.
  - Recorded: 4,200.00.
  - **Short 1,427.38** → AJE-2.
  - These are the corrected (re-run aging) figures. On the aging as
    exported, which is what a learner loads and reperforms, Ridgeback's
    3,150.00 in the over-90 column adds 1,260.00: required **6,887.38**,
    short **2,687.38**. The difference is the input, not the method.

**Confirmations (nonstatistical).**
- The key items are every customer at or above 9,000: 11 customers, all
  confirmed.
  - Big Sky Pedal Co.: client misstatement **2,250.00** (priced above
    contract).
  - Gallatin Gear Exchange: 6,400 difference, **timing**. Not a misstatement.
  - Yellowstone Velo: 1,100 difference, **customer error**. Not a
    misstatement.
- Sample of 5 from the 7 remaining debit-balance customers:
  - Bitterroot Wheelworks: client misstatement **620.00** (freight
    double-billed).
  - Projection: 620.00 / 24,207.30 sample book × 32,552.30 remainder book =
    **833.73**.
- Total likely misstatement 2,250.00 + 833.73 = **3,083.73**, below tolerable
  9,000.
- On the aging as exported (Ridgeback still in the remainder): 620.00 /
  24,207.30 × 35,702.30 = **914.41**; total likely **3,164.41**. Same
  conclusion.

## Inventory

**Count ↔ listing.**
- The listing totals **66,353.90**, which agrees with the TB. There are 27
  tags; tag 1017 is VOID and carries no quantity.
- Tag 1016's SKU, `kv-brk-pad `, is KV-BRK-PAD. Tags 1016 and 1018 total 380,
  which agrees with the listing.
- Three exceptions:
  - **KV-CHN-11:** counted 230 on tags 1001 + 1002 against 240 listed. 10
    short × 17.10 = **171.00** → AJE-3.
  - **KV-HUB-DT:** listed at 4 units (850.00), not counted. Shipped and
    invoiced 06/29 without relieving inventory: an **850.00** uncorrected
    misstatement.
  - **KV-TUBE-29P:** counted 36, not listed. This is Moraine consignment stock
    and **correctly excluded**. It is not a misstatement.

**Pricing projection.**
- Sample recorded 39,116.50, audited 38,921.50, net **195.00 over**:
  KV-DER-11S 231.00 over, KV-SAD-CMP 36.00 under.
- Projected: 195.00 / 39,116.50 × 66,353.90 = **330.78**, below tolerable
  9,000.

## Cash

**Bank reconciliations.** Both re-foot, and both register balances agree with
the TB.
- Checking: statement 239,107.60, register **188,700.95**.
- Payroll: statement 51,340.00, register **46,500.00**.

Against the cutoff statement (07/01–07/15):
- **Check 4421, 3,100.00:** not cleared by 07/15. Follow up (stale, voided or
  fictitious?).
- **Check 4425:** 1,780.00 on the reconciliation, cleared at **1,870.00**. The
  books are off by **90.00**.
- Check 4412, check 4418, check 4427 and the 40,000 transfer each clear at
  their listed amounts.
- Deposit **12,650.00** cleared 07/07, 7 days after year end, over the 3-day
  policy. Deposit 4,318.75 cleared 07/01.

**Interbank transfers.**
- T-0615: no exception.
- T-0630: no exception. It appears on the checking reconciliation as an
  uncleared transfer and cleared 07/01.
- **T-0701 (check 4429), 25,000:** received per books and bank 06/30,
  disbursed per books 07/01 and per bank 07/02. Cash is counted in both
  accounts at year end, **overstated 25,000**. The payroll deposit was
  credited to 10900 Transfers Clearing → AJE-1.

## Completion

**Adjusting entries** (each one balances):
- AJE-1: Dr 10900 25,000.00 / Cr 10100 25,000.00.
- AJE-2: Dr 65000 1,427.38 / Cr 11900 1,427.38.
- AJE-3: Dr 51000 171.00 / Cr 12100 171.00.

Adjusted balances:
- Checking 163,700.95
- Transfers Clearing 0.00
- Allowance −5,627.38
- Inventory 66,182.90
- Shrinkage 6,411.00
- Bad debt 9,347.38

The adjusted TB foots.

**Uncorrected misstatements** (a negative figure means the balance falls if
corrected):

| Item | Identified | Likely | Current assets | Current liabilities | Income before taxes |
|---|---|---|---|---|---|
| Big Sky pricing | 2,250.00 | — | −2,250.00 | — | −2,250.00 |
| A/R sample, projected | 620.00 | 213.73 | −833.73 | — | −833.73 |
| Inventory pricing, projected | 195.00 | 135.78 | −330.78 | — | −330.78 |
| Hubs not relieved | 850.00 | — | −850.00 | — | −850.00 |
| Check 4425 | 90.00 | — | −90.00 | — | −90.00 |
| Summit Loop reclass | 1,840.00 | — | +1,840.00 | +1,840.00 | — |
| **Total** | | | **−2,514.51** | **+1,840.00** | **−4,354.51** |

Every total is below materiality (15,000). On this evidence the uncorrected
misstatements are not material; the opinion remains the partner's decision.
