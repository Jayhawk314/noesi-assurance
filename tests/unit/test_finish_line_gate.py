# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The finish-line check's gate: a known difference passes only while the
Workbench still gives the exact value it was pinned at."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = (Path(__file__).resolve().parents[2] / "case-studies" / "kestrel-valley-cycle"
          / "instructor" / "finish_line_check.py")


@pytest.fixture(scope="module")
def flc():
    spec = importlib.util.spec_from_file_location("finish_line_check_gate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not SCRIPT.is_file(), reason="case not in tree")
def test_a_known_difference_fails_when_its_value_moves(flc):
    c = flc.Check()
    c("pinned, unchanged", "1.01", "0.99", "known reason", expect="0.99")
    c("pinned, value moved", "1.01", "999", "known reason", expect="0.99")
    c("reason but nothing pinned", "1.01", "999", "known reason")
    c("no reason", "1.01", "999")
    c("pinned as not produced, still not", True, flc.NOT_IN, "known", expect=flc.NOT_IN)
    c("pinned as not produced, now produced", True, False, "known", expect=flc.NOT_IN)
    c("matches", "1.01", "1.0100")
    why = {r["item"]: r["why"] for r in c.rows}
    assert why["pinned, unchanged"] == "known reason"
    assert why["pinned as not produced, still not"] == "known"
    assert why["matches"] == ""
    for item in ("pinned, value moved", "reason but nothing pinned", "no reason",
                 "pinned as not produced, now produced"):
        assert why[item].startswith("UNEXPLAINED"), item
