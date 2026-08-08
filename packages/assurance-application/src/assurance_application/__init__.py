# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Application layer: the use cases the workbench API exposes.

Every mutation is a command through the transactional spine, authorized
against principal assignments server-side. Display names are never
authorization inputs. Datasets are rebuilt from immutable artifacts through
approved mapping specs and digest-verified on every rebuild — reperformance
is the read path, not a special feature.
"""
