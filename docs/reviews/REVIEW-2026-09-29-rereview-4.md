# Fourth independent re-review: RRRR1 fix

**Date:** 2026-09-29  
**Commit:** `7319f17`  
**Method:** report only; no application or test code changed

## Scope

I re-ran both RRRR1 reproductions from
`REVIEW-2026-09-29-rereview-3.md`, inspected commit `7319f17`, and attacked
total-row recognition with:

- textual and numeric-looking identifiers;
- normal and compact dates;
- amount and quantity columns;
- payroll hours;
- inventory quantity, unit cost, and extended cost; and
- reports that map one of several available amount fields.

I also ran the full suite, dependency check, Harborline verifier, and Kestrel
answer-key checker. I did not read `oceanview/`, `strategy/`, or `video/`.

## Findings

### RRRRR1 — Medium: payroll hours are a quantity but are not typed as one, so a total row loads as an employee

**Fix being re-reviewed:** a total row may carry fields typed as amounts or
quantities; populated identifiers, dates, and counterparties prevent total
classification.

The implementation defines the complete quantity set as
`{"quantity"}`. Payroll `hours` is also a quantity and payroll reports commonly
total it. Because it is not in `_QUANTITY_FIELDS`, an otherwise ordinary total
row fails the total-row shape check and is loaded as an employee.

**Reproduction:** normalize this `Payroll_register`:

```text
Employee ID,Pay Date,Gross,Tax Withheld,Deductions,Net,Hours
E1,2025-01-15,1000,100,100,800,80
E2,2025-01-15,1000,100,100,800,80
TOTAL,,2000,200,200,1600,160
```

Observed result:

```text
loaded employee IDs ['E1', 'E2', 'TOTAL']
total_rows_set_aside 0
control_total 4000.00
```

The gross control total is doubled instead of remaining 2000.00.

**Impact:** the normalized payroll population contains a fictitious `TOTAL`
employee and its aggregate dollars are counted again. Payroll tests and the
register-to-ledger comparison can therefore report incorrect populations and
differences. Quantity typing needs to cover every semantically quantitative
canonical field used by supported roles, not only inventory `quantity`.

### RRRRR2 — Medium: total detection selects the first amount field in the schema, not the applicable mapped total

`normalize_table()` chooses one `amount_field` by taking the first schema field
that belongs to `_AMOUNT_FIELDS`, before checking which amount fields are
actually mapped. For `Inventory_listing`, that field is `unit_cost`. A valuation
summary's total row normally totals extended `cost`, not unit cost.

**Reproduction:** normalize:

```text
Stock Number,Quantity,Unit Cost,Cost
A,1,10,10
B,2,20,40
TOTAL,3,,50
```

Observed result:

```text
loaded stock numbers ['A', 'B', 'TOTAL']
total_rows_set_aside 0
total_labelled_rows_kept [4]
control_total 30.00
```

The same issue is sharper when only `Quantity` and `Cost` are mapped: the
detector still selects the unmapped `unit_cost`, records no control total, and
loads the `TOTAL` row.

**Impact:** a valid inventory valuation total is loaded as an SKU and extended
cost can be doubled. Control totals also sum unit prices, which is not a valid
population control. For roles with multiple numeric measures, the report's
control-total measure must be explicit or selected from the mapped aggregate
field rather than schema order.

## Original-residual result

### RRRR1 — Closed for both reported reproductions

- A numeric-looking `target_entity=12345` now prevents total classification;
  the `Total Cycling` value-flow row is retained.
- A compact mapped date `20250102` now prevents total classification; the
  `Total Cycling` purchase-order row is retained.
- Textual counterparties, identifiers, and dates continue to prevent total
  classification.
- A sparse total carrying only its label and the recognized inventory
  `quantity` field passes the new shape rule when the selected control amount
  is present.

The new implementation resolves the exact identifier-versus-measure error but
does not yet provide a complete semantic type/control-total model, as RRRRR1
and RRRRR2 show.

## Confirmations

- Targeted historical review tests: **48 passed**.
- Full suite: **385 passed** in 23.61 seconds, matching the expected count.
- `pip check`: **No broken requirements found**.
- Harborline verifier: **52 findings**; its eleven-procedure result is
  unchanged.
- Kestrel key checker: **13/13 checks agree**.
- No application or test code was modified, committed, or pushed by this
  review.

## Not checked

- I did not run browser-based exploratory testing or performance tests.
- I did not inspect Oceanview material or the excluded `strategy/` and
  `video/` directories.
- I did not review or implement the draft-opinion work.

## Verdict

Commit `7319f17` closes the exact RRRR1 reproductions and correctly separates
numeric-looking identifiers from measures. The total-row remediation gate is
still not clean: payroll hours expose incomplete quantity typing, and
multi-measure roles expose an unsafe control-field selection rule. Fix and
independently re-review RRRRR1–RRRRR2 before treating population construction
as complete or pushing the rollout.
