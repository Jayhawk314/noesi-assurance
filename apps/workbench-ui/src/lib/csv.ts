// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** CSV downloads, so the auditor can take what Noesi found (and what it could
 *  not test) into their own working papers. Opens in Excel.
 *
 *  A cell that begins with = + - @ (or a tab or return) is prefixed with an
 *  apostrophe, so client data can never run as a spreadsheet formula
 *  (CSV injection). Negative amounts are written as numbers, not text. */

type Cell = string | number | boolean | null | undefined;

function cell(value: Cell): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "";
  let text = String(value);
  if (/^[=+\-@\t\r]/.test(text) && !/^-?\d+(\.\d+)?$/.test(text)) text = `'${text}`;
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function toCsv(header: string[], rows: Cell[][]): string {
  return [header, ...rows].map((row) => row.map(cell).join(",")).join("\r\n") + "\r\n";
}

export function downloadCsv(filename: string, header: string[], rows: Cell[][]): void {
  // A byte-order mark so Excel reads the file as UTF-8 (names with accents, "—").
  const blob = new Blob(["﻿", toCsv(header, rows)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** A file name from the client and what it holds: "Kestrel Valley ... - findings - 2026-09-30.csv". */
export function csvName(client: string, what: string): string {
  const safe = client.replace(/[\\/:*?"<>|]+/g, " ").replace(/\s+/g, " ").trim() || "engagement";
  return `${safe} - ${what} - ${new Date().toISOString().slice(0, 10)}.csv`;
}
