# How Noesi Assurance works

*What it does, the maths it uses, what makes it different, where it can be wrong, and what it adds.*
*Written 4 Oct 2026 from the code (`packages/`), not from the lesson text. File references say where to
check each claim.*

---

## 1. What it is, in one paragraph

Noesi is a workbench that runs alongside a real audit. You load the client's own files, such as
QuickBooks exports and schedules. It tests **every row**, not a sample, wherever the data allows, and
gives every result with its evidence. It also says plainly what it could **not** test, and why. It
does not sign, approve, or decide: one user per engagement, and the judgments stay with the auditor
(THE-REAL-GOAL.md).

## 2. How a test runs, start to finish

1. **Load.** A file is stored with its SHA-256 fingerprint, size and source. QuickBooks exports load
   *raw*, through a recipe that knows their layout. Each export is footed against its own TOTAL row;
   one that doesn't add up is refused, not guessed (`procedures_ap/quickbooks.py`, `ingest.py`;
   `service.py` build_trial_balance).
2. **Map.** The user confirms which file is which table (vendors, journal, trial balance). The mapping
   is recorded (`service.confirm_source_mapping`).
3. **Run.** Before a procedure runs, Noesi freezes a **job manifest**: the procedure, its version, each
   input table's SHA-256 and row count, and every setting in force. The job ID is a hash of all of
   that, and the tables are re-checked against those hashes before the run (`assurance_domain/jobs.py`).
4. **Record what was read.** The run logs which tables and settings the engine actually read. A later
   change marks the result **stale** only if it touched one of those (`procedures_cycles/engines.py`,
   `service.run_procedure`).
5. **Findings.** Each finding is a **receipt**: a verdict, its evidence, and a content hash, so the same
   finding always gets the same ID (`assurance_domain/receipts.py`). The verdicts:
   - **AGREE:** checked, and it holds;
   - **TENSION:** something to look at;
   - **CLASH:** an exception;
   - **ORPHAN:** something on one side with no match on the other;
   - **AMBIGUOUS:** the test refused to decide;
   - **ERROR:** the test failed to run.
6. **Decide.** The auditor gives each finding a disposition. The summary of audit differences (SAD)
   totals the misstatements by statement line against materiality (`assurance_domain/sad.py`).
7. **Complete.** The readiness check lists, by name, everything still open. The draft opinion says what
   the evidence points to and which judgments remain (`readiness.py`, `opinion.py`).
8. **Export.** The record can be exported and re-verified offline. Every receipt re-hashes.

## 3. The maths

| Area | Method | Where |
|---|---|---|
| Footing and ties | Exact decimal arithmetic (no floating point for money); totals against TOTAL rows; subledger to ledger | `assurance_domain/money.py`, `procedures_cycles/statements.py` |
| Analytics | Movement flagged when the change is over the % threshold or the amount threshold; ratios from mapped statement lines | `statements.py` |
| Statistical sampling (MUS) | Sample size n = confidence factor ÷ (tolerable ÷ population); interval = population ÷ n; tainting = misstatement ÷ book value; upper misstatement limit by the textbook layering of Poisson upper limits | `procedures_cycles/sampling.py` |
| Attribute sampling | Exact one-sided binomial upper deviation rate; sample size as the smallest n that keeps the upper bound under the tolerable rate | `sampling.py` |
| Nonstatistical sampling | Ratio projection: sample misstatement × population $ ÷ sample $; allowance for sampling risk = tolerable − projected | `sampling.py` |
| Benford's law | First-digit test per population, judged by mean absolute deviation against Nigrini's bands. The per-digit z-test is shown but deliberately not used to raise findings: with nine digits, about one clean population in five would flag by chance | `procedures_cycles/forensic.py` |
| Recomputations | Depreciation (straight line), accruals and prepaids by days, interest on average balance, the covenant ratio | `ppe.py`, `accruals.py`, `debt_equity.py` |
| Population completeness | Every account rolled forward: last year's balance + this year's Journal lines = this year's balance | `procedures_cycles/journal.py` |
| Journal-entry traits | Weekend or holiday, round amount (≥ threshold and a multiple of the unit), unauthorized user, seldom-used account, posted after period end, manual with no description | `journal.py` |
| Duplicates and twins | Same supplier invoice number across vendor records; vendor records with near-identical name, address or phone | `procedures_ap/engines.py`, `structural.py` |
| Split purchases | A vendor's payments grouped within a window, under the approval limit | `procedures_ap/engines.py` |
| Check sequence | Gaps and reused numbers per bank account | `forensic.py` |
| Vendor ↔ employee | Bank account, phone (last seven digits), tax ID, full name; and it says which fields couldn't be compared | `forensic.py` |
| Money out and back | Directed graph of payments; cycles back to the client with amounts within a tolerance and dates within a window; known legitimate flows (reversals, intercompany) set aside | `procedures_ap/structural.py` |

## 4. What makes it different

- **Whole populations, not samples,** for the tests above. Sampling remains where the audit needs it
  (confirmations, pricing), with the standard formulas.
- **It says what it could not test.** The Coverage screen reconciles every procedure against the data:
  - **executable:** the data supports it;
  - **partial:** only part of it can be tested;
  - **blocked:** it can't run, and the screen names the missing field or dataset.

  On the Kestrel demo, Coverage shows 37 executable, 4 partial and 6 blocked (49 in the catalog, 2
  left out). A blocked test is never shown as passed.
- **Refuses instead of guessing:** an unfooted export, an unknown layout, a population too small for
  Benford, an unset setting. Each refusal names its reason.
- **Every result can be traced and re-checked:** input hashes, setting values and content-addressed
  receipts. The question "what exactly did you test, on which data?" has a mechanical answer.
- **Calibrated against an answer key, never fitted to it.** Kestrel's finish-line check compares the
  Workbench with an independently computed key: **174 match, 0 differ, 2 not in Noesi**, 37 procedures
  run (FINISH-LINE-REPORT.md). The engine is never changed just to make a Kestrel number match.

## 5. Uncertainty, limits and possible errors

These are stated plainly because they are the point.

- **A finding is a lead, not a conclusion.** Exceptions need inquiry. Fraud is a legal judgment.
- **Data in, results out.** Noesi tests the files it is given. It cannot tell whether they are complete
  or real: a missing Journal entry, a forged invoice, or a whole second set of books is invisible to it.
  The roll-forward proves the account totals reconcile, not that every entry exists.
- **It cannot test what the records don't hold.** QuickBooks Online exports carry no approver and no
  goods-received record, so the three-way match is blocked and segregation of duties is partial.
  Signatures come only from what the team recorded off the bank's images.
- **It cannot see people.** It cannot confirm whether an employee exists, why an entry was posted, or
  whether a related party was left off management's list. Matching only finds names on the list.
- **Thresholds are judgments.** Materiality, tolerances, windows and the Benford minimum are the
  auditor's settings. Different settings give different findings.
- **Float arithmetic in the structural layer.** Twin and round-trip screening uses floating point (for
  parity with the prototype). It only produces leads routed to review, never SAD amounts.
- **Known open items (4 Oct 2026):**
  - The related-party match words Jo Kestrel's address match as "employee e01, a family member?",
    though E01 *is* Jo Kestrel.
  - The demo labels all six hand-prepared files "from the QuickBooks export", though some come from
    bank, client or auditor files.
  - Going-concern indicators use the current ratio before adjustments.
  - A QuickBooks recipe version change turns most pages red instead of flagging the one file.

  Each one may be a software bug, and none has been investigated yet.
- **Tested so far on teaching cases.** It has 523 unit tests and is calibrated on Kestrel, but not yet
  checked on Oceanview with a working CPA, or on a real client.

## 6. What it adds to an audit

- **Coverage you can state:** "every bill, payment and journal line was tested for these traits", instead
  of "a sample of 40".
- **Speed on the mechanical work:** footing, ties, roll-forwards, recomputations and fraud screens, so the
  auditor's time goes to the exceptions and the judgments.
- **Honesty about limits as a deliverable:** the blocked and partial list is what to ask the client for,
  and what the file must say was not tested.
- **A record that can be checked:** hashes and receipts make the work reproducible and tamper-evident.
  That matters in review, and if the work is ever challenged.
- **A teaching tool:** every number in the Kestrel course is computed both by hand and by the Workbench,
  and compared with the key.

## See also
- The manual, chapters 1–8: the audit process and the Workbench, step by step.
- The Audit Code Atlas (HTML): every stop's route through the code, with the real source.
- `docs/ARCHITECTURE.md`, `docs/PRODUCTION-READINESS.md`, `THE-REAL-GOAL.md`.
