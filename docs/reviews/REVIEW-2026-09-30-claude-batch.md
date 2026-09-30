# Independent review: commits 7cfb3fe, 76dfb83, 8da4827 (30 Sep 2026)

Reviewer: Claude (independent reviewer agent; did not build these commits).
Scope: the three local, unpushed commits `7cfb3fe`, `76dfb83`, `8da4827` (diff `f0bbdce..8da4827`).
I did not edit any source file, commit or push. I did not open anything inside `oceanview/`.

## Baseline checks (run this session)

| Check | Result | How |
|---|---|---|
| `python -m pytest -q` | **499 passed** | `.venv/Scripts/python.exe -m pytest -q`, output read |
| finish-line check | **157 of 160 match; 0 unexplained** (the 3 are roadmap C, QuickBooks exports) | `.venv/Scripts/python.exe case-studies/kestrel-valley-cycle/instructor/finish_line_check.py` |
| Migrations 10 + 11 on a pre-batch database | Applied cleanly; a **v1 lock made by the old code still verifies** after migrating | Extracted `f0bbdce` code to a scratch folder, used it to build a DB at migration 9 with a signed v1 lock (with a risk), then opened it with the new code |
| Archive / restore a locked engagement | Lock still verifies while archived and after restore | same scratch DB |
| v1 lock → unlock → relock (v2) | Relock verifies; superseded v1 in history verifies; flipping `fraud` in the DB afterwards gives `drift=['risks']`, `verified=False` | same scratch DB |
| Real DB `C:\Users\JAMES\.noesi-assurance\control.db` | Opened **read-only** (`mode=ro`) and backed up into scratch. It is already at migration 11; 2 engagements, both `open`, `archived_at` NULL, no lock snapshots. Never written. | sqlite3 backup |
| Oceanview content in the commits | Only the case name, its year end (since removed from the public code) and the loader path `oceanview/adapter/load_workbench.py`. No figures, vendors or documents. `oceanview/` is git-ignored. | `git diff f0bbdce..8da4827 \| grep -i oceanview`, `git check-ignore`, `git ls-files` |

## Findings, most severe first

### 1. HIGH: the draft working paper says "Opinion: unmodified" for an engagement that is not ready (reproduced)

`packages/assurance-workpapers/src/assurance_workpapers/workpaper.py:78-86` prints **"Opinion: <x>"** in bold whenever
`draft_opinion()["opinion"]` is set, and "Draft opinion (not settled)" only when it is None. Before this batch the paper was only
produced from a locked, verified packet, so readiness was already green. Commit 8da4827 now renders the same section on the
**draft** paper of any open engagement, and never shows `status: not_ready` or the readiness blockers.

Reproduced: a new engagement with **no data, materiality not set, risk stage not complete and all 6 completion checks open**
(`readiness.ready = False`, 4 blockers). `workpaper_html()` returns a DRAFT banner and then
**"Opinion: unmodified"**, basis *"uncorrected misstatements (0) are below materiality (0); no open scope limitation;
representations obtained"*. Representations were not obtained (`management_representations` is not done), materiality is 0.
The in-app Opinion tab shows the same label but puts "Not ready: see below" and the blockers next to it; the draft paper has neither.

Scenario: a preparer prints the draft paper mid-engagement; it reads as a clean opinion with representations obtained.

Related, older than this batch (not introduced here): `packages/assurance-domain/src/assurance_domain/opinion.py:141` writes
"representations obtained" whenever no representation is recorded as *missing*, and sets `opinion` to "unmodified" regardless of
readiness (`opinion.py` ~150-160). The draft paper is what now puts it in front of a reader without the "not ready" context.

Fix direction (not applied): on a draft, label it "Draft opinion (not settled)" unless `status == "draft_for_partner"`, and render
the readiness blockers on the draft paper.

### 2. HIGH: What Changed hides a changed amount on rows whose new key is duplicated, and calls it "none" (reproduced on Kestrel's own data)

`packages/assurance-application/src/assurance_application/impact.py:83-84` keys `Bank_reconciliation` and `Cutoff_statement` on
`(account, item_type, reference)`. On Kestrel these keys are **not unique**: Bank_reconciliation has 2 rows keyed
`checking|deposit in transit|Deposit`; Cutoff_statement has 4 rows keyed `checking|deposit|` (blank reference).
`diff_records.index()` (`impact.py:216-218`) keeps only the last row per key, so a change to the earlier row is never compared.

Reproduced (scratch copy of Kestrel loaded via `load_case`): adding **+250,000** to the first duplicate row in each file and running
`diff_records(..., thresholds(100000), role)` gives `changed: 0`, `significance: "none"`, `net_amount_change: 0.0`, with the key
listed in `duplicate_keys`. The UI (`apps/workbench-ui/src/screens/WhatChanged.tsx:101-127`) shows the "none" pill and a net of 0.00
at the top, and the duplicate-key note below without saying that those rows were not compared.

The comment at `impact.py:80-82` ("account, kind and reference identify the item") is false for Kestrel. The docstring
"Duplicate keys are reported rather than silently collapsed" is only half true: the key is reported, the change is collapsed.
The duplicate collapse itself is older than this batch; the new cycle keys expose it on the case.

Fix direction: when a key is duplicated in either version, compare those rows by content (the new `_diff_by_content`), or mark
the revision's significance "not_measured" rather than "none".

### 3. MEDIUM: Fraud tab shows a similarity score as a dollar amount (reproduced)

`apps/workbench-ui/src/screens/Fraud.tsx:138` renders `money(f.verdict.score)` in a column headed "Amount". For
`ap.vendor_relational_twins` the score is a match score: on Kestrel the Moraine Cycle Components twin finding has
`score = 1.0`, so the tab shows **"1.00"** as its amount. The other fraud tests' scores I printed (split payments 7,325.00,
duplicate bill 18,432.50, payroll 692.33, payments without bills, JE) are dollar amounts.
`FRAUD-TAB-CHECK-2026-09-30.md` compared finding identities, not this column, so it did not catch it.

### 4. MEDIUM: one partner can permanently delete a **signed, locked** engagement; the dialog does not say a signed lock is destroyed (reproduced)

`packages/assurance-application/src/assurance_application/service.py:225-283` deletes locked engagements too (the commit message
says so on purpose). Reproduced: deleting a v1-locked engagement removed its `lock_snapshot` and `lock_signature` rows; the journal
still verifies and gains an `engagement.deleted` line. The confirmation text (`apps/workbench-ui/src/App.tsx:275`) lists "files,
mappings, runs, findings, team and settings" and does not mention the signed lock, signature or audit file.

This is a judgment call for James, not a code bug: a signed audit file normally has a retention period (AU-C 230 assembly and
retention), and here one partner can erase it after typing the name. Options: refuse delete while locked (archive only), or at least
name the signed lock in the dialog. Note also that roles come from the `X-Acting-Principal` header, so on this single-user local
server any session holder can act as the partner (existing design, not new in this batch).

### 5. MEDIUM: Fraud tab counts a failed run as "run" (reasoned, not reproduced)

`service.py:1244`: `"run": sum(1 for t in tests if t["last_run"])`, and `last_run` is the latest run of any status, including
`error` (`service.py` fraud_view: `latest[...] = run` for every run). A fraud test whose only run errored is counted in
"N of 11 fraud tests run". Its findings column would be 0 (findings come only from non-error runs), so a failed test contributes
to "run" with 0 findings, which reads closer to "ran, clean". The row itself does show "error, <date>". I did not force an
error run to confirm on screen.

### 6. LOW: sign-off separation of duties does not hold for items completed before this batch (reproduced)

`service.py:1370` refuses a sign-off only when `done_by == actor`. Stages and completion checks marked done before this batch have
no `done_by`, so the person who did them can sign them off. Reproduced: a stage completed by `alice` under the old code; `alice`
(partner) then signed it off with the new code without error. Sign-off is not a lock gate yet (commit message says so), which
limits the impact. Fix direction: treat a missing `done_by` as "unknown, needs re-marking" rather than "anyone".

### 7. LOW: materiality preview and saved amount can differ by a cent (reproduced arithmetically)

UI preview `apps/workbench-ui/src/screens/Risk.tsx:39-40` uses `Math.round(base*pct)/100` (half up); the server
(`service.py` update_workflow materiality) uses `Decimal.quantize` (banker's rounding, half even). Example: benchmark 250,000.10 at
5%: UI shows **12,500.01**, server saves **12,500.00**. The UI sends only benchmark and percentage, so it is not refused; the saved
figure silently differs from what was previewed. Checked with node and Python, not by clicking the UI.
Also: `Decimal("NaN")` or `"Infinity"` as the benchmark raises an uncaught `InvalidOperation` on comparison/quantize (reasoned).

### 8. LOW: bulk dispose can report "N selected" and silently save fewer (reasoned)

`apps/workbench-ui/src/screens.tsx:672-691, 776`. The loop only applies to `shown ∩ picked`. Changing the procedure/status
filters clears `picked`, but toggling "latest run of each procedure only" does not; a finding from an earlier run can stay picked
while hidden, and is then skipped with no message while the header still counts it. The skip is in the safe direction (nothing
unintended is written). Stale versions are handled correctly: each call sends the row's `disposition.version`, a conflict lands in
the "not saved" list, and duplicates across runs are de-duplicated by `finding_uid` (dispositions are keyed by `finding_uid`, so
copies share one version). After a partial failure the selection is cleared, so the user must re-pick the failed ones.

### 9. LOW: migration 11 restores `status` but not `version` for old-style archives (reasoned)

`packages/assurance-persistence/src/assurance_persistence/database.py:361-379`. Its comment says the old archive changed "status
and version"; the migration puts back status only. A locked engagement archived by the interim code would still fail verification
(`drift=['engagement']`). Only databases that ran the uncommitted interim code are affected. The real DB copy has 1 historic
`engagement.archived` event but no archived rows and no locks, so it is unaffected. The migration test
(`tests/unit/test_review_2026_09_30.py:78`) checks status only.

### 10. LOW: archive guard is checked outside the write transaction (reasoned)

`_require_unlocked` / `_require_not_archived` read `archived_at` before `run_command`; other writes do not touch the engagement
version, so a write that starts just before an archive can land after it. Same pattern as the existing lock check; low risk on a
local single-user server.

### Test gaps

- No test locks with the **old** (v1) code and verifies after migration; the existing tests lock with new code (v2). I did it by
  hand above and it passed. Worth a fixture with a stored v1 manifest.
- No test that the draft paper does not show a settled opinion when not ready (finding 1).
- No test with duplicate cycle keys in What Changed (finding 2).

## What held up (verified)

- Lock manifest v2: verification re-derives in the schema the lock was signed in; v1 locks still verify; the fraud flag is signed in
  v2 and tampering it breaks verification.
- Archive/restore touch only `archived_at`; status and version (which the lock signs) are untouched; locks verify throughout.
  Archived engagements refuse lock/unlock and every `_require_unlocked` write.
- Archive, restore, delete are partner-only inside the transaction; delete needs the typed client name and a reason; the journal
  stays one intact hash chain after delete.
- Procedure exclusion requires the partner and a 10+ character reason, stored in the workflow document the lock hashes.
- Sign-off requires reviewer or partner and refuses the person who marked the item done (for items marked after this batch); editing
  the item clears the sign-off.
- The draft paper has no signature, digest or verification section; it carries a "DRAFT — not locked, not signed" banner and its own
  limitations text; it requires a team role; it is not journaled as an export. (Its opinion section is the problem in finding 1.)
- Oceanview: no case content committed. Note: `docs/OCEANVIEW_MARINE_CASE_MAP.md` is **untracked and not git-ignored**, so a
  careless `git add -A` would commit it. I did not open it.

## Not checked

- The UI in a browser (no clicks, no screenshots); UI findings are from reading the code.
- Loading the real Oceanview case (I did not run its loader or open `oceanview/`).
- Concurrency (finding 10) and the error-run case (finding 5) were not reproduced.
- The Kestrel Learn app commits (older than this batch) were out of scope.

## Response (Claude, 30 Sep 2026), each with a test in tests/unit/test_review_2026_09_30.py

1. **Fixed.** A not-ready draft paper opens its Opinion section with "NOT READY" and the open blockers; "Opinion" (not "Draft opinion") only when the file is ready and the judgments are recorded, on the paper and on the Draft Opinion tab. The engine's reason no longer says "representations obtained" when none were loaded ("no missing written representation recorded").
2. **Fixed.** Rows sharing a key are compared as whole rows (a change shows as removed + added), never collapsed; the screen explains it. The older test that expected one row for a duplicated key encoded this bug and was corrected (net 0.0, not -30.0).
3. **Fixed.** Fraud tab column is "Magnitude"; vendor twins show "similarity n" (both twin kinds score 0-1 similarity, checked in the engines).
4. **Default taken, James to confirm:** an engagement with any signed lock (current or superseded) cannot be deleted, only archived; the delete dialog says so.
5. **Fixed.** An errored latest run is not counted as run.
6. **Fixed.** An item done before who-did-it was recorded cannot be signed off until reopened and marked done again.
7. **Fixed.** Materiality rounds half up (as the preview does); NaN and Infinity are refused.
8. **Fixed.** Changing "latest run only" clears the selection, like the other filters.
9. **Left as a known limit.** Only rows archived by the uncommitted pre-migration-11 code are affected; James's database has none (checked read-only).
10. **Left as a known limit.** Same pattern as the existing lock check; single-user local server.

Also: `docs/OCEANVIEW*` is now git-ignored.

## Verification of fixes (independent reviewer, commit 4ccd6f6)

I did not edit source, commit or push. I reran my original scenarios against 4ccd6f6 with scratch databases (the old-code
v1-lock fixture and a scratch Kestrel load). The real DB was not touched in this round.

- **Tests:** `pytest -q` gave **504 passed**. `finish_line_check.py` gave **157 of 160; 0 unexplained**. It rewrote
  FINISH-LINE-REPORT.md, and `git diff` of that file is empty. `npx tsc --noEmit` on apps/workbench-ui: no errors.

| # | Result | How checked |
|---|---|---|
| 1 | **Fixed** | Same not-ready engagement: the paper now reads "Opinion — NOT READY … Still open: MATERIALITY_NOT_SET (1), RISK_ASSESSMENT_NOT_COMPLETE (1), NO_DATA_WITHOUT_PARTNER_ASSERTION (1), COMPLETION_PROCEDURES_INCOMPLETE (6). Draft opinion (not settled): unmodified". There is no `<b>Opinion:` and no "representations obtained". A ready, locked engagement's paper still says "Opinion: unmodified" with no NOT READY (reproduced). Opinion tab: `final = opinion && ready` (code read, compiles). |
| 2 | **Fixed** | Kestrel Bank_reconciliation and Cutoff_statement, +250,000 on the first duplicate-key row: now 1 removed + 1 added, net 250,000.00, `above_performance` (was: none / 0). Identical files: no changes, net 0. Deleted duplicate row: net −12,650.00 / −4,318.75. A unique-key row +5 is still a keyed "changed" row. Row counts are the true totals (14→14, 14→13). |
| 3 | **Fixed** | Code read: the column is "Magnitude"; vendor twins show "similarity n". The other fraud engines whose findings I printed on Kestrel score in dollars; the AP engines that did not run on Kestrel pass no score, so they show "—". |
| 4 | **Fixed** (the rule itself is still James's decision) | Delete of the v1-locked engagement is refused ("signed audit files are kept. Archive it instead"); lock_snapshot and lock_signature rows remain. A never-locked engagement still deletes. |
| 5 | **Fixed** | Code read (`status != "error"`). New test b5 passes; I did not run a separate reproduction. |
| 6 | **Fixed** | Old-code fixture: the legacy stage sign-off is now refused ("who marked 'controls' done is not recorded; reopen it…"). |
| 7 | **Fixed** | 250,000.10 × 5% saves 12,500.01. I compared the UI preview formula (node) with the server (Decimal HALF_UP) on 14,000 benchmark/percentage pairs: 0 mismatches. NaN, sNaN, Infinity and −Infinity are refused. |
| 8 | **Fixed** | Code read: toggling "latest run only" now clears the selection. |

### New or remaining issues from the fix (all low)

- **a. A date-only change on a shared-key row now looks significant.** Moving the Kestrel duplicate deposit's date by one day
  gives removed 12,650 + added 12,650, net 0.00, overall **above_trivial**. Before the fix this showed "none", which hid the
  change. Now the change shows, but it is labelled by the row's full amount even though no money moved. This errs on the safe
  side; the note under the table explains the removed+added rule. Reproduced.
- **b. Duplicate keys lost their warning styling.** Duplicate voucher numbers (Kestrel's MC-25009) used to show a red
  "Duplicate keys" error bar. They are now a plain grey note saying rows are compared whole. A duplicated key is an audit fact in
  its own right. The duplicate-bills procedure still catches it, so nothing is lost, but it is less prominent. Code read.
- **c. A signed paper with open partner decisions would read "NOT READY … Still open: see the readiness gate".** When readiness is
  green but partner decisions are open, `draft_opinion` returns `status=not_ready` with no blockers. A locked paper would then show
  NOT READY and point at a gate that is green; the open items are the partner's decisions, which the section lists further down.
  Wording only. Reasoned from opinion.py and workpaper.py; not reproduced.
- **d. A huge benchmark exponent crashes instead of being refused.** A benchmark of `1e999999` still raises an uncaught
  `decimal.InvalidOperation` at quantize (would be a 500). NaN and Infinity are handled. Reproduced; trivial.
- Findings 9 and 10 are left as known limits, as the response says. The real DB has no affected rows (checked read-only in round 1).

## After the verification (Claude)
- a. Kept: a date-only change on a shared-key row shows at its full amount; it errs toward showing, never hiding.
- b. Fixed: shared keys get the red warning bar again (a duplicated key is itself an audit fact).
- c. Fixed: with no readiness blockers, NOT READY points to the partner's decisions under "Still to decide".
- d. Fixed: a benchmark too large to compute is refused ("too large"), tested.

## Reversed later on 30 Sep (James)
Noesi is a supplement, not audit software. The sign-off (finding 6's fix), the required notes on stages and checks, and the refusal to delete a signed engagement (finding 4's default) were removed. Deleting a signed engagement works again, with the signature cleanup from the first review.
