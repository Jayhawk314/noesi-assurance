# Noesi Assurance Workbench

Local-first audit procedure and evidence workbench: a modular monolith that
tests supplied data across audit cycles, including fraud and forensic work,
records what it could not test, and produces an evidence-linked record.

**Not an audit, not an opinion, not professional advice.** Free for
noncommercial use (students, teaching, research); commercial use requires a
license — see [License, use, and professional
disclaimers](#license-use-and-professional-disclaimers).

This is the product repository. The audit logic (procedure contracts,
coverage compiler and explicit refusals) grew from the `noesi-cpa` prototype;
the persistence, evidence storage, API and UI were rebuilt. The Workbench
supplements a complete human audit: it has one user per engagement and no
approval or sign-off workflow. See the [roadmap](docs/ROADMAP.md) for the product
direction and [production readiness](docs/PRODUCTION-READINESS.md) for the remaining
local-use gaps. `docs/ARCHITECTURE.md` and `docs/architecture/` contain older
design descriptions and must be checked against the current code.

## Layout

```
apps/
  workbench-api/          # localhost HTTP boundary (token, Origin,
                          # body limits, security headers)
  workbench-ui/           # review UI: React + TypeScript,
                          # served as static assets by workbench-api
  studio-ui/              # visual practitioner view and Harborline Learn,
                          # served at /studio/
  learn-streamlit/        # hosts Harborline Learn on Streamlit (static)
  learn-kestrel-ui/       # separate public Kestrel Learn course
  learn-kestrel-streamlit/ # hosts Kestrel Learn on Streamlit (static)
packages/
  assurance-domain/       # pure entities, money, receipts, SAD, readiness,
                          # worker protocol — no I/O
  assurance-persistence/  # SQLite adapter, migrations, transactional spine
  assurance-artifacts/    # quarantine -> register -> promote evidence vault;
                          # the .xlsx reader
  assurance-application/  # use cases behind the screens, backup and restore
  assurance-workpapers/   # unsigned record verification and workpaper
  procedures-ap/          # AP methodology: contracts, coverage, engines,
                          # structural layer, ingestion/mapping, QuickBooks
                          # report recipes
  procedures-cycles/      # planning, controls, journal entries, receivables,
                          # payroll, forensic, cash, inventory, PP&E, debt,
                          # accruals, estimates and completion procedures
  structural-adapters/    # owned ports of the KOMPOSOS-derived methods
                          # (authorship verified: docs/PROVENANCE.md)
tests/
  unit/
  fixtures/               # real client-style files: an Excel register and
                          # QuickBooks Online report exports
  golden/                 # frozen bundles captured from noesi-cpa (Phase 0)
case-studies/
  kestrel-valley-cycle/   # the full-cycle QuickBooks-shaped teaching case
  harborline-marine/      # the frozen AP regression case and legacy course
docs/
  manual/                 # the textbook, served in the workbench
  learn/                  # Learn course plan and research notes
  architecture/           # historical prototype assessment, kept as record
```

Boundary rule: `assurance-domain` and `procedures-ap` import no framework,
database, or HTTP code. Adapters implement ports from the outside.

Further pieces are split out only when a boundary earns it.

## Development

Requires Python >= 3.12 and Node >= 20 (UI build only). Every package
declares `requires-python = ">=3.12"`.

```
python -m venv .venv
.venv\Scripts\python -m pip install -e packages/assurance-domain -e packages/structural-adapters ^
    -e packages/assurance-persistence -e packages/assurance-artifacts -e packages/procedures-ap ^
    -e packages/procedures-cycles ^
    -e packages/assurance-application -e packages/assurance-workpapers -e apps/workbench-api
.venv\Scripts\python -m pip install pytest
.venv\Scripts\python -m pytest tests\unit
```

## Running the workbench

One-time UI build, then a one-liner:

```
cd apps\workbench-ui && npm install && npm run build && cd ..\..
.venv\Scripts\noesi-workbench
```

Open the address it prints — the served page carries its own session token.
Data lives under `~/.noesi-assurance` (control DB, evidence vault).

### First five minutes

```
.venv\Scripts\noesi-workbench --demo
```

`--demo` seeds and runs a Kestrel Valley Cycle Supply engagement through the
same service path as the Workbench: QuickBooks-shaped reports, client and
auditor schedules, engagement policies, confirmed mappings, and the selected
procedures those inputs support. Open the completed runs and read what the
engine found and what coverage could not test.

### Loading a client's files

Upload CSV or Excel (.xlsx) exports in **Sources & Mappings**. For a
workbook you choose the sheet and the heading row; the choice becomes part
of the confirmed mapping. Standard **QuickBooks Online** report exports
(Bill Payment List, Transaction List by Vendor, Unpaid Bills, Vendor
Contact List) are recognized on upload and read by a recipe that flattens
the report's groups and recomputes every subtotal before dropping it.
With Unpaid Bills and either a General Ledger export or a loaded trial balance,
the Workbench can build the AP subledger-to-ledger tie. What an export does
not contain is refused, not invented. Manual chapter 3 explains each step.

### One user per engagement

The session user maps, confirms, and loads files, runs procedures, records
judgments, and exports the record. Confirming a mapping checks that its
columns were understood; it is not an approval. Actions are journaled under
the session's principal label, which is not proof of a person's identity.
Noesi does not perform the firm's review or sign-off.

### The exported record

The record exports at any time as one JSON file: a manifest of every
entity (file digests, mappings, datasets, runs, dispositions, risks,
journal position), every run with its findings and digests, the SAD,
readiness, scope and the draft opinion. Each export is journaled with its
digest. `verify_packet` re-checks it offline. It is not signed: the digests
show it is internally consistent, not who made it; the firm archives it
like any other working paper.

### Back up and restore

The backup command captures the control database and the vault files named
by it in one zip. Run these commands with the Workbench installed; restore
to a new directory while that destination is offline:

```text
python -m workbench_api.backup create --data DIR --to FILE
python -m workbench_api.backup verify FILE
python -m workbench_api.backup restore FILE --data NEW_DIR
```

Start the Workbench with `--data NEW_DIR` to open the restored store. Backup
files are not encrypted or signed by Noesi; use encrypted storage and verify
a restore before relying on a backup. See [production readiness](docs/PRODUCTION-READINESS.md)
for the recovery limits.

### The manual and the teaching case

`docs/manual/` is a working textbook that teaches the audit process and the
workbench together — every chapter pairs what professional standards require
(**in practice**) with the concrete steps in the tool (**in the workbench**)
and the running example (**in Kestrel**). The workbench serves it
rendered: the **📖 manual** button in the header, from any screen — so a
student never leaves the tool to look up why a gate refused them.

`case-studies/kestrel-valley-cycle/` is the full-cycle case behind it:
QuickBooks-shaped exports, client and auditor schedules, independently
computed answer keys, and headless checks that rederive the expected figures.
The frozen Harborline case remains as the AP engine's regression fixture and
the source for the legacy Studio course; it is not the manual's running case.

## Reference repository

`../noesi-cpa` is read-only reference material: golden-bundle capture runs
there; ported code is copied from there. No new features land there.

## Workbench views and separate Learn apps

`noesi-workbench` serves two UIs over the same API and the same journaled
commands:

- **Workbench** (`/`) — the full-control instrument and teaching surface,
  including the manual.
- **Studio** (`/studio/`) — the visual practitioner view: a seven-stage journey
  read straight off the record, a "next step" card, the purchase-to-pay cycle
  drawn with each test's result, exceptions
  judged in plain words, the SAD against a materiality ruler, and a cascade of
  what a corrected client file reaches. Build it with
  `cd apps/studio-ui && npm install && npm run build`.

**Revised evidence.** When a client replaces a file, `GET
/api/engagements/{id}/impact` (the **What Changed** tab in both UIs) compares
the old and new versions, names the runs whose inputs moved, reperforms them in
memory, and shows which findings appear, disappear or move and which recorded
judgments to revisit. It is read-only: it records nothing and concludes nothing
about misstatement. Harborline's Assignment 11 exercises it.

**Harborline Learn** (`/studio/#/learn`) is a ten-lesson course through a typical
CPA financial-statement audit, from client acceptance to the report, taught on
the Harborline case. Each lesson reveals section by section, checks
understanding with explained questions, sets a hands-on task, and ends with an
**In Noesi** reminder: what the system does for that step, where, and what it
does not do. The course needs no session. Its plan, research notes and sources
are in `docs/learn/CURRICULUM.md`. A separate **Fraud in payables** track
(`/studio/#/learn/fraud`) aligns with the CFE exam; its first four lessons are
written and its plan is `docs/learn/FRAUD-MODULE-OUTLINE.md`.

**The documents** (`/studio/#/learn/documents`) renders the paper trail an
auditor reads: one real Harborline purchase (PO-2026-0009) traced from order to
ledger, the AP tie-out and a year-end bank reconciliation built from the case
data, plus illustrative confirmations, a count sheet and a representation
letter. Numbered markers point at each figure to check, with the assertion it
evidences and the Noesi test that compares it.

**Kestrel Learn** (`apps/learn-kestrel-ui`, with a separate Streamlit host in
`apps/learn-kestrel-streamlit`) is a distinct public course built on the
Kestrel Valley case. It is not the Studio journey or Harborline Learn. The
Workbench remains the audit-supplement product; both Learn apps teach with
case material.

## License, use, and professional disclaimers

Copyright (c) 2026 James Hawkins. Licensed under the **PolyForm Noncommercial
License 1.0.0** — see [LICENSE.md](LICENSE.md). In plain terms: personal
study, teaching, research, and use by noncommercial organizations (including
classroom use of the included teaching cases) are free; **any commercial use —
including use on client engagements — requires a separate commercial license
from the copyright holder** (jhawk314@gmail.com).

Say plainly what this software is not:

- **It is not an audit.** Running its procedures does not constitute an
  audit, a review, or any assurance engagement under any professional
  standard.
- **It produces no opinion.** Its outputs — findings, coverage, readiness,
  workpapers, evidence packets — are records of mechanical checks over the
  data supplied, not audit opinions or professional conclusions. The
  "report implication" language describes what a practitioner would have to
  consider; it decides nothing.
- **It is not professional advice.** Nothing in this software, its manual,
  or its teaching case is accounting, auditing, legal, or tax advice.
  Professional judgments remain the responsibility of the licensed
  practitioners who make them.
- **No warranty.** The software comes as is, without warranty or condition
  of any kind; see the "No Liability" section of LICENSE.md.

The references to AU-C, AS, and other standards in the manual and in code
comments explain the design intent; they are not claims of compliance with,
or endorsement by, the AICPA, PCAOB, or any other body.
