# Review of uncommitted changes — 2026-09-30

## Findings

### 1. Critical — archived engagements remain writable

`packages/assurance-application/src/assurance_application/service.py:148`

`_require_unlocked()` rejects only `status == "locked"`; it accepts `"archived"`. Most mutation paths use this common gate, so an archived engagement can still receive team assignments, workflow edits, sources, mappings, runs, dispositions, and risk changes through direct API calls even though it is hidden from the active list. Concrete reproduction: create and archive an engagement, then call `assign_team()`; it succeeds and the new preparer appears in `team()`. Archived engagements are therefore not locked/immutable.

### 2. High — archive/restore invalidates a valid signed lock without superseding it

`packages/assurance-application/src/assurance_application/service.py:175`, `packages/assurance-application/src/assurance_application/service.py:260`

Archiving a locked engagement calls `set_status()`, which increments the signed engagement version; restoring it increments the version again and returns status `locked`, while leaving the original lock snapshot active. Concrete reproduction with a genuinely signed, initially verified lock: `archive_engagement()` then `restore_engagement()` returns the engagement to `locked`, but `verify_lock()` changes from `verified=True` to `verified=False` with `drift == ["engagement"]`. This bypasses the documented unlock/supersede/re-lock trail and leaves a record that looks locked in the list but cannot verify or export.

### 3. High — large cycle-record revisions are displayed as zero and insignificant

`packages/assurance-application/src/assurance_application/impact.py:30`, `packages/assurance-application/src/assurance_application/impact.py:107`, `packages/assurance-application/src/assurance_application/impact.py:195`

The new cycle keys make cycle rows match, but `_record_amount()` still recognizes only the original AP amount fields plus generic `amount`. It does not recognize `balance`, `identified`, `likely`, `gross`, `net`, `cost`, `ending_balance`, and the other monetary fields used by the newly keyed record types. Concrete reproduction: change Trial Balance account 1000 from `balance=1000000` to `balance=2000000`; `diff_records()` lists the changed field but reports `amount_change: 0.0`, `net_amount_change: 0.0`, and `significance: "none"`. This is exactly a wrong number made to look harmless.

### 4. High — the new fraud-risk judgment is outside the signed lock manifest

`packages/assurance-application/src/assurance_application/service.py:1938`

The lock manifest's risk query does not select the new `fraud` column. A fraud designation is an auditor judgment shown on the Fraud and Risk screens, but the signed snapshot does not bind it. Changing/corrupting only `risk_assessment.fraud` after locking (without changing `version`) leaves the recomputed manifest and lock verification unchanged, so the application can display a different fraud-risk population while still reporting the signed lock as verified.

### 5. High — deleting a signed engagement always aborts and deletes nothing

`packages/assurance-application/src/assurance_application/service.py:221`, `packages/assurance-persistence/src/assurance_persistence/database.py:253`

Deletion discovers only tables that directly contain `engagement_id`. `lock_signature` has only `snapshot_id`, so it is never selected; its foreign key prevents deletion of `lock_snapshot`. Concrete reproduction: create and sign a ready engagement, then call `delete_engagement()` with the correct name and reason. It raises `RuntimeError: could not delete rows in ['lock_snapshot']`, rolls back, and the engagement remains. The new test covers only an unlocked engagement and therefore misses the indirect child table.

### 6. Medium — the Fraud tab double-counts stale and repeated findings

`packages/assurance-application/src/assurance_application/service.py:1169`, `packages/assurance-application/src/assurance_application/service.py:1170`

The code correctly identifies the latest run per procedure for `last_run`, but builds `findings` from `self.findings()`, which returns findings from every historical run. Concrete reproduction: two runs of `ap.duplicate_bills` containing the same current exception produce `last_run == r2` but `findings == 2`, `open == 2`, and summary findings `== 2`. A finding resolved by the latest rerun also remains on the Fraud tab from the older run. The existing service already shows the correct current-run filtering pattern at `service.py:1701-1704`.

### 7. Medium — several new row keys contain the values being revised

`packages/assurance-application/src/assurance_application/impact.py:52`, `packages/assurance-application/src/assurance_application/impact.py:54`, `packages/assurance-application/src/assurance_application/impact.py:55`

`Inventory_count` includes `stock_number` alongside the stable tag, while bank reconciliation and cutoff keys include mutable dates and amounts and omit the bank `account`. Correcting any keyed value makes the same business row appear as one removal plus one addition instead of one changed row; identical references across two accounts can also collide. For example, correcting a cutoff item's cleared date changes its identity rather than reporting `cleared_date` as the changed field. This weakens row matching and can distort the presentation and significance aggregation.

### 8. Medium — omitting `fraud` on an existing-risk update silently clears it

`apps/workbench-api/workbench_api/server.py:550`, `packages/assurance-application/src/assurance_application/service.py:1031`

The endpoint defaults a missing field to `False`, and the repository always writes that value. An older client or direct caller that updates the title, level, rationale, or response of an existing fraud risk without sending the newly introduced field silently removes its fraud designation. Also, `bool("false")` is `True`, so a JSON string value is accepted with the opposite likely meaning rather than rejected as a non-boolean.

## Verification performed

- `python -m pytest -q`: **474 passed in 36.51s**.
- `.venv/Scripts/python.exe case-studies/kestrel-valley-cycle/instructor/finish_line_check.py`: the sandboxed attempt could not create its temporary SQLite file; the identical command was then run with filesystem permission and completed **152 of 155 match; 0 unexplained**. The three explained gaps are the expected roadmap C items.
- Migration 10 was tested only on disposable copies of `C:\Users\JAMES\.noesi-assurance\control.db`; the real database was not opened for writing. On a copy with migration 10 rolled back, the project migrator applied `[10]`, preserved every non-migration table count, returned `integrity_check = ok`, returned no foreign-key violations, created `fraud NOT NULL DEFAULT 0`, and returned `[]` on a second idempotency run.
- The new archive/delete/restore service methods enforce the partner role inside their transactions, and tenant lookup precedes those mutations. I found no separate principal-bypass issue in the new mutation endpoints.

