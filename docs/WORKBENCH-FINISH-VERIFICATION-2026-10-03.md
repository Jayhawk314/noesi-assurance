# Workbench finish-map verification — 3 October 2026

This records what this session checked. It does not declare the one-user audit
supplement finished or ready for client data. Videos remain paused.

## 1. Independent review of 04d3c5f and c38d567

See `docs/reviews/REVIEW-2026-10-03-workbench-commits.md`. The review read both
diffs and reproduced an older-packet compatibility bug: a v4-shaped packet
with `HIGH_RISK_RESPONSES_NOT_PERFORMED.items` and no `by_risk` rendered a
blank response cell. A local fix now maps a unique risk title and shows an
unassigned warning when duplicate titles make attribution ambiguous. An
invented-packet regression covers both cases. A second agent later reviewed
the new code and identified further stale-result paths; see section 3.

## 2. Invented-data ordinary UI journey

In a new throwaway local store under `.tmp/invented-journey-2026-10-03`,
Playwright clicked the built Workbench UI to create **Invented Test Company**,
upload `journal.csv` and `payments.csv`, choose and confirm their roles, load
8 journal lines and 1 payment, scope journal entries, and set the Benford
minimum to 4. The Benford run showed **partly tested**: four journal amounts
were tested and the one-payment population was refused. A follow-up note was
saved on the refusal. The engagement was archived, restored, and reopened.
SQLite then showed one open engagement, the two loaded dataset row counts, one
completed run, and the saved `follow_up` note. The browser-downloaded 10,263
byte JSON record passed all `verify_packet` checks, including the journal
status recorded at export.

Folder upload through the UI added `vendor_list.csv` and reported that
`readme.xyz` was skipped. The stored follow-up note was visible again after
reopening the engagement. A later UI pass set materiality to 1,000, added an
invented low risk, and saved a reason for leaving out the unsupported journal
population-completeness procedure. After a rerun, the old Benford run stayed
marked historical and the latest run was current.

The **UI evidence-replacement click and What Changed after replacement were
not completed**. Browser automation failed repeatedly before that click and
the check was bounded. An invented-data service regression does verify that a
replacement dataset marks the latest run stale. This does not substitute for
the missing clicked workflow.

## 3. Screen wording and freshness

All eleven engagement tabs opened on the restored invented store without an
unexpected error. Runs & Findings, Fraud, SAD & Completion, Draft Opinion, and
Export showed the stale-result limit after a UI policy change from 4 to 1,000.
The Fraud header distinguishes current findings from historical findings on
stale runs; the SAD conclusion is labeled historical while results are stale.
SAD & Completion now includes completion readiness and links to the tabs that
clear its open items. Known readiness codes are no longer printed below their
plain-language descriptions; unknown codes still show rather than disappear.
The Flow Map calls procedures outside its diagrams “Other procedures” and
explains the cross-cycle Fraud tab. Run details were opened in the browser.

This was a text and selected-action walkthrough, not a visual layout review or
an exhaustive click of every control. Flow Map's other cycle diagrams, all
evidence disclosures, every disposition type, and every completion decision
were not exercised in the browser. The exported HTML working paper still
prints some internal readiness codes. The general UI replacement path remains
the concrete unfinished finish-map check.

A second agent independently reviewed the new stale-result code and identified
three gaps: a blocked or partial current population could mask a stale older
run, a failed fraud rerun could make older findings appear current, and a
failed completion rerun could leave an older SAD schedule styled current. Each
received a general fix and an invented-data regression. The reviewer checked
the final failed-rerun logic and found two misleading messages; those messages
were corrected afterward. The last wording edits have not had another
independent review.

## 4. Recovery and client-data boundary

The local server was stopped before an invented-store backup. `backup create`
reported one engagement, three files, schema 12, and a valid 17-entry journal.
`backup verify` passed. `backup restore` wrote a new `restored` folder, and
the Workbench opened it. All eleven tabs opened there; its browser-downloaded
10,690 byte record passed offline `verify_packet`.

This was a small **unencrypted invented-data** drill. It does not satisfy the
real-client P0 requirements: protected encrypted device and backup storage,
documented restore practice on the intended installation, controlled
retention, pinned release evidence, and firm methodology validation. The
current tests do not establish million-row capacity, broad import support,
or professional audit accuracy. See `docs/PRODUCTION-READINESS.md`.

## Verification and custody

- `python -m pytest tests -q`: **580 passed** before the final two wording
  edits, after the fixture was corrected to set policy and materiality before
  its runs.
- `npm run build` in `apps/workbench-ui`: passed.
- Kestrel finish-line calibration: **174/176 match, 0 unexplained**. The two
  named QuickBooks gaps remain roadmap C. This is calibration, not proof for
  arbitrary client data.
- No push, publication, external upload, or credit spend. Pre-existing
  uncommitted and untracked files were preserved.

## Remaining order

1. Finish the clicked UI replacement/What Changed check on invented data.
2. Review the final wording and complete a clicked pass of replacement,
   What Changed, and other controls not exercised above.
3. Keep the P0 client-data boundary separate from teaching readiness. Videos
   stay paused.
