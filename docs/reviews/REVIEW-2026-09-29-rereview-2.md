# Second independent re-review: RR1–RR4 fixes

**Date:** 2026-09-29  
**Commit:** `2327016`  
**Method:** report only; no application or test code changed

## Scope

I re-ran the RR1–RR4 reproductions from
`REVIEW-2026-09-29-rereview.md`, inspected commit `2327016`, and attacked:

- coded-only representation recognition, conflicting statuses, and signer
  parsing;
- every remaining `VALUE_OPTIONAL` exemption;
- total detection through the mapped key column across column orders, partial
  mappings, and roles whose key is a real name rather than an identifier; and
- strict report-date parsing.

I also ran the full suite, dependency check, Harborline verifier, and Kestrel
answer-key checker. I did not read `oceanview/`, `strategy/`, or `video/`.

## Findings

### RRR1 — High: signer phrases that explicitly mean “not signed” still count as signers

**Fix being re-reviewed:** RR1. Representations now count only when coded, and
boolean/placeholder signer values are meant not to satisfy the signature
requirement.

The coded-only change works: uncoded wording, including the prior negated
sentences, is suggested for human review but does not satisfy a representation.
Conflicting obtained/refused rows are also named. The remaining weakness is
`_signer()`: after its exact denylist, any value containing two alphabetic
characters is accepted as a person or title.

Each of these values was accepted as the signer, with no `unsigned` finding:

```text
refused
not signed by management
signature pending
CEO (unsigned)
not applicable
```

**Reproduction:** create a complete coded letter with each row obtained and
dated correctly, set every `signed_by` field to one of the values above, and
call `completion.representation_letter`.

Observed example:

```text
signed_by ['signature pending']
unsigned? False
```

**Impact:** a representation letter that expressly says its signature is
pending or absent can still appear signed. Because the planned opinion will
consume this result, Noesi could omit a representation-letter scope
limitation. A signer should be an affirmative reviewed identity/title field,
not arbitrary free text accepted by exclusion.

### RRR2 — Medium: a post-period invoice with no shipping date still produces no cutoff refusal

**Fix being re-reviewed:** RR2 and the remaining `VALUE_OPTIONAL` exemptions.

The fixes correctly exclude confirmations with no confirmed value, and a
pre-period-end invoice with a shipping document but no shipping date now gets
`no_ship_date`. However, `rev.sales_cutoff` only creates that refusal when the
invoice date is on or before period end.

For this row:

```text
invoice_number I1
invoice_date   2026-01-02
amount         4000
ship_date      blank
shipping_document BOL-9
```

with period end `2025-12-31`, the observed result was:

```text
findings []
invoices_without_ship_date 1
exceptions 0
```

A post-period invoice needs its shipping date to determine whether goods were
shipped before period end and revenue was understated. The invoice's date does
not make cutoff testable.

I also exercised the other exemptions. Missing estimate inputs are refused;
an inspection without a liability date needs an accepted recorded conclusion;
accrual and PPE items missing inputs are named in `not_recomputed`; and a blank
confirmation classification is accepted only when the confirmed value itself
supports the result. No other residual was reproduced.

**Impact:** an untestable possible understatement is omitted from the open
findings even though the summary counts the missing date. The run can therefore
appear to have no cutoff exception requiring disposition.

### RRR3 — Medium: mapped key columns that contain names can still delete a real row as a total

**Fix being re-reviewed:** RR3. The total label is now read from the mapped key
column, which fixes Payments in either column order.

Not every role's first required key is an identifier. `Value_flows` uses
`source_entity`. A real entity whose name begins with `Total ` is therefore
still treated as a total label when its amount happens to tie the preceding
rows.

**Reproduction:** normalize:

```text
Source Entity,Target Entity,Amount,Date
Acme,Bank,100.00,2025-01-01
Total Cycling,Bank,100.00,2025-01-02
```

Observed result:

```text
loaded rows [('Acme', 'Bank')]
total_rows_set_aside 1
reject reason: a total row: its amount equals the sum of the rows above it
```

The same failure occurs in a partially mapped Purchase Orders export when the
primary PO number is unmapped and `vendor_number` becomes the selected required
key.

**Impact:** a legitimate value-flow transaction can be removed from the audit
population. The removal is visible as a rejection, but it is incorrectly
described and downstream procedures never test it. “Mapped key” is not enough;
the field also needs to be one in which a total label is structurally valid,
or total rows need a stronger shape/recipe rule.

## Prior-residual results

### RR1 — Partially fixed; RRR1 remains

- Uncoded wording never satisfies a representation.
- Negated uncoded wording is only suggested for review.
- Conflicting obtained/refused entries produce a finding.
- The exact prior signer values (`false`, `true`, `0`, `yes`, `X`) are refused.
- Longer phrases explicitly indicating no signature still pass.

### RR2 — Partially fixed; RRR2 remains

- A blank confirmation value is no longer exempt and is excluded with an
  incomplete-row refusal under all three confirmation methods.
- A shipping document without a date is refused for invoices dated in the
  audited period.
- The same missing date remains clean for invoices dated after period end.

### RR3 — Partially fixed; RRR3 remains

- Payments are no longer affected by whether Vendor or Payment Number appears
  first in the source file.
- Roles whose mapped key is itself a name can still lose a real `Total ...`
  record.

### RR4 — Closed

Missing, pre-period-end, and malformed report dates are refused. The original
`2026-02-15garbage`, an appended timestamp, and free-form text no longer pass
through truncation.

## Confirmations

- Targeted remediation set: **57 passed**.
- Full suite: **373 passed** in 22.45 seconds, matching the expected count.
- `pip check`: **No broken requirements found**.
- Harborline verifier: **52 findings**; its eleven-procedure result is
  unchanged.
- Kestrel key checker: **13/13 checks agree**.
- No application or test code was modified, committed, or pushed by this
  review.

## Not checked

- I did not independently validate the substantive completeness of the AU-C
  representation list; I tested the program's enforcement of its declared
  coded list.
- I did not run browser-based exploratory testing or performance tests.
- I did not inspect Oceanview material or the excluded `strategy/` and
  `video/` directories.
- I did not review or implement the draft-opinion work.

## Verdict

Commit `2327016` closes RR4 and materially strengthens RR1–RR3, but the
remediation gate is not clean. RRR1 can still make an unsigned representation
letter look signed, RRR2 can omit an untestable revenue-cutoff item, and RRR3
can still remove a real transaction from the normalized population. Remediate
and independently re-review these three residuals before the draft-opinion
layer relies on the completion results.
