// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** "Fraud at Kestrel": the fraud track, on the schemes planted in the Kestrel
 *  case. Same topics and order as the Harborline track (apps/studio-ui,
 *  lessons-fraud.ts), each lesson in the Kestrel four steps.
 *
 *  No figure is typed here: answers name lines of the finish-line check
 *  (`row`, in `module`) and paths into the answer key (`key`), and
 *  scripts/check-lessons.mjs refuses prose numbers the key does not hold.
 *
 *  The forensic tests and the two schemes added on 2 Oct 2026 (ROADMAP D10,
 *  E3) are taught here too: missing check numbers, a vendor named after an
 *  employee, checks signed by the person who prepared them, and money sent
 *  out and back through a related party. */

import { Lesson } from "./types";

const DEMO_START = "Start the Workbench with the Kestrel demo: `python -m workbench_api --demo`, open the address it prints, and open **Kestrel Valley Cycle Supply (demo)**. (Without `--demo`, choose Kestrel under **load teaching case**.)";
const JOURNAL_NOTE = "The demo loads QuickBooks' Journal export raw, through its QuickBooks recipe; **Sources & Mappings** shows the rows loaded and footed.";
const PAYABLES = "Payables", PAYROLL = "Payroll", JOURNAL = "Journal entries", CASH = "Cash";
const ESTIMATES = "Estimates and related parties", COMPLETION = "Completion";

export const FRAUD_LESSONS: Lesson[] = [
  {
    n: 1,
    slug: "fraud-why-it-happens",
    video: {
      file: "kestrel-f01-trust-is-not-a-control.mp4",
      poster: "kestrel-f01-trust-is-not-a-control.jpg",
      title: "Trust is not a control",
      minutes: 3,
      credits: "Narration: ElevenLabs voice “Guy”. Screens: Noesi Workbench and Noesi Learn on the Kestrel demo; spreadsheet views drawn from the case files. Photos: Wikimedia Commons, each credited on screen.",
    },
    title: "Why fraud happens",
    phase: "Fraud",
    question: "What turns an employee into a fraudster, and what at Kestrel made it possible?",
    minutes: 25,
    objectives: [
      "Tell fraud apart from error by intent, not by the trace it leaves",
      "Explain the three sides of the fraud triangle and which one the company controls",
      "Place a scheme on the three branches of the fraud tree",
      "Name the opportunity Kestrel's setup creates",
    ],
    sections: [
      {
        heading: "Fraud is about intent",
        blocks: [
          { p: "An **error** is an unintentional mistake. **Fraud** is intentional deception to gain something the person is not entitled to. The two can leave identical traces in the records; what separates them is intent, and intent is exactly what records rarely show." },
          { p: "That is why an auditor's data finding is always a **lead**, never a conclusion of fraud. Concluding fraud is a legal judgment, made on evidence gathered by people trained to gather it." },
        ],
      },
      {
        heading: "The fraud triangle",
        blocks: [
          { terms: [
            ["Pressure", "A need the person feels they cannot share: debt, a lifestyle, a target to hit."],
            ["Opportunity", "A way to commit it and hide it: a control that is missing, or one person holding duties that should be split."],
            ["Rationalization", "A story that makes it acceptable: \"I'm underpaid\", \"I'll pay it back\"."],
          ] },
          { p: "An auditor can rarely see pressure or rationalization. **Opportunity** is the side the company controls, and the side the audit can assess: who can do what, alone, without anyone else seeing." },
        ],
      },
      {
        heading: "The fraud tree",
        blocks: [
          { p: "Occupational fraud falls on three branches: **asset misappropriation** (taking cash or goods: billing schemes, payroll schemes, check tampering), **corruption** (bribes, kickbacks, conflicts of interest), and **financial statement fraud** (misstating the numbers). Most cases are the first; the last is rarer and costlier." },
        ],
      },
      {
        heading: "Opportunity at Kestrel",
        blocks: [
          { kestrel: "Kestrel is small. One bookkeeper, Dana Merritt, is the authorized QuickBooks user who posts the entries, and also reconciles the bank. QuickBooks Online records no receipt of goods and no approver. The managing member can post entries directly. None of that is fraud. All of it is opportunity, and the rest of this track follows what grew in it." },
          { watch: "\"Small company, one trusted bookkeeper\" is the setting of a great many real cases. Trust is not a control." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "The auditor's responsibilities relating to fraud: professional skepticism, the fraud triangle's conditions, and the presumed risks"],
      ["AU-C 315", "Understanding internal control, including segregation of duties"],
    ],
    check: [
      { q: "A data test finds a payment that matches the pattern of a billing scheme. What is it?",
        options: ["Proof of fraud", "A lead that needs follow-up; intent is not in the data", "An error", "Nothing, unless it is material"],
        answer: 1,
        why: "The same record can come from error or fraud. The finding tells you where to look, not what happened." },
      { q: "Which side of the fraud triangle can a company most directly reduce?",
        options: ["Pressure", "Opportunity", "Rationalization", "None of them"],
        answer: 1,
        why: "Controls and segregation of duties remove opportunity. Pressure and rationalization live in people's lives." },
    ],
    byHand: {
      files: ["quickbooks/Vendor_Contact_List.xlsx", "client/employee_master.csv", "quickbooks/Checking_Reconciliation.xlsx", "the case README.md"],
      intro: "Map who can do what at Kestrel, from the files alone.",
      steps: [
        "From the reconciliation report's header, note who reconciled the bank; in the Journal, note who created the entries.",
        "Compare every employee's home address with every vendor's billing address.",
        "Look at the payables exports for an approver column, and for any record that goods were received.",
      ],
      asks: [
        { label: "Employee whose address is a vendor's", row: "bookkeeper's address is a vendor's (E07, DM Consulting)", module: PAYROLL, key: "part2.payroll.bookkeeper_address_is_a_vendor_address.employee" },
        { label: "Can the exports show who approved a payment?", row: "segregation of duties not testable", module: PAYABLES, key: "payables.segregation_of_duties" },
        { label: "Can they show goods were received?", row: "three-way match not testable", module: PAYABLES, key: "payables.purchase_orders.three_way_match" },
      ],
    },
    inNoesi: {
      procedures: ["Coverage", "payroll.register_tests"],
      steps: [
        DEMO_START,
        "**Coverage:** find the payables procedures marked blocked or partial, and read why. Each is an opportunity the records cannot rule out.",
        "**Runs & Findings:** open `payroll.register_tests` and find the address finding.",
      ],
    },
    keyModule: PAYABLES,
    keyLines: [
      [PAYROLL, "bookkeeper's address is a vendor's (E07, DM Consulting)"],
      [PAYABLES, "segregation of duties not testable"],
      [PAYABLES, "three-way match not testable"],
    ],
    noesi: {
      coverage: "partial",
      summary: "Noesi shows where the records cannot rule a scheme out, and finds the patterns the data does hold. It cannot see pressure, rationalization or intent.",
      does: [
        "Marks tests the records cannot support as blocked or partial, with the reason, rather than passing them.",
        "Compares employee and vendor addresses across the whole population.",
      ],
      where: ["Workbench → Coverage", "Workbench → Runs & Findings"],
      doesNot: [
        "It cannot judge intent or conclude that fraud occurred.",
        "It cannot see who really does what in the office; that takes a walkthrough and inquiry.",
      ],
    },
  },

  {
    n: 2,
    slug: "fraud-risk-assessment",
    title: "Fraud risk assessment",
    phase: "Fraud",
    question: "Where could fraud happen at Kestrel, and which risks are presumed in every audit?",
    minutes: 35,
    objectives: [
      "State the two fraud risks AU-C 240 presumes in every audit",
      "Explain why journal entries are tested for management override",
      "Read a journal entry's who, when and how much for signs of override",
    ],
    sections: [
      {
        heading: "Two risks presumed everywhere",
        blocks: [
          { p: "AU-C 240 presumes a fraud risk in **revenue recognition** (the auditor may rebut it, with reasons) and treats **management override of controls** as a risk in every audit, never rebutted. Management can post an entry, change an estimate or record a transaction that no control below it will stop." },
          { p: "So every audit tests journal entries, reviews estimates for bias, and looks at significant unusual transactions." },
        ],
      },
      {
        heading: "What a suspicious entry looks like",
        blocks: [
          { list: [
            "Posted by someone who does not normally post entries.",
            "Posted on a weekend or a holiday, when no one else is around.",
            "A round amount, as an estimate or a plug usually is.",
            "Posted to an account that is seldom used.",
            "Posted after the period end but dated inside it.",
            "A manual entry with no description.",
          ] },
          { p: "No single trait means fraud. An entry with several is one to pull and ask about." },
        ],
      },
      {
        heading: "Kestrel's journal",
        blocks: [
          { kestrel: "The partner's policies name the authorized journal user (the bookkeeper), the holidays, the round-amount threshold and unit, and how rarely an account must be used to count as seldom used. The journal is QuickBooks' own Journal report, one row per line." },
          { watch: "An entry by the owner is not wrong in itself: owners of small companies post entries. It is the combination, owner and weekend and round and large, that asks for a question." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "Presumed fraud risks: revenue recognition and management override; journal entry testing"],
      ["AU-C 330", "Responses to assessed risks of material misstatement"],
    ],
    check: [
      { q: "Which fraud risk can the auditor never rebut?",
        options: ["Revenue recognition", "Management override of controls", "Inventory theft", "Payroll fraud"],
        answer: 1,
        why: "Management sits above the controls, so override is a risk in every entity. Revenue recognition is presumed but may be rebutted." },
      { q: "An entry was posted on a Saturday by the managing member for a round amount. What do you do?",
        options: ["Reverse it", "Ask for the support and the reason, and see what accounts it touched", "Report fraud to the lender", "Ignore it; owners can post entries"],
        answer: 1,
        why: "It carries several traits of override. The next step is evidence and inquiry, not a conclusion." },
    ],
    byHand: {
      files: ["quickbooks/Journal.xlsx"],
      intro: "Test the year's journal for the traits of override.",
      steps: [
        "QuickBooks groups each transaction's lines under its transaction ID, closed by a **Total for** row; date, type, number and name repeat on every line, so each line already carries its entry.",
        "Filter **Created by** for anyone other than the authorized user.",
        "Add a weekday column (`=WEEKDAY(date)`) and filter for Saturday and Sunday.",
        "Filter amounts at or above the round-amount threshold that are exact multiples of the round unit.",
        "Filter manual journal entries with a blank **Description**.",
      ],
      asks: [
        { label: "Who posted an entry outside the authorized user?", row: "unauthorized user: entries", module: JOURNAL, key: "payables.owner_entry.by" },
        { label: "Which entry?", row: "unauthorized user: entries", module: JOURNAL, key: "payables.owner_entry.num" },
        { label: "On what day of the week?", row: "weekend or holiday: entries", module: JOURNAL, key: "payables.owner_entry.weekday" },
        { label: "For how much?", row: "round amount: entries", module: JOURNAL, key: "payables.owner_entry.amount" },
        { label: "The manual entry with no description", row: "manual entries without a description", module: JOURNAL, key: "payables.no_description_entry" },
      ],
    },
    inNoesi: {
      procedures: ["je.journal_entry_testing"],
      steps: [
        DEMO_START,
        "**Scope & Policies:** read the journal-entry policies (authorized users, holidays, round amounts, seldom-used accounts).",
        "**Runs & Findings:** open `je.journal_entry_testing` and read the findings by test. Find the entry that appears under several tests.",
        JOURNAL_NOTE,
      ],
    },
    keyModule: JOURNAL,
    keyLines: [
      [JOURNAL, "unauthorized user: entries"],
      [JOURNAL, "weekend or holiday: entries"],
      [JOURNAL, "round amount: entries"],
      [JOURNAL, "posted after period end: entries"],
      [JOURNAL, "manual entries without a description"],
    ],
    noesi: {
      coverage: "partial",
      summary: "Noesi runs the journal-entry tests on every line of the year, under the partner's policies, and lists each entry with the traits it has.",
      does: [
        "Tests every entry for unauthorized users, weekends and holidays, round amounts, seldom-used accounts, posting after period end, and missing descriptions.",
        "Lets an entry that shows up under several tests stand out.",
      ],
      where: ["Workbench → Scope & Policies", "Workbench → Runs & Findings (journal entries)"],
      doesNot: [
        "It cannot say why an entry was posted; the support and the conversation are yours.",
        "It tests only the entries in the Journal it is given; the population check is what says whether that is all of them.",
      ],
    },
  },

  {
    n: 3,
    slug: "fraud-billing-schemes",
    title: "Billing schemes and shell vendors",
    phase: "Fraud",
    question: "How does a fake or duplicated bill get paid, and what trace does it leave?",
    minutes: 35,
    objectives: [
      "Describe the shell-vendor and duplicate-billing schemes",
      "Find twin vendor records and a supplier invoice entered twice",
      "Find payments with no bill behind them",
    ],
    sections: [
      {
        heading: "Billing schemes",
        blocks: [
          { p: "A billing scheme makes the company pay a bill it does not owe. Three common forms:" },
          { terms: [
            ["Shell vendor", "A company that exists on paper, set up by the fraudster, billing for goods or services never delivered."],
            ["Duplicate billing", "A real supplier's invoice paid twice, often through a second vendor record for the same supplier."],
            ["Personal purchases", "The company pays for things the employee keeps."],
          ] },
        ],
      },
      {
        heading: "The traces",
        blocks: [
          { list: [
            "Two vendor records with the same address, phone or bank account.",
            "The same supplier invoice number twice.",
            "A vendor paid by plain checks, with no invoices on file.",
            "A vendor whose address is an employee's.",
          ] },
          { watch: "A shell vendor rarely looks strange on its own. Its address, its lack of bills, and who set it up are what give it away." },
        ],
      },
      {
        heading: "At Kestrel",
        blocks: [
          { kestrel: "Kestrel has both. One supplier appears twice on the vendor list, and one invoice was entered under each record and paid twice. And one vendor, a \"consulting\" firm, was paid by checks with no bills at all." },
        ],
      },
      {
        heading: "A vendor named after an employee",
        blocks: [
          { p: "An employee who sets up a vendor in their own name, or a relative's, can bill the company for work they are already paid to do, or for work never done. The trace is a vendor that shares a bank account, phone number or tax ID with an employee, or carries an employee's full name." },
          { kestrel: "Kestrel's vendor list includes a hauling firm carrying the full name of a warehouse employee. It billed freight three times during the year. QuickBooks' vendor export carries no bank account or tax ID, so the name is the only match these records allow." },
          { watch: "A shared name can be a coincidence or a relative. It is a question for the employee and their manager, and a reason to look at what the vendor was paid for." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "Fraud risk factors and responses: asset misappropriation"],
      ["AU-C 500", "Audit evidence: vouching payments to invoices"],
    ],
    check: [
      { q: "The same invoice number appears under two vendor names with the same address and phone. What is the likeliest scheme?",
        options: ["Personal purchases", "Duplicate billing through a twin vendor record", "Kiting", "A ghost employee"],
        answer: 1,
        why: "A twin record lets one real invoice be entered and paid twice." },
      { q: "A vendor is paid every quarter by plain checks and has no bills on file. What do you ask for first?",
        options: ["A bank confirmation", "The invoices and the contract behind the payments, and who set the vendor up", "The vendor's tax return", "Nothing; consulting is often informal"],
        answer: 1,
        why: "A payment should have a bill and an agreement behind it. Their absence is the finding; who created the vendor is the next question." },
    ],
    byHand: {
      files: ["quickbooks/Vendor_Contact_List.xlsx", "quickbooks/Transaction_List_by_Vendor.xlsx", "client/employee_master.csv"],
      intro: "Look for twin vendors, duplicate invoices and checks without bills.",
      steps: [
        "Sort the vendor list by address, then by phone. Note any pair that looks like one supplier.",
        "In the Transaction List by Vendor, sort the bills by **Num** and find an invoice number under two vendors.",
        "Filter **Transaction type** for Check. Find the vendor with checks but no bills and no other support; total the checks.",
        "Compare that vendor's address with the employee master.",
        "Compare every vendor name with every employee's full name.",
      ],
      asks: [
        { label: "The twin of Moraine Cycle Components", row: "vendor twins", module: PAYABLES, key: "payables.duplicate_bill.vendor" },
        { label: "Invoice entered twice", row: "duplicate bill MC-25009", module: PAYABLES, key: "payables.duplicate_bill.invoice" },
        { label: "Its amount", row: "duplicate's misstatement", module: PAYABLES },
        { label: "Vendor paid by checks with no bills", row: "checks without bills: DM Consulting", module: PAYABLES, key: "payables.checks_without_bills.vendor" },
        { label: "Those checks' total", row: "checks without bills: DM Consulting", module: PAYABLES },
        { label: "Vendor carrying an employee's name", row: "vendor named after an employee: Owen Pike Hauling (E08)", module: PAYABLES, key: "payables.vendor_employee_match.vendor" },
        { label: "That employee (ID)", row: "vendor named after an employee: Owen Pike Hauling (E08)", module: PAYABLES, key: "payables.vendor_employee_match.employee" },
        { label: "Paid to that vendor", row: "vendor named after an employee: Owen Pike Hauling (E08)", module: PAYABLES, key: "payables.vendor_employee_match.paid" },
      ],
    },
    inNoesi: {
      procedures: ["ap.vendor_relational_twins", "ap.duplicate_bills", "ap.payments_without_bills",
                   "forensic.vendor_employee_match"],
      steps: [
        DEMO_START,
        "**Runs & Findings:** open each procedure above. The vendor list and payables exports load raw from QuickBooks.",
        "In `forensic.vendor_employee_match`, read which fields were compared and which were not, and why.",
        "Open **The documents** page of this course to see the duplicate trail laid out, document by document.",
      ],
    },
    keyModule: PAYABLES,
    keyLines: [
      [PAYABLES, "vendor twins"],
      [PAYABLES, "duplicate bill MC-25009"],
      [PAYABLES, "duplicate's misstatement"],
      [PAYABLES, "checks without bills: DM Consulting"],
      [PAYABLES, "vendor named after an employee: Owen Pike Hauling (E08)"],
      [PAYABLES, "vendors matching an employee (leads)"],
    ],
    noesi: {
      coverage: "partial",
      summary: "Noesi finds twin vendors, duplicate invoices, checks without bills and vendors that match an employee, across every row of QuickBooks' own exports.",
      does: [
        "Pairs vendor records by name, address and phone.",
        "Finds a supplier invoice number entered more than once, across vendor records, and states the amount.",
        "Lists payees paid by check with no bills.",
        "Compares vendors with the employee master by bank account, phone, tax ID and full name, and says which fields could not be compared.",
      ],
      where: ["Workbench → Runs & Findings (payables)"],
      doesNot: [
        "It cannot tell a slip from a scheme, or say who created a vendor record: QuickBooks' exports do not carry it.",
        "It cannot ask the supplier for a refund, or confirm that a consulting firm exists.",
      ],
    },
  },

  {
    n: 4,
    slug: "fraud-splits-and-check-tampering",
    title: "Split purchases and check irregularities",
    phase: "Fraud",
    question: "How are approval limits and payment records got around, and where does it show?",
    minutes: 30,
    objectives: [
      "Recognize a purchase split to stay under an approval limit",
      "Read a bank reconciliation for checks that behave oddly",
      "Say what the records cannot show about approval",
    ],
    sections: [
      {
        heading: "Getting under the limit",
        blocks: [
          { p: "Where bills above a limit need a second approval, a purchase can be cut into several bills, each just under it, entered days apart. Each bill passes; the purchase never meets an approver." },
          { p: "The trace: several bills to one vendor, each under the limit, close together in time, for the same kind of goods." },
        ],
      },
      {
        heading: "Checks that behave oddly",
        blocks: [
          { list: [
            "A check that never clears: was it mailed, and is the payee real?",
            "A check that clears for a different amount than was recorded: altered, or recorded wrongly.",
            "A check written on a weekend, at year end.",
          ] },
          { p: "Each has innocent explanations. Each is traced to the bank and asked about." },
        ],
      },
      {
        heading: "Missing check numbers",
        blocks: [
          { p: "Checks are numbered in order. A number missing between the first and last check of the year was voided, issued outside the records, or used for a payment someone wanted hidden. Each bank account, and payroll, is its own run of numbers; a number used for two different payees is a second check under one number." },
          { p: "A gap is accounted for with the voided check itself, or with the bank's paid-check images for the months around it." },
        ],
      },
      {
        heading: "Who signed the check",
        blocks: [
          { p: "A check should be prepared by one person and signed by another. The bank's paid-check images show the signature, so the auditor can read who signed each check selected and compare it with who prepared it. A check signed by the person who prepared it passed through no second pair of eyes." },
        ],
      },
      {
        heading: "Kestrel",
        blocks: [
          { kestrel: "Kestrel's approval limit is in the partner's policies. One vendor billed display fixtures three times in one week, each just under it. On the June reconciliation, one check written on a Saturday never cleared, and another cleared at a different amount from the one recorded, leaving part of a bill open." },
          { kestrel: "Kestrel's checks run in one unbroken sequence for the year, except for three numbers the client cannot produce. And the team read the signer off the bank's images for the year's larger checks and for the payees under inquiry: the managing member signs, except on the consulting firm's checks, which the bookkeeper both prepared and signed." },
          { watch: "Kestrel's QuickBooks exports record no approver, so the records cannot show whether any bill was approved at all. The split is visible; the approval that was dodged is not. The signer comes from separate evidence, the bank's images, and only for the checks inspected." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "Misappropriation: fraudulent disbursements"],
      ["AU-C 330", "Tests of details over cash disbursements"],
    ],
    check: [
      { q: "Three bills from one vendor within a week, each just under the approval limit. What is the question?",
        options: ["Were they paid on time?", "Were they one purchase, split to avoid approval?", "Are they duplicates?", "Is the vendor a related party?"],
        answer: 1,
        why: "The pattern is the split. Ask whether it was one order, and who decided to bill it in pieces." },
      { q: "A check on the year-end reconciliation has not cleared two weeks later. What do you do?",
        options: ["Nothing; checks take time", "Trace it to the cutoff statement, ask whether it was mailed, and confirm the payee exists", "Void it", "Add it to income"],
        answer: 1,
        why: "An uncleared check may never have been sent, or may pay someone who does not exist." },
      { q: "Three check numbers in the middle of the year are missing from the books, and the client cannot produce them. What do you do?",
        options: ["Nothing; checks get lost", "Ask for the voided checks, and if they cannot be produced, inspect the bank's paid-check images for those months", "Assume they were voided", "Report fraud"],
        answer: 1,
        why: "A gap is a lead until the checks are accounted for. The bank shows whether any of them cleared." },
      { q: "A check was prepared and signed by the same person. Why does it matter?",
        options: ["It does not, if the amount is right", "No second person saw the payment before it left; it is the opening for a false one", "Signatures are a formality", "Only the bank can judge a signature"],
        answer: 1,
        why: "The second signer is the control. Without one, the payment's support is the only thing left to check." },
    ],
    byHand: {
      files: ["quickbooks/Transaction_List_by_Vendor.xlsx", "quickbooks/Checking_Reconciliation.xlsx", "bank/first_prairie_xxxx2208_2026-07-01_to_2026-07-15.csv", "quickbooks/Unpaid_Bills.xlsx", "quickbooks/Journal.xlsx", "quickbooks/Journal_2026-07.xlsx", "auditor/check_signatures.csv"],
      intro: "Find the split, trace the reconciliation's checks, run the check numbers, and read the signers.",
      steps: [
        "Filter bills under the approval limit; sort by vendor and date; find several to one vendor within a week.",
        "Trace each uncleared check on the June reconciliation to the July cutoff statement.",
        "For the check that cleared at another amount, find its bill in Unpaid Bills.",
        "From both Journals, list every **Check** and **Bill Payment (Check)** number, sort them, and find the numbers missing between the first and the last.",
        "In the check signatures file, find the checks whose **Signed By** is the same person as **Prepared By**.",
      ],
      asks: [
        { label: "Approval limit", row: "split bills: Hyalite total", module: PAYABLES, key: "payables.split_bills.approval_limit" },
        { label: "Vendor with split bills", row: "split bills: Hyalite total", module: PAYABLES, key: "payables.split_bills.vendor" },
        { label: "Their total", row: "split bills: Hyalite total", module: PAYABLES },
        { label: "Check that never cleared", row: "check 4421 did not clear by 07-15", module: CASH, key: "part1.cash.bank_reconciliation.outstanding_check_not_cleared_by_07-15.0.check" },
        { label: "Amount left open by the short payment", row: "short payment on check 4425 (left open)", module: PAYABLES },
        { label: "First of the missing check numbers", row: "check sequence: the one gap, checks 4422-4424", module: PAYABLES, key: "part3.forensic.check_number_sequence.disbursements.gaps.0.first_missing" },
        { label: "How many numbers are missing", row: "check sequence: the one gap, checks 4422-4424", module: PAYABLES, key: "part3.forensic.check_number_sequence.disbursements.gaps.0.count" },
        { label: "Who signed the checks they prepared", row: "self-signed checks: Dana Merritt's DM Consulting checks", module: PAYABLES, key: "payables.self_approved_payments.self_signed_by" },
        { label: "Those checks' total", row: "self-signed checks: Dana Merritt's DM Consulting checks", module: PAYABLES, key: "payables.self_approved_payments.self_signed_total" },
      ],
    },
    inNoesi: {
      procedures: ["ap.split_payment_review", "cash.bank_reconciliation", "je.journal_entry_testing",
                   "forensic.check_number_sequence", "forensic.self_approved_payments"],
      steps: [
        DEMO_START,
        "**Runs & Findings:** open `ap.split_payment_review` for the split, and `cash.bank_reconciliation` for the two checks.",
        "In `je.journal_entry_testing`, find the check that never cleared among the weekend entries.",
        "Open `forensic.check_number_sequence`: read the run (first and last check) and the one gap. Then `forensic.self_approved_payments` for the self-signed checks.",
        "The demo loads the reconciliation and cutoff statement prepared by hand from their exports (roadmap C), and the signatures as the team recorded them from the bank's images.",
      ],
    },
    keyModule: PAYABLES,
    keyLines: [
      [PAYABLES, "split bills: Hyalite total"],
      [CASH, "check 4421 did not clear by 07-15"],
      [CASH, "check 4425 cleared at another amount"],
      [PAYABLES, "short payment on check 4425 (left open)"],
      [JOURNAL, "weekend or holiday: entries"],
      [PAYABLES, "check sequence: first to last check"],
      [PAYABLES, "check sequence: the one gap, checks 4422-4424"],
      [PAYABLES, "check sequence: reused numbers"],
      [PAYABLES, "checks inspected for their signer"],
      [PAYABLES, "self-signed checks: Dana Merritt's DM Consulting checks"],
      [PAYABLES, "checks with no signer"],
    ],
    noesi: {
      coverage: "partial",
      summary: "Noesi finds splits under the approved threshold and window, traces every reconciling check to the bank, finds missing and reused check numbers, and compares each inspected check's signer with its preparer.",
      does: [
        "Groups bills by vendor within the split window and flags clusters under the threshold.",
        "Traces each uncleared item to the cutoff statement, and flags a check that did not clear or cleared at another amount.",
        "Runs every check number in the Journal, by bank account, and lists gaps and numbers used twice.",
        "Reads a signature or approval log and lists checks signed by their preparer, and checks with no signer.",
      ],
      where: ["Workbench → Runs & Findings (payables, cash)"],
      doesNot: [
        "It cannot test approval of bills: QuickBooks' exports carry no approver.",
        "It cannot read a check image itself; the signer is what the team recorded, and only for the checks inspected.",
        "It cannot say why a check number is missing; the voided check or the bank's images can.",
      ],
    },
  },

  {
    n: 5,
    slug: "fraud-payroll-schemes",
    title: "Payroll schemes",
    phase: "Fraud",
    question: "How does money leave through payroll, and what do the records show?",
    minutes: 30,
    objectives: [
      "Describe ghost employees, pay after termination and diverted deposits",
      "Test a payroll register against the employee master",
      "Say what a payroll finding does and does not prove",
    ],
    sections: [
      {
        heading: "Payroll schemes",
        blocks: [
          { terms: [
            ["Ghost employee", "Someone on the payroll who does not work there, whose pay goes to the fraudster."],
            ["Pay after termination", "A departed employee left on the payroll, with the pay redirected."],
            ["Diverted deposits", "Two employees' pay, or a ghost's, deposited into one account."],
            ["Falsified amounts", "Pay or net pay larger than it should be."],
          ] },
        ],
      },
      {
        heading: "Where it shows",
        blocks: [
          { p: "Every one of these is visible by testing the register against the employee master: IDs not on it, dates after termination, bank accounts shared, arithmetic that does not hold." },
          { watch: "The register ties to the ledger even when a ghost is paid: the ghost's pay is in both. The tie is not the test." },
        ],
      },
      {
        heading: "Kestrel",
        blocks: [
          { kestrel: "Kestrel's register holds an ID that is not on the master, paid every payday; a terminated employee paid after the final-pay period; two employees paid into one account; and a net-pay error in the employee's favour." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "Misappropriation through payroll"],
      ["AU-C 330", "Substantive procedures over payroll"],
    ],
    check: [
      { q: "An ID is paid every payday all year and is not on the employee master. What is the first question?",
        options: ["Was withholding correct?", "Who is it, who set it up, and where does the pay go?", "Is the register complete?", "Did it tie to the ledger?"],
        answer: 1,
        why: "A payee the master does not know is the ghost pattern. The deposit account and who created the ID are the leads." },
      { q: "Why does the register tying to the ledger not rule out a ghost?",
        options: ["It does rule it out", "The ghost's pay is recorded in both, so they still agree", "Ghosts are paid in cash", "The ledger excludes payroll"],
        answer: 1,
        why: "Tying proves the totals agree, not that each payee is real." },
    ],
    byHand: {
      files: ["client/payroll_register_FY2026.csv", "client/employee_master.csv"],
      intro: "Test every payroll payment against the master (see also Module 8 and Excel for audit).",
      steps: [
        "Look up every register ID in the master; list those not found and count their payments and net pay.",
        "For the terminated employee, list payments after the final-pay period.",
        "Count employees per direct-deposit account.",
      ],
      asks: [
        { label: "Ghost employee ID", row: "ghost employee E16: payments", module: PAYROLL, key: "part2.payroll.ghost_employee.id" },
        { label: "Net paid to it", row: "ghost employee E16: payments", module: PAYROLL, key: "part2.payroll.ghost_employee.net_paid" },
        { label: "Paid after termination (ID)", row: "paid after termination: E12", module: PAYROLL, key: "part2.payroll.paid_after_termination.id" },
        { label: "Payment date beyond the final-pay period", row: "paid after termination: E12", module: PAYROLL, key: "part2.payroll.paid_after_termination.payments_beyond_grace" },
        { label: "Sharing one account (IDs)", row: "shared bank account: E03, E09", module: PAYROLL, key: "part2.payroll.shared_bank_account" },
      ],
    },
    inNoesi: {
      procedures: ["payroll.register_tests"],
      steps: [
        DEMO_START,
        "**Runs & Findings:** open `payroll.register_tests`; the register and master load as the client gave them.",
      ],
    },
    keyModule: PAYROLL,
    keyLines: [
      [PAYROLL, "ghost employee E16: payments"],
      [PAYROLL, "paid after termination: E12"],
      [PAYROLL, "shared bank account: E03, E09"],
      [PAYROLL, "net pay error: E05"],
    ],
    noesi: {
      coverage: "full",
      summary: "Noesi tests every payroll payment against the master: not on it, after termination, shared account, net pay, vendor address.",
      does: ["Runs every payment through the payroll tests and lists each exception with its evidence."],
      where: ["Workbench → Runs & Findings (payroll)"],
      doesNot: [
        "It cannot confirm a person exists or see whose account a deposit reaches.",
        "It cannot tell a late final bonus from a scheme.",
      ],
    },
  },

  {
    n: 6,
    slug: "fraud-following-one-person",
    title: "Following one person",
    phase: "Fraud",
    question: "When do separate exceptions become a case, and what do you do next?",
    minutes: 35,
    objectives: [
      "Connect findings from different tests through one person",
      "Recognize an undisclosed related party",
      "Know when the auditor's work ends and an investigation begins",
    ],
    sections: [
      {
        heading: "From findings to a pattern",
        blocks: [
          { p: "Each test reports its own exceptions. A fraud usually shows up across several: a vendor with no bills, an address that matches an employee, a person who can both create the vendor and pay it. Line the findings up by **person** and a pattern can appear that no single test shows." },
        ],
      },
      {
        heading: "Undisclosed related parties",
        blocks: [
          { p: "Management gives the auditor a list of related parties. A related party left off the list, deliberately or not, is found only through other evidence: shared addresses, shared bank accounts, people in two roles." },
        ],
      },
      {
        heading: "What comes next",
        blocks: [
          { p: "When findings point at one person, the auditor does not confront them. The auditor tells the right level of management, or those charged with governance when management is involved, and considers the effect on the audit. Investigating is a separate job, often for forensic specialists, with evidence handled so it can be used." },
          { kestrel: "At Kestrel, one person posts the entries in QuickBooks and reconciles the bank. Their home address is the address of a vendor paid by checks with no bills, that vendor is not on management's related-party list, and the bank's images show they signed that vendor's checks themselves." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "Communicating fraud to management and those charged with governance"],
      ["AU-C 550", "Related parties, including parties management did not disclose"],
      ["AU-C 265", "Communicating internal control matters"],
    ],
    check: [
      { q: "Findings from three tests all lead to the bookkeeper. What does the auditor do?",
        options: ["Confront the bookkeeper", "Communicate to the appropriate level above the bookkeeper and consider the effect on the audit", "Ignore it; each finding is small", "Call the police"],
        answer: 1,
        why: "The auditor reports to those who can act, and plans the audit's response. Investigation is a separate engagement." },
      { q: "Why can matching management's related-party list not find this vendor?",
        options: ["The software is limited", "It is not on the list; matching only finds names management gave", "The vendor is too small", "Vendors are never related parties"],
        answer: 1,
        why: "An omission is found by other evidence, here a shared address." },
    ],
    byHand: {
      files: ["quickbooks/Vendor_Contact_List.xlsx", "client/employee_master.csv", "client/related_parties.csv", "quickbooks/Transaction_List_by_Vendor.xlsx"],
      intro: "Line up the findings by person.",
      steps: [
        "Take the vendor at an employee's address. Who is the employee, and what is their job?",
        "Total that vendor's payments and look for its bills.",
        "Look for the vendor on management's related-party list.",
        "In the check signatures file, find who signed that vendor's checks.",
      ],
      asks: [
        { label: "The employee", row: "bookkeeper's address is a vendor's (E07, DM Consulting)", module: PAYROLL, key: "part2.payroll.bookkeeper_address_is_a_vendor_address.employee" },
        { label: "The vendor at their address", row: "bookkeeper's address is a vendor's (E07, DM Consulting)", module: PAYROLL, key: "part2.payroll.bookkeeper_address_is_a_vendor_address.vendor" },
        { label: "Paid to it without bills", row: "checks without bills: DM Consulting", module: PAYABLES },
        { label: "Party missing from management's list", row: "DM Consulting not findable by matching management's list", module: ESTIMATES, key: "part3.related_parties.undisclosed_not_findable_by_matching.party" },
        { label: "Who signed that vendor's checks", row: "self-signed checks: Dana Merritt's DM Consulting checks", module: PAYABLES, key: "payables.self_approved_payments.self_signed_by" },
      ],
    },
    inNoesi: {
      procedures: ["payroll.register_tests", "ap.payments_without_bills", "related_parties.matching",
                   "forensic.self_approved_payments"],
      steps: [
        DEMO_START,
        "**Runs & Findings:** read the four procedures above and line their findings up by name.",
        "Note what `related_parties.matching` does **not** report, and why.",
      ],
    },
    keyModule: PAYABLES,
    keyLines: [
      [PAYROLL, "bookkeeper's address is a vendor's (E07, DM Consulting)"],
      [PAYABLES, "checks without bills: DM Consulting"],
      [ESTIMATES, "DM Consulting not findable by matching management's list"],
      [PAYABLES, "segregation of duties not testable"],
      [PAYABLES, "self-signed checks: Dana Merritt's DM Consulting checks"],
    ],
    noesi: {
      coverage: "partial",
      summary: "Noesi reports each finding with its evidence; lining them up by person, and deciding what they mean, is the auditor's.",
      does: [
        "Finds the shared address, the checks without bills, and the checks signed by the person who prepared them.",
        "Matches management's related-party list, and says what matching cannot find.",
      ],
      where: ["Workbench → Runs & Findings"],
      doesNot: [
        "It does not assemble findings into a case against a person.",
        "It cannot decide whom to tell, or investigate.",
      ],
    },
  },

  {
    n: 7,
    slug: "fraud-following-the-money",
    title: "Following the money",
    phase: "Fraud",
    question: "Cash moved between accounts at year end, and money left and came back. How do you tell a scheme from a normal transfer?",
    minutes: 40,
    objectives: [
      "Explain kiting: cash counted in two accounts at once",
      "Test interbank transfers around year end, books against bank",
      "Recognize a round trip: money sent out and brought back as something else",
    ],
    sections: [
      {
        heading: "Kiting",
        blocks: [
          { p: "A transfer between two of the company's own accounts takes time to clear. If the receiving account records it before year end and the sending account records it after, the same cash sits in both balances on the balance sheet. Done deliberately, it hides a shortage or props up a ratio." },
          { p: "The test is a schedule of every transfer around year end, with four dates: disbursed and received, per books and per bank. A transfer received in the books in one year and disbursed in the books in the next is counted twice." },
        ],
      },
      {
        heading: "Kestrel",
        blocks: [
          { kestrel: "Kestrel moves money from checking to payroll checking before each payroll. The team scheduled three transfers from June and July. One was received in the books on the last day of the year and disbursed in the books the day after. Kestrel also had a current-ratio covenant to meet." },
          { watch: "A lender's covenant is pressure, in the fraud triangle's sense. It does not make the transfer fraud; it is a reason to ask why it was booked that way." },
        ],
      },
      {
        heading: "Round trips",
        blocks: [
          { p: "In a round trip the company's own money leaves, passes through one or more outsiders, and comes back dressed as something else: a customer's payment, a loan, a sale. On the company's books each leg looks ordinary. It shows only when the money is followed beyond the books: whose account a check was deposited to, and who paid the money back." },
          { p: "The auditor's tool is a flow-of-funds schedule: every payment out above a size, plus each leg traced through endorsements, deposit records or the counterparty's statements. A cycle in it, out and back for about the same amount within days, is a lead." },
          { kestrel: "Kestrel paid a new vendor for display racks. The team traced the check: it was deposited by Summit Loop Racing, a customer owned by a related party, which a few days later paid the same amount back to Kestrel. QuickBooks records it as a customer's payment." },
          { watch: "A round trip is not fraud by itself; businesses settle debts through third parties. The questions are whether the racks were ever received, and why the customer's \"payment\" was Kestrel's own money." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "Fraud risk factors: incentives and pressures, including covenants"],
      ["AU-C 500", "Audit evidence: the bank's records as independent evidence"],
    ],
    check: [
      { q: "A transfer is received in the books on June 30 and disbursed in the books on July 1. What is wrong at June 30?",
        options: ["Nothing", "The cash is counted in both accounts: cash is overstated", "Cash is understated", "Only the timing of interest"],
        answer: 1,
        why: "The receiving account has it; the sending account still has it too." },
      { q: "Why does a covenant matter here?",
        options: ["It does not", "It gives a reason to present cash or ratios favourably at year end", "It proves fraud", "It changes the transfer's date"],
        answer: 1,
        why: "It is an incentive to consider, not evidence of intent." },
      { q: "A vendor's check is deposited by one of your client's customers, who then pays the same amount back to your client. What is it?",
        options: ["A normal collection", "A round trip: a lead to follow, starting with whether the vendor delivered anything", "Kiting", "A duplicate payment"],
        answer: 1,
        why: "The client's own money came back as a customer's payment. The bill behind the first leg is the first thing to test." },
    ],
    byHand: {
      files: ["auditor/interbank_transfers.csv", "quickbooks/Checking_Reconciliation.xlsx", "quickbooks/Journal_2026-07.xlsx", "auditor/flow_of_funds.csv"],
      intro: "Work the team's transfer schedule, then its flow-of-funds schedule.",
      steps: [
        "For each transfer, compare the books' received date with the books' disbursed date, around June 30.",
        "Find the transfer received in one year and disbursed in the next.",
        "Find its July check in the July journal.",
        "In the flow-of-funds schedule, follow each row whose **From** is not Kestrel: where did the money go next, and does any of it come back to Kestrel?",
      ],
      asks: [
        { label: "The transfer counted twice", row: "transfer T-0701", module: CASH, key: "part1.cash.interbank_transfers.T-0701" },
        { label: "Its July check", row: "subsequent-event lead: check 4429 25000.00", module: COMPLETION },
        { label: "Transfers clearing after the adjustment", row: "adjusted 10900 Transfers Clearing", module: COMPLETION },
        { label: "Amount that went out and came back", row: "round trip: Kestrel to Gallatin to Summit Loop and back", module: PAYABLES, key: "payables.round_trip.amount" },
        { label: "The vendor it went out to", row: "round trip: Kestrel to Gallatin to Summit Loop and back", module: PAYABLES, key: "payables.round_trip.legs.0.to" },
        { label: "Who paid it back", row: "round trip: Kestrel to Gallatin to Summit Loop and back", module: PAYABLES, key: "payables.round_trip.legs.2.from" },
      ],
    },
    inNoesi: {
      procedures: ["cash.interbank_transfers", "completion.subsequent_events", "fs.adjusted_trial_balance",
                   "forensic.closed_value_flow"],
      steps: [
        DEMO_START,
        "**Runs & Findings:** open `cash.interbank_transfers` and read the transfer flagged, and `fs.adjusted_trial_balance` for the adjustment.",
        "Open `forensic.closed_value_flow` and read the round trip's path, leg by leg.",
        "The demo loads the transfer schedule and reconciliation prepared by hand (roadmap C), and the flow-of-funds schedule as the team prepared it.",
      ],
    },
    keyModule: CASH,
    keyLines: [
      [CASH, "transfer T-0615"],
      [CASH, "transfer T-0630"],
      [CASH, "transfer T-0701"],
      [COMPLETION, "subsequent-event lead: check 4429 25000.00"],
      [COMPLETION, "adjusted 10900 Transfers Clearing"],
      [PAYABLES, "round trip: Kestrel to Gallatin to Summit Loop and back"],
      [PAYABLES, "round trips found (leads)"],
    ],
    noesi: {
      coverage: "partial",
      summary: "Noesi tests every transfer's four dates and flags cash counted twice, and finds money that goes out and comes back in the flow-of-funds schedule.",
      does: [
        "Compares books and bank dates for each transfer around year end.",
        "Lists post-year-end payments above the threshold as leads.",
        "Finds cycles in the flow-of-funds schedule that return to the client for about the same amount within a month.",
      ],
      where: ["Workbench → Runs & Findings (cash, completion, payables)"],
      doesNot: [
        "It cannot say whether a transfer was booked that way on purpose.",
        "It cannot trace money beyond the books itself: every leg must be in the schedule the team prepared.",
      ],
    },
  },

  {
    n: 8,
    slug: "fraud-data-analysis",
    title: "Data analysis for fraud detection",
    phase: "Fraud",
    question: "How do you test every transaction, and how do you read what the tests say, and don't say?",
    minutes: 30,
    objectives: [
      "Explain why fraud tests run on the whole population",
      "Foot and count a population before testing it",
      "Read a test's silence correctly",
    ],
    sections: [
      {
        heading: "Whole populations",
        blocks: [
          { p: "Sampling finds errors that are spread through a population. Fraud is rare and deliberate: a sample of a few dozen entries will usually miss the one that matters. Data analysis tests every transaction, then the auditor looks hard at the few it flags." },
        ],
      },
      {
        heading: "Before any test",
        blocks: [
          { p: "Count and foot the population and tie it to the ledger. A test on an incomplete population is silent about what is missing. Then run the tests, and read each result for what it covers." },
          { watch: "\"No exceptions\" means none of the kind the test looks for, in the data it was given. It does not mean nothing is wrong." },
        ],
      },
      {
        heading: "Kestrel's journal as a population",
        blocks: [
          { kestrel: "Kestrel's Journal for the year is counted in transactions and lines, every account's balance rolls forward from last year to this, and the tests run over all of it. Several accounts were used only once all year, and many entries have no description, most of them automatic entries from invoices and bills." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "Journal entry testing and the use of data"],
      ["AU-C 500", "The completeness and accuracy of information produced by the entity"],
      ["AU-C 530", "Audit sampling, and why fraud tests do not rely on it"],
    ],
    check: [
      { q: "A test reports no exceptions. What may you conclude?",
        options: ["Nothing is wrong", "No exceptions of that kind in the data it was given", "The population is complete", "Controls work"],
        answer: 1,
        why: "A test speaks only about its own question and its own data." },
      { q: "Most entries with no description are automatic entries from invoices. Why does that matter?",
        options: ["It does not", "The risk is in manual entries; automatic ones carry their document", "Automatic entries are always fraud", "Descriptions are optional"],
        answer: 1,
        why: "A manual entry with no description has nothing behind it on its face. Separate them before you judge." },
    ],
    byHand: {
      files: ["quickbooks/Journal.xlsx", "quickbooks/Trial_Balance_2025-06-30.xlsx", "quickbooks/Trial_Balance_2026-06-30.xlsx"],
      intro: "Treat the Journal as a population.",
      steps: [
        "Count the transactions and the lines.",
        "Count the lines per account; list accounts used no more often than the seldom-used policy allows.",
        "Find the entry dated inside the year but created after it.",
        "Count lines with no description, then separate the manual journal entries from the rest.",
      ],
      asks: [
        { label: "Transactions in the Journal", row: "transactions in the Journal", module: JOURNAL },
        { label: "Seldom-used accounts", row: "seldom-used accounts", module: JOURNAL },
        { label: "Entry posted after period end", row: "posted after period end: entries", module: JOURNAL },
        { label: "Entries with no description", row: "no description: count", module: JOURNAL },
      ],
    },
    inNoesi: {
      procedures: ["je.population_completeness", "je.journal_entry_testing"],
      steps: [
        DEMO_START,
        "**Runs & Findings:** open `je.population_completeness` (does every account roll forward?) before `je.journal_entry_testing`.",
        JOURNAL_NOTE,
      ],
    },
    keyModule: JOURNAL,
    noesi: {
      coverage: "partial",
      summary: "Noesi counts and rolls forward the population before testing it, then runs every test over every line.",
      does: [
        "Checks that every account rolls forward from last year to this, so the population is complete.",
        "Runs the journal tests on every line and separates manual entries without a description.",
      ],
      where: ["Workbench → Runs & Findings (journal entries)"],
      doesNot: [
        "It cannot see entries made outside the Journal it is given.",
        "A silent test is silent only about its own question.",
      ],
    },
  },

  {
    n: 9,
    slug: "fraud-prevention",
    title: "Preventing it next time",
    phase: "Fraud",
    question: "Which controls would have stopped each scheme, and who has to be told?",
    minutes: 25,
    objectives: [
      "Match each Kestrel scheme to the control that would have prevented or found it",
      "Say which deficiencies the auditor communicates, and to whom",
    ],
    sections: [
      {
        heading: "Scheme by scheme",
        blocks: [
          { table: { head: ["Scheme at Kestrel", "A control that would stop or find it"], rows: [
            ["Twin vendor, duplicate invoice", "Vendor master changes approved by someone who does not pay bills; the system rejecting a repeated supplier invoice number"],
            ["Checks with no bills", "No payment without an approved bill; a second signer"],
            ["Split bills", "Approval by purchase, not by bill; review of bills just under the limit"],
            ["Ghost employee, pay after termination", "The employee master kept by someone who does not run payroll; payroll reviewed against it"],
            ["Owner's weekend entry", "Review of all manual entries by someone independent of those who post them"],
            ["Transfer counted twice", "Transfers recorded on both sides on the same date; a monthly transfer schedule reviewed"],
            ["Vendor named after an employee", "New vendors checked against the employee master before their first payment"],
            ["Checks signed by their preparer", "A signer who never prepares checks; the bookkeeper off the bank's signature card"],
            ["Missing check numbers", "Blank check stock kept locked, voids kept and logged, the sequence reviewed monthly"],
            ["Money sent out and back", "Related-party payments and receipts reviewed by someone outside the transaction; new vendors' existence and deliveries confirmed"],
          ] } },
        ],
      },
      {
        heading: "In a very small company",
        blocks: [
          { p: "Kestrel cannot hire a second bookkeeper. Where duties cannot be split, **review** does the work: the managing member reviews the vendor list, the bank reconciliation and the payroll register each month, looking at the items, not just the totals." },
        ],
      },
      {
        heading: "Telling the right people",
        blocks: [
          { p: "Significant deficiencies and material weaknesses in internal control are communicated in writing to management and those charged with governance. Fraud, or information indicating it, is communicated promptly to the appropriate level." },
        ],
      },
    ],
    standards: [
      ["AU-C 265", "Communicating internal control related matters identified in an audit"],
      ["AU-C 240", "Communications about fraud"],
    ],
    check: [
      { q: "In a company too small to split duties, what substitutes for segregation?",
        options: ["Nothing", "Review of the detail by someone independent, such as the owner", "More auditing", "Insurance"],
        answer: 1,
        why: "An independent person looking at the items each month removes much of the opportunity." },
      { q: "Which control would have stopped the duplicate invoice?",
        options: ["A bank reconciliation", "Controlled vendor-master changes and a rejected repeat of a supplier invoice number", "A physical count", "A payroll review"],
        answer: 1,
        why: "The twin record and the repeated invoice number are exactly what those controls block." },
    ],
    byHand: {
      files: ["this track's lessons", "the Coverage screen"],
      intro: "Write the controls memo.",
      steps: [
        "For each scheme found, name the control that would have prevented it and who would own it.",
        "Note the tests the exports could not support, and the evidence the client would need to keep so they can be tested next year.",
      ],
      asks: [
        { label: "Three-way match from these exports", row: "three-way match not testable", module: PAYABLES },
        { label: "Segregation of duties from these exports", row: "segregation of duties not testable", module: PAYABLES },
        { label: "Why the PO overrun is not found", row: "PO overrun: Summit Tire PO 1021", module: PAYABLES, key: "payables.po_overrun.po" },
      ],
    },
    inNoesi: {
      procedures: ["Coverage", "SAD & Completion"],
      steps: [
        DEMO_START,
        "**Coverage:** list the procedures blocked or partial, and what each needs.",
        "**SAD & Completion:** see which findings reached the summary of audit differences.",
      ],
    },
    keyModule: PAYABLES,
    keyLines: [
      [PAYABLES, "three-way match not testable"],
      [PAYABLES, "segregation of duties not testable"],
      [PAYABLES, "PO overrun: Summit Tire PO 1021"],
      [PAYABLES, "A/P subledger ties to the ledger"],
    ],
    noesi: {
      coverage: "partial",
      summary: "Noesi records what it could and could not test; the controls memo, and the conversation with management, are the auditor's.",
      does: ["Shows, procedure by procedure, what the client's records support and what they do not."],
      where: ["Workbench → Coverage", "Workbench → SAD & Completion"],
      doesNot: [
        "It does not design controls or write the communication.",
        "It does not evaluate whether a deficiency is significant; that is judgment.",
      ],
    },
  },
];
