# Noesi CPA: implementation assessment and recommended production architecture

**Assessment date:** 22 July 2026  
**Code reviewed:** `C:\Users\JAMES\github\noesi-cpa`  
**Companion document:** `RECOMMENDED_EPISTEMIC_ARCHITECTURE.md`

## Executive verdict

Noesi CPA is the strongest near-market product in the reviewed ecosystem. It is
not merely an idea or a mathematical demonstration. It already performs a coherent
accounts-payable audit workflow:

1. ingest supplied accounting exports;
2. preserve file, row, mapping, and control-total lineage;
3. compile which procedures are executable, partial, blocked, or excluded;
4. request missing evidence;
5. require preparer validation and separate reviewer approval;
6. execute deterministic procedures;
7. preserve findings and procedure-run history;
8. route findings through human disposition and a Summary of Audit Differences;
9. block completion when evidence, review, scope, or workflow conditions remain open;
10. lock a reviewable snapshot and export an evidence packet and workpaper.

That is a real product-shaped spine. The distinctive value is not “AI does an
audit.” It is:

> **Noesi tells an auditor which procedures the supplied data can honestly support,
> records why the others cannot run, and produces a reproducible evidence-linked
> workpaper.**

My recommendation is **not a complete rewrite of the audit logic**. Preserve and
port the procedure contracts, coverage compiler, deterministic checks, refusal
semantics, review gates, run receipts, field-intake validation, and workpaper
model. Rewrite the product boundaries around them:

- engagement identity and isolation;
- persistence and transactions;
- authenticated identity and authorization;
- evidence storage and provenance;
- API and UI separation;
- procedure execution and resource isolation;
- packaging and dependency ownership;
- signed locking and durable audit history.

The best next system is a **local-first assurance workbench implemented as a
modular monolith, with isolated procedure workers**. It should support a
single-user encrypted local deployment first and a firm-hosted PostgreSQL
deployment from the same application contracts later. Microservices are not the
right starting point.

### Short scorecard

| Dimension | Current state | Judgment |
|---|---:|---|
| Audit workflow concept | Strong | Preserve |
| Procedure executability and refusal | Strong and differentiating | Preserve and deepen |
| Deterministic AP procedures | Useful but narrow | Validate, version, and expand |
| Human review gates | Strong prototype semantics | Preserve, bind to real identities |
| Data lineage | Good prototype | Port to immutable artifact manifests |
| Evidence/workpaper output | Strong prototype | Preserve, sign, and make reperformable |
| Persistence | Prototype only | Rewrite |
| Engagement isolation | Unsafe for multiple periods/users | Rewrite first |
| Authentication/authorization | Not implemented | Rewrite first |
| Local HTTP product shell | Demonstration-quality | Replace |
| Packaging/dependencies | Research-repository quality | Separate and rebuild |
| Independent field accuracy | Not established | Pilot before efficacy claims |
| Paid market readiness | Pilot candidate, not production product | Conditional high potential |

## What Noesi CPA actually is

Noesi CPA currently contains three different things in one Python distribution:

1. **The audit product** in `noesis/audit/`, about 37 modules and roughly 11,600
   lines according to the repository footprint.
2. **The inherited Noesis research runtime**, including the
   observe → propose → judge → remember organism, SEAM experiments, AERO, and
   adjacent capabilities.
3. **A vendored KOMPOSOS-V codebase** used by structural routing and
   Dempster–Shafer fusion through runtime `sys.path` modification.

The product path is a local Python application. Its main operable surface is
`noesis/audit/engagement_view.py`, a roughly 1,500-line module containing:

- HTML and CSS generation;
- browser-side JavaScript;
- report assembly;
- workflow orchestration;
- evidence upload handling;
- procedure rerun triggers;
- persistence calls;
- a threaded standard-library HTTP server.

It binds only to `127.0.0.1`, which is a sensible prototype safety choice, but
loopback binding is not authentication and does not make a consequential tool
production-safe.

### Supported accounting roles

The canonical ingestion layer recognizes:

- vendors;
- employees;
- purchase orders;
- vouchers/invoices;
- payments;
- value flows;
- bank transactions;
- general-ledger entries;
- goods receipts;
- AP control balances.

It maps source headers through declared synonym sets, records the file SHA-256,
row count, column map, unmapped headers, refused canonical fields, source row,
row content hash, and a control total where applicable.

### Current procedure contracts

The procedure registry declares eleven versioned procedures:

1. payment-to-voucher reference;
2. voucher-to-purchase-order reference;
3. PO → voucher → payment chain coherence;
4. payment segregation of duties;
5. vendor relational-twin screening;
6. payment-to-bank clearing;
7. payment-to-GL posting;
8. AP subledger-to-GL control-account tie;
9. PO/invoice/goods-receipt three-way match;
10. split-payment review;
11. closed-population value-flow review.

Each contract records an objective, cycle, assertions, required roles and fields,
required policies, evidence source, denominator, policy version, and limitations.
That contract model is one of the best parts of the repository.

### Current state and evidence files

The live product state is spread across:

- `engagement_workflow.json`;
- `dispositions.json`;
- `trail.jsonl`;
- an `evidence/` directory;
- generated JSON, JSONL, CSV, and HTML outputs.

The trail is hash-chained. Evidence and snapshots are content-addressed. These
features detect certain later changes, but they do not authenticate a person,
establish a trusted time, prevent a local user from rebuilding the chain, or make
separate file updates transactional.

## What the implementation gets right

### 1. It distinguishes missing evidence from a passed procedure

Many audit prototypes quietly skip checks that cannot run. Noesi instead compiles
coverage and exposes `executable`, `partial`, `blocked`, and `not_selected`.
Missing roles, fields, and policy values become explicit requests tied to the
procedures they would unlock.

This is commercially meaningful. An auditor often spends considerable time
discovering what a client export does not contain. A defensible, reviewable
coverage map can save time before any anomaly detector runs.

### 2. It does not treat an upload as a completed procedure

The evidence lifecycle distinguishes open, requested, received, validated,
rejected, and superseded states. Evidence must be validated by a preparer and
approved by a different reviewer before it can support a procedure. Newly
supported procedures become ready to run; the file's arrival is not itself a
test result.

That separation is correct and should survive the rewrite unchanged in meaning.

### 3. It favors deterministic procedure execution

The important procedure engines are ordinary Python functions. The product can
run without an LLM deciding audit conclusions. AI could later propose mappings,
explanations, or request wording, but approval can freeze those proposals into
deterministic inputs.

This is the right risk posture for audit software.

### 4. It has unusually honest refusal and limitation semantics

The code repeatedly distinguishes:

- observed mismatch;
- expected-but-missing evidence;
- structural anomaly;
- control observation;
- investigation lead;
- scope limitation;
- proved exception.

For example, a missing receipt is not automatically called fraud, a relational
twin is not proof of duplication, and document-chain coherence does not
authenticate the documents. This restraint is a product advantage.

### 5. It preserves enough lineage to support reperformance

File hashes, row locators, row hashes, mappings, engine and policy versions,
procedure input hashes, superseded run IDs, findings, and review state are all
represented. The evidence packet openly disclaims what its seals cannot prove.

The existing representation needs hardening, but the underlying information
model is valuable.

### 6. It has real completion gates

Readiness checks include materiality, stage completion, risk and control
assessment, unsupported control reliance, selected procedure coverage, procedure
review, evidence review, source extraction and transformation approval,
unresolved misstatements, invalid waivers, scope items, completion procedures,
trail integrity, and team assignments.

This is more than an exception dashboard. It is the beginning of an assurance
workflow engine.

### 7. The repository is candid about validation

The independent-validation harness fails closed when independence conditions are
not met. Repository-authored cases are not presented as field accuracy. The dated
technical audit explicitly says no new independently authored engagement has
been supplied.

That honesty should remain part of the product brand.

## The production blockers

The following are not cosmetic cleanup items. They decide whether an audit firm
can trust the system with real engagements.

### P0 — Engagement isolation is not safe

Workflow engagements use `company|fye` as an identifier, but dispositions are
stored globally and finding IDs are formed from:

`company | domain | finding key`

The fiscal period is absent. Two audits of the same company can therefore reuse
the same disposition key across years. The shared `dispositions.json` and
`trail.jsonl` increase the possibility of cross-engagement contamination.

Names and periods are also not durable internal identifiers. A spelling or
renaming change can fork state, while a collision can join state that should be
separate.

**Required correction:** assign opaque `tenant_id`, `engagement_id`,
`engagement_version_id`, `artifact_id`, `procedure_run_id`, and `finding_id`
values. Every persisted row, artifact path, event, receipt, and export must carry
the engagement boundary. Human-readable company and period are attributes, not
keys.

### P0 — State changes are not transactional

The current application performs read-modify-write updates to ordinary JSON
files. Disposition persistence and trail append are separate operations.
Workflow saving, procedure execution history, trail updates, evidence-file
creation, and evidence metadata changes can also span separate writes.

Consequences include:

- two HTTP threads can overwrite one another;
- a crash can save the decision but omit the trail entry, or vice versa;
- partial evidence metadata can outlive a failed workflow update;
- lock checks and mutations are subject to time-of-check/time-of-use races;
- there is no reliable optimistic version check;
- backups cannot capture a guaranteed consistent engagement snapshot.

**Required correction:** one database transaction must commit the command's
domain change, append-only event, projection update, and outbox record. Artifact
bytes should be staged, hashed, and atomically promoted only after the database
accepts the artifact manifest.

### P0 — Roles are strings, not authenticated principals

The UI accepts preparer, reviewer, partner, locker, and unlocker names as text.
The workflow correctly rejects identical names and restricts later entries to
assigned names, but it cannot prove who typed them.

Separation of duties is therefore a logical demonstration, not an access
control. Anyone with access to the local endpoint or state files can act under
another typed identity.

**Required correction:** bind every command to an authenticated `principal_id`
and an engagement assignment. Enforce role and separation rules server-side.
Use firm identity through OIDC/SAML for shared deployments; use an
OS/device-bound local identity and a short-lived session for the desktop
deployment. Display names are never authorization inputs.

### P0 — The local HTTP boundary is not hardened

The standard-library server has no login, authorization token, CSRF defense,
Origin/Host allowlist, TLS, security headers, request schema layer, or general
request-size limit. Evidence uses base64 inside JSON, expanding memory use.
`ThreadingHTTPServer` admits concurrent mutations even though persistence has no
locking.

Loopback-only service reduces network exposure but does not address malicious
local pages, other local processes, browser-origin attacks, or multi-user
workstations.

**Required correction:** replace the server. For a local browser application,
launch with a high-entropy per-session token, strict Host and Origin validation,
SameSite cookies or explicit bearer binding, CSRF protection, a narrow Content
Security Policy, body limits, and no unauthenticated mutation. Prefer a signed
desktop shell once the workflow stabilizes.

### P0 — Hashes are being asked to do more than hashes can do

The code's documentation understands this, but a production implementation must
make the distinction operational:

- a SHA-256 digest identifies bytes;
- a hash chain detects changes relative to a known head;
- neither proves source authenticity, reviewer identity, trusted time, or
  external custody.

Because the local user controls the state and chain, the user can replace both
content and hashes unless an external or cryptographic trust anchor exists.

**Required correction:** sign lock manifests with an authenticated user/firm key,
include certificate/key identity and verification material, and optionally
anchor final snapshot digests to a customer-controlled or independently
witnessed store. Never claim that signing proves the accounting source was
complete; it proves who approved a particular byte set and when the signing
service recorded it.

### P1 — Executability and execution semantics are inconsistent

The base coverage compiler marks a procedure with all required fields as
`execution_status = completed`. Procedures unlocked later by uploaded evidence
receive explicit versioned `procedure_run` records and review state.

This creates two models:

- base procedures appear completed because inputs exist and the unified engine
  ran broadly;
- incremental procedures have an explicit contract-specific run receipt.

For professional use, every selected procedure needs the same lifecycle:

`planned → executable → queued → running → completed/error → reviewed → approved`

Presence of required fields means **executable**, never completed. Each completion
must point to a frozen input manifest, mapping version, procedure code digest,
policy values, parameters, result digest, and logs.

### P1 — Accounting numbers use binary floating point

Ingestion and several procedures convert money to Python `float`. Control totals
and findings are rounded later. This is acceptable for a prototype but not the
canonical arithmetic boundary of an accounting workbench.

**Required correction:** use decimal values with explicit scale and currency, or
integer minor units where appropriate. Preserve original text, parsed decimal,
currency, sign convention, and debit/credit interpretation. A procedure must
refuse mixed or unknown currencies rather than silently aggregate them.

### P1 — Mapping needs a first-class reviewed transformation model

Header synonyms are a useful bootstrap, but exact synonym matching is not enough
for messy exports. Production ingestion needs:

- explicit source schema profiling;
- proposed versus approved column mappings;
- source and target data types;
- value transformations;
- date, time-zone, decimal, sign, and currency rules;
- rejected-row quarantine;
- duplicate-key and null diagnostics;
- row-count and control-total reconciliation;
- versioned mapping changes and rerun impact.

The current system records the detected map and requests transformation approval,
which is the correct seed. The map itself must become a durable, reviewable object.

### P1 — Evidence storage is a local folder, not a vault

Evidence is content-addressed and path traversal is checked before use—both good.
However, the store lacks encryption management, retention policies, legal holds,
quotas, backup/restore verification, malware scanning, MIME verification, and
artifact-level access control. Uploading as base64 requires the full file to exist
multiple times in memory.

**Required correction:** stream multipart uploads into a quarantine area; enforce
size and type policies; scan before promotion; encrypt with engagement-scoped
data keys; store immutable artifact manifests; and record retention and deletion
events. Production evidence should never be served directly from an arbitrary
filesystem path.

### P1 — Procedure code and methodology governance are not yet separated

Eleven contracts are hard-coded Python objects. Engine and policy versions are
strings, but professional methodology needs:

- effective dates;
- author and approver;
- jurisdiction or standards applicability;
- semantic version and immutable code digest;
- parameter schema and defaults;
- expected input/output schemas;
- change rationale;
- regression evidence;
- deprecation state;
- firm-specific overlays;
- reproducibility guarantees.

A procedure library is not merely a plugin folder. It is controlled audit
methodology.

### P1 — The package cannot be shipped cleanly

The repository is branded `noesi-cpa`, while `pyproject.toml` still calls the
package `noesis` and describes the generic cognition loop. Only `noesis*` packages
are selected for installation. Structural code expects a sibling
`KOMPOSOS-V-base` directory and modifies `sys.path` to import its absolute
`core.*` and `categorical.*` modules.

A normal built wheel would not contain that sibling code in the expected place.
This makes behavior dependent on a source checkout layout and risks module-name
collisions.

**Required correction:** create separately versioned installable packages:

- `noesi-assurance-core`;
- `noesi-procedures-ap`;
- optional, explicitly owned structural libraries;
- `noesi-workbench`.

Vendor only audited code actually required by a procedure, or publish the
dependency as a proper locked package. Remove runtime `sys.path` mutation.

### P1 — The application is a dictionary-oriented monolith

The product spine passes large untyped dictionaries between ingestion, unified
reporting, workflow, procedures, review, and UI. The single engagement-view
module combines rendering, transport, orchestration, persistence, and execution.

This makes schema evolution and security review difficult. It also increases the
chance that a field is omitted from a receipt, silently defaulted, or interpreted
differently by two modules.

**Required correction:** introduce explicit versioned command, entity, event,
artifact, procedure-run, finding, and export models. Keep domain code independent
of HTTP, database, and UI frameworks.

### P1 — Field efficacy remains unknown

The tests show mechanism consistency and regression resistance. A prior full-suite
run in this review thread collected 206 tests, with 205 passing and one unrelated
CHEM compatibility-score drift. The repository's documentation claims an earlier
206-pass checkpoint. In the current restricted filesystem, an audit-focused rerun
could execute 68 non-temporary-path cases successfully, while 42 cases requiring
pytest temporary writes were blocked by environment permissions; that is not a
product failure and is not a substitute for the prior full run.

None of these test results establish:

- accuracy on a new company's books;
- false-positive cost;
- procedure coverage across ERP exports;
- auditor time saved;
- confirmed recoveries;
- workpaper acceptance;
- security suitability.

The next evidence milestone is an independently authored, externally reviewed
field pilot—not more internal mathematical machinery.

### P2 — The Summary of Audit Differences is a useful but incomplete model

The repository itself notes that the SAD currently does not fully model:

- income-statement versus balance-sheet effects;
- overstatement versus understatement direction;
- factual, judgmental, and projected misstatements;
- sampling projection;
- passed adjustments across accounts and periods;
- tax effects and prior-period effects.

Keep it, but label it as an AP pilot summary until methodology review expands it.

## Recommended target: Noesi Assurance Workbench v2

### Architectural style

Use a **modular monolith** for the control plane and separate **sandboxed worker
processes** for data transformations and procedure execution.

This means one deployable application owns transactions, identity, workflow,
review, locking, and exports. Internally it has strict module boundaries and
ports. Expensive or risky procedures execute out of process against immutable
input manifests.

Do not begin with networked microservices. They would add distributed
transactions, service authentication, message delivery, tracing, deployment
operations, and more validation surfaces before Noesi has proven repeatable
field value.

### Target flow

```text
Authenticated auditor
        |
        v
Workbench UI  --->  Application API / command handlers
                           |
             +-------------+-------------+
             |                           |
             v                           v
   Transactional control DB       Encrypted artifact vault
   engagement/workflow/events     raw files/manifests/exports
             |
             v
   Mapping + coverage compiler
             |
             v
   Immutable procedure job manifest
             |
             v
   Isolated deterministic worker
             |
             v
   Run receipt + findings + refusals
             |
             v
   Human review -> SAD -> completion gates
             |
             v
   Signed lock manifest -> workpaper/evidence packet
```

### Modules

#### 1. Engagement module

Owns tenants, clients, engagements, periods, versions, assignments, status, and
retention policy. It is the root isolation boundary.

#### 2. Artifact and observation registry

Owns immutable source artifacts, hashes, media types, declared provenance,
custody events, encryption metadata, and the exact observations derived from an
artifact. This is the audit-specific use of the Observation Registry proposed
in the companion epistemic architecture.

#### 3. Mapping and normalization module

Profiles source schemas, proposes mappings, records human approval, produces
typed canonical Parquet tables, quarantines rejected rows, and emits
reconciliation receipts. Original bytes are never replaced.

#### 4. Procedure registry and coverage compiler

Owns immutable procedure versions and compiles the engagement's approved
artifacts, mappings, policy values, and selections into executable, partial,
blocked, or excluded states. It emits refusal records as first-class results.

#### 5. Execution coordinator and workers

Creates idempotent jobs from frozen manifests. Workers have:

- read-only access to declared inputs;
- a writable scratch directory;
- no network by default;
- CPU, memory, and time limits;
- deterministic locale and time-zone settings;
- locked dependency and code digests;
- structured logs;
- one signed result bundle.

Workers cannot mutate engagement workflow directly.

#### 6. Findings and SAD module

Owns findings, stable identities, linkage to procedure runs and source
observations, dispositions, adjustment state, materiality, and aggregation. A new
run never silently inherits an old disposition: the system proposes carry-forward
only when identity and relevant evidence are unchanged, and a human approves it.

#### 7. Review and completion module

Implements the explicit state machines for evidence, mappings, runs, findings,
scope, completion, lock, and supersession. Commands are authorized using principal
IDs and current assignments.

#### 8. Evidence packet and workpaper builder

Builds exports from a frozen snapshot manifest, not from live mutable files.
Every displayed conclusion must resolve to:

- the applicable procedure version;
- its input manifest;
- source observation locators;
- parameters and policies;
- run result;
- human review;
- limitations and refusals.

#### 9. Signed event journal

Each accepted command appends an immutable event in the same transaction as its
state change. Important events are chained and periodically signed or anchored.
This journal should become the audit vertical's projection into the single
Decision Ledger proposed in `RECOMMENDED_EPISTEMIC_ARCHITECTURE.md`; Noesi should
not invent a competing universal ledger.

## Canonical data model

At minimum, use explicit entities similar to:

| Entity | Essential identity and content |
|---|---|
| `Engagement` | tenant, engagement UUID, client, period, version, status |
| `PrincipalAssignment` | principal UUID, engagement, role, effective interval |
| `Artifact` | artifact UUID, engagement, byte digest, size, media type, vault key, provenance state |
| `MappingSpec` | source schema digest, canonical role, field transforms, version, preparer/reviewer |
| `NormalizedDataset` | artifact inputs, mapping version, schema, row/reject counts, control totals, output digest |
| `ProcedureDefinition` | procedure/version/code digest/objective/assertions/input and parameter schema/limitations |
| `ProcedurePlan` | selection, rationale, coverage state, missing requirements |
| `ProcedureRun` | immutable job/run ID, input manifest, environment digest, status, output digest |
| `Finding` | stable finding UUID, run, type, magnitude, currency, source observations, limitations |
| `Disposition` | finding version, status, note, actor, event ID, supersession |
| `Review` | object type/ID/version, decision, actor, role, note, timestamp |
| `SnapshotManifest` | every entity/artifact/version included in a lock |
| `Signature` | snapshot digest, signer principal/key, signature, trusted-time evidence |
| `DomainEvent` | tenant, engagement, sequence, command ID, actor, before/after versions, event payload |

Use database constraints—not only application `if` statements—for engagement
foreign keys, uniqueness, optimistic versions, role separation where feasible,
and immutable object states.

## Storage and deployment profiles

### Pilot: encrypted local workbench

- One application process is the only control-database writer.
- SQLite is acceptable for transactional control state if all writes go through
  the application and migrations/backups are tested.
- Raw and normalized data live in an encrypted engagement vault.
- Parquet plus in-process DuckDB is appropriate for analytical scans.
- DuckDB is not the multi-user control database. Its official concurrency model
  is strongest for threads within one writer process, and cautions against
  multi-process/shared-directory write patterns.
- A desktop wrapper or authenticated localhost UI provides the interface.
- Export and backup are explicit signed operations.

### Firm-hosted deployment

- PostgreSQL is the control database.
- Tenant and engagement filters are enforced in the repository layer and with
  row-level security as defense in depth.
- An S3-compatible customer-controlled object store holds encrypted artifacts
  with versioning/retention controls.
- Workers consume immutable jobs through a durable queue/outbox.
- Firm SSO supplies principals and MFA.
- HTTPS, centralized audit logging, backup restore tests, key rotation, and
  monitoring are mandatory.

PostgreSQL row-level security can default-deny normal access when enabled without
an applicable policy, but table owners and privileged roles require careful
handling. It is defense in depth, not a replacement for application
authorization.

### Managed cloud

Do not make this the first commitment. Offer it only after pilots reveal buyer
requirements for data residency, SOC reports, retention, identity providers,
incident response, and customer-managed keys.

## Keep, port, rewrite, or retire

| Current element | Decision | Reason |
|---|---|---|
| `ProcedureContract` concepts | **Keep and extend** | Core differentiation |
| Coverage compiler and evidence requests | **Keep and port** | Strong, honest pre-procedure value |
| Deterministic AP checks | **Keep, characterize, validate** | Useful domain logic; needs field benchmarks |
| Refusal and limitation semantics | **Keep** | Trust and defensibility advantage |
| Field-intake hash verification | **Keep and port** | Good custody boundary seed |
| Review/readiness rules | **Keep and port to state machines** | Good workflow logic |
| Procedure-run fingerprints/history | **Keep and strengthen** | Reperformance foundation |
| Evidence packet/workpaper concepts | **Keep and rebuild from snapshots** | Valuable output |
| `engagement_view.py` server/UI/orchestration | **Rewrite** | Monolithic, unauthenticated boundary |
| JSON workflow/disposition stores | **Rewrite** | No transactions or concurrency control |
| Local JSONL hash chain as authority | **Replace** | Useful format, insufficient trust anchor |
| Typed names as roles | **Replace** | Not authenticated |
| Base64 JSON evidence upload | **Replace** | Memory and security limitations |
| Float monetary arithmetic | **Replace** | Accounting correctness risk |
| Global finding/disposition IDs | **Replace immediately** | Cross-period contamination risk |
| Runtime `sys.path` KOMPOSOS imports | **Replace** | Unshippable dependency boundary |
| Copied Noesis research runtime inside product distribution | **Separate** | Research and product release risks differ |
| SEAM receipt vocabulary | **Port selectively** | Keep useful result/refusal meaning; avoid metaphysical coupling |
| Halotheia | **Use only at consequential gates** | Good future governance court; not required inside arithmetic |
| PiNode memory | **Use as a derived projector only** | Useful recall; never source of audit truth |
| Aletheia ledger | **Do not duplicate** | Project legal/audit views from one decision journal |

## Recommended repository shape

```text
noesi-assurance/
  apps/
    workbench-api/
    workbench-ui/
    desktop-shell/
  packages/
    assurance-domain/       # pure entities, state machines, commands
    assurance-application/  # use cases and ports
    assurance-persistence/  # SQLite/PostgreSQL adapters and migrations
    assurance-artifacts/    # vault, hashing, encryption, scanning
    assurance-execution/    # job manifests and worker protocol
    assurance-workpapers/   # snapshot export and verification
    procedures-ap/          # controlled AP methodology + deterministic engines
    structural-adapters/    # optional, benchmarked KOMPOSOS-derived methods
  workers/
    procedure-runner/
  tests/
    unit/
    contract/
    integration/
    security/
    golden/
    field-validation/
  docs/
    architecture/
    methodology/
    threat-model/
    validation/
```

The Python domain packages should not import FastAPI, SQLAlchemy, React artifacts,
Tauri, PostgreSQL, or local paths. Frameworks implement ports at the outside.

## Migration plan

### Phase 0 — Freeze and measure the current behavior

Before moving code:

- create golden input/output bundles for all eleven procedures;
- capture refusal behavior and known limitations;
- record mapping, coverage, finding, SAD, readiness, and export snapshots;
- add a failing regression for same-company/different-period disposition
  isolation;
- add concurrency and crash-consistency tests around current state to document
  the failure modes;
- pin exact dependency and procedure source digests.

The goal is not to bless current accuracy. It is to prevent accidental semantic
changes during extraction.

### Phase 1 — Build the engagement-safe transactional spine

- introduce UUID identities and engagement-scoped repositories;
- create the relational schema and migrations;
- implement optimistic entity versions and idempotency keys;
- append events and outbox rows in the same transaction;
- import existing JSON state through a one-time migration tool;
- keep the current HTML read-only against the new application layer temporarily.

This is the first implementation phase because it removes the greatest evidence
integrity risk.

### Phase 2 — Extract pure audit domain modules

- turn workflow rules into explicit state machines;
- turn dictionary payloads into versioned models;
- separate procedure planning from execution;
- normalize all procedure runs to the same lifecycle;
- convert monetary values to decimal/currency types;
- create a stable worker protocol.

Run old and new engines in shadow mode against golden engagements and diff every
receipt.

### Phase 3 — Rebuild ingestion and the evidence vault

- immutable streamed artifact intake;
- approved mapping specifications;
- normalized Parquet datasets;
- row rejects and reconciliation reports;
- encryption, retention, quota, malware, and backup controls;
- source-system connector interfaces.

### Phase 4 — Replace the UI boundary

Build a typed API and a dense review-oriented TypeScript UI. Preserve the current
workflow concepts, not its mixed implementation. The first screens should be:

1. engagement and team;
2. source inventory and mapping review;
3. procedure coverage and evidence requests;
4. runs and findings;
5. SAD, scope, and completion;
6. review, lock, and export.

FastAPI is a reasonable Python API boundary because it supports standard security
schemes and production worker deployment, but adopting it does not itself provide
authorization, TLS, safe deployment, or audit controls. Those remain application
responsibilities.

### Phase 5 — Signatures and firm deployment

- bind locks to authenticated users and keys;
- add trusted-time or external anchoring where buyers require it;
- implement SSO and engagement assignments;
- add PostgreSQL and object-store adapters;
- complete threat modeling, penetration testing, restore testing, and dependency
  security review.

### Phase 6 — Field validation and commercial decision

Run at least three independently sourced AP engagements with design partners.
Measure:

- time from raw export to approved mapping;
- percentage of selected procedures executable;
- evidence-request reduction;
- auditor review minutes per finding;
- false-positive and false-negative observations;
- confirmed adjustment or recovery value;
- workpaper rework;
- failures by ERP/export shape;
- whether reviewers accept the packet without parallel manual reconstruction.

Only then decide which procedures to expand and how to price the product.

## Test and assurance strategy

### Every procedure version needs

- unit tests for boundaries and monetary arithmetic;
- property tests for invariants;
- mutation/adversarial cases;
- golden engagement results;
- schema-contract tests;
- deterministic rerun verification;
- performance and resource limits;
- methodology owner approval;
- field-validation status separate from code-test status.

### The platform needs

- tenant and engagement isolation tests;
- authorization matrix tests;
- preparer/reviewer separation tests;
- concurrent update and optimistic-lock tests;
- crash recovery at every multi-step transition;
- artifact tampering and path traversal tests;
- malicious CSV/XLSX/ZIP and formula-injection tests;
- localhost CSRF/Origin/Host tests;
- signature verification and key-rotation tests;
- backup and point-in-time restore exercises;
- full evidence-packet reperformance in a clean environment.

### Release gates

Do not collapse these into one “tests pass” badge:

1. **code correctness** — automated tests pass;
2. **procedure validation** — known cases and methodology review pass;
3. **field evidence** — independent engagement results exist;
4. **platform security** — threat and penetration findings are resolved;
5. **operational readiness** — restore, monitoring, support, and incident
   procedures work;
6. **market evidence** — auditors save time or improve evidence quality enough to
   pay.

## How Noesi should relate to PiNode and Halotheia

Noesi CPA should remain the **audit vertical**, not become the universal runtime.

- Noesi owns audit procedures, accounting schemas, materiality, findings, SAD,
  scope, and workpapers.
- Halotheia can later authorize consequential transitions such as approving a
  mapping, accepting evidence, overriding a blocked procedure, signing a lock,
  or releasing an export. It should consume clear Noesi claims and evidence
  references; it should not recompute accounting tests.
- PiNode can project useful engagement memory—prior mappings, recurring evidence
  gaps, review patterns—but a memory record cannot become audit evidence without
  returning through the observation and review boundaries.
- Aletheia can provide a claim-access-verdict view for legal work, while Noesi
  provides an engagement-procedure-finding view. Both should project from the
  same core observation, event, and decision contracts where integration is
  justified.

Do not integrate them until Noesi's own engagement IDs, artifact manifests,
procedure-run receipts, and authenticated review commands are stable. Premature
weaving would preserve the current ambiguities across more repositories.

## Product and market recommendation

The most credible initial paid product is:

> **A local-first AP procedure coverage and evidence workbench for small and
> mid-sized audit teams, internal audit groups, and forensic/accounting advisory
> practices.**

Sell the ability to:

- determine what can be tested from the exports received;
- create an evidence request list automatically;
- run a controlled set of deterministic AP procedures;
- review every mapping, input, exception, and limitation;
- produce a reperformable workpaper.

Do not initially sell:

- an autonomous CPA;
- an audit opinion;
- general fraud detection;
- whole-company assurance;
- guaranteed recovery;
- “mathematical proof” of accounting truth.

A free community edition could support one local engagement and a small AP
procedure library. Paid value can attach to firm identity, controlled methodology
libraries, team review, signed workpapers, connectors, firm hosting, support,
retention, and governance. Pricing should follow pilot evidence, not precede it.

## Final recommendation

Noesi CPA is successful as a **serious prototype of the right audit workflow**.
It is not successful yet as a secure multi-engagement professional system.

The valuable invention is already visible:

- compile procedure executability before claiming coverage;
- refuse unsupported work explicitly;
- make evidence lifecycle and reviewer separation first-class;
- execute deterministic procedures against frozen inputs;
- preserve findings, limitations, review, and workpaper lineage.

Protect that invention. Do not restart from a blank page and do not bury it under
more general intelligence machinery.

The decisive next move is to replace the unsafe shell:

1. engagement-safe identities;
2. transactional persistence and one audit journal;
3. authenticated principals and real role enforcement;
4. immutable encrypted evidence;
5. uniform procedure-run receipts;
6. signed snapshot locking;
7. independent field pilots.

If those are done well, Noesi CPA can become a credible paid B2B assurance
workbench. If they are skipped in favor of adding more detectors or mathematical
families, the system will remain impressive in a repository and difficult to
trust in an audit room.

## Current technical references used for the target design

- [DuckDB concurrency documentation](https://duckdb.org/docs/current/connect/concurrency)
- [PostgreSQL row security policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/)
- [FastAPI OAuth2/JWT security example](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [Tauri capability security model](https://v2.tauri.app/security/capabilities/)

