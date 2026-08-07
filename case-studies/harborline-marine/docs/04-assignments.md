# Assignments

Spreadsheet-first. Every assignment can be completed in LibreOffice Calc using
only `data/` and the templates in `workpapers/`. Where the workbench can also
perform the test, the assignment says so — do it by hand *first*, then compare.

Open a CSV in Calc with **File → Open**, comma separator, and set the amount
columns to a number format with two decimals. Save your work as `.ods`.

## How to get started in Calc

Most of these are lookup problems. The pattern you will use repeatedly:

```
=IF(ISNA(VLOOKUP(A2, vouchers.B:B, 1, 0)), "EXCEPTION", "ok")
```

For amount comparisons, guard against floating point:

```
=IF(ABS(C2 - D2) > 0.005, "DIFFERENCE", "ok")
```

---

## Assignment 1 — Vendor master review
**Procedure:** `ap.vendor_relational_twins` · **Workbench: errors, do it by hand**

Open `vendors.csv`. Sort by `Vendor Name`.

1. Identify every pair of vendors that appear to be the same party recorded
   twice. Look at names, remit city, and tax ID together — no single column
   gives it away.
2. For each pair, trace both vendor numbers into `payments.csv`. Did both
   receive money? How much in total?
3. The engagement brief says vendor creation moved into purchasing in April.
   Does the timing of the payments support or undercut a concern about that
   change?

**Deliver:** `workpapers/WP-A1-vendor-twins.csv`, one row per suspected pair,
with your conclusion and the amounts involved.

> A near-duplicate is a lead, not a finding. Say what further evidence you would
> request before calling it a duplicate payment.

---

## Assignment 2 — Segregation of duties over disbursements
**Procedure:** `ap.segregation_of_duties` · **Workbench: errors, do it by hand**

In `payments.csv`, compare `Created By` and `Approved By`.

1. Flag every payment where they are the same person. Use `employees.csv` to
   name them.
2. Total the flagged payments. Compare that total to performance materiality
   (315,000).
3. Cross-reference the payment dates against the June–September supervisor
   vacancy described in the engagement brief. Do the exceptions cluster there,
   or are they spread across the year? Your answer changes the conclusion: a
   cluster is a control gap with a known cause and end date; a spread is a
   pervasive design failure.

**Deliver:** `workpapers/WP-A2-segregation.csv` plus a short memo answering (3).

---

## Assignment 3 — Reference integrity
**Procedures:** `ap.payment_voucher_reference`, `ap.voucher_po_reference` ·
**Workbench: both error, do them by hand**

1. Every `Voucher Number` in `payments.csv` should exist in `vouchers.csv`.
   Find the ones that do not.
2. Every `PO Number` in `vouchers.csv` should exist in `purchase_orders.csv`.
   Find the ones that do not.
3. For each orphan, state what it could mean. A missing reference is not
   automatically fraud — a truncated export and a fabricated invoice look
   identical in the data. What would distinguish them?

**Deliver:** `workpapers/WP-A3-reference-integrity.csv`.

---

## Assignment 4 — Three-way match
**Procedure:** `ap.three_way_receipt_match` · **Workbench: works — compare after**

1. For each voucher, find the PO and the goods receipt. Flag vouchers with no
   receipt at all, and receipts short of the invoiced amount.
2. Quantify the total invoiced value with no evidence of receipt.
3. Run the procedure in the workbench. **It will find more exceptions than you
   did.** Work out why before reading on.

<details>
<summary>Why the tool finds more</summary>

Vouchers citing a non-existent PO (Assignment 3) also have no reachable goods
receipt, so they surface here as well. One underlying defect, two procedures.
Deciding whether that is one finding or two — and whether double-counting the
amount would overstate the SAD — is exactly the judgment the tool cannot make.
</details>

**Deliver:** `workpapers/WP-A4-three-way-match.csv`, with a reconciliation of
your count to the tool's.

---

## Assignment 5 — Bank clearing and GL posting
**Procedures:** `cash.bank_clearing`, `gl.payment_posting` ·
**Workbench: both work — compare after**

1. Match `payments.csv` to `bank.csv` on payment number. Flag uncleared
   payments and amount differences.
2. Match `payments.csv` to `gl.csv` on `Reference`. Flag unposted payments and
   amount differences.
3. For every uncleared payment, decide: is this a misstatement, a cut-off
   matter, or neither? Justify each. Only some belong on the SAD.

**Deliver:** `workpapers/WP-A5-clearing.csv`.

---

## Assignment 6 — Subledger to control account
**Procedure:** `ap.subledger_gl_balance_tie` · **Workbench: works**

1. Sum `Voucher Amount` in `vouchers.csv`. Compare to `Subledger Balance` in
   `ap_control_balance.csv`.
2. Compare the subledger to `GL Balance`. Quantify the variance.
3. The variance is below overall materiality. Does that settle it? Argue both
   sides, then conclude.

**Deliver:** `workpapers/WP-A6-control-tie.csv`.

---

## Assignment 7 — Split payments
**Procedure:** `ap.split_payment_review` · **Workbench: permanently partial**

The approval threshold is **$10,000**.

1. Group `payments.csv` by vendor and sort by date. Find clusters of payments
   just below the threshold within a short window.
2. Total each cluster. Would a single payment of that total have required a
   second signature?
3. The workbench reports this procedure as *partial* because it needs a
   `split_threshold` policy and there is no way to set one. Write the sentence
   you would put in the workpaper's limitations section describing this.

**Deliver:** `workpapers/WP-A7-split-payments.csv`.

---

## Assignment 8 — Value flows
**Procedure:** `forensic.closed_value_flow` · **Workbench: works**

1. In `value_flows.csv`, find any closed cycle — value leaving Harborline and
   returning through intermediaries.
2. Identify the counterparties and the amount.
3. The audit plan records that this extract is management-prepared with no
   independent reconciliation. What does a closed cycle in an unverified
   population actually entitle you to conclude? Write the finding so that it
   survives review — and so that it does not allege more than the evidence
   supports.

**Deliver:** `workpapers/WP-A8-value-flows.csv`.

---

## Assignment 9 — Summary of audit differences

Using `workpapers/WP-SAD.csv`:

1. Bring forward every quantified misstatement from Assignments 1–8. Not every
   exception is a misstatement — this is the assignment where that distinction
   matters most.
2. Separate adjusted from unadjusted.
3. Compare the unadjusted total to overall materiality (420,000) and to clearly
   trivial (21,000).
4. Conclude: is the aggregate effect material? State the report implication.

**Deliver:** completed `WP-SAD.csv` and a one-page conclusion memo.

---

## Assignment 10 — Scope and limitations

Write the limitations section for the workpaper. At minimum, address:

1. Purchase-order approval timestamps are absent, so approval sequence cannot
   be tested.
2. The value-flow population's completeness is unverified.
3. Five of eleven planned procedures could not be performed by the software and
   were performed manually — describe the effect, if any, on the evidence
   obtained.
4. The audit covered accounts payable and cash disbursements only.

**Deliver:** a limitations memo, one page.

> Point 3 is the one to think hardest about. Manual performance is not
> inherently weaker evidence — but it is less reproducible, and the workpaper
> should say so plainly rather than leave a reader to assume the tool did it.
