# Fifth independent re-review: RRRRR1–RRRRR2 fixes

**Date:** 2026-09-29  
**Commit:** `295a53b`  
**Method:** report only; no application or test code changed

## Scope

I re-ran both reproductions from
`REVIEW-2026-09-29-rereview-4.md`, inspected commit `295a53b`, and attacked
total-row recognition across payroll, inventory, receivables, equity, and
fixed assets. The attacks varied which mapped amount or quantity tied, made
other mapped measures disagree, used zero-valued aging buckets, and attempted
to make a per-unit rate act as the tie or control field.

I also ran the full suite, dependency check, Harborline verifier, and Kestrel
answer-key checker. I did not read `oceanview/`, `strategy/`, or `video/`.

## Finding

### RRRRRR1 — Medium: one tying measure silently overrides contradictory totals in every other populated measure

At `packages/procedures-ap/src/procedures_ap/ingest.py:526`, total recognition
uses `next(...)`: a labelled row is set aside as soon as **any one** mapped
measure equals its running or grand-total sum. The implementation does not
check whether the row's other populated measures also tie. It then reports
only the successful field and silently discards the contradictory values.

**Payroll reproduction:** normalize this `Payroll_register`:

```text
Employee ID,Pay Date,Hours,Gross,Net
E1,2025-06-15,80,2000,1600
E2,2025-06-15,80,1800,1440
TOTAL,,160,9999,9999
```

Observed result:

```text
loaded employee IDs ['E1', 'E2']
total_rows_set_aside 1
control_total 3800.00
reason: its hours equals the sum of the rows above it
```

The hours total is valid, but the stated gross and net totals are both false.
Neither discrepancy is reported.

**Cross-role reproduction:** an `AR_listing` with detail balances 100 and 200,
zero in each detail row's Current bucket, and this final row behaves the same
way:

```text
Customer Number,Balance,Current,31-60
TOTAL,999,0,999
```

The row is set aside because Current ties at zero; the contradictory Balance
and 31–60 totals disappear. Equivalent attacks succeeded when Beginning tied
but the other measures disagreed in `Equity_rollforward`, and when Cost tied
but the remaining amount columns disagreed in `Fixed_assets`.

**Impact:** detail rows are not doubled, but Noesi can silently accept a
damaged or internally inconsistent source report and manufacture its control
total from detail rows without naming the report's contradictory stated
totals. That weakens the ingestion evidence and can make downstream work look
reconciled when the client's report itself does not reconcile. A total row
with multiple populated measures should be accepted only when every
aggregatable populated measure ties, or it should be quarantined with an
explicit mismatch diagnostic for each contradictory field. A zero tie should
not mask nonzero contradictions.

## Original-residual results

### RRRRR1 — Closed for the reported reproduction

`hours` is now treated as a quantity. The payroll total carrying hours, gross,
and net is set aside rather than loaded as a `TOTAL` employee, and the gross
control remains 3800.00.

### RRRRR2 — Closed for the reported reproduction

The inventory total can tie on quantity or extended cost even though unit cost
appears earlier in the schema. The `TOTAL` row is set aside and the control
total is the 150.00 extended cost, not the sum of unit prices.

The rate exclusion also held under attack: an inventory row whose unit cost
alone equalled the sum of preceding unit costs was retained and named as a
total-labelled row that did not tie. Unit cost did not trigger total
recognition and was not selected as the control total.

## Confirmations

- Targeted historical review tests: **50 passed**.
- Full suite: **387 passed** in 24.84 seconds, matching the expected count.
- `pip check`: **No broken requirements found**.
- Harborline verifier: **52 findings** across its eleven procedures.
- Kestrel key checker: **13/13 checks agree**.
- No application or test code was modified, committed, or pushed by this
  review.

## Not checked

- I did not run browser-based exploratory testing or performance tests.
- I did not inspect Oceanview material or the excluded `strategy/` and
  `video/` directories.
- I did not review or implement the draft-opinion work.

## Verdict

Commit `295a53b` closes both exact RRRRR1–RRRRR2 reproductions and correctly
keeps rates out of summation and control-total selection. The remediation gate
is not clean because multi-measure total rows can still hide contradictory
source totals. Fix and independently re-review RRRRRR1 before treating
population construction as complete or pushing the rollout.
