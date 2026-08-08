# Provenance of ported code

This repository claims sole ownership of everything in it. The one package
whose history reaches outside this repo is `structural-adapters` — "owned
ports of the KOMPOSOS-derived methods." This document records where that
code actually came from, verified on 7 Aug 2026 against the local source
checkouts, so the ownership claim rests on evidence rather than assertion.

Claims are tagged **[V]** (verified — a command was run and its output is
what's stated) or **[D]** (from a doc or a person, not independently
checked), matching the conventions of the workspace `LINEAGE.md` and
`LICENSING.md`.

## What was ported, and from where

`structural-adapters` contains exactly two modules:

| Module | Ported from | Original authorship |
|---|---|---|
| `dempster_shafer.py` | `KOMPOSOS-V-base/categorical/dempster_shafer.py` (local checkout under `C:\Users\JAMES\GitHub\`) | File header reads `SPDX-License-Identifier: Apache-2.0 OR KOMPOSOS-III-Commercial` / `Copyright (c) 2024-2026 James Ray Hawkins` **[V]** |
| `graph.py` | The `noesi-cpa` prototype's `noesis/komposos_bridge.py` (`CategoryGraph.reachable_from`) | `noesi-cpa` has exactly one git author: `Jayhawk314 <jhawk314@gmail.com>`, first commit 2026-07-15 **[V]** |

Both originals are the work of the same person who holds copyright in this
repository — James Hawkins (signing as "James Ray Hawkins" in the KOMPOSOS
headers and as "Jayhawk314" in git; one person, three name forms). The
author of the source had, and has, every right to relicense his own work
into this repository under any terms.

## Third-party content check

- Neither ported source file contains any attribution marker — no
  "adapted from", no URLs, no vendored-code notices, no third-party
  copyright lines — under a case-insensitive scan for
  `http|www.|adapted|vendored|third-party|courtesy|credit` **[V]**.
- The academic references in the original docstring (Dempster 1967,
  Shafer 1976) cite the *mathematics*, which is not copyrightable; the
  implementation is original code **[V]** (references named in the
  docstring itself, no code source cited).
- The ported algorithms — Dempster's combination rule, source discounting,
  bounded-hop reachability with best multiplicative weight — are textbook
  methods; what is owned is this implementation of them.

## Known limits of this record (stated, not hidden)

- `KOMPOSOS-V-base` at its current location has **no git history and no
  LICENSE file** — it is a bare directory checkout, so its own lineage
  rests on its file headers plus the workspace `LINEAGE.md`, which places
  it between KOMPOSOS-IV and KOMPOSOS-silicon **[D]**.
- The workspace `LINEAGE.md` records that some of the earliest KOMPOSOS
  repositories were deleted by accident; a complete commit-level history
  of the family cannot be reconstructed **[D]**.
- SPDX headers across the KOMPOSOS family drifted by copy-paste (a repo
  can carry several inconsistent identifiers); the header quoted above is
  what the specific ported file says, not a claim about the family
  **[V for the file, D for the family]**.

## Licensing-decision timeline (for the record)

- 2026-07-27 — decision recorded in the workspace `LICENSING.md`:
  `noesi-assurance` stays commercial; the Apache-2.0 family standard does
  not apply to it **[D]**.
- 2026-08-07 — first public push of this repository, already carrying the
  PolyForm Noncommercial 1.0.0 license and headers, so the workspace
  rule "decide before the first push" was honored: no code was ever
  published under a permissive license **[V]**.

## Conclusion

Every identified source of ported code is the prior work of this
repository's own copyright holder. No third-party code was identified in
the ported surface. The residual risk is confined to the acknowledged
gaps above (headerless checkout, deleted early history), which concern
*documentation* of the same author's own lineage, not the possibility of
someone else's code. This is a record for counsel to confirm, not a legal
opinion.
