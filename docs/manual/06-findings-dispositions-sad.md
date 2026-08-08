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

**Above clearly-trivial, a disposition is a proposal.** Judging a
material-in-context exception — even to *clear* it — is a significant
judgment (AU-C 220), so the workbench treats it exactly like a run or a
mapping: the proposer's disposition awaits a second person's concurrence
(reviewer or partner chair, never the proposer — separation is enforced),
and changing the disposition voids any concurrence it had, because the
concurrence was with a different judgment. Below the threshold, one
person's judgment stands alone, for the same reason clearly-trivial items
stay off the SAD. The **Review** column on the findings table shows where
each judgment stands.

The **SAD** screen aggregates unadjusted items against materiality,
performance materiality, and clearly trivial, and concludes
immaterial/material. Undisposed findings, invalid waivers (waived above
the trivial threshold), and dispositions still awaiting concurrence are
completion blockers — the SAD refuses to conclude over an unreviewed
judgment. This is the gate that implements AU-C 450's "evaluate before
you conclude".

## In Harborline

Work the 52 findings. The instructive ones:

- **The subledger tie** (`CLASH`, variance 18,450): below clearly trivial?
  No — 21,000 is the line and this is under it, but is a control-account
  reconciliation difference *qualitatively* trivial at year end? Argue it
  both ways (Assignment 6), then disposition with the argument in the note.
- **The five self-approvals**: individually small, collectively evidence
  about the approval control during the supervisor vacancy. Their
  disposition notes should say what the control conclusion is, not just
  "cleared".
- **The cross-findings**: the three phantom-PO vouchers appear in both the
  reference test and the three-way match. If both land on the SAD at face
  value you have double-counted ~27,000 of exposure. Decide which
  procedure's finding carries the amount and clear the other *by
  reference* — the note on each should point at the other.
- **The value-flow ring** (`TENSION`, 48,500 returning through Meridian
  within days): the population is management-prepared and unverified. Write
  the disposition so it does not allege more than the evidence supports —
  Assignment 8's exact exercise.

Then set materiality (420,000) if you have not, and read the SAD's
conclusion. With the planted misstatements dispositioned honestly, the
aggregate stays under materiality — the interesting output is not the
conclusion but the discipline of the trail that supports it.
