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
| 6.4 | **[P2] Interop** | CSV and .xlsx in (standard-library reader; the sheet, heading row and converter version are part of the reviewed spec); recipes for four standard QuickBooks Online report exports; JSON/HTML out | A QuickBooks General Ledger recipe; AICPA Audit Data Standards mapping for GL/AP extracts; live connectors (QuickBooks/NetSuite/Sage) with extraction receipts; Excel workpaper output |

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

## 8. Audit coverage

Sections 1–6 are about deploying what exists; this section is about what an
audit needs that Noesi does not do at all. Today the Workbench runs eleven
registered procedures (`procedures_ap/engines.py`, `EXECUTORS`), all in
payables, cash disbursements and payment posting. The order below is a
first guess; the friction log from an integrated practice case
([learn/FRICTION-LOG-TEMPLATE.md](learn/FRICTION-LOG-TEMPLATE.md)) is meant
to re-rank it by what a full audit actually kept needing.

| # | Item | Today | Deployment requires |
|---|---|---|---|
| 8.1 | **[P1] Journal-entry testing** | Not modeled | The AU-C 240 response to management override, required on every audit: GL population completeness, selection criteria (unusual users, times, accounts, round amounts, post-close entries), and a documented rationale per selected entry |
| 8.2 | **[P1] Revenue & receivables** | Not modeled | Procedures for the presumed revenue fraud risk (AU-C 240): sales cutoff, receivable aging, confirmation tracking (AU-C 505) with alternative procedures for non-responses |
| 8.3 | **[P1] Analytical procedures** | Not modeled | Preliminary and final analytics (AU-C 315 / 520): expectations, ratios and trends against prior period, with a threshold for investigation and the explanation recorded |
| 8.4 | **[P1] Sampling** | Procedures scan the whole supplied population; one known cap is in `ap.vendor_relational_twins`' activity-twin path (500 candidate pairs, `structural.py`), which reports a refusal past the cap instead of skipping pairs silently | Sample selection and evaluation (AU-C 530) for populations that cannot be tested in full: sample size, selection method, projected misstatement |
| 8.5 | **[P2] Inventory** | Not modeled | Count observation records, test counts, and price testing (AU-C 501) |
| 8.6 | **[P1] Duplicate-invoice test** | `ap_checks.duplicates()` exists but only the Rockwood golden path uses it; it is not a registered Workbench procedure, so Harborline's VCH-9338 has to be found by hand | Register it as a contract + engine (vendor, invoice number, amount, date proximity) with the same receipt model as the other eleven |
| 8.7 | **[P2] Vendor identity beyond names** | `ap.vendor_relational_twins` compares vendor names only for identity twins | Add tax ID, address and bank-account matches between vendors, and between vendors and the employee master |
| 8.8 | **[P2] Full bank reconciliation** | `cash.bank_clearing` checks payments against the bank feed | A bank reconciliation: book balance to bank balance with outstanding items and deposits in transit, not only disbursement clearing |
| 8.9 | **[P2] Fraud-risk documentation** | Not modeled | Records of the engagement-team fraud discussion and the management / TCWG inquiries AU-C 240 requires, linked into risk assessment |

**QuickBooks import: fixes to make** (from the 2026-09-24 code review; each
checked against the code):

- Refuse the AP tie when Unpaid Bills and the General Ledger name different
  dates, or a date other than the engagement's period end. Today the
  mismatch is only a note (`service.py`, `build_ap_control_balance`).
- Refuse a General Ledger whose opening balance can't be read. Today it is
  read as zero (`quickbooks.gl_account_balance`), and the running-balance
  check only catches it when the account has activity.
- Require a grand TOTAL row for the grouped reports that carry one
  (`quickbooks.apply`); the Bill Payment List normally has none.
- Check the report title, not only the column headings, when a recipe is
  chosen explicitly.
- Add a uniqueness guard so two simultaneous normalize calls can't both
  succeed (needed once requests run concurrently, item 6.1).
- Offer every sheet of a workbook for the AP tie, not only the first.

Related items tracked above, not repeated here: acceptance, independence and
engagement letter (4.1); management letter / control deficiencies, AU-C 265
(4.3); QuickBooks General Ledger recipe and Excel workpaper output (6.4).

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
