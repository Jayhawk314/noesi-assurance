# Independent residual re-review — R1–R5

**Date:** 2026-09-27  
**Range reviewed:** `2672bba..778868c` (local, unpushed)  
**Disposition:** report only; no implementation changes made

## Scope

I independently inspected the fixes for R1–R5 described in
`REVIEW-2026-09-27-remediation.md`, re-ran each reported reproduction, and attacked the
specific boundary cases in the review brief. I also ran the complete Python suite,
`pip check`, and the Harborline instructor verifier.

I did not read or stage `oceanview/`, `strategy/`, or `video/`; did not inspect private
case content; and did not push, commit, amend history, or modify application code. The
private Oceanview lock result is therefore not independently checked here. Pre-existing
untracked files were left untouched.

## Findings

### RR1 — Medium: disabling a cycle preserves its policy and procedure decisions, which silently reactivate later

**Claim contradicted.** R4 says procedures and settings for a switched-off cycle are
refused. The new guards correctly prevent creating those decisions while a cycle is
off (`service.py:1043-1052`, `:1089-1096`), but the cycle-removal path only protects
risk links and recorded runs before assigning the new list (`service.py:1008-1042`). It
does not reject or clear existing policies and selections owned by the removed cycle.

**Reproduction.** In a fresh temporary `WorkbenchService` engagement:

```python
s.update_workflow(partner, eid, "cycles", {"cycles": ["inventory"]})
s.update_workflow(partner, eid, "policy",
                  {"name": "inventory_tolerable_misstatement", "value": "1000"})
s.update_workflow(partner, eid, "procedure_selection",
                  {"procedure_id": "inventory.count_listing_trace",
                   "selected": False, "rationale": "not applicable"})
s.update_workflow(partner, eid, "cycles", {"cycles": []})
print(s.workflow_document(eid)[0])
```

Observed:

```text
before {'cycles': ['inventory'],
        'policies': {'inventory_tolerable_misstatement': '1000'},
        'procedures': {'inventory.count_listing_trace':
                       {'rationale': 'not applicable', 'selected': False}}}
remove_result {'version': 4, 'section': 'cycles'}
after {'cycles': [],
       'policies': {'inventory_tolerable_misstatement': '1000'},
       'procedures': {'inventory.count_listing_trace':
                      {'rationale': 'not applicable', 'selected': False}}}
```

**Impact.** The signed workflow can carry an approved tolerable-misstatement setting
and selection judgment for a cycle it says is out of scope. If the cycle is later
re-enabled, those old decisions become effective again without being re-approved or
reconsidered for the new scope decision. A CPA could unknowingly reuse a stale sampling
threshold or stale exclusion rationale. Removing a cycle should either be refused while
cycle-owned decisions remain, or should explicitly retire those decisions with an
auditable event; silently retaining and later reactivating them is unsafe.

### RR2 — Low: the README's supported Python version contradicts all package metadata

**Claim contradicted.** R5 correctly changes `procedures-cycles` to Python `>=3.12`
(`packages/procedures-cycles/pyproject.toml:9`), matching every other package. However,
the development instructions still say “Requires Python >= 3.10” and explicitly claim
that the 3.12 floor was overstated (`README.md:70-72`).

**Reproduction.** Run:

```powershell
rg -n "requires-python" packages apps -g pyproject.toml
rg -n "Requires Python" README.md
```

Observed: all nine package/application manifests say `>=3.12`; the README says
`>= 3.10`.

**Impact.** A developer following the documented setup on Python 3.10 will be refused by
the packages' own metadata. This does not alter audit results, but it makes the supported
installation contract false. Either the packages need demonstrated 3.10 support and
aligned metadata, or the README must state 3.12.

## Confirmations

### R1 — Confirmed fixed, including per-run policy overrides

The original no-data reproduction now records an error run rather than a completed run:

```text
result {'status': 'error', 'summary': {'population': 0, 'exceptions': 0},
        'findings': 0,
        'error': "ap.payment_voucher_reference is blocked ...
                  missing ['Payments', 'Vouchers']"}
stored [('ap.payment_voucher_reference', 'error', ...)]
```

I searched for all persistent run writes: `run_procedure` is the only path calling
`uow.runs.record`; the other `run_job` call is an in-memory revision-impact reperformance.

I then ingested a valid two-row Payments file and attacked request-level overrides:

```text
override_good completed 0
override_empty error 0 ap.split_payment_review is partial ...
                       missing ['split_threshold']
persisted_statuses ['completed', 'error']
```

Thus the same effective policies drive coverage and execution: a valid per-run required
policy unlocks the run, while an empty override records an error rather than a false
completion.

### R2 — Confirmed fixed across identifier formatting and mixed evidence forms

The committed regression reproduces conflicting dated rows and an orphan inspection.
I additionally used payment `" 001 "` and inspection identifiers `"1.0"` and
`" 001 "`, with one conclusion row and one dated row. Canonicalization recognized them
as the same payment, refused the conflict, left it uninspected, and separately named the
orphan:

```text
keys [(('ap.unrecorded_liabilities_search', '1',
        'conflicting_inspections'), 'AMBIGUOUS'),
      (('ap.unrecorded_liabilities_search', '999',
        'inspection_without_payment'), 'ORPHAN'),
      (('ap.unrecorded_liabilities_search', '1',
        'selected_not_inspected'), 'TENSION')]
inspected_checks []
```

No conclusion or dated result from the conflicting pair entered the outcome counts.
The implementation conservatively refuses any duplicate inspection rows, even identical
ones; that is stricter than the stated conflicting-row rule but does not silently choose
evidence.

### R3 — Confirmed fixed for detail and summary shapes

An invoice-detail population containing a $5,000 invoice and a $300 credit memo for the
same customer produced no credit-balance finding. A summary population containing a
single net $300 customer credit produced the expected lead:

```text
detail []
summary_credit [(('ar.listing_tie', 'credit_balance', 'c2'), 'TENSION')]
```

Case and surrounding whitespace variants of the customer identifier aggregated to the
same customer.

### R4 — Partially confirmed

The committed test confirms that a cycle-only procedure selection and cycle-only policy
are refused while that cycle is off, and that the AP optional policy
`split_window_days` remains settable. The policy-owner map covers every current required
and optional cycle policy. Cycle removal remains incomplete as RR1 describes.

### R5 — Package alignment confirmed

The source manifest now declares `requires-python = ">=3.12"`, matching every other
package. The review environment is Python 3.12.9. I did not reinstall the editable
package because this is a report-only review; its already-installed metadata still
reflects the prior 3.10 declaration until reinstall. RR2 records the separate README
contradiction.

### Full suite and dependency check

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Observed:

```text
264 passed in 25.87s
No broken requirements found.
```

`git diff --check 2672bba..778868c` produced no errors.

### Harborline invariant

```powershell
.\.venv\Scripts\python.exe case-studies\harborline-marine\instructor\verify_run.py
```

Observed coverage after the approved policy:

```text
blocked=0, executable=11, not_selected=0, partial=0, total=11
```

All 11 runs completed and the verifier ended with:

```text
== Total findings: 52 ==
```

## Not checked

- The private Oceanview run or its three open lock items, because `oceanview/` was
  explicitly excluded.
- Browser UI behavior, npm builds, lesson rendering, or videos.
- A clean installation under Python 3.10 or 3.12; source metadata and the existing
  environment were inspected, and `pip check` was run, but no new environment was
  installed.
- The QuickBooks-shaped second case; it has not begun and should remain the next phase
  only after the residuals above are addressed or consciously accepted.

## Overall verdict

R1, R2, and R3 are fixed and survived the requested adversarial checks. R5 is fixed in
package metadata, and Harborline remains exactly 11 procedures and 52 findings. R4 is
only partially fixed: choices cannot be created while a cycle is off, but disabling a
cycle preserves and can later reactivate its old choices. The code remains suitable for
continued local development and the planned independent QuickBooks test case, but RR1
should be resolved before relying on cycle scope as a signed audit record or pushing the
rollout. RR2 should be corrected with the same small follow-up so the installation
contract is truthful. No lesson or video changes should begin on the strength of this
review alone.
