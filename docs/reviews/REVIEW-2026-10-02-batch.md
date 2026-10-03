# Review, 2 Oct 2026: the batch after the fixes check

Reviewer: Claude (Opus 5.5), a fresh session that did not build this work.
Brief: `docs/reviews/BRIEF-2026-10-02-batch.md`. **Report only:** nothing was
fixed, committed or pushed. The only file written in the repo is this one.
The probe scripts and the old-schema database were in the session's scratch
folder, outside the repo. Oceanview was not read.

Classification used for each finding: **possible software bug**, **as
expected** (works as designed and stated), **text** (a doc or key says
something the files or code do not), or **not covered** (no test or key line
reaches it). Nothing below is a planted case error.

## 1. Reruns (all confirmed this session)

| Command | Claimed | Seen |
|---|---|---|
| `python -m pytest tests -q` | 536 pass | `536 passed in 49.46s` |
| `finish_line_check.py` | 172/174, 0 unexplained | `172 of 174 match; 0 unexplained` (the 2 are the known "not in Noesi" lines: PO overrun, unrecorded liability) |
| `check_key.py` | 24/24 | `24/24 checks agree` |
| `check-lessons.mjs` | 48 fraud answers, all tied | `13 modules, 101 answers, all tied to the key; ... 9 fraud lessons, 48 answers` |
| `npx tsc --noEmit` (workbench-ui, studio-ui, learn-kestrel-ui) | pass | no errors printed by any of the three |
| `npm run build` (same three) | pass | exit 0 for all three (`dist/` is git-ignored; tracked files unchanged afterwards, checked with `git status`) |

Note for the next runner: on Windows, PYTHONPATH for the two instructor
scripts must be `;`-separated. With `:` the finish-line script fails with
`ModuleNotFoundError: No module named 'assurance_application'`.

## 2. Findings, most severe first

### M1. One engagement can confirm and load another engagement's mapping or file. **Possible software bug** (Medium-High)

None of these three calls checks that the spec or artifact belongs to the
engagement in the URL:
- `confirm_pending_mapping` (new in 4bfed89). `MappingRepository.confirm_pending`
  updates by `spec_id` and `tenant_id` only (`spine.py:461-467`).
- `confirm_source_mapping`, which takes any `artifact_id`.
- `normalize_source` (`_rebuild_table` reads the spec by `spec_id` only).

`_require_open` is checked only on the URL's engagement, so the other
engagement can even be archived.

How confirmed:
1. I built a database with the code before D9 stage 3 (`git archive 0b1a16a`).
   It holds engagements A and B, each with a mapping proposed but never
   approved (chairs: alice partner, bob preparer, carol reviewer). Then I
   archived B.
2. I opened that database with the current server as user `dave`.
3. `POST /api/engagements/{A}/mappings/{B's spec}/confirm` returned
   `200 {"status": "approved"}`.
4. `POST /api/engagements/{A}/mappings/{B's spec}/normalize` returned
   `200 {"load_mode": "first", ...}`. The journal records `dataset.normalized`
   under engagement A for B's file.
5. A's own file was then refused: `Payments already has data in use
   (payments.csv)`. That data in use was B's file.

On a fresh database, through the service:
`confirm_source_mapping("u", A, role="Payments", artifact_id=<B's artifact>)`
and then `normalize_source` printed `A loaded B's file: b_payments.csv 6000.00`.

Impact: the engagement record and every procedure in A can rest on another
client's data. The UI does not send these IDs across engagements, but the
API accepts them. Partly older than this batch: the old `approve`, `normalize`
and artifact paths had the same gap behind their role checks. The new
`confirm_pending` repeats it. Not covered by any test.

### M2. A voided check that is in the Journal shows as a gap, and as a run of its own. **Possible software bug** (Medium)

A check whose lines carry no amount (as I understand QuickBooks prints a
voided check: zero debit and credit; **not checked against a real export**)
has no credited account. `_journal_checks` then gives it bank account `""`.
That puts it in a separate run, "account (none named)". This has two effects:
- The real run reports its number as missing: "1002 not in the records".
  That is false, because the check is in the records, as a void.
- With two runs, every run is renamed `disbursements, account 10100`.

The QuickBooks recipe keeps zero lines (`blank_amounts` is zero), so this
would reach a real load.

How confirmed: Journal checks 1001 (50), 1002 (0, 0), 1003 (70), all on 10100.
The result was a finding `('disbursements, account 10100', '1002', 'gap')`
and sequences `{'disbursements, account (none named)': {first 1002 ...},
'disbursements, account 10100': {missing_numbers 1, gaps 1}}`. With two
accounts plus a voided 5002, the same split happens and 10200 reports 5002
missing.

Kestrel has no voided checks, so the key and the finish line do not reach
this. Not covered. The manual says "a gap is voided, issued outside the
records, or hidden". Here the void is inside the records and is still called
missing.

### M3. Coverage says "executable" for a Journal with no checks, and the run then reports a clean result on zero checks. **Possible software bug** (Medium; invariant 1)

L5 makes the Journal an alternative input set for
`forensic.check_number_sequence`. Coverage only needs `Journal_entries` to
have rows. If the Journal numbers no checks and no payment records are
loaded, the run does not refuse.

How confirmed: an inventory of `Journal_entries` with 1 row (a Journal Entry,
no check) and no Payments. Coverage returned `{'status': 'executable',
'population': 1, 'satisfied_by': ['Journal_entries']}`. `execute_procedure`
returned 0 findings, with stats `{'population': 0, 'exceptions': 0,
'disbursements_from': 'payment records', 'sequences': {}}`.

So the run says its checks came from "payment records" when none were loaded,
and it reports no exceptions over nothing tested. This is the "never claim
more than it can show" case the brief asks about. Coverage said executable,
and the run neither refused nor said "not tested".

### L1. With both Payments and a Journal that numbers checks, the run reports on a file it does not read. **Possible software bug** (Low)

The required set (Payments) is "active" whenever Payments has rows, so a
Payments row with a blank `payment_number` is set aside with an
`incomplete_rows` finding. But the test itself reads the Journal. Coverage's
population is the Payments count, not the checks tested.

How confirmed: 2 Payments rows (one blank number) and Journal checks 1001,
1002 and 1004. Findings were `[('incomplete_rows', 'Payments'),
('disbursements', '1003', 'gap')]`, with stats `disbursements_from: Journal,
population: 3`. Coverage population was 2.

### L2. Declining balance: a disposal with accumulated depreciation cleared gives a false difference. **Possible software bug, limit not stated** (Low-Medium)

`_declining_balance` takes the opening book value as cost less (ending
accumulated less this period's expense). Many registers clear accumulated
depreciation when an asset is sold. The opening value then comes out above
cost.

How confirmed: cost 10,000, salvage 1,000, 5-year DDB, acquired 2024-01-01,
sold 2026-06-30, full month, recorded expense 600. By hand: opening book
value 3,600 × 40% × 5/12 = 600.
- With accumulated depreciation kept at 7,000: no finding (correct).
- With it cleared to 0: finding `depreciation_differs`, recomputed 1,766.67
  against recorded 600.
- With it blank: listed as not recomputed (correct).

The contract's limit ("the opening book value the register implies") does
not warn about disposals.

Answer to the brief's question 5: "opening value = ending accumulated less
this period's expense" is sound when the register's rollforward holds. The
recorded expense cancels out, so the base is independent of it. It is
unsound for disposed assets whose accumulated depreciation was cleared, and
for registers that do not update accumulated depreciation. Only the second
is implied by the stated limit.

The hand-worked cases all matched:
- 2-year-old asset: 1,440.
- Bought 15 Apr: 4,500 full month, 3,000 half year.
- At salvage: 0.
- Capped at salvage: 200.
- Beyond its life: no error.

Factors 0, `abc` and `-2` are listed as not recomputed (correct).

### L3. The declining-balance factor accepts "200%" as 200. **Possible software bug** (Low)

`dec()` strips `%`, so an auditor who types `200%` for double declining gets
a factor of 200. The result is a finding (recomputed 10,000.00 against
recorded 4,000) instead of a refusal. There is no range check: factors of 1
to 3 are plausible.

How confirmed: a plain "declining balance" asset with policy
`ppe_declining_balance_factor = "200%"` returned
`('a5', 'depreciation_differs', '10000.00', '4000')`.

Also: `"150% DB"` (a common spelling) is not in `_DECLINING` and is listed as
not recomputed. That is honest, but worth adding to the list.

### L4. Self-approved payments: a blank preparer passes silently, and the population is log rows, not payments. **Not covered** (Low)

- A row with an approver but no preparer is neither flagged nor counted. The
  stats have `no_approver` but no `no_preparer`.
- A dual-signature check logged as two rows (preparer plus a second signer)
  is flagged `self_approved` on the preparer's row, although it was
  co-signed.
- `population` counts rows. In my log, 5 rows covered 4 payments.
- "D. Merritt" and "Dana Merritt" do not match. That is stated ("as
  written").

How confirmed: a log of 5 rows gave stats `{'population': 5,
'self_approved': 1, 'no_approver': 0}`. The blank-preparer row and the
"D. Merritt" row produced nothing.

### L5. Vendor and employee match: one-word employee names are skipped silently. **Not covered** (Low)

The name test needs 2 or more words. An employee named only "Pike" is not
compared, and `employees_without_a_name` counts only empty names, so the skip
is not reported. A masked number on one side is counted
(`masked_numbers_not_compared: 1`), as L2 intended.

How confirmed: stats `employees_without_a_name: 0` with the employee "Pike"
untested.

### L6. Text: the first check number and the signature-log selection. **Text** (Low)

- `case-studies/kestrel-valley-cycle/README.md:246` and `docs/ROADMAP.md`
  (D10) say the checks run **4267**–4433. The key
  (`answer_key_part3.json`: `"first": 4266`), the Journal (first check 4266,
  counted by script) and `auditor/check_signatures.csv` (first row 4266) say
  **4266**. The brief says 4266. `check_key.py` checks the count and the gap
  but not `first`, so nothing caught it.
- The key's signature-log `selection` reads "every check of 2,500.00 or
  more...". The log holds the year to 30 June 2026 only. July's 4427 (7,500),
  4429 (25,000) and 4433 (6,100) are not in it. Confirmed by comparing the
  log's 96 checks with the 165 checks in both Journals. The lesson line "the
  team read the signer off the bank's images for the larger checks"
  (`lessons-fraud.ts:402`) carries the same gap. The wording should say "in
  the year".

### L7. Leftover chair and approval wording after D9 stage 3. **Text** (Low)

- Docstrings and messages still describe a reviewer's approval:
  - `service.py:2001` ("a reviewer approves its mapping")
  - `service.py:2264` ("for the preparer and reviewer")
  - `service.py:1936` ("Propose and approve the file again")
  - `assurance_domain/lifecycle.py:7-8,74`
  - `procedures_ap/coverage.py:146-147` ("a different reviewer approves that
    validation")
  - `procedures_ap/quickbooks.py:40-41,585`
  - `workbench_seed.py:7` ("the reviewer approves each mapping")
- `readiness()` still builds `document["team"]` with a `reviewer` slot from
  old `principal_assignment` rows (`service.py:1648-1656`). Display only: no
  gate reads it (`readiness.py:91`). But on an old engagement, a person can
  appear as "reviewer" next to work they never reviewed. The roadmap states
  that the table stays as history.

No behavior found that records a review.

### Info. A full refund shows as a round trip. **As expected**

Pay vendor 5,000; the vendor returns 5,000 (or 4,950) within 30 days. That is
reported as 1 cycle. A 500 partial refund is not. Each is a lead, the manual
calls them leads, and flows typed as reversals are suppressed. No change
suggested.

## 3. Claims checked and confirmed

- **D9 stage 3.**
  - The removed routes (`team`, `mappings/x/approve`, `lock`,
    `runs/x/review`, `dispositions/concur`) return 404.
  - `X-Acting-Principal: carol` changed nothing. The journal and
    `approved_by` show the session user (`dave`).
  - An old database with pending mappings loads, migrates, lists sources and
    team, and confirms the pending mapping (`approved_by: dave`, event
    `mapping.confirmed`).
  - Every POST route passes the session's `actor`. None takes a person's
    name from the body. `opinion_decision`'s `decided_by` and the
    disposition and risk `proposed_by` are the session user.
  - The case loaders (`load_case`, `seed_kestrel`) take the session user.
  - Exception: M1. It is about the engagement, not the person.
- **Case not fitted.**
  - `git diff --stat a2cd564~1 HEAD` lists no Trial_Balance file.
  - Journal net by account, before (a2cd564~1) and after (HEAD): 0 accounts
    changed (script over both workbooks).
  - Unpaid Bills open-balance total 287,640.18, before and after. The
    per-vendor balances moved (Kinetic, Moraine, Summit, Velo). A search of
    keys, lessons and docs found none of the old per-vendor figures.
  - Checking reconciliation totals are identical.
  - In the July bank statement only the check numbers changed, not the
    amounts.
  - a2cd564 touched no engine file.
  - a541e50's engine changes are the new procedure and the neutral company
    name. I read the graph code: flows create `entity:` nodes and payments
    end at `vendor:` nodes, so the "changed no result" claim holds.
  - `check_key.py` derives the sequence, the vendor name match, the
    self-signed checks and the round trip from the data files, not from the
    generator.
- **The manual's round-trip text** ("about the same amount within a month,
  through up to four transfers") matches the code: `amount_tolerance 0.02`,
  `max_days 30`, `max_hops 4`.
- **The signature log agrees with the Journal.** Of its 96 checks, all are
  in the Journal and none differs in amount from the Journal's bank credit.

## 4. Not checked

- No screen.
- f99a39b ("map all" leaves out raw exports) beyond the test suite.
- f01b9c7 (Benford in by default) beyond reading the roadmap.
- The Benford 1,000 source (known and stated).
- Oceanview.
- The 8f206a5/13b94be/9a2800a roadmap commits, beyond reading the sections
  the brief names.
- How QuickBooks prints a voided check in the Journal export (M2 rests on my
  understanding of it).
