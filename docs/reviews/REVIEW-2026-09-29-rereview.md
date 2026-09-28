# Independent re-review: audit-frame F1–F5 fixes

**Date:** 2026-09-29  
**Range:** `3a0bb22..cd75810`  
**Method:** report only; no application or test code changed

## Scope

I re-ran the original F1–F5 reproductions from
`REVIEW-2026-09-28-audit-frame.md`, inspected the five remediation commits,
and attacked the boundaries around representation wording, affirmation and
signature values, every `VALUE_OPTIONAL` exemption, total-row column order,
report-date parsing, and period-start parsing.

I also ran the full suite, dependency check, Harborline verifier, and Kestrel
answer-key checker. I did not read `oceanview/`, `strategy/`, or `video/`.

## Findings

### RR1 — High: negated representations and `signed_by=false` still satisfy the representation-letter procedure

**Fix being re-reviewed:** F1, which requires affirmative representations,
a real signer, and a valid report date before the result can feed the planned
opinion.

The original F1 examples are fixed, but the new wording recognizer tests only
whether required substrings occur. It does not distinguish an affirmation from
its negation. These uncoded rows were each recognized as the named required
representation and produced no `not_obtained` finding:

```text
Management is not responsible for the financial statements
Management disclaims responsibility for internal control
The accounting estimates are not reasonable
Related parties were not disclosed
Subsequent events were not adjusted or disclosed
```

The signature denylist has the same open-ended problem. Setting every row's
`signed_by` value to `false` produced:

```text
unsigned? False
signed_by ['false']
```

A duplicate `fraud` representation with one row marked `yes` and another
marked `refused` also retained `obtained`; the conflict was not named.

**Reproduction:** construct all other required rows by code, omit the target
code, append one of the sentences above with `obtained=yes`, the report date,
and `signed_by=CEO`, then call:

```python
execute_procedure(
    "completion.representation_letter",
    {"Representations": rows},
    {"period_end": "2025-12-31", "report_date": "2026-02-15"},
)
```

For each of the five sentences, the target key was absent from the findings
and `unrecognized_rows` was empty.

**Impact:** wording that expressly denies a required representation can be
treated as providing it, and a machine-style false value can be treated as a
signature. The planned opinion could therefore miss an AU-C 580 scope
limitation. Free-text recognition needs a conservative refusal boundary (or
reviewed codes), not an expanding collection of negative words.

### RR2 — Medium: two `VALUE_OPTIONAL` paths still allow missing evidence to produce an agree/clean result

**Fix being re-reviewed:** F2, which says blank required values are named and
not tested rather than read as zero or silently skipped.

I exercised every entry in `VALUE_OPTIONAL`. The estimate, unrecorded-liability,
accrual, and PPE paths did name the gap either as a finding or in the
`not_recomputed` summary. Two exemptions remain unsafe:

1. `rev.sales_cutoff` exempts `ship_date`. An invoice dated before period end,
   with `ship_date=None` and a nonblank shipping-document number, returned no
   finding. The summary said one invoice lacked a ship date but reported
   `exceptions: 0`. A document number does not establish which side of period
   end shipment occurred on.
2. All three confirmation methods exempt `confirmed_value` and
   `classification`. A confirmation with `confirmed_value=None` and
   `classification=timing` was included as a zero misstatement. Nonstatistical,
   MUS, and difference estimation each emitted an `AGREE` evaluation and no
   unclassified-response refusal.

Observed sales-cutoff output:

```text
findings []
invoices_without_ship_date 1
exceptions 0
```

Observed confirmation result under each method:

```text
unclassified? False
confirmations 2
evaluation AGREE
```

**Impact:** revenue cutoff can be recorded with no open finding when its date
evidence is missing, and an unquantified confirmation difference can enter a
projection as zero. Both can understate audit exceptions. The exemptions need
conditions: a field is optional only when the alternate evidence needed by
that specific row is present and sufficient.

### RR3 — Medium: changing column order reopens the false total-row deletion

**Fix being re-reviewed:** F3, which now examines the first nonblank cell
rather than every cell.

The original reproduction is fixed when `Payment Number` is the first column.
The same two valid transactions fail when an export puts Vendor first:

```text
Vendor,Payment Number,Payment Amount
Acme,P1,100.00
Total Cycling,P2,100.00
```

Observed normalization:

```text
loaded payment numbers ['P1']
total_rows_set_aside 1
```

**Impact:** ordinary source-column order determines whether a legitimate
transaction is removed from the tested population. The total label needs to
be tied to a mapped identifier/label field or a stronger row-shape rule, not
physical first-nonblank position.

### RR4 — Low: malformed report dates are still truncated and accepted

**Fix being re-reviewed:** F4, requiring a valid report-date boundary.

Missing report dates and dates on or before period end are now refused, and
coverage requires the policy. However, `report_window()` calls the shared
`day()` helper, which parses only the first ten characters.

With `report_date="2026-02-15garbage"`, the subsequent-events procedure ran
and reported:

```text
report_date 2026-02-15
```

**Impact:** the boundary used in arithmetic is a valid date, so this is not a
calculation error, but it contradicts the new valid-boundary rule and repeats
the parsing weakness that F5 closed for period start.

## Original-finding results

### F1 — Partially fixed; residual RR1 remains

- Blank, `pending`, and `unknown` no longer count as obtained.
- `no`, `unsigned`, `n/a`, and `TBD` no longer count as signers.
- A missing or pre-period-end report date is refused.
- The original weak sentence, `The financial statements were delivered`, is
  no longer accepted.
- Negated wording and uncovered false-style signer values still pass.

### F2 — Partially fixed; residual RR2 remains

- The original blank trial-balance balances are excluded and produce an
  incomplete-row refusal.
- The original blank credit-memo date is excluded and named.
- Complete rows continue to run beside excluded rows.
- Conditional exemptions for sales cutoff and confirmations remain too broad.

### F3 — Partially fixed; residual RR3 remains

- The original `Payment Number, Payment Amount, Vendor` reproduction now keeps
  `Total Cycling`.
- Reordering Vendor to the first column causes the same real row to be removed.

### F4 — Partially fixed; residual RR4 remains

- Missing report date is refused.
- A report date before period end is refused.
- Records after a valid report date are outside the tested window.
- Coverage reports a missing report date as partial.
- Trailing garbage is still accepted by truncation.

### F5 — Closed

Both original malformed starts, `2025-04-01garbage` and
`2025-04-01T99:99:99`, are refused. Valid `YYYY-MM-DD`, end-date ordering, the
24-month bound, partner authorization, clearing, and procedure propagation
continue to pass.

## Confirmations

- Targeted remediation tests: **34 passed**.
- Full suite: **353 passed** in 24.48 seconds, matching the expected count.
- `pip check`: **No broken requirements found**.
- Harborline verifier: **52 findings** (and the run remains eleven procedures).
- Kestrel key check: **13/13 checks agree**.
- No tracked or untracked source file was modified by the review.

## Not checked

- I did not independently validate the substantive completeness of the AU-C
  representation list; I tested whether the program faithfully recognizes the
  list it declares.
- I did not run browser-based exploratory UI testing or performance tests.
- I did not inspect private Oceanview material or the excluded `strategy/` and
  `video/` directories.
- I did not review or implement the draft-opinion work.

## Verdict

The five commits improve every original reproduction, and F5 is closed, but
the remediation gate is not clean. RR1 can still suppress a representation
scope limitation, RR2 can still treat missing cutoff/confirmation evidence as
clean, and RR3 can still remove a real transaction based solely on export
column order. Fix and independently re-review RR1–RR3 before building the
draft opinion; RR4 should be closed in the same remediation pass.
