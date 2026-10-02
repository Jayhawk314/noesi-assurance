# Chapter 6 — Findings, dispositions, and the summary of audit differences

## In practice

AU-C 450 governs what happens after testing: **accumulate** identified
misstatements (other than clearly trivial ones), **communicate** them, ask
management to correct, and **evaluate** whether what remains uncorrected is
material — individually or in aggregate, quantitatively or qualitatively.
The working document for this is the **summary of audit differences**
(SAD; also called the summary of uncorrected misstatements).

The chain of reasoning for every exception:

1. *What did the test actually observe?* (A payment with no bank clearing.)
2. *What could explain it?* (Timing, a data gap, an error, something worse.)
3. *What did the investigation conclude?* — and only now:
4. *Is there a misstatement, and how large?*

Skipping from 1 to 4 is the most common student error and a real-world
review comment: an exception quantifies an **exposure**; a misstatement is
a conclusion. Qualitative significance cuts the other way — an
unauthorized $500 payment is not "immaterial", it is evidence about
control integrity, whatever its size.

## In the workbench

Findings live on **Runs & Findings**, each carrying its receipt (verdict,
reason, evidence rows, limits). The verdict tells you what *kind* of claim
the engine is making:

| Verdict | The engine's claim | Your job |
|---|---|---|
| `CLASH` | two pieces of evidence contradict (amounts differ beyond tolerance; same person created and approved) | investigate; likely SAD candidate or control exception |
| `ORPHAN` | something expected is absent (no bank clearing, no voucher, no approver) | determine what absence means here — timing, completeness, or worse |
| `TENSION` | a pattern warrants review (a sub-threshold cluster, an identity twin, a value-flow ring) | treat as a lead; decide what further evidence settles it |

Every finding requires a **disposition** with a note:

- `cleared` — investigated, no misstatement; the note says why.
- `adjusted` — the client corrected it.
- `unadjusted` — a real difference the client will not correct; flows to
  the SAD.
- `waived` — below clearly trivial and not qualitatively significant. The
  tool checks the first half; *you* are asserting the second.
- `follow_up` — genuinely unresolved; blocks completion until resolved.

"Cleared" with an empty note is not documentation. Write the sentence a
reviewer will read.

Each disposition records who made it and when. Noesi asks for no
second-person concurrence; review of significant judgments is your firm's
process (AU-C 220).

The **SAD** screen aggregates unadjusted items against materiality,
performance materiality, and clearly trivial, and concludes
immaterial/material. Undisposed findings and invalid waivers (waived
above the trivial threshold) are completion blockers. This is the gate that implements AU-C 450's "evaluate before
you conclude".

## In Kestrel

Start with root causes, not the number of receipts:

- The aging-to-ledger difference is explained by a write-off entered after
  the aging was exported. Clear it only after obtaining the rerun or recording
  why alternative evidence resolves the population difference.
- The customer credit balance is a classification question, while the
  allowance shortfall is a valuation difference. They are not one item merely
  because both come from `ar.listing_tie`.
- Confirmation timing and customer-error differences are not client
  misstatements; the pricing and freight differences are. The sampling result
  reports what was identified and what was projected.
- Cash and inventory each contain exceptions that lead to proposed
  adjustments and others that remain uncorrected. Link cross-findings to one
  root cause so the SAD does not count the same exposure twice.

Kestrel's final uncorrected-misstatements schedule uses “Likely” for the amount
beyond identified on some rows. The run records how that convention was
determined and aggregates by statement line. Read that completion schedule
alongside the finding-based SAD: the current pilot still exposes both because
they answer related but not identical questions. The partner, not either
screen alone, concludes on materiality and the opinion.
