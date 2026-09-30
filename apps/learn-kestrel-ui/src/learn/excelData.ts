// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** "Excel for audit": exercises on the Kestrel files. Every answer is read
 *  from kestrel-key.json (the answer key) or kestrel-records.json (the case
 *  files); none is typed. */

import { keyAt } from "./keyData";
import { usd } from "./records";

export type Exercise = {
  skill: string;
  audit: string;
  file: string;
  steps: string[];
  formula?: string;
  answer: string;
  noesi: string;
  module: number;
};

const k = (path: string) => keyAt(path) ?? "(missing from the key)";
const LIMIT = k("payables.split_bills.approval_limit");
const LIMIT_N = String(Number(LIMIT));
const est = (i: number) => `${k(`part3.estimates.items.${i}.estimate`)} ${Number(k(`part3.estimates.items.${i}.miss_pct`)).toFixed(1)}%`;
const splits = (keyAt("payables.split_bills.bills") ?? "").split(", ").map(usd).join(", ");

export const EXERCISES: Exercise[] = [
  {
    skill: "SUM and footing",
    audit: "Foot the payroll register and tie it to the ledger before testing it",
    file: "client/payroll_register_FY2026.csv + quickbooks/Trial_Balance_2026-06-30.xlsx",
    steps: [
      "Open the register. Select the Gross Pay column (C) and read the Sum on the status bar.",
      "Write it into a cell with the formula below so the footing is documented.",
      "Find account 60100 Wages and Salaries in the trial balance and compare.",
    ],
    formula: "=SUM(C:C)",
    answer: `Register gross ${usd(k("part2.payroll.register_gross"))}; wages per the ledger ${usd(k("part2.payroll.tb_wages_60100"))}; difference ${usd(k("part2.payroll.difference"))}. It ties, which proves the totals agree, not that the people are real.`,
    noesi: "payroll.register_to_ledger makes the same tie.",
    module: 8,
  },
  {
    skill: "Tables, filters and a helper column",
    audit: "Payroll arithmetic: does gross less taxes equal net on every row?",
    file: "client/payroll_register_FY2026.csv",
    steps: [
      "Click any cell, then Home → Format as Table. Tick \"My table has headers\".",
      "In the first empty column (G), type the heading Check. In G2 enter the formula below; the table fills it down.",
      "Use the filter arrow on Check and hide 0.",
    ],
    formula: "=ROUND(C2-D2-E2,2)",
    answer: `One row: employee ${k("part2.payroll.net_pay_error.id")} on ${k("part2.payroll.net_pay_error.date")}, net pay over by ${usd(k("part2.payroll.net_pay_error.over_by"))}.`,
    noesi: "payroll.register_tests reports it as net pay differs.",
    module: 8,
  },
  {
    skill: "XLOOKUP across two sheets",
    audit: "Ghost employees: is everyone paid on the employee master?",
    file: "client/payroll_register_FY2026.csv + client/employee_master.csv",
    steps: [
      "Copy all of employee_master.csv into a new sheet in the same workbook and name the sheet master.",
      "Back on the register, enter the formula below in column G (Name on master).",
      "Filter for not found. Count the rows and sum Net Pay for them.",
    ],
    formula: "=XLOOKUP(A2,master!A:A,master!B:B,\"not found\")",
    answer: `Employee ${k("part2.payroll.ghost_employee.id")} is not on the master: ${k("part2.payroll.ghost_employee.payments")} payments, ${usd(k("part2.payroll.ghost_employee.net_paid"))} net.`,
    noesi: "payroll.register_tests lists each payment to an ID not on the master.",
    module: 8,
  },
  {
    skill: "COUNTIF",
    audit: "Two employees paid into one bank account",
    file: "client/employee_master.csv",
    steps: [
      "In column H enter the formula below; it counts how many employees share each row's Direct Deposit Account (column F).",
      "Filter column H for values greater than 1.",
    ],
    formula: "=COUNTIF(F:F,F2)",
    answer: `${k("part2.payroll.shared_bank_account")} share one account.`,
    noesi: "payroll.register_tests reports the shared account.",
    module: 8,
  },
  {
    skill: "Filling down a report's group labels",
    audit: "Duplicate bills: the same supplier invoice number entered twice",
    file: "quickbooks/Transaction_List_by_Vendor.xlsx",
    steps: [
      "QuickBooks prints the vendor name once, above its transactions. Add a Vendor column (K): in K6 enter =IF(A6<>\"\",A6,K5) and fill it down, so every row carries its vendor.",
      "In column L enter the formula below. It counts the bills with the same Num (column E).",
      "Filter Transaction type (D) for Bill and column L for values greater than 1. Read the vendor on each. Two bills with a blank Num also pair up: those are the bills without a number, a separate finding.",
    ],
    formula: "=COUNTIFS(E:E,E6,D:D,\"Bill\")",
    answer: `${k("payables.duplicate_bill.invoice")}, ${usd(k("payables.duplicate_bill.amount"))}, under both ${k("payables.duplicate_bill.twin_of")} and ${k("payables.duplicate_bill.vendor")} (${k("payables.duplicate_bill.original_date")} and ${k("payables.duplicate_bill.duplicate_date")}).`,
    noesi: "ap.duplicate_bills finds the pair across the twin vendor records.",
    module: 5,
  },
  {
    skill: "COUNTIFS with dates",
    audit: `Split bills: several bills to one vendor, each under the ${usd(LIMIT)} approval limit, within a week`,
    file: "quickbooks/Transaction_List_by_Vendor.xlsx (with the Vendor column from the last exercise)",
    steps: [
      "QuickBooks exports the dates as text. In column M enter =DATEVALUE(B6) and format it as a date.",
      "In column N enter the formula below: for each bill under the limit, how many bills under the limit did the same vendor get within seven days either side?",
      "Filter Transaction type for Bill and column N for values of 3 or more.",
    ],
    formula: `=COUNTIFS(K:K,K6,D:D,"Bill",J:J,"<${LIMIT_N}",M:M,">="&(M6-7),M:M,"<="&(M6+7))`,
    answer: `${k("payables.split_bills.vendor")}: bills of ${splits}; ${usd(k("payables.split_bills.total"))} in total. One purchase, cut under the limit.`,
    noesi: "ap.split_payment_review, with the approved split threshold and window, reports the same cluster.",
    module: 5,
  },
  {
    skill: "SUMIFS",
    audit: "Payments with no bill behind them",
    file: "quickbooks/Transaction_List_by_Vendor.xlsx (with the Vendor column)",
    steps: [
      "Filter Transaction type for Check. These are payments written straight to a payee, not bill payments.",
      "For each payee, check whether it has any Bill row. Four payees are paid only by check.",
      "For each, look for the support elsewhere: a loan agreement, a tax return, an asset addition vouched to its invoice. One has no support at all. Total its checks with the formula below.",
    ],
    formula: "=SUMIFS(J:J,K:K,\"DM Consulting\",D:D,\"Check\")",
    answer: `${k("payables.checks_without_bills.vendor")}: ${usd(k("payables.checks_without_bills.total"))} in checks, no bills. Its address matches ${k("payables.checks_without_bills.address_matches")}. The other three (the bank's loan payments, a state tax payment, the racking purchase) have support outside payables.`,
    noesi: "ap.payments_without_bills lists payees paid by check with no bills, DM Consulting among them; the support for each is yours to find. payroll.register_tests finds the shared address.",
    module: 5,
  },
  {
    skill: "A percentage column",
    audit: "Retrospective review: how far did last year's estimates miss?",
    file: "client/prior_year_estimates.csv",
    steps: [
      "In column D enter the formula below and format it as a percentage.",
      `Mark each miss beyond the ${k("part3.estimates.hindsight_threshold_pct")}% threshold, and note the direction of every miss.`,
    ],
    formula: "=(C2-B2)/B2",
    answer: `${est(0)}; ${est(1)}; ${est(2)}; ${est(3)}. Every outcome came in above the estimate: an indicator of possible bias.`,
    noesi: "estimates.retrospective_review reports each miss and the one-direction indicator.",
    module: 11,
  },
];

