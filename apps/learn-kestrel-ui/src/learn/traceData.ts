// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** "Follow a number": the duplicate Moraine invoice, from the order to the
 *  misstatement schedule. Figures from kestrel-records.json and
 *  kestrel-key.json only; the boundary between the records and a teaching
 *  entry stays visible. */

import { keyAt } from "./keyData";
import { BILL, DUP_LINE, DUPLICATE, PAY_DUPLICATE, PAY_ORIGINAL, PO, usd } from "./records";

export type Stage = {
  title: string;
  amount: string;
  status: string;
  question: string;
  evidenceHeading: string;
  observed: string[];
  meaning: string;
  limit: string;
  source: string;
};

const AMOUNT = usd(DUPLICATE.amount);
const LARGEST = usd(keyAt("part3.final_misstatements.largest") ?? "0");
const MATERIALITY = usd(keyAt("part3.final_misstatements.materiality") ?? "0");

export const HEADLINE = AMOUNT;

export const STAGES: Stage[] = [
  {
    title: "The business event", amount: `${usd(PO.amount)} ordered`, status: "Source records",
    question: "What did Kestrel agree to buy, and what was billed?",
    evidenceHeading: "What the records show",
    observed: [
      `Purchase order ${PO.num}, dated ${PO.date}, orders ${usd(PO.amount)} from ${PO.vendor}.`,
      `Bill ${BILL.num}, dated ${BILL.date}, bills ${usd(BILL.amount)}; its memo reads "${BILL.memo}".`,
      `The bill posts to ${BILL.split} and ${BILL.account}.`,
    ],
    meaning: "An order is a commitment, not yet a cost or a payable. The bill records the goods as inventory and the amount owed to the supplier.",
    limit: "QuickBooks Online at Kestrel records no receipt of goods, so the records cannot show that the goods arrived; only inquiry or inspection can.",
    source: "quickbooks/Transaction_List_by_Vendor.xlsx: Purchase Order and Bill rows",
  },
  {
    title: "The same bill again", amount: `${AMOUNT} billed again`, status: "Observed",
    question: "What does the second bill record, and how would anyone notice?",
    evidenceHeading: "What the records show",
    observed: [
      `Bill ${DUPLICATE.num}, dated ${DUPLICATE.date}, for ${AMOUNT}, under the vendor record ${DUPLICATE.vendor}.`,
      "That record has the same phone and address as the original supplier.",
      `It carries no purchase order in its memo and posts to ${DUPLICATE.split} again.`,
    ],
    meaning: "The same supplier invoice, entered a second time under a twin vendor record, debits inventory for goods received once. Only the supplier's invoice number gives it away: sort bills by it and the pair sits together.",
    limit: "The records cannot say whether this was a slip or a scheme. A twin record created by the person who enters and pays bills is a lead to follow up, not a conclusion.",
    source: "quickbooks/Transaction_List_by_Vendor.xlsx · quickbooks/Vendor_Contact_List.xlsx",
  },
  {
    title: "Payment", amount: `${usd(PAY_DUPLICATE.amount)} paid`, status: "Observed with a limit",
    question: "Was the duplicate paid?",
    evidenceHeading: "What the records show",
    observed: [
      `Check ${PAY_DUPLICATE.num}, dated ${PAY_DUPLICATE.date}, pays ${usd(PAY_DUPLICATE.amount)} to ${PAY_DUPLICATE.vendor}: the duplicate's amount to the cent.`,
      `Check ${PAY_ORIGINAL.num}, dated ${PAY_ORIGINAL.date}, pays ${usd(PAY_ORIGINAL.amount)} to the original record, a payment for several bills.`,
      "Both are bill payments from the checking account.",
    ],
    meaning: "For a bill payment, debit Accounts Payable to clear the obligation and credit Cash. The duplicate's payable was cleared by a real check: the money left.",
    limit: "The export lists each check and its payee, not which bills it pays. That the smaller check pays the duplicate is an inference from the exact amount; ask the client for the payment's bill detail to prove it.",
    source: "quickbooks/Transaction_List_by_Vendor.xlsx: Bill Payment (Check) rows",
  },
  {
    title: "Toward the statements", amount: `${AMOUNT} overstated cost`, status: "Where it lands",
    question: "Where would this appear in the financial statements?",
    evidenceHeading: "What we can connect",
    observed: [
      "The second bill debited inventory. As goods sell, inventory cost moves to cost of goods sold on the income statement.",
      "The payable is gone (paid), so the balance sheet shows nothing owed to the supplier for it.",
      "What is missing is the other side: the supplier owes Kestrel a refund that is recorded nowhere.",
    ],
    meaning: `Correcting it records a receivable from the supplier and reduces cost: current assets and income each go up by ${AMOUNT}.`,
    limit: "Whether the cost still sits in inventory or has moved to cost of sales depends on sales after March; the records do not tie this one invoice to either.",
    source: "quickbooks/Trial_Balance_2026-06-30.xlsx · the correcting entry is a teaching model below",
  },
  {
    title: "What we can conclude", amount: `${LARGEST} on current assets`, status: "Finding, not conclusion",
    question: "What does the audit do with it?",
    evidenceHeading: "What the records show",
    observed: [
      `The team's schedule of uncorrected misstatements carries "${DUP_LINE.Description}" (${DUP_LINE["WP Reference"]}) at ${usd(DUP_LINE.Identified)}.`,
      `With the other uncorrected items, current assets are misstated by ${LARGEST} in total, against materiality of ${MATERIALITY}.`,
      "That line is one of the matters the draft opinion turns on.",
    ],
    meaning: "One duplicate invoice, found by sorting on the supplier's invoice number, is most of the reason one statement line is materially misstated.",
    limit: "The finding is not a misstatement conclusion or an opinion: management may still record the refund, and the partner decides what the uncorrected total means.",
    source: "auditor/uncorrected_misstatements_final.csv · answer key, final misstatements",
  },
];

/** The correcting entry, as a teaching model (not in Kestrel's books). */
export const CORRECTION = {
  debit: "Receivable from Moraine Cycle Components (refund due)",
  credit: "Cost of goods sold (or Inventory, if unsold)",
  amount: DUPLICATE.amount,
};
