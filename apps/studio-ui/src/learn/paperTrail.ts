// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** The documents an auditor reads, rendered from Harborline's case data.
 *
 *  Documents 1–8 use only values present in case-studies/harborline-marine/
 *  data (one purchase traced end to end, plus year-end balances). Anything
 *  the extracts do not contain is shown as "not in the extract" or marked
 *  illustrative. Documents 9–12 are wholly illustrative: the case has no
 *  receivables, inventory, confirmation or representation data. */

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
  illustrative: boolean;
  source: string;
  issuer: string;
  issuerLine?: string;
  addressee?: string[];
  docTitle: string;
  docNumber?: string;
  meta: Field[];
  table?: { head: string[]; rows: Row[]; numericFrom?: number };
  totals?: Field[];
  body?: string[];
  signatures?: Field[];
  footer?: string;
  notes: Note[];
  noesi: string;
  lessons: number[];
}

const HARBORLINE = "Harborline Marine Group, Inc.";

export const CHAIN: { id: string; label: string; test?: string }[] = [
  { id: "po", label: "Purchase order" },
  { id: "grn", label: "Receiving report", test: "three-way match" },
  { id: "invoice", label: "Vendor invoice", test: "voucher → PO reference" },
  { id: "check", label: "Check / payment", test: "payment → voucher · document chain · two people" },
  { id: "bank", label: "Bank statement", test: "bank clearing (2% tolerance)" },
  { id: "gl", label: "General ledger", test: "GL posting · period" },
];

export const PAPERS: Paper[] = [
  {
    id: "po", n: 1, kind: "Purchase order", illustrative: false,
    source: "purchase_orders.csv · vendors.csv · employees.csv",
    issuer: HARBORLINE, issuerLine: "Purchasing Department · Norfolk, Virginia",
    addressee: ["Kingfisher Security Services", "Norfolk, Virginia", "Vendor V1035 · Tax ID 39-8273946"],
    docTitle: "PURCHASE ORDER", docNumber: "PO-2026-0009",
    meta: [
      { label: "PO number", value: "PO-2026-0009", mark: 1 },
      { label: "PO date", value: "February 7, 2026" },
      { label: "Vendor", value: "V1035 — Kingfisher Security Services" },
    ],
    table: {
      head: ["Description", "Amount"],
      rows: [{ cells: ["Security services (line detail not in the extract)", "4,325.33"] }],
      numericFrom: 1,
    },
    totals: [{ label: "PO total", value: "$4,325.33", mark: 2 }],
    signatures: [
      { label: "Created by", value: "Samir Haddad (E318), Buyer" },
      { label: "Approved by", value: "Rosalind Achebe (E102), Approver", mark: 3 },
    ],
    footer: "Approval timestamps are not in the extract: the case's scope limitation #1.",
    notes: [
      { mark: 1, title: "The PO number", text: "Every later document should cite it. It is the key the three-way match and the voucher-to-PO test join on.", assertion: "Occurrence" },
      { mark: 2, title: "The ordered amount", text: "Compare it to what was received (document 2) and what was billed (document 3). Here, ordered and billed agree at $4,325.33, but receiving disagrees.", assertion: "Accuracy" },
      { mark: 3, title: "Who approved it", text: "Created by a buyer, approved by a different person in an approver role. That is what you want to see. Without timestamps you cannot tell whether approval came before the order.", assertion: "Authorization" },
    ],
    noesi: "voucher → PO reference confirms VCH-2026-0009 cites this PO. The three-way match compares this PO with the receipt and the invoice.",
    lessons: [4, 5, 6],
  },
  {
    id: "grn", n: 2, kind: "Receiving report", illustrative: false,
    source: "goods_receipts.csv",
    issuer: HARBORLINE, issuerLine: "Receiving · Norfolk parts warehouse",
    docTitle: "RECEIVING REPORT", docNumber: "GRN-2026-0009",
    meta: [
      { label: "Receipt number", value: "GRN-2026-0009" },
      { label: "PO reference", value: "PO-2026-0009", mark: 1 },
      { label: "Date received", value: "February 15, 2026", mark: 3 },
      { label: "Received by", value: "not in the extract", tone: "muted" },
    ],
    table: {
      head: ["Description", "Accepted amount"],
      rows: [{ cells: ["Services accepted against PO-2026-0009", "3,244.00"], mark: 2, highlight: "bad" }],
      numericFrom: 1,
    },
    totals: [{ label: "Received / accepted", value: "$3,244.00", mark: 2, tone: "bad" }],
    footer: "For a services vendor, the 'receipt' is the record that the service was delivered and accepted.",
    notes: [
      { mark: 1, title: "Which order it fulfils", text: "Ties this receipt to PO-2026-0009. A receipt that cites no PO, or a PO with no receipt, is an exception." },
      { mark: 2, title: "What actually arrived", text: "$3,244.00 against an order of $4,325.33, which is $1,081.33 short. Paying more than was received is the classic three-way-match failure.", assertion: "Occurrence · Accuracy" },
      { mark: 3, title: "When it arrived", text: "February 15, five days before the invoice. At year end, this date decides which period the liability belongs to.", assertion: "Cutoff" },
    ],
    noesi: "The three-way match flags VCH-2026-0009: the voucher amount of $4,325.33 exceeds observed receipts of $3,244.00, a $1,081.33 exception. This is a real Harborline finding.",
    lessons: [5, 6, 9],
  },
  {
    id: "invoice", n: 3, kind: "Vendor invoice (voucher)", illustrative: false,
    source: "vouchers.csv · vendors.csv · employees.csv",
    issuer: "Kingfisher Security Services", issuerLine: "Norfolk, Virginia · Tax ID 39-8273946",
    addressee: [HARBORLINE, "Accounts Payable"],
    docTitle: "INVOICE", docNumber: "VCH-2026-0009",
    meta: [
      { label: "Invoice / voucher no.", value: "VCH-2026-0009" },
      { label: "Invoice date", value: "February 20, 2026" },
      { label: "Your PO", value: "PO-2026-0009", mark: 2 },
    ],
    table: {
      head: ["Description", "Amount"],
      rows: [{ cells: ["Security services per PO-2026-0009 (line detail not in the extract)", "4,325.33"], mark: 1, highlight: "bad" }],
      numericFrom: 1,
    },
    totals: [{ label: "Amount due", value: "$4,325.33", mark: 1, tone: "bad" }],
    signatures: [
      { label: "Entered (voucher) by", value: "Priya Raman (E218), AP clerk" },
      { label: "Approved for payment by", value: "Rosalind Achebe (E102), Approver", mark: 3 },
    ],
    notes: [
      { mark: 1, title: "The billed amount", text: "$4,325.33 agrees with the PO but is $1,081.33 more than was received. Before paying, AP should have matched it to the receipt and held it.", assertion: "Accuracy · Occurrence" },
      { mark: 2, title: "The PO it cites", text: "Vouch it back: does PO-2026-0009 exist, from this vendor, for this amount? Three Harborline vouchers cite POs that do not exist." },
      { mark: 3, title: "Approval for payment", text: "A different person from the one who entered it. Good segregation, but the approver still approved an invoice that did not match the receipt.", assertion: "Authorization" },
    ],
    noesi: "voucher → PO reference passes for this invoice. The three-way match flags it. In Assignment 11's corrected file, this invoice is quietly 'corrected' to $3,244.00, and What Changed shows the exception moving to the payment.",
    lessons: [5, 6],
  },
  {
    id: "check", n: 4, kind: "Check / payment", illustrative: false,
    source: "payments.csv · employees.csv",
    issuer: HARBORLINE, issuerLine: "Operating account",
    docTitle: "CHECK", docNumber: "CHK-20009",
    meta: [
      { label: "Date", value: "March 16, 2026" },
      { label: "Pay to the order of", value: "Kingfisher Security Services", mark: 2 },
      { label: "Amount", value: "$4,325.33", mark: 1 },
      { label: "In words", value: "Four thousand three hundred twenty-five and 33/100 dollars" },
      { label: "Memo", value: "VCH-2026-0009 · payment PAY-2026-0009", mark: 4 },
    ],
    signatures: [
      { label: "Prepared by", value: "Priya Raman (E218), AP clerk" },
      { label: "Authorized signature", value: "Rosalind Achebe (E102), Approver", mark: 3 },
    ],
    footer: "Under the $10,000 limit, one approver's signature suffices under Harborline's written policy.",
    notes: [
      { mark: 1, title: "The amount paid", text: "$4,325.33, the full invoice. The company paid $1,081.33 for services it has no record of receiving.", assertion: "Occurrence · Accuracy" },
      { mark: 2, title: "The payee", text: "Agree it to the vendor master (V1035). A payee name that does not match the vendor record is a fraud signal." },
      { mark: 3, title: "Prepared vs signed", text: "Two different people: the control worked here. Five Harborline payments were prepared and approved by the same person.", assertion: "Authorization" },
      { mark: 4, title: "What it pays", text: "The voucher reference links the payment back to the invoice. A payment citing a voucher that does not exist is what the search for unrecorded liabilities starts from." },
    ],
    noesi: "payment → voucher reference passes, segregation of duties passes (E218 ≠ E102), and document chain checks the dates run PO → invoice → payment.",
    lessons: [5, 6, 8],
  },
  {
    id: "bank", n: 5, kind: "Bank statement", illustrative: false,
    source: "bank.csv (the independent bank feed, March 2026 debits)",
    issuer: "Operating bank", issuerLine: `Account holder: ${HARBORLINE} · Operating account`,
    docTitle: "STATEMENT OF ACCOUNT — MARCH 2026",
    meta: [
      { label: "Period", value: "March 1 – March 31, 2026" },
      { label: "Opening / closing balance", value: "not in the extract (the feed lists debits only)", tone: "muted" },
    ],
    table: {
      head: ["Date", "Bank ref", "Description", "Debit"],
      numericFrom: 3,
      rows: [
        { cells: ["Mar 05", "BNK-00069", "PAY-2026-0072", "969.02"] },
        { cells: ["Mar 06", "BNK-00016", "PAY-2026-0017", "941.12"] },
        { cells: ["Mar 08", "BNK-00045", "PAY-2026-0047", "28,638.47"] },
        { cells: ["Mar 08", "BNK-00106", "PAY-2026-0109", "27,088.43"] },
        { cells: ["Mar 09", "BNK-00047", "PAY-2026-0049", "26,428.44"] },
        { cells: ["Mar 11", "BNK-00073", "PAY-2026-0076", "26,768.68"] },
        { cells: ["Mar 17", "BNK-00046", "PAY-2026-0048", "2,483.09"] },
        { cells: ["Mar 17", "BNK-00093", "PAY-2026-0096", "24,182.83"] },
        { cells: ["Mar 18", "BNK-00049", "PAY-2026-0051", "33,467.83"] },
        { cells: ["Mar 19", "BNK-00114", "PAY-2026-0118", "18,960.95"] },
        { cells: ["Mar 22", "BNK-00008", "PAY-2026-0009 — CHK-20009", "4,325.33"], mark: 1, highlight: "focus" },
        { cells: ["Mar 22", "BNK-00030", "PAY-2026-0031", "37,465.62"] },
        { cells: ["Mar 30", "BNK-00013", "PAY-2026-0014", "11,854.13"] },
        { cells: ["Mar 30", "BNK-00086", "PAY-2026-0089", "12,363.07"] },
      ],
    },
    notes: [
      { mark: 1, title: "Where the check cleared", text: "March 22, six days after it was written, at exactly $4,325.33. The bank is independent of Harborline, so this is the strongest evidence that the money actually left.", assertion: "Occurrence (independent evidence)" },
      { title: "Reading the whole page", text: "Two of these lines pay invoices that Harborline's tests flag: PAY-2026-0049 was self-approved, and PAY-2026-0109 has an 18% payment/voucher difference. Clearing proves payment, not that it was proper." },
    ],
    noesi: "bank clearing matches every recorded payment to this feed at the same amount within 2%. PAY-2026-0009 clears. Payments that never appear here are flagged.",
    lessons: [5, 8],
  },
  {
    id: "gl", n: 6, kind: "General ledger detail", illustrative: false,
    source: "gl.csv (postings to AP control account 2000)",
    issuer: HARBORLINE, issuerLine: "General ledger · account 2000, Accounts Payable",
    docTitle: "GL DETAIL — ACCOUNT 2000", docNumber: "GL-00008",
    meta: [
      { label: "Entry", value: "GL-00008" },
      { label: "Posting date", value: "March 16, 2026", mark: 1 },
      { label: "Reference", value: "PAY-2026-0009", mark: 2 },
    ],
    table: {
      head: ["Account", "Description", "Debit", "Credit"],
      numericFrom: 2,
      rows: [
        { cells: ["2000 Accounts payable", "Kingfisher Security — VCH-2026-0009", "4,325.33", ""], mark: 3, highlight: "focus" },
        { cells: ["1010 Cash — operating (illustrative account no.)", "CHK-20009", "", "4,325.33"] },
      ],
    },
    footer: "The extract contains only account 2000 postings; the cash line is shown to complete the entry and is illustrative.",
    notes: [
      { mark: 1, title: "The period", text: "March 16 is the payment date, so it is in the right period. At year end, a December payment posted in January (or the reverse) is a cutoff error.", assertion: "Cutoff" },
      { mark: 2, title: "The reference", text: "Trace from the payment to here: every payment should post once, to account 2000, with its own reference.", assertion: "Completeness" },
      { mark: 3, title: "The amount", text: "It agrees with the check and the bank at $4,325.33. The entry clears the liability the invoice created." },
    ],
    noesi: "GL posting checks that each payment posts to the GL at the same amount and in the same period. Differences are cutoff or accuracy exceptions.",
    lessons: [6, 8],
  },
  {
    id: "tieout", n: 7, kind: "AP subledger to GL tie-out", illustrative: false,
    source: "ap_control_balance.csv",
    issuer: HARBORLINE, issuerLine: "Year-end close · December 31, 2026",
    docTitle: "AP CONTROL ACCOUNT RECONCILIATION",
    meta: [{ label: "As of", value: "December 31, 2026" }],
    table: {
      head: ["", "Amount"],
      numericFrom: 1,
      rows: [
        { cells: ["Accounts payable subledger (open invoices by vendor)", "2,731,569.42"], mark: 1 },
        { cells: ["General ledger control account 2000", "2,750,019.42"], mark: 2 },
        { cells: ["Unreconciled difference", "18,450.00"], mark: 3, highlight: "bad" },
      ],
    },
    footer: "Clearly trivial for this engagement: $21,000 · Performance materiality: $315,000.",
    notes: [
      { mark: 1, title: "The detail", text: "The subledger is the list you will test. If it does not equal the balance sheet figure, your testing covers a different number.", assertion: "Completeness" },
      { mark: 2, title: "The balance on the statements", text: "What the lender sees." },
      { mark: 3, title: "The difference", text: "$18,450, just under clearly trivial. But an unexplained control-account difference at year end says something about the close process. Argue whether it is qualitatively trivial." },
    ],
    noesi: "The subledger–GL tie reports this difference exactly: a CLASH of 18,450.00.",
    lessons: [6, 10],
  },
  {
    id: "bankrec", n: 8, kind: "Year-end bank reconciliation", illustrative: false,
    source: "payments.csv + bank.csv for the reconciling items; balances illustrative",
    issuer: HARBORLINE, issuerLine: "Operating account · December 31, 2026",
    docTitle: "BANK RECONCILIATION",
    meta: [{ label: "As of", value: "December 31, 2026" }],
    table: {
      head: ["", "Check date", "Cleared", "Amount"],
      numericFrom: 3,
      rows: [
        { cells: ["Balance per bank statement (illustrative)", "", "", "1,427,407.53"] },
        { cells: ["Less outstanding checks:", "", "", ""] },
        { cells: ["CHK-20028 · PAY-2026-0028 · Jubilee Uniform", "Dec 31", "Jan 2, 2027", "(16,830.55)"], mark: 1, highlight: "ok" },
        { cells: ["CHK-20001 · PAY-2026-0001", "Apr 30", "never", "(16,607.94)"], mark: 2, highlight: "bad" },
        { cells: ["CHK-20038 · PAY-2026-0038", "Aug 14", "never", "(20,076.43)"], mark: 2, highlight: "bad" },
        { cells: ["CHK-20116 · PAY-2026-0116", "Oct 15", "never", "(44,587.96)"], mark: 2, highlight: "bad" },
        { cells: ["CHK-20052 · PAY-2026-0052", "Nov 17", "never", "(44,804.65)"], mark: 2, highlight: "bad" },
        { cells: ["Total outstanding checks", "", "", "(142,907.53)"], mark: 3 },
        { cells: ["Balance per books (illustrative)", "", "", "1,284,500.00"] },
      ],
    },
    footer: "Deposits in transit are omitted: the case has no receipts-side data. Bank and book balances are illustrative; every reconciling item is real.",
    notes: [
      { mark: 1, title: "A normal outstanding check", text: "Written December 31 and cleared January 2. Tracing it to the January statement is the test, and it passes.", assertion: "Existence · Cutoff" },
      { mark: 2, title: "Four checks that never cleared", text: "The oldest was written in April. Checks outstanding for months are a red flag: were they ever mailed? Do the payees exist? CHK-20116 also pays VCH-2026-0116, which has no goods receipt at all.", assertion: "Existence · Occurrence" },
      { mark: 3, title: "Foot it", text: "Add the column yourself and tie each item to the check register and the January statement. Never accept a reconciliation's arithmetic on sight." },
    ],
    noesi: "bank clearing flags the four payments that never appear in the bank feed. Noesi does not build or audit the reconciliation itself.",
    lessons: [8],
  },

  // ------------------------------------------------ illustrative documents
  {
    id: "arconf", n: 9, kind: "Customer confirmation (positive)", illustrative: true,
    source: "Illustrative: the case has no receivables data",
    issuer: HARBORLINE, issuerLine: "Request sent by the auditor, on client letterhead",
    addressee: ["Chesapeake Charter Co. (illustrative)", "Accounts Payable Department"],
    docTitle: "CONFIRMATION REQUEST",
    meta: [
      { label: "Date sent", value: "January 12, 2027" },
      { label: "Balance as of", value: "December 31, 2026", mark: 1 },
      { label: "Balance per our records", value: "$86,400.00", mark: 1 },
    ],
    body: [
      "Our auditors are examining our financial statements. Please confirm directly to them whether the balance above agrees with your records as of the date shown. If it does not, please give details of any difference.",
      "Please reply directly to our auditors in the enclosed envelope addressed to them. This is not a request for payment.",
    ],
    signatures: [
      { label: "Authorized by (client)", value: "Chief Financial Officer, Harborline Marine Group" },
      { label: "Customer reply", value: "☐ Agrees   ☒ Does not agree: paid $30,000 on Dec 30, check 4417", mark: 2, tone: "bad" },
    ],
    footer: "Reply to: [Audit firm], Engagement: Harborline Marine Group, FYE 12/31/2026",
    notes: [
      { mark: 1, title: "What is being confirmed", text: "A specific balance at a specific date, taken from the aged receivables listing, which you tie to the GL first.", assertion: "Existence" },
      { mark: 2, title: "An exception", text: "The customer says it paid $30,000 on December 30. Either cash in transit (a timing difference) or a payment misapplied or taken. Trace it to the January deposits and the cash receipts journal." },
      { title: "Control of the process", text: "The auditor mails it and the reply comes straight back to the auditor. A reply that routes through the client is worthless." },
    ],
    noesi: "Not in Noesi: there are no receivables procedures and no confirmation tracking. A reply received as a PDF can be stored in the evidence vault.",
    lessons: [7],
  },
  {
    id: "bankconf", n: 10, kind: "Bank confirmation", illustrative: true,
    source: "Illustrative",
    issuer: "[Audit firm]", issuerLine: "Request authorized by Harborline Marine Group",
    addressee: ["Operating bank (illustrative)", "Confirmation services"],
    docTitle: "BANK CONFIRMATION",
    meta: [{ label: "As of", value: "December 31, 2026", mark: 1 }],
    table: {
      head: ["Account", "Type", "Balance", "Rate"],
      numericFrom: 2,
      rows: [
        { cells: ["Operating ••4471", "Checking", "1,427,407.53", "—"], mark: 1, highlight: "focus" },
        { cells: ["Line of credit", "Loan (limit $6,000,000)", "3,150,000.00", "Prime + 1.25%"], mark: 2 },
      ],
    },
    signatures: [{ label: "Confirmed by (bank officer)", value: "Signed and returned directly to the auditor" }],
    notes: [
      { mark: 1, title: "The cash balance", text: "It agrees with 'balance per bank' on the reconciliation (document 8). Independent evidence of existence.", assertion: "Existence" },
      { mark: 2, title: "Loans and covenants", text: "The bank also confirms borrowings: here the $6 million line from the engagement brief. Unrecorded debt surfaces this way.", assertion: "Completeness · Presentation" },
      { title: "What changes in 2028", text: "SAS 150 makes confirming cash held by third parties a requirement unless certain conditions exist, for periods ending on or after December 15, 2028." },
    ],
    noesi: "Not in Noesi. Bank clearing uses a bank feed of payments, not a confirmation of the balance.",
    lessons: [8],
  },
  {
    id: "count", n: 11, kind: "Inventory count sheet", illustrative: true,
    source: "Illustrative: the case has no inventory data",
    issuer: HARBORLINE, issuerLine: "Physical inventory · Norfolk parts warehouse · December 31, 2026",
    docTitle: "COUNT SHEET", docNumber: "Sheet 14 of 62",
    meta: [
      { label: "Counted by", value: "Warehouse team B" },
      { label: "Last receiving report before count", value: "GRN-2026-0127", mark: 3 },
    ],
    table: {
      head: ["Tag", "SKU", "Description", "Client count", "Auditor test count"],
      numericFrom: 3,
      rows: [
        { cells: ["1401", "PRP-3B-14", "Propeller, 3-blade, 14 in.", "22", "22 ✓"] },
        { cells: ["1402", "IMP-WP-60", "Impeller, water pump", "140", "132 ✗"], mark: 1, highlight: "bad" },
        { cells: ["1403", "BAT-AGM-100", "Marine battery, AGM 100Ah", "36", "—"] },
        { cells: ["1404", "VSL-CN-2210", "24 ft center console (consigned — Sandbar Boats)", "1", "1 ✓"], mark: 2, highlight: "focus" },
      ],
    },
    footer: "✓ agreed · ✗ difference · — not test-counted",
    notes: [
      { mark: 1, title: "A test-count difference", text: "132 on the shelf against 140 recorded. Recount with the client, correct the sheet, and consider whether errors like this are widespread before relying on the count.", assertion: "Existence · Accuracy" },
      { mark: 2, title: "It is here, but it is not theirs", text: "A consigned boat belongs to the manufacturer. It must be excluded from Harborline's inventory even though it exists.", assertion: "Rights and obligations" },
      { mark: 3, title: "Cutoff information", text: "Record the last receiving and shipping document numbers. Goods received after GRN-2026-0127 must not be in the count, and goods received before it must be in both inventory and payables." },
    ],
    noesi: "Not in Noesi: there are no inventory procedures. Count sheets can be stored in the vault as PDF or CSV.",
    lessons: [9],
  },
  {
    id: "reps", n: 12, kind: "Management representation letter", illustrative: true,
    source: "Illustrative excerpt",
    issuer: HARBORLINE, issuerLine: "On company letterhead",
    addressee: ["[Audit firm]"],
    docTitle: "REPRESENTATION LETTER",
    meta: [{ label: "Date", value: "the date of the auditor's report", mark: 1 }],
    body: [
      "We confirm, to the best of our knowledge and belief, the following representations made to you during your audit of the financial statements of Harborline Marine Group, Inc. as of and for the year ended December 31, 2026:",
      "1. We have fulfilled our responsibilities for the preparation and fair presentation of the financial statements in accordance with U.S. GAAP, and for the design, implementation and maintenance of internal control.",
      "2. We have provided you with all relevant information and access, and all transactions have been recorded in the accounting records.",
      "3. All liabilities, both actual and contingent, have been recorded or disclosed, including those arising after the approval-limit changes during the June–September supervisor vacancy.",
      "4. All events subsequent to the date of the financial statements that require adjustment or disclosure have been adjusted or disclosed.",
      "5. The effects of uncorrected misstatements summarized in the attached schedule are immaterial, individually and in aggregate.",
    ],
    signatures: [
      { label: "Chief Executive Officer", value: "signature", mark: 2 },
      { label: "Chief Financial Officer", value: "signature", mark: 2 },
    ],
    notes: [
      { mark: 1, title: "The date", text: "Dated as of the auditor's report date, not year end, so it covers subsequent events up to the day you sign." },
      { mark: 2, title: "Who signs", text: "Those with overall responsibility and knowledge: normally the CEO and CFO. A refusal is a scope limitation." },
      { title: "Representations are not evidence of amounts", text: "Paragraph 3 does not prove liabilities are complete. It supports your search for unrecorded liabilities and does not replace it." },
    ],
    noesi: "Management representations is one of Noesi's six completion checks. It needs a note or evidence, and the lock stays blocked until it is done. Noesi does not draft the letter.",
    lessons: [10],
  },
];
