# Cycle procedures: from an AP pilot to a full audit

*Written 2026-09-26. The design behind `packages/procedures-cycles`. It was prompted by
working a published integrated practice case end to end (friction log kept privately).
No case content is reproduced here. The methods are standard textbook and AICPA *Audit
Sampling* guide methods.*

## What was missing

The workbench ran eleven AP contracts. A full integrated audit also needs:

| Audit step | Mechanical work software can do | Judgment it must leave to the auditor |
|---|---|---|
| Preliminary analytics | foot the trial balance; compute ratios and % changes; flag movements | what a movement means; going-concern assessment |
| Materiality | allocate performance materiality; check the allocation ceiling | benchmark and percentage |
| Tests of controls | attribute sample size and CUER (statistical); SER + judged risk (nonstatistical) | which controls; what counts as a deviation; the conclusion |
| AR confirmation | nonstatistical, MUS and difference-estimation size, selection, projection and bounds | classifying each difference (client error, timing, customer error) |
| Unrecorded liabilities | selection of subsequent disbursements; tracing to the year-end listing | the date the liability arose (receiving report, invoice) |
| Cash | re-foot the reconciliation; outstanding-check and DIT cutoff; interbank transfer (kiting) analysis | follow-up of unusual items |
| Inventory | two-way count ↔ listing tracing; listing footing; pricing-test projection | observation of the count; obsolescence |
| Completion | apply proposed AJEs to the TB; summarize uncorrected misstatements by statement line vs materiality | the opinion |

## Design

1. **New package, not new AP contracts.** The eleven AP contracts stay byte-for-byte frozen
   (golden tests). `procedures_cycles.contracts.CYCLE_PROCEDURES` uses the same
   `ProcedureContract` shape, and `procedures_cycles.engines.EXECUTORS` uses the same
   `(tables, policies) -> (receipts, stats)` signature, so jobs, receipts, findings,
   review, dispositions and lock work unchanged.
2. **Opt-in by scope.** A partner records the engagement's scope (`workflow` section
   `cycles`: e.g. `["receivables", "cash"]`; kept apart from the existing `scope`
   key, which records scope-limitation decisions). Coverage includes a cycle's contracts only
   when that cycle is in scope. With no scope set, coverage is exactly what it was, so no
   existing engagement gains blocked procedures or readiness blockers. The service also
   refuses direct execution and risk-response links outside that recorded scope; a scope
   cannot be removed while an active risk or recorded run still depends on it.
3. **Auditor-obtained evidence is its own role.** Confirmation replies, inspected
   receiving-report dates and attribute-test exceptions are not client exports. Each has a
   role whose contract names it as auditor evidence. The engine evaluates it; it never
   invents it.
4. **Honesty rules carried over.** Missing or zero-row inputs mean `blocked`/`partial`,
   and the cycle executor independently emits a refusal if called with an empty role;
   judgments are policies (`blocked` until set); every projection states its method and
   its limits; a result "within tolerable" is a statement about sampling risk, not a
   clean opinion. A/R detail rows are aggregated to customer balance before confirmation
   sampling so the population and sampling unit stay consistent.
5. **Deterministic math, stdlib only.** Binomial and Poisson bounds by bisection on exact
   CDFs; normal coefficients from `statistics.NormalDist`; money in `Decimal`.

## Methods (reference)

- **Attribute sample size / CUER:** one-sided exact binomial upper bound at the risk of
  overreliance, rounded up to 0.1%. Size is the smallest *n* whose bound at
  ⌈n·EPER⌉ deviations is ≤ TER. This reproduces the AICPA tables.
- **Nonstatistical attribute:** SER = deviations / n; CUER = SER + auditor-estimated sampling risk.
- **Nonstatistical balances:** *n* = BV × CF / TM for the untested stratum; projection =
  sample misstatement × (stratum value / sample value); allowance = TM − |projection|.
- **MUS:** confidence factor via Poisson/gamma expansion; SI = population / *n*; basic
  precision = SI × UL(0); taintings (rounded up to 4 dp) ranked high to low × SI × the
  incremental factor; misstatements in items ≥ SI added unprojected.
- **Difference estimation:** *n* = (SD·(Z_A+Z_R)·N / (TM−E*))²; projection = mean
  difference × N; precision = N·Z_A·SD/√n·√((N−n)/N); accept when both limits lie within ±TM.
- **Kiting:** a transfer whose receipt is booked in the period but whose disbursement is
  booked after it overstates cash. A transfer in transit must appear as a DIT on the
  receiving reconciliation and an outstanding check on the disbursing one.

## Provenance and limits: read before relying on this

- **Where it came from.** These procedures were built while working one published
  integrated practice case written by textbook authors. The data shapes (an item-typed
  bank reconciliation, a four-date transfer schedule, a four-bucket aging, attribute
  data sheets) follow that textbook tradition. Real client exports rarely arrive in these
  shapes, so each needs an adapter, and no real-client export has been run through these
  procedures yet.
- **What is verified.** The sampling arithmetic reproduces the AICPA *Audit Sampling*
  tables cell for cell. Every executor has tests on invented data. The practice case's
  own worked figures (ratios, allowance, sample sizes) were reproduced without tuning.
  That shows the arithmetic is right. It does not show the procedures are complete or
  that they help on a real engagement.
- **What was kept out on purpose.** The engine never accepts a sample value or sample
  size typed in beside the rows. Every sampled item must be itemized, so the result can
  be recomputed. Shorthand in a source (e.g. "items 6–35: various") is the adapter's
  problem, not the engine's.
- **What it is not.** It is not an audit methodology, not a substitute for AU-C / PCAOB
  compliance, quality management or professional judgment, and it issues no opinion.
  It performs and records mechanical tests the auditor chose, with their evidence.
- **Before any real engagement:** independent review of this package
  (docs/INDEPENDENT-REVIEW.md); a second, independently written test case for these
  cycles; adapters for at least one real export per role (e.g. an accounting-package
  aging report, a bank CSV); a pilot alongside a licensed CPA doing the work by hand.
