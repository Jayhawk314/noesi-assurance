# Assignment 11 — The client sends a corrected file

Do this after you have run all eleven procedures and disposed at least a
few findings (Assignments 1–9, or the walkthrough through step 9).

## The situation

In February the controller emails a "corrected" voucher extract:

> "Our first export dropped a voucher and had a couple of keying errors.
> Please use this one instead." — `revision/vouchers_revised.csv`

Real engagements get files like this constantly. The file is not the
problem. The problem is that you have already done work on the old one:
runs, findings, judgments, maybe a draft SAD. Which of those still stand?

## Part A — predict before you look (spreadsheet only)

1. Open `data/vouchers.csv` and `revision/vouchers_revised.csv` side by
   side. List every row that was added, removed, or changed, with the
   dollar effect of each.
2. Classify each change against the plan's thresholds: below clearly
   trivial (21,000), above it, or above performance materiality (315,000).
3. For each change, predict which of your earlier findings it touches,
   and whether any disposition you recorded is now resting on numbers
   that no longer exist.
4. Look hard at the row that was added. Compare it with every existing
   voucher from the same vendor. What is it really?

**Deliver:** `WP-A11-revision.csv` (one row per change: key, before, after,
effect, threshold class, findings touched) and a short prediction memo.

## Part B — load it and read the impact report

1. As the preparer, upload `vouchers_revised.csv` on **Sources &
   Mappings**, propose its mapping, approve it as the reviewer, and
   normalize it. The workbench now uses the newest Vouchers file for
   everything that follows.
2. Open **What Changed**. It shows three things, and changes nothing:
   - the file comparison (what moved, and how much it matters),
   - which runs are now stale (only procedures that read Vouchers),
   - one card per finding whose standing moves, with the action it
     implies: *dispose*, *revisit your disposition*, or *nothing after a
     rerun*.
3. Reconcile the report to your Part A prediction. Explain every
   difference.

## Part C — act on it

1. Rerun the stale procedures, then send them back through review and
   approval. A reviewed run built on the old file is not reviewed work on
   the new one.
2. Revisit every judgment the report flags. Where a finding disappeared
   because the client "corrected" the record, your note must say what the
   correction was and why you accept it, or why you do not.
3. Update the SAD and say, in one sentence, whether the conclusion moved.

## The questions that matter

- **A finding that disappears is not a finding that was wrong.** One
  exception in this file vanishes because the voucher was edited to match
  what was received. What did the company actually pay? Is that
  resolved, or has the exception moved somewhere the tool now reports
  differently?
- **Silence again.** No procedure in the library tests for duplicate
  invoices. Whatever you concluded about the added voucher in Part A, the
  tool will not say it for you. What does the report *not* show?
- **Who asked for the correction?** A client correcting records *after*
  seeing your requests is evidence about the client, not only about the
  records.
