# Noesi Assurance Workbench

Local-first AP procedure coverage and evidence workbench: a modular monolith
that compiles which audit procedures supplied data can honestly support,
records why the others cannot run, and produces a reproducible
evidence-linked workpaper.

**Not an audit, not an opinion, not professional advice.** Free for
noncommercial use (students, teaching, research); commercial use requires a
license — see [License, use, and professional
disclaimers](#license-use-and-professional-disclaimers).

This is the v2 product repository. The audit logic (procedure contracts,
coverage compiler, refusal semantics, review gates) was ported from the
`noesi-cpa` prototype; the product boundaries around it (identity,
persistence, evidence storage, API/UI) were rebuilt. **See
`docs/ARCHITECTURE.md` for the current system description** and
`docs/PRODUCTION-READINESS.md` for the tracked gap list between this pilot
and real-industry deployment — `docs/architecture/` is the historical
prototype assessment and porting notes, kept as record.

## Layout

```
apps/
  workbench-api/          # hardened localhost HTTP boundary (token, Origin,
                          # body limits, security headers; FastAPI swap-in
                          # planned for the firm-hosted profile)
  workbench-ui/           # dense review UI: React + TypeScript, six screens,
                          # served as static assets by workbench-api
packages/
  assurance-domain/       # pure entities, state machines, money, receipts,
                          # SAD, readiness, worker protocol — no I/O
  assurance-persistence/  # SQLite adapter, migrations, transactional spine
  assurance-artifacts/    # quarantine -> register -> promote evidence vault
  assurance-application/  # use cases behind the six screens, authorization
  procedures-ap/          # AP methodology: contracts, coverage, engines,
                          # structural layer, ingestion/mapping
  structural-adapters/    # owned ports of the KOMPOSOS-derived methods
                          # (authorship verified: docs/PROVENANCE.md)
tests/
  unit/
  golden/                 # frozen bundles captured from noesi-cpa (Phase 0)
docs/
  architecture/
```

Boundary rule: `assurance-domain` and `procedures-ap` import no framework,
database, or HTTP code. Adapters implement ports from the outside.

Further pieces (`assurance-workpapers`, out-of-process workers, the
TypeScript review UI) are split out only when a boundary earns it — not
preemptively.

## Development

Requires Python >= 3.10 and Node >= 20 (UI build only). (Developed and
independently reviewed on 3.10.11; an earlier ">= 3.12" floor here was
never exercised and overstated the requirement.)

```
python -m venv .venv
.venv\Scripts\python -m pip install -e packages/assurance-domain -e packages/structural-adapters ^
    -e packages/assurance-persistence -e packages/assurance-artifacts -e packages/procedures-ap ^
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
Data lives under `~/.noesi-assurance` (control DB, evidence vault,
signing keys).

### First five minutes

```
.venv\Scripts\noesi-workbench --demo
```

`--demo` seeds a fully loaded engagement from the Harborline Marine teaching
case (836 rows across ten record sets, loaded through the real three-chair
review path, with the split-payment policies approved). Open it, press "run"
on any procedure, and read what the engine found — and refused to claim.

### One operator, several chairs

Separation of duties is enforced server-side: whoever proposes a mapping
cannot approve it, whoever runs a procedure cannot review it, and only the
partner locks. On a single laptop you play every part — the **acting as**
control in the header switches which chair you sit in (the demo comes with
`demo-preparer` and `demo-reviewer`; the Team screen adds more). Every action
is journaled under the chair that performed it and appears that way on the
signed workpaper. This is the pilot's honest trust model: the console owner
already controls every local identity, so the switcher changes convenience,
not the security boundary. A firm-hosted profile with real per-person
sessions replaces it.

### Locking, reopening, and the amendment record

Locking freezes a signed manifest of every covered entity, anchored to the
hash-chained journal. Reopening a locked engagement follows the professional
rule for changes after file assembly (AU-C 230 / PCAOB AS 1215): nothing is
ever deleted. Unlock **supersedes** the lock — the partner must give a
specific reason, which enters the journal permanently; the superseded
snapshot, its signature, and its journal anchor stay verifiable forever; work
after reopening passes through the same preparer/reviewer/partner gates; and
the next lock signs a manifest that names its predecessor and the reason it
was reopened. Evidence packets carry the full amendment history, and
`verify_packet` re-verifies every superseded lock offline along with the
active one.

### The manual and the teaching case

`docs/manual/` is a working textbook that teaches the audit process and the
workbench together — every chapter pairs what professional standards require
(**in practice**) with the concrete steps in the tool (**in the workbench**)
and the running example (**in Harborline**). The workbench serves it
rendered: the **📖 manual** button in the header, from any screen — so a
student never leaves the tool to look up why a gate refused them.

`case-studies/harborline-marine/` is the complete instructor-ready case
behind it: generated data with 40 planted exceptions, spreadsheet-first
student assignments, workpaper templates, and an answer key.
`instructor/verify_run.py` re-runs the whole case headlessly and prints
every finding for reconciliation against the key.

## Reference repository

`../noesi-cpa` is read-only reference material: golden-bundle capture runs
there; ported code is copied from there. No new features land there.

## License, use, and professional disclaimers

Copyright (c) 2026 James Hawkins. Licensed under the **PolyForm Noncommercial
License 1.0.0** — see [LICENSE.md](LICENSE.md). In plain terms: personal
study, teaching, research, and use by noncommercial organizations (including
classroom use of the Harborline case) are free; **any commercial use —
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
  practitioners who make them, exactly as the workbench's own review gates
  assume.
- **No warranty.** The software comes as is, without warranty or condition
  of any kind; see the "No Liability" section of LICENSE.md.

The references to AU-C, AS, and other standards in the manual and in code
comments explain the design intent; they are not claims of compliance with,
or endorsement by, the AICPA, PCAOB, or any other body.
