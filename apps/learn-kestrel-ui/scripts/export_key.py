# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Write the figures the Kestrel lessons show (src/learn/kestrel-key.json).

Every figure a lesson shows comes from here, never typed by hand. It runs the
finish-line check (case-studies/kestrel-valley-cycle/instructor/
finish_line_check.py): the Workbench demo seeded as ``--demo`` does, compared
line by line with answer_key*.json. It writes each line's key value, the
Workbench value and the status, plus the four key files themselves.

It refuses (exit 1) when a line differs or is unexplained, or when the
per-module counts disagree with FINISH-LINE-REPORT.md.

    .venv\\Scripts\\python apps\\learn-kestrel-ui\\scripts\\export_key.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INSTRUCTOR = ROOT / "case-studies" / "kestrel-valley-cycle" / "instructor"
OUT = HERE.parent / "src" / "learn" / "kestrel-key.json"
sys.path.insert(0, str(INSTRUCTOR))
import finish_line_check as flc  # noqa: E402


def show(value, key=None) -> str:
    """A value as the lesson prints it. A yes/no line reads as whether its
    label holds: the key's side always holds; the Workbench's holds when it
    gives the key's answer."""
    if value is flc.NOT_IN:
        return "—"
    if isinstance(key, bool):
        return "yes" if flc.same(key, value) else "no"
    if isinstance(value, (list, tuple, set, frozenset)):
        return ", ".join(str(v) for v in value) or "none"
    return str(value)


def report_counts() -> dict[str, tuple[int, int, int]]:
    text = (INSTRUCTOR / "FINISH-LINE-REPORT.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\| (\d+) \| ([^|]+) \| (\d+) \| (\d+) \| (\d+) \|$", text, re.M)
    return {name.strip(): (int(m), int(d), int(n)) for _, name, m, d, n in rows}


def main() -> int:
    svc, outcome = flc.seed()
    data = flc.gather(svc, outcome["engagement_id"])
    data["refused"] = outcome.get("refused", [])
    check = flc.compare(data)

    problems = [f"{r['module']}: {r['item']} ({r['status']}: {r['why']})" for r in check.rows
                if r["status"] == "differs" or r["why"].startswith("UNEXPLAINED")]
    modules: dict[str, list] = {m: [] for m in flc.MODULES}
    for r in check.rows:
        key, noesi = ("yes" if isinstance(r["key"], bool) else show(r["key"]),
                      show(r["got"], r["key"]))
        if r["item"].startswith("transfer "):
            # The label names a transfer, not a claim: say what each side found.
            verdict = lambda v: "exception" if v else "no exception"  # noqa: E731
            key = verdict(r["key"])
            noesi = "—" if r["got"] is flc.NOT_IN else verdict(r["got"])
        modules[r["module"]].append({
            "item": r["item"], "status": r["status"], "why": r["why"],
            "key": key, "noesi": noesi,
        })
    expected = report_counts()
    for name, rows in modules.items():
        got = tuple(sum(r["status"] == s for r in rows)
                    for s in ("match", "differs", "not in Noesi"))
        if expected.get(name) != got:
            problems.append(f"{name}: the check gives {got}, FINISH-LINE-REPORT.md "
                            f"{expected.get(name)}; re-run finish_line_check.py")
    if problems:
        print("Refused; the lessons would show figures the report does not:")
        print("\n".join(f"  {p}" for p in problems))
        return 1

    key = {name: json.loads((INSTRUCTOR / f"answer_key{suffix}.json").read_text(encoding="utf-8"))
           for name, suffix in (("part1", ""), ("payables", "_payables"),
                                ("part2", "_part2"), ("part3", "_part3"))}
    OUT.write_text(json.dumps({
        "source": "finish_line_check.py against answer_key*.json; do not edit, re-run "
                  "scripts/export_key.py",
        "modules": modules, "key": key}, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    total = sum(len(r) for r in modules.values())
    matched = sum(r["status"] == "match" for rows in modules.values() for r in rows)
    print(f"wrote {OUT.name}: {matched} of {total} lines match, as the report says")
    return 0


if __name__ == "__main__":
    sys.exit(main())
