# The Noesi Assurance Manual

*A working textbook: the audit process and the workbench, taught together.*

Every chapter follows the same three-part pattern:

- **In practice** — what the auditing standards and normal professional
  practice require, and why. References are to the AICPA clarified standards
  (AU-C sections); PCAOB equivalents are noted where they differ in a way
  that matters.
- **In the workbench** — the concrete steps in the tool, which chair
  performs them, and what the tool records.
- **In Kestrel** — the running example: how the step plays out in the
  Kestrel Valley Cycle Supply case (`case-studies/kestrel-valley-cycle/`),
  a full-cycle, QuickBooks-shaped population with an independently computed
  answer key.

The point of pairing them: the workbench is not a substitute for the audit
process — it is the audit process, instrumented. Every gate in the tool
(a mapping you cannot approve yourself, a lock that refuses while a run is
unreviewed) exists because the profession requires it, and each chapter
names the requirement the gate implements.

## The chapters

| | Chapter | You will learn |
|---|---|---|
| 1 | [The engagement and the team](01-engagement-and-team.md) | Roles, separation of duties, chairs, why the journal exists |
| 2 | [Planning, materiality, and risk](02-planning-materiality-risk.md) | Materiality bases, performance materiality, clearly trivial, risk-to-procedure linkage |
| 3 | [Evidence and ingestion](03-evidence-and-ingestion.md) | PBC lists, evidence reliability, footing client reports, mappings as reviewed transformations, refusals; Excel and QuickBooks exports |
| 4 | [Coverage and scoping](04-coverage-and-scoping.md) | What "the data supports this procedure" honestly means; policies; deselection with rationale |
| 5 | [Executing procedures](05-executing-procedures.md) | Procedure families, assertion by assertion; tolerances; what silence means |
| 6 | [Findings, dispositions, and the SAD](06-findings-dispositions-sad.md) | Exception ≠ misstatement; dispositions; AU-C 450 evaluation |
| 7 | [Completion, lock, and the archive](07-completion-lock-archive.md) | Readiness gates, signing, the evidence packet, reopening under AU-C 230 |
| 8 | [Glossary and reference](08-glossary.md) | Product terms ↔ standards vocabulary; verdicts; blocker codes |

## Two ways to work through it

**Tool-first (about half a day).** Start the workbench with the case
pre-loaded and follow the chapters in order, doing each "In the workbench"
section as you read:

```
.venv\Scripts\noesi-workbench --demo
```

**Judgment-first (a course module).** Read chapters 1–2, then do the
source files described in
[`case-studies/kestrel-valley-cycle/README.md`](../../case-studies/kestrel-valley-cycle/README.md)
*before* opening the completed demo runs. Write down your expectations, then
continue with chapters 3–7 and compare them with the tool and, only afterward,
the instructor answer key. Forming your own expectation before the tool gives
you one is the better learning order.

## Companion courses

The Kestrel Learn course is being rebuilt as a separate companion with the
same lesson player and a module for each audit area. Until it is published,
this manual and the Workbench's Kestrel demo are the current full-cycle
course. The existing Studio lessons remain available as a legacy payables
course.

## What this manual assumes

Basic accounting literacy (you know what a voucher and a subledger are) and
nothing else. Where a standard is cited, the citation is the anchor for
further reading, not a substitute for reading it. The manual follows planning,
controls, journal entries, the principal transaction cycles, and completion.
The process it teaches — evidence, review, evaluation, documentation, and
professional judgment — is general; the automated procedures remain bounded
by the contracts and limitations shown in Coverage.

One honest limitation, stated up front: this workbench is a pilot. The
gap list between it and deployment in a real practice is tracked openly in
[`docs/PRODUCTION-READINESS.md`](../PRODUCTION-READINESS.md), and chapter 1
explains the parts of the pilot's trust model (chairs) you must understand
before relying on anything it produces.
