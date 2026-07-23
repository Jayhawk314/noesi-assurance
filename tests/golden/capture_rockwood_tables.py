"""Supplementary Phase 0 capture: the parsed Rockwood tables.

The ACL binary reader is prototype-only (real clients export CSVs), so the
v2 port's input boundary is the parsed tables, not the .fil files. This
captures ``rockwood.read_tables(...)`` output as JSON with explicit
``{"$date": "YYYY-MM-DD"}`` markers so hydration restores exactly the types
the engines saw — no guessing about which strings were dates.

Run with the noesi-cpa venv from the noesi-cpa checkout root:

    .venv/Scripts/python.exe C:/Users/JAMES/github/noesi-assurance/tests/golden/capture_rockwood_tables.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path

BUNDLES = Path(__file__).resolve().parent / "bundles"
CPA_ROOT = Path(r"C:\Users\JAMES\github\noesi-cpa")


def mark(value):
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    if isinstance(value, dict):
        return {str(k): mark(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [mark(v) for v in value]
    return value


def main() -> int:
    sys.path.insert(0, str(CPA_ROOT))
    from noesis.audit.rockwood import read_tables

    acl = CPA_ROOT / ("data/external/audit/acl_sample/extracted/"
                      "ACL_Rockwood/ACL_Rockwood.ACL")
    tables = read_tables(str(acl))
    payload = {
        "source": str(acl.relative_to(CPA_ROOT)),
        "tables": {
            name: {
                "records": [mark(dict(r)) for r in table.records],
                "refused_fields": sorted(getattr(table, "refused_fields", ())),
                "column_map": dict(getattr(table, "column_map", {}) or {}),
                "control_total": getattr(table, "control_total", None),
                "source_file": str(getattr(table, "source_file", "") or ""),
                "rows": len(table.records),
            }
            for name, table in sorted(tables.items())
        },
    }
    BUNDLES.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    # Stored gzipped only: the raw JSON is ~185 MB and regenerable.
    import gzip
    with gzip.open(BUNDLES / "rockwood_tables.json.gz", "wt",
                   encoding="utf-8", compresslevel=9) as fh:
        fh.write(text)

    digest = hashlib.sha256(json.dumps(
        json.loads(text), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, default=str).encode("utf-8")).hexdigest()
    manifest_path = BUNDLES / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["bundles"] = [entry for entry in manifest["bundles"]
                           if entry["file"] != "rockwood_tables.json"]
    manifest["bundles"].append(
        {"file": "rockwood_tables.json", "sha256": digest})
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    total = sum(t["rows"] for t in payload["tables"].values())
    print(f"captured {len(payload['tables'])} tables, {total} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
