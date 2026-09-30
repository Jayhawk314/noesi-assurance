// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Amounts inside engine text, written the way an auditor reads them.
 *
 *  Findings and the opinion's basis are built by the engine as plain text
 *  ("3 payments ... total 7325.0 around threshold 2500.0"). The stored text is
 *  evidence and is never changed; only its display is. A number with one or
 *  two decimals becomes "7,325.00". Left alone: percentages ("24.2%"), ratios
 *  and rates with more decimals ("1.1291"), multiples ("2.0 ×"), whole numbers (account numbers,
 *  counts, years), and anything joined to letters, dashes or slashes (dates,
 *  invoice and check numbers). */
const AMOUNT = /(?<![\w./-])(-?)(\d+)\.(\d{1,2})(?![\d%\w])(?!\s*×)/g;

export function amountsInWords(text: string): string {
  return text.replace(AMOUNT, (_m, sign: string, whole: string, cents: string) =>
    `${sign}${Number(whole).toLocaleString("en-US")}.${cents.padEnd(2, "0")}`);
}

/** A money amount with cents: 300 -> "300.00", 15650.37 -> "15,650.37". */
export function cents(value: number | string | null | undefined): string {
  const n = Number(value);
  return Number.isFinite(n)
    ? n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : "—";
}
