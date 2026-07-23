# Noesi Assurance Workbench

Local-first AP procedure coverage and evidence workbench: a modular monolith
that compiles which audit procedures supplied data can honestly support,
records why the others cannot run, and produces a reproducible
evidence-linked workpaper.

This is the v2 product repository. The audit logic (procedure contracts,
coverage compiler, refusal semantics, review gates) is being ported from the
`noesi-cpa` prototype; the product boundaries around it (identity,
persistence, evidence storage, API/UI) are being rebuilt. See
`docs/architecture/` for the full assessment and target design.

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

Requires Python >= 3.12 (plus `cryptography`) and Node >= 20 for the UI.

```
python -m venv .venv
.venv\Scripts\activate
pip install -e packages/assurance-domain -e packages/assurance-persistence -e packages/procedures-ap
pip install pytest cryptography
pytest
```

## Running the workbench

```
cd apps/workbench-ui && npm install && npm run build && cd ../..
python -m workbench_api            # prints the session token
```

Open http://127.0.0.1:8347/ and paste the token. Data lives under
`~/.noesi-assurance` (control DB, evidence vault, signing keys).

## Reference repository

`../noesi-cpa` is read-only reference material: golden-bundle capture runs
there; ported code is copied from there. No new features land there.
