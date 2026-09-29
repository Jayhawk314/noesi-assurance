# Independent review: completion fixes (2026-09-28)

## Scope

Reviewed local commits `ef44399..3a0950a` on `main`, without pushing or
staging:

- `ef44399`: trial-balance statement-line mapping in the cycle executor,
  application service/API, and Scope UI.
- `a9d348a`: QuickBooks aging bucket aliases, four/five-column allowance
  recomputation, net-credit exclusion, and policy validation.
- `a20dfb6`: the `misstatement_likely_basis` policy and inference from
  statement-line columns.
- `3a0950a`: Kestrel's hand-prepared QuickBooks Journal seed.

I read `docs/INDEPENDENT-REVIEW.md`, inspected the four diffs and their new
tests, attacked the changed engines with independent inputs, inspected the
two supplied Kestrel Journal workbooks through `prep_journal`, and ran the
full Python suite. I did not change implementation code.

## Findings

### F1 — High: an all-blank but present 1–30 column shifts the allowance rates and can produce a wrongly clean result

**Contradicted claim:** `a9d348a` says the allowance takes one rate per column
in a four- or five-column aging. `listing_tie` decides whether the 1–30 column
exists with `any(r.get("days_1_30") is not None for r in listing)`. That tests
whether the column has a value, not whether the mapped column exists. A real
five-column aging whose 1–30 bucket happens to be blank throughout is therefore
treated as a four-column aging. The later rates move one bucket to the left.

**Reproduction:**

```python
from decimal import Decimal as D
from procedures_cycles.engines import execute_procedure

rows = [{
    "customer_number": "A", "balance": D("100"), "current": D("10"),
    "days_1_30": None,                 # column is present, all values blank
    "days_31_60": D("20"), "days_61_90": D("30"),
    "days_over_90": D("40"),
}]
tb = [
    {"account": "1100", "balance": D("100"), "side": "DR",
     "line": "receivables"},
    {"account": "1190", "balance": D("8"), "side": "CR",
     "line": "allowance"},
]
findings, stats = execute_procedure(
    "ar.listing_tie", {"AR_listing": rows, "Trial_balance": tb},
    {"ar_allowance_rates": "0.01,0.02,0.05,0.15"},
)
print(stats)
print([f.key for f in findings])
```

Observed material output:

```text
'aging_totals': {'current': '10.00', 'days_31_60': '20.00',
                 'days_61_90': '30.00', 'days_over_90': '40.00'},
'allowance_required': '8', 'allowance_recorded': '8', 'exceptions': 0
[]
```

With the five-column method and the example rates documented by the code
(`0.01,0.02,0.05,0.15,0.40`), the correct recomputation is
`10×.01 + 0×.02 + 20×.05 + 30×.15 + 40×.40 = 21.60`, rounded to 22. The
recorded allowance of 8 should therefore produce a difference of 14, but the
engine reports no exception.

**Audit-practice impact:** a CPA could accept an understated allowance and a
wrongly clean receivables-valuation result merely because one valid aging
bucket contains no balances. Column presence must be derived from the mapped
schema/keys, not from the presence of a nonblank amount.

### F2 — High: duplicate descriptions discard conflicting “Likely” evidence, yielding a wrong total with no ambiguity finding

**Contradicted claim:** `a20dfb6` says statement-line columns determine the
meaning of `Likely`, and otherwise the engine emits an `AMBIGUOUS` finding.
`uncorrected_misstatements` stores inferred bases in a dictionary keyed by
description. Descriptions are not declared unique. A later row with the same
description overwrites an earlier row, so conflicting row evidence disappears.

**Reproduction:**

```python
from decimal import Decimal as D
from procedures_cycles.engines import execute_procedure

rows = [
    {"description": "duplicate", "identified": D("100"),
     "likely": D("200"), "current_assets": D("-200")},  # total basis
    {"description": "duplicate", "identified": D("100"),
     "likely": D("200"), "current_assets": D("-300")},  # beyond basis
]
findings, stats = execute_procedure(
    "completion.uncorrected_misstatements", {"Misstatements": rows},
    {"materiality": "1000"},
)
print(stats)
print([f.key for f in findings])
```

Observed material output:

```text
'totals': {'identified': '200.00', 'likely': '600.00',
           'current_assets': '-500.00', ...},
'likely_basis': 'beyond_identified',
'likely_basis_source': 'statement-line columns', 'exceptions': 0
[]
```

The rows demonstrate two different bases. The result should not confidently
choose either basis; it should report the conflict/ambiguity. Instead, the
second row wins, the first row's `likely` is changed from 200 to 300, and the
engine reports a 600 likely total even though the statement-line effects total
500.

**Audit-practice impact:** repeated descriptions such as “projection” or
“cutoff” can silently alter the summary of uncorrected misstatements and the
remaining materiality displayed to the engagement team. This can distort an
opinion decision without any warning.

### F3 — Medium: the Kestrel journal key is not unique and merges two supplied deposits

**Contradicted claim:** `3a0950a` says date, type, Num, and name identify an
entry as the key does. In the supplied `Journal.xlsx`, two separate deposits
on 2026-06-30 have the same date and type and both have blank Num and name.
`prep_journal` assigns both the ID `2026-06-30 Deposit (no num)`. The journal
engine groups on that ID, so it treats two entries as one.

**Reproduction:** inspect transaction-start rows in the supplied workbook,
build the same key as `prep_journal`, and compare starts with distinct keys:

```text
Journal.xlsx transaction starts: 461
distinct prepared entry IDs:      460
duplicate ID: 2026-06-30 Deposit (no num)
```

The two distinct source rows are:

```text
06/30/2026  Deposit  (blank Num/name)  debit 12,650.00
06/30/2026  Deposit  (blank Num/name)  debit  4,318.75
```

The prepared output confirms the merge and even restarts the line number
inside the one ID:

```text
('1', '10100', '12650', '')
('2', '11000', '', '12650')
('1', '10100', '4318.75', '')
('2', '11000', '', '4318.75')
```

Running `je.journal_entry_testing` over the prepared current-year journal
reports `population: 460`, `entries: 460`, and `lines: 1006`, although the raw
report has 461 transaction starts.

**Audit-practice impact:** the demo understates the journal-entry population
and evaluates the two deposits as a single sampling/test unit. This particular
collision does not disturb the account-activity rollforward because all four
lines remain, but it can change per-entry fraud-risk tests and selection. A
stable occurrence discriminator is required when the visible QuickBooks fields
are not unique.

## Confirmations

- **Full suite confirmed:**

  ```text
  .venv/Scripts/python.exe -m pytest -q
  431 passed in 36.93s
  ```

- **Scoped unit tests confirmed:** with a workspace-local `--basetemp`, the
  three new test files passed `13 passed in 0.23s`. These confirm the covered
  cases: label/account override precedence and mapping propagation; populated
  four- and five-bucket aging layouts plus syntactically bad rate rejection;
  and unique-description total/beyond/unknown likely-basis cases. The temporary
  test directory was removed afterward.

- **Trial-balance mapping confirmed for the tested paths:** the independent
  and repository tests showed an account override wins over its label, source
  rows remain unchanged, and the mapped trial balance reaches the going-concern
  executor. I did not find a wrong or wrongly clean result in the scoped mapping
  behavior.

- **Named JE results confirmed:** on the prepared Kestrel current-year journal,
  entry 1047 produced `weekend_or_holiday`, `round_amount`, and
  `unauthorized_user`; entry 1066 produced `posted_after_period_end`.

- **Five July subsequent-event leads confirmed:** after applying the same
  normalized field names/date representation used by the service, the two
  prepared journal files produced seven reviewed July entries and five leads:
  check 4429, the 2026-07-01 transfer, the 2026-07-08 deposit, JE 1071, and the
  2026-07-14 deposit.

- **Kestrel collision is bounded:** the duplicate-ID scan found one collision
  in `Journal.xlsx` and none in `Journal_2026-07.xlsx`. This confirms the five
  July leads while contradicting the current-year population count.

## Not checked

- I did not run the complete Workbench demo seed or independently reproduce
  the claimed aggregate reduction from 697 to 296 findings.
- I did not build or interact with the React UI in a browser; the Scope panel
  was reviewed statically and through its service/API tests.
- I did not re-review unrelated earlier commits, production-readiness claims,
  security boundaries, locking/export, licensing, or case studies outside the
  four-commit scope.
- I did not review or modify unrelated pre-existing untracked files.

## Overall verdict

The four commits materially improve the Kestrel demonstration and their
ordinary covered cases pass, but the changed outputs are not yet reliable for
unattended audit use. The software may be used as a supervised teaching and
reperformance aid when a CPA validates source-population identity, aging
layout, and misstatement conventions. It must not be relied on to conclude A/R
valuation, aggregate uncorrected misstatements, or define the complete
journal-entry population until the three silent data-shape failures above are
addressed.
