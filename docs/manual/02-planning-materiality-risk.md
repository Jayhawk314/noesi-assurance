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

**The audit risk model** frames *how much* work a risk demands. Audit
risk — the risk of issuing a clean opinion on materially misstated
statements — is the product of three factors:

- **Inherent risk** — susceptibility to misstatement before any controls
  (a cash-heavy cycle, complex estimates, incentive to misstate).
- **Control risk** — the risk that the client's controls fail to prevent or
  detect it.
- **Detection risk** — the risk that *your own* procedures fail to catch
  what remains.

Inherent and control risk are the client's condition; you assess them.
Their combination is the **risk of material misstatement** (RMM). Detection
risk is the one you control: the higher you assess RMM, the *lower* the
detection risk you can accept — and therefore the more persuasive, and more
extensive, your procedures must be. A **significant risk** (AU-C 315) sits
high enough on that scale to demand specific attention and, usually, a
substantive response designed for it alone. This is the arithmetic behind
"which procedures, and how much" — it is judgment expressed as a dial, not a
formula the software computes for you.

The discipline to internalize: a procedure justifies its place on the plan
by the risk and assertion it addresses, not by being easy to run.

**Fraud is part of the same risk assessment** (AU-C 240). The auditor
keeps professional skepticism throughout, holds an engagement-team
discussion of how and where the statements could be misstated by fraud,
asks management and others about fraud risks, and weighs **fraud risk
factors**: incentives or pressures, opportunities, and attitudes or
rationalizations (the fraud triangle). Two fraud risks are built in:
**revenue recognition** is presumed a fraud risk unless you document why
not, and **management override of controls** is a risk in every audit,
answered by testing journal entries, reviewing estimates for bias, and
evaluating significant unusual transactions. A fraud risk is normally a
significant risk. SAS No. 151, approved in August 2026, replaces AU-C 240
for periods ending on or after December 15, 2028 (early adoption
permitted); the definition of fraud and the auditor's objective do not
change. The **Fraud in payables** course, lesson F2 (`/studio/#/learn/fraud/2`),
works a full fraud risk assessment on Harborline.

## In the workbench

On **SAD & Completion**:

- Set **materiality** with its basis and rationale. The workbench derives
  performance materiality (75%) and the clearly-trivial threshold (5%)
  from it, and both appear on the SAD and the workpaper.
- Mark the **risk assessment** and **controls** stages complete when that
  work is done — both are readiness gates
  (`RISK_ASSESSMENT_NOT_COMPLETE`, `CONTROLS_NOT_COMPLETE`).

On **Planning & Risk** you keep the risk register itself. Record each risk
of material misstatement **at the assertion level** — choose the assertion
(occurrence, accuracy, authorization, cutoff, completeness), grade its
**level** (unassessed → low → moderate → high → significant), and state the
rationale and your planned response. Then **link the procedures that respond
to it**; the screen offers the candidates whose contract addresses that same
assertion, so the mapping is checkable rather than aspirational.

The **level** you grade is the combined risk of material misstatement — the
inherent-times-control conclusion from the model above. You perform that
decomposition in your judgment and record it in the rationale; the workbench
stores the conclusion and the response it drives, not the arithmetic. It
deliberately does not present separate inherent/control/detection dials,
because it will not manufacture the look of a computed number where the
substance is professional judgment.

The register is auditor **judgment**, not a computed output — the engine
never grades a risk. So it carries the same separation as dispositions and
runs: a high or significant risk is a *proposal* until a second person
(reviewer or partner, never the proposer) concurs, and changing the level,
response, or linked procedures voids that concurrence. Three readiness gates
follow from the register, and each blocks the lock:

- `HIGH_RISKS_WITHOUT_RESPONSE` — a significant risk with no planned response.
- `HIGH_RISKS_WITHOUT_PROCEDURE` — a significant risk no procedure answers.
- `RISKS_AWAITING_CONCURRENCE` — a fully-specified significant risk no second
  person has concurred.

That last trio is the point: the tool will not let you lock an engagement
that names a significant risk and then does nothing about it.

**Fraud risks go in the same register.** There is no separate fraud flag,
so start the title with "Fraud:" and name the fraud risk factor in the
rationale, for example "Fraud: self-approved payments during the
supervisor gap", against **authorization**, linked to
`ap.segregation_of_duties`. The payables procedures answer fraud risks in
this cycle (look-alike vendors, self-approval, split payments, bank and
ledger mismatches). Two AU-C 240 responses fall outside the workbench:
journal-entry testing for management override, and procedures for the
revenue presumption. Record those risks here anyway, with the response you
perform elsewhere, so the plan shows how every fraud risk was answered.

Every procedure contract in the library also carries its cycle, its
**assertions**, its stated **limitations**, and the data and policies it
requires — visible on the **Coverage** tab. The findings table on **Runs &
Findings** now shows the **assertion** each exception bears, so a finding
traces back to the risk and assertion that put its procedure on the plan.

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
