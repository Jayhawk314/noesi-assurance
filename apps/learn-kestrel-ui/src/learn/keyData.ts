// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** The figures the lessons show, read from kestrel-key.json. That file is
 *  written by scripts/export_key.py from the finish-line check, so each
 *  figure is the answer key's and agrees with FINISH-LINE-REPORT.md. */

import data from "./kestrel-key.json";

export interface KeyRow {
  item: string;
  status: "match" | "differs" | "not in Noesi";
  why: string;
  key: string;
  noesi: string;
}

const MODULES = data.modules as Record<string, KeyRow[]>;

export function moduleRows(module: string): KeyRow[] {
  return MODULES[module] ?? [];
}

export function findRow(module: string, item: string): KeyRow | undefined {
  return moduleRows(module).find((r) => r.item === item);
}

/** Follow a dotted path, allowing keys that themselves contain dots (the
 *  first key file has "cash.interbank_transfers"): the longest key that
 *  exists at each level wins. */
function walk(at: unknown, parts: string[]): unknown {
  if (!parts.length) return at;
  if (at === null || typeof at !== "object") return undefined;
  for (let i = parts.length; i > 0; i--) {
    const key = parts.slice(0, i).join(".");
    if (key in (at as Record<string, unknown>)) {
      const found = walk((at as Record<string, unknown>)[key], parts.slice(i));
      if (found !== undefined) return found;
    }
  }
  return undefined;
}

/** A value from the answer key by path, e.g. "payables.duplicate_bill.invoice". */
export function keyAt(path: string): string | undefined {
  const at = walk(data.key, path.split("."));
  if (at === undefined || at === null) return undefined;
  if (Array.isArray(at)) return at.map(String).join(", ");
  if (typeof at === "boolean") return at ? "yes" : "no";
  return typeof at === "object" ? undefined : String(at);
}

/** Loose agreement for a learner's own answer: numbers at two decimals
 *  (commas, $ and % ignored); text by its words, case ignored. */
export function agrees(mine: string, key: string): boolean {
  const num = (s: string) => {
    const t = s.replace(/[$,%\s]/g, "");
    return /^-?\d+(\.\d+)?$/.test(t) ? Number(t) : null;
  };
  const a = num(mine), b = num(key);
  if (a !== null && b !== null) return Math.abs(a - b) < 0.005;
  const words = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  return words(mine) !== "" && words(mine) === words(key);
}
