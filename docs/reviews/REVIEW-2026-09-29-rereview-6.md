# Sixth independent re-review: all-measures total-row fix

**Date:** 2026-09-29  
**Commit:** `626db7b`  
**Method:** report only; no application or test code changed

## Scope

I re-ran the payroll, A/R, equity, and fixed-asset reproductions from
`REVIEW-2026-09-29-rereview-5.md`, inspected commit `626db7b`, and attacked
the revised rule with:

- fully tying and partly tying rows;
- zero-valued buckets;
- blank, malformed, and rate fields;
- subtotals followed by grand totals;
- values split between the subtotal and grand-total bases; and
- sparse real records whose key begins with `Total`.

I also ran the full suite, dependency check, Harborline verifier, and Kestrel
answer-key checker. I did not read `oceanview/`, `strategy/`, or `video/`.

## Findings

### RRRRRRR1 — Medium: a populated but unparsable measure is omitted and can let a bad total be reported as tying

At `packages/procedures-ap/src/procedures_ap/ingest.py:531`, `shown` includes a
populated measure only when `_measure()` successfully returns a number. A
populated value that cannot be parsed therefore disappears before the
all-populated-measures test at line 533.

**Reproduction:** normalize this `Payroll_register`:

```text
Employee ID,Pay Date,Hours,Gross,Net
E1,2025-06-15,80,2000,1600
E2,2025-06-15,80,1800,1440
TOTAL,,160,"3,8O0",3040
```

Observed result:

```text
loaded employee IDs ['E1', 'E2']
total_rows_not_tying []
reason: its net, hours equal the sums of the rows above it
```

The populated Gross value is neither tied nor named; it is treated as if it
were blank. With Gross as the only mapped measure, the row is quarantined but
the diagnostic says it “carries no amounts” and records an empty `gaps` list,
again failing to name the populated invalid field.

**Impact:** a corrupted amount or quantity on the client's stated total can
be represented as a cleanly tying total. Populated-but-unparsable measures
should make the total non-tying and identify the field and raw value in
`total_rows_not_tying`.

### RRRRRRR2 — Medium: a sparse real record whose key begins with “Total” is unconditionally removed

The new branch treats every row that matches `_looks_like_total()` and
`_only_label_and_amounts()` as a report total and never loads it, even when no
measure ties. This reverses the prior safeguard in which a non-tying label was
retained for review as a possible real record. It also contradicts the nearby
`_looks_like_total()` contract that a payee named `Total Cycling` is never a
total merely because of its name.

**Reproduction:** normalize a valid, sparse QuickBooks-shaped `AR_listing`:

```text
Customer,Balance
Total Cycling,100.00
```

Observed result:

```text
loaded customer numbers []
control_total 0.00
total_rows_set_aside 1
total_rows_not_tying [{source_row: 2,
  gaps: ['balance shows 100.00, rows above sum to 0']}]
```

**Impact:** a genuine customer, vendor, employee, account, or other key
beginning with `Total` can be removed from the audit population when its
export contains only the key and numeric measures. A non-tying label is
evidence against total classification, not proof of it. The importer needs an
unambiguous total marker or a review/quarantine state that does not silently
exclude the row from the population.

### RRRRRRR3 — Low: a non-tying grand total is diagnosed only against the post-subtotal basis

The acceptance test correctly tries both `since_total` and `all_loaded`, but
the gap construction at line 539 always compares against `since_total`.

**Reproduction:** after a valid departmental subtotal, add another employee
and then this grand total:

```text
GRAND TOTAL,,160,999,240
```

The detail's actual grand totals are Hours 160, Gross 300, and Net 240. Only
Gross is wrong. The diagnostic instead reports all three fields as gaps:

```text
gross shows 999, rows above sum to 200
net shows 240, rows above sum to 160
hours shows 160, rows above sum to 80
```

**Impact:** the row is safely quarantined, but the reviewer is told that two
correct grand-total fields are also wrong. For an explicit grand total, gaps
should be calculated against `all_loaded`; for an ambiguous label, the
diagnostic should identify the chosen basis or show both comparisons.

## Original finding result

### RRRRRR1 — Closed for all reported reproductions

- The payroll row whose Hours tied but Gross and Net did not was set aside;
  both monetary mismatches were named.
- The A/R row whose zero Current bucket tied but Balance and 31–60 did not was
  set aside; both mismatches were named.
- Equivalent equity and fixed-asset rows were set aside and every conflicting
  populated measure was named.
- A fully tying payroll total was accepted as a total and never loaded as an
  employee.
- A row mixing subtotal-basis values with grand-total-basis values did not
  pass the one-basis rule.
- Per-unit rates remained excluded from summation and control-total selection.

The central “every populated numeric measure on one basis” behavior is fixed
for parseable values and correctly prevents contradictory report totals from
entering the population.

## Confirmations

- Targeted historical review tests: **53 passed**.
- Full suite: **390 passed** in 23.40 seconds, matching the expected count.
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

Commit `626db7b` closes the exact RRRRRR1 reproduction and correctly prevents
parseable mixed-measure totals from being accepted on different bases. The
total-row remediation gate is not yet clean: malformed populated measures can
evade the rule, sparse real `Total ...` records can be removed, and grand-total
diagnostics can name the wrong fields. Fix and independently re-review
RRRRRRR1–RRRRRRR3 before treating population construction as complete or
pushing the rollout.
