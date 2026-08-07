# Chapter 2 — Planning, materiality, and risk

## In practice

**Materiality** (AU-C 320) is the magnitude of misstatement that could
reasonably influence the economic decisions of the financial-statement
user. You set it at planning, on a benchmark that matters to the user —
revenue, assets, pre-tax income — and you document the basis and rationale.
Two derived figures do the day-to-day work:

- **Performance materiality** (commonly 50–75% of overall) — the level you
  actually design procedures to, leaving headroom for undetected and
  aggregation error.
- **Clearly trivial** (commonly ~5% of overall) — below this, a
  misstatement need not even be accumulated, *unless it is qualitatively
  significant*. An unauthorized payment is qualitatively significant at any
  amount; a $40 pricing difference is not.

**Risk assessment** (AU-C 315) identifies where the statements could be
materially misstated and *why* — and every identified risk must map to a
response (AU-C 330): a procedure that addresses it at the assertion level.
The assertions for a transaction cycle: **occurrence** (it happened and
pertains to the entity), **completeness** (everything that happened is
recorded), **accuracy**, **cutoff** (right period), **classification**, and
— treated as first-class in this cycle — **authorization**.

The discipline to internalize: a procedure justifies its place on the plan
by the risk and assertion it addresses, not by being easy to run.

## In the workbench

On **SAD & Completion**:

- Set **materiality** with its basis and rationale. The workbench derives
  performance materiality (75%) and the clearly-trivial threshold (5%)
  from it, and both appear on the SAD and the workpaper.
- Mark the **risk assessment** and **controls** stages complete when that
  work is done — both are readiness gates
  (`RISK_ASSESSMENT_NOT_COMPLETE`, `CONTROLS_NOT_COMPLETE`).

Every procedure contract in the library carries its cycle, its
**assertions**, its stated **limitations**, and the data and policies it
requires — visible on the **Coverage** tab. This is the tool's half of the
risk-to-procedure linkage: you decide which risks matter; the contracts
tell you which assertions each procedure actually addresses, so your plan's
mapping is checkable rather than aspirational.

Deselecting a procedure is allowed — with a written rationale. An
unexplained exclusion blocks completion
(`PROCEDURE_EXCLUSIONS_WITHOUT_RATIONALE`), because "we skipped it" is not
documentation.

## In Harborline

The audit plan
([`02-audit-plan.md`](../../case-studies/harborline-marine/docs/02-audit-plan.md))
sets materiality at **420,000** (1% of revenue — the benchmark the lender's
covenant tracks), giving performance materiality 315,000 and clearly
trivial 21,000. Enter 420000 on the SAD screen and confirm the derived
figures match the plan.

Then read the plan's risk table closely — it is the best page in the case.
Each row is a fact from the engagement brief (the AP supervisor vacancy,
vendor creation moving into purchasing, the receiving-process change)
turned into an assertion-level risk and answered by a specific procedure.
When you reach chapter 5, you will run those procedures; the reason each
one is on the plan is in this table, not in the software.
