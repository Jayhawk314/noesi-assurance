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
| Risk level | The combined inherent-times-control **RMM** conclusion (unassessed → significant); `high`/`significant` need a response and a responding procedure |
| Assertion | What a finding (or a risk) is about: occurrence, existence, completeness, accuracy, valuation, cutoff, classification, presentation, rights, authorization |
| Disposition | The auditor's documented conclusion on a finding (AU-C 450 accumulation and evaluation) |
| SAD | Summary of audit differences / uncorrected misstatements |
| Record | The engagement's testing, exported as one JSON file with its own digests; unsigned (locks and signatures were removed on 2 Oct 2026) |
| Supersession | A standards term: a documented post-assembly change (AU-C 230 / AS 1215) with reason, who and when, the prior record preserved. Noesi has no unlock or supersession step since 2 Oct 2026; each export is journaled and earlier exports stay as they were |
| User | The one person an engagement's work is recorded under; Noesi has no chairs or roles (removed 2 Oct 2026) |
| Journal | The engagement's hash-chained decision trail: who did what, and when |
| Refused field | A canonical field the client's file does not contain — recorded, never filled in; a gap in the evidence obtained |
| Set aside (quarantined row) | A row excluded from the tested population at normalization, with its reason and sheet row — a **completeness** question to resolve, not a deletion |
| Recipe | A reviewed way of reading one known client report layout (a QuickBooks Online export); part of the mapping you confirm |
| Subtotal check | **Footing** a client-prepared report: re-adding its detail and comparing with its printed totals before relying on it |
| Subledger tie | Agreeing the AP subledger (the unpaid-bills listing) to the Accounts Payable control account in the general ledger |

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
| `not_selected` | Left out of the audit (shown as "left out"; a rationale is required) |

## Readiness blocker codes

| Code | Clears when |
|---|---|
| `MATERIALITY_NOT_SET` | Materiality entered with an amount > 0 |
| `RISKS_UNASSESSED` | Every recorded risk graded to a level |
| `HIGH_RISKS_WITHOUT_RESPONSE` | Every high/significant risk has a planned response |
| `HIGH_RISKS_WITHOUT_PROCEDURE` | Every high/significant risk has a responding procedure linked |
| `SELECTED_PROCEDURES_BLOCKED` / `_PARTIAL` | Missing data/fields/policies supplied — or the procedure deselected with rationale |
| `SELECTED_PROCEDURES_PENDING_RUN` | Every selected executable procedure has been run |
| `PROCEDURE_RESULTS_STALE` | Every run whose file or setting changed since (or whose rerun failed) has been rerun |
| `HIGH_RISK_RESPONSES_NOT_PERFORMED` | Every procedure linked to a high/significant risk actually ran on current inputs and tested something |
| `PROCEDURE_EXCLUSIONS_WITHOUT_RATIONALE` | Every deselection has a written rationale |
| `MISSTATEMENTS_UNRESOLVED` / `SUBSTANTIVE_ITEMS_UNRESOLVED` | Every misstatement candidate dispositioned |
| `FINDINGS_OPEN` | Every other finding (leads, refusals) disposed, none left undisposed or at follow-up |
| `WAIVERS_ABOVE_TRIVIAL_THRESHOLD` | No waiver exceeds the clearly-trivial threshold |
| `SCOPE_ITEMS_UNRESOLVED` | Every refusal resolved or accepted as a scope limitation |
| `DECISION_TRAIL_BROKEN` | The journal hash chain verifies (if it does not, stop and investigate) |
| `NO_DATA_WITHOUT_PARTNER_ASSERTION` | With no data loaded: a recorded reason that no data-dependent procedure applies |

## Standards referenced in this manual

AU-C 220 (engagement quality), 230 (documentation; assembly and
post-assembly changes), 240 (fraud considerations), 300/315/330 (planning,
risk, responses), 320 (materiality), 450 (evaluation of misstatements),
500 (audit evidence), 560 (subsequent events), 580 (written
representations), 700 (forming the opinion). PCAOB AS 1215 where retention
(7 years) and the assembly window differ: 45 days, amended to 14 days effective
December 15, 2026. Citations anchor further reading;
they are not a substitute for the standards themselves.

## The case, cross-referenced

| You are reading | Pair it with (in `case-studies/kestrel-valley-cycle/`) |
|---|---|
| Chapters 1–5 | The case description in `README.md`, and the files under `data/` |
| Chapters 6–7 | The answer key, `instructor/ANSWER-KEY.md`, only after your own work |
| Any chapter | `instructor/FINISH-LINE-REPORT.md`: where the Workbench matches the key, and the two lines it does not cover |
