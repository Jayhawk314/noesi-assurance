// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
// Refuse lessons that could show a figure the answer key does not hold.
//  - every module's keyModule, and every ask's row, is a line of the
//    finish-line check in kestrel-key.json; every ask's key path resolves;
//  - every number in a lesson's text (two or more digits, or with decimals)
//    is a number in the key or in a line of the check. Standards references
//    (AU-C 320, SAS 145, SQMS 1) are not figures and are skipped;
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
const { PAPERS } = await load("papers.ts");
const { STAGES, CORRECTION } = await load("traceData.ts");
const { EXERCISES } = await load("excelData.ts");

const problems = [];
const numbers = new Set();
const collect = (v) => {
  if (v === null || v === undefined) return;
  if (typeof v === "object") { for (const [k, x] of Object.entries(v)) { collect(k); collect(x); } return; }
  for (const m of String(v).matchAll(/-?\d[\d,]*(?:\.\d+)?/g)) {
    const n = Number(m[0].replace(/,/g, ""));
    if (!Number.isNaN(n)) numbers.add(Math.abs(n));
  }
};
collect(data);
const lessonNumbers = new Set(numbers);   // lessons: the key only
collect(records);                          // pages: the key and the case records

const keyAt = (path) => path.split(".").reduce((at, p) => (at && typeof at === "object" ? at[p] : undefined), data.key);

function textOf(lesson) {
  const out = [];
  const walk = (v, where) => {
    if (typeof v === "string") out.push([where, v]);
    else if (Array.isArray(v)) v.forEach((x, i) => walk(x, `${where}[${i}]`));
    else if (v && typeof v === "object") for (const [k, x] of Object.entries(v)) {
      if (k === "row" || k === "key" || k === "keyModule" || k === "n" || k === "minutes" || k === "answer") continue;
      walk(x, `${where}.${k}`);
    }
  };
  walk(lesson, `module ${lesson.n}`);
  return out;
}

for (const lesson of LESSONS) {
  const rows = data.modules[lesson.keyModule];
  if (!rows) { problems.push(`module ${lesson.n}: no key module "${lesson.keyModule}"`); continue; }
  for (const ask of lesson.byHand.asks) {
    if (!rows.some((r) => r.item === ask.row)) problems.push(`module ${lesson.n}: ask "${ask.label}" names no line "${ask.row}"`);
    if (ask.key !== undefined) {
      const v = keyAt(ask.key);
      if (v === undefined || v === null || (typeof v === "object" && !Array.isArray(v))) problems.push(`module ${lesson.n}: ask "${ask.label}" key path ${ask.key} does not resolve to a value`);
    }
  }
  for (const [where, text] of textOf(lesson)) {
    const clean = text.replace(/\b(AU-C|SAS|SQMS)\s+\d+/g, "").replace(/`[^`]*`/g, "").replace(/\b[\w-]+\.(csv|xlsx|md)\b/g, "");
    for (const m of clean.matchAll(/\d[\d,]*(?:\.\d+)?/g)) {
      const raw = m[0].replace(/,$/, "");
      if (/^\d$/.test(raw)) continue;
      if (!lessonNumbers.has(Number(raw.replace(/,/g, "")))) problems.push(`${where}: "${raw}" is not a number the key holds`);
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
if (written !== "1,5,8,9,10,11,12,13") problems.push(`modules written are ${written}, agreed 1,5,8,9,10,11,12,13`);
if (coming !== "2,3,4,6,7") problems.push(`modules coming are ${coming}, agreed 2,3,4,6,7`);

if (problems.length) {
  console.error("check-lessons refused:\n" + problems.map((p) => "  " + p).join("\n"));
  process.exit(1);
}
const asks = LESSONS.reduce((n, l) => n + l.byHand.asks.length, 0);
console.log(`check-lessons: ${LESSONS.length} modules, ${asks} answers, all tied to the key; ${COMING.length} coming; ` +
  `${PAPERS.length} documents, ${STAGES.length} trace stages, ${EXERCISES.length} Excel exercises, every number from the key or the case files`);
