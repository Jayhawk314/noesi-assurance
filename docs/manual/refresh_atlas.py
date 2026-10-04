"""Refresh the code excerpts in "Noesi Audit Code Atlas.html" from the current source.

    python docs/manual/refresh_atlas.py          report only
    python docs/manual/refresh_atlas.py --write  rewrite the page

Each excerpt in the page's DATA block names a file, a symbol, a line range and its source. This
re-finds the symbol's definition in the current file, re-extracts it (Python by indentation, TypeScript
by braces), and updates line/start/end/total/src. It reports excerpts that changed, excerpts it could
not find, and highlight marks that no longer occur in the source. It never edits the prose.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = Path(__file__).resolve().parent / "Noesi Audit Code Atlas.html"


def py_block(lines, i):
    indent = len(lines[i]) - len(lines[i].lstrip())
    k = i
    while lines[k].lstrip().startswith("@"):       # decorators: the block starts at the def/class below
        k += 1
    j = k + 1
    while j < len(lines):
        s = lines[j]
        if s.strip() and (len(s) - len(s.lstrip())) <= indent and not s.lstrip().startswith((")", "]", "}")):
            break
        j += 1
    while j > i + 1 and not lines[j - 1].strip():
        j -= 1
    return j


def ts_block(lines, i):
    depth, seen = 0, False
    for j in range(i, len(lines)):
        for ch in lines[j]:
            if ch == "{":
                depth += 1; seen = True
            elif ch == "}":
                depth -= 1
        if seen and depth <= 0:
            return j + 1
        if not seen and j > i and lines[j].rstrip().endswith(";"):
            return j + 1
    return len(lines)


def verbatim(lines, item):
    """Where the excerpt still appears word for word (nearest its old start), else None."""
    old = item["src"].splitlines()
    if not old:
        return None
    hits = [i for i in range(len(lines) - len(old) + 1) if lines[i:i + len(old)] == old]
    if not hits:
        return None
    i = min(hits, key=lambda c: abs(c + 1 - item.get("start", c + 1)))
    return i, i + len(old)


def find(lines, item):
    exact = verbatim(lines, item)
    if exact:
        return exact
    sym, kind = item["symbol"], item["kind"]
    first = item["src"].splitlines()[0].strip() if item["src"] else ""
    cands = [i for i, s in enumerate(lines) if first and s.strip() == first]
    if not cands:
        pat = (re.compile(rf"^\s*(async\s+)?(def|class)\s+{re.escape(sym)}\b") if kind == "py" else
               re.compile(rf"(function\s+{re.escape(sym)}\b|\b{re.escape(sym)}\s*[:=(]|^\s*{re.escape(sym)}\s*\()"))
        cands = [i for i, s in enumerate(lines) if pat.search(s)]
    if not cands:
        return None
    i = min(cands, key=lambda c: abs(c + 1 - item.get("start", c + 1)))
    j = py_block(lines, i) if kind == "py" else ts_block(lines, i)
    return i, j


def main(write):
    html = PAGE.read_text(encoding="utf-8")
    a = html.index("const DATA = ") + len("const DATA = ")
    b = html.index(";\n", a)
    data = json.loads(html[a:b])
    changed, missing, badmarks, total = [], [], [], 0
    cache = {}
    for stop in data:
        for item in stop["items"]:
            if "path" not in item or "src" not in item:
                continue
            total += 1
            path = ROOT / item["path"]
            if not path.exists():
                missing.append(f"{item['path']} (file gone)"); continue
            lines = cache.setdefault(path, path.read_text(encoding="utf-8").splitlines())
            hit = find(lines, item)
            if not hit:
                missing.append(f"{item['path']}:{item['symbol']}"); continue
            i, j = hit
            src = "\n".join(lines[i:j])
            if src.splitlines() != item["src"].splitlines() or item.get("start") != i + 1:
                changed.append(f"{item['path']}:{item['symbol']} {item.get('start')}->{i + 1}"
                               + ("" if src.splitlines() == item["src"].splitlines() else " (source changed)"))
            item.update(line=i + 1, start=i + 1, end=j, total=j - i, src=src, truncated=0)
            for mk in item.get("marks", []):
                if mk not in src:
                    badmarks.append(f"{item['path']}:{item['symbol']} mark {mk!r}")
    print(f"{total} excerpts; {len(changed)} updated; {len(missing)} not found; {len(badmarks)} marks missing")
    for x in changed: print("  updated", x)
    for x in missing: print("  NOT FOUND", x)
    for x in badmarks: print("  MARK", x)
    if write:
        PAGE.write_text(html[:a] + json.dumps(data, ensure_ascii=False) + html[b:], encoding="utf-8")
        print("wrote", PAGE.name)
        copy_to_learn()
    return 1 if missing or badmarks else 0


def copy_to_learn():
    """The Workbench copy, at /kestrel/code-atlas.html (see atlas_copy.py)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from atlas_copy import write_learn_copy
    write_learn_copy(PAGE, ROOT)


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
