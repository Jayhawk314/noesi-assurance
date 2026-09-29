# Plan (for later): the Kestrel Learn app

Agreed with James on 2026-09-29. **Nothing here starts until the engine and
Workbench work in "When it starts" is done**, so lessons and videos are made
once.

## Decision

- **Harborline is not used for new teaching.** It is too close to the
  Oceanview case (a marine company, the same kind of structure).
- **Nothing is deleted.** The Harborline Learn app stays online, reachable
  by its link.
- **Harborline stays in the code** as the internal engine test (the fixed
  "11 procedures, 52 findings" baseline).
- **A new Learn app is built on Kestrel Valley** (option A: a copy, not a
  swap inside the old app). Kestrel was written independently of Oceanview,
  and Oceanview content is never used.

## Two apps side by side

| | Harborline app (today) | Kestrel app (new) |
|---|---|---|
| Lessons source | `apps/studio-ui` | a copy, e.g. `apps/learn-kestrel-ui` |
| Streamlit host | `apps/learn-streamlit` | a copy, e.g. `apps/learn-kestrel-streamlit` |
| Streamlit Cloud | the existing app and address | a second app, its own address |
| Case | Harborline (payables) | Kestrel (the full audit) |
| Status | unchanged, online by link | built new |

**The switch.** When the Kestrel app is ready, the public links (repo
README, website, video descriptions) point to its address. Harborline's
address keeps working.

## What the Kestrel app teaches

There are 13 modules, one per audit area. Each has the same four steps:
1. **The idea:** what the procedure is for, in plain words.
2. **By hand:** work the Kestrel file in the spreadsheet view and write
   down an answer.
3. **In Noesi:** load the same file in the Workbench, run the procedure,
   read the findings.
4. **Compare:** the learner's answer, Noesi's findings, and the answer key
   (shown only after the learner answers). This step also says what Noesi
   cannot do (observation, confirmation, judgment).

| # | Module | Kestrel files |
|---|---|---|
| 1 | Engagement setup | trial balances; materiality, team, period, cycles |
| 2 | Planning | trial balances, performance materiality |
| 3 | Journal entries | Journal |
| 4 | Revenue and receivables | aging, confirmations |
| 5 | Payables | vendor list, bills, payments, unpaid bills |
| 6 | Cash | reconciliation reports, cutoff statement |
| 7 | Inventory | valuation, count tags, pricing |
| 8 | Payroll | payroll register, employee master |
| 9 | Property and equipment | asset register, vouching |
| 10 | Debt, equity, accruals | schedules, covenants |
| 11 | Estimates and related parties | prior estimates, related-party list |
| 12 | Completion | July journal, representation letter, final summary |
| 13 | The opinion | the draft opinion and the partner's decisions |

## Videos (ElevenLabs)

- New videos for Kestrel, one per module. The Harborline videos are not
  reused.
- **Scripts first:** plain words, each checked against the case figures.
- **James approves** the scripts and the credit estimate before any voicing.
- Videos show real Workbench screens, so they come after those screens
  exist.

## When it starts

In order, before any lesson or video:
1. ~~Fix the final Codex review's findings.~~ Done. No further review round.
2. A real QuickBooks Journal export from James, then the Journal import
   built to it.
3. The QuickBooks recipes for trial balance, aging, inventory and bank
   reconciliation, so learners load raw exports.
4. Workbench screens for cycles and policies, period start, and the draft
   opinion.
5. The account-to-statement-line mapping step (K8).
6. Push to GitHub, with James's approval.

Then: the Kestrel app copy, the lessons (James reviews each), the video
scripts, and the voicing.

## Rough effort

- **App copy and 13 lessons:** about two to three sessions, plus James's
  review.
- **Scripts:** one or two sessions.
- **Voicing:** after approval; it depends on credits.
