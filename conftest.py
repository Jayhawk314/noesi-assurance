# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Test path setup: make the workspace packages importable without installs.

Once a project venv exists, `pip install -e packages/...` replaces this; the
inserts are harmless no-ops when the packages are already installed.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
for pkg in sorted((_ROOT / "packages").iterdir()):
    src = pkg / "src"
    if src.is_dir() and str(src) not in sys.path:
        sys.path.insert(0, str(src))
for app in sorted((_ROOT / "apps").iterdir()):
    if app.is_dir() and str(app) not in sys.path:
        sys.path.insert(0, str(app))
