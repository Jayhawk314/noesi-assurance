# Phase 2: deliberate divergences from prototype behavior

The port is shadow-tested against the Phase 0 golden bundles. Everything not
listed here must match the prototype exactly (for engine receipts,
bit-for-bit including `receipt_id`). Each divergence is intentional,
justified by the architecture assessment, and normalized explicitly in the
shadow tests.

## D1 — Compiling coverage never marks a procedure "completed"

Prototype: `compile_coverage` set `execution_status: "completed"` on any row
whose required fields were present (the P1 "two run models" defect).
v2: compile always emits `"not_run"`; only the run lifecycle
(`planned → … → completed → reviewed → approved` in
`assurance_domain.lifecycle`) can produce completion. The evidence-lifecycle
overlay's `"ready_to_run"` semantics are preserved unchanged.

Shadow normalization: golden `"completed"` → `"not_run"` before diffing.

## D2 — `forensic.closed_value_flow` is deferred, refused explicitly

Prototype: executed via the vendored KOMPOSOS structural graph
(`sys.path`-dependent). v2 refuses with a clear message until the structural
code ships as an explicitly owned, benchmarked adapter package
(`structural-adapters`). Refusal, not silent absence: the contract remains
in the registry and compiles in coverage.

## D3 — Decimal arithmetic with a float serialization boundary

Prototype: binary floats end to end (P1 defect). v2: all monetary
arithmetic is `Decimal` (`assurance_domain.money`); floats are produced only
by `fnum()` when writing receipts/reasons, keeping v2 receipts diffable
against float-era goldens. Mixed-currency aggregation raises
`CurrencyMismatchError` instead of silently summing.

## D4 — GL/bank period comparison accepts ISO date strings

Prototype `closure._period` recognized only `datetime.date` objects (string
dates silently skipped the cutoff check unless upstream ingestion parsed
them). v2 also parses ISO `YYYY-MM-DD` strings. Golden cases are unaffected
(their periods match), but real string-dated exports now get the cutoff test
instead of a silent skip.

## Scope note (not a divergence)

The five base procedures (`ap.payment_voucher_reference`,
`ap.voucher_po_reference`, `ap.document_chain`, `ap.segregation_of_duties`,
`ap.vendor_relational_twins`) run in the prototype through the
rockwood/structural engines, not the incremental executor — the prototype's
`execute_procedure` raises "no incremental executor…" for them, and v2
preserves that exact behavior. Porting those engines (against
`rockwood_unified.json`) is the remaining Phase 2/3 work.
