// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
// Refuse lessons that could show a figure the answer key does not hold.
//  - every module's keyModule, and every ask's row, is a line of the
//    finish-line check in kestrel-key.json; every ask's key path resolves;
//  - every number in a lesson's text (two or more digits, or with decimals)
//    is a number in that lesson's part of the key: the check lines of the
//    modules it names and the key entries its asks read. Standards
//    references (AU-C 320, SAS 145, SQMS 1) and "module 12" are skipped;
//  - the modules written and the modules coming are the ones agreed;
//  - the documents, trace and Excel pages (papers.ts, traceData.ts,
//    excelData.ts) hold no number that is not in the key or the case records
//    (kestrel-records.json), and no value that failed to resolve.
// Usage: node scripts/check-lessons.mjs   (runs in `npm run build`)
import { build } from "esbuild";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const data = JSON.parse(readFileSync(join(root, "src/learn/kestrel-key.json"), "utf-8"));
const records = JSON.parse(readFileSync(join(root, "src/learn/kestrel-records.json"), "utf-8"));
async function load(file) {
  const bundled = await build({
    entryPoints: [join(root, "src/learn", file)], bundle: true, write: false,
    format: "esm", platform: "neutral",
  });
  return import("data:text/javascript;base64," + Buffer.from(bundled.outputFiles[0].text).toString("base64"));
}
const { LESSONS, COMING } = await load("lessons.ts");
const { FRAUD_LESSONS } = await load("lessons-fraud.ts");
const { PAPERS } = await load("papers.ts");
const { STAGES, CORRECTION } = await load("traceData.ts");
const { EXERCISES } = await load("excelData.ts");

const problems = [];
const numbers = new Set();
function collectInto(v, into) {
  if (v === null || v === undefined) return;
  if (typeof v === "object") { for (const [k, x] of Object.entries(v)) { collectInto(k, into); collectInto(x, into); } return; }
  for (const m of String(v).matchAll(/-?\d[\d,]*(?:\.\d+)?/g)) {
    const n = Number(m[0].replace(/,/g, ""));
    if (!Number.isNaN(n)) into.add(Math.abs(n));
  }
}
const collect = (v) => collectInto(v, numbers);
collect(data);
collect(records);                         // pages: the key and the case records

// Keys may contain dots ("cash.interbank_transfers"): the longest existing key wins, as in keyData.ts.
function walk(at, parts) {
  if (!parts.length) return at;
  if (at === null || typeof at !== "object") return undefined;
  for (let i = parts.length; i > 0; i--) {
    const key = parts.slice(0, i).join(".");
    if (key in at) { const found = walk(at[key], parts.slice(i)); if (found !== undefined) return found; }
  }
  return undefined;
}
const keyAt = (path) => walk(data.key, path.split("."));

function textOf(lesson) {
  const out = [];
  const walk = (v, where) => {
    if (typeof v === "string") out.push([where, v]);
    else if (Array.isArray(v)) v.forEach((x, i) => walk(x, `${where}[${i}]`));
    else if (v && typeof v === "object") for (const [k, x] of Object.entries(v)) {
      if (k === "row" || k === "key" || k === "keyModule" || k === "module" || k === "keyLines" || k === "n" || k === "minutes" || k === "answer"
          || k === "file" || k === "poster") continue;   // video file names are not teaching text
      walk(x, `${where}.${k}`);
    }
  };
  walk(lesson, lesson.phase === "Fraud" ? `fraud lesson F${lesson.n}` : `module ${lesson.n}`);
  return out;
}

const hasLine = (module, item) => (data.modules[module] ?? []).some((r) => r.item === item);
for (const lesson of [...LESSONS, ...FRAUD_LESSONS]) {
  const name = `${lesson.phase === "Fraud" ? "fraud lesson F" : "module "}${lesson.n}`;
  if (!data.modules[lesson.keyModule]) { problems.push(`${name}: no key module "${lesson.keyModule}"`); continue; }
  for (const [module, item] of lesson.keyLines ?? []) {
    if (!hasLine(module, item)) problems.push(`${name}: key line "${module} / ${item}" does not exist`);
  }
  for (const ask of lesson.byHand.asks) {
    const module = ask.module ?? lesson.keyModule;
    if (!hasLine(module, ask.row)) problems.push(`${name}: ask "${ask.label}" names no line "${module} / ${ask.row}"`);
    if (ask.key !== undefined) {
      const v = keyAt(ask.key);
      const scalar = (x) => x !== undefined && x !== null && typeof x !== "object";
      if (!(scalar(v) || (Array.isArray(v) && v.every(scalar)))) problems.push(`${name}: ask "${ask.label}" key path ${ask.key} does not resolve to a value`);
    }
  }
  // A lesson's figures must come from its own part of the key: the lines of
  // the modules it names and the key entries its asks read. A number found
  // anywhere in the key is not enough (review 2026-10-02 M3: the key's part 1
  // and final misstatements both passed that test, the 30 Sep confusion).
  const own = new Set();
  const modules = new Set([lesson.keyModule, ...(lesson.keyLines ?? []).map(([m]) => m),
    ...lesson.byHand.asks.map((a) => a.module ?? lesson.keyModule)]);
  for (const m of modules) collectInto(data.modules[m], own);
  for (const ask of lesson.byHand.asks) {
    if (ask.key === undefined) continue;
    const parts = ask.key.split(".");   // the entry the ask reads, and its siblings
    collectInto(walk(data.key, parts.slice(0, -1)) ?? keyAt(ask.key), own);
  }
  for (const [where, text] of textOf(lesson)) {
    const clean = text.replace(/\b(AU-C|SAS|SQMS)\s+\d+/g, "").replace(/\b[Mm]odules? \d+/g, "")
      .replace(/\b[\w-]+\.(csv|xlsx|md)\b/g, "");
    for (const m of clean.matchAll(/\d[\d,]*(?:\.\d+)?/g)) {
      const raw = m[0].replace(/,$/, "");
      if (/^\d$/.test(raw)) continue;
      if (!own.has(Number(raw.replace(/,/g, ""))))
        problems.push(`${where}: "${raw}" is not a number in this lesson's part of the key (${[...modules].join(", ")})`);
    }
  }
}

function strings(v, where, out = []) {
  if (typeof v === "string") out.push([where, v]);
  else if (Array.isArray(v)) v.forEach((x, i) => strings(x, `${where}[${i}]`, out));
  else if (v && typeof v === "object") for (const [k, x] of Object.entries(v)) strings(x, `${where}.${k}`, out);
  return out;
}
const pages = [...strings(PAPERS, "documents"), ...strings(STAGES, "trace"),
  ...strings(CORRECTION, "trace correction"), ...strings(EXERCISES, "excel")];
for (const [where, text] of pages) {
  if (/undefined|NaN|missing from the key|\[object Object\]/.test(text)) problems.push(`${where}: a value did not resolve: "${text.slice(0, 80)}"`);
  const clean = text.replace(/\b(AU-C|SAS|SQMS)\s+\d+/g, "").replace(/\b[\w-]+\.(csv|xlsx|md)\b/g, "")
    .replace(/\b[A-Z]{1,2}\d+\b/g, "");  // spreadsheet cell and column references (K6, C2)
  for (const m of clean.matchAll(/\d[\d,]*(?:\.\d+)?/g)) {
    const raw = m[0].replace(/,$/, "");
    if (/^\d$/.test(raw)) continue;
    if (!numbers.has(Number(raw.replace(/,/g, "")))) problems.push(`${where}: "${raw}" is in neither the key nor the case records`);
  }
}

const written = LESSONS.map((l) => l.n).sort((a, b) => a - b).join(",");
const coming = COMING.map((c) => c.n).sort((a, b) => a - b).join(",");
if (written !== "1,2,3,4,5,6,7,8,9,10,11,12,13") problems.push(`modules written are ${written}, agreed 1 to 13`);
if (coming !== "") problems.push(`modules coming are ${coming}, agreed none`);
const fraudNs = FRAUD_LESSONS.map((l) => l.n).join(",");
if (fraudNs !== "1,2,3,4,5,6,7,8,9") problems.push(`fraud lessons are ${fraudNs}, expected 1 to 9`);

if (problems.length) {
  console.error("check-lessons refused:\n" + problems.map((p) => "  " + p).join("\n"));
  process.exit(1);
}
const asks = LESSONS.reduce((n, l) => n + l.byHand.asks.length, 0);
const fraudAsks = FRAUD_LESSONS.reduce((n, l) => n + l.byHand.asks.length, 0);
console.log(`check-lessons: ${LESSONS.length} modules, ${asks} answers, all tied to the key; ${COMING.length} coming; ` +
  `${FRAUD_LESSONS.length} fraud lessons, ${fraudAsks} answers; ` +
  `${PAPERS.length} documents, ${STAGES.length} trace stages, ${EXERCISES.length} Excel exercises, every number from the key or the case files`);
