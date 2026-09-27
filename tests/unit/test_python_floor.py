# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The README's supported Python matches every package's metadata (review RR2)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_readme_python_floor_matches_package_metadata():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    stated = re.search(r"Requires Python >= (\d+\.\d+)", readme)
    assert stated, "README no longer states a Python floor"
    manifests = list(ROOT.glob("packages/*/pyproject.toml")) + \
        list(ROOT.glob("apps/*/pyproject.toml"))
    assert manifests
    for manifest in manifests:
        floor = re.search(r'requires-python\s*=\s*">=(\d+\.\d+)"',
                          manifest.read_text(encoding="utf-8"))
        assert floor and floor.group(1) == stated.group(1), manifest
