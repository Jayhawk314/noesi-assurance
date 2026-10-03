# Review brief, 2 Oct 2026: the batch after the fixes check

For an independent reviewer (a fresh Claude or Codex session) who did not
build this work. Read `AGENT-WARNINGS.md` first, then `docs/ROADMAP.md`
(Direction, D9, D10, E2, E3, parking lot) and `docs/INDEPENDENT-REVIEW.md`.

**Report only.** Do not fix, commit or push. Write findings to
`docs/reviews/REVIEW-2026-10-02-batch.md`: each with severity, how you
confirmed it (command and output), and whether it is planted in the case,
as expected, a possible software bug, or not covered. Oceanview is a
purchased case: read `oceanview/` if useful, never quote its content in the
public repo.

## The commits (oldest first; all on `main`, the last five not yet pushed)

| Commit | What it claims |
|---|---|
| 4bfed89 | D9 stage 3: one user per engagement. No role checks, `assign_team`, team route or X-Acting-Principal (ignored); a mapping is confirmed in one step (`confirm_source_mapping`); old pending mappings confirm via `confirm_pending_mapping`; readiness team gate removed |
| a2cd564 | D10 in Kestrel: checks renumbered 4266-4433 with one planted gap 4422-4424 (key's 4421, 4425, 4429, 4433 kept); vendor Owen Pike Hauling named after employee E08; trial balances unchanged |
| a541e50 | E3: new role `Payment_approvals` and `forensic.self_approved_payments`; Kestrel `auditor/check_signatures.csv` (three DM Consulting checks prepared and signed by Dana Merritt) and `auditor/flow_of_funds.csv` (round trip Kestrel → Gallatin Display Works → Summit Loop Racing → Kestrel, 9,800); the round-trip test no longer names every client "Rockwood" (said to change no result) |
| ea8e02d, ab17c59 | Fraud lessons and manual ch. 5 teach the new tests; stale "prepared by hand" lesson lines corrected |
| 8f206a5, 13b94be, 9a2800a | Roadmap: C closed as it stands; E2 engine pass done (Oceanview Run 4); review items L1 and L3 accepted with reasons |
| f99a39b | "Map all" leaves out the raw exports a built schedule was made from |
| abd71cf | Review L2 (masked numbers not compared, phones on last seven digits, split names joined) and L6 (dead code, INDEPENDENT-REVIEW invariants 3-4 rewritten) |
| f01b9c7 | Benford in by default; demo minimum stays 1,000 (source as recalled, unchecked) |
| abaa49b | L5: contracts may name alternative input sets; the check sequence runs on the Journal alone; coverage reports `satisfied_by` |
| 8b79750 | PP&E: declining-balance depreciation recompute (double declining, 150%, or `ppe_declining_balance_factor`) |

## Rerun

    python -m pytest tests -q                                   # claimed 536 pass
    python case-studies/kestrel-valley-cycle/instructor/finish_line_check.py   # 172/174, 0 unexplained
    python case-studies/kestrel-valley-cycle/instructor/check_key.py           # 24/24
    node apps/learn-kestrel-ui/scripts/check-lessons.mjs        # 48 fraud answers, all tied
    (the three apps: npx tsc --noEmit; npm run build)

The finish-line and export scripts need the package `src` folders and
`apps/*` on PYTHONPATH (see `conftest.py`).

## Worth attacking

1. **D9 stage 3.** Any route or service call that still records a second
   person, a review or a sign-off; any way to act under a name other than
   the session's. Does an old database with pending mappings still load?
2. **Was the case fitted?** D10 and E3 changed Kestrel's generators. Check
   the trial balances did not move (`git diff a541e50~3 -- ...Trial_Balance*`),
   that `check_key.py` derives the new key lines from the files and not
   from the generator, and that the engine was not changed to make a
   Kestrel line match.
3. **The forensic tests on data not written for them.** Invent populations:
   checks across two bank accounts, voided checks with zero amounts,
   vendors with masked bank numbers, approval logs with stamps or blank
   preparers, value flows with a legitimate refund cycle. Look for false
   alarms and silent skips.
4. **L5's alternative inputs.** A client with both Payments and a Journal;
   with a Journal that numbers no checks; with an empty Payments file.
   Does coverage ever say executable when the run then refuses?
5. **Declining balance.** Recompute by hand on your own register:
   acquisitions and disposals mid-year under both conventions, an asset at
   salvage, a factor of 0 or text. Is "opening value = ending accumulated
   less this period's expense" sound, and is its limit stated?
6. **Honesty of the text.** Lessons, manual ch. 5 and the case README now
   describe these tests and schemes. Anything that overclaims, or names a
   figure the key does not hold?

## Known and stated (do not report as new)

L1 and L3 accepted with reasons (ROADMAP parking lot); Benford's 1,000 is
recalled, not checked; no screen was checked for this batch except the D9
Sources page; the two finish-line "not in Noesi" lines (PO overrun,
unrecorded liability) wait on exports that do not exist.
