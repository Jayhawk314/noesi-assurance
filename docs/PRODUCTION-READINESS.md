# Production readiness — pilot → real-industry deployment

This is the tracked gap list between the pilot as built and deployment in a
real assurance practice under professional standards. Each item states what
exists today, what deployment requires, and where the change lands. The
pilot's design intent holds throughout: the boundaries (API server, key
store, identity) are swappable adapters; the domain, methodology, and
evidence model do not change.

Legend: **[P0]** blocks any real-client use · **[P1]** blocks firm-wide
rollout · **[P2]** competitive/operational maturity.

The P0 items (plus trusted time) are sequenced into a concrete build plan
with arc-by-arc exit criteria in [P0-DEPLOYMENT-PLAN.md](P0-DEPLOYMENT-PLAN.md);
the independent review of 2026-08-07 (`reviews/REVIEW-2026-08-07.md`) is
the current statement of what the tool may be used for until that plan
completes.

---

## 1. Identity, sessions, and signatures

| # | Item | Today | Deployment requires |
|---|---|---|---|
| 1.1 | **[P0] Per-person authentication** | One bearer token per process; the operator switches chairs via `X-Acting-Principal` (openly documented as pilot role-play) | Real per-person sessions (SSO/OIDC or passkeys). Chair switching is removed; a principal id maps to an authenticated human. Lands in `workbench-api` (ASGI swap) + a principal directory; `WorkbenchService` is unchanged by design |
| 1.2 | **[P0] Key custody** | `LocalKeyStore` mints ed25519 keys per principal id in a local directory | Keys bound to the authenticated person and protected by OS keystore / HSM / cloud KMS; key rotation and revocation with re-signing policy; signature metadata already stores public material in-band, so verification of old packets survives rotation |
| 1.3 | **[P1] Trusted time** | Timestamps are local clock; packets state "no trusted time" in-band | RFC 3161 timestamp authority (or transparency-log anchoring) on lock digests and packet seals, so "when" in the amendment record is provable, not asserted. The limits text then changes honestly |
| 1.4 | **[P1] Role administration** | Partner assigns roles per engagement; roles are strings in `principal_assignment` | Firm-level admin (who may be a partner at all), licensing/CPE status flags, conflict screening hooks |

## 2. Archive, retention, and the documentation clock

| # | Item | Today | Deployment requires |
|---|---|---|---|
| 2.1 | **[P0] Retention enforcement** | Nothing is deletable through the app (tombstones, supersession), but the SQLite file and vault are ordinary files the OS owner can delete | Immutable archive storage for locked engagements (WORM / object-lock), scheduled retention: 5 years AICPA (AU-C 230), 7 years PCAOB (AS 1215), longer where state boards require; legal-hold override |
| 2.2 | **[P1] Documentation completion clock** | Lock can happen any time; no report-release-date concept | Record the **report release date**; surface the assembly window (60 days AICPA / 45 days PCAOB) as a visible clock and a readiness consideration; after the completion date, route all changes through the existing supersession path (already built) |
| 2.3 | **[P0] Backup / disaster recovery** | Single local directory (`~/.noesi-assurance`) | Tested backup and restore of control DB + vault + keys together (a restored DB without its vault fails digest verification — by design); documented RPO/RTO |
| 2.4 | **[P2] Archive format longevity** | Evidence packet is self-contained JSON + HTML workpaper | Long-term readability commitment: packet schema versioning discipline (v2→v3 precedent exists), PDF/A rendering of the workpaper |

## 3. Quality management and review

| # | Item | Today | Deployment requires |
|---|---|---|---|
| 3.1 | **[P1] Disposition review lifecycle** | **Done (Aug 2026).** A disposition on a factual dollar exception above clearly-trivial is a proposal until a reviewer or partner (never the proposer — separation enforced) concurs; changing a disposition voids its concurrence; the SAD withholds its conclusion and readiness blocks the lock (`DISPOSITIONS_AWAITING_CONCURRENCE`) while concurrence is pending; proposer and concurrer travel in the packet | — |
| 3.2 | **[P1] Workflow-edit review** | Materiality, stages, completion checks, and policies are direct writes (partner/preparer) | Materiality and policy changes carry rationale and reviewer concurrence; the journal already records who/when |
| 3.3 | **[P1] Engagement quality review (EQR)** | Roles are preparer/reviewer/partner | An EQR role with its own gate before lock for engagements that require it (SQMS No. 1 / QC 1000 risk criteria); the role matrix and readiness blockers are the extension points |
| 3.4 | **[P1] Data-less lock hole** | **Done (Aug 2026, after independent-review reproduction).** With zero normalized datasets, readiness raises `NO_DATA_WITHOUT_PARTNER_ASSERTION` and the lock refuses until the partner asserts on the record — with a ≥10-char reason — that no data-dependent procedures apply; the assertion enters the workflow document (covered by the signed manifest's payload hash) and travels in the evidence packet | — |
| 3.5 | **[P2] Firm methodology configuration** | Eleven AP contracts, versioned in code | Firm-editable contract catalogs with the same versioning discipline (a methodology change is a new version, never an edit), approval workflow for methodology changes, per-engagement methodology pinning (the job manifest already pins engine version) |
| 3.6 | **[P2] Peer review / inspection support** | Evidence packet + workpaper | An inspection export profile: packet plus journal extract plus supersession history, organized for a peer reviewer or PCAOB inspector |

## 4. Engagement lifecycle completeness

| # | Item | Today | Deployment requires |
|---|---|---|---|
| 4.1 | **[P1] Acceptance & continuance** | Engagement = client name + period | Acceptance/continuance documentation, independence confirmations per team member, engagement letter linkage — all before fieldwork gates open |
| 4.2 | **[P1] Completion-check evidence linkage** | Six completion checks (subsequent events, going concern, representations, …) take a note + free-form evidence list | Each check links to actual artifacts (e.g., the signed representation letter as a vault artifact), and the representation-letter date must not precede the report date |
| 4.3 | **[P2] TCWG communications** | Not modeled | Track required communications (AU-C 260/265: significant findings, control deficiencies) with the SAD feeding them directly |
| 4.4 | **[P2] Subsequent discovery workflow** | Unlock reason is free text | A structured reopening type (subsequent discovery of facts, AU-C 560/925 vs. administrative correction) driving different documentation prompts |

## 5. Confidentiality and data protection

| # | Item | Today | Deployment requires |
|---|---|---|---|
| 5.1 | **[P0] Encryption at rest** | Plain SQLite + vault files on the local disk | Full-disk or application-level encryption for control DB, vault, and keys; client data is confidential under AICPA ET 1.700 |
| 5.2 | **[P1] Tenant isolation** | `tenant_id` columns exist; one tenant per deployment in practice | Enforced isolation for a hosted profile (per-tenant DBs or row-level security), client-data residency options |
| 5.3 | **[P1] PII minimization** | Ingestion loads whatever the export contains (names, employee ids) | Field-level classification at mapping time; redaction options for teaching/demo exports; breach-notification runbook |
| 5.4 | **[P2] Vendor SOC 2** | n/a (local-first) | If hosted: SOC 2 Type II for the service itself — firms will ask before their risk committees allow it |

## 6. Scale and operations

| # | Item | Today | Deployment requires |
|---|---|---|---|
| 6.1 | **[P1] Concurrency** | One process, one writer, every request serialized on a lock | ASGI boundary + per-engagement write serialization; the worker protocol (frozen job manifests) was built so engine execution can move out-of-process without behavior change |
| 6.2 | **[P1] Large populations** | Engines are in-memory over normalized lists (tested to ~10³ rows) | Chunked/columnar ingestion and engine paths for 10⁶-row GL files; the manifest digest model already supports it (digest per table) |
| 6.3 | **[P2] Observability** | The journal is the audit log; server is silent | Separate ops telemetry (never mixed into the evidence journal), health checks, update channel with signed releases |
| 6.4 | **[P2] Interop** | CSV in; JSON/HTML out; Excel refused with instructions | First-class XLSX ingestion (converted, with conversion recorded as provenance), AICPA Audit Data Standards mapping for GL/AP extracts, connectors (QuickBooks/NetSuite/Sage) with extraction receipts |

## 7. Professional positioning (not code)

- **Statement of responsibilities**: the tool compiles coverage, executes
  deterministic procedures, and preserves evidence; **the auditor owns every
  judgment** — selection rationale, dispositions, materiality, the opinion.
  This must be stated in product terms of use and on the workpaper (the
  limits blocks already say it in-band; counsel should review the wording).
- **Not a substitute for a methodology**: firms adopt it under their own
  quality-management system; the contract catalog is an input to that
  conversation, not a replacement for it.
- **Names**: "receipt", "verdict", "refusal" are product terms; customer-facing
  material should map them to standards vocabulary (audit evidence,
  exception, scope limitation) to survive a technical reviewer's reading.

---

## Already deployment-grade (keep, do not regress)

- Supersession-only unlock with mandatory reason, journaled, signature-covered
  (AU-C 230 / AS 1215 change documentation) — including offline verification
  of the full amendment history in every packet.
- Content-addressed finding receipts; bit-frozen golden baselines with a
  documented re-baseline discipline.
- Reperform-on-read datasets (the read path *is* reperformance, digest-verified).
- Hash-chained decision journal wired into readiness as a hard blocker.
- Separation of duties enforced in the domain, not the UI.
- Refusal semantics: the tool states what it cannot prove, in-band, everywhere.
