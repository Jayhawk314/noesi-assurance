# Independent review — fraud readiness changes (2026-09-29)

## Scope

I reviewed the five local commits `7879214..d962b0a` without changing the
implementation:

- `38db3ff` — prior review fixes and blank-voucher treatment in the
  unrecorded-liabilities search;
- `7b3055b` — README/manual conversion to the Kestrel teaching case;
- `4458c52` — in-period counting for seldom-used journal accounts;
- `2a97f54` — supplier invoice numbers for duplicate-bill testing; and
- `d962b0a` — the `je_manual_sources` policy.

I read the handoff and independent-review brief, inspected the commit diffs and
the affected implementation/tests, searched the permitted repository for
remaining `voucher_number`/`invoice_number` assumptions, ran focused invented
data reproductions, and ran the tests listed under Confirmations. I did not
stage, fix, commit, or push anything. I did not read or include material from
the prohibited case/material paths named in the review request.

## Findings

### High — an all-blank description column disables the very test meant to find blank descriptions

**Claim contradicted.** The journal contract says `no_description` selects
journal entries with that fraud-risk characteristic, and the new policy says
the selection is limited to manual entries. Instead, the implementation uses
“any nonblank value exists” as its test for whether the description *column*
exists. If the mapped column is present but blank on every entry, the engine
says the column is absent, marks the test not performed, and selects nothing.

**Location.** `packages/procedures-cycles/src/procedures_cycles/journal.py:57`
defines `has` in terms of nonblank values; lines 86–87 then use it as a column-
presence test. The manual-source branch at lines 174–182 is never reached.

**Reproduction.** I ran:

```powershell
.\.venv\Scripts\python.exe -c "from decimal import Decimal as D; from procedures_cycles.engines import execute_procedure; rows=[{'entry_id':'E1','entry_date':'2025-06-01','account':'1000','amount':D('1'),'description':'','source':'Journal Entry'},{'entry_id':'E1','entry_date':'2025-06-01','account':'2000','amount':D('-1'),'description':'','source':'Journal Entry'}]; f,s=execute_procedure('je.journal_entry_testing',{'Journal_entries':rows},{'period_end':'2025-12-31','je_manual_sources':'Journal Entry'}); print('no_description_findings=',[x.key for x in f if x.key[-1]=='no_description']); print('not_performed=',s['not_performed'])"
```

Relevant output:

```text
no_description_findings= []
not_performed= {..., 'no_description': 'the listing has no description column'}
```

**Concrete failure scenario and audit impact.** A complete journal export has a
mapped Memo/Description column, but all manual journal entries omit memos. This
is the maximum possible population of the risk characteristic, yet the run
produces zero no-description leads and tells the auditor the field was not
supplied. An auditor relying on the run can omit inspection of every
undescribed manual entry based on a false data-availability statement.

### Medium — the common `Invoice Number` heading is still assigned to the internal voucher key, making duplicate-bill testing unavailable

**Claim contradicted.** Commit `2a97f54` correctly changes
`ap.duplicate_bills` to require the supplier's `invoice_number`, not the
client's internal `voucher_number`. The ordinary header detector nevertheless
gives a lone `Invoice Number` column to `voucher_number` first and forbids
header reuse, so the supplier field is absent. The procedure then reports that
it needs data even though the file contains the supplier invoice number under
its most ordinary heading.

**Location.** `packages/procedures-ap/src/procedures_ap/ingest.py:57-65`
lists `invoice number` under both fields but declares `voucher_number` first;
`detect_columns` at lines 235–249 resolves by declaration order with no reuse.
The duplicate-bill contract requires `invoice_number` at
`packages/procedures-cycles/src/procedures_cycles/contracts.py:186-197`.

**Reproduction.** I ran:

```powershell
.\.venv\Scripts\python.exe -c "from procedures_ap.ingest import detect_columns,ROLE_SCHEMAS; print(detect_columns(['Invoice Number','Vendor Number','Voucher Amount'],ROLE_SCHEMAS['Vouchers']))"
```

Output:

```text
{'voucher_number': 'Invoice Number', 'vendor_number': 'Vendor Number', 'voucher_amount': 'Voucher Amount'}
```

There is no `invoice_number` in the proposed mapping. The existing unit test
only covers a file that has both `Voucher Number` and `Invoice Number`, so it
does not exercise this common single-number layout.

**Concrete failure scenario and audit impact.** A vendor-bill export headed
`Invoice Number, Vendor Number, Voucher Amount` contains two entries of the
same supplier invoice. If the reviewed proposal is accepted as presented,
the data lands under the internal key and `ap.duplicate_bills` is blocked for
missing `invoice_number`; the duplicated bill is never compared. This fails
closed rather than issuing a false pass, but it removes a core fraud procedure
from an otherwise sufficient generic export and can be mistaken for a client
data deficiency. The explicit QuickBooks recipes do map `Num` to both fields,
so this failure is in ordinary header mapping, not those recipes.

### Medium — manual-source filtering does not leave a reperformance trail for exclusions and overstates unknown/mixed entries as manual

**Claim contradicted.** The run should let the auditor see which entries were
tested and what was left out. The new branch records only an aggregate
`no_description_not_manual` count for excluded entries. It records neither
their entry IDs/source rows nor their observed source values. In addition, an
entry whose source is blank, or whose lines mix a configured manual source
with a nonmanual source, is selected with the categorical reason “of a manual
entry.” Blank is unknown, not manual; mixed source data is at least an
inconsistency that the receipt does not disclose.

**Location.** `packages/procedures-cycles/src/procedures_cycles/journal.py:174-182`
uses “any source intersects the policy” and treats an empty source set as the
manual branch. Lines 193–194 expose only the policy and aggregate exclusion
count.

**Reproduction.** With one described entry (to establish that the description
column exists), I supplied an undescribed blank-source entry, an undescribed
entry with one `Journal Entry` line and one `Invoice` line, and an undescribed
`Invoice` entry. I ran:

```powershell
.\.venv\Scripts\python.exe -c "from decimal import Decimal as D; from procedures_cycles.engines import execute_procedure; L=lambda e,a,v,s,d='': {'entry_id':e,'entry_date':'2025-06-01','account':a,'amount':D(v),'description':d,'source':s}; rows=[L('DESCRIBED','1000','1','Invoice','memo'),L('DESCRIBED','2000','-1','Invoice','memo'),L('BLANK','1000','1',''),L('BLANK','2000','-1',''),L('MIXED','1000','1','Journal Entry'),L('MIXED','2000','-1','Invoice'),L('AUTO','1000','1','Invoice'),L('AUTO','2000','-1','Invoice')]; f,s=execute_procedure('je.journal_entry_testing',{'Journal_entries':rows},{'period_end':'2025-12-31','period_start':'2025-01-01','je_manual_sources':'Journal Entry'}); print('findings=',[(x.key,x.reason) for x in f if x.key[-1]=='no_description']); print('stats=',{k:s[k] for k in ('manual_sources','no_description_not_manual')})"
```

Output:

```text
findings= [(('je.journal_entry_testing', 'blank', 'no_description'),
  'entry blank: no description on any line of a manual entry'),
 (('je.journal_entry_testing', 'mixed', 'no_description'),
  'entry mixed: no description on any line of a manual entry')]
stats= {'manual_sources': ['journal entry'], 'no_description_not_manual': 1}
```

The output does not identify that the one omitted entry is `AUTO`, does not
show its source rows, and does not disclose that `MIXED` has contradictory
source values.

**Concrete failure scenario and audit impact.** A mapping error labels 176
undescribed entries `Invoice`, or a policy typo names a source value that does
not exactly match the export. The run reports only that 176 were “not manual.”
The auditor cannot extract the excluded population from the receipt to verify
the classification, sample exclusions, or notice that the policy matched no
observed manual source. Conversely, a blank-source automated entry is described
as manual in the evidence record. The selection is conservative for blank and
mixed sources, but its stated basis is not supported and its exclusions are
not independently reperformable from the run output.

## Confirmations

- I ran `.\.venv\Scripts\python.exe -m pytest -q` from the repository root:
  **439 passed in 31.51s**.
- I separately ran the affected demo, duplicate-bill, journal-entry, and cycle
  engine modules:
  `.\.venv\Scripts\python.exe -m pytest -q tests\unit\test_kestrel_demo.py tests\unit\test_duplicate_bills.py tests\unit\test_journal_entries.py tests\unit\test_cycles_engines.py`:
  **36 passed in 6.67s**. This includes the Kestrel demo's draft-opinion check.
- I reviewed the unreviewed blank-voucher change in `38db3ff` as strictly as
  the others. Its role-qualified optionality leaves blank voucher references
  in the subsequent-payment selection while continuing to require voucher
  numbers on the year-end Vouchers role. The focused test confirms that a
  blank-reference payment remains in the population, is selected, and can be
  reported as unrecorded. I found no defect in that change.
- I tested `4458c52` with one in-period entry, one pre-period entry, and an
  entry whose date was blank. The in-period entry remained seldom-used; the
  pre-period entry was counted under `dated_before_period_start`; and the two
  blank-date lines produced an explicit `incomplete_rows` refusal and were not
  allowed to affect account frequency. The relevant output was:

  ```text
  seldom_ids= ['in']
  stats= {'population': 1, 'dated_before_period_start': 1, 'dated_after_period_end': 0}
  incomplete= [(..., '2 Journal_entries row(s) have no value for entry_date; they were not tested. Supply the values or record why the gap is accepted')]
  ```

- I inspected remaining permitted uses of `voucher_number`. Payment-to-voucher
  joins, payment duplicate checks, document-chain tests, and voucher/PO checks
  use it as the client's internal reference and should continue to do so. I
  found no other executor in scope that still uses `voucher_number` as the
  supplier invoice number. The generic ingestion ambiguity reported above is
  the remaining scoped assumption.
- I inspected the other `38db3ff` changes (aging bucket shape, duplicate
  descriptions in likely-basis evidence, and Kestrel journal ID
  disambiguation) and the associated invented-data tests. I did not find a
  further concrete failure in them.

## Not checked

- I did not open a browser or manually inspect UI rendering of coverage, run
  stats, or print output. My statement about the run output is based on the
  procedure's returned findings/stats, which are the persisted executor result.
- I did not run the JavaScript build, live HTTP/API security tests, packet
  export/offline verification, lock tampering, or production-readiness attacks;
  they are outside this five-commit review.
- I did not independently recompute the full teaching-case answer key from the
  source workbooks. I confirmed the checked-in headless demo tests, including
  its expected draft opinion, rather than treating that as an independent
  audit of every case number.
- I did not test against exports from accounting products beyond the checked-in
  fixtures and the invented generic-header reproduction above.
- I did not inspect unrelated untracked files or any expressly prohibited
  case/material content.

## Overall verdict

The five commits preserve the full 439-test baseline, and the blank-voucher
liability-search change and in-period seldom-used-account change behaved
correctly under adversarial invented inputs. The branch remains suitable as a
pilot/teaching system whose refusals and receipts are independently reviewed;
it is not yet safe to rely on as the sole fraud-risk selection record. In
particular, an all-blank description population currently creates a false
negative, ordinary `Invoice Number` exports can lose duplicate-bill coverage,
and manual-source exclusions cannot be reperformed from the run result. Those
conditions must be resolved before the affected procedures support a clean
audit conclusion.
