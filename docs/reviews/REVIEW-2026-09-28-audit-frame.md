# Independent review: audit-frame expansion

**Date:** 2026-09-28  
**Range:** `94ecaa7^..e29331a` (17 commits, inclusive of `94ecaa7`)  
**Method:** report only; no application or test code changed

## Scope

I reviewed the explicit replace/add ingestion choice, total-row handling,
multi-section workbook refusal, the new audit-area contracts and executors,
deterministic load/run ordering, period start, unified-area classification,
completion procedures, tests, and the claims added to the audit-frame plan.

I attacked the paths most capable of giving an auditor a false clean result:
population construction, mapped columns containing blank values, completion
inputs, policy boundaries, and representation-letter recognition. I also ran
the full automated suite, the UI production build, the Harborline verifier,
and both Kestrel instructor programs.

## Findings

### F1 — High: the representation-letter procedure can report complete when representations were not actually obtained

**Contradicted claim:** `completion.representation_letter` says it checks that
every required representation was “obtained, signed, and dated as of the
report date.” The proposed opinion will rely on a missing representation as a
scope limitation.

There are four permissive paths in
`packages/procedures-cycles/src/procedures_cycles/completion.py`:

1. At line 191, every `obtained` value except five exact negative spellings is
   treated as affirmative. Blank, `pending`, and `unknown` therefore mean
   obtained.
2. At line 221, any nonblank `signed_by` value counts as a signer. Values such
   as `no` or `unsigned` pass.
3. `report_date` is not a required policy in the procedure contract. When it
   is absent, lines 205–207 put dating only in `stats.not_performed`; they add
   no finding and do not refuse the run.
4. Wording recognition uses `any(...)` keyword, so a sentence merely
   mentioning “financial statements” satisfies `fs_responsibility` even when
   it does not acknowledge management's responsibility.

**Reproduction:** from the repository root, call
`execute_procedure("completion.representation_letter", ...)` with one row for
each key in `REQUIRED_REPRESENTATIONS`, `obtained=""`, a valid date, and
`signed_by="CEO"`.

Observed output:

```text
findings 0 obtained 12 not_performed {}
```

Remove `report_date` from the policy dictionary and the result remains:

```text
findings 0 obtained 12 not_performed {'dating': 'policy report_date is not set'}
```

A lone row worded `The financial statements were delivered` was also accepted
as `fs_responsibility`; only the other eleven representations were reported
missing.

**Impact:** Noesi can omit a real AU-C 580 scope limitation from the findings
that the planned draft opinion consumes. A CPA could be shown no exception for
a blank/pending representation, an unsigned letter, an undated letter, or
wording that does not make the represented assertion.

### F2 — High: blank values in mapped required columns can produce clean procedure results

**Contradicted claim:** coverage and the procedure contracts present required
fields as support for execution, and the audit-frame rule says missing work is
named rather than silently treated as performed.

Coverage verifies that a mapped field exists, not that required values exist
on each accepted row. Several new executors then turn a blank amount into zero
or silently skip a blank date.

Two reproductions establish the audit impact:

- A `Trial_balance` with recognized lines for cash, current liabilities,
  equity, and sales, but `balance=None` on every row, produced **zero**
  going-concern findings. Its summary reported working capital, equity, and
  net income as `0.00`, with `exceptions: 0`.
- A $5,000 credit memo whose `memo_date` was blank, linked to a valid period
  invoice, produced **zero** findings. The summary reported a population of
  one, zero after-period memos, and `exceptions: 0`.

The first behavior follows `money(None) -> 0` through the trial-balance totals.
The second is explicit at
`packages/procedures-cycles/src/procedures_cycles/revenue.py:94`, where a
missing date is skipped with no refusal.

**Impact:** an incomplete export can look healthy. In particular, the planned
opinion could receive no going-concern indicator because the figures needed to
calculate it were blank, and revenue cutoff work can omit an untestable credit
memo without an open finding. This needs a shared rule for required row values,
not case-by-case reliance on column presence.

### F3 — Medium: the total-row heuristic can discard a real transaction

**Contradicted claim:** K1 is marked fixed because a report total is set aside
rather than loaded as a record.

`_looks_like_total` examines every text cell, not a designated label column.
If any cell begins with `Total`, and the row amount happens to equal either the
preceding subtotal or all prior loaded rows, normalization declares the row a
total and removes it.

**Reproduction:** normalize these two Payments rows using the ordinary proposed
and approved mapping:

```text
Payment Number,Payment Amount,Vendor
P1,100.00,Acme
P2,100.00,Total Cycling
```

Observed output:

```text
loaded payment numbers: ['P1']
total_rows_set_aside: 1
reject reason: a total row: its payment_amount equals the sum of the rows above it
```

The existing test uses `Total Cycling` with an amount that does not tie, so it
does not exercise this collision.

**Impact:** a legitimate transaction can be removed from the normalized audit
population. The rejection is visible, which limits the severity, but its
reason positively misidentifies the client record and downstream procedures
never test it.

### F4 — Medium: subsequent-events work can complete without a valid report-date boundary

**Contradicted claim:** `completion.subsequent_events` says it examines records
after year end “up to the report date.”

The contract requires `period_end` and `se_threshold`, but not `report_date`.
At `completion.py:31–32`, an absent report date means there is no upper bound.
There is also no validation that a supplied report date follows period end.

**Reproduction:** run the procedure with period end `2025-12-31`, threshold
`10000`, no report date, and a balanced $500 entry dated `2035-01-10`.

Observed output:

```text
findings 0
population 1
reviewed {'journal_entries': 1, 'payments': 0}
report_date None
exceptions 0
```

With `report_date=2025-12-15`, the procedure instead completes with a
`no_subsequent_records` finding describing an impossible window rather than
refusing the policy.

**Impact:** the run lifecycle can record subsequent-events work as completed
even though its required audit window was never defined. That completion state
is not suitable as an opinion input.

### F5 — Low: period-start validation accepts malformed values by truncating them

**Contradicted claim:** the partner records a date and Noesi refuses a start
that is not a date.

`service.py:1047–1050` parses only `raw[:10]`. Both
`2025-04-01garbage` and `2025-04-01T99:99:99` were accepted and stored as
`2025-04-01`.

**Impact:** the stored date itself is valid, so procedure arithmetic is not
corrupted, but the application silently accepts malformed input instead of
enforcing the documented `YYYY-MM-DD` boundary.

## Confirmations

The following claims were actively checked and held:

- `python -m pytest -q`: **334 passed** in 23.72 seconds.
- `python -m pip check`: **No broken requirements found**.
- `npm run build` in `apps/workbench-ui`: TypeScript and Vite production build
  completed successfully (37 modules).
- Harborline verifier: **11 procedures and 52 findings**.
- Kestrel answer-key checker: **13/13 checks agree**.
- Kestrel unchanged-engine runner still exposes its refused/partial imports
  and now refuses an implicit second Trial Balance load.
- The K3 tests confirm that a second dataset must say replace or add, added
  same-shape files are combined and recorded in the run manifest, replacement
  retires the old file from use, and different mapped field sets are refused.
- A valid period start is partner-only, reaches payroll/PPE/journal policies,
  can be cleared, and the 24-month and end-date bounds pass their tests.
- The unified classifier preserves the older payables and financial-statement
  placement rules and places the new procedure findings under their declared
  areas.
- Completion procedures are registered and have positive-path tests for
  subsequent-event leads, the stated financial warning signs, and a fully
  populated coded/worded representation fixture.
- Deterministic same-timestamp ordering, repeated-heading refusal, and the
  ordinary tying-total examples are covered by passing regression tests.

## Not checked

- I did not independently determine whether the twelve entries in
  `REQUIRED_REPRESENTATIONS` exhaust every engagement-specific representation
  required by current professional standards. This review establishes that
  even the list the program chose can be falsely marked obtained.
- I did not perform a browser-based exploratory pass through every new screen
  or operate a live HTTP server; the API/UI automated tests and production
  build were run.
- I did not benchmark large journal, payroll, or trial-balance populations.
- I did not review or use private Oceanview material, `strategy/`, or `video/`.
- The draft-opinion procedure does not exist in this range and was not
  reviewed.

## Overall verdict

The expansion is suitable for continued teaching-case and engineering work,
and the replace/add, period, area-placement, and thin audit-area architecture
are materially in place. It is not yet safe to build the draft opinion on the
completion outputs: F1, F2, and F4 allow missing evidence or missing boundaries
to look complete, while F3 can remove a real transaction from the tested
population. Remediate and independently re-review these findings before the
opinion layer. No work in this range should be represented as a production
audit system or system of record.
