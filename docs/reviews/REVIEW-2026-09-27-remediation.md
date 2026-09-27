# Re-review: remediation of REVIEW-2026-09-26 (F1–F5)

**Date:** 2026-09-27  
**Commit reviewed:** `a322b6a` (range `5368e40..a322b6a`), local and unpushed  
**Reviewer:** Claude (a separate session from the one that wrote the fixes)  
**Disposition:** report only; no code changed

**Independence disclosure.** The fixes were written in a Codex session; this reviewer did
not write them. This reviewer did write the original `procedures-cycles` package, so the
review is independent of the remediation, not of the underlying code. A reviewer who wrote
neither should look at the same range before any push.

## Method

For each finding: read the fix, re-run the original reproduction, then try to break it.
Also checked that payables-only behaviour is unchanged, and installed from scratch.

- `.venv\Scripts\python -m pytest -q` → **260 passed**
- `pip check` → no broken requirements
- Clean Python 3.12 venv, the README's editable-install command, `import
  assurance_application.service, procedures_cycles` → OK; `assurance-application`
  now requires `procedures-cycles`
- Harborline demo seeded and every executable procedure run → **11 executable, 52 findings** (unchanged)

## Verdict on F1–F5

| Finding | Fixed? | Evidence |
|---|---|---|
| F1 empty populations | **Yes for cycle procedures** | Every one of the 14 cycle procedures, run on empty required roles, returns an `empty_population` refusal; coverage treats a zero-row role as missing. See R1 for the payables side. |
| F2 scope bypass | **Yes for runs and risk links** | Out-of-scope `run_procedure` is refused; `link_risk_procedures` refuses out-of-scope ids; candidates come from in-scope contracts; removing a cycle is refused after its procedures ran or while risks link them. See R4. |
| F3 partial inspection of multi-line checks | **Yes** | A selected two-line check with one inspected line now reports `selected_not_inspected` for the other line. See R2. |
| F4 missing dependency | **Yes** | Declared in `assurance-application/pyproject.toml` and the README command; a clean install imports. |
| F5 A/R detail grain | **Yes for the three confirmation methods** | Balances are summed to customer before joining confirmations; population counts are customers. See R3. |

## Residual findings

### R1 — Medium: a payables procedure can still run, and be recorded as completed, while coverage says it is blocked

The F1 refusal was added only to the cycle executors. `run_procedure` does not check
coverage status, so a payables procedure can run directly on an engagement with no data:

```text
run ap.payment_voucher_reference on an engagement with no sources:
  status completed, findings 0, error -
  coverage for the same procedure: blocked
```

Readiness still blocks through coverage (`SELECTED_PROCEDURES_BLOCKED`), so this cannot
lock by itself. But the sealed run record states a test was completed on nothing, and the
packet includes every recorded run. This behaviour predates the cycle work. It is the same
class as F1, which is why it is reported here. Suggested fix: `run_procedure` refuses
(or records a refusal) when the procedure's compiled coverage status is not `executable`.

### R2 — Medium: duplicate or orphan inspection rows are resolved silently

In `ap.unrecorded_liabilities_search`, inspections are keyed by payment number in a
dictionary, so the last row wins:

```text
inspections: 900-1 dated 2026-12-20, 900-1 dated 2027-01-20, 999-9 (no such payment)
result: 900-1 judged on 2027-01-20 (improperly_included); the 2026-12-20 row ignored;
        the orphan 999-9 ignored; no finding for either
```

Two conflicting inspection results for one line are a contradiction in the auditor's own
evidence and should be refused, not resolved by row order. An inspection that matches no
payment is often a keying error that hides an uninspected line. Both should produce a
finding.

### R3 — Low: the credit-balance check misfires on invoice-detail A/R exports

F5 moved confirmation evaluation to customer grain, but `ar.listing_tie` still tests each
row for a credit balance. On an invoice-detail export, a credit memo line on a customer
whose total is a debit is flagged:

```text
C1: invoice 5,000 and credit memo -300 (net debit 4,700)
→ TENSION credit_balance · c1
```

Evaluate credit balances on the customer's net balance. The aging-footing check can stay
per row.

### R4 — Low: out-of-scope choices are stored

With no cycles in scope, `procedure_selection` for `inventory.count_listing_trace` and the
policy `inventory_tolerable_misstatement` are both accepted and saved. They do nothing
(coverage ignores them and runs are refused), but the engagement record then holds
decisions about procedures it does not include. Refuse them, or accept them only for
in-scope cycles.

Also noted: coverage now treats an inventory entry with no `rows` key as missing. Internal
callers always set `rows` (`inventory_from_tables`), and the golden coverage tests pass, so
nothing breaks today. But the meaning of an absent `rows` key changed; say so in the
`compile_coverage` docstring.

### R5 — Low: Python version declaration

`packages/procedures-cycles/pyproject.toml` says `requires-python >= 3.10`; every other
package says `>= 3.12`. Align it.

## Other checks

- `docs/CYCLES-STATUS-SUMMARY.md` names the private practice case but contains no case
  figures or content (scanned for amounts). It states that the fixes await re-review,
  which this document now provides.
- `ENGINE_VERSION` moved to `cycles-v2`, so sealed manifests distinguish pre- and
  post-fix runs. Payables runs keep their engine version.

## Verdict

F1–F5 are fixed as described, with the scope noted against each. None of R1–R5 is a
regression introduced by the remediation. R1 and R2 are the two worth fixing before any
push: R1 because a sealed record can claim a test that never ran, R2 because it silently
picks between contradictory audit evidence. After that, the QuickBooks-shaped second case
can proceed.

## Engineering follow-up (added after this re-review)

R1–R5 were addressed locally on 2026-09-27 by the same reviewer. This is therefore **not**
an independent check of these fixes, and someone who wrote neither the package nor the
fixes should re-review them before any push.

- **R1:** `run_procedure` compiles coverage on the same data and policies. When the
  procedure is not executable, the attempt is recorded as an **error run** with the
  reason, never as completed. This keeps the existing rule that attempts are journaled,
  not hidden (`test_error_runs_are_recorded_not_hidden`).
- **R2:** conflicting inspection rows for one payment line produce a
  `conflicting_inspections` refusal, and the line stays uninspected. An inspection naming
  a missing payment line produces `inspection_without_payment`.
- **R3:** credit balances are judged on each customer's net balance.
- **R4:** out-of-scope cycle procedure selections and cycle-only policies are refused.
  Policies shared with the payables contracts are unaffected.
- **R5:** `procedures-cycles` now requires Python >= 3.12.

Regression tests were added for R1–R4. Full suite: **264 passed**. Harborline is still
11 executable procedures and 52 findings.
