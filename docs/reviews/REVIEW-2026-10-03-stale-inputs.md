# Review of the uncommitted stale-result work, 3 Oct 2026 (Claude)

This review covers the uncommitted changes left by the previous session: stale
results after changed inputs or a failed rerun, the older-packet working-paper
fix, and the final wording edits. Nothing is committed or pushed.

## Reproduced bug: every result marked stale after any unrelated change

Each run recorded the IDs of **every** loaded dataset and **every** engagement
setting, and staleness compared all of them. With invented data (a journal and
a Benford run), these changes each marked the Benford result stale:

- an unrelated PP&E setting: "settings changed";
- an unrelated fixed-asset file: "loaded data changed".

Benford reads neither. On Kestrel, replacing the confirmations file would have
marked all 37 results "historical; rerun required" and listed every procedure
under `PROCEDURE_RESULTS_STALE`. A freshly seeded demo showed 0 of 37 stale,
because everything loads before the runs, so the problem appears only after
later changes.

**Fix (uncommitted):**
- `procedures_ap/readlog.py` logs the tables each engine looks up. The log sits
  in the three record helpers, so it survives table copies and also records
  roles that were absent. Settings are logged through the mapping the engine
  receives; any whole-mapping access marks every setting read.
- Each run stores `inputs_read` in its manifest, and staleness compares only
  those inputs.
- Runs recorded before this change have no `inputs_read` and keep the
  cautious compare-everything behaviour.

Contracts were not used to narrow the comparison. They under-declare: Benford
declares only the journal but also reads bills and payments, and optional
settings are not declared at all. Narrowing by contract would hide real
changes.

**Checked:**
- `tests/unit/test_stale_inputs_read.py` (4 tests):
  - an unrelated setting or file leaves the result current;
  - its own setting, a payments file arriving where none was loaded before,
    and a replaced journal each make it stale;
  - a rerun clears the flag;
  - an older run stays cautious.
- Full suite: 584 passed.
- Kestrel calibration: 174/176, 0 unexplained, unchanged. Logging does not
  alter engine results.

## Rest of the uncommitted diff

- **Older-packet working paper:** reads correctly. Old title-prefixed items are
  assigned only when a risk title is unique, and ambiguous ones are listed
  separately.
- **Failed-rerun handling** (runs / overlay / fraud view): reads correctly.
- **UI wording:** reads correctly. One harmless leftover: the screens map
  `SELECTED_PROCEDURES_STALE`, a readiness code the server never emits.

## Clicked replacement journey: not completed

On a fresh invented store, Invented Trading Co, the setup was done through the
service:

- loaded a 4-entry journal, a vendor list and an employee list;
- ran Benford and the vendor/employee match, both completed and current.

A revised journal (adds J5, 840.00) is ready in the scratch folder. In
Chrome, the engagement could not be opened:

- two clicks on the "open" button's element reference did nothing;
- a third click by screen position hit "archive" instead, because the button
  positions differ from the Kestrel store.

The browser work stopped there, as instructed. That click only opened the
archive form. It was cancelled, and SQLite confirms the engagement is still
open with no archive event.

**Still untested by clicks:**
- uploading and confirming the revised file;
- the "replaces it" click;
- Runs & Findings and What Changed after replacement, compared with SQLite;
- the rerun;
- downloading the record and verifying it offline.

## Review status

No second agent has reviewed the read-logging fix or this note.

## Second-agent review of 1b6d7b1, and what was done (3 Oct, later)

A separate Claude reviewed the commit (report only). It found no case of a
result staying "current" after an input it read changed. Of what it reproduced:

- **Fixed:** a line-mapping edit marked 31-33 unrelated Kestrel results
  stale. The engine relabels the trial balance for every procedure, and the
  relabelling counted as a read. Now it does not; the line mapping counts as
  read only for runs that read the trial balance or prior statements. On
  Kestrel the same edit now marks 12, all of which read the trial balance.
- **Fixed:** a left-out procedure (with a reason) whose result went stale was
  a readiness blocker that could never be cleared. It no longer blocks; its
  findings still need dispositions. The four procedures the draft opinion
  reads even when left out (uncorrected misstatements, going-concern
  indicators, representation letter, covenants) still block.
- **Not fixed, by decision:** runs recorded before 28 Sep 2026 have no
  dataset record, so a replaced file does not flag them. New stores have
  none.
- **Not fixed, harmless:** a run made with a one-off setting override is
  flagged when the engagement's own value of that setting later changes.
