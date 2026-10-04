"""Add a lesson-by-lesson section to "Noesi Audit Code Atlas.html", built only from sources.

    python docs/manual/build_atlas_lessons.py

One stop per Kestrel Learn lesson (13 modules, 9 fraud lessons). Nothing is written by hand:
- the question, the by-hand steps, the "in Noesi" steps and "what Noesi cannot do" come from the
  lesson files (apps/learn-kestrel-ui/src/learn/lessons.ts, lessons-fraud.ts), read through esbuild;
- each procedure the lesson names is resolved through the engines' registries (EXECUTORS), and its
  real source, file and line numbers are read with inspect; its note is the procedure contract's
  objective and limitations (contracts.py);
- "What the key checks" lists the lesson's answer-key lines from kestrel-key.json.
Rerun after any change to the lessons, the key or the code. Procedures a lesson names that are
screens, not registered procedures (Coverage, SAD & Completion), are listed in the In Noesi text only.
"""
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = Path(__file__).resolve().parent / "Noesi Audit Code Atlas.html"
APP = ROOT / "apps" / "learn-kestrel-ui"
for src in (ROOT / "packages").glob("*/src"):
    sys.path.insert(0, str(src))

from procedures_ap import contracts as ap_contracts  # noqa: E402
from procedures_ap import engines as ap_engines  # noqa: E402
from procedures_cycles import contracts as cy_contracts  # noqa: E402
from procedures_cycles import engines as cy_engines  # noqa: E402

DUMP = r"""
import { createRequire } from "node:module";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
const app = process.cwd();
const require = createRequire(join(app, "package.json"));
const { build } = await import(pathToFileURL(require.resolve("esbuild")).href);
async function load(file, name) {
  const out = await build({ entryPoints: [join(app, "src/learn", file)], bundle: true, write: false,
                            format: "esm", platform: "neutral" });
  return (await import("data:text/javascript;base64," + Buffer.from(out.outputFiles[0].text).toString("base64")))[name];
}
const m = await load("lessons.ts", "LESSONS"), f = await load("lessons-fraud.ts", "FRAUD_LESSONS");
process.stdout.write(JSON.stringify({ modules: m, fraud: f }));
"""


def plain(text):
    """Lesson markdown to plain text: **bold**, `code` and [links](...) lose their marks."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(text))
    return text.replace("**", "").replace("`", "")


def lessons():
    out = subprocess.run(["node", "--input-type=module", "-e", DUMP], cwd=APP, capture_output=True,
                         text=True, encoding="utf-8", check=True, shell=False)
    return json.loads(out.stdout)


def procedure_item(pid, registry, contracts):
    fn = registry[pid]
    path = Path(inspect.getsourcefile(fn)).resolve().relative_to(ROOT).as_posix()
    lines, start = inspect.getsourcelines(fn)
    src = "".join(lines).rstrip("\n")
    c = contracts.get(pid)
    note = (f"{c.name}. {c.objective} Limits: {c.limitations}" if c and c.limitations
            else f"{c.name}. {c.objective}" if c else pid)
    return {"layer": "engine", "path": path, "symbol": f"{pid} → {fn.__name__}", "kind": "py",
            "line": start, "start": start, "end": start + len(lines) - 1, "total": len(lines),
            "truncated": 0, "doc": inspect.getdoc(fn) or "", "src": src, "note": note, "marks": []}


def key_lines(lesson, key, fraud):
    if fraud:
        pairs = lesson.get("keyLines") or []
        rows = [(m, i) for m, i in pairs]
    else:
        rows = [(lesson["keyModule"], r["item"]) for r in key["modules"].get(lesson["keyModule"], [])]
    out = []
    for module, item in rows:
        row = next((r for r in key["modules"].get(module, []) if r["item"] == item), None)
        if row is not None:
            out.append(f"{item}: {row['key']}" + ("   (not in Noesi)" if row["status"] == "not in Noesi" else ""))
    return out


def main():
    key = json.loads((APP / "src" / "learn" / "kestrel-key.json").read_text(encoding="utf-8"))
    registry = {**cy_engines.EXECUTORS, **ap_engines.EXECUTORS}
    contracts = {**ap_contracts.CONTRACTS_BY_ID, **cy_contracts.CYCLE_CONTRACTS_BY_ID}
    data = lessons()
    stops, skipped = [], []
    for fraud, group in ((False, data["modules"]), (True, data["fraud"])):
        for l in group:
            label = f"F{l['n']}" if fraud else f"M{l['n']}"
            procs = l["inNoesi"]["procedures"]
            items = [procedure_item(p, registry, contracts) for p in procs if p in registry]
            skipped += [f"{label}: {p}" for p in procs if p not in registry]
            hand = l["byHand"]
            steps = [plain(s) for s in l["inNoesi"]["steps"] if not s.startswith("Start the Workbench")]
            keys = key_lines(l, key, fraud)
            stops.append({
                "n": (200 if fraud else 100) + l["n"], "label": label, "lesson": True,
                "t": l["title"], "ch": ("Fraud lesson " if fraud else "Module ") + str(l["n"]),
                "ask": l["question"],
                "xl": plain(hand.get("intro", "")) + " " + " ".join(f"({i}) {plain(s)}" for i, s in enumerate(hand["steps"], 1)),
                "nx": " ".join(steps) + (f" Screens: {', '.join(p for p in procs if p not in registry)}." if any(p not in registry for p in procs) else ""),
                "mathLabel": "What the key checks",
                "math": "\n".join(keys[:14]) + (f"\n… and {len(keys) - 14} more lines" if len(keys) > 14 else "") if keys else "(no key lines)",
                "limit": " ".join(plain(x) for x in l["noesi"]["doesNot"]),
                "items": items,
            })
    html = PAGE.read_text(encoding="utf-8")
    block = "const LESSON_STOPS = " + json.dumps(stops, ensure_ascii=False) + ";\n"
    if "const LESSON_STOPS = " in html:
        a = html.index("const LESSON_STOPS = "); b = html.index(";\n", a) + 2
        html = html[:a] + block + html[b:]
    else:
        html = html.replace("const META = ", block + "const META = ", 1)
        # render: the ten stops, then the lessons in their own line, from the same template
        swaps = [
            ('document.getElementById("line").innerHTML = DATA.map(s => `', "const stationHTML = s => `"),
            ('<div class="stop" aria-hidden="true">${s.n}</div>', '<div class="stop" aria-hidden="true">${s.label || s.n}</div>'),
            ("<b>The maths</b>", '<b>${s.mathLabel || "The maths"}</b>'),
            ("</article>`).join(\"\");",
             "</article>`;\n"
             "document.getElementById(\"line\").innerHTML = DATA.filter(s => !s.lesson).map(stationHTML).join(\"\");\n"
             "document.getElementById(\"line2\").innerHTML = DATA.filter(s => s.lesson).map(stationHTML).join(\"\");"),
            ("// Items in each stop are shown in layer order: that is the route.",
             "DATA.push(...LESSON_STOPS);\n// Items in each stop are shown in layer order: that is the route."),
            ("<span><b>10</b> stops</span>",
             "<span><b>${DATA.filter(s => !s.lesson).length}</b> stops</span><span><b>${DATA.filter(s => s.lesson).length}</b> lessons</span>"),
            ("`Stop ${s.n} · ${s.t}", "`${s.label || \"Stop \" + s.n} · ${s.t}"),
            ('<div class="line" id="line"></div>',
             '<div class="line" id="line"></div>\n\n<section class="idea" id="lessons">\n'
             '  <span class="eyebrow">Lesson by lesson · the Kestrel course</span>\n'
             '  <h2>Each Learn lesson, and the code behind it</h2>\n'
             '  <p>One stop per module and fraud lesson. The question, the by-hand work, the In Noesi steps and '
             '"what Noesi cannot do" are the lesson\'s own text. Each procedure chip opens its real source, found '
             'through the engine registry, with its contract\'s objective and limits. "What the key checks" '
             'lists the lesson\'s answer-key lines. Built by docs/manual/build_atlas_lessons.py.</p>\n'
             '  <div class="line" id="line2"></div>\n</section>'),
        ]
        for old, new in swaps:
            assert html.count(old) == 1, f"template changed, cannot place: {old[:60]}"
            html = html.replace(old, new)
    PAGE.write_text(html, encoding="utf-8")
    n_items = sum(len(s["items"]) for s in stops)
    print(f"{len(stops)} lesson stops, {n_items} procedures with source")
    for s in skipped:
        print("  screen, not a procedure:", s)


if __name__ == "__main__":
    main()
