# The Noesi Assurance Manual

*A working textbook: the audit process and the workbench, taught together.*

Every chapter follows the same three-part pattern:

- **In practice** — what the auditing standards and normal professional
  practice require, and why. References are to the AICPA clarified standards
  (AU-C sections); PCAOB equivalents are noted where they differ in a way
  that matters.
- **In the workbench** — the concrete steps in the tool and what the tool
  records.
- **In Kestrel** — the running example: how the step plays out in the
  Kestrel Valley Cycle Supply case (`case-studies/kestrel-valley-cycle/`),
  a full-cycle, QuickBooks-shaped population with an independently computed
  answer key.

The point of pairing them: the workbench is not a substitute for the audit
process — it is the audit process, instrumented. Every gate in the tool
(a file whose totals do not foot, a readiness list that names every open
finding) exists because the profession requires it, and each chapter
names the requirement the gate implements.

## Three ways in

- **This manual** (chapters 1–8 below): the audit process and the workbench, step by step.
- **[How Noesi works](HOW-NOESI-WORKS.md)**: what it does, the maths it uses, what makes it different,
  its limits and possible errors, and what it adds to an audit.
- **[The Audit Code Atlas](https://htmlpreview.github.io/?https://github.com/Jayhawk314/noesi-assurance/blob/main/docs/manual/Noesi%20Audit%20Code%20Atlas.html)**
  (opens as a page): ten stops through a Kestrel audit, then every Learn lesson (13 modules, 9 fraud
  lessons), each with its route through the real source code.
  In the repository it is `docs/manual/Noesi Audit Code Atlas.html`; open it in a browser. Its code
  excerpts are refreshed from the source by `python docs/manual/refresh_atlas.py --write` (the ten stops)
  and `python docs/manual/build_atlas_lessons.py` (the lessons).

## The chapters

| | Chapter | You will learn |
|---|---|---|
| 1 | [The engagement and the team](01-engagement-and-team.md) | Roles and separation of duties in a firm, one user in Noesi, why the journal exists |
| 2 | [Planning, materiality, and risk](02-planning-materiality-risk.md) | Materiality bases, performance materiality, clearly trivial, risk-to-procedure linkage |
| 3 | [Evidence and ingestion](03-evidence-and-ingestion.md) | PBC lists, evidence reliability, footing client reports, mappings as confirmed transformations, refusals; Excel and QuickBooks exports |
| 4 | [Coverage and scoping](04-coverage-and-scoping.md) | What "the data supports this procedure" honestly means; policies; deselection with rationale |
| 5 | [Executing procedures](05-executing-procedures.md) | Procedure families, assertion by assertion; tolerances; what silence means |
| 6 | [Findings, dispositions, and the SAD](06-findings-dispositions-sad.md) | Exception ≠ misstatement; dispositions; AU-C 450 evaluation |
| 7 | [Completion, the record, and the archive](07-completion-lock-archive.md) | Readiness, the exported record and its offline check, what it does not prove |
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
explains why Noesi has one user and leaves review to the firm, which you
must understand before relying on anything it produces.
