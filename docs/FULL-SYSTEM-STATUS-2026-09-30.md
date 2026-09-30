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
| Workbench matches the key | **157 of 160 lines**, 0 unexplained | `finish_line_check.py`, today |
| The 3 lines left | Wait for roadmap C (QuickBooks exports) | the check's own notes |
| The learner's path | Every lesson's "In Noesi" steps name real tabs; every procedure a lesson lists exists, ran on the demo, and has the status the lesson claims. Two wrong steps fixed: lesson 1 sent learners to Scope & Policies for materiality (it is on Planning & Risk and SAD); every lesson said to "paste the session token" (nothing asks for one) | script over lessons.ts + the demo seed; prose read by hand |
| "From files as a learner would load them" | **The lessons do not do this.** Every lesson starts from the preloaded Kestrel demo; no learner uploads or maps a file. The finish line and the lessons disagree: James to decide which is right | lessons.ts (DEMO_START) |
| Oceanview (nothing fitted to Kestrel) | Full run repeated today: all 35 differences from the 29 Sep run trace to the engine fixes made on 29 Sep; no engine file changed on 30 Sep (git diff f0bbdce..HEAD on the procedure engines, SAD and readiness is empty) | run_full.py pass 2; private repo f0e56b1 |

## The 13 modules

| # | Module | Learn lesson | Video script | Silent preview |
|---|---|---|---|---|
| 1 | Engagement setup | written | yes | rebuilt today, checked by frames |
| 2 | Planning | **coming**: waits for roadmap C | no | no |
| 3 | Journal entries | **coming**: roadmap C | no | no |
| 4 | Revenue and receivables | **coming**: roadmap C | no | no |
| 5 | Payables | written | yes | rebuilt today, checked by frames |
| 6 | Cash | **coming**: roadmap C | no | no |
| 7 | Inventory | **coming**: roadmap C | no | no |
| 8 | Payroll | written | yes | built 29 Sep (you OK'd it); re-filming now |
| 9 | Property and equipment | written | yes | built 29 Sep; re-filming now |
| 10 | Debt, equity, accruals | written | yes | built; not reviewed |
| 11 | Estimates and related parties | written | yes | built; not reviewed |
| 12 | Completion | written | yes | built; not reviewed |
| 13 | The opinion | written | yes | **not built** |

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
4. **Videos:** finish previews for 8-13, then your approval per module, then
   voicing (about 900 credits a module; your OK each time).
5. **Scripts, lessons and videos for modules 2, 3, 4, 6, 7**, after roadmap C.

## Decisions still yours
- E3: Kestrel's two missing fraud schemes (add to Kestrel, or teach on Harborline).
- Harborline in the load list; `--demo` in your launcher.
- The 3 Fraud-tab findings not in the key (loan payments, an equipment
  purchase, tax payments): add to the key as expected, or leave.
