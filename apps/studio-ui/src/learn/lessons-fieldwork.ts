// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Lessons 5–9: fieldwork. Sources: docs/learn/CURRICULUM.md.
 *  Lessons 7 and 9 use illustrative figures — the case has no AR or
 *  inventory data — and say so. */

import { Lesson } from "./types";

export const FIELDWORK: Lesson[] = [
  {
    n: 5,
    slug: "evidence-and-testing",
    title: "Evidence, sampling and tests of transactions",
    phase: "Fieldwork",
    question: "What counts as evidence, and how much is enough?",
    minutes: 35,
    objectives: [
      "Judge evidence by relevance and reliability",
      "Distinguish tests of controls from substantive tests of transactions",
      "Design an attribute sample and evaluate deviations",
      "Know what full-population testing changes — and what it does not",
    ],
    sections: [
      {
        heading: "Sufficient, appropriate evidence",
        blocks: [
          { p: "AU-C 500 (as revised by SAS 142) asks for evidence that is **sufficient** (enough) and **appropriate** (relevant and reliable). Reliability depends on the source and how you got it:" },
          { list: [
            "**independent, external** evidence beats internal evidence (a bank statement beats a client ledger);",
            "evidence you obtain **directly** beats evidence obtained indirectly;",
            "evidence from an entity with **effective controls** is more reliable than from one without;",
            "**documents** and **originals** beat oral statements and copies.",
          ] },
          { p: "Data the client extracts from its system is itself evidence you must evaluate: is the population **complete** and **accurate**? A test run on half a population proves nothing about the other half." },
        ],
      },
      {
        heading: "Two kinds of test",
        blocks: [
          { terms: [
            ["Test of controls", "Did the control operate throughout the period? (Was each payment above $10,000 actually second-signed?) The output is a deviation rate."],
            ["Substantive test of transactions", "Is the transaction itself right — did it occur, at the right amount, in the right period? (Vouch a payment to its invoice, PO and receipt.) The output is a dollar misstatement."],
          ] },
          { p: "Often one procedure does both at once — a **dual-purpose test**: while vouching a payment's documents you also check the approval signature." },
        ],
      },
      {
        heading: "Sampling",
        blocks: [
          { p: "When you cannot examine everything, you **sample** (AU-C 530). For a test of controls (**attribute sampling**):" },
          { steps: [
            "Define the **attribute** (evidence of approval) and what counts as a **deviation**.",
            "Define the **population** and confirm it is complete.",
            "Set the **tolerable deviation rate**, the **expected rate**, and your risk of over-reliance; these drive the sample size.",
            "Select items **randomly** or systematically so every item has a chance.",
            "Test, count deviations, compute the **upper deviation limit**, and compare it with the tolerable rate.",
          ] },
          { p: "If the upper limit exceeds the tolerable rate, the control cannot be relied on as planned: raise control risk and do more substantive work." },
        ],
      },
      {
        heading: "Full-population testing",
        blocks: [
          { p: "With the client's data in hand, software can compare **every** payment with its voucher, PO, receipt and bank clearing. That removes sampling risk — but three things stay true:" },
          { list: [
            "**Silence means 'within tolerance', not 'nothing there'.** Every automated comparison has a tolerance; know it before you call a result clean.",
            "**An exception is not a misstatement.** It is an exposure to investigate (Lesson 6).",
            "**Matching records do not authenticate documents.** A forged invoice that matches a forged PO passes a match.",
          ] },
          { harborline: "Run across Harborline's full populations, the eleven procedures report **52 findings**. The bank-clearing test is silent on one planted difference of 0.9% because its tolerance is 2% — a student reconciling by hand finds what the software correctly does not flag." },
        ],
      },
    ],
    standards: [
      ["AU-C 500 (SAS 142)", "Audit evidence: sufficiency, relevance, reliability; information produced by the entity"],
      ["AU-C 530", "Audit sampling"],
      ["AU-C 330", "Tests of controls and substantive procedures"],
    ],
    check: [
      { q: "Which evidence is most reliable?",
        options: ["The client's AP aging", "A bank statement obtained directly from the bank", "The controller's explanation", "A photocopy of an invoice"],
        answer: 1,
        why: "External evidence obtained directly by the auditor ranks highest." },
      { q: "An attribute sample's upper deviation limit is 9%; tolerable is 6%. Conclusion?",
        options: ["Rely on the control as planned", "The control is not effective as planned — raise control risk and extend substantive work", "Take a smaller sample", "Ignore deviations under $21,000"],
        answer: 1,
        why: "When the upper limit exceeds the tolerable rate, planned reliance is not supported." },
      { q: "A full-population test finds no exceptions. What can you say?",
        options: ["The population contains no errors", "No differences beyond the test's tolerance, within a population whose completeness you verified", "The controls are effective", "The documents are authentic"],
        answer: 1,
        why: "Silence is bounded by tolerance and by the completeness of the data." },
    ],
    task: {
      title: "Sample versus population",
      intro: "Use payments.csv and employees.csv.",
      steps: [
        "Draw a random sample of 25 payments and test the attribute 'created by and approved by different people'. Compute your deviation rate.",
        "Now test all 123 payments with a spreadsheet formula. How many deviations exist?",
        "Explain why the two answers differ and which one you would put in the workpaper.",
      ],
      deliver: "Both results and a paragraph comparing them.",
    },
    noesi: {
      coverage: "full",
      summary: "Noesi is built around evidence integrity and full-population testing. Each run is frozen, can be reperformed, and is reviewed by two other people.",
      does: [
        "**Upload → map → approve → normalize.** The original file is stored unaltered in a vault, identified by its SHA-256 fingerprint. The column mapping is proposed by one person and approved by another. Row counts must reconcile: rows in = rows loaded + rows rejected.",
        "**Refused fields** are recorded as audit facts: data the client did not provide.",
        "**Reperform-on-read.** Every screen rebuilds the data from the original file and refuses to show data it cannot reproduce.",
        "Each **run** freezes a manifest (procedure, engine version, a fingerprint of every input table, policies). A run is reviewed by the reviewer and approved by the partner, three different chairs.",
      ],
      where: ["Workbench → Sources & Mappings", "Workbench → Runs & Findings", "Studio → Next step 'Run', 'Review', 'Approve'"],
      doesNot: [
        "It does **no sampling**: no sample-size calculator, random selection, or attribute-test workpaper.",
        "It does not inspect documents or judge authenticity. It compares records.",
        "It reads CSV and Excel (.xlsx) files, and has ready-made readings for four standard QuickBooks Online reports (Lesson 6). Other formats, such as PDF statements, are kept as evidence but not tested.",
      ],
      tryIt: "In Studio, follow the Next step card through Run, Review and Approve, switching chairs when it asks.",
    },
  },

  {
    n: 6,
    slug: "accounts-payable",
    title: "Accounts payable and the search for unrecorded liabilities",
    phase: "Fieldwork",
    question: "Is every liability at year end recorded — and only real ones?",
    minutes: 40,
    objectives: [
      "Get payables records out of the client's accounting system and check they are complete",
      "Tie the AP subledger to the general ledger",
      "Perform a search for unrecorded liabilities",
      "Test cutoff around year end",
      "Turn exceptions into dispositions without overstating them",
    ],
    sections: [
      {
        heading: "Getting the records from the client's books",
        blocks: [
          { p: "The client's records live in its accounting system, often **QuickBooks** at a small company or an **ERP** at a larger one. The auditor asks for **reports**, not a summary: the list of open bills, the payments, the vendor list, the general ledger. Ideally you watch them being run, or run them yourself with read-only access." },
          { p: "A report the client produces is **information produced by the entity**. Before relying on it, test that it is complete and accurate (AU-C 500): does it foot, does it cover the whole period, does it agree to the ledger? A clean-looking export can still leave things out." },
          { terms: [
            ["Unpaid Bills", "QuickBooks' list of open bills by vendor. This is the **AP subledger**."],
            ["General Ledger", "Every account's activity and balance. Its **Accounts Payable** balance is the **control account** the subledger must equal."],
            ["Bill Payment List", "The payments made against bills: the population for payment tests and the search for unrecorded liabilities."],
            ["Vendor Contact List", "The vendor master: names, addresses and tax IDs, where look-alike vendors show up."],
          ] },
          { p: "Export each report to Excel and keep the file exactly as exported. Then **foot it**: recompute the totals yourself before you trust them. That is the first thing to do in a spreadsheet, and the first thing Noesi does too." },
          { harborline: "Harborline moved from QuickBooks to a mid-market ERP in March 2024, so its records reached you as ERP exports in CSV. The steps are the same: the subledger, the ledger, the payments and the vendors, each checked for completeness before any test." },
        ],
      },
      {
        heading: "Start with the tie-out",
        blocks: [
          { p: "Before testing detail, prove the detail supports the balance: the **AP subledger** (the list of open invoices by vendor) should equal the **GL control account**. A difference means the detail you are about to test is not the balance on the statements." },
          { harborline: "Harborline's AP subledger totals **$2,731,569.42**; GL control account 2000 shows **$2,750,019.42** — a **$18,450.00** difference. It is below clearly trivial ($21,000). Is a year-end control-account difference *qualitatively* trivial? That is your judgment to argue and document." },
        ],
      },
      {
        heading: "The search for unrecorded liabilities",
        blocks: [
          { p: "Because payables are usually **understated**, testing the recorded balance is not enough — you look for liabilities that **should** be there but are not. The classic procedure:" },
          { steps: [
            "Take **cash disbursements after year end** (typically through fieldwork) above a threshold.",
            "For each, find the invoice and receiving evidence and ask: **when was the liability incurred?**",
            "If the goods or services were received **on or before year end**, the liability belonged in the year-end balance. Check that it was recorded.",
            "Also review unmatched receiving reports, unprocessed invoices, and vendor statements.",
          ] },
          { harborline: "Harborline's payment **PAY-2026-0055** is dated **8 January 2027** — after year end — and cleared the bank on 12 January. It pays voucher **VCH-2026-9336**, which is **not in the voucher population at all**. Its $32,208.42 exceeds clearly trivial. A January payment for a voucher that the year-end records do not contain is exactly what this search exists to catch." },
        ],
      },
      {
        heading: "Cutoff",
        blocks: [
          { p: "Transactions near year end must land in the right period. Examine receiving reports and invoices dated in the last days before and first days after year end, and check each against the period it was recorded in. A December receipt booked in January **understates** year-end liabilities." },
        ],
      },
      {
        heading: "From exception to conclusion",
        blocks: [
          { p: "Each exception needs a documented judgment. The chain is always the same:" },
          { steps: [
            "**What did the test observe?** (A payment citing a voucher that does not exist.)",
            "**What could explain it?** (Export gap, keying error, duplicate, fabrication.)",
            "**What did the investigation conclude?**",
            "Only then: **is there a misstatement, and how much?**",
          ] },
          { p: "Watch for one defect surfacing in two tests. A voucher citing a nonexistent PO fails both the PO-reference test and the three-way match. Put it on the summary of differences once." },
          { harborline: "In Harborline, three vouchers with phantom POs appear in both tests. Counting both would double up about $27,000 of exposure." },
        ],
      },
      {
        heading: "When the client sends a corrected file",
        blocks: [
          { p: "Mid-audit, clients send corrected extracts. The file is not the problem: the problem is the work you already did on the old one. Every run, exception and judgment that rested on the old file must be revisited, and a finding that **disappears** after a 'correction' is not automatically resolved. Ask what the correction was, and why it came when it did." },
        ],
      },
    ],
    standards: [
      ["AU-C 330", "Substantive procedures responsive to completeness and cutoff risks"],
      ["AU-C 500", "Evaluating the completeness of populations used as evidence"],
      ["AU-C 450", "Accumulating and evaluating identified misstatements"],
    ],
    check: [
      { q: "Why does the search for unrecorded liabilities look at payments made *after* year end?",
        options: ["Because year-end payments are not important", "Because a liability incurred before year end is often paid after it — the later payment reveals a liability that may be missing from the balance", "To test the bank reconciliation", "To test sales cutoff"],
        answer: 1,
        why: "Completeness is tested by starting outside the recorded balance and working back to it." },
      { q: "Goods arrived 29 December; the invoice was recorded 6 January. At 31 December AP is…",
        options: ["correct", "understated", "overstated", "unaffected"],
        answer: 1,
        why: "The liability existed at year end (goods received) but was not recorded until January." },
      { q: "One phantom-PO voucher fails both the PO-reference test and the three-way match. On the SAD it appears…",
        options: ["twice — once per test", "once, with the other finding cleared by reference", "not at all", "as two halves"],
        answer: 1,
        why: "One root cause, one misstatement. Cross-reference the second finding to avoid double-counting." },
    ],
    task: {
      title: "Search for unrecorded liabilities",
      intro: "Use payments.csv, vouchers.csv and ap_control_balance.csv.",
      steps: [
        "List every payment dated after 31 December 2026 and every payment whose voucher is missing from vouchers.csv.",
        "For each, state whether a year-end liability may be missing and what evidence you would request.",
        "Reconcile the subledger to the GL, and write both sides of the argument on whether $18,450 is qualitatively trivial.",
      ],
      deliver: "A search-for-unrecorded-liabilities workpaper and a tie-out.",
    },
    noesi: {
      coverage: "full",
      summary: "Accounts payable is Noesi's home ground: eleven procedures, recorded judgments, and a trail of what changed when the client's files changed.",
      does: [
        "It runs the AP procedures: **payment→voucher** and **voucher→PO references**, **document chain**, **three-way match**, **segregation of duties**, **vendor twins**, **split payments**, **subledger–GL tie**, **bank clearing**, **GL posting** and **closed value flows**.",
        "Every exception needs a **disposition** with a note: cleared, unadjusted, adjusted, waived, or follow-up. Above clearly trivial, the disposition is a **proposal until a second person concurs**.",
        "**What Changed** compares a corrected client file with the one it replaced. It names the stale runs, shows which exceptions appear, disappear or move, and flags the judgments to revisit. It changes nothing by itself.",
        "It reads **QuickBooks Online exports** directly (Excel files): Unpaid Bills, Bill Payment List, Transaction List by Vendor and Vendor Contact List. It recomputes every subtotal and refuses a report whose layout it doesn't recognize.",
        "From an **Unpaid Bills** export and a **General Ledger** export it builds the AP control balance: both reports footed first, then saved as a source file that goes through the same propose and approve steps as any other.",
      ],
      where: ["Studio → Exceptions (judge in plain words)", "Studio → What changed (cascade)", "Workbench → Runs & Findings, What Changed", "Workbench → Sources & Mappings (QuickBooks files, AP subledger-to-ledger tie)"],
      doesNot: [
        "It has **no subsequent-disbursements search procedure**. PAY-2026-0055 surfaces as a reference exception, but the unrecorded-liability judgment is yours.",
        "It does not detect duplicate invoices. Harborline's Assignment 11 exists to show that silence.",
        "It does not check cutoff on receipts, because the receipts file has no receiving-cutoff test.",
        "It does not connect to QuickBooks. You export the reports and upload them.",
        "It reads only the Accounts Payable balance from a General Ledger export, not the full ledger detail. If the two reports are dated differently, it notes the mismatch but does not yet refuse the tie.",
      ],
      tryIt: "Load case-studies/harborline-marine/revision/vouchers_revised.csv after judging a few exceptions, then open What changed.",
    },
    video: {
      file: "learn-6-a-bill-nobody-can-find.mp4",
      poster: "learn-6-a-bill-nobody-can-find.jpg",
      title: "A bill nobody can find",
      minutes: 3,
      credits: "Narration: ElevenLabs voice “Guy”. Screens: QuickBooks Online test-drive sample company (Craig's Design and Landscaping Services), recorded live; Excel for the web; Noesi Workbench and Learn on the Harborline demo.",
    },
  },

  {
    n: 7,
    slug: "revenue-and-receivables",
    title: "Revenue and accounts receivable",
    phase: "Fieldwork",
    question: "Did the sales happen, and will the receivables be collected?",
    minutes: 30,
    objectives: [
      "Apply the presumed fraud risk in revenue recognition",
      "Design receivable confirmations and alternative procedures",
      "Test revenue cutoff",
      "Evaluate the allowance for doubtful accounts",
    ],
    sections: [
      {
        heading: "Revenue is presumed risky",
        blocks: [
          { p: "AU-C 240 presumes a risk of material misstatement due to fraud in **revenue recognition**. You may rebut the presumption only with documented reasons. The typical fraud is **overstatement**: fictitious sales, early recognition, or channel stuffing. So for revenue and receivables, **occurrence and existence** lead, with **cutoff** close behind." },
          { harborline: "Harborline earns revenue from vessel sales, service work and winter storage across four locations. A lender watching revenue and a current-ratio covenant supplies the pressure. **Figures in this lesson are illustrative — the case data covers payables only.**" },
        ],
      },
      {
        heading: "Confirmations",
        blocks: [
          { p: "Sending **external confirmations** to customers is the strongest existence evidence for receivables. Under AU-C 330, when receivables are material and you decide **not** to confirm them, you must document why. AU-C 505 governs how confirmations are sent and controlled." },
          { terms: [
            ["Positive confirmation", "The customer replies whether they agree or not. Stronger evidence. Non-replies need follow-up."],
            ["Negative confirmation", "The customer replies only if they disagree. Weaker evidence, suitable only in limited, low-risk conditions."],
            ["Control of the process", "You select the accounts, mail or send them yourself, and replies come directly to you, never through the client."],
          ] },
          { p: "For non-replies, perform **alternative procedures**: examine **cash received after year end** for that invoice, or shipping documents and the customer's order." },
        ],
      },
      {
        heading: "Cutoff and valuation",
        blocks: [
          { list: [
            "**Revenue cutoff**: examine shipments or service completions just before and after year end and check the period of the sale. Sales pulled into December overstate revenue and receivables.",
            "**Valuation**: review the **aging** of receivables, subsequent collections, and management's **allowance for doubtful accounts**. An estimate needs evidence about its method, data and assumptions.",
          ] },
          { p: "Illustration: a $180,000 boat sale recorded 30 December, with the vessel delivered 4 January. If control passes on delivery, that revenue belongs in January. Against $420,000 materiality it is significant, and qualitatively sensitive because of the covenant." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "Presumed fraud risk in revenue recognition"],
      ["AU-C 330", "Documenting a decision not to confirm material receivables"],
      ["AU-C 505", "External confirmations"],
      ["AU-C 540", "Accounting estimates, e.g. the allowance for doubtful accounts"],
    ],
    check: [
      { q: "Which assertion does an AR confirmation mainly address?",
        options: ["Completeness", "Existence", "Valuation", "Presentation"],
        answer: 1,
        why: "A customer confirming a balance evidences that the receivable exists. It says little about collectibility." },
      { q: "A positive confirmation is not returned. Next step?",
        options: ["Treat it as confirmed", "Perform alternative procedures: subsequent cash receipts or shipping documents", "Remove the balance", "Ask the client to call the customer"],
        answer: 1,
        why: "A non-reply is not evidence. Alternative procedures supply it." },
      { q: "Revenue recognition fraud risk under AU-C 240 is…",
        options: ["only considered for public companies", "presumed, and rebutting it requires documented reasons", "never presumed", "the auditor's to ignore if controls are strong"],
        answer: 1,
        why: "It is a rebuttable presumption, and the documentation requirement is explicit." },
    ],
    task: {
      title: "Design the confirmation plan",
      intro: "Illustrative: Harborline has 240 customer balances totalling $3.1m; the ten largest total $1.9m.",
      steps: [
        "Decide which balances to confirm and whether positive or negative, and justify it.",
        "Write the alternative procedures for a non-reply.",
        "List three cutoff tests for vessel sales around 31 December.",
      ],
      deliver: "A one-page receivables plan.",
    },
    noesi: {
      coverage: "none",
      summary: "Noesi does not audit revenue or receivables yet. Here is what it can and cannot hold.",
      does: [
        "The **evidence vault** keeps PDFs, CSVs and Excel files unaltered with a SHA-256 fingerprint, for example confirmation replies received as PDFs.",
        "The engagement's review, disposition and lock disciplines apply to the whole file.",
      ],
      where: ["Workbench → Sources & Mappings (upload documents)"],
      doesNot: [
        "It has **no receivables or revenue procedures**, no confirmation tracking, and no aging or allowance tools. Coverage will not invent them, and AP engines cannot be relabeled as AR tests.",
        "Images (photos or scans saved as images) are not accepted file types.",
      ],
    },
  },

  {
    n: 8,
    slug: "cash",
    title: "Cash",
    phase: "Fieldwork",
    question: "Does the cash on the balance sheet really exist, and is it cut off correctly?",
    minutes: 25,
    objectives: [
      "Audit a bank reconciliation",
      "Explain outstanding checks and deposits in transit",
      "Test cash cutoff with subsequent bank activity",
      "Know what SAS 150 changes for cash confirmations",
    ],
    sections: [
      {
        heading: "The bank reconciliation",
        blocks: [
          { p: "The client's reconciliation explains the difference between the **bank's balance** and the **book balance** at year end:" },
          { table: { head: ["Bank balance", "± reconciling items", "= Book balance"], rows: [
            ["per bank statement", "− outstanding checks (written, not yet cleared)", ""],
            ["", "+ deposits in transit (recorded, not yet credited)", ""],
            ["", "± bank errors", "per general ledger"],
          ] } },
          { p: "You test it: agree the bank balance to **independent evidence** (a confirmation or the next statement obtained directly), agree the book balance to the GL, and **trace reconciling items** to the bank activity in the following weeks. Outstanding checks should clear soon after year end; deposits in transit should appear within a few days." },
        ],
      },
      {
        heading: "Cutoff and kiting",
        blocks: [
          { p: "Checks written at year end but held back (not mailed) make liabilities look paid and cash look lower. Checks recorded in January but dated December do the opposite. **Kiting** moves money between accounts at year end so the same cash appears in both. A **bank transfer schedule** around year end exposes it." },
          { harborline: "Harborline's **PAY-2026-0028** ($16,830.55) is dated **31 December 2026** and cleared the bank on **2 January 2027**: a genuine outstanding check at year end. Tracing it to January clearing is the test. A check that never clears would be the question." },
        ],
      },
      {
        heading: "Confirmations and SAS 150",
        blocks: [
          { p: "Cash is often confirmed directly with the bank. The AICPA's **SAS No. 150, External Confirmations** (July 2026) adds a **requirement to confirm cash and cash equivalents held by third parties** unless certain conditions exist. It is effective for audits of periods ending on or after **December 15, 2028**, with early adoption permitted. Harborline's 2026 audit predates it, but the direction is clear." },
        ],
      },
    ],
    standards: [
      ["AU-C 505", "External confirmations"],
      ["SAS 150", "External Confirmations: cash confirmation requirement, effective for periods ending on or after 12/15/2028"],
      ["AU-C 330 / 500", "Substantive procedures and evidence for cash"],
    ],
    check: [
      { q: "An outstanding check at year end is…",
        options: ["recorded by the bank but not the books", "recorded in the books but not yet cleared by the bank", "a deposit in transit", "a bank error"],
        answer: 1,
        why: "The company wrote and recorded it. The bank has not paid it yet." },
      { q: "The best evidence that a year-end outstanding check was real is…",
        options: ["the controller's list", "its clearing on the bank statement shortly after year end, obtained directly", "the check stub", "the GL entry"],
        answer: 1,
        why: "Subsequent bank clearing, from a source you obtained, is independent evidence." },
      { q: "SAS 150 applies to audits of periods ending on or after…",
        options: ["December 15, 2023", "December 15, 2025", "December 15, 2028", "It is already mandatory for 2026"],
        answer: 2,
        why: "SAS 150 is effective for periods ending on or after December 15, 2028, with early adoption permitted." },
    ],
    task: {
      title: "Cash cutoff from the bank feed",
      intro: "Use payments.csv and bank.csv.",
      steps: [
        "List every payment dated in the last ten days of 2026 and find its bank clearing date.",
        "Classify each: cleared before year end, or an outstanding check at year end.",
        "Find any payment that never clears in bank.csv and say what you would do.",
      ],
      deliver: "An outstanding-check listing with clearing dates.",
    },
    noesi: {
      coverage: "partial",
      summary: "Noesi tests the payments side of cash against an independent bank feed. It is not a bank-reconciliation tool.",
      does: [
        "**Bank clearing** (`cash.bank_clearing`) checks that every recorded payment appears in the bank feed at the same amount, within a **2% tolerance**.",
        "**GL posting** (`gl.payment_posting`) checks that each payment posted to the GL at the right amount and in the right period. Period mismatches are cutoff exceptions.",
      ],
      where: ["Studio → Overview (the 'Cleared bank' and 'Posted to GL' circles)", "Workbench → Runs & Findings"],
      doesNot: [
        "It does not audit the cash balance itself: no bank-reconciliation workpaper, deposits in transit, receipts side, or bank confirmation tracking.",
        "Its 2% tolerance hides small differences. In Harborline, one 0.9% difference is correctly silent, so reconcile by hand to find it.",
      ],
    },
  },

  {
    n: 9,
    slug: "inventory",
    title: "Inventory",
    phase: "Fieldwork",
    question: "Is the inventory there, owned, and worth what it is carried at?",
    minutes: 25,
    objectives: [
      "Plan and attend a physical inventory count",
      "Perform test counts in both directions",
      "Test inventory cutoff, pricing and obsolescence",
    ],
    sections: [
      {
        heading: "Attend the count",
        blocks: [
          { p: "When inventory is material, AU-C 501 requires you to **attend the physical count** unless impracticable. If you cannot, you must perform alternative procedures. If those fail, you must modify the opinion. You observe the client's count procedures and make **test counts**." },
          { terms: [
            ["Floor to sheet", "Count items on the floor and trace them to the count records. This tests **completeness**."],
            ["Sheet to floor", "Take items from the count records and find them on the floor. This tests **existence**."],
          ] },
          { harborline: "Harborline carries vessels for sale and a parts warehouse in Norfolk. **Figures here are illustrative — the case data covers payables only.** A boat on consignment from a manufacturer sits on the lot but may not be Harborline's: **rights and obligations** matter as much as existence." },
        ],
      },
      {
        heading: "Cutoff, pricing and obsolescence",
        blocks: [
          { list: [
            "**Cutoff**: record the last receiving and shipping document numbers at the count. Goods received before the count must be in both inventory and payables. This is where inventory meets Lesson 6.",
            "**Pricing**: test the cost of counted items against vendor invoices and the costing method.",
            "**Valuation**: identify slow-moving or damaged items and test whether inventory is written down to the lower of cost and net realizable value.",
          ] },
          { watch: "Harborline's warehouse switched to scanner receiving mid-year, and the controller expects some receipts never reached the system. That affects inventory completeness and payables completeness at the same time." },
        ],
      },
    ],
    standards: [
      ["AU-C 501", "Specific considerations for inventory: attendance at physical counting"],
      ["AU-C 540", "Estimates: net realizable value, obsolescence reserves"],
    ],
    check: [
      { q: "Tracing items from the floor to the count sheets tests…",
        options: ["existence", "completeness", "valuation", "presentation"],
        answer: 1,
        why: "Starting from the physical items checks that everything present was recorded." },
      { q: "Inventory is material and you cannot attend the count. You must…",
        options: ["rely on management's count", "perform alternative procedures; if they are insufficient, modify the opinion", "exclude inventory from the audit", "issue a clean opinion with a note"],
        answer: 1,
        why: "AU-C 501 requires attendance unless impracticable, then alternatives, then a modified opinion." },
      { q: "A consigned vessel on Harborline's lot threatens which assertion if it is counted?",
        options: ["Cutoff", "Rights and obligations", "Classification", "Accuracy"],
        answer: 1,
        why: "It exists, but Harborline does not own it." },
    ],
    task: {
      title: "Plan the count",
      intro: "Illustrative: 38 vessels on four lots; 6,200 part SKUs in Norfolk.",
      steps: [
        "Write the count instructions you would review and the observations you would make.",
        "Design test counts in both directions, with sample sizes.",
        "Link the receiving-process change to both inventory and payables cutoff.",
      ],
      deliver: "A count-attendance plan.",
    },
    noesi: {
      coverage: "none",
      summary: "Noesi has no inventory procedures. Count attendance is physical work that no software performs.",
      does: [
        "The vault can keep count sheets and price lists as PDF, CSV or Excel files, unaltered and fingerprinted.",
        "The **three-way match** touches inventory indirectly: it flags invoices without receipts, which is also an inventory-completeness signal.",
      ],
      where: ["Workbench → Sources & Mappings (store documents)"],
      doesNot: [
        "It has no count, test-count, cutoff, pricing or obsolescence procedures. Coverage will never report inventory as tested.",
      ],
    },
  },
];
