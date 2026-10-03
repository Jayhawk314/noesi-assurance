# Independent depth review — 2 October 2026

Reviewer: Codex. Review only: no source fix, commit, or push.

## Scope and method

I reviewed the committed changes in:

- `8b79750`: declining-balance depreciation in `ppe.py`, including its
  contract, policy text, and unit tests.
- `f389bc8`: additions projection in `ppe.py`, including its contract,
  policy text, and unit tests.
- `d9ebf4b`: adjusted/add-back/trailing covenant measures in
  `debt_equity.py`, the covenant schema and contract, and the Kestrel key
  calculation in `generate_part2.py`.

I read `AGENT-WARNINGS.md` and `docs/ROADMAP.md` first. I did not read
Oceanview material. I used invented records, independent hand arithmetic,
the procedure executor, the full pytest suite, and the Kestrel finish-line
check. Classification below is one of **possible software bug**, **as
expected**, or **text**.

## Findings

### 1. Medium-high — a row containing only an asset ID is counted as completed vouching and can produce a zero projection

**Classification: possible software bug.** This may be a software bug.

`ppe.additions_vouching` requires only `asset_id` on the vouching table
(`contracts.py:411-412`). `additions_vouching` puts every such row in the
`vouched` dictionary (`ppe.py:313-315`), while amount and capitalization are
optional checks (`ppe.py:325-340`). `_project_additions` then includes the
book value of every ID in the sample (`ppe.py:393-395`), even when neither
an invoice amount nor a capitalization conclusion was supplied.

How confirmed: I supplied two period additions, 1,000 and 3,000, and two
`Additions_vouching` rows containing only their IDs. I set no vouch threshold
and set tolerable misstatement to 1. The result had no finding and reported:

```text
vouched=2, unvouched_value=0, coverage=1.0000
sample_value=4000.00, sample_misstatement=0.00
projected=0.00, likely_misstatement=0.00, exceptions=0
```

No invoice amount or capitalization evidence had actually been tested. A CPA
could read full coverage and a zero projection where the input proves only
that two asset IDs were typed. The procedure should refuse an evidentially
blank vouch row or exclude it from the sample and coverage.

### 2. Medium-high — a denominator reduced to zero by adjusting entries is silently skipped

**Classification: possible software bug.** This may be a software bug.

The unadjusted measure correctly refuses a zero denominator
(`debt_equity.py:208-213`). For the adjusted measure, `_measure` also returns
`None` on zero (`debt_equity.py:149-158`), but the caller stores
`adjusted_value=None` and performs no comparison or refusal
(`debt_equity.py:221-230`).

How confirmed: I used numerator 100, denominator credit 80, and an 80 debit
adjustment to the denominator account. By hand, the pre-adjustment ratio is
`100 / 80 = 1.2500`; after the entry the denominator is zero, so the adjusted
ratio is not measurable. The procedure returned no findings and:

```text
measured=[{value: 1.2500, adjusted_value: None}], exceptions=0
```

This is a silent skip precisely where the commit claims to measure the
covenant again after the entries. A user could miss that adjusted covenant
compliance cannot be established.

### 3. Medium — a breach cured by the adjustments still gets an unconditional breach finding

**Classification: possible software bug.** This may be a software bug and
its finding text overclaims the post-adjustment result.

The code emits `adjustments_change_compliance`, but then independently emits
`breached` whenever the *unadjusted* value fails (`debt_equity.py:228-247`).

How confirmed: numerator 100, denominator 80, minimum 1.50, followed by a 40
debit adjustment to the numerator. By hand, `100 / 80 = 1.2500` fails and
`140 / 80 = 1.7500` passes. The procedure emitted both:

```text
1.2500 before ... breaches; 1.7500 after ... meets it. The adjustments decide compliance
measured 1.2500 ... breached. Is there a waiver? If not, the debt may be due on demand
```

The second statement is unqualified and conflicts with the first statement
that the adjusted result decides compliance. At minimum, breach wording must
identify which basis it describes; if adjusted balances are the stated
compliance basis, the generic breach finding should follow the adjusted
result.

### 4. Medium — agreement add-backs can change compliance with no supporting note

**Classification: possible software bug.** The contract text says add-backs
are entered “with a note” (`contracts.py:449-451`), but the implementation
does not require one (`debt_equity.py:204-218`).

How confirmed: numerator 100, denominator 80, minimum 1.50, and a numerator
add-back of 30 with no note. By hand, the raw ratio is `1.2500` (breached) and
the add-back changes it to `130 / 80 = 1.6250` (met). The procedure returned
no finding and stored `note: ''`.

An unsupported typed amount can therefore reverse compliance while the
output presents it as the agreement's add-back. This contradicts the
contract and weakens the evidence trail.

### 5. Low — the TTM gate counts month labels, not a twelve-month duration

**Classification: possible software bug.** The six-month short-period case is
correctly refused, but the calculation at `debt_equity.py:174-177` ignores
the days.

How confirmed:

- 1 July–31 December produced a `not_measurable` finding saying six months:
  **as expected**.
- 31 January–1 December produced no finding and was labelled
  `trailing twelve months = the twelve-month period`: **possible software
  bug**. That interval is only 305 days, not a trailing twelve months.

This boundary is less common, but a nonstandard short reporting period can
be accepted as TTM merely because it touches twelve named calendar months.

## Independent arithmetic confirmations

### Declining balance (`8b79750`)

**As expected.** I used a 2025 calendar period and recomputed these without
using the implementation's totals:

- Full-month acquisition: 12,000 cost, five-year life, DDB, acquired 15 July:
  `12,000 × 2/5 × 6/12 = 2,400`.
- Full-month disposal: 10,000 cost, opening book value 6,000, disposed
  15 July: `6,000 × 2/5 × 6/12 = 1,200` (disposal month excluded).
- Full-month acquisition and disposal in the same year: 12,000, six years,
  acquired 15 March and disposed 15 September:
  `12,000 × 2/6 × 6/12 = 2,000`.
- Half-year acquisition: 12,000, six years: `12,000 × 2/6 × 1/2 = 2,000`.
- Half-year disposal with 6,000 opening book value:
  `6,000 × 2/6 × 1/2 = 1,000`.
- Half-year acquisition and disposal in the same year: one half-year,
  `12,000 × 2/6 × 1/2 = 2,000`.
- An asset at its 1,000 salvage value recomputed to zero under both
  conventions.

The executor returned no findings: full-month recomputed total 5,600 and
half-year total 5,000, matching those sums. The stated limitations—opening
book value inferred from the register and no switch to straight line—are
present in the contract. I found no wrong figure in these cases.

### Additions projection (`f389bc8`)

**As expected for complete vouch rows.** With a 10,000 threshold, the entire
below-threshold stratum was also the sample: 1,000 vouched to 900 and 3,000
vouched to 2,700. The sample and stratum were both 4,000; actual sample error
was `100 + 300 = 400`; ratio projection was
`400 × 4,000 / 4,000 = 400`. The executor returned those figures.

A sample cannot be larger than its own stratum in this implementation
because it is constructed as a subset of that stratum; equality is the
boundary case above.

With no threshold, all additions correctly formed one stratum. A 1,000
sample item vouched to 800 in a 4,000 population projected to
`200 × 4,000 / 1,000 = 800`, which the executor returned and compared with
tolerable misstatement. The representativeness limit is stated in the
contract. Finding 1 above applies when the supposed vouch rows carry no
actual test result.

### Covenants and Kestrel key (`d9ebf4b`)

**As expected in the remaining requested cases.** An adjusting entry solely
to account 999, outside numerator account 100 and denominator account 200,
left both the pre- and post-adjustment ratio at `100 / 80 = 1.2500`, with no
finding. A zero denominator before adjustments produced an explicit
`not_measurable` finding. The adjusted-zero case is Finding 2.

I independently summed Kestrel's current accounts from
`Trial_Balance_2026-06-30.xlsx`:

```text
188,700.95 + 46,500 + 500 - 25,000 + 261,733.70 - 4,200
+ 66,353.90 + 18,400 = 552,988.55

287,640.18 + 42,315 + 9,812.44 + 150,000 = 489,767.62
552,988.55 / 489,767.62 = 1.1291 (rounded)
```

The transfer AJE moves 25,000 between two current-asset accounts, so it has
no net ratio effect. The allowance AJE reduces current assets by 1,427.38 and
the inventory AJE by 171.00:

```text
552,988.55 - 1,427.38 - 171.00 = 551,390.17
551,390.17 / 489,767.62 = 1.1258 (rounded)
```

These figures match the generated `answer_key_part2.json` line. Both values
remain below 1.20, so both breach flags are correct.

## Regression checks

- `python -m pytest tests -q`: **546 passed in 69.63s**. The first sandboxed
  attempts were invalid because pytest could not create/inspect its temporary
  directory and yielded setup permission errors; I reran outside that
  restriction and report only the valid run as the code result.
- `finish_line_check.py`, with semicolon-separated `packages/*/src` and
  `apps/*` entries on `PYTHONPATH`: **174 of 176 match; 0 unexplained**. The
  two stated gaps were PO overrun and unrecorded liability. Its regenerated
  `FINISH-LINE-REPORT.md` had no tracked diff.

The green regressions do not exercise Findings 1–5.

## Not checked

- Browser/UI rendering of these results.
- Tax-table depreciation or declining-balance methods beyond the named
  DDB/150%/auditor-factor scope.
- Whether any particular loan agreement legally permits the invented
  add-backs; the test was of the software's evidence requirement and output.
- Private Oceanview data.

