# Full system status, 30 Sep 2026

*Claude, end of day. Everything the roadmap's finish line and the Learn plan
need, not a page list. Each line says how it was checked, or "not checked".*

**What Noesi is:** a supplement to an audit. It tests the client's data, shows
what it found, and says what it could not test. It is not audit software: no
sign-offs, approvals or file management get built.

## The finish line (docs/ROADMAP.md)

> Every one of the 13 Kestrel modules runs in the Workbench and matches the
> answer key, from files as a learner would load them. Oceanview runs
> privately as the check that nothing is fitted to Kestrel.

| Part | Status | How checked |
|---|---|---|
| Workbench matches the key | **162 of 164 lines**, 0 unexplained (evening; 157 of 160 in the morning) | `finish_line_check.py`, rerun after every fix |
| The 2 lines left | PO overrun (Summit Tire PO 1021) and unrecorded liability (check 4433): wait for roadmap C (QuickBooks exports) | the check's own notes |
| The learner's path | Every lesson's "In Noesi" steps name real tabs; every procedure a lesson lists exists, ran on the demo, and has the status the lesson claims. Two wrong steps fixed: lesson 1 sent learners to Scope & Policies for materiality (it is on Planning & Risk and SAD); every lesson said to "paste the session token" (nothing asks for one) | script over lessons.ts + the demo seed; prose read by hand |
| "From files as a learner would load them" | **The lessons do not do this.** Every lesson starts from the preloaded Kestrel demo; no learner uploads or maps a file. The finish line and the lessons disagree: James to decide which is right | lessons.ts (DEMO_START) |
| Oceanview (nothing fitted to Kestrel) | Full run repeated today: all 35 differences from the 29 Sep run trace to the engine fixes made on 29 Sep; no engine file changed on 30 Sep (git diff f0bbdce..HEAD on the procedure engines, SAD and readiness is empty) | run_full.py pass 2; private repo f0e56b1 |

## The 13 modules

| # | Module | Learn lesson | Video script | Silent preview |
|---|---|---|---|---|
| 1 | Engagement setup | written | yes | rebuilt 30 Sep on current screens; every paragraph checked by frames |
| 2 | Planning | **coming**: waits for roadmap C | no | no |
| 3 | Journal entries | **coming**: roadmap C | no | no |
| 4 | Revenue and receivables | **coming**: roadmap C | no | no |
| 5 | Payables | written | yes | rebuilt 30 Sep on current screens; every paragraph checked by frames |
| 6 | Cash | **coming**: roadmap C | no | no |
| 7 | Inventory | **coming**: roadmap C | no | no |
| 8 | Payroll | written | yes | rebuilt 30 Sep; every paragraph checked by frames |
| 9 | Property and equipment | written | yes | rebuilt 30 Sep; every paragraph checked by frames |
| 10 | Debt, equity, accruals | written | yes | rebuilt 30 Sep; every paragraph checked by frames |
| 11 | Estimates and related parties | written | yes | rebuilt 30 Sep; every paragraph checked by frames |
| 12 | Completion | written | yes | rebuilt 30 Sep; every paragraph checked by frames |
| 13 | The opinion | written | yes | built 30 Sep; every paragraph checked by frames |

Voiced: none. Fact check on all 8 scripts: every figure passes
(`check_facts.py`, today).

## What blocks a full system

1. **Roadmap C: your real QuickBooks exports.** The case's QuickBooks files
   for trial balances, aging, bank reconciliations and inventory valuation
   are imitations of the report layouts (the case README says so). The import
   recipes must be built to real exports, or they are fitted to a guess.
   This one item holds 5 of the 13 modules and the last 3 key lines.
   Needed from you: the Kestrel company's Trial Balance (both year ends),
   A/R Aging Summary, Inventory Valuation Summary, both Reconciliation
   Reports, the Journal, and the General Ledger, exported from QuickBooks.
2. **Learners never load files themselves** (see above): either the finish
   line's wording changes to "on the Kestrel demo", or lessons gain a
   "load it yourself" step. Your call.
3. ~~Oceanview full run~~ done today (see above).
4. **Videos:** all 8 silent previews built and checked (30 Sep); m10 scene 5 opens on the top of the Runs list before the debt findings (a loose shot, nothing wrong on screen). Next: your approval per module, then voicing (about 900 credits a module; your OK each time).
5. **Scripts, lessons and videos for modules 2, 3, 4, 6, 7**, after roadmap C.

## Evening, 30 Sep: page-by-page check of the Workbench (Claude)

Every tab was opened on a fresh `--demo` in a scratch folder (Playwright,
real Chromium; screenshots read) and each odd figure looked up in the key
first: planted and found as the key expects, disagreeing with the key
(possible bug), or not covered by the key.

**One disagreement with the key, fixed:** the confirmation method Kestrel
uses (nonstatistical) showed as "left out, no reason" on Coverage, Draft
Opinion and Lock & Export although it ran and matched the key. The service
ignored the partner's include/leave-out choices; the check never looked.
Fixed (`9d80e3e`); two check lines added, shown to fail on the old code.

**Fixed, each verified on screen or by test (commits 9d80e3e..000d37f):**
open items readable (no raw-key dump); amounts as 7,325.00; plain procedure
names; every setting explained with its unit; "largest single change" label
on What Changed; Flow Map shows rows set aside and covers all seven cycles;
Sources no longer offers to map a mapped file again; A/P subledger tied to
the trial balance (no GL export needed; 287,640.18 both sides, as the key);
performance materiality is a setting (was fixed at 75%); CSV downloads of
findings and coverage (formula-safe); findings tagged with the assertion
their procedure states (movements by account type and direction).
Tests 499 -> 505. Oceanview pass 2: findings unchanged.

**Not fixed, and why:**
- Payment-to-ledger posting and credit memos after year end need the Journal
  read as a general ledger / sales register: that is the Journal import,
  which waits on a real QuickBooks Journal export (roadmap C). Sales cutoff
  also needs shipping dates, which no QuickBooks report holds.
- Payment-to-bank clearing stays blocked correctly: a July cutoff statement
  is not the year's bank activity.
- New forensic tests (check-number gaps, first-digit/Benford, vendor vs
  employee in payables, cash-theft tests): they would add leads to Kestrel
  and Oceanview that no key covers (e.g. Kestrel's checks jump from 4141 to
  about 4400). Needs James's decision (with E3) on extending the cases' keys.

**Not checked:** buttons that change data (propose, leave out, dispose,
lock, export, archive, delete) were not clicked; Harborline and Oceanview
were not opened in the Workbench screens.

## Decisions still yours

- Approval-workflow features against the supplement rule: chairs (preparer,
  reviewer, partner), "mark reviewed / approve" on runs, concurrence on
  dispositions and significant risks, "mark done" stages and checks, and the
  signed lock. Keep, simplify or remove?
- Forensic tests above: build them, and extend the Kestrel key for them?
- E3: Kestrel's two missing fraud schemes (add to Kestrel, or teach on Harborline).
- Harborline in the load list; `--demo` in your launcher.
- The 3 Fraud-tab findings not in the key (loan payments, an equipment
  purchase, tax payments): add to the key as expected, or leave.
