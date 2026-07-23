# Phase 5 scoping: signed locking

## Built (pilot profile)

- **Hash-chained event journal**: every accepted command's event links to
  its predecessor (`prev_hash`/`entry_hash`); `verify_journal` recomputes
  the whole chain, and a broken chain raises the `DECISION_TRAIL_BROKEN`
  readiness blocker automatically.
- **Lock snapshot manifests**: locking freezes a deterministic manifest of
  every covered entity — engagement, workflow document digest, artifact
  digests, mapping specs, dataset receipts, run receipts, dispositions,
  team — plus the journal head, in the same transaction as the status
  change.
- **Ed25519 signatures with device-bound keys**: one key per principal,
  created on first use (`assurance_artifacts/signing.py`); key id is the
  SHA-256 of the public key; verification material is stored beside the
  signature so a packet verifies with no key-store access.
- **Honest claims, stated in the manifest itself**: the signature proves
  which principal's device key approved exactly this byte set and when the
  local signer recorded it — not that the accounting source was complete
  or authentic, and not trusted time.
- **Verification as a use case and endpoint** (`verify_lock`,
  `GET /api/engagements/{id}/lock`): re-derives the manifest from current
  rows, reports per-section drift, verifies the signature from stored
  material, and re-walks the journal chain against the recorded head.
- **Locked means locked**: every mutation use case refuses on a locked
  engagement (HTTP 423); unlock-with-supersession is future work and will
  be an explicit, journaled, re-signed act.

## Deferred (firm profile; revisit before shared hosting)

- **SSO/OIDC principals and MFA** — the pilot principal is the local
  session identity; the service's role matrix is already keyed by opaque
  principal ids, so the swap is additive.
- **Trusted time / external anchoring** of snapshot digests — buyers'
  requirements decide the anchor (customer-controlled store vs witness).
- **PostgreSQL + object-store adapters, row-level security** — the
  repository layer is the seam; SQLite remains the single-writer pilot
  store.
- **Key passphrases / OS keychain integration** — pilot assumes an
  OS-encrypted single-user disk.
- **Threat modeling, penetration testing, restore drills, dependency
  review** — required release gates before any firm deployment; not
  meaningfully performable against a pilot that changes weekly.

## Note on journal history

Events written before migration 4 carry empty hashes; the chain and its
verification start at the first hashed event. Fresh databases chain
everything from the first command.
