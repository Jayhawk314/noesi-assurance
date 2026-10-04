# Chapter 5 — Executing procedures

## In practice

Substantive procedures produce evidence at the assertion level. Full-
population testing — examining every record rather than a sample — is one
of the genuine advantages data-driven auditing has over manual work, but it
changes how you read results:

- **A silent procedure means "within tolerance", not "nothing there".**
  Every automated comparison has a tolerance; differences inside it produce
  no exception. Whether a sub-tolerance difference matters is the
  auditor's call, so you must know the tolerance to interpret the silence.
- **An exception is not a misstatement.** A payment absent from the bank
  feed is an *exposure* to investigate; the misstatement is whatever the
  investigation concludes — possibly zero, if it cleared in January.
- **One defect can surface in several procedures.** A voucher citing a
  nonexistent PO fails the PO-reference test *and* the three-way match.
  Recognizing shared root causes — and not double-counting the exposure —
  is judgment no engine exercises for you.

Every run of a procedure is itself audit work, so its record says who ran
it, when, on which data and with which settings. Reviewing and approving the
work is your firm's process; Noesi asks for no sign-off.

## In the workbench

Run procedures from **Runs & Findings** or directly from the **Flow Map**
(the purchase-to-pay diagram; each arrow shows the procedures testing that
link). What a run records: a frozen **job manifest** (procedure and engine
versions, a digest of every input table, the effective policies) and a
sealed result. Re-running later is *reperformance* — a new job with its
own sequence number, never an overwrite.

"Completed" is not the same as "tested", and the Runs tab says which:

- **partly tested** — the run refused part of its population (for example
  Benford with one population below the minimum) and tested the rest;
- **tested nothing** — every part was refused; read its findings for why;
- **stale** — a file or setting that this run read has changed since, or a
  later rerun failed. The result is historical until you rerun it, and
  while the procedure is in the audit, readiness lists it
  (`PROCEDURE_RESULTS_STALE`). Left out with a reason, it stays labelled
  stale but does not block (except the procedures the draft opinion reads, which still block when
  stale); its findings still need a disposition. A change
  to a file or setting the run did not read leaves it current. The
  trial-balance line mapping counts as read only by runs that read the
  trial balance or the prior statements.

The live catalog on Coverage is the source of truth; it grows as a tested
cycle earns a contract and executor. Read it in families rather than
memorizing a frozen list:

| Family | Representative procedures | Read the results knowing |
|---|---|---|
| Planning and controls | trial-balance analytics, performance-materiality allocation, attribute evaluation | analytics create inquiry leads; control deviations change the audit response, not the books |
| Journal entries | fraud-risk tests and population rollforward | a risk characteristic selects an entry for inspection; it does not prove fraud |
| Revenue and receivables | cutoff, aging-to-ledger tie, confirmations and three sampling methods | alternative sampling methods are not cumulative; classification of confirmation differences is auditor evidence |
| Payables | references, duplicates, subsequent-disbursement search, document chain and three-way match | missing purchase or receiving evidence limits the conclusion; a selected payment needs every line inspected |
| Payroll, PP&E, debt, equity and accruals | register tests, rollforwards, recalculations and covenant tests | schedules are management assertions until vouched; covenant and estimate conclusions remain professional judgments |
| Cash and inventory | bank reconciliation, transfers, count/listing trace and pricing projection | cutoff evidence is account-specific; observation and ownership cannot be automated from a spreadsheet |
| Estimates and related parties | retrospective review and matching | bias patterns and name/address matches are leads, not conclusions about intent or completeness |
| Completion | adjusted trial balance, subsequent events, going concern, representations and uncorrected misstatements | the engine assembles evidence and contradictions; the partner records the report judgments |
| Fraud and forensic | check-number sequence, vendors that match an employee, payments approved by their preparer, round trips in a flow-of-funds schedule, first-digit (Benford) test | every result is a lead for follow-up, never a conclusion of fraud; each test also says what it could not compare |

**The forensic tests, one by one** (all on the **Fraud** tab, with the other
fraud tests):

- **Check-number sequence** runs every check number in the Journal (or the
  payment records and payroll register when the Journal carries none), one
  run per bank account and payroll apart, and lists the numbers missing
  between the first and last check and any number used for two payees. A gap
  is voided, issued outside the records, or hidden; account for it with the
  voided check or the bank's paid-check images.
- **Vendors that match an employee** compares the vendor list with the
  employee master by bank account, phone, tax ID and full name, and states
  which fields one side did not carry.
- **Payments approved by their preparer** reads an approval or signature log
  (a bill-pay approval report, or the signers the team read off the bank's
  paid-check images; role *Payment approvals*) and lists each payment signed
  or approved by the person who prepared it, and each with no approver. It
  tests only the payments in the log, and cannot see a stamp or a forgery.
- **Round trips** (closed value flow) look for money that leaves and returns
  to the client for about the same amount within a month, through up to four
  transfers, in the *Value flows* file. Every leg must be in that file,
  including the client's own payment: the tool does not trace money beyond
  the books. A cycle with a flow typed as a reversal, a correction, an
  intercompany or shared-service settlement is not reported, and the run
  counts it as suppressed.
- **First-digit (Benford) test** compares the first digits of journal lines,
  bills and payments with Benford's law, once the population reaches the
  minimum the team sets; below it, the result says *not tested*.

Every finding arrives as a **receipt**: verdict, reason, the source rows
(with content hashes), the tolerance applied, and a stated limitation —
identified by the hash of its own content. Chapter 6 is about judging them.

## In Kestrel

The demo has already run every executable selected procedure. Open the runs
and reconcile each result to your own work. Useful anchors:

- Journal-entry testing identifies the post-closing entry and the unusual
  round, weekend entry posted by someone outside the authorized-user policy.
- Receivables separates the aging-to-ledger difference, a customer credit,
  the allowance recomputation, and confirmation misstatements. The remaining
  allowance difference is a known write-off timing question for the auditor;
  the engine does not guess it away.
- Cash distinguishes a stale outstanding check, an amount mismatch, a slow
  deposit in transit, and a kiting-shaped transfer.
- Inventory keeps count/listing exceptions separate from the projected
  pricing result.
- Completion finds all five above-threshold July transactions, but the team
  must decide which reflect conditions at year end and which are routine.
- The forensic tests find one gap in the check sequence (three numbers the
  client cannot produce), one vendor carrying an employee's name (QuickBooks'
  vendor export has no bank account to compare), the consulting firm's checks
  signed by the bookkeeper who prepared them (from
  `auditor/check_signatures.csv`), and one round trip through a related-party
  customer (from `auditor/flow_of_funds.csv`). The first-digit test reports
  every Kestrel population as *not tested*: each is below the minimum the
  demo sets.

Where the tool and your hand work differ, trace the source rows and policy
before reading the answer key. A mismatch can be an engine defect, a mapping
defect, a population limitation, or a judgment the engine properly leaves to
you.
