// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** The documents an auditor reads, rendered from Kestrel's case files.
 *
 *  Every figure is read from kestrel-records.json (the case files) or
 *  kestrel-key.json (the answer key); scripts/check-lessons.mjs refuses a
 *  number in this text that neither holds. Kestrel's records are QuickBooks
 *  reports and the team's schedules, so these are those reports, laid out as
 *  a reader sees them; nothing here is illustrative. */

import { keyAt } from "./keyData";
import {
  BILL, DUP_LINE, DUPLICATE, PAY_DUPLICATE, PAY_ORIGINAL, PO, R, TWINS, money, summary, tb, uncleared, usd,
} from "./records";

export interface Field {
  label: string;
  value: string;
  mark?: number;
  tone?: "bad" | "ok" | "muted";
}

export interface Row {
  cells: string[];
  mark?: number;
  highlight?: "bad" | "ok" | "focus";
}

export interface Note {
  /** Absent for general notes that point at no single figure. */
  mark?: number;
  title: string;
  text: string;
  assertion?: string;
}

export interface Paper {
  id: string;
  n: number;
  kind: string;
  source: string;
  issuer: string;
  issuerLine?: string;
  docTitle: string;
  docNumber?: string;
  meta?: Field[];
  table?: { head: string[]; rows: Row[]; numericFrom?: number };
  totals?: Field[];
  signatures?: Field[];
  footer?: string;
  notes: Note[];
  noesi: string;
  lessons: number[];
  group: "trail" | "yearend";
}

const QBO = R.company;
const QBO_LINE = "QuickBooks Online report";
const REPORT_DATE = keyAt("part3.representation_letter.report_date") ?? "";
const pos = (v: string) => money(Math.abs(Number(v)));

export const CHAIN: { id: string; label: string; test?: string }[] = [
  { id: "vendors", label: "Vendor list" },
  { id: "po", label: "Purchase order", test: "the vendor on the order" },
  { id: "bill", label: "The bill", test: "bill → PO (memo only)" },
  { id: "duplicate", label: "The same bill again", test: "duplicate bills" },
  { id: "payments", label: "Payments", test: "not linked in the export" },
  { id: "tb", label: "Trial balance", test: "ledger balances" },
  { id: "sad", label: "Misstatement schedule", test: "summary of audit differences" },
];

const twin = (i: number) => TWINS[i];
const dmVendor = R.vendors.find((v) => v.name === "DM Consulting");
const dmTotal = R.dm_checks.reduce((s, c) => s + Math.abs(Number(c.amount)), 0);
const reps = R.representations;
const dated = reps[0]?.Dated ?? "";
const signer = reps[0]?.["Signed By"] ?? "";

export const PAPERS: Paper[] = [
  {
    id: "vendors", n: 1, kind: "Vendor master", group: "trail",
    source: "quickbooks/Vendor_Contact_List.xlsx",
    issuer: QBO, issuerLine: QBO_LINE, docTitle: "VENDOR CONTACT LIST",
    meta: [{ label: "Vendors on the list", value: String(R.vendors.length) }],
    table: {
      head: ["Vendor", "Phone", "Billing address", "Account #"],
      rows: TWINS.map((v, i) => ({
        cells: [v.name, (v.phone ?? "").replace("Phone:", "").trim(), v.address ?? "", v.account ?? "—"],
        mark: i === 0 ? 1 : 2, highlight: "bad" as const,
      })),
    },
    notes: [
      { mark: 1, title: "The supplier as first set up", text: `${twin(0).name}, with a contact and an account number. Every real supplier should appear once.` },
      { mark: 2, title: "The same supplier again", text: `${twin(1).name}: the same phone and the same address, no contact, no account number. A second record for one supplier lets one invoice be paid twice, once under each name.`, assertion: "Occurrence" },
    ],
    noesi: "ap.vendor_relational_twins pairs the two records by name, address and phone. A twin is a lead, not a finding of fraud.",
    lessons: [5],
  },
  {
    id: "po", n: 2, kind: "Purchase order", group: "trail",
    source: "quickbooks/Transaction_List_by_Vendor.xlsx (Purchase Order row)",
    issuer: QBO, issuerLine: QBO_LINE, docTitle: "PURCHASE ORDER", docNumber: PO.num,
    meta: [
      { label: "PO number", value: PO.num, mark: 1 },
      { label: "Date", value: PO.date },
      { label: "Vendor", value: PO.vendor },
    ],
    totals: [{ label: "Ordered", value: usd(PO.amount), mark: 2 }],
    footer: "QuickBooks lists the order as a non-posting transaction. It carries no receipt of goods: QuickBooks Online at Kestrel records none.",
    notes: [
      { mark: 1, title: "The order number", text: `A bill should cite it. At Kestrel the bill cites it only in its memo text ("PO ${PO.num}"), so a test that joins bills to orders has nothing reliable to join on.` },
      { mark: 2, title: "What was ordered", text: `${usd(PO.amount)}, one order. Keep this figure: the supplier's invoice for it appears twice.`, assertion: "Occurrence" },
    ],
    noesi: "ap.voucher_po_reference is partial on Kestrel: the export carries no PO link on a bill. That is why the PO overrun is not found (roadmap C).",
    lessons: [5],
  },
  {
    id: "bill", n: 3, kind: "Supplier bill", group: "trail",
    source: "quickbooks/Transaction_List_by_Vendor.xlsx (Bill row)",
    issuer: BILL.vendor, issuerLine: "entered in QuickBooks as a bill", docTitle: "BILL", docNumber: BILL.num,
    meta: [
      { label: "Invoice number", value: BILL.num, mark: 1 },
      { label: "Date", value: BILL.date },
      { label: "Memo", value: BILL.memo || "—", mark: 2 },
    ],
    table: { head: ["Posted to", "Amount"], rows: [
      { cells: [BILL.split, money(BILL.amount)] },
      { cells: [BILL.account, money(BILL.amount)] },
    ], numericFrom: 1 },
    totals: [{ label: "Billed", value: usd(BILL.amount) }],
    notes: [
      { mark: 1, title: "The supplier's invoice number", text: "The one number that identifies this invoice to the supplier. It should appear once in the payables records." },
      { mark: 2, title: "The order it fills", text: `The memo cites the purchase order, and the amount agrees with it at ${usd(PO.amount)}. So far, a clean purchase: inventory debited, payables credited.`, assertion: "Occurrence · Accuracy" },
    ],
    noesi: "ap.duplicate_bills reads every bill's supplier invoice number. This one is the first of a pair.",
    lessons: [5],
  },
  {
    id: "duplicate", n: 4, kind: "Supplier bill, entered again", group: "trail",
    source: "quickbooks/Transaction_List_by_Vendor.xlsx (Bill row)",
    issuer: DUPLICATE.vendor, issuerLine: "entered in QuickBooks as a bill", docTitle: "BILL", docNumber: DUPLICATE.num,
    meta: [
      { label: "Invoice number", value: DUPLICATE.num, mark: 1, tone: "bad" },
      { label: "Date", value: DUPLICATE.date, mark: 2 },
      { label: "Memo", value: DUPLICATE.memo || "none", tone: "muted" },
    ],
    table: { head: ["Posted to", "Amount"], rows: [
      { cells: [DUPLICATE.split, money(DUPLICATE.amount)], highlight: "bad", mark: 3 },
      { cells: [DUPLICATE.account, money(DUPLICATE.amount)], highlight: "bad" },
    ], numericFrom: 1 },
    totals: [{ label: "Billed", value: usd(DUPLICATE.amount), tone: "bad" }],
    notes: [
      { mark: 1, title: "The same invoice number", text: `${DUPLICATE.num} again, for the same ${usd(DUPLICATE.amount)}, under the twin vendor record.`, assertion: "Occurrence" },
      { mark: 2, title: "Eleven days later", text: `The original is dated ${BILL.date}; this copy ${DUPLICATE.date}. No purchase order in the memo: nothing was ordered twice.` },
      { mark: 3, title: "Where it went", text: "Inventory was debited a second time for goods received once. The cost ends up overstated in inventory or cost of sales." },
    ],
    noesi: `ap.duplicate_bills finds ${DUPLICATE.num} across the two vendor records and states the amount likely recorded twice.`,
    lessons: [5],
  },
  {
    id: "payments", n: 5, kind: "Bill payments", group: "trail",
    source: "quickbooks/Transaction_List_by_Vendor.xlsx (Bill Payment rows)",
    issuer: QBO, issuerLine: QBO_LINE, docTitle: "BILL PAYMENTS (CHECK)",
    meta: [{ label: "Paid from", value: PAY_ORIGINAL.account }],
    table: {
      head: ["Date", "Check", "Paid to", "Amount"],
      rows: [
        { cells: [PAY_ORIGINAL.date, PAY_ORIGINAL.num, PAY_ORIGINAL.vendor, pos(PAY_ORIGINAL.amount)], mark: 1 },
        { cells: [PAY_DUPLICATE.date, PAY_DUPLICATE.num, PAY_DUPLICATE.vendor, pos(PAY_DUPLICATE.amount)], mark: 2, highlight: "bad" },
      ],
      numericFrom: 3,
    },
    footer: "The export lists each check and its payee, not the bills it pays.",
    notes: [
      { mark: 1, title: "A check that pays several bills", text: `Check ${PAY_ORIGINAL.num} pays ${usd(PAY_ORIGINAL.amount)} to the original vendor record. The export does not say which bills it covers; the original ${BILL.num} is presumably among them.` },
      { mark: 2, title: "A check for exactly the duplicate", text: `Check ${PAY_DUPLICATE.num} pays ${usd(PAY_DUPLICATE.amount)} to the twin record, the duplicate's amount to the cent. The money has left: a refund is now due from the supplier.`, assertion: "Occurrence" },
    ],
    noesi: "Noesi loads the bill payments raw and foots them. It cannot tie a check to the bills it pays from these exports; that link is a request to the client.",
    lessons: [5],
  },
  {
    id: "tb", n: 6, kind: "Trial balance (extract)", group: "trail",
    source: "quickbooks/Trial_Balance_2026-06-30.xlsx",
    issuer: QBO, issuerLine: QBO_LINE, docTitle: "TRIAL BALANCE", docNumber: "As of June 30, 2026",
    meta: [{ label: "Report total", value: `${money(R.tb_total[0])} / ${money(R.tb_total[1])}`, mark: 1 }],
    table: {
      head: ["Account", "Debit", "Credit"],
      rows: ["12100", "20000", "50000"].map((a, i) => {
        const row = tb(a);
        return { cells: [row.account, row.debit ? money(row.debit) : "", row.credit ? money(row.credit) : ""],
                 mark: i === 0 ? 2 : undefined };
      }),
      numericFrom: 1,
    },
    notes: [
      { mark: 1, title: "It foots", text: "Debits equal credits. That proves the arithmetic of double entry, not that each entry is right: the duplicate is in here, on both sides." },
      { mark: 2, title: "Where the duplicate sits", text: "The second bill debited inventory. As goods are sold, inventory cost moves to cost of goods sold, so the overstatement sits in one or the other; the payables side cleared when the check was paid." },
    ],
    noesi: "fs.trial_balance_analytics reads this report (the demo builds the trial balance from QuickBooks' two Trial Balance exports, raw) and foots it before any analytic.",
    lessons: [1, 5],
  },
  {
    id: "sad", n: 7, kind: "Schedule of uncorrected misstatements", group: "trail",
    source: "auditor/uncorrected_misstatements_final.csv",
    issuer: "Audit team working paper", docTitle: "UNCORRECTED MISSTATEMENTS", docNumber: DUP_LINE["WP Reference"],
    meta: [{ label: "Materiality", value: usd(keyAt("part3.final_misstatements.materiality") ?? "0") }],
    table: {
      head: ["Misstatement", "Ref", "Current assets", "Income before taxes"],
      rows: R.misstatements.map((m) => ({
        cells: [m.Description, m["WP Reference"], money(m["Current Assets"]), money(m["Income Before Taxes"])],
        highlight: m === DUP_LINE ? "bad" as const : undefined, mark: m === DUP_LINE ? 1 : undefined,
      })),
      numericFrom: 2,
    },
    totals: [{ label: "Current assets, all lines", value: usd(keyAt("part3.final_misstatements.largest") ?? "0"), mark: 2, tone: "bad" }],
    notes: [
      { mark: 1, title: "The duplicate, as a misstatement", text: `The team records it as a refund due from the supplier: current assets and income both understated by ${usd(DUP_LINE["Current Assets"])} until it is recorded.` },
      { mark: 2, title: "Added up by line", text: `The current-assets column totals ${usd(keyAt("part3.final_misstatements.largest") ?? "0")}, above materiality. That is one of the three matters the opinion turns on.`, assertion: "Evaluation" },
    ],
    noesi: "completion.uncorrected_misstatements totals the schedule by line and marks the line at materiality; the SAD carries it to the draft opinion.",
    lessons: [12, 13],
  },

  // ------------------------------------------------ the year-end records
  {
    id: "bankrec", n: 8, kind: "Bank reconciliation", group: "yearend",
    source: "quickbooks/Checking_Reconciliation.xlsx",
    issuer: QBO, issuerLine: R.checking.reconciled.join(" · "), docTitle: "RECONCILIATION REPORT",
    docNumber: R.checking.title,
    meta: [
      { label: "Statement ending balance", value: usd(summary("Statement ending")) },
      { label: "Register balance", value: usd(summary("Register balance")) },
    ],
    table: {
      head: ["Date", "Type", "Ref", "Payee", "Amount"],
      rows: R.checking.uncleared.map((u) => ({
        cells: [u.date, u.type, u.ref || "—", u.payee, money(u.amount)],
        mark: u.ref === "4421" ? 1 : u.ref === "4425" ? 2 : undefined,
        highlight: u.ref === "4421" || u.ref === "4425" ? "bad" as const : undefined,
      })),
      numericFrom: 4,
    },
    totals: [{ label: "Uncleared, net", value: money(summary("Uncleared")) }],
    notes: [
      { mark: 1, title: "A check that never cleared", text: `Check 4421 to ${uncleared("4421").payee}, ${usd(uncleared("4421").amount)}: still not through the bank by the end of the cutoff statement. Was it mailed? Is the payee real?`, assertion: "Existence" },
      { mark: 2, title: "A check that cleared at another amount", text: `Check 4425 is listed at ${usd(uncleared("4425").amount)}. Trace it to the cutoff statement and compare. Every reconciling item gets traced; none is accepted on sight.`, assertion: "Accuracy" },
      { title: "Foot it", text: "Statement balance plus deposits in transit, less outstanding checks, should give the register balance. Add it yourself." },
    ],
    noesi: "cash.bank_reconciliation refoots the report and traces every uncleared item to the cutoff statement (the demo loads it hand-prepared; roadmap C).",
    lessons: [5],
  },
  {
    id: "unpaid", n: 9, kind: "Unpaid bills", group: "yearend",
    source: "quickbooks/Unpaid_Bills.xlsx",
    issuer: QBO, issuerLine: QBO_LINE, docTitle: "UNPAID BILLS", docNumber: "As of June 30, 2026",
    table: {
      head: ["Vendor", "Bill", "Date", "Amount", "Open balance"],
      rows: R.unpaid_alder.map((b) => ({ cells: ["Alder & Finch CPAs", b.num, b.date, money(b.amount), money(b.open)], mark: 1, highlight: "bad" as const })),
      numericFrom: 3,
    },
    notes: [
      { mark: 1, title: "A bill paid short", text: `Billed ${usd(R.unpaid_alder[0]?.amount ?? "0")}; ${usd(R.unpaid_alder[0]?.open ?? "0")} left open. Compare with check 4425 on the reconciliation: the check was written for less than the bill and cleared for more than it was written.`, assertion: "Accuracy · Completeness" },
    ],
    noesi: "The short payment surfaces in cash.bank_reconciliation, as a check that cleared at another amount.",
    lessons: [5],
  },
  {
    id: "dm", n: 10, kind: "A vendor at an employee's address", group: "yearend",
    source: "quickbooks/Vendor_Contact_List.xlsx · client/employee_master.csv · quickbooks/Transaction_List_by_Vendor.xlsx",
    issuer: QBO, issuerLine: "three records side by side", docTitle: "DM CONSULTING",
    meta: [
      { label: "Vendor address", value: dmVendor?.address ?? "", mark: 1, tone: "bad" },
      { label: `Employee ${R.e07["Employee ID"]}, ${R.e07.Name}`, value: R.e07["Home Address"], mark: 1, tone: "bad" },
    ],
    table: {
      head: ["Date", "Type", "Check", "Memo", "Amount"],
      rows: R.dm_checks.map((c) => ({ cells: [c.date, c.type, c.num, c.memo, pos(c.amount)], mark: 2 })),
      numericFrom: 4,
    },
    totals: [{ label: "Paid, no bills", value: usd(dmTotal), tone: "bad" }],
    notes: [
      { mark: 1, title: "One address, two roles", text: "The vendor's billing address is the bookkeeper's home address. The bookkeeper also keeps the vendor list and writes the checks." },
      { mark: 2, title: "Checks with no bills", text: "Each is a plain check, not a bill payment: there is no invoice behind any of them. And DM Consulting is not on management's related-party list." },
    ],
    noesi: "payroll.register_tests finds the shared address; ap.payments_without_bills finds the checks. related_parties.matching cannot: the party is not on the list it matches.",
    lessons: [5, 8, 11],
  },
  {
    id: "ghost", n: 11, kind: "Payroll register (extract)", group: "yearend",
    source: "client/payroll_register_FY2026.csv · client/employee_master.csv",
    issuer: QBO, issuerLine: "payroll register, year ended June 30, 2026", docTitle: "PAYROLL REGISTER",
    meta: [
      { label: "Register rows", value: String(R.register_rows) },
      { label: "IDs on the employee master", value: R.master_ids.join(", "), mark: 1 },
    ],
    table: {
      head: ["Employee", "Date", "Gross", "Taxes", "Net", "Deposit"],
      rows: R.e16.sample.map((r) => ({ cells: [r["Employee ID"], r["Check Date"], money(r["Gross Pay"]), money(r["Taxes Withheld"]), money(r["Net Pay"]), r["Check Number"]], highlight: "bad" as const, mark: 2 })),
      numericFrom: 2,
    },
    totals: [{ label: `E16, ${R.e16.payments} payments, ${R.e16.first} to ${R.e16.last}: net`, value: usd(R.e16.net), tone: "bad" }],
    notes: [
      { mark: 1, title: "Who works here", text: "The master lists every employee. E16 is not on it." },
      { mark: 2, title: "Paid all year anyway", text: `E16 was paid ${R.e16.payments} times, every payday, ${usd(R.e16.net)} net in total. Where did the deposits go, and who set the ID up?`, assertion: "Occurrence" },
    ],
    noesi: "payroll.register_tests lists every payment to an ID the master does not have.",
    lessons: [8],
  },
  {
    id: "fa06", n: 12, kind: "Fixed-asset register (one asset)", group: "yearend",
    source: "client/fixed_asset_register.csv",
    issuer: QBO, issuerLine: "fixed-asset register", docTitle: "FIXED ASSET", docNumber: R.fa_06["Asset ID"],
    meta: [
      { label: "Description", value: R.fa_06.Description },
      { label: "Placed in service", value: R.fa_06["Placed in Service"] },
      { label: "Cost", value: usd(R.fa_06.Cost), mark: 1 },
      { label: "Useful life (years)", value: R.fa_06["Useful Life"], mark: 1 },
      { label: "Salvage", value: usd(R.fa_06["Salvage Value"]) },
    ],
    totals: [
      { label: "This year's depreciation, as recorded", value: usd(R.fa_06["Current Year Depreciation"]), mark: 2, tone: "bad" },
      { label: "Recomputed (straight line)", value: usd(keyAt("part2.ppe.depreciation_differs.recomputed") ?? "0") },
    ],
    notes: [
      { mark: 1, title: "The inputs", text: "Cost less salvage, over the useful life: the straight-line charge for a full year." },
      { mark: 2, title: "The register's figure", text: `Recorded ${usd(R.fa_06["Current Year Depreciation"])}; recomputed ${usd(keyAt("part2.ppe.depreciation_differs.recomputed") ?? "0")}. The difference is on the misstatement schedule.`, assertion: "Valuation" },
    ],
    noesi: "ppe.depreciation_recompute recomputes every asset under the policy's convention and lists each difference.",
    lessons: [9],
  },
  {
    id: "je1071", n: 13, kind: "Journal entry after year end", group: "yearend",
    source: "quickbooks/Journal_2026-07.xlsx",
    issuer: QBO, issuerLine: "Journal, July 2026", docTitle: "JOURNAL ENTRY", docNumber: R.je_1071[0]?.num,
    meta: [
      { label: "Date", value: R.je_1071[0]?.date ?? "", mark: 1 },
      { label: "Name", value: R.je_1071[0]?.name ?? "" },
      { label: "Memo", value: R.je_1071[0]?.memo ?? "", mark: 2 },
    ],
    table: {
      head: ["Account", "Debit", "Credit"],
      rows: R.je_1071.map((l) => ({ cells: [l.account, l.debit ? money(l.debit) : "", l.credit ? money(l.credit) : ""] })),
      numericFrom: 1,
    },
    notes: [
      { mark: 1, title: "After the year end", text: "Dated in July, so outside the year audited. That alone does not keep it out of the statements." },
      { mark: 2, title: "What it settles", text: "A dispute from March: the condition existed at year end. The settlement is evidence of its amount, so the June statements are adjusted (AU-C 560).", assertion: "Completeness · Cutoff" },
    ],
    noesi: "completion.subsequent_events lists it as a lead above the threshold. Whether it adjusts is the partner's judgment.",
    lessons: [12],
  },
  {
    id: "replett", n: 14, kind: "Representation letter (as received)", group: "yearend",
    source: "auditor/representation_letter.csv",
    issuer: R.company, issuerLine: "to the auditor", docTitle: "MANAGEMENT REPRESENTATIONS",
    meta: [
      { label: "Dated", value: dated, mark: 1, tone: "bad" },
      { label: "Report date", value: REPORT_DATE },
    ],
    table: {
      head: ["Representation", "Obtained"],
      rows: reps.map((r) => ({ cells: [r.Representation, r.Obtained] })),
    },
    signatures: [{ label: "Signed", value: signer }],
    notes: [
      { mark: 1, title: "The date", text: `Dated ${dated}; the report is dated ${REPORT_DATE}. The letter must speak as of the report date, so it has to be re-dated.` },
      { title: "What is not there", text: "Read the list for what is missing, not only what is present. There is no representation about related parties, at a company whose managing member is on the payroll and whose customer Summit Loop Racing is owned by the managing member's brother.", assertion: "AU-C 580" },
    ],
    noesi: "completion.representation_letter checks the letter against the required list, the signer and the report date, and names what is missing.",
    lessons: [12, 13],
  },
];
