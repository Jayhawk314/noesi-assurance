# Friction log — auditing a practice case with Noesi

A template for working an integrated practice case (one Noesi was not
built around) and recording, step by step, what the tool did. Copy it into
the case's own folder before you start; for a licensed case that folder is
git-ignored (e.g. `oceanview/`), because the filled-in log quotes case
material and answers.

**How to run each step:** do it by hand first (paper, Excel), then do the
same step in Noesi, then log one row. Doing it by hand first keeps the
learning honest: you know the answer before you see whether the tool finds it.

## Marks

| Mark | Meaning |
|---|---|
| **DID** | Noesi performed the step; you only reviewed its result |
| **HELPED** | You did the step, but Noesi did part of it (a match, a total, a lead) |
| **HAND** | Noesi could not help; done entirely by hand or in Excel |

Add **GOT IN THE WAY** in the notes whenever the tool slowed you down
(a refused import, a wrong column guess, a confusing screen), even on a DID
or HELPED row. Those are bugs, not gaps.

## Log

| Date | Assignment | Step | Audit area | Mark | What happened | Would need |
|---|---|---|---|---|---|---|
| | | | | | | |

- **Assignment / Step:** the case's own numbering, so you can find it again.
- **Audit area:** planning, risk assessment, payables, cash, revenue,
  receivables, inventory, journal entries, analytics, completion, reporting.
- **What happened:** one or two sentences; for DID/HELPED, whether Noesi's
  answer matched yours by hand.
- **Would need:** for HAND rows, the feature that would have turned it into
  HELPED or DID. Point at a row in
  [PRODUCTION-READINESS.md § 8](../PRODUCTION-READINESS.md#8-audit-coverage)
  when one fits; otherwise describe it.

## After every few assignments

Count the HAND rows by "Would need". The needs that keep coming back are
the build list, ranked by what the case actually required rather than by
guessing. Update the order in PRODUCTION-READINESS.md § 8 to match.
