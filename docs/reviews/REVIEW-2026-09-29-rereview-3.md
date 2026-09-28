# Third independent re-review: RRR1–RRR3 fixes

**Date:** 2026-09-29  
**Commit:** `2dcb621`  
**Method:** report only; no application or test code changed

## Scope

I re-ran the RRR1–RRR3 reproductions from
`REVIEW-2026-09-29-rereview-2.md`, inspected commit `2dcb621`, and attacked:

- required-signer policy parsing and exact matching, including missing,
  placeholder, reordered, case-varied, and extra entries;
- missing shipping dates for invoices on both sides of period end, with and
  without a shipping-document number; and
- total-row shape recognition with textual and numeric-looking identifiers,
  dates, counterparties, and amounts.

I also ran the full suite, dependency check, Harborline verifier, and Kestrel
answer-key checker. I did not read `oceanview/`, `strategy/`, or `video/`.

## Finding

### RRRR1 — Medium: numeric-looking identifiers are treated as total-row numbers, so a real row can still be removed

**Fix being re-reviewed:** RRR3. A row whose mapped key begins with `Total` is
supposed to be a total only when every mapped field other than its label and
numeric totals is blank.

`_only_label_and_amounts()` permits a populated mapped field when either its
canonical field is an amount field **or `parse_decimal(value)` succeeds**.
The second condition applies to every mapped field, including counterparties,
identifiers, and dates. A numeric-looking identifier is therefore mistaken for
an aggregatable number. This contradicts the helper's own row-shape rule: “no
counterparty, no second identifier.”

**Reproduction:** normalize this ordinary `Value_flows` input:

```text
Source Entity,Target Entity,Amount,Date
Acme,Bank,100.00,2025-01-01
Total Cycling,12345,100.00,
```

The second row has a populated second identifier (`target_entity=12345`) and
is therefore a transaction, not a total. Observed result:

```text
loaded rows [('Acme', 'Bank')]
total_rows_set_aside 1
reject reason: a total row: its amount equals the sum of the rows above it
```

The same failure was reproduced with a partially mapped Purchase Orders row
whose mapped date was the numeric-looking `20250102`.

**Impact:** a legitimate transaction can still be removed from the normalized
audit population. Numeric-looking account, vendor, employee, entity, reference,
or compact-date values are common in accounting exports; their lexical form
does not turn them into total measures. The exception should be based on the
canonical field's semantic type (amount/quantity fields explicitly allowed),
not whether arbitrary text parses as a decimal.

## Prior-residual results

### RRR1 — Closed

- `rep_signers` is required by coverage and at execution.
- Every required signer must appear as a separate exact normalized entry.
- Missing one of `CEO, CFO` produces an `unsigned` finding naming the missing
  signer.
- The prior phrases (`refused`, `not signed by management`, `signature
  pending`, `CEO (unsigned)`, and `not applicable`) do not satisfy a policy
  requiring `CEO`.
- Case, whitespace, comma, semicolon, `and`, and ampersand normalization did
  not permit substring matches; `CEO (unsigned)` did not match `CEO`.
- Coded-only representation recognition and conflicting-status detection
  continue to hold.

### RRR2 — Closed

Every tested invoice with a blank shipping date now creates a finding:

- in-period with no document: `no_shipping_evidence`;
- in-period with a document: `no_ship_date`;
- post-period with no document: `no_ship_date`; and
- post-period with a document: `no_ship_date`.

Each run reported one exception. The post-period understatement path from the
prior review is no longer clean.

### RRR3 — Partially fixed; RRRR1 remains

- The original `Total Cycling` value-flow row with a textual target entity and
  date is retained.
- The partially mapped Purchase Orders reproduction with a normal date is
  retained.
- A genuine sparse report total is still set aside.
- A populated nonnumeric mapped field prevents total classification.
- A populated numeric-looking identifier or compact date does not prevent it.

## Confirmations

- Targeted remediation set: **57 passed**.
- Full suite: **383 passed** in 23.42 seconds, matching the expected count.
- `pip check`: **No broken requirements found**.
- Harborline verifier: **52 findings**; the eleven-procedure result is
  unchanged.
- Kestrel key checker: **13/13 checks agree**.
- No application or test code was modified, committed, or pushed by this
  review.

## Not checked

- I did not independently validate the substantive completeness of the AU-C
  representation list.
- I did not run browser-based exploratory testing or performance tests.
- I did not inspect Oceanview material or the excluded `strategy/` and
  `video/` directories.
- I did not review or implement the draft-opinion work.

## Verdict

Commit `2dcb621` closes the signer and revenue-cutoff residuals and materially
narrows the total-row problem. The gate is not fully clean because RRRR1 can
still remove a real transaction based on the textual format of a nonamount
identifier. Fix and independently re-review that population-integrity boundary
before treating the remediation series as complete or pushing the rollout.
