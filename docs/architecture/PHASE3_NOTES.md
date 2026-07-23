# Phase 3 scoping: ingestion and the evidence vault

What the assessment's Phase 3 requires versus what the encrypted-local pilot
profile actually needs now. Deferrals are explicit so they cannot silently
become permanent.

## Built

- **Streamed quarantine intake** (`assurance-artifacts/vault.py`): bytes are
  hashed and size/type-policed while streaming; an over-limit upload is cut
  off mid-stream, never buffered whole (replaces the prototype's
  base64-in-JSON upload, P1).
- **Write-once content-addressed store**: promotion is idempotent by
  content; a blob address can never be overwritten with different bytes;
  every read re-verifies the digest and refuses tampered evidence.
- **Stage → register → promote ordering** (`intake.py`): the database
  accepts the artifact manifest inside one command transaction *before*
  bytes are promoted (assessment P0); failures discard the staged copy;
  a crash between commit and promote is retryable because promotion is
  content-idempotent.
- **Explicit retention**: retirement tombstones the manifest first, then
  removes bytes; the event journal records both.
- **Reviewed transformation model** (`procedures_ap/ingest.py` +
  `mapping_spec` table): header detection produces a *proposal*; a
  different principal approves it (separation enforced server-side in the
  repository, not the UI); only approved specs can normalize.
- **Normalization receipts**: rejected-row quarantine with reasons,
  duplicate-key and null-amount diagnostics, row-count and Decimal
  control-total reconciliation, content-addressed output digest —
  persisted per dataset in `normalized_dataset`.

## Deferred (firm-deployment concerns, revisit before any shared hosting)

- **Encryption at rest / engagement-scoped data keys** — pilot runs on a
  single-user machine with OS-level disk encryption assumed.
- **Malware scanning and MIME sniffing** — declared media type is policed;
  content sniffing needs a scanner dependency the pilot does not carry.
- **Quotas, backup/restore verification, legal holds** — with the explicit
  retention events as the hook they will attach to.
- **Source-system connector interfaces** — CSV export intake first; the
  pilot will reveal which ERPs matter.
- **Parquet + DuckDB analytics** — normalized datasets are held as canonical
  JSON-safe rows with digests; the analytical store lands when scan volume
  demands it. The dataset receipt schema will not change.

## Divergence note (D8)

Normalized records store Decimal amounts and real dates (the doc's
"preserve parsed decimal" requirement). The float-era golden
(`ingest_mapping.json`) is compared through an explicit float/isoformat
projection; `NormalizedTable.engine_view()` provides the same projection
for the float-parity screening layer (D7).
