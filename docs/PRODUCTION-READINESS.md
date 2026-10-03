# Production readiness — one-user local audit supplement

Status date: 2 October 2026.

This is the gap list between the Workbench today and responsible use beside a
real audit. The product boundary comes from `THE-REAL-GOAL.md`:

> Noesi-Assurance supplements a complete human audit. It has one user per
> engagement and no approvals, signatures, locks, concurrence, or sign-offs.

The Workbench tests supplied data, records what it did and could not test,
and exports an unsigned evidence record. It is not the audit file, the firm's
quality-management system, or the source of an audit opinion. The auditor
owns scope, evidence selection, judgments, review, sign-off, reporting, and
retention under the applicable standards.

Legend: **[P0]** must be addressed before client data is entrusted to this
local installation · **[P1]** operational maturity for repeated real use ·
**[OUT]** belongs to multi-user audit-management software, not this product.

The older `P0-DEPLOYMENT-PLAN.md` describes the retired multi-user, signed,
locked design. It is historical and no longer governs this product.

---

## 1. Current product boundary

| Area | What exists now | Honest limit |
|---|---|---|
| User | One local user is recorded on each engagement. Commands are journaled under the session's principal id. | The principal id is a local label, not proof of a person's identity. The machine owner controls the process and its bearer token. |
| Network | A loopback-only HTTP server with bearer-token, Host/Origin, body-size, and static-path checks. | It is not a hosted or multi-user service. Do not expose it to a LAN or the internet. |
| Evidence | Files are content-addressed; normalized data is reperformed from the immutable vault bytes and checked against digests. | A digest detects changed bytes. It does not prove that the client supplied a complete or authentic population. |
| Decision record | A hash-chained journal, frozen run inputs, findings, dispositions, risks, coverage, and an exportable packet. | The packet is unsigned. Offline verification proves internal consistency, not who performed the work or when an external authority received it. |
| Readiness | Gates are about data, scope, procedures, open findings, risks, and broken integrity. | “Ready” means the supplement's own work is internally complete. It is not an approval, review, sign-off, or permission to issue a report. |
| Audit administration | None. | Acceptance, independence, staffing, supervision, EQR, communications, report release, documentation assembly, legal holds, and opinion approval stay in the firm's audit system and human process. |

Old database columns and tables for chairs and locks may remain so existing
stores still migrate and read. They are history, not current capabilities.

## 2. P0 — client-data custody and recovery

| # | Item | Status now | Required boundary or remaining work |
|---|---|---|---|
| 2.1 | **[P0] Encryption at rest** | SQLite and vault files are plaintext on disk. | Before client data is stored, use full-disk encryption with a protected OS account and encrypted backups. Application-level encryption is not built. Full-disk encryption protects a powered-off/stolen disk, not a compromised live session. |
| 2.2 | **[P0] Retention responsibility** | Engagements can be archived and, when eligible, deleted; the OS owner can remove the entire data folder. The Workbench exports an unsigned record. | The firm must retain its audit file, Noesi export, and required source evidence in its controlled retention system. Noesi does not enforce AU-C/PCAOB/state retention, WORM storage, or legal holds. Those are outside this local supplement. |
| 2.3 | **[P0] Backup and restore** | **Built and tested.** One zip contains a SQLite backup-API snapshot plus every promoted vault blob named by that snapshot. Each database and blob fingerprint is checked. Restore stages into a temporary directory, refuses a missing/damaged/mismatched vault or database, and never overwrites an existing store. | The manifest is unsigned: it catches damage and mismatches, not deliberate forgery of the whole backup. Backup is manual, local, and unencrypted unless the destination storage provides encryption. Restore must be run while the destination store is offline. |
| 2.4 | **[P0] Recovery practice** | Create, verify, and restore commands are available; tests use invented stores. | Before relying on the Workbench for client work, make an encrypted backup, restore it into a new folder, open that restored store, and document the drill. Repeat after material software/storage changes. A Kestrel-sized manual drill is still not recorded here. |

### Backup commands

```text
python -m workbench_api.backup create --data DIR --to FILE
python -m workbench_api.backup verify FILE
python -m workbench_api.backup restore FILE --data NEW_DIR
```

`create` refuses an incomplete or damaged live vault. `verify` checks the
whole backup without restoring it. `restore` accepts only a new or empty
destination and tells the operator to start the Workbench with `--data`
pointing at the restored directory.

There is no automatic schedule or service-level promise. Therefore:

- **RPO:** all work since the last successfully verified backup can be lost.
  The operator or firm chooses the backup frequency based on acceptable loss.
- **RTO:** the time to obtain the backup, run `verify`, restore to a new
  directory, and open/recheck the engagement. No maximum time is promised;
  the local restore drill establishes the practical time for that machine.

A backup taken during the narrow point where an upload record exists before
its blob is promoted may be refused. Retry after the upload finishes; no
successful backup is published from that incomplete snapshot.

## 3. Integrity claims — what they do and do not prove

### Built

- SQLite integrity is checked when a backup is verified or restored.
- Every promoted artifact named by the database must be present, filed under
  its sha256, and hash to that name.
- The backup manifest, zip contents, restored database, engagement count,
  schema version, journal check, blob sizes, and blob fingerprints must agree.
- Unexpected/duplicate zip entries and path-escape entries are refused.
- A database from newer software is refused rather than guessed at.
- A broken decision journal is reported in the backup/restore report. Backup
  preserves the store for recovery; it does not relabel a broken journal as
  sound.

### Permanent limits of the local model

- The machine owner can alter the program, database, vault, backup, and local
  clock. Digests are tamper-evident against accidental or partial change, not
  an external trust anchor against a determined owner.
- The backup manifest and exported engagement record are unsigned.
- Noesi proves what bytes it tested. It cannot prove source-system
  completeness, authorization, or client authenticity without external
  audit evidence.

## 4. Audit coverage and result honesty

The executor registry currently contains **50 procedures**: 11 original AP
procedures and 39 cycle procedures. Coverage includes planning analytics,
controls evaluation, journal entries, revenue/receivables, payables, payroll,
forensic tests, cash, inventory, PP&E, debt/equity, accruals, estimates,
related parties, and completion. Fraud/forensic work includes check-sequence,
vendor/employee matching, self-approved payments, Benford first digits, and
closed value-flow testing.

Kestrel currently runs 37 applicable procedures and its finish-line check is
174/176 with 0 unexplained differences. The two named gaps are the PO overrun
and unrecorded-liability line that the available QuickBooks exports cannot
support. Kestrel calibrates the engine; it is not proof that another client's
data is complete. Oceanview is a private second calibration case and must
never be published.

**Verification status, 3 October:** later Workbench UI defects show that a
passing procedure suite and case-key check are insufficient to call the
product finished. The remaining end-to-end UI and independent-review checks
are tracked in `docs/ROADMAP.md` and
`docs/WORKBENCH-FINISH-MAP-2026-10-03.md`. The P0 client-data controls in
this document are a separate requirement; passing the UI checks will not
waive them.

### Remaining operational gaps

| # | Item | Status now | Needed for broader use |
|---|---|---|---|
| 4.1 | **[P1] Large populations** | Engines operate on in-memory normalized lists; no current million-row benchmark is recorded. | Benchmark representative large GL/AP files, set supported limits, and refuse before memory exhaustion. Add chunked/columnar paths only where evidence shows they are needed. |
| 4.2 | **[P1] Import breadth** | CSV/XLSX mapping and reviewed QuickBooks report recipes exist. Unsupported exports are refused. | Add and test formats from real users; never infer a guessed layout merely to make a case run. Live connectors remain optional. |
| 4.3 | **[P1] Procedure validation** | Invented-data unit tests, Kestrel, Harborline, and private Oceanview calibration exist. | A practitioner must validate the procedures, thresholds, and limitations against the firm's methodology and the engagement. Standards/counsel review of customer-facing claims remains external. |
| 4.4 | **[P1] Update and incident practice** | Local process; no update channel, health dashboard, or incident runbook. | Pin releases used on engagements, keep the corresponding tests/results, and document how to stop use, preserve evidence, recover, and notify affected users after a defect or data incident. |

## 5. Confidentiality and local security

| # | Item | Status now | Remaining work or operator control |
|---|---|---|---|
| 5.1 | **[P0] Device/storage protection** | Localhost and session-token boundary; plaintext local data. | Protected OS account, screen lock, patched device, full-disk encryption, encrypted backup destination, and restricted filesystem permissions. |
| 5.2 | **[P1] PII minimization** | Ingestion retains mapped source files, which may contain employee/customer identifiers. | Export only needed fields, avoid unnecessary PII, control backup copies, and follow the firm's breach-response process. Teaching/demo exports must contain invented or properly licensed data. |
| 5.3 | **[P1] Dependency/release review** | Automated tests cover product behavior; this document records no current vulnerability or release-signing check. | Before client use, scan/pin dependencies and record the exact release/commit used. |
| 5.4 | **[OUT] Hosted tenant security / SOC reporting** | Not present. | Required only if the product boundary changes to a hosted multi-tenant service. |

## 6. Explicitly outside Noesi's scope

These are not readiness gaps for the one-user local supplement. They would
become a new product decision if Noesi becomes multi-user audit software:

- per-person SSO/passkeys, a principal directory, team roles, chair
  assignment, or separation-of-duties enforcement;
- review/approval/concurrence workflows, EQR gates, completion sign-offs, or
  methodology-approval workflows;
- signing keys, signature custody, trusted timestamps, signed packets, locks,
  unlock/supersession workflows, or report-release/documentation clocks;
- engagement acceptance/continuance, independence tracking, staffing,
  licensing/CPE, TCWG communications, or opinion authorization;
- hosted multi-tenancy, internet exposure, vendor SOC 2, data residency, and
  multi-writer concurrency.

The firm may and usually will perform many of these activities elsewhere.
Noesi must not claim that their absence means they occurred.

## 7. Professional positioning

- **A supplement, not an audit.** Running procedures does not constitute an
  audit, review, or assurance engagement.
- **No opinion or approval.** Draft opinion/SAD language is a structured aid
  that must show its limits; it is not a professional conclusion or sign-off.
- **Auditor judgment remains outside the engine.** The auditor owns data
  completeness, sample rationale, dispositions, materiality, risk responses,
  waivers, report implications, and whether sufficient appropriate evidence
  was obtained.
- **Not a substitute for firm methodology.** A firm adopts and validates the
  tool within its own quality-management and documentation system.
- **Commercial license required.** Use on client engagements is commercial
  use under this repository's license and requires permission from the
  copyright holder.

## 8. Minimum local-use checklist

Before placing real client data in the Workbench:

1. Confirm the commercial-use license and the firm's authorization to use
   the tool.
2. Use a protected, patched, full-disk-encrypted device and encrypted backup
   destination.
3. Pin the exact software commit/release and retain its test evidence.
4. Create and verify a backup, restore it into a new directory, open the
   restored store, and record the practical recovery time.
5. Set a backup frequency whose “since last backup” loss is acceptable.
6. Put the exported Noesi record and required source evidence into the firm's
   controlled audit-file retention process.
7. Validate scope, mappings, procedure limitations, thresholds, findings,
   refusals, and “not tested” results for the actual engagement.

Passing this checklist does not turn Noesi into the audit or transfer the
auditor's responsibilities to the software.
