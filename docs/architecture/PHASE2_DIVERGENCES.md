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

Consequence (deliberate, tested): with v2-compiled coverage, `readiness()`
now raises `SELECTED_PROCEDURES_PENDING_RUN` for executable procedures that
were never actually run — a real completion gate the prototype's
compile-time "completed" used to mask. Legacy-shaped coverage fed to the
same function still reproduces the golden readiness exactly.

## D2 — vendored KOMPOSOS replaced by owned adapters (resolved)

Prototype: the structural layer reached KOMPOSOS through runtime `sys.path`
mutation into a vendored checkout (unshippable, P1). v2 ports exactly the
code the procedures require into the `structural-adapters` package —
composition reachability (`CompositionIndex`, the bridge's own BFS) and
Dempster-Shafer fusion (same author's dual-licensed math, operation order
preserved). `forensic.closed_value_flow` and the whole Rockwood structural
stack now run without any vendored runtime; the Rockwood shadow suite
verifies every receipt bit-for-bit against the prototype's report.

## D3 — Decimal arithmetic with a float serialization boundary

Prototype: binary floats end to end (P1 defect). v2: all monetary
arithmetic is `Decimal` (`assurance_domain.money`); floats are produced only
by `fnum()` when writing receipts/reasons, keeping v2 receipts diffable
against float-era goldens. Mixed-currency aggregation raises
`CurrencyMismatchError` instead of silently summing.

SAD aggregation (`assurance_domain.sad`) accumulates exact Decimals and
quantizes once at the boundary, where the prototype re-rounded floats after
each addition — identical on clean inputs (shadow-verified), and the exact
path cannot accumulate drift on messy ones.

Finding identity in the SAD prefers an engagement-scoped `finding_uid` and
falls back to the legacy `engagement|domain|key` composition only for
migrated rows (`assurance_domain.readiness.legacy_report_finding_id` is
likewise migration-only).

## D4 — GL/bank period comparison accepts ISO date strings

Prototype `closure._period` recognized only `datetime.date` objects (string
dates silently skipped the cutoff check unless upstream ingestion parsed
them). v2 also parses ISO `YYYY-MM-DD` strings. Golden cases are unaffected
(their periods match), but real string-dated exports now get the cutoff test
instead of a silent skip.

## D6 — exposure algebra label

The research-queue ranking folds exposure additively. The prototype
imported KOMPOSOS's `ADDITIVE_QUANTALE` for the same fold and labelled rows
`komposos_additive_quantale`; v2's owned fold is labelled
`additive_quantale`. Shadow normalization maps the old label to the new.

## D7 — the structural screening layer stays float

The structural/triage/fusion/ranking layer retains the prototype's float
arithmetic (scores, similarities, energies, exposure) for bit-for-bit
receipt parity. This is deliberate: everything that layer emits is an
investigation lead or control observation routed to human review — never a
SAD candidate. Deterministic monetary procedures (`engines`) run on Decimal
(D3). Migrating screening magnitudes to Decimal is future work that will
version the affected policies.

## Scope note (closed)

The five base procedures (`ap.payment_voucher_reference`,
`ap.voucher_po_reference`, `ap.document_chain`, `ap.segregation_of_duties`,
`ap.vendor_relational_twins`) run through the ported rockwood/structural
engines (`rockwood.py`, `structural.py`, `triage.py`, `fusion.py`,
`ranking.py`, `unified.py`), shadow-verified against `rockwood_unified.json`
— the full 39-verdict report matches bit-for-bit. The prototype's
`execute_procedure` behavior for these IDs (no incremental executor) is
preserved; they execute through the unified engagement path. The ACL binary
reader is intentionally not ported: the v2 input boundary is parsed
canonical tables.
