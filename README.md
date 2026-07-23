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
packages/
  assurance-domain/       # pure entities, state machines, commands — no I/O
  assurance-persistence/  # SQLite adapter, migrations, transactional journal
  procedures-ap/          # AP methodology contracts + deterministic engines
tests/
  unit/
  golden/                 # frozen input/output bundles captured from noesi-cpa
docs/
  architecture/
```

Boundary rule: `assurance-domain` and `procedures-ap` import no framework,
database, or HTTP code. Adapters implement ports from the outside.

Further packages (`assurance-artifacts`, `assurance-execution`,
`assurance-workpapers`, apps, workers) are split out only when a boundary
earns it — not preemptively.

## Development

Requires Python >= 3.12.

```
python -m venv .venv
.venv\Scripts\activate
pip install -e packages/assurance-domain -e packages/assurance-persistence -e packages/procedures-ap
pip install pytest
pytest
```

## Reference repository

`../noesi-cpa` is read-only reference material: golden-bundle capture runs
there; ported code is copied from there. No new features land there.
