// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Amounts inside engine text, written the way an auditor reads them.
 *
 *  Findings and the opinion's basis are built by the engine as plain text
 *  ("3 payments ... total 7325.0 around threshold 2500.0"). The stored text is
 *  evidence and is never changed; only its display is, and only where a number
 *  is plainly an amount the engine printed:
 *  - two decimals ("18432.50" -> "18,432.50"), or
 *  - one decimal on a number of four or more digits ("7325.0" -> "7,325.00").
 *  Left alone: ratios and short one-decimal figures ("1.5", "45.3 days"),
 *  anything followed by %, "percent", "days" or "×", anything after "account",
 *  "AS", "section" or "§" (references, sub-accounts like 1200.10), dotted dates
 *  ("2026.06.30"), and numbers joined to letters, dashes or slashes (dates,
 *  invoice and check numbers). Not for text a person typed. */
const AMOUNT = /(?<![\w./-])(-?)(\d+)\.(\d{1,2})(?![\d\w]|\.\d|\s*(?:%|percent\b|days?\b|×))/g;
const REFERENCE = /(?:\baccount|\bacct|\bAS|\bsection|§)\s*$/i;

export function amountsInWords(text: string): string {
  return text.replace(AMOUNT, (match: string, sign: string, whole: string, cents: string,
                               offset: number, all: string) => {
    if (cents.length === 1 && whole.length < 4) return match;
    if (REFERENCE.test(all.slice(Math.max(0, offset - 12), offset))) return match;
    return `${sign}${Number(whole).toLocaleString("en-US")}.${cents.padEnd(2, "0")}`;
  });
}

/** A money amount with cents: 300 -> "300.00", 15650.37 -> "15,650.37". */
export function cents(value: number | string | null | undefined): string {
  const n = Number(value);
  return Number.isFinite(n)
    ? n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : "—";
}
