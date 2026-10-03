# Workbench finish map — 3 October 2026

This is a handoff, not a claim that Noesi is finished. Read `AGENT-WARNINGS.md`
and `THE-REAL-GOAL.md` first. **The Workbench is the real one-user audit
supplement.** Kestrel, Oceanview, Harborline, Learn, Studio, and videos are
calibration or teaching surfaces. Do not fit the engine to a case or use a
case-key match as proof that arbitrary client data works. Keep videos paused.

## What is actually evidenced

- At local commit `c38d567`, `python -m pytest tests -q` passed 575 tests and
  the Workbench UI build passed. The Kestrel finish-line check ran 174/176,
  zero unexplained; its two absent QuickBooks-supported lines remain named in
  roadmap C. Those are test results, not a complete audit validation.
- On a throwaway Kestrel store, ordinary browser clicks opened the Workbench
  tabs without an error bar. A policy setting saved, a finding disposition
  and revised note saved, and the SAD displayed the final key's schedule.
- A real bug was found in the Workbench's downloaded audit record: browser
  JSON reserialization broke its offline digests. `c38d567` downloads the
  server's exact bytes; the actual browser-downloaded file then passed all
  `verify_packet` checks. This fix has **not had independent review**.
- The backup/restore command and a Kestrel-sized recovery drill were reported
  previously. `docs/PRODUCTION-READINESS.md` states its custody limits.

## Finish in this order

1. **Independent review of recent Workbench changes.** Review local commits
   `04d3c5f` (refusal-limited runs and retained edits) and `c38d567`
   (verifiable download), especially false claims of testing and export
   compatibility. Review only first; record possible bugs and evidence.
2. **General Workbench user journey on invented data.** Through normal UI
   actions, create an engagement, upload a small non-case CSV set, confirm
   mappings, load it, set scope/policies, run applicable procedures, inspect
   a refusal/partial result and finding, save a disposition, reopen the
   engagement, download the record, and verify it offline. Check persisted
   database state against what the screen says. Exercise archive/restore and
   folder upload on a throwaway store. Fix only reproducible product bugs,
   with invented-data regression tests. An internal service call alone is
   not a substitute for a clicked workflow.
3. **Auditor-facing honesty and coverage.** Check each Workbench screen for
   usable actions and whether wording distinguishes not run, refused,
   partly tested, and tested. Check that changed policy inputs or replaced
   evidence do not leave a stale result looking current. Assess remaining
   raw identifiers and Flow Map/completion display issues in
   `docs/WORKBENCH-WALKTHROUGH-2026-10-03.md`; that document predates some
   fixes, so reproduce before changing code. Do not invent an audit
   conclusion or suppress correct figures for a video.
4. **Real-client boundary, separately from teaching readiness.** Before
   entrusting client data, meet `docs/PRODUCTION-READINESS.md`: protected
   encrypted device and backups, a documented restore drill, retained
   release/test evidence, firm retention and methodology validation.
   Million-row capacity, broad import formats, and professional validation
   are not established by the current tests. State supported limits rather
   than promising universal files or audit accuracy.
5. **Only then resume teaching work.** James may run Oceanview privately as
   a learning and second-calibration exercise. Kestrel's public Learn app
   and videos come after the Workbench checks above; Oceanview content must
   never be published. No push, upload, publication, or credit spend without
   James's explicit yes.

## Stop condition for the next session

Do not announce “finished” from a green suite or Kestrel key alone. Report
exactly which ordinary Workbench journey ran, what was observed, what remains
untried, and whether another agent reviewed new code. If an output appears
wrong, say **“this may be a software bug”** and investigate before work on
videos or cosmetic polish.

## Working tree at handoff

`main` was nine commits ahead of `origin/main` after `c38d567`; no push was
made. The Learn lesson edit and video draft are deliberately uncommitted.
Numerous pre-existing untracked handoffs, personal notes, and a `.tmp` tree
remain; do not bulk-stage or delete them. The browser check used a unique
invented-data subfolder under `.tmp`; its test server was stopped. Recheck
`git status` at the start of the next session.
