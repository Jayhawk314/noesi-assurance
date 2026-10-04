# Review: manual docs against the code (4 Oct 2026)

Independent reviewer (Claude, fresh session). Nothing edited except this file. No push, no publish, no credits.
Code read is the working tree on 4 Oct (HEAD 5ded289 plus the uncommitted changes in `git status`,
including an uncommitted edit to `procedures_cycles/estimates.py`).

## How this was checked

- **Code read** for every table row and verdict claim in HOW-NOESI-WORKS.md (files named below).
- **Demo run:** `.venv\Scripts\python -m workbench_api --demo --port 8613 --data <scratchpad>`; read
  `/api/engagements/<id>/coverage`, `/readiness`, `/findings`, `/sources`, `/team` with the session token.
  The server was stopped afterwards.
- **Finish-line check re-run** against current code, with its report sent to the scratchpad (the repo's
  FINISH-LINE-REPORT.md was not touched): "174 of 176 match; 0 unexplained".
- **Test count:** `pytest --collect-only -q` → 587 tests collected (all under `tests/unit`).
- **Atlas:** `python docs\manual\refresh_atlas.py` (report mode) → "139 excerpts; 0 updated; 0 not found;
  0 marks missing". A separate script compared each excerpt's `src` with `lines[start-1:end]` of the
  current file: all 139 match exactly. Prose pulled out of the HTML (tags stripped) and the DATA block,
  then read.

## Must-fix

1. **HOW-NOESI-WORKS.md:58 says vendor twins match on a "near-identical name, address or phone". The code
   compares neither address nor phone.** `procedures_ap/engines.py:331-375` (`vendor_relational_twins`)
   compares vendor **names** only (SequenceMatcher on a normalized name). It then calls
   `structural.relational_twin_findings` (`structural.py:407-460`), which fingerprints **activity**:
   amounts, months, and created_by/approved_by. The contract (`procedures_ap/contracts.py:100-104`) requires
   only `vendor_number, vendor_name`. A grep of `procedures_ap/` for "address" or "phone" finds only the
   ingest synonyms and the QuickBooks recipe column names. As written, the doc claims a test the software
   does not run. (Address matching does exist elsewhere: payroll.py compares employees with vendors, and
   estimates.py compares related parties with employees.)
2. **HOW-NOESI-WORKS.md:109 says "523 unit tests". The count is 587.** Checked with `pytest --collect-only`.
   The 11b4038 commit message says 586, and the uncommitted test in `test_estimates.py` adds one.
3. **HOW-NOESI-WORKS.md:50 says analytics flag a movement over "the % threshold *or* the amount threshold".
   The default is *and*.** `statements.py:273-298`: `rule = ... or "and"` (comment: "unset, both (the
   stricter)"). "or" applies only when the auditor sets `analytics_threshold_rule`. Saying "or" overstates
   what gets flagged by default.

## Should-fix

4. **The first open item (HOW-NOESI-WORKS.md:101-102, "Jo Kestrel ... a family member?") is stale against
   the working tree, and line 108 ("none has been investigated yet") is no longer true for it.** The
   uncommitted diff to `estimates.py:154-165` adds a same-name branch ("matches employee e01 by name and
   address"), with a test in `test_estimates.py`. On the demo, `/findings` now reads "related party Jo
   Kestrel matches employee e01 by name and address — confirm the role and pay are real and disclosed".
   The fix is **uncommitted and has not had a second-agent review**, so the doc should say "fixed in
   working tree, not yet committed or reviewed", not "open".
5. **The Atlas still shows a visible "Still to fix" warning that the code no longer supports.** Stop 10
   ("The record and the backup") has `flag`: *"workpaper.py prints 'Approved mappings and datasets' and an
   'Approved by' column (lines 135–136)"*, and the page renders it as ⚠ (`Noesi Audit Code Atlas.html`
   template line 279). `workpaper.py:189-190` now prints "Confirmed mappings and datasets" / "Confirmed
   by". The same stop's `render_workpaper` note, and the page intro, both say it "was fixed on 3 Oct", so
   the page contradicts itself. `refresh_atlas.py` never edits prose, so it cannot catch this.
6. **Chapter 5 (05-executing-procedures.md:42-44) and the glossary (08-glossary.md:62) leave out the
   opinion-input exception for stale results.** `readiness.py:62-69, 166-169`: a stale result that is left
   out with a reason does **not** block, *except* for the four procedures the draft opinion reads
   (`completion.uncorrected_misstatements`, `completion.going_concern_indicators`,
   `completion.representation_letter`, `debt.covenants`), which block even when left out. As written,
   chapter 5 tells the reader a left-out stale result never blocks. The glossary row's "Clears when"
   ("every run whose file or setting changed ... has been rerun") also misses that a left-out procedure
   with a rationale clears without a rerun. The rest of chapter 5's new paragraph matches commit 11b4038:
   only inputs actually read count, and the line mapping counts as read only when Trial_balance or
   Prior_statements was read (`service.py:798-806`, `engines.py:86-105`).
7. **The glossary blocker table (08-glossary.md:52-70) does not match `readiness.py`.**
   - Missing codes the code can emit: `CONTROLS_UNASSESSED`, `CONTROL_RELIANCE_UNSUPPORTED`,
     `EVIDENCE_REVIEW_PENDING`, `EXTRACTION_APPROVAL_PENDING`, `TRANSFORMATION_APPROVAL_PENDING`
     (`readiness.py:141-146, 258-279`). The UI labels them in `screens.tsx:1044-1054`.
   - `SCOPE_ITEMS_UNRESOLVED` is listed, but in the Workbench it can never fire: `service.readiness`
     (`service.py:1812-1820`) passes `report = {"verdicts": [], "refusals": [], ...}`, and that blocker
     counts `report["refusals"]`. Refusals do still block, through `FINDINGS_OPEN`, as undisposed
     findings. The same empty `review_sources` means the two `*_APPROVAL_PENDING` codes cannot fire either.
     This may be dead code left from the approval removal, or a gap. **Not investigated: possible software
     issue, flagged rather than judged.**
   - `NO_DATA_WITHOUT_PARTNER_ASSERTION` still carries "PARTNER" in its name and comment
     (`readiness.py:241-250`), though roles were removed. The wording is a leftover. Behaviour is fine.
8. **Ch 1 and the glossary say there are "no chairs or roles". The API and the export still carry a
   `partner` role.** `/api/engagements/<id>/team` on the demo returns
   `{"principal_id": "local:JAMES", "role": "partner"}`. `service.py:185-186` assigns it ("kept so older
   records read the same way"), `service.readiness` (`service.py:1776-1784`) still builds
   preparer/reviewer/engagement_partner slots, and the export manifest includes `team` (`service.py:1914`;
   ch 7:45 lists "team"). Behaviour is one user. The docs should say the stored label stays for
   compatibility, as the Atlas does for the `approved` mapping status.
9. **HOW-NOESI-WORKS.md:58 points duplicates at the wrong file.** "Same supplier invoice number across
   vendor records" is `procedures_cycles/duplicates.py:25-65` (`ap.duplicate_bills`), not
   `procedures_ap/engines.py`. It also matches the same invoice number under the same vendor, not only
   across vendor records.
10. **README.md:29 links the Atlas through raw.githack on `main`, but the Atlas HTML is untracked**
    (`git status`: `?? docs/manual/Noesi Audit Code Atlas.html`). The link will 404 until the file is
    committed and pushed, which needs James's approval. Also, README.md picked up this "Three ways in"
    section while the review was running: it was not modified in the session-start git status but was by
    the time the Atlas was checked. Someone else is editing these docs at the same time.
11. **Thresholds on the round-trip test are fixed in code, not settings.** HOW-NOESI-WORKS.md:96-97 says
    "tolerances, windows ... are the auditor's settings". `engines.py:575-577` calls
    `directed_round_trip_findings(..., 0.02)` with defaults `max_days=30, max_hops=4`
    (`structural.py:521-524`), and none of these is a policy. Chapter 5:82-84 states "about the same
    amount within a month, through up to four transfers" correctly; the general sentence overstates.

## Notes

12. **ERROR verdict (HOW-NOESI-WORKS.md:38, glossary :37).** `ERROR` is in `receipts.VERDICTS`, but no
    engine emits it: a grep of `packages/` for `"ERROR"` finds only receipts.py. A failed run is a run
    with `status: "error"` and no findings (`jobs.py:120-124`). The doc reads as if failures arrive as
    ERROR receipts.
13. **"Recomputations: depreciation (straight line)"** (HOW-NOESI-WORKS.md:55). `ppe.py:8, 160-175` also
    recomputes declining balance (double and 150%). "The covenant ratio" is really covenants, plural
    (`debt_equity.py:162-245`).
14. **"Each export is footed against its own TOTAL row"** (HOW-NOESI-WORKS.md:20). True for grouped
    reports and list reports with `totals=True` (`quickbooks.py:91, 341-355, 445-480`). The Vendor Contact
    List is a flat list with no amounts to foot. Slight overgeneralization.
15. **Stale wording (HOW-NOESI-WORKS.md:28-30).** "Only if it touched one of those" is true for runs
    recorded since 3 Oct. Older runs without `inputs_read` go stale on any data or settings change, and a
    failed later rerun also marks a result stale (`service.py:855-895`). Chapter 5 mentions the
    failed-rerun case; HOW-NOESI-WORKS does not.
16. **Round trip "back to the client"** (HOW-NOESI-WORKS.md:62). `directed_round_trip_findings` walks
    cycles from **every** node, not only the client (`structural.py:563-564`). On Kestrel the one cycle
    found does return to the client.
17. **"Readiness lists, by name, everything still open"** (HOW-NOESI-WORKS.md:41, ch 7:33-34).
    `MISSTATEMENTS_UNRESOLVED` (demo: count 18), `SUBSTANTIVE_ITEMS_UNRESOLVED` and
    `WAIVERS_ABOVE_TRIVIAL_THRESHOLD` carry only a count, no `items` (`readiness.py:281-296`; demo
    `/readiness`). They are named on the SAD screen instead. "By name" overstates for those three.
18. **The Atlas run-sheet example cites `procedures_cycles/receivables.py:273 confirmations_mus`.** The
    def is at line 274. The example is labelled "Invented figures", so this is minor, but the refresh
    script does not cover prose line references.
19. **Atlas `journal_entry_testing` note: "Each test switches on only when you set its policy".** The
    unbalanced and weekend tests run with no policy (holidays are optional), and posted-after-period-end
    depends on a column (`journal.py:69-96, 150-157`).
20. **Refresh-script limitation (not a page error):** `refresh_atlas.py:51-61` (`verbatim`) accepts an
    excerpt if its old lines still appear anywhere in the file. If a function grows *after* its excerpted
    lines, the script reports "0 updated" while the excerpt has quietly become partial. The independent
    check found all 139 excerpts exact today, so no harm yet.
21. **Ch 3:189-193** says hand-prepared files' "provenance says so". It does, but as "prepared by hand
    from the QuickBooks export" for all six (`/sources` on the demo: inventory_count, bank_reconciliation,
    cutoff_statement, transfers, pricing_tests, adjusting_entries). That is HOW-NOESI-WORKS open item 2,
    **confirmed on the demo**.

## Claims checked and found consistent with the code

- Job manifest: procedure, versions, per-table SHA-256 and rows, policies, rerun sequence. Job ID = hash;
  `run_job` re-checks digests and refuses extra tables (`jobs.py:34-124`).
- Verdict list (`receipts.py:20`); receipt ID = SHA-256 of canonical JSON (`receipts.py:60-66`).
- MUS: n = CF×BV/TM rounded up, interval = BV/n, tainting, Poisson layering, CF solves CF = UL(r·CF)
  (`sampling.py:242-345`). Attribute: exact binomial upper rate, smallest n (`sampling.py:109-151`).
  Nonstatistical ratio projection and allowance = TM − |projected| (`sampling.py:225-239`). MUS is wired
  into `receivables.py:278-322`.
- Benford: MAD against Nigrini bands, z-test only names digits, minimum-population refusal is
  `AMBIGUOUS`/`REFUSAL` (`forensic.py:422-511`).
- Vendor ↔ employee: bank account, phone (last 7 digits), tax ID, full name; reports fields not compared
  (`forensic.py:238-339`).
- Check sequence: gaps and reuses per bank account (`forensic.py:28-160`).
- Roll-forward: prior + journal activity = current per account, with the closing-to-retained-earnings
  case (`journal.py:221-280`). JE traits as listed, plus "unbalanced" and "self_approved", which are not
  in the doc (`journal.py:203-205`).
- Split purchases: per-vendor clusters within `split_window_days`, each payment under the threshold
  (`procedures_ap/engines.py:135-216`).
- Float in the structural layer is stated in its docstring (`structural.py:1-11`). Round-trip and twin
  findings are TENSION/STRUCTURAL_ANOMALY, which `sad._is_candidate` (`sad.py:51-66`) never puts on the
  SAD. *Partly checked:* `ap.document_chain`'s classes were read only in part.
- Coverage on the Kestrel demo: `summary` = executable 37, partial 4, blocked 6, not_selected 2, total 49.
  The two left out are the partial `ar.confirmations_mus` and `ar.confirmations_difference`.
  Three-way match is blocked and segregation of duties is partial, as the doc says.
- Finish line: current code gives 174 match, 0 differ, 2 not in Noesi, 37 procedures run, the same as
  FINISH-LINE-REPORT.md.
- Open items 2 (provenance label) and 3 (going concern uses the unadjusted trial balance,
  `completion.py:86-110`) are confirmed in code/demo.
- Ch 2 defaults: PM 75%, clearly trivial 5% (`sad.py:24-25`). Ch 5's Kestrel forensic results (gap
  4422-4424, Owen Pike name match, three DM Consulting self-approvals, one round trip, Benford not tested
  for all three populations at minimum 1000) match the demo's `/findings`.
- Ch 1, 6, 7 have no leftover descriptions of locks, sign-off, approvals, concurrence or "mark reviewed"
  as live features. Each mention is framed as removed or as the firm's own process. UI tab names in the
  chapters exist in `apps/workbench-ui/src`.
- Atlas: opinion rule "largest ≥ M, from completion run else SAD total" matches `opinion.py:87-99`. SAD
  conclusion rule matches `sad.py:172-173`.

## Not checked

- Open item 4 (a QuickBooks recipe version change turns most pages red): not reproduced.
- Ch 2 lines 1-59 and ch 3 lines 1-39 ("In practice" standards text): standards citations not verified.
- Ch 3's claims about upload refusal of duplicate bytes, bulk loading, and "reperformance is the read
  path": not traced in code.
- The UI screens themselves: no browser was opened. Screen claims were checked only against tab-name
  strings and API output.
- `verify_packet` behaviour (ch 7 step 4): not run.
- Atlas DATA notes beyond those listed: about half the notes were compared with code, the rest read only
  for plausibility.
- Whether the uncommitted `estimates.py` change is correct beyond its own test and the demo output.
