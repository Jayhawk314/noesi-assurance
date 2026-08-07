# Noesi Assurance Workbench — Architecture

> **This is the current, authoritative description of the system as built.**
> The files under `docs/architecture/` are a historical assessment of the
> `noesi-cpa` prototype and the phase-by-phase porting notes; they describe
> plans and divergences, not the present code. When they disagree with this
> document or with the source, they lose.
>
> Last verified against the code: August 2026 (140 unit tests passing).

## What this product is

A local-first accounts-payable audit workbench. It ingests client accounting
exports, compiles which audit procedures that data can **honestly** support,
executes deterministic procedure engines that emit content-addressed finding
receipts, walks every result through preparer → reviewer → partner gates, and
produces a signed, offline-verifiable evidence packet.

The organizing principle is **honesty about what the tool can prove**:

- Coverage never claims a procedure is runnable unless an executor for it
  actually exists (status `unsupported` otherwise) and the data supplies every
  required field (`blocked` / `partial` otherwise).
- Engines emit **refusals** when evidence is absent rather than silently
  passing ("no bank feed provided; payment-to-bank clearing cannot be
  tested").
- Every finding is a receipt whose `receipt_id` is the SHA-256 of its own
  canonical content; every signature states in-band exactly what it does and
  does not prove.
- Silence is meaningful: a procedure that reports nothing means "within
  tolerance", never "nothing there". Tolerances are visible in evidence.

## Repository layout

```
apps/
  workbench-api/     hardened localhost HTTP boundary + demo seeding
  workbench-ui/      React/TypeScript review UI (Vite, no UI kit, no router)
packages/
  assurance-domain/       pure entities: money (Decimal), receipts, SAD,
                          readiness, jobs/worker protocol — no I/O
  assurance-persistence/  SQLite spine: migrations, unit of work,
                          hash-chained journal, repositories
  assurance-artifacts/    evidence vault (quarantine → promote), ed25519
                          signing (LocalKeyStore)
  assurance-application/  WorkbenchService: the use cases behind the screens,
                          role matrix, lock lifecycle
  assurance-workpapers/   evidence packet sealing/verification, HTML workpaper
  procedures-ap/          AP methodology: contracts, coverage compiler,
                          procedure engines, structural layer, ingestion
  structural-adapters/    owned graph/composition ports (ex-KOMPOSOS)
tests/
  unit/              the whole suite (140 tests)
  golden/            frozen Phase 0 bundles + capture scripts
case-studies/
  harborline-marine/ complete teaching case (see below)
docs/
  ARCHITECTURE.md    this document
  architecture/      historical prototype assessment — stale, kept as record
```

**Boundary rule:** `assurance-domain` and `procedures-ap` import no
framework, database, or HTTP code. Adapters implement ports from the outside.
The API server can be replaced (FastAPI/SSO for a firm-hosted profile)
without touching the service or anything beneath it.

## The methodology layer (`procedures-ap`)

### Contracts

Eleven versioned `ProcedureContract`s (`contracts.py`) declare, per
procedure: objective, cycle, financial-statement assertions, required
tables/fields, required policies, and stated limitations. Contract content is
frozen against the Phase 0 golden bundle — methodology changes require a new
version, not an edit. `OPTIONAL_POLICIES` (currently `split_window_days`)
lives beside the contracts because the contract dataclass shape is frozen.

### Coverage compilation (`coverage.py`)

`compile_coverage(inventory, policies, …)` reconciles three things:

1. the contract's required roles/fields against the supplied data inventory;
2. required policies against the approved engagement policies;
3. **the contract against the executor registry** — a contract with no entry
   in `engines.EXECUTORS` compiles as `unsupported`, never `executable`
   (divergence D3). No evidence request is generated for an unsupported
   procedure, and the evidence lifecycle can never promote one.

Statuses: `executable` | `partial` (fields or policies missing) | `blocked`
(tables missing) | `unsupported` (software gap). Compile-time never marks
anything `completed` (divergence D1) — execution status belongs to the run
lifecycle.

### Engines (`engines.py`)

`EXECUTORS` is the single source of truth for what this build can run — one
entry per procedure id, dispatched by `execute_procedure`. All eleven
contracts have executors:

| Procedure | Nature |
|---|---|
| `ap.payment_voucher_reference` | every payment cites an observed voucher |
| `ap.voucher_po_reference` | every PO-citing voucher reaches an observed PO |
| `ap.document_chain` | PO→voucher→payment coherence (amounts, date order, actors) |
| `ap.segregation_of_duties` | row-level self-approval and missing-approver checks |
| `ap.vendor_relational_twins` | identity twins (name similarity) + relationship twins (transaction profiles) |
| `ap.three_way_receipt_match` | PO / invoice / goods-receipt match |
| `ap.split_payment_review` | sub-threshold clusters; `split_window_days` widens same-day to N-day windows |
| `ap.subledger_gl_balance_tie` | AP subledger vs GL control account |
| `cash.bank_clearing` | payment-to-bank clearing (2% tolerance) |
| `gl.payment_posting` | payment-to-GL amount and period |
| `forensic.closed_value_flow` | directed round-trips over the value-flow graph |

Money is `Decimal` end to end; floats appear only at the receipt
serialization boundary (`fnum`) for bit-compatibility with the float-era
goldens. The structural layer (`structural.py`) stays float (divergence D7) —
its output is leads and control observations, never SAD candidates. The two
structural functions reused by engines (`document_chain_findings`,
`relational_twin_findings`) take `domain`/`policy`/scope-note parameters so
generic runs emit generic receipts while the legacy Rockwood defaults stay
bit-identical for the shadow tests.

### Receipts (`assurance-domain/receipts.py`)

One finding = one `Receipt`: domain, key, verdict (`AGREE/TENSION/CLASH/
ORPHAN/AMBIGUOUS/ERROR`), policy id, sources, score, reason, evidence dict.
Validation is structural (ORPHAN requires exactly one observed source; paired
verdicts need two). `receipt_id` is the SHA-256 of the canonical JSON —
content-addressed, so identical findings hash identically across runs and
eras.

### Jobs (`assurance-domain/jobs.py`)

A procedure never runs against "whatever is loaded". `build_manifest` freezes
procedure id/version, engine version, per-table row counts + SHA-256 digests,
and policies; `run_job` refuses inputs that do not match the manifest and
returns a `ResultBundle` (status, summary, receipt dicts, `result_digest`).
Executor `ValueError`s become recorded error runs, never hidden.

## Persistence (`assurance-persistence`)

SQLite, one writer, explicit `BEGIN IMMEDIATE`/`COMMIT`. Every use case goes
through `run_command(conn, Command, handler)`: one transaction containing the
state change, the domain events, the outbox rows, and an idempotency receipt
(same `command_id` → replayed result, not re-execution).

**Hash-chained journal:** every accepted `domain_event` links to its
predecessor (`prev_hash`/`entry_hash`). `verify_journal` re-derives the whole
chain; a broken chain is a readiness blocker (`DECISION_TRAIL_BROKEN`).

Migrations are numbered and additive (`database.py`, currently 1–5).
Migration 5 rebuilt the lock tables for supersession (SQLite cannot drop a
UNIQUE constraint in place); an upgrade test proves legacy locked databases
survive byte-for-byte.

## Evidence (`assurance-artifacts`)

Uploaded bytes go through quarantine → register → **promote** into a
content-addressed vault; the `artifact` row is the authority on existence and
retention. Retirement is a tombstone, never a delete. Datasets are not stored
materialized: every read **reperforms** normalization from the immutable
artifact through the approved mapping and verifies the recorded
`output_digest` — refusing to serve data it cannot reproduce.

Signing: `LocalKeyStore` mints a stable ed25519 key per principal;
verification material (public key PEM) is stored alongside every signature so
packets verify with no access to the key store.

## Application layer (`WorkbenchService`)

The pilot authorization model: the first principal to create an engagement is
its **partner**; partners assign the team; **preparers** ingest, map,
normalize, run procedures; **reviewers** approve mappings and review runs;
partners approve reviewed runs, lock, and unlock. Separation of duties is
enforced in the domain/repositories (a proposal's author cannot approve it; a
run's executor cannot review it; a reviewer cannot approve their own review)
— the service adds the role matrix, never replaces those checks.

The screen-by-screen use cases:

1. **Engagement/team** — create, assign roles.
2. **Sources & mappings** — upload artifact → propose mapping (auto header
   detection; unmapped headers and refused fields are explicit) → reviewer
   approves → normalize (Excel uploads are refused at mapping time with
   instructions; the workbook bytes stay in the vault as evidence).
3. **Coverage** — compile against live data + approved policies; set
   policies inline (`update_workflow` section `"policy"`).
4. **Runs & findings** — run executable procedures (approved engagement
   policies merge into every run; per-run values override), review/approve
   runs, disposition findings (cleared/unadjusted/adjusted/waived/follow-up).
5. **SAD & readiness** — summary of audit differences vs materiality with a
   clearly-trivial threshold; readiness derives blockers and a report
   implication.
6. **Lock & export** — see the lock lifecycle below.

## The lock lifecycle

Professional basis: AU-C 230 / PCAOB AS 1215 — after file assembly, nothing
is deleted or discarded, and changes record the specific reason, by whom, and
when.

- **Lock** (partner, green readiness gate required): freezes a deterministic
  manifest of every covered entity (engagement, workflow hash, artifacts,
  mappings, datasets, runs, dispositions, team), anchors it to the journal
  head, signs the digest with the partner's device key. One transaction — or
  none of it.
- **Verify** (`verify_lock`): re-derives the manifest from live state and
  reports drift section-by-section; re-verifies the signature; re-verifies
  the journal chain and the anchored head. Also re-verifies every
  **superseded** lock from stored material alone.
- **Unlock = supersession, never deletion**: partner-only, specific reason
  required (≥10 chars); the active snapshot is marked superseded in place
  with reason/who/when, and the same facts ride the journal event — the
  amendment record is inside the hash chain. The engagement reopens and
  changes flow through the normal review gates again.
- **Re-lock**: a new signed snapshot (sequence n+1) whose manifest carries a
  `supersedes` section naming the predecessor's digest and the unlock
  reason — the new signature covers the amendment record itself. First locks
  keep the original v1 manifest shape, so pre-supersession digests still
  verify. At most one active lock per engagement (partial unique index).
- **Export** (`export_packet`, packet v3): refuses unless the active lock
  fully verifies right now. The packet carries the lock, the **full amendment
  history** (superseded manifests + signatures + reasons), every run with
  findings and result digests, dispositions, the SAD, and stated limits, then
  is sealed with the exporter's signature. `verify_packet` reperforms seven
  integrity claims offline — receipts, run seals, lock manifest, lock
  signature, lock history, packet digest, export signature — needing nothing
  but the packet. `render_workpaper` produces a self-contained HTML document
  from it, including the amendment history.

What none of this proves is stated in-band: source authenticity, extraction
completeness, or trusted time.

## API and UI

**Server** (`workbench-api`): stdlib `ThreadingHTTPServer`, loopback only.
Every request — reads included — requires the per-session bearer token; Host
and Origin are allowlisted; bodies are limited (and drained before a 413 so
clients get the refusal, not a reset); responses carry a strict CSP. The
built UI is served statically with the token injected into the page.

**Chairs:** the token authenticates the local *operator*; a request may act
as any principal via `X-Acting-Principal` (validated), defaulting to the
startup principal. On one laptop the operator plays every chair —
separation-of-duties gates apply to chairs exactly as to people, every
command journals its chair, and the UI shows "acting as" at all times. This
is stated openly as the pilot trust model: the console owner already controls
every local identity, so the header changes convenience, not the boundary. A
firm-hosted profile with real per-person sessions replaces it.

**UI** (`workbench-ui`): seven tabs — Flow Map (purchase-to-pay diagram
driven by live coverage), Team, Sources & Mappings, Coverage, Runs &
Findings, SAD & Completion, Lock & Export. Dark/light theme; dense tables; no
router, no component library.

**Startup:** `noesi-workbench [--data DIR] [--port N] [--principal ID]
[--demo [CASE_DIR]]`. `--demo` idempotently seeds the Harborline engagement
through the real three-chair path with policies approved.

## Golden bundles and the freeze policy

`tests/golden/bundles/` are frozen captures from the Phase 0 prototype:
contracts, coverage compilations, executor receipts (bit-for-bit including
`receipt_id`), SAD, readiness, and the full Rockwood structural run. Shadow
tests assert exact equality, normalized only by the documented divergences.
The digests of the bundles themselves are pinned in `MANIFEST.json`.

Behaviour frozen by goldens is changed only deliberately: re-baseline the
probe or bundle, and record what changed and why. Divergences to date:
D1 (no compile-time `completed`), D2 (owned structural adapters replace
vendored KOMPOSOS), D3 (coverage reconciles against the executor registry),
D7 (structural layer stays float). New behaviour (five new executors, the
split window, supersession) is covered by ordinary unit tests, not goldens.

## The Harborline Marine teaching case

`case-studies/harborline-marine/` — a complete, instructor-ready case:

- `generate.py` — deterministic generator (846 rows across ten roles,
  **40 planted exceptions** across all eleven procedures); regenerating the
  data regenerates the answer key, so they cannot drift apart.
- `data/` — the ten CSV exports.
- `docs/` — engagement brief, audit plan, walkthrough, assignments.
- `workpapers/` — student working-paper templates (WP-A1 … WP-SAD, PBC list).
- `instructor/ANSWER-KEY.md` — what was planted (do not distribute).
- `instructor/VERIFIED-RUN.md` — what the engine actually found, verbatim;
  where the two differ, this file is the authority on tool behaviour.
- `instructor/verify_run.py` — headless end-to-end re-run through
  `WorkbenchService` with three principals; prints every finding for
  line-by-line reconciliation.

Designed teaching points: one bank-clearing difference sits inside the 2%
tolerance and stays silent; the three phantom-PO vouchers surface in two
procedures (double-count judgment for the SAD); the split cluster spans nine
days and is invisible until the auditor chooses a window.

## Known limits / next hardening

- Readiness does not yet distinguish a first lock from a re-lock: after
  reopening, nothing forces the *new* work to be re-reviewed before relocking
  (each run's own review state still shows on the workpaper).
- Source loading is one file at a time (upload → propose → approve →
  normalize per role); fine for the demo seed, tedious for real engagements.
- Single process, single writer, requests serialized; the firm-hosted
  profile (real sessions, ASGI, external time-stamping) is a boundary swap by
  design, not a rewrite.
