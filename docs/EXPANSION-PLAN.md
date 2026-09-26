# Expansion plan: from partial coverage to the full suite

*Written 2026-09-25, after every main lesson (1–10) and fraud lessons F1–F6 got a video.
Nothing here is scheduled. The order is a first guess: working an integrated practice
case with the friction log ([learn/FRICTION-LOG-TEMPLATE.md](learn/FRICTION-LOG-TEMPLATE.md))
should re-rank it before any of it is built.*

Product gaps are already itemized in [PRODUCTION-READINESS.md §8](PRODUCTION-READINESS.md)
(8.1–8.9, plus the QuickBooks import fixes). This plan does not repeat them. It adds what
§8 doesn't track: which Learn badge each gap holds back, the case data each one needs, the
three unwritten fraud lessons, and what the lesson videos will need when a badge changes.

## 1. What holds each Learn badge back

**Main course**

| Lesson | Badge now | Missing in Noesi | §8 item | Needs new Harborline data |
|---|---|---|---|---|
| 1 Acceptance | part | acceptance / continuance record, independence confirmations, engagement-letter link | §4.1 | no |
| 2 Understanding, analytics | part | ratios and trends against expectations; journal-entry testing | 8.3, 8.1 | yes: trial balance (two years), full general ledger |
| 7 Revenue and AR | none | sales cutoff, AR aging, confirmation tracking with alternative procedures | 8.2 | yes: customers, invoices, cash receipts |
| 8 Cash | part | bank reconciliation (outstanding items, deposits in transit), receipts side, bank confirmations | 8.8 | partly: receipts |
| 9 Inventory | none | count records, test counts, count-to-book, price tests | 8.5 | yes: inventory listing |

Lessons 3, 4, 5, 6 and 10 already show "Noesi covers this step".

**Fraud track**

| Lesson | Badge now | Missing in Noesi | §8 item | Needs new data |
|---|---|---|---|---|
| F1 Why fraud happens | none | nothing: it is theory, and the badge is right | — | — |
| F2 Risk assessment | part | fraud flag on a risk; record of the team discussion and inquiries; journal entries | 8.9, 8.1 | journal entries only |
| F3 Billing schemes | part | registered duplicate-invoice test; tax ID / address matching | 8.6, 8.7 | no (`vendors.csv` has Tax ID and Remit City) |
| F5 Following one person | part | a per-person view of findings (created by / approved by) | not in §8 | no |
| F6 Kickbacks | part | noticing findings that share the same excess rate | not in §8 | no |

F4 already shows "covers this step".

## 2. Suggested order

1. **Fraud tests on the data we already have:** duplicate invoices (8.6; `ap_checks.duplicates()`
   exists, it only needs registering), tax ID and remit-city matching (8.7), a per-person view,
   same-rate clustering, and a fraud flag on risks (part of 8.9). Moves F2, F3, F5 and F6.
2. **Acceptance and independence** (§4.1). Small; no data needed. Moves lesson 1.
3. **Extend the Harborline case data:** customers, sales invoices, cash receipts, a two-year trial
   balance, a full general ledger, an inventory listing. Everything below depends on it. Keep the
   planted-exception style and the instructor answer key.
4. **Confirmation tracker** for receivables and bank confirmations (8.2, 8.8). Serves lessons 7
   and 8. SAS No. 150 will require cash confirmations for periods ending on or after
   December 15, 2028.
5. **Bank reconciliation** (8.8), **analytics** (8.3), **journal-entry testing** (8.1).
6. **Inventory** (8.5), at most "covers part": the count itself stays physical.
7. **Sampling** (8.4), when a practice case supplies populations too large to test in full.
8. **QuickBooks import fixes** (§8, six items). These matter to real users before any new module.

## 3. The fraud lessons still to write (F7–F9)

Planned in [learn/FRAUD-MODULE-OUTLINE.md](learn/FRAUD-MODULE-OUTLINE.md). Write each one after
the procedures it teaches exist, so its "In Noesi" section is true on the day it ships.

| Lesson | Question | Harborline material | Noesi today |
|---|---|---|---|
| F7 Following the money | How do you trace funds that leave and come back? | 48,500 to Bayview Advisory Partners (2026-11-03), to Meridian Holdings LC (11-05), back to Harborline (11-07) | `forensic.closed_value_flow`; can be written now |
| F8 Data analysis for fraud detection | How do you test everything and read the results well? | 52 findings across 11 procedures; PAY-2026-0025 silent under the 2% tolerance | best written after step 1 above; Benford stays a spreadsheet exercise (123 rows is too few) |
| F9 Preventing it next time | Which controls would have stopped each scheme, and who is told? | map F3–F7 to failed controls; draft AU-C 265 letter points | Noesi doesn't write the management letter |

Each gets the usual lesson video afterwards (facts, script, captures, silent preview, voice).

## 4. Lesson videos when a badge changes

- Only the "In Noesi" and "What it doesn't do" scenes change: about 15–20 seconds per video.
  The builds are scripted (`komposos-labs-videos/noesi_learn_videos/`), so re-rendering is free;
  re-voicing one paragraph is about 100 credits.
- Update the lesson's `noesi` block in the same commit, rebuild `apps/learn-streamlit/learn.html`,
  and commit only the final cut: every re-committed video adds its full size to git history.
- Optional polish already noted: real QuickBooks and Excel footage for lessons 5, 3 and 2
  (steps in each video folder's `HANDOFF.md`).

## 5. Bringing in an external practice case

What the Workbench accepts today, so a case's files can be judged before a session:

- **Accepted:** CSV, TXT, JSON, PDF, XLS, XLSX. Every file is kept unaltered with its SHA-256.
- **Not accepted:** images (JPG, PNG, scans saved as pictures).
- **Excel:** choose the sheet and the heading row; reading stops at the first blank row. Formatted
  workpapers (titles, merged cells, totals blocks) may need a clean listing sheet first.
- **Procedures run only on payables-shaped data:** the mapping roles are vendors, employees,
  purchase orders, goods receipts, vouchers, payments, bank, GL, value flows and the AP control
  balance. Revenue, receivables or inventory files can be stored as evidence but not tested.
- Keep purchased case materials and the filled-in friction log in the git-ignored `oceanview/`
  folder; they are licensed per student and must never be committed.
