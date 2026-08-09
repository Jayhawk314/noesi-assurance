# Chapter 8 — Glossary and reference

## Product terms ↔ standards vocabulary

| Product term | In standards language |
|---|---|
| Receipt | Documented audit evidence of one finding: the observation, its source records (content-hashed), the tolerance applied, and its stated limitation — identified by the hash of its own content |
| Verdict | The type of claim a finding makes (contradiction, absence, pattern) — see table below |
| Refusal | The tool declining to perform or conclude for stated reasons — the raw material of a **scope limitation** |
| Coverage | Scoping: which planned procedures the obtained evidence (and this build) can actually support |
| Evidence request | An incremental **PBC item**, annotated with the procedures it would unlock |
| Policy | A documented engagement-level parameter (approval threshold, testing window) — an audit decision, not a data fact |
| Contract | The versioned definition of a procedure: objective, assertions, required evidence, limitations — the methodology artifact |
| Risk register | The assessed **risks of material misstatement** at the assertion level (AU-C 315), each graded and linked to the procedures that respond to it (AU-C 330) |
| Risk level | The combined inherent-times-control **RMM** conclusion (unassessed → significant); `high`/`significant` require a second person's concurrence, like a disposition |
| Assertion | What a finding (or a risk) is about: occurrence, accuracy, authorization, cutoff, completeness — the audit assertions this cycle tests |
| Concurrence | A second person's agreement with a proposed judgment (AU-C 220), required above the trivial threshold for dispositions and for high/significant risks; never the proposer |
| Disposition | The auditor's documented conclusion on a finding (AU-C 450 accumulation and evaluation) |
| SAD | Summary of audit differences / uncorrected misstatements |
| Lock | File assembly: the frozen, signed, journal-anchored record of the completed engagement |
| Supersession | A documented post-assembly change (AU-C 230 / AS 1215): reason, who, when — with the prior record preserved intact |
| Chair | The role a single pilot operator is currently acting in; gates treat chairs as separate people |
| Journal | The engagement's hash-chained decision trail: who did what, when, in what capacity |

## Verdicts

| Verdict | Claim | Typical practice meaning |
|---|---|---|
| `CLASH` | Two pieces of evidence contradict beyond tolerance | Exception / potential misstatement or control violation |
| `ORPHAN` | Expected corroborating evidence is absent | Exposure to investigate; may be timing, completeness, or worse |
| `TENSION` | A pattern warrants review | Lead / anomaly — not an allegation |
| `AGREE` | Evidence corroborates | Coherence pass (mostly internal) |
| `ERROR` / `AMBIGUOUS` | The comparison itself failed or cannot decide | Fix the evidence or the parameters before relying on anything |

Finding classes inside evidence: `PROVED_EXCEPTION`, `EXPECTED_BUT_MISSING`,
`STRUCTURAL_ANOMALY`, `CONTROL_OBSERVATION`, `CONJECTURE`, `REFUSAL`.

## Coverage statuses

| Status | Meaning |
|---|---|
| `executable` | Data present, policies set, executor registered — will run |
| `partial` | Fields or a required policy missing |
| `blocked` | A required population not supplied |
| `unsupported` | No executor in this build; data cannot change it |
| `not_selected` | Deselected by the team (rationale required) |

## Readiness blocker codes

| Code | Clears when |
|---|---|
| `MATERIALITY_NOT_SET` | Materiality entered with an amount > 0 |
| `RISK_ASSESSMENT_NOT_COMPLETE` / `CONTROLS_NOT_COMPLETE` | Stage marked complete |
| `RISKS_UNASSESSED` | Every recorded risk graded to a level |
| `HIGH_RISKS_WITHOUT_RESPONSE` | Every high/significant risk has a planned response |
| `HIGH_RISKS_WITHOUT_PROCEDURE` | Every high/significant risk has a responding procedure linked |
| `RISKS_AWAITING_CONCURRENCE` | Every fully-specified high/significant risk concurred by a second person |
| `TEAM_ASSIGNMENTS_INCOMPLETE` | Preparer and reviewer assigned |
| `SELECTED_PROCEDURES_BLOCKED` / `_PARTIAL` | Missing data/fields/policies supplied — or the procedure deselected with rationale |
| `SELECTED_PROCEDURES_PENDING_RUN` | Every selected executable procedure has been run |
| `PROCEDURE_RUN_REVIEW_PENDING` | Every completed run reviewed **and** approved (applies to reruns after reopening too) |
| `PROCEDURE_EXCLUSIONS_WITHOUT_RATIONALE` | Every deselection has a written rationale |
| `MISSTATEMENTS_UNRESOLVED` / `SUBSTANTIVE_ITEMS_UNRESOLVED` | Every finding dispositioned |
| `WAIVERS_ABOVE_TRIVIAL_THRESHOLD` | No waiver exceeds the clearly-trivial threshold |
| `SCOPE_ITEMS_UNRESOLVED` | Every refusal resolved or accepted as a scope limitation |
| `COMPLETION_PROCEDURES_INCOMPLETE` / `COMPLETION_EVIDENCE_MISSING` | All six completion checks done, each with a note or evidence |
| `DECISION_TRAIL_BROKEN` | The journal hash chain verifies (if it does not, stop and investigate) |

## Standards referenced in this manual

AU-C 220 (engagement quality), 230 (documentation; assembly and
post-assembly changes), 240 (fraud considerations), 300/315/330 (planning,
risk, responses), 320 (materiality), 450 (evaluation of misstatements),
500 (audit evidence), 560 (subsequent events), 580 (written
representations), 700 (forming the opinion). PCAOB AS 1215 where retention
and the 45-day assembly window differ. Citations anchor further reading;
they are not a substitute for the standards themselves.

## The case, cross-referenced

| You are reading | Pair it with |
|---|---|
| Chapter 1–2 | Case brief `01-engagement-brief.md`, plan `02-audit-plan.md` |
| Chapter 3–5 | Walkthrough `03-walkthrough.md`, assignments A1–A8 |
| Chapter 6 | Assignments A9 (SAD) |
| Chapter 7 | Assignment A10 (limitations), instructor `VERIFIED-RUN.md` |
