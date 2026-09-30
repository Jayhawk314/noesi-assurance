// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** The Kestrel case records the documents, trace and Excel pages show, read
 *  from kestrel-records.json (written by scripts/export_records.py from the
 *  case files). Pages format these values; they never type a figure. */

import records from "./kestrel-records.json";

export const R = records;

type Tx = (typeof records.moraine)[number];

/** 1234.5 → "1,234.50"; the sign is kept. */
export function money(value: string | number): string {
  return Number(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
/** 1234.5 or -1234.5 → "$1,234.50". */
export function usd(value: string | number): string {
  return "$" + money(Math.abs(Number(value)));
}

function find<T>(rows: T[], test: (row: T) => boolean, what: string): T {
  const row = rows.find(test);
  if (!row) throw new Error(`kestrel-records.json has no ${what}; re-run scripts/export_records.py`);
  return row;
}

const MORAINE = "Moraine Cycle Components";
export const TWINS = R.vendors.filter((v) => v.name.startsWith(MORAINE));
export const PO = find(R.moraine, (t: Tx) => t.type === "Purchase Order", "purchase order");
export const BILL = find(R.moraine, (t: Tx) => t.type === "Bill" && t.vendor === MORAINE, "original bill");
export const DUPLICATE = find(R.moraine, (t: Tx) => t.type === "Bill" && t.vendor !== MORAINE, "duplicate bill");
export const PAY_ORIGINAL = find(R.moraine, (t: Tx) => t.type.startsWith("Bill Payment") && t.vendor === MORAINE, "original payment");
export const PAY_DUPLICATE = find(R.moraine, (t: Tx) => t.type.startsWith("Bill Payment") && t.vendor !== MORAINE, "duplicate payment");
export const DUP_LINE = find(R.misstatements, (m) => m.Description.startsWith("Duplicate"), "duplicate misstatement line");

export function tb(account: string) {
  return find(R.trial_balance, (row) => row.account.startsWith(account), `trial balance account ${account}`);
}
export function uncleared(ref: string) {
  return find(R.checking.uncleared, (row) => row.ref === ref, `uncleared item ${ref}`);
}
export function summary(label: string): string {
  const key = Object.keys(R.checking.summary).find((k) => k.startsWith(label));
  if (!key) throw new Error(`reconciliation summary has no "${label}"`);
  return (R.checking.summary as Record<string, string>)[key];
}
