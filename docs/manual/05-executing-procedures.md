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

Where the tool and your hand work differ, trace the source rows and policy
before reading the answer key. A mismatch can be an engine defect, a mapping
defect, a population limitation, or a judgment the engine properly leaves to
you.
