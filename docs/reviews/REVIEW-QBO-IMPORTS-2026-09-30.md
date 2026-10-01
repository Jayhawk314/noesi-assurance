# Independent review: QuickBooks Online imports (uncommitted work, 30 Sep 2026)

Reviewer: Claude (a separate session from the builder), 30 Sep 2026.
Scope: the uncommitted working-tree changes listed in `git status` against HEAD
`2b70566`: QBO recipes in `packages/procedures-ap/src/procedures_ap/quickbooks.py`,
the trial-balance builder and coverage `_inventory` in
`packages/assurance-application/src/assurance_application/service.py`, the API
route, the UI panel, the Kestrel generators and regenerated xlsx files, the demo
seed, the tests and the docs.

I found and reported problems. I did not fix anything. The only file I wrote is
this report. Two throwaway copies of a script were made briefly in
`apps/learn-kestrel-ui/scripts/` (as `_tmp_review_export.py`, which wrote only to
my scratchpad) and deleted straight away. `git status` for that folder is clean.
All other experiments ran from the session scratchpad on temporary databases.

Severity: **High** means wrong audit results or a false claim of testing.
**Medium** means an overclaim or a silent data problem that can be reached in
normal use. **Low** means an edge case, a cosmetic issue or a documentation
inaccuracy.

No High findings.

---

## Findings

### M1 (Medium): coverage calls trial-balance procedures "executable" when the line mapping covers no account
`service.py:706-717` (`_inventory`). If the engagement has **any** `line_mapping`
entry and the trial balance has no `line` column, `"line"` is added to the trial
balance's fields. It does not check whether the mapping actually gives a line to
any account in this trial balance.

*Failure scenario:* A QuickBooks trial balance is loaded, and the only mapping is
one account override that is not in this trial balance (or a stale `label:` entry
left from an earlier file that had a line column). Coverage moves
`fs.trial_balance_analytics` from `partial` to `executable`. The seed and the
run gate (`service.py:767`) both trust that status. The run then sets aside all 9
rows as incomplete and refuses an empty population.

*Verified:* by script on the real fixture `kestrel_qbo/trial_balance.xlsx`, run
through `build_trial_balance`, propose, approve and normalize:
- no mapping: `partial`;
- after `line_mapping {"account": "99999", "line": "cash"}`: `executable`;
- the run: `population 0, refused_empty_roles ['Trial_balance'], excluded_incomplete_rows {'Trial_balance': 9}`.

The run itself stays honest, so this is not a false "tested". But it breaks
invariant 1 in `docs/INDEPENDENT-REVIEW.md` ("coverage never overclaims"). It
also contradicts the docstring ("this claims no more than runs") and the status
doc's line "Coverage now counts the line mapping". A partial mapping has a
related effect: coverage says executable, and the run gives ratios on a partial
trial balance plus a refusal for the unmapped rows. That partial-population
behaviour already existed (F2), but a QuickBooks trial balance, which has no line
column at all, now reaches it far more easily. Suggested direction (not applied):
apply the mapping to the records and count `line` as present only when the mapped
rows carry it, or show "N of M accounts mapped".

### M2 (Medium): with a QuickBooks trial balance, the line-mapping screen offers only a "map" button that always fails, plus manual per-account typing
`service.py:1687-1706` (`trial_balance_lines`), `apps/workbench-ui/src/screens/Scope.tsx:117-140`,
`service.py:1376-1393`. A QuickBooks trial balance has no `line`, so every account
lands under one label `""` with no suggestion. The screen shows "(blank)" with a
"map" button. That button sends `label: ""`, which is refused: "map either a label
or one account, not both". The only working path is the account-override form:
type each account number and choose its line, one at a time, with no suggestion
taken from the account name.

*Failure scenario:* an auditor loads a real 80-account QuickBooks trial balance
and follows the new panel's instruction ("map its accounts to statement lines
under 'Trial balance lines'"). The obvious button errors. They have to type 80
overrides.

*Verified:* by script: `trial_balance_lines` returned `[('', 9, None)]`, and
`update_workflow(... "line_mapping", {"label": "", ...})` raised that
ValueError. The Kestrel seed avoids this by reading the case's own
`auditor/tb_line_mapping.csv` (`workbench_seed.py:157-170`). So the demo works,
but nothing shows the real-user path working, on screen or in a test. The status
doc says the panel was "seen", not the line mapping.

### M3 (Medium): two Journal exports that overlap in dates, loaded with mode "add", merge into double-counted entries without any warning
`quickbooks.py:508-546` (`_derive_journal`) and `service.py:462-470` (add mode
checks only that the column maps match). Entry names are unique only within one
file. The `[txn N]` suffix is added only when a name collides inside the same
file. Add mode does not check for duplicate (entry, line) pairs or repeated
QuickBooks transaction IDs.

*Failure scenario:* the client sends a full-year Journal and later a "June-July"
Journal. Or the same report is re-exported (different bytes, so the SHA-256
duplicate check doesn't catch it) and added. The June transactions come out under
identical entry names, and the journal engine (`journal.py:38`, grouping by
`entry_id`) treats each pair as one entry with doubled lines. Each merged entry
still balances, so nothing flags it. Two distinct transactions with the same
name, one in each file, would also merge.

*Verified:* by script: `journal_created_by.xlsx` loaded, then a re-exported copy
(footer timestamp changed) loaded with `mode="add"`. Result: 62 rows, 11 entries,
up to 14 lines per entry, 31 duplicate (entry, line) pairs, and no refusal or
note. This gap existed before (the old `prep_journal` was also per-file), but
uploads are now raw, and the Transaction ID that would catch it is available and
not used. Not a problem for Kestrel's two files, which do not overlap
(FY ends 06-30, July file starts 07-01).

A related point (Low): the name of the same transaction depends on what else is
in its export. It gets `[txn N]` only when its file has a twin. So two exports
over different ranges can name it differently.

### L1 (Low): flat-list behaviour changed under the same `RECIPE_VERSION = "qbo-v1"`
`quickbooks.py:66`, `quickbooks.py:416-481`. The vendor contact list is the only
recipe that existed before and takes the flat path. It now goes through
`_apply_flat`. A row with values but a blank `Vendor` is now **refused**
(`RecipeError: a row with values but no Vendor`). Before, it was kept, and
`missing_required` reported it for quarantine. Blank rows and "Total for" rows
are also handled differently now. The version string, which exists to stop an
approved spec being re-read by changed logic (`service.py:2361-2365`), did not
change.

*Verified:* (a) I ran the HEAD `quickbooks.py` and the working-tree version on
every old-recipe file in the repo (7 fixtures in `tests/fixtures/quickbooks/`
plus Kestrel's Bill Payment List, Transaction List by Vendor ×4 recipes, Unpaid
Bills, Vendor Contact List). Headers, rows and source rows were **identical**. The
report gains only the key `rows_footed`. So no approved spec in the repo
changes. (b) A synthetic vendor list with a blank-name row: old code kept 2 rows
with 1 missing_required; new code refuses. An already-approved vendor spec over
such a file would now fail at normalize with no version mismatch to explain why.

### L2 (Low): `build_trial_balance` accepts a trial balance that is not at the period end, with only a note
`service.py:2557-2560`. *Scenario:* engagement period end 2025-12-31 with a
trial balance dated 2026-06-30. It builds, and the only signal is
`notes: ["this period's trial balance is as of '2026-06-30', not the engagement's period end 2025-12-31"]`.
That note appears once in the panel and in provenance JSON. Nothing in coverage
or the run carries it. *Verified:* by script. This may be a design choice, but
the procedures will then test balances at the wrong date.

### L3 (Low): spurious note in the prior-year check in a leap year
`service.py:2566`. For the expected prior date, a current date of 2025-02-28
gives 2024-02-28. A February year end in 2024 is 02-29, so a correct prior
export gets a "not one year before" note. The code was read, not run. It is only
a note.

### L4 (Low): `last_date` edge cases
`quickbooks.py:609-660`. Checked by calling it:
- QuickBooks forms reproduced correctly: "As of Jun 30, 2026", "April-June, 2026",
  "July 2025-June 2026", "August 2026", "July 1-24, 2026", "January 1-September
  23, 2026", "Mar 1-31, 2026", "As of Sept. 30, 2026".
- `"Jan 1, 2026 - Mar 2026"` gives **2026-01-01**. A day-dated match always wins
  over a later whole-month end. This is not a format QuickBooks was seen to
  print.
- `"June 31, 2026"` raises `ValueError` instead of returning None. In
  `trial_balance_candidates` that would error the whole candidates call for the
  engagement, not just skip one file. (The old code raised too.)
- Numeric dates ("As of 06/30/2026") give None, so they fail safe.

### L5 (Low): an all-blank flat row counts as a "nested heading", and a blank TOTAL cell counts as a disagreement
`quickbooks.py:444-447` and `_check` at `quickbooks.py:586-594`. If an
inventory item or customer row has every amount cell blank, the whole file is
refused as "sub-items or categories". If a TOTAL cell is blank, `_check` gets
stated `None` and reports the total as disagreeing. For a trial balance that
makes `build_trial_balance` refuse. *Verified:* the real exports write `0` in
TOTAL for empty buckets (aging TOTAL `['TOTAL','1460','1140','1400','0','0','4000']`),
so neither case appears in what was seen. I did not check whether QuickBooks ever
prints an item row with no quantity and no value.

### L6 (Low): account-number parsing is a guess about how QuickBooks shows numbered accounts
`quickbooks.py:484-490`, `_ACCOUNT_NUMBER`. The real company typed the number into
the account name. The README says this openly. Untested guesses: (a) an account
named with a leading year and no number ("2024 Vehicle Loan") is keyed "2024";
(b) if QuickBooks prints sub-accounts as "60000 Utilities:60100 Gas", parent and
child both key "60000", and the trial balance is refused as a duplicate account.
That failure would at least be loud. Neither was checked against a real export.

### L7 (Low): the Learn app's records are stale against the regenerated files
`apps/learn-kestrel-ui/src/learn/kestrel-records.json`. I re-ran
`scripts/export_records.py` with its output sent to the scratchpad. One key
differs, `je_1071`: the new Journal repeats the date, type, Num and name on the
second line. It is cosmetic, but the committed JSON no longer matches what its
generator produces. The "Memo/Description" lesson text is disclosed in the status
doc and still present (`lessons-fraud.ts`, `learn.html`).

### L8 (Low): documentation inaccuracies
- `service.py:711-712` docstring and the status doc say unmapped accounts are set
  aside "by name". The refusal (`engines.py:170-176`) names **sheet rows**
  (`source_row`), not account names.
- The status doc's line "every figure equal" is accurate for figures. It does not
  mention the two renamed entries (`[txn 445]`, `[txn 446]`), which only the
  builder's summary to the caller named. It also does not say that
  `Journal_2026-07.xlsx` lines now come in a different order (sorted by
  date/type/num/name instead of date only). Content is unchanged; see Claims.
- UI (`screens.tsx` TrialBalancePanel): if the user picks as "this period" the
  file that was preselected as prior, the prior state keeps that id even though
  the option disappears. Build then fails with "must be dated before", which
  doesn't explain the real cause. It is safe, just confusing. The code was read,
  not run.

### Checked and found fine
- **(a) Fitting to Kestrel:** I found no Kestrel constants in the package or API
  code (I grepped the added lines for Kestrel, 11900, 10100, First Prairie, Dana
  and 2026: only docstring examples). The recipes match the real exports' exact
  headings (`recognize` on each `kestrel_qbo/*.xlsx` claims exactly the intended
  recipe; the GL claims none, as designed). Case-specific mapping (account 11900
  on the allowance line, `tb_line_mapping.csv`) lives only in the case seed, as
  before.
- **(e) Blank amounts:** grouped payables recipes still refuse a blank amount
  (`blank_amounts=False`), and their outputs are unchanged (L1). The Journal
  recipes treat a blank debit or credit as 0. Flat recipes always treat a blank
  amount as 0. Non-numbers are refused in both.
- **Journal ID reuse inside one file:** if two groups share a Transaction ID with
  different date/type/num/name, the file is refused (`quickbooks.py:518-520`), not
  merged. In the real export, IDs ran as one sequence across types (2..12), but 11
  transactions is a small sample.
- Same TB built twice: succeeds (no crash). Prior equal to current: refused.

---

## Claims checked

| Builder's claim | Result | How |
|---|---|---|
| pytest: 518 pass | **Confirmed** | `.venv/Scripts/python.exe -m pytest -q`: `518 passed in 44.65s` |
| finish_line_check: 162 of 164, 0 unexplained | **Confirmed** | ran `instructor/finish_line_check.py`: "162 of 164 match; 0 unexplained". The 2 open lines are the PO overrun and the unrecorded liability (roadmap C). It rewrote FINISH-LINE-REPORT.md |
| check_key.py 16/16 | **Confirmed** | ran it: "16/16 checks agree" |
| Regenerated data carry the same figures; only two same-day deposits renamed | **Confirmed, with one addition** | scratchpad `compare.py`/`compare2.py`: the HEAD copy of the case (`git archive HEAD`) run through the HEAD `run_noesi.prep_trial_balance/prep_aging/prep_inventory` and HEAD `workbench_seed.prep_journal`, against the new recipes on working-tree files. TB 32 accounts, balance, prior balance and description all equal. Aging 20 customers, all 5 buckets and the total equal (20 rows footed). Inventory 20 SKUs, description, qty, cost and unit cost (4 dp) equal. Journal.xlsx 1006 lines / 461 entries and Journal_2026-07.xlsx 14 lines / 7 entries: multisets of (entry, line, date, type, account, debit, credit, posted date, posted by, description) are equal once `2026-06-30 Deposit (no num)` becomes `[txn 445]` and `... [2]` becomes `[txn 446]`. Grand totals foot (20,393,152.56; 164,800.05). Addition: Journal_2026-07 line **order** changed (content equal). The renamed names do not appear in any answer key. The key's `2026-06-30 Deposit (no num) Checking` is a different entry that carries a name |
| No answer-key json and no CSV under case-studies changed | **Confirmed** | `git diff --stat -- '*.json' 'case-studies/**/*.csv'` is empty. `git status case-studies` shows only README, 6 xlsx, generate.py, generate_part3.py, payables_outputs.py and workbench_seed.py |
| Oceanview pass 2: `git -C oceanview diff --stat` empty | **Confirmed** | `run_full.py 2` exited 0. `diff --stat` was empty. Untracked files were the same before and after (2 pre-existing html files) |
| Status doc: "11 tests on the real files", "507 + 11" | **Confirmed** | 11 `test_` functions in `tests/unit/test_quickbooks_reports.py`. The Kestrel demo test was replaced one for one |
| Status doc: seed refused list empty | **Confirmed** (by test) | `test_kestrel_demo.py:42` asserts `refused == []`, and it passes. finish_line_check line "every file loads" passes |
| Status doc: coverage counts the line mapping, so it "claims no more than runs" | **Contradicted** | see M1 |
| Status doc: unmapped accounts set aside "by name" | **Contradicted (minor)** | see L8. They are set aside by sheet row |
| Reconciliation report has no Excel export (PDF only) | **Not checked** | I cannot see the QuickBooks UI. `reconciliation_report_screen.txt` is correctly described as on-screen text, not an export |
| Fixtures are real QuickBooks exports | **Not independently provable** | the files have QuickBooks' layout (company "xx", formulas with cached values, "GMT-07:00" footer, `Total for <ID>`), which is consistent with the claim. I can't prove where they came from |
