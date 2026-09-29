# Plan (for later): a full-audit course on Kestrel Valley

Written 2026-09-29. **Nothing here starts until the engine work below is
done.** Lessons and videos come last, so each is made once.

## What exists today

- **The Learn app** (`apps/studio-ui/src/learn/`, wrapped by
  `apps/learn-streamlit/`). Lessons in planning, fieldwork, completion and
  fraud tracks, all built on **Harborline** (payables in depth). It has an
  Excel audit view, a paper-trail trace, and lesson videos.
- **Harborline** is original, first committed on 2026-08-07, seven weeks
  before the Oceanview case was bought. It shares none of Oceanview's names
  and is already public. It stays as it is: the payables deep dive.
- **Kestrel Valley** (`case-studies/kestrel-valley-cycle/`) is a complete,
  QuickBooks-shaped audit, written independently of Oceanview. It has frozen
  answer keys for every area (parts 0–3).
- **Oceanview** stays private. It is never quoted, copied, shown, or used as
  a template for lesson content.

## The course: "Audit a small business end to end, with Noesi"

Build it as a **new track in the existing Learn app**, not a separate app.
It reuses the lesson engine, Excel view, trace and video player, so there is
one codebase to maintain. Harborline lessons stay as they are.

Each module follows the same four steps:
1. **The audit idea:** what the procedure is for and which assertion it
   addresses (short, plain words).
2. **Do it by hand:** the learner works the Kestrel file in a spreadsheet
   (the Excel view) and writes down their answer.
3. **Do it in Noesi:** load the same file in the Workbench, run the
   procedure, read the findings.
4. **Compare:** the learner's answer, Noesi's findings, and the answer key.
   It is also where Noesi says what it *cannot* do (observation,
   confirmation, judgment).

| # | Module | Kestrel data | Noesi procedures |
|---|---|---|---|
| 1 | Engagement setup | trial balances, materiality | engagement, team roles, period, cycles |
| 2 | Planning | trial balances, performance materiality | TB analytics, performance materiality |
| 3 | Journal entries (fraud risk) | Journal | JE testing, population completeness |
| 4 | Revenue and receivables | aging, invoices, confirmations | listing tie, cutoff, credit memos, confirmations |
| 5 | Payables | vendor list, bills, payments, unpaid bills | vendor twins, duplicate bills, split payments, subledger tie |
| 6 | Cash | reconciliation reports, cutoff statement | bank reconciliation, interbank transfers (kiting) |
| 7 | Inventory | valuation, count tags, pricing | count ↔ listing, pricing projection |
| 8 | Payroll | register, employee master | register tests (ghost, terminated), register to ledger |
| 9 | Property and equipment | asset register, vouching | rollforward, depreciation, additions |
| 10 | Debt, equity, accruals | schedules, covenants | rollforwards, covenant, recompute |
| 11 | Estimates and related parties | prior estimates, related-party list | retrospective review, matching |
| 12 | Completion | July journal, representation letter, final SUM | subsequent events, going concern, representation letter |
| 13 | The opinion | everything | draft opinion and the partner's decisions |

**Learner answers vs. keys.** The instructor keys (`instructor/`) are shown
only after the learner submits, as Harborline does now.

## Videos (ElevenLabs)

- **One short video per module (13).** Each follows the four steps and shows
  real Workbench screens.
- **Order of work:**
  1. Script every video first, in plain words, and check each script against
     the case figures.
  2. James approves the scripts and the credit estimate.
  3. Then voice them.
- **Credits:** budget roughly from past use (about 400–500 credits
  re-voiced one scene per video in the cycles rollout). A full new video
  costs several times that; estimate per script before voicing.
- **Nothing is voiced until the Workbench screens it shows exist** (see
  below). Otherwise the videos would need redoing.

## What must be done first (the engine and Workbench)

1. **The final Codex review** of `7dbb2c8..f5d6e61`, and its fixes.
2. **A real QuickBooks Journal export**, so the Journal import is built to
   the real layout. It fixes J1–J4 and the subsequent-period gaps (C4).
3. **The QuickBooks trial balance, aging, inventory and reconciliation
   recipes** (K4–K14), so learners load the raw exports, not hand-prepared
   files.
4. **Workbench screens:**
   - switching cycles on and setting their policies;
   - the period start;
   - the draft opinion page.
5. **The account-to-statement-line mapping step (K8)**, so going concern
   and ratios work on the learner's own trial balance.
6. **Push the engine**, with James's approval.

Only then: lesson text, then the Learn-app track, then scripts, then videos.

## Rough effort

- **Lessons and track:** 13 modules. About two to three working sessions of
  building, plus James's review of every lesson.
- **Videos:** 13 scripts in one or two sessions. Voicing follows script
  approval and depends on credits.
