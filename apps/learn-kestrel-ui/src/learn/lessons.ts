// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** The Kestrel Learn modules (docs/LEARN-KESTREL-PLAN.md), in engagement
 *  order. Eight are written; five wait for the Workbench to load QuickBooks'
 *  own exports (ROADMAP section C) and show on the course map as coming.
 *
 *  No figure is typed here. Each "ask" names a line of the finish-line check
 *  (`row`) and, where that line is yes/no, a path into the answer key (`key`);
 *  the compare step reads both from kestrel-key.json. */

import { Coming, Lesson } from "./types";

const DEMO_START = "Start the Workbench with the Kestrel demo: `python -m workbench_api --demo`, open the address it prints, paste the session token, and open **Kestrel Valley Cycle Supply (demo)**.";

export const LESSONS: Lesson[] = [
  {
    n: 1,
    slug: "engagement-setup",
    title: "Engagement setup",
    phase: "Planning",
    question: "Before any testing: what period, how big a mistake matters, and who does what?",
    minutes: 20,
    objectives: [
      "Say why the period, materiality and team are fixed before any procedure runs",
      "Read a QuickBooks trial balance export and find the period it covers",
      "Name the three chairs of an engagement and why they are kept apart",
    ],
    sections: [
      {
        heading: "The audit starts with a frame, not a test",
        blocks: [
          { p: "Every procedure in the audit leans on a few decisions made first. **The period** says which transactions belong to this year. **Materiality** says how big a misstatement must be before it would change a reader's decision. **The team** says who prepares the work, who reviews it, and who signs. **The audit areas** say which parts of the statements are in scope." },
          { p: "Set these late, or change them quietly, and every result built on them moves. So the partner sets them at the start, writes down why, and changes them only on the record." },
        ],
      },
      {
        heading: "Materiality and the policies built on it",
        blocks: [
          { p: "Materiality is a judgment on a benchmark: for a profitable private company, usually a percentage of pretax income. It is not a test result; it is the ruler the results are measured with." },
          { terms: [
            ["Materiality", "The size of misstatement, alone or added up, that could change the decisions of someone relying on the statements (AU-C 320)."],
            ["Policies", "The thresholds the procedures use: tolerable misstatement, how large a movement must be to explain, how many days a deposit may take to clear. The partner approves them, so the tool does not choose them."],
            ["Period", "The first and last day of the year audited. Tests such as \"paid after the year end\" or \"account used only once this year\" need both ends."],
          ] },
        ],
      },
      {
        heading: "Three chairs",
        blocks: [
          { p: "Quality management expects the work to be **prepared** by one person, **reviewed** by another, and **signed off** by the partner. The separation is the point: a reviewer who also prepared the work is checking their own answer." },
          { watch: "On a practice laptop one person sits in every chair. That is role-play, and the record should say so rather than pretend a second person looked." },
        ],
      },
      {
        heading: "Kestrel, as the engagement begins",
        blocks: [
          { kestrel: "Kestrel Valley Cycle Supply, LLC sells bicycle parts to independent bike shops and keeps its books in **QuickBooks Online**. The bookkeeper, Dana Merritt, prepares the reports; the managing member is Jo Kestrel. It is a pass-through LLC, so there is no income tax provision. The client hands over QuickBooks exports and a few schedules; the audit team adds its own working files." },
          { p: "The trial balances come as two exports, one run at this year end and one at the prior year end. The period is read from them, and materiality is set on the pretax income they show." },
        ],
      },
    ],
    standards: [
      ["AU-C 210", "Terms of the engagement and the preconditions for an audit"],
      ["AU-C 220 / SQMS 1", "Quality management for an audit; the engagement partner's responsibilities, including direction, supervision and review"],
      ["AU-C 300", "Planning an audit: the overall strategy set before the work"],
      ["AU-C 320", "Materiality in planning and performing an audit"],
    ],
    check: [
      { q: "Why is materiality set before the procedures run?",
        options: ["The software needs a number to start", "It is the ruler the results are judged by; setting it after seeing them invites fitting it to them", "Lenders require it in the engagement letter", "It is only needed at the end"],
        answer: 1,
        why: "Materiality set after the results are known can be moved to make them look immaterial. Setting it first, on the record, keeps it honest." },
      { q: "A reviewer approves a file mapping they prepared themselves. What is wrong?",
        options: ["Nothing, if the mapping is right", "The review is not independent of the preparation, so it adds no second look", "Only the partner may map files", "Mappings do not need review"],
        answer: 1,
        why: "The value of review is a second person. The same person in both chairs is one look, recorded twice." },
    ],
    byHand: {
      files: ["quickbooks/Trial_Balance_2026-06-30.xlsx", "quickbooks/Trial_Balance_2025-06-30.xlsx", "the Policies table in the case README.md"],
      intro: "Set up the engagement as the partner would, from the client's exports and the partner's approved policies.",
      steps: [
        "Open this year's trial balance. Read the **As of** line under the title: that is the period end.",
        "Open the prior year's trial balance. The period starts the day after its **As of** date.",
        "Read the partner's approved materiality in the Policies table of the case README.",
        "Write down the three chairs an engagement needs, and who at the firm may sit in each.",
      ],
      asks: [
        { label: "Period start", row: "period start" },
        { label: "Period end", row: "period end" },
        { label: "Materiality", row: "materiality" },
        { label: "The three chairs", row: "team: partner, preparer, reviewer" },
      ],
    },
    inNoesi: {
      procedures: ["Team", "Scope & Policies", "Sources & Mappings"],
      steps: [
        DEMO_START,
        "**Team:** see the partner, preparer and reviewer, each a different login.",
        "**Scope & Policies:** read materiality, the period start and end, the audit areas switched on, and every approved policy.",
        "**Sources & Mappings:** check that every file loaded and none was refused. Note which files say they were **prepared by hand from the QuickBooks export**: the trial balances are among them, because the Workbench does not yet read that report raw.",
      ],
    },
    keyModule: "Engagement setup",
    noesi: {
      coverage: "partial",
      summary: "Noesi records the frame (period, materiality, team, areas, policies) and holds every procedure to it. Choosing them stays with the partner.",
      does: [
        "Keeps materiality, the period and the policies on the engagement record, changed only by the partner and journaled with who changed what.",
        "Keeps the three chairs apart: a reviewer cannot approve their own mapping.",
        "Shows each file's provenance, including files prepared by hand from an export.",
      ],
      where: ["Workbench → Team", "Workbench → Scope & Policies", "Workbench → Sources & Mappings"],
      doesNot: [
        "It does not decide acceptance, independence or materiality; it records the partner's decisions.",
        "It has no engagement-letter or independence checklist.",
        "On one laptop the chairs are role-play; the tool cannot know that two logins are two people.",
      ],
    },
  },

  {
    n: 5,
    slug: "payables",
    title: "Payables",
    phase: "Fieldwork",
    question: "Is every bill real, recorded once, and paid to someone who should be paid?",
    minutes: 40,
    objectives: [
      "Foot a QuickBooks payables export before testing it",
      "Find twin vendors, duplicate bills and bills split under an approval limit",
      "Find payments with no bill behind them",
      "Say which payables tests the exports cannot support, and why",
    ],
    sections: [
      {
        heading: "What can go wrong in purchase to pay",
        blocks: [
          { p: "Money leaves a business through payables. The risks run both ways: liabilities left out (completeness) and payments that should never have happened (occurrence). The second is where most payables fraud lives." },
          { list: [
            "**Twin vendors:** the same supplier set up twice, which lets one invoice be paid twice.",
            "**Duplicate bills:** the same supplier invoice entered twice, often a few days apart.",
            "**Split bills:** one purchase cut into bills just under the approval limit.",
            "**Payments without bills:** checks written straight to a payee, with no invoice behind them.",
            "**Short or over payments:** a check that does not match the bill it pays.",
          ] },
        ],
      },
      {
        heading: "Foot first, then test",
        blocks: [
          { p: "Before any test, count and foot the population you were given. If the count or total disagrees with the ledger, the test runs on the wrong population and every result is suspect." },
          { watch: "An export can quietly drop rows. Bills with no number are a common case: a tool that needs a bill number may set them aside. Count them yourself so you know what was set aside." },
        ],
      },
      {
        heading: "Tests the records cannot support",
        blocks: [
          { p: "Some classic payables tests need facts the client's system does not keep. The **three-way match** compares the order, the receipt of goods and the bill; if no receipt is recorded, there is nothing to match. **Segregation of duties** asks whether the same person entered and approved a payment; if no approver is recorded, it cannot be tested from the data." },
          { p: "Saying \"not testable from these records\" is a finding in itself. It tells the partner that assurance must come from somewhere else: inquiry, inspection, or a control walkthrough." },
        ],
      },
      {
        heading: "Kestrel's payables",
        blocks: [
          { kestrel: "Kestrel's QuickBooks keeps vendors, purchase orders, bills and bill payments. It records **no receipts** and **no approver**. A bill's purchase order number is typed in its memo, not linked. The client's approval limit is set in the partner's policies, and the split-bill test looks for bills to one vendor within a week of each other." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "The auditor's responsibilities relating to fraud"],
      ["AU-C 330", "Performing audit procedures in response to assessed risks"],
      ["AU-C 500", "Audit evidence, including the completeness and accuracy of information the entity produces"],
    ],
    check: [
      { q: "Two vendors share an address and phone number, one named with \", Inc.\" and one without. Why does it matter?",
        options: ["It does not; names vary", "The same supplier set up twice lets one invoice be paid twice, once under each record", "Vendors with the same address are always fraud", "QuickBooks forbids it"],
        answer: 1,
        why: "A twin is not proof of fraud, but it is the setup a duplicate payment needs. Look for the same invoice under both records." },
      { q: "The system records no receipts of goods. What do you conclude about the three-way match?",
        options: ["It passes", "It fails", "It is not testable from these records; assurance must come from other procedures", "Use the purchase order twice"],
        answer: 2,
        why: "A test with a missing leg is neither passed nor failed. Say so, and plan another way to get the evidence." },
    ],
    byHand: {
      files: ["quickbooks/Vendor_Contact_List.xlsx", "quickbooks/Transaction_List_by_Vendor.xlsx", "quickbooks/Bill_Payment_List.xlsx", "quickbooks/Unpaid_Bills.xlsx", "quickbooks/Checking_Reconciliation.xlsx"],
      intro: "Work the payables exports in a spreadsheet, as they came from QuickBooks.",
      steps: [
        "**Vendor Contact List:** count the vendors. Sort by billing address and phone; note any two records that look like one supplier.",
        "**Transaction List by Vendor:** filter **Transaction type** to Bill. Count the bills, including any with a blank **Num**.",
        "Sort the bills by **Num** and look for the same supplier invoice number under two vendor records. Note its amount.",
        "Look for one vendor's bills that each sit just under the approval limit and fall within a week of each other. Add them up.",
        "Filter **Transaction type** to Check. Find a payee paid by checks with no bill for that vendor anywhere in the list. Total those checks.",
        "Compare each bill's memo (**PO …**) with the purchase order of that number. Note any bill larger than its order.",
        "**Bill Payment List:** count and foot the payments.",
        "**Unpaid Bills:** find the bill left partly open. Compare it with the check that paid it on the checking reconciliation.",
      ],
      asks: [
        { label: "Vendors on the list", row: "vendors" },
        { label: "Bills, including any with no number", row: "bills (loaded + set aside)" },
        { label: "Bill payments total", row: "bill payments total" },
        { label: "Invoice number entered twice", row: "duplicate bill MC-25009", key: "payables.duplicate_bill.invoice" },
        { label: "Amount of the duplicate", row: "duplicate's misstatement" },
        { label: "Split bills: their total", row: "split bills: Hyalite total" },
        { label: "Checks with no bill: their total", row: "checks without bills: DM Consulting" },
        { label: "Amount left open on the short-paid bill", row: "short payment on check 4425 (left open)" },
        { label: "Purchase order a bill exceeded", row: "PO overrun: Summit Tire PO 1021", key: "payables.po_overrun.po" },
      ],
    },
    inNoesi: {
      procedures: ["ap.vendor_relational_twins", "ap.duplicate_bills", "ap.split_payment_review", "ap.payments_without_bills", "cash.bank_reconciliation", "ap.voucher_po_reference", "ap.three_way_receipt_match", "ap.segregation_of_duties"],
      steps: [
        DEMO_START,
        "**Sources & Mappings:** the vendor list, the Transaction List by Vendor and the Bill Payment List load **raw**, through QuickBooks recipes. Read the rows loaded and set aside for each, and the payments' control total.",
        "**Coverage:** see which payables procedures are executable, partial or blocked, and why.",
        "**Runs & Findings:** read the findings of each procedure above. Each finding is a lead to follow up, not a conclusion.",
      ],
    },
    keyModule: "Payables",
    noesi: {
      coverage: "partial",
      summary: "Noesi runs the whole-population payables tests on QuickBooks' own exports, and says which tests the exports cannot support.",
      does: [
        "Loads the vendor list, bills and bill payments raw from QuickBooks exports, footing and counting each, with rows set aside shown, not dropped.",
        "Finds twin vendors, duplicate bills, split bills and checks without bills across every row.",
        "Marks the three-way match **blocked** and segregation of duties **partial**, with the reason, instead of reporting them as passed.",
      ],
      where: ["Workbench → Sources & Mappings", "Workbench → Coverage", "Workbench → Runs & Findings"],
      doesNot: [
        "It cannot link a bill to its purchase order: QuickBooks keeps the PO number only in the memo, so the PO overrun is not found (waits for roadmap C).",
        "It cannot tie the payables subledger to the ledger without a General Ledger export (roadmap C).",
        "It cannot inspect an invoice, ask the supplier, or judge whether a payment was authorized. A finding is a lead; the follow-up is yours.",
      ],
    },
  },

  {
    n: 8,
    slug: "payroll",
    title: "Payroll",
    phase: "Fieldwork",
    question: "Were the people paid real employees, paid the right amount, while they worked here?",
    minutes: 35,
    objectives: [
      "Tie a payroll register to the wages in the ledger",
      "Test every payment against the employee master",
      "Recognize the patterns of a ghost employee and of payroll diversion",
    ],
    sections: [
      {
        heading: "Why payroll is tested whole",
        blocks: [
          { p: "Payroll is many small, similar payments, so a sample of a few checks tells you little. The useful tests run over every payment in the year, against the employee master file: the list of who works here, since when, and where they are paid." },
        ],
      },
      {
        heading: "Five questions of every payment",
        blocks: [
          { terms: [
            ["Is the payee on the master?", "A payment to an ID the master does not have is the classic **ghost employee**."],
            ["Were they still employed?", "Pay after the termination date, beyond the final-pay period in the policies, needs an explanation."],
            ["Is the bank account theirs alone?", "Two employees paid into one account can mean one person collecting two salaries."],
            ["Does the arithmetic hold?", "Gross pay less withholding should equal net pay. An error that favors the employee is worth asking about."],
            ["Does their address belong to a vendor?", "An employee living at a vendor's address may be billing the company as well as being paid by it."],
          ] },
        ],
      },
      {
        heading: "Tie the register to the ledger",
        blocks: [
          { p: "Before the payment tests, foot the register's gross pay and compare it with the wages account in the trial balance. If they differ, the register is not the whole population." },
          { watch: "A register that ties to the ledger can still hold a ghost. Tying proves the totals agree; it does not prove the people are real." },
        ],
      },
      {
        heading: "Kestrel's payroll",
        blocks: [
          { kestrel: "Kestrel pays by direct deposit twice a month. The client gives a payroll register for the year and an employee master with status, hire and termination dates, bank account and home address. The managing member is on the payroll, and so is the bookkeeper, who also keeps the vendor list." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "Fraud risk, including misappropriation through payroll"],
      ["AU-C 330", "Substantive procedures in response to assessed risks"],
      ["AU-C 500", "Audit evidence; information produced by the entity"],
    ],
    check: [
      { q: "The payroll register ties exactly to the wages account. What does that prove?",
        options: ["Every employee is real", "The totals agree; it does not prove the people or the payments are proper", "No further testing is needed", "The register is complete and accurate in every respect"],
        answer: 1,
        why: "A ghost's pay is in both the register and the ledger, so they still tie. The payment tests against the master find what the tie cannot." },
      { q: "Two employees' net pay goes to the same bank account. What is the first step?",
        options: ["Report fraud", "Ask why, and look at who controls the account and who set up the second employee", "Ignore it; couples share accounts", "Stop the payroll"],
        answer: 1,
        why: "There may be an innocent reason. It is a lead to follow, with the person who can explain it." },
    ],
    byHand: {
      files: ["client/payroll_register_FY2026.csv", "client/employee_master.csv", "quickbooks/Trial_Balance_2026-06-30.xlsx", "quickbooks/Vendor_Contact_List.xlsx"],
      intro: "Test every payroll payment in a spreadsheet.",
      steps: [
        "Foot **Gross Pay** in the register. Find the wages account (60100) in the trial balance and compare.",
        "Look up every register **Employee ID** in the master (a lookup column works). List any ID the master does not have, and count its payments.",
        "For the terminated employee, list payments dated more than the final-pay days (in the policies) after the **Termination Date**.",
        "Count employees per **Direct Deposit Account** in the master; note any account used by two.",
        "Add a column **Gross − Taxes − Net**; find the row that is not zero.",
        "Compare each employee's **Home Address** with the vendors' **Billing address**.",
      ],
      asks: [
        { label: "Register gross pay", row: "register gross" },
        { label: "Wages per the ledger", row: "wages per ledger" },
        { label: "Employee ID not on the master", row: "ghost employee E16: payments", key: "part2.payroll.ghost_employee.id" },
        { label: "Payments to that ID", row: "ghost employee E16: payments" },
        { label: "Paid after termination (ID)", row: "paid after termination: E12", key: "part2.payroll.paid_after_termination.id" },
        { label: "Sharing one bank account (IDs)", row: "shared bank account: E03, E09", key: "part2.payroll.shared_bank_account" },
        { label: "Net pay error (ID)", row: "net pay error: E05", key: "part2.payroll.net_pay_error.id" },
        { label: "Vendor at an employee's address", row: "bookkeeper's address is a vendor's (E07, DM Consulting)", key: "part2.payroll.bookkeeper_address_is_a_vendor_address.vendor" },
      ],
    },
    inNoesi: {
      procedures: ["payroll.register_to_ledger", "payroll.register_tests"],
      steps: [
        DEMO_START,
        "**Sources & Mappings:** the register and the employee master load as the client gave them.",
        "**Runs & Findings:** open `payroll.register_to_ledger` for the tie, then `payroll.register_tests` for each finding: not on the master, paid after termination, shared bank account, net pay differs, address is a vendor's.",
      ],
    },
    keyModule: "Payroll",
    noesi: {
      coverage: "full",
      summary: "Noesi ties the register to the ledger and tests every payment against the master and the vendor list.",
      does: [
        "Ties register gross pay to the wages accounts named in the policies.",
        "Runs every payment through the five tests and lists each exception with its evidence.",
        "Compares employee addresses with vendor addresses, which finds a vendor that management's related-party list leaves out.",
      ],
      where: ["Workbench → Runs & Findings (payroll)"],
      doesNot: [
        "It cannot confirm that a person exists: seeing them, or their tax forms, is inspection and inquiry.",
        "It cannot tell a legitimate reason (a final bonus, a shared family account) from a scheme; each finding needs follow-up.",
        "It does not test pay rates against contracts or hours worked.",
      ],
    },
  },

  {
    n: 9,
    slug: "property-and-equipment",
    title: "Property and equipment",
    phase: "Fieldwork",
    question: "Do the assets exist, and is their cost and depreciation right?",
    minutes: 30,
    objectives: [
      "Roll the fixed-asset register forward from beginning to ending cost",
      "Recompute straight-line depreciation under a full-month convention",
      "Vouch additions to their invoices",
    ],
    sections: [
      {
        heading: "The roll-forward",
        blocks: [
          { p: "Property and equipment is audited as a movement: beginning cost, plus additions, less disposals, equals ending cost. The beginning ties to last year's audited figures; the ending ties to this year's ledger. What moved in between is what you test." },
          { steps: [
            "Foot the register and tie ending cost and accumulated depreciation to the ledger.",
            "Split the year's movement into additions and disposals.",
            "Vouch additions to invoices: was it bought, for this amount, and is it a capital item?",
            "Recompute depreciation for each asset.",
          ] },
        ],
      },
      {
        heading: "Recomputing depreciation",
        blocks: [
          { p: "Straight-line depreciation is (cost − salvage) ÷ useful life, per year. A **full-month convention** counts the month an asset is placed in service as a full month. An asset fully depreciated before the year starts gets none; an asset added during the year gets only the months it was in service." },
          { watch: "A register's depreciation column is the client's calculation, not evidence. Recompute it; do not add it up and call it tested." },
        ],
      },
      {
        heading: "Kestrel's register",
        blocks: [
          { kestrel: "Kestrel's register lists each asset with its date placed in service, cost, life, salvage, the year's depreciation and the accumulated total. The engagement team vouched the year's one addition to its invoice in a working file. The policies name the cost, accumulated depreciation and depreciation expense accounts, and the full-month convention." },
        ],
      },
    ],
    standards: [
      ["AU-C 500", "Audit evidence: recalculation and inspection"],
      ["AU-C 330", "Substantive procedures for significant account balances"],
      ["AU-C 540", "Auditing accounting estimates: useful lives and salvage values"],
    ],
    check: [
      { q: "An asset was placed in service before this year and is not fully depreciated. Under straight line, this year's depreciation should be…",
        options: ["whatever the register says", "(cost − salvage) ÷ useful life", "cost ÷ useful life, ignoring salvage", "zero"],
        answer: 1,
        why: "A full year's straight-line charge is the depreciable base over the life. The register's figure is what you check against it." },
      { q: "Why tie beginning cost to last year's figures?",
        options: ["To test this year's additions", "Because the roll-forward only proves the movement if the starting point is right", "It is optional", "To find disposals"],
        answer: 1,
        why: "An error in the opening balance flows straight into the ending balance, however well the movement is tested." },
    ],
    byHand: {
      files: ["client/fixed_asset_register.csv", "auditor/additions_vouching.csv", "quickbooks/Trial_Balance_2026-06-30.xlsx"],
      intro: "Roll the register forward and recompute each asset's depreciation.",
      steps: [
        "Sum the cost of assets placed in service before the period start: beginning cost. Sum those placed in service during the year: additions.",
        "Ending cost is beginning plus additions less disposals. Sum accumulated depreciation.",
        "Sum the register's **Current Year Depreciation**.",
        "For each asset, recompute the year's straight-line depreciation with a full-month convention. Note any asset where recorded and recomputed differ, and by how much (recorded − recomputed).",
        "Check the addition against the vouching file.",
      ],
      asks: [
        { label: "Beginning cost", row: "beginning cost" },
        { label: "Additions", row: "additions" },
        { label: "Ending cost", row: "ending cost" },
        { label: "Accumulated depreciation", row: "accumulated" },
        { label: "Depreciation per the register", row: "depreciation per register" },
        { label: "Asset whose depreciation differs", row: "FA-06 depreciation differs by", key: "part2.ppe.depreciation_differs.asset" },
        { label: "By how much (recorded − recomputed)", row: "FA-06 depreciation differs by" },
      ],
    },
    inNoesi: {
      procedures: ["ppe.rollforward", "ppe.depreciation_recompute", "ppe.additions_vouching"],
      steps: [
        DEMO_START,
        "**Scope & Policies:** see the PP&E accounts and the depreciation convention.",
        "**Runs & Findings:** open `ppe.rollforward` for the movement and its tie to the ledger, `ppe.depreciation_recompute` for each asset's recomputation, and `ppe.additions_vouching` for coverage of additions.",
      ],
    },
    keyModule: "Property and equipment",
    noesi: {
      coverage: "partial",
      summary: "Noesi rolls the register forward, ties it to the ledger, recomputes every asset's depreciation, and measures how much of additions was vouched.",
      does: [
        "Rolls cost and accumulated depreciation forward and ties them to the ledger accounts in the policies.",
        "Recomputes straight-line depreciation for every asset under the policy's convention.",
        "Reports the share of additions vouched and any vouching exception the team recorded.",
      ],
      where: ["Workbench → Scope & Policies", "Workbench → Runs & Findings (PP&E)"],
      doesNot: [
        "It cannot see an asset: existence is physical inspection.",
        "It does not read invoices; it reads the team's vouching record of them.",
        "It does not judge useful lives, salvage values or impairment, and it recomputes straight line only.",
      ],
    },
  },

  {
    n: 10,
    slug: "debt-equity-accruals",
    title: "Debt, equity, accruals",
    phase: "Fieldwork",
    question: "Do the schedules behind the balance sheet add up, tie to the ledger, and hold up on recomputation?",
    minutes: 40,
    objectives: [
      "Roll a loan forward and test its interest for reasonableness",
      "Recompute a debt covenant from the ledger",
      "Tie equity and accrual schedules to the ledger",
      "Recompute a prepaid and an accrual by days",
    ],
    sections: [
      {
        heading: "Schedules are the client's claims",
        blocks: [
          { p: "Debt, equity and accruals usually reach the auditor as schedules the client prepared. Each is tested three ways: does it **foot**, does it **tie** to the ledger, and does it hold up when you **recompute** it from its own terms?" },
        ],
      },
      {
        heading: "Debt and covenants",
        blocks: [
          { p: "Roll the loan forward: beginning, plus advances, less repayments, equals ending. Test interest by expectation: the rate times the average balance should be close to the interest recorded, within the tolerance in the policies." },
          { p: "Then recompute the lender's **covenants** from the ledger. A breached covenant can make the whole loan callable, which bears on its classification and on going concern." },
          { watch: "Recompute the covenant from the ledger accounts the loan agreement names, not from a ratio the client reports." },
        ],
      },
      {
        heading: "Equity and accruals",
        blocks: [
          { p: "An equity roll-forward can foot perfectly and still not tie: a contribution on the schedule that never reached the ledger is a difference between what the owners say and what the books say." },
          { p: "Prepaids and accruals are recomputed from their contracts. A prepaid is the unexpired share of what was paid; an accrual is the earned-but-unbilled share of what is owed. Prorate by days of service. An accrual that did not move all year is its own question: is it still owed?" },
        ],
      },
      {
        heading: "Kestrel's schedules",
        blocks: [
          { kestrel: "Kestrel has one bank loan with a current-ratio covenant, an equity roll-forward for members' capital and retained earnings, and a schedule of prepaids and accruals: an insurance premium, software and dues, accrued payroll and the audit fee. The team wrote the covenant down, with the ledger accounts it counts, in a working file." },
        ],
      },
    ],
    standards: [
      ["AU-C 500", "Audit evidence: recalculation and reperformance"],
      ["AU-C 505", "External confirmations (the lender's confirmation of the loan)"],
      ["AU-C 520", "Analytical procedures: the interest expectation"],
      ["AU-C 570", "Going concern: covenant breaches as an indicator"],
    ],
    check: [
      { q: "The equity schedule foots but its ending does not agree with the ledger. What is it?",
        options: ["Fine, because it foots", "A difference between the schedule and the books that must be explained before either is relied on", "A rounding error", "Only a presentation matter"],
        answer: 1,
        why: "Footing tests the schedule's arithmetic; tying tests whether it describes the books. Both are needed." },
      { q: "An accrual shows the same balance at the start and end of the year, with no activity. What do you do?",
        options: ["Nothing; it ties", "Ask whether it is still owed and why nothing moved", "Reverse it", "Double it"],
        answer: 1,
        why: "A balance that never moves may no longer be a liability. The ledger cannot answer that; management can, and the evidence behind their answer can." },
    ],
    byHand: {
      files: ["client/debt_schedule.csv", "auditor/covenants.csv", "client/equity_rollforward.csv", "client/accruals_prepaids_schedule.csv", "quickbooks/Trial_Balance_2026-06-30.xlsx"],
      intro: "Foot, tie and recompute each schedule.",
      steps: [
        "Roll the loan forward. Compute expected interest as the rate times the average of beginning and ending balances; express the difference from recorded interest as a percentage.",
        "Recompute the covenant from the trial balance: add the numerator accounts and the denominator accounts listed in the covenants file, divide, and compare with the threshold.",
        "Foot each equity line and compare its ending with the trial balance.",
        "Recompute the insurance prepaid: the contract amount times the days of cover left after the period end over the days in the term. Recompute the audit-fee accrual: the fee times the days of service through the period end over the days in the term. Compare each with the schedule.",
        "Find the accrual with no movement all year.",
      ],
      asks: [
        { label: "Loan ending balance", row: "loan ending" },
        { label: "Interest: difference from expectation (%)", row: "interest within tolerance (4.8% < 10%)", key: "part2.debt_equity.loan.interest_difference_pct" },
        { label: "Current ratio for the covenant", row: "current-ratio covenant breached", key: "part2.debt_equity.covenant_current_ratio.ratio" },
        { label: "Covenant breached? (yes/no)", row: "current-ratio covenant breached", key: "part2.debt_equity.covenant_current_ratio.breached" },
        { label: "Insurance prepaid: recorded − recomputed", row: "insurance premium recompute differs by" },
        { label: "Audit fee accrual: recorded − recomputed", row: "audit fee recompute differs by" },
        { label: "Accrual unchanged all year", row: "stale accrual: Accrued payroll unchanged all year" },
      ],
    },
    inNoesi: {
      procedures: ["debt.rollforward_and_interest", "debt.covenants", "equity.rollforward", "accruals.rollforward", "accruals.recompute"],
      steps: [
        DEMO_START,
        "**Scope & Policies:** see the debt and interest accounts and the interest tolerance.",
        "**Runs & Findings:** open each procedure above. Read the covenant finding, the equity line that does not tie, the two recompute differences, and the accrual that never moved.",
      ],
    },
    keyModule: "Debt, equity, accruals",
    noesi: {
      coverage: "partial",
      summary: "Noesi foots, ties and recomputes the client's schedules and the team's covenant, and lists what it could not recompute.",
      does: [
        "Rolls the loan forward and tests interest against the rate and average balance, within the policy's tolerance.",
        "Recomputes each covenant from the ledger accounts the team listed.",
        "Ties equity and accruals to the ledger, recomputes prepaids and accruals that carry contract terms, and names the ones it could not recompute.",
        "Flags an accrual with no movement all year.",
      ],
      where: ["Workbench → Runs & Findings (debt, equity, accruals)"],
      doesNot: [
        "It does not confirm the loan with the lender or read the loan agreement; the covenant terms are the team's reading of it.",
        "It cannot recompute an item with no contract terms on the schedule (software and dues, accrued payroll).",
        "Whether a breached covenant makes the loan current, or casts doubt on going concern, is the partner's judgment.",
      ],
    },
  },

  {
    n: 11,
    slug: "estimates-and-related-parties",
    title: "Estimates and related parties",
    phase: "Fieldwork",
    question: "Does management's judgment lean one way, and who is on both sides of a deal?",
    minutes: 30,
    objectives: [
      "Perform a retrospective review of last year's estimates",
      "Recognize a pattern that indicates possible management bias",
      "Match management's related-party list against the entity's records",
      "Explain why matching the list cannot find a party the list leaves out",
    ],
    sections: [
      {
        heading: "Looking back at last year's estimates",
        blocks: [
          { p: "An estimate is a judgment about an uncertain amount: an allowance, a reserve, an accrual. The auditor compares last year's estimates with how they turned out. One miss says little; **every miss in the same direction** says management's judgment may lean." },
          { p: "The comparison is not a test of last year's audit. It asks what this year's estimates should be read against." },
        ],
      },
      {
        heading: "Related parties",
        blocks: [
          { p: "A related party is someone who can influence the entity or be influenced by it: owners, their families, companies they own. Transactions with them may not be at arm's length, so they must be identified and disclosed." },
          { p: "The usual first step is to take **management's list** and look for its names in customers, vendors, employees and the ledger." },
          { watch: "Matching the list finds only parties management chose to list. A related party they left out is found some other way: shared addresses, bank accounts, or people who hold two roles." },
        ],
      },
      {
        heading: "Kestrel",
        blocks: [
          { kestrel: "Kestrel gives last year's estimates with their outcomes, and a list of three related parties: the managing member, a holding company the managing member owns, and a racing team owned by the managing member's brother. The hindsight threshold in the policies sets how far an outcome may miss before it is noted." },
        ],
      },
    ],
    standards: [
      ["AU-C 540", "Auditing accounting estimates, including the retrospective review and indicators of management bias"],
      ["AU-C 550", "Related parties"],
      ["AU-C 240", "Fraud: management bias and override"],
    ],
    check: [
      { q: "Every one of last year's estimates came in below the outcome. What does it indicate?",
        options: ["Last year's audit failed", "A possible management bias to consider in this year's estimates", "Nothing, if each miss is small", "Fraud"],
        answer: 1,
        why: "A consistent direction is an indicator of possible bias, not proof. It shapes how skeptically this year's estimates are read." },
      { q: "Why can matching management's list not find every related party?",
        options: ["The software is slow", "It only looks for the names management gave; an undisclosed party is not on the list", "Related parties are always listed", "Matching is done at year end only"],
        answer: 1,
        why: "An omission is found by other evidence, such as an employee's home address shared with a vendor." },
    ],
    byHand: {
      files: ["client/prior_year_estimates.csv", "client/related_parties.csv", "client/employee_master.csv", "quickbooks/AR_Aging_Summary.xlsx", "quickbooks/Vendor_Contact_List.xlsx"],
      intro: "Review last year's estimates, then look for the related parties in the records.",
      steps: [
        "For each estimate, compute (outcome − prior) ÷ prior. List those that missed by more than the hindsight threshold, and note the direction of every miss.",
        "Look for each listed party among the customers on the A/R aging, the vendors, and the employee master (names and addresses).",
        "Then look beyond the list: compare employee home addresses with vendor addresses.",
      ],
      asks: [
        { label: "Estimates that missed beyond the threshold", row: "estimates missed beyond 20%" },
        { label: "All missed the same way? (yes/no)", row: "bias indicator (all missed one way)", key: "part3.estimates.bias_indicator" },
        { label: "Listed party that is a customer", row: "related party: Summit Loop Racing is a customer", key: "part3.related_parties.listed.2" },
        { label: "Listed party on the payroll", row: "related party: Jo Kestrel on the payroll (E01)", key: "part3.related_parties.listed.0" },
        { label: "A party not on management's list", row: "DM Consulting not findable by matching management's list", key: "part3.related_parties.undisclosed_not_findable_by_matching.party" },
      ],
    },
    inNoesi: {
      procedures: ["estimates.retrospective_review", "related_parties.matching", "payroll.register_tests"],
      steps: [
        DEMO_START,
        "**Runs & Findings:** open `estimates.retrospective_review` for each miss and the one-direction indicator, and `related_parties.matching` for where each listed party appears.",
        "Then open `payroll.register_tests` and find the address finding: that is where the unlisted party shows up, not in the related-party matching.",
      ],
    },
    keyModule: "Estimates and related parties",
    noesi: {
      coverage: "partial",
      summary: "Noesi performs the retrospective review and matches management's list against customers, vendors and employees. It cannot find a party the list omits by matching the list.",
      does: [
        "Computes each estimate's miss against the policy threshold and flags when every miss runs one way.",
        "Looks for every listed party among customers, vendors and employees, by name and address.",
        "Elsewhere (payroll), finds an employee living at a vendor's address, a lead to an undisclosed party.",
      ],
      where: ["Workbench → Runs & Findings (estimates, related parties, payroll)"],
      doesNot: [
        "It cannot find a related party management left off the list by matching the list; that needs other evidence and inquiry.",
        "It does not judge whether this year's estimates are reasonable or whether a transaction was at arm's length.",
        "It does not read board minutes, ownership records or contracts.",
      ],
    },
  },

  {
    n: 12,
    slug: "completion",
    title: "Completion",
    phase: "Completion",
    question: "Before the report: what happened after year end, what did management confirm, and what is left uncorrected?",
    minutes: 45,
    objectives: [
      "Search the period after year end for events that bear on the statements",
      "Check the representation letter for completeness and date",
      "Total uncorrected misstatements by statement line and compare with materiality",
      "Recompute going-concern indicators",
    ],
    sections: [
      {
        heading: "Subsequent events",
        blocks: [
          { p: "Between the year end and the report date, things happen. Some reveal conditions that **existed at year end** (a lawsuit settled in July over a dispute from March): those are adjusted. Others arise after (a fire in July): those may be disclosed. The auditor reads the books and bank after year end for leads above a threshold." },
          { watch: "An unrecorded liability often shows up as a payment in July for something received in June. A search limited to large items can miss it." },
        ],
      },
      {
        heading: "The representation letter",
        blocks: [
          { p: "Management confirms in writing what the audit relied on: its responsibilities, that it gave all information, that it disclosed related parties, and more. The letter is dated **as of the report date**, because the auditor's work runs to that date." },
          { p: "A missing representation is not a paperwork gap. If management will not confirm something the audit needs, the auditor cannot rely on the evidence it underpins." },
        ],
      },
      {
        heading: "Uncorrected misstatements and going concern",
        blocks: [
          { p: "All misstatements found and not corrected are summarized by statement line: the **summary of audit differences**. Each line is compared with materiality, and so is the total's effect on income." },
          { p: "Going-concern indicators are recomputed from the adjusted figures: working capital, income, equity, and ratios the lender watches." },
        ],
      },
      {
        heading: "Kestrel at completion",
        blocks: [
          { kestrel: "The report date is in July. The client gives the July journal and the bank's cutoff statement; the team has the signed representation letter, its schedule of uncorrected misstatements, and its adjusting entries. The policies set the subsequent-events threshold, the report date, who must sign the letter, and the current-ratio floor for going concern." },
        ],
      },
    ],
    standards: [
      ["AU-C 560", "Subsequent events and subsequently discovered facts"],
      ["AU-C 580", "Written representations"],
      ["AU-C 450", "Evaluation of misstatements identified during the audit"],
      ["AU-C 570", "Going concern"],
    ],
    check: [
      { q: "In July the company settles a dispute that began in March. How is it treated?",
        options: ["Ignored; it happened after year end", "As a condition that existed at year end: the statements are adjusted", "Only disclosed", "Deferred to next year"],
        answer: 1,
        why: "The dispute existed at year end; the settlement is evidence of its amount. That is an adjusting event." },
      { q: "The representation letter is signed but dated four days before the report. What follows?",
        options: ["Nothing", "It must be dated as of the report date; ask for it to be re-dated", "The report is backdated to match", "The auditor signs it instead"],
        answer: 1,
        why: "Representations must cover the whole period of the auditor's work, up to the report date." },
    ],
    byHand: {
      files: ["quickbooks/Journal_2026-07.xlsx", "bank/first_prairie_xxxx2208_2026-07-01_to_2026-07-15.csv", "auditor/representation_letter.csv", "auditor/uncorrected_misstatements_final.csv", "auditor/adjusting_entries.csv"],
      intro: "Do the completion work from the files after year end and the team's schedules.",
      steps: [
        "Read the July journal and the cutoff statement for items above the subsequent-events threshold. For each, decide: a year-end condition (adjust) or routine?",
        "Look for a July payment for something received in June that is below the threshold.",
        "Compare the representation letter with the representations the audit needs; note any missing, and compare its date with the report date.",
        "Total the uncorrected misstatements by statement line and compare each line with materiality.",
        "From the adjusted trial balance, recompute the current ratio for going concern.",
      ],
      asks: [
        { label: "July item that adjusts the year end", row: "subsequent-event lead: JE 1071 settlement 30000.00" },
        { label: "Representation missing", row: "representation missing" },
        { label: "Date on the letter", row: "letter not dated the report date", key: "part3.representation_letter.dated" },
        { label: "Report date", row: "letter not dated the report date", key: "part3.representation_letter.report_date" },
        { label: "Uncorrected on Current Assets", row: "uncorrected misstatements: Current Assets" },
        { label: "Going concern: current ratio", row: "going concern: current ratio" },
        { label: "Unrecorded liability: July check amount", row: "unrecorded liability: check 4433" },
      ],
    },
    inNoesi: {
      procedures: ["completion.subsequent_events", "completion.representation_letter", "completion.uncorrected_misstatements", "completion.going_concern_indicators", "fs.adjusted_trial_balance"],
      steps: [
        DEMO_START,
        "**Runs & Findings:** open each procedure above. Read the subsequent-event leads, the missing representation and the date finding, the totals by line, and the going-concern indicators.",
        "**SAD & Completion:** see the summary of audit differences, with the line that reaches materiality.",
        "Note in **Sources & Mappings** that the trial balance, the July journal and the adjusting entries were prepared by hand from their exports; the Workbench does not yet read those reports raw (roadmap C).",
      ],
    },
    keyModule: "Completion",
    noesi: {
      coverage: "partial",
      summary: "Noesi gathers the completion evidence into findings and the summary of audit differences. The conclusions on each stay with the partner.",
      does: [
        "Lists every post-year-end item above the threshold as a lead.",
        "Checks the representation letter against the required list, the signer and the report date.",
        "Totals uncorrected misstatements by line and marks any line at materiality; the summary of audit differences carries the schedule.",
        "Recomputes going-concern indicators from the adjusted trial balance.",
      ],
      where: ["Workbench → Runs & Findings (completion)", "Workbench → SAD & Completion"],
      doesNot: [
        "It cannot search for unrecorded liabilities without payments linked to bills and the team's inspection results, so the July check below the threshold is not found (roadmap C).",
        "It does not decide whether an event adjusts or is disclosed, or whether substantial doubt exists; it presents the leads and indicators.",
        "It does not obtain the letter or talk to management.",
      ],
    },
  },

  {
    n: 13,
    slug: "the-opinion",
    title: "The opinion",
    phase: "Completion",
    question: "Given everything found, what can the auditor say, and what must the partner decide first?",
    minutes: 30,
    objectives: [
      "Tell a misstatement from a scope limitation, and material from pervasive",
      "Explain why a missing representation can outweigh a known misstatement",
      "List the decisions a partner records before the opinion",
    ],
    sections: [
      {
        heading: "Four opinions",
        blocks: [
          { table: { head: ["What the auditor found", "Material, not pervasive", "Material and pervasive"], rows: [
            ["The statements are misstated", "Qualified opinion", "Adverse opinion"],
            ["The auditor could not obtain enough evidence", "Qualified opinion", "Disclaimer of opinion"],
          ] } },
          { p: "With neither, the opinion is **unmodified**. The choice turns on two questions: is the problem a misstatement or a lack of evidence, and is it confined to some items or does it run through the statements as a whole?" },
        ],
      },
      {
        heading: "When the evidence itself is in doubt",
        blocks: [
          { p: "Written representations underpin evidence throughout the audit. If management will not give one the auditor asked for, the auditor considers what it does to the rest: can management's other statements be relied on at all? When that doubt runs through the statements, the auditor may be unable to form an opinion." },
          { watch: "A disclaimer is not a stronger adverse opinion. It says the auditor cannot say, and why." },
        ],
      },
      {
        heading: "Decisions before the report",
        blocks: [
          { p: "Some conclusions are the partner's alone and are recorded before any opinion: the going-concern conclusion when indicators are present, what to do about a representation letter that is incomplete or wrongly dated, and whether uncorrected misstatements are material." },
          { kestrel: "At Kestrel the completion work leaves three things on the partner's desk: a missing representation, uncorrected misstatements on one statement line at materiality, and going-concern indicators including the breached covenant." },
        ],
      },
    ],
    standards: [
      ["AU-C 700", "Forming an opinion and reporting on financial statements"],
      ["AU-C 705", "Modifications to the opinion: qualified, adverse, disclaimer"],
      ["AU-C 580", "Written representations, and the effect of one not provided"],
      ["AU-C 570", "Going concern: the auditor's conclusion and reporting"],
    ],
    check: [
      { q: "Misstatements above materiality are confined to one line, and nothing else is wrong. The usual opinion is…",
        options: ["Unmodified", "Qualified", "Disclaimer", "Adverse, always"],
        answer: 1,
        why: "Material but not pervasive misstatement gives a qualified opinion. Adverse needs pervasiveness." },
      { q: "Why record the partner's going-concern conclusion before the opinion?",
        options: ["It is optional", "The opinion and its wording depend on it; it is a judgment the tool cannot make", "The lender asks for it", "To date the report"],
        answer: 1,
        why: "Whether substantial doubt exists, and how it is reported, is the partner's judgment, on the record before the report." },
    ],
    byHand: {
      files: ["your module 12 results", "auditor/representation_letter.csv", "auditor/uncorrected_misstatements_final.csv"],
      intro: "Use your completion results to propose an opinion, as the senior would for the partner.",
      steps: [
        "Classify each open matter: misstatement or lack of evidence; material; pervasive?",
        "Decide which matter governs the opinion and why.",
        "List the decisions the partner must record before signing.",
      ],
      asks: [
        { label: "Proposed opinion", row: "proposed opinion" },
        { label: "What governs it", row: "basis: related-parties representation not provided", key: "part3.draft_opinion.why" },
        { label: "Partner decision: going concern", row: "decision: going-concern conclusion (incl. covenant breach)" },
        { label: "Partner decision: the letter", row: "decision: re-date the representation letter" },
      ],
    },
    inNoesi: {
      procedures: ["Draft Opinion"],
      steps: [
        DEMO_START,
        "**Draft Opinion:** read the proposed opinion, its basis, and the decisions the partner must record.",
        "Go back to **SAD & Completion** and **Runs & Findings** for the findings each basis rests on.",
      ],
    },
    keyModule: "The opinion",
    noesi: {
      coverage: "partial",
      summary: "Noesi proposes a draft opinion from the recorded findings and lists the partner's decisions. It never issues an opinion.",
      does: [
        "Proposes an opinion from the completion findings, with the basis for each modification.",
        "Lists the decisions the partner must record first, with the finding behind each.",
      ],
      where: ["Workbench → Draft Opinion", "Workbench → SAD & Completion"],
      doesNot: [
        "It does not form the opinion or sign the report: the proposal is a draft for the partner.",
        "It does not judge pervasiveness beyond the rules it applies; the partner may reach a different view and records why.",
        "It does not write the report's wording, disclosures or the going-concern paragraph.",
      ],
    },
  },
];

const WAITS = "Waits for the Workbench to read QuickBooks' own exports of ";
export const COMING: Coming[] = [
  { n: 2, title: "Planning", phase: "Planning", waitsFor: WAITS + "the trial balances (roadmap C)." },
  { n: 3, title: "Journal entries", phase: "Fieldwork", waitsFor: WAITS + "the Journal (roadmap C)." },
  { n: 4, title: "Revenue and receivables", phase: "Fieldwork", waitsFor: WAITS + "the A/R aging (roadmap C)." },
  { n: 6, title: "Cash", phase: "Fieldwork", waitsFor: WAITS + "the bank reconciliation reports (roadmap C)." },
  { n: 7, title: "Inventory", phase: "Fieldwork", waitsFor: WAITS + "the inventory valuation (roadmap C)." },
];
