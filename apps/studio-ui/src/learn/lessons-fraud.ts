// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** "Fraud in payables": a CFE-aligned track. Plan, exam mapping and sources:
 *  docs/learn/FRAUD-MODULE-OUTLINE.md. ACFE figures are from its
 *  Occupational Fraud 2026: A Report to the Nations; standards facts were
 *  checked on 2026-09-23. */

import { Lesson } from "./types";

export const FRAUD_LESSONS: Lesson[] = [
  {
    n: 1,
    slug: "fraud-why-it-happens",
    title: "Why fraud happens",
    phase: "Fraud",
    question: "What turns an employee into a fraudster, and how do we sort what they did?",
    minutes: 25,
    objectives: [
      "Tell fraud apart from error, and occupational fraud from organizational crime",
      "Explain the three sides of the fraud triangle and which one an organization controls most directly",
      "Place a scheme on one of the three branches of the ACFE's Fraud Tree",
      "Use the latest ACFE research on how common and how costly each kind of fraud is",
    ],
    sections: [
      {
        heading: "Fraud is about intent",
        blocks: [
          { p: "An **error** is an unintentional mistake: a clerk keys 1,000 instead of 100. **Fraud** is intentional deception to gain something the person is not entitled to. The two can leave identical traces in the records. What separates them is intent, and intent is exactly what records rarely show." },
          { p: "Two words you will meet everywhere:" },
          { terms: [
            ["Occupational fraud", "Someone uses their job to enrich themselves by deliberately misusing the organization's resources. The organization is the **victim**. This is the ACFE's subject and this track's."],
            ["Organizational crime", "The organization itself commits the crime, for example deceiving customers or regulators. The organization is the **offender**."],
          ] },
          { p: "A financial-statement auditor sorts fraud a little differently. AU-C 240 names two kinds of intentional misstatement: **fraudulent financial reporting** (cooking the books) and **misappropriation of assets** (theft). An auditor cares about fraud because it can make the statements materially wrong." },
          { watch: "An exception in the data is not fraud. Noesi finds exceptions; people decide what they mean. Even then, an auditor does not make legal determinations of whether fraud occurred. That is for investigators and courts." },
        ],
      },
      {
        heading: "The fraud triangle",
        blocks: [
          { p: "In the 1950s the criminologist Donald Cressey interviewed people imprisoned for embezzlement. He found three conditions present together, now called the **fraud triangle**:" },
          { terms: [
            ["Pressure", "A financial or personal need the person feels they cannot share or solve honestly: debt, a lender covenant, a bonus target."],
            ["Opportunity", "A way to commit the fraud and hide it: a missing approval, one person controlling a whole process, nobody reviewing."],
            ["Rationalization", "A story that makes it feel acceptable: \"I'm only borrowing it\", \"everyone does it\", \"they underpay me\"."],
          ] },
          { p: "An organization can do something about all three, but it controls **opportunity** most directly. That is why controls matter: pressure and rationalization live inside people, while a second approval lives in the process. Culture reaches rationalization too; \"handled informally\" is a culture signal as well as a control gap." },
          { p: "Auditing standards use the same three ideas. AU-C 240 groups **fraud risk factors** as incentives or pressures, opportunities, and attitudes or rationalizations." },
          { watch: "The triangle explains fraud; it does not predict who will commit it. Most people under pressure never steal. Assess conditions and processes, never profile individuals." },
        ],
      },
      {
        heading: "The Fraud Tree: three branches",
        blocks: [
          { p: "The ACFE classifies occupational fraud in its **Occupational Fraud and Abuse Classification System**, usually called the Fraud Tree. It has three branches:" },
          { table: {
            head: ["Branch", "What it is", "In payables, for example", "Share of cases (2026)", "Median loss (2026)"],
            rows: [
              ["Asset misappropriation", "An employee steals or misuses the organization's resources", "Billing through a fake vendor; altering or self-approving payments", "90%", "$100,000"],
              ["Corruption", "An employee misuses their influence in a business deal for a benefit", "A buyer steers orders to a vendor that pays them a kickback; an undisclosed interest in a supplier", "45%", "$150,000"],
              ["Financial statement fraud", "Intentional misstatement or omission in the financial reports", "Leaving unpaid bills out of year-end payables to flatter the current ratio", "6%", "$1,000,000"],
            ],
          } },
          { p: "The shares add to more than 100% because one case can involve more than one branch. Notice the pattern: financial statement fraud is the **rarest** and the **costliest**." },
          { p: "Asset misappropriation splits further. The branch this track works on is **fraudulent disbursements**, where money leaves through the payment process: billing schemes, check and payment tampering, payroll, expense reimbursements and cash register disbursements. Harborline's data lets us practice the first two." },
        ],
      },
      {
        heading: "What the research says",
        blocks: [
          { p: "Every two years the ACFE publishes **Occupational Fraud: A Report to the Nations**, built from cases investigated by Certified Fraud Examiners. The 2026 edition covers **2,402 cases in 143 countries and territories**. Losses exceeded $3.4 billion; the **median loss was $104,000** per case." },
          { p: "The report finds that organizations with anti-fraud controls, such as **management review, proactive data monitoring and surprise audits**, had lower losses and caught fraud sooner. Proactive data monitoring is what Noesi's full-population procedures do: test every payment, not a sample." },
          { watch: "Report to the Nations describes cases that were found and investigated. Frauds never detected are not in it. Read its numbers as \"what investigated fraud looks like\", not the whole picture." },
        ],
      },
      {
        heading: "Harborline through the triangle",
        blocks: [
          { harborline: "The engagement brief (`docs/01-engagement-brief.md`) gives facts for every side except personal pressure. **Pressure on management:** the lender requires audited statements within 120 days and a current ratio of at least 1.25. **Opportunity:** the AP supervisor left in June and was not replaced until September; for about eleven weeks two AP clerks released payments without a dedicated approver. Vendor setup moved to purchasing in April, so the department that raises orders now also creates the vendors it orders from. Receiving moved to scanners, and \"a handful\" of receipts from the transition may be missing. **Rationalization, as a culture signal:** approval limits were \"handled informally\"." },
          { p: "Notice what the brief does **not** say: nothing about any employee's debts or motives. Do not invent them. The audit responds to conditions: where opportunity is high, test harder. The next lesson turns these conditions into a fraud risk assessment." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "Consideration of fraud in a financial statement audit: the two kinds of fraud, fraud risk factors, the auditor's responsibilities (current standard)"],
      ["SAS No. 151", "Replaces AU-C 240 for periods ending on or after December 15, 2028 (early adoption permitted); the definition of fraud is unchanged"],
      ["ACFE Fraud Tree", "The Occupational Fraud and Abuse Classification System: corruption, asset misappropriation, financial statement fraud"],
      ["ACFE Report to the Nations 2026", "2,402 cases; median loss $104,000; branch shares and median losses quoted above"],
    ],
    check: [
      { q: "An AP clerk keys a $4,500 invoice as $5,400 by mistake, and it is paid. What is it?",
        options: ["Asset misappropriation", "An error, not fraud", "Corruption", "Financial statement fraud"],
        answer: 1,
        why: "There is no intent to deceive. It is a misstatement that needs correcting, but fraud requires intent. The traces in the data could look the same, which is why intent has to be established, not assumed." },
      { q: "Which side of the fraud triangle can an organization reduce most directly?",
        options: ["Pressure", "Opportunity", "Rationalization", "None; all three are personal"],
        answer: 1,
        why: "Controls such as independent approval, segregation of duties and review remove or shrink opportunity. Pressure and rationalization live inside people, though culture influences rationalization." },
      { q: "A purchasing manager steers contracts to a supplier that secretly pays him 5% of each invoice. Which branch of the Fraud Tree?",
        options: ["Corruption", "Asset misappropriation", "Financial statement fraud", "Organizational crime"],
        answer: 0,
        why: "He misuses his influence in a business transaction for a personal benefit: a kickback, which is bribery under corruption. The company may also overpay, but the scheme is classified by how it works." },
      { q: "In the ACFE's 2026 report, which branch had the highest median loss per case?",
        options: ["Asset misappropriation", "Corruption", "Financial statement fraud", "They were about equal"],
        answer: 2,
        why: "Financial statement fraud: a median of $1,000,000, although it appeared in only 6% of cases. Asset misappropriation was the most common (90%) with the lowest median ($100,000)." },
      { q: "The brief says Harborline's approval limits were \"handled informally\" during the supervisor gap. Which side of the triangle does that mainly describe?",
        options: ["Pressure", "Opportunity", "Rationalization only", "None of them"],
        answer: 1,
        why: "Informal approval means payments could be released without an independent check, which is opportunity. It is also a culture signal that can feed rationalization (\"nobody follows the limit anyway\")." },
    ],
    task: {
      title: "Classify the schemes and map Harborline's triangle",
      intro: "Use the engagement brief (`case-studies/harborline-marine/docs/01-engagement-brief.md`) and this lesson.",
      steps: [
        "Name the Fraud Tree branch for each: (a) a clerk sets up a vendor in her cousin's name and bills for services never delivered; (b) a controller leaves December invoices out of payables; (c) a buyer accepts season tickets from a supplier bidding for a contract; (d) a clerk alters the payee on a check; (e) a manager records next year's sales in December; (f) a buyer owns part of a supplier he approves orders from.",
        "Draw the fraud triangle for Harborline. Under each side, list the facts from the brief that belong there, with a quote.",
        "Mark each fact as bearing on **management** (financial statement fraud) or on **employees** (asset misappropriation or corruption).",
        "Write one sentence on what the brief does not tell you, and why you should not fill that gap by guessing.",
      ],
      deliver: "A one-page classification and triangle, ready to feed the fraud risk assessment in the next lesson.",
    },
    noesi: {
      coverage: "none",
      summary: "This lesson is the thinking that comes before any tool. Noesi does not assess anyone's pressure or motives, and it does not classify schemes. It does run the payables tests that later lessons use to find the traces schemes leave.",
      does: [
        "Its procedures look for the traces of **fraudulent disbursements** that later lessons teach: look-alike vendors (`ap.vendor_relational_twins`), self-approved payments (`ap.segregation_of_duties`), payments split under an approval limit (`ap.split_payment_review`), and money that goes out and comes back (`forensic.closed_value_flow`).",
        "Each finding carries its own stated limitation, for example \"a twin is an investigation lead, not proof of duplication or fraud\".",
      ],
      where: ["Workbench → Runs & Findings", "Workbench → 📖 manual, chapter 5 (the procedures and their limits)"],
      doesNot: [
        "It does not judge intent, and it never labels a finding as fraud.",
        "It does not record fraud risk factors or the fraud triangle; you write those into the risk register (next lesson).",
      ],
    },
  },

  {
    n: 2,
    slug: "fraud-risk-assessment",
    title: "Fraud risk assessment",
    phase: "Fraud",
    question: "Where could fraud happen here, what would stop it, and what do we test?",
    minutes: 35,
    objectives: [
      "Tell a fraud from a fraud risk, and inherent risk from residual risk",
      "Carry out the steps of a fraud risk assessment for one process",
      "Describe the auditor's fraud responsibilities under AU-C 240, and what SAS No. 151 changes",
      "Link each fraud risk to a control and to a specific audit response",
    ],
    sections: [
      {
        heading: "A fraud risk is not a fraud",
        blocks: [
          { p: "A **fraud** is something that happened. A **fraud risk** is a way fraud could happen in a process, whether or not anyone has tried. A fraud risk assessment lists those ways before anyone is accused of anything." },
          { terms: [
            ["Inherent risk", "The risk before any controls: how likely and how damaging a scheme would be if nothing stood in its way."],
            ["Residual risk", "The risk left after the controls that actually operate. A control that exists on paper but was not performed does not lower it."],
            ["Internal vs external fraud risk", "Schemes by insiders (employees, management) vs outsiders (vendors, customers, hackers). Many payables schemes combine both, such as an employee colluding with a vendor."],
          ] },
          { p: "Management owns the organization's fraud risk management. In the widely used COSO internal control framework, one principle of the **risk assessment** component is that the organization considers the potential for fraud. The COSO and ACFE **Fraud Risk Management Guide** builds a full program around it. The auditor makes a separate assessment for the audit." },
        ],
      },
      {
        heading: "The steps",
        blocks: [
          { steps: [
            "**Understand the process** and who can move money or change records in it: who creates vendors, who enters bills, who approves and releases payments.",
            "**Brainstorm the schemes.** Walk the Fraud Tree: how could someone steal here, bribe here, or misstate here? Think like the person who wants to do it.",
            "**Rate inherent risk**, meaning likelihood and impact, before controls.",
            "**Identify the anti-fraud controls**, preventive (stop it) or detective (catch it), and find out whether they actually operated.",
            "**Rate residual risk**, what is left after the controls that operate.",
            "**Respond** to each residual risk: accept it, reduce it with a control, avoid the activity, or transfer it (for example insurance), within the organization's risk appetite. For an auditor, respond with specific audit procedures.",
          ] },
          { watch: "The most common mistake is rating residual risk from the control design. Harborline had an approval limit on paper; during the supervisor gap nobody enforced it. Residual risk follows what operated, not what was written." },
        ],
      },
      {
        heading: "The auditor's responsibility today: AU-C 240",
        blocks: [
          { p: "The auditor's objective is **reasonable assurance** that the statements are free of material misstatement, **whether due to fraud or error**. AU-C 240 turns that into specific work:" },
          { list: [
            "Keep **professional skepticism** throughout: recognize that fraud could exist regardless of past experience with the client's honesty.",
            "Hold an **engagement team discussion** about how and where the statements could be misstated by fraud.",
            "**Inquire** of management and others about fraud risks, known or suspected fraud, and how management responds to them.",
            "Evaluate **fraud risk factors**: incentives or pressures, opportunities, attitudes or rationalizations.",
            "Presume a fraud risk in **revenue recognition**. The presumption can be overcome only with documented reasons.",
            "Treat **management override of controls** as a risk in every audit. Respond by testing journal entries, reviewing accounting estimates for bias, and evaluating the business reason for significant unusual transactions.",
            "Build **unpredictability** into the procedures, and communicate identified or suspected fraud to the appropriate level of management and to those charged with governance.",
          ] },
          { watch: "A new standard is coming. The AICPA approved **SAS No. 151** in August 2026. It replaces AU-C 240 for audits of periods ending on or after **December 15, 2028** (early adoption permitted). It applies a fraud lens to the AU-C 315 risk assessment, requires understanding the entity's **whistleblower program** where one exists, and expands the responses and communications when fraud is identified or suspected. The definition of fraud and the auditor's overall objective do not change. Harborline's 2026 audit follows AU-C 240." },
        ],
      },
      {
        heading: "Harborline's payables fraud risks",
        blocks: [
          { p: "Here the brief's conditions from Lesson F1 become assessed risks. Three are worked through; the task asks you to finish the register." },
          { table: {
            head: ["Condition (brief)", "Scheme it enables", "Inherent", "Control, and did it operate?", "Residual", "Audit response"],
            rows: [
              ["AP supervisor gone June–September", "Payments entered and approved by the same clerk; payments with no valid bill", "High", "Independent payment approval: **not operating** for about eleven weeks", "High", "Test **every** payment for creator = approver; examine all gap-period payments to supporting bills"],
              ["Vendor setup moved to purchasing (April)", "A shell or duplicate vendor created and then ordered from by the same department", "High", "Independent review of vendor master changes: **unknown**, so ask and test", "High until shown otherwise", "Compare vendors on tax ID, name and address; trace new vendors to real business"],
              ["$10,000 payment approval limit", "Splitting one purchase into several payments just under the limit", "Moderate", "The limit, but no monitoring of clusters", "Moderate", "Look for several payments to one vendor, just under $10,000, within a few days"],
            ],
          } },
          { harborline: "Two more to finish yourself. **Scanner receiving**: missing receipts could hide bills for goods never delivered. **The lender covenant**: leaving unpaid bills out of year-end payables would lower current liabilities and flatter the current ratio. That is a financial statement fraud risk for management, and the classic response is a **search for unrecorded liabilities** in payments made after year end." },
        ],
      },
      {
        heading: "From risk to response",
        blocks: [
          { p: "Every residual risk needs an answer in the audit plan: which procedure, on what population, when. For payables, testing the **whole population** is the strongest answer a data tool gives. It cannot miss a self-approved payment because it wasn't in the sample." },
          { p: "Some fraud risks cannot be answered with payables data at all. Management override needs journal-entry testing; the revenue presumption needs revenue procedures. A good assessment says which risks it answered, and how, and which it answered some other way." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "The auditor's fraud responsibilities: skepticism, team discussion, inquiries, fraud risk factors, the revenue presumption, management override, unpredictability, communication"],
      ["SAS No. 151", "Approved August 2026; replaces AU-C 240 for periods ending on or after December 15, 2028; fraud lens on AU-C 315, whistleblower programs, responses and communications"],
      ["AU-C 315", "Identifying and assessing risks of material misstatement, including inherent and control risk"],
      ["COSO Internal Control framework (2013)", "Five components; the risk assessment component includes considering the potential for fraud"],
      ["COSO / ACFE Fraud Risk Management Guide", "Management's fraud risk program: governance, assessment, prevention and detection, investigation, monitoring"],
    ],
    check: [
      { q: "A control is designed but was not performed for three months. How does it affect residual risk for those months?",
        options: ["It lowers residual risk as designed", "It does not lower residual risk; residual risk follows the controls that operated", "Residual risk becomes zero", "It only affects inherent risk"],
        answer: 1,
        why: "Residual risk is what is left after controls that actually work. Harborline's approval limit during the supervisor gap is exactly this case." },
      { q: "Which response does AU-C 240 require in every audit, because management override is always a risk?",
        options: ["Confirming all receivables", "Testing journal entries, reviewing estimates for bias, and evaluating significant unusual transactions", "Observing the inventory count", "Interviewing every employee"],
        answer: 1,
        why: "Management can override any control, so the standard prescribes these three responses regardless of the assessed risk." },
      { q: "Harborline moved vendor setup into purchasing. Which scheme risk rises most?",
        options: ["Payroll ghost employees", "A shell or duplicate vendor that the same department then orders from and bills through", "Cash register skimming", "Revenue recognized too early"],
        answer: 1,
        why: "When one department both creates vendors and raises orders, nobody independent checks that a new vendor is real. That is the opportunity a billing scheme needs." },
      { q: "An auditor wants to rebut the presumed fraud risk in revenue recognition. What must they do?",
        options: ["Nothing; it is optional", "Document the reasons the presumption is overcome", "Get the client's written consent", "It can never be rebutted"],
        answer: 1,
        why: "AU-C 240 presumes the risk; overcoming it is allowed, but only with documented reasons." },
      { q: "Harborline's 2026 year-end audit: which fraud standard applies?",
        options: ["SAS No. 151 is mandatory", "AU-C 240; SAS No. 151 applies to periods ending on or after December 15, 2028, with early adoption permitted", "Neither; fraud is not an audit matter", "PCAOB AS 2401 only"],
        answer: 1,
        why: "SAS No. 151 was approved in August 2026 but is not yet effective for a December 2026 year end. A firm could adopt it early, but by default AU-C 240 applies." },
    ],
    task: {
      title: "Build Harborline's payables fraud risk register",
      intro: "Use the brief, the audit plan (`docs/02-audit-plan.md`) and this lesson.",
      steps: [
        "List every condition in the brief that creates a payables fraud risk, including the approval limit and the lender covenant.",
        "For each: the scheme it enables (with its Fraud Tree branch), inherent risk, the control and whether it operated, and residual risk.",
        "Write a specific audit response for each residual risk: which records, which test, whole population or sample, and why.",
        "Mark the risks that payables data cannot answer (for example management override) and name the procedure that would.",
        "Enter your three highest risks in Noesi's risk register (Workbench → Planning & Risk) with \"Fraud:\" at the start of each title, and link the procedures that respond.",
      ],
      deliver: "A fraud risk register of five to seven rows, and three risks recorded and linked in Noesi.",
    },
    noesi: {
      coverage: "partial",
      summary: "Noesi keeps the assessed risks and links each one to the procedures that answer it, with a second person's agreement for the serious ones. It does not have a separate fraud category, and it cannot answer fraud risks that need data it does not test.",
      does: [
        "The **risk register** records a title, the assertion at risk (occurrence, completeness, accuracy, authorization or cutoff), a level from unassessed to significant, a rationale and a planned response.",
        "Each risk links to the **procedures that respond** to it; Coverage then shows whether the data you loaded can actually run them.",
        "A risk rated **high** or **significant** needs a second person's concurrence. Completion is blocked while any risk is unassessed, or while a high or significant risk has no response or no linked procedure.",
      ],
      where: ["Workbench → Planning & Risk", "Workbench → Coverage", "Workbench → 📖 manual, chapter 2"],
      doesNot: [
        "It has no fraud flag or fraud-risk-factor fields. Name fraud in the title and rationale.",
        "It does not test journal entries, estimates or revenue, so management override and the revenue presumption need work outside it.",
        "It keeps no record of the team discussion or the inquiries AU-C 240 requires.",
      ],
      tryIt: "Start with --demo, open Planning & Risk, and add \"Fraud: self-approved payments during the supervisor gap\" against authorization, linked to ap.segregation_of_duties.",
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
      "Describe the three kinds of billing scheme: shell company, non-accomplice vendor and personal purchases",
      "Recognize the red flags of a shell or duplicate vendor in a vendor master",
      "Explain how duplicate invoices and bills for goods never received get through",
      "Name the prevention and detection controls for billing schemes",
    ],
    sections: [
      {
        heading: "Billing schemes: making the company pay a false bill",
        blocks: [
          { p: "In a **billing scheme** the fraudster makes the organization pay an invoice it does not owe. The payment process itself does the stealing; nobody has to touch cash. That is why billing schemes are among the most common fraudulent disbursements." },
          { terms: [
            ["Shell company scheme", "The fraudster creates a fictitious vendor, often with a name close to a real one, and bills for goods or services that never existed. The payments go to an account they control."],
            ["Non-accomplice vendor scheme", "A real vendor is used without knowing it: the fraudster pays the same invoice twice and intercepts the refund, or inflates a genuine invoice (\"pay and return\" and overbilling)."],
            ["Personal purchases", "The fraudster buys things for themselves with company money and codes the invoice as a business expense."],
          ] },
          { watch: "Services are easier to fake than goods. Nothing has to arrive at the warehouse, so there is no receiving record to contradict the bill." },
        ],
      },
      {
        heading: "Red flags in the vendor master",
        blocks: [
          { p: "A shell vendor has to exist in the vendor master before it can be paid. That makes the vendor list one of the best places to look:" },
          { list: [
            "Two vendors with the **same tax ID**, bank account or address, but different vendor numbers.",
            "Near-identical names: \"Harbor\" and \"Harbour\", \"Inc\" and \"Inc.\", \"&\" and \"and\".",
            "A vendor whose address or bank account matches an **employee's**.",
            "A P.O. box or mail drop as the only address; no phone; a tax ID that does not validate.",
            "A new vendor that quickly receives large or frequent payments, often round amounts, for vague services.",
          ] },
          { p: "Who can **create** a vendor matters as much as who can pay one. If the same person or department can set up a vendor, raise its order and approve its bill, one person can run the whole scheme." },
        ],
      },
      {
        heading: "Duplicate bills and goods never received",
        blocks: [
          { p: "Two quieter versions leave traces in the document chain rather than the vendor list:" },
          { list: [
            "**Duplicate invoice**: the same purchase billed twice, for example with a new invoice number, a slightly different date, or a second voucher against the same purchase order. One payment is real; the other is the theft.",
            "**Billing for goods never received**: an invoice is paid although no receipt shows the goods arrived, or arrived in a smaller quantity than billed. This is what the **three-way match** (order, receipt, invoice) exists to stop.",
          ] },
          { p: "**Prevention:** independent vendor setup and review, a three-way match before payment, and a system check for duplicate invoice numbers and amounts. **Detection:** compare the vendor master against itself and against employee records, test every paid invoice for a receipt, and look for the same vendor, amount and order paid twice." },
        ],
      },
      {
        heading: "Harborline: look-alike vendors and a second bill",
        blocks: [
          { harborline: "Three pairs of vendors share a remit city (Norfolk) **and a tax ID**: V1038 \"Harbor Marine Supply LLC\" and V1039 \"Harbour Marine Supply, L.L.C.\"; V1040 \"Nautical Parts Inc\" and V1041 \"Nautical Parts, Inc.\"; V1042 \"Coastal Fuel & Marine Services\" and V1043 \"Coastal Fuel and Marine Svcs\". **Both identities in every pair are being paid.** Remember that vendor setup moved into purchasing in April." },
          { harborline: "PAY-2026-0013 (21,619.99 to Gulfstream Propulsion) cites voucher VCH-2026-9338, which is **not in the voucher file**. When the client later sends a corrected file (Assignment 11), 9338 appears: same vendor, same amount and same purchase order as VCH-2026-0013, entered one week later. That is the shape of a duplicate invoice." },
          { harborline: "Seven vouchers fail the three-way match: four were paid with **no receipt at all** (VCH-2026-0010, 0020, 0043, 0116) and three were billed for more than was received (0009, 0078, 0104)." },
          { watch: "Each of these is a lead. Look-alike vendors can be a legitimate company entered twice by mistake; a missing receipt can be a lost scan from the receiving change. The job is to find out which, not to assume." },
        ],
      },
    ],
    standards: [
      ["ACFE Fraud Tree", "Billing schemes (shell company, non-accomplice vendor, personal purchases) under fraudulent disbursements"],
      ["CFE exam 2026, section 1", "Asset misappropriation: fraudulent disbursements (13%); procurement fraud (8%)"],
      ["AU-C 240", "Misappropriation of assets as a source of material misstatement; fraud risk factors"],
    ],
    check: [
      { q: "A clerk sets up \"Harbour Supply LLC\" next to the real \"Harbor Supply LLC\", with her own bank account, and bills for consulting. What kind of scheme?",
        options: ["Non-accomplice vendor scheme", "Shell company scheme", "Personal purchases", "Payment tampering"],
        answer: 1,
        why: "The vendor is fictitious and the payments go to an account she controls. A look-alike name helps the fake vendor blend in." },
      { q: "Which single fact in a vendor master is the strongest duplicate-vendor signal?",
        options: ["Both vendors are in the same city", "Two vendor numbers share one tax ID", "The vendor was created this year", "The vendor sells services"],
        answer: 1,
        why: "A tax ID identifies one taxpayer. Two vendor records with the same one are the same business, or someone copying a real business's identity." },
      { q: "An invoice is paid twice: once on the original voucher and once on a new voucher for the same purchase order. What control would most directly have stopped it?",
        options: ["Bank reconciliation", "A check for duplicate invoices against the same vendor, amount and order before payment", "Physical inventory count", "Management representation letter"],
        answer: 1,
        why: "A duplicate check at the point of entry or payment stops the second bill. A bank reconciliation would show both payments as legitimately cleared." },
      { q: "Why are billing schemes for services harder to detect than for goods?",
        options: ["Services cost more", "No receiving record has to contradict the bill", "Services are never audited", "Service vendors have no tax ID"],
        answer: 1,
        why: "Goods should produce a receipt that the three-way match can check. A service leaves nothing at the loading dock, so the approver's knowledge is the main control." },
    ],
    task: {
      title: "Find the look-alikes before Noesi does",
      intro: "Use `case-studies/harborline-marine/data/vendors.csv`, `vouchers.csv` and `payments.csv` in a spreadsheet.",
      steps: [
        "Sort `vendors.csv` by **Tax ID**. List every tax ID used by more than one vendor number.",
        "For each pair, count the vouchers and payments to each vendor number. Is only one identity active, or both?",
        "In `payments.csv`, list payments whose voucher number is not in `vouchers.csv`. For each, what would you ask the client?",
        "For one pair, write what evidence would show it is a harmless duplicate entry, and what would show a shell vendor.",
      ],
      deliver: "A one-page vendor analysis: the pairs, their activity, and the evidence you would request.",
    },
    noesi: {
      coverage: "partial",
      summary: "Noesi finds look-alike vendors by name, payments that cite vouchers missing from the file, and vouchers paid without a matching receipt. It does not compare tax IDs or bank accounts, and it has no duplicate-invoice test.",
      does: [
        "`ap.vendor_relational_twins` flags vendors with **near-identical names** (and vendors with near-identical activity). Its stated limit: \"A structural twin is an investigation lead, not proof of duplication or fraud.\"",
        "`ap.payment_voucher_reference` flags payments whose voucher is **not in the voucher population**, like PAY-2026-0013.",
        "`ap.three_way_receipt_match` flags vouchers paid with no receipt, or billed above what was received.",
      ],
      where: ["Workbench → Runs & Findings", "Workbench → What Changed (for the corrected file in Assignment 11)"],
      doesNot: [
        "It reads only vendor number and name, so **shared tax IDs, addresses or bank accounts** are yours to find.",
        "It has **no duplicate-invoice test**. VCH-2026-9338 is found by reading the data, not by a procedure.",
        "It does not compare vendors with employee records.",
      ],
      tryIt: "Start with --demo, run ap.vendor_relational_twins, and compare its pairs with the tax-ID pairs from your spreadsheet.",
    },
  },

  {
    n: 4,
    slug: "fraud-payment-tampering",
    title: "Payment tampering, self-approval and split payments",
    phase: "Fraud",
    question: "How are payment controls bypassed, and where does it show?",
    minutes: 35,
    objectives: [
      "Describe the main payment tampering schemes, on paper checks and electronic payments",
      "Explain why one person entering and approving a payment is a control failure, not a finding of fraud",
      "Recognize payments split to stay under an approval limit",
      "Use the bank and the general ledger as independent checks on the payment records",
    ],
    sections: [
      {
        heading: "Payment tampering",
        blocks: [
          { p: "In **payment tampering** the fraudster takes control of a payment itself rather than inventing a bill. With paper checks the classic forms are:" },
          { terms: [
            ["Forged maker", "Signing a company check without authority."],
            ["Forged endorsement", "Intercepting a check made out to someone else and endorsing it to yourself."],
            ["Altered payee or amount", "Changing who a legitimate check pays, or how much, after it is approved."],
            ["Authorized maker", "Someone allowed to sign or release payments simply pays themselves or an accomplice."],
            ["Concealed check", "Slipping a check into a batch so an approver signs without reading it."],
          ] },
          { p: "Electronic payments have the same shapes: changing the bank account on a vendor record, or releasing a payment you also approved. Tampering needs concealment afterwards, so it often leaves a mismatch between the **payment record**, the **bank** and the **general ledger**." },
        ],
      },
      {
        heading: "Self-approval and approval limits",
        blocks: [
          { p: "The core payment control is **segregation of duties**: the person who enters a payment is not the person who approves it. When one person does both, nothing independent stands between that person and the money. That is the **authorized maker** opportunity." },
          { p: "An **approval limit** adds a second layer: payments above, say, $10,000 need a more senior approver. The standard way around it is **splitting**: several payments to one vendor, each just under the limit, within a few days." },
          { watch: "Self-approval is a control failure, not proof of fraud. The engine's own limit says \"Field semantics and compensating controls require auditor evaluation.\" The approver field may mean something else in the system, or another control may have covered the gap. Find out before concluding." },
        ],
      },
      {
        heading: "Three independent records: payments, bank, ledger",
        blocks: [
          { p: "A payment is recorded in the payments file, clears through the **bank**, and posts to the **general ledger**. The bank is the most independent of the three: the company does not write the bank's records." },
          { table: {
            head: ["What you see", "What it can mean"],
            rows: [
              ["The bank paid **more** than the payment record shows", "An altered check amount, or an error; the classic trace of tampering"],
              ["A recorded payment never clears the bank", "An outstanding check, a voided payment still on the books, or a record that hides something"],
              ["A payment never posts to the ledger, or posts a different amount", "A posting error, or concealment: the ledger is where a theft would be hidden or \"forced\" to balance"],
              ["A payment exceeds its voucher, or is dated before it", "Overpayment (possibly returned to someone), or a bill created after the fact to support a payment"],
            ],
          } },
        ],
      },
      {
        heading: "Harborline: the payment records",
        blocks: [
          { harborline: "**Self-approval:** five payments were entered and approved by the same AP clerk: E227 Alice Bergeron (PAY-2026-0013 on July 5, PAY-2026-0064 on September 13, PAY-2026-0055 on January 8, 2027) and E231 Ken Nakashima (PAY-2026-0049 in March, PAY-2026-0007 on August 1). Three of the five fall between July and mid-September, while the AP supervisor's post was empty." },
          { harborline: "**Split payments:** V1042 Coastal Fuel & Marine Services received five payments between September 14 and 22: 9,850, 9,720, 9,905, 9,640 and 9,880, each **just under the $10,000 approval limit**, totalling 48,995. V1042 is also one half of a look-alike pair from Lesson F3." },
          { harborline: "**Bank and ledger:** PAY-2026-0006 is recorded at 20,084.72, but the bank cleared **20,787.69**, 702.97 more. Four payments (PAY-2026-0001, 0038, 0052, 0116) never cleared the bank. Three never posted to the ledger (0008, 0017, 0058), and two posted the wrong amount (0003, 0004). Three payments exceed their vouchers by 4,132 to 5,898 (PAY-2026-0016, 0093, 0109), and two are dated before their vouchers (0018, 0085)." },
          { watch: "PAY-2026-0116 appears twice: its voucher was paid with no receipt (F3) and the payment never cleared the bank. When one transaction fails several independent tests, it moves up the list." },
        ],
      },
    ],
    standards: [
      ["ACFE Fraud Tree", "Check and payment tampering (forged maker, forged endorsement, altered payee, authorized maker, concealed checks) under fraudulent disbursements"],
      ["CFE exam 2026, section 1", "Fraudulent disbursements (13%): types, prevention and detection of payment tampering and billing schemes"],
      ["AU-C 240", "Fraud risk factors: opportunities from inadequate segregation of duties and approval controls"],
      ["COSO Internal Control framework", "Control activities: segregation of duties and authorization"],
    ],
    check: [
      { q: "The bank cleared a check for $20,787.69, but the payment record says $20,084.72. Which scheme does this most suggest?",
        options: ["Shell company", "Altered check amount", "Personal purchases", "Forged endorsement only"],
        answer: 1,
        why: "The check paid more than was approved and recorded. An altered amount is the classic explanation, though a keying error is possible too; the check image would decide." },
      { q: "One clerk enters and approves a payment. What is the right conclusion?",
        options: ["The clerk committed fraud", "A segregation-of-duties control failed for that payment; find out what the fields mean and whether another control covered it", "Nothing; clerks may approve", "Reverse the payment"],
        answer: 1,
        why: "It is a control failure and an opportunity, not proof. Noesi's own limitation says field meanings and compensating controls need auditor evaluation." },
      { q: "Five payments of 9,640 to 9,905 to one vendor in nine days, with a $10,000 approval limit. What is the concern?",
        options: ["Duplicate vendor", "Splitting to stay under the approval limit", "Late payment", "Nothing: each payment is within the limit"],
        answer: 1,
        why: "Each payment is within the limit, which is exactly the point. Together they are 48,995, well above what one approver could release. The business purpose needs review." },
      { q: "Why is the bank the strongest of the three records (payments, bank, ledger)?",
        options: ["It is the largest file", "It is produced outside the company, so staff cannot easily alter it", "It includes vendor names", "It is always complete"],
        answer: 1,
        why: "Independent, third-party evidence is more reliable than records the client produces itself (AU-C 500). A fraudster can alter the payments file or the ledger far more easily than the bank's records." },
    ],
    task: {
      title: "Test the payment controls yourself",
      intro: "Use `payments.csv`, `bank.csv`, `gl.csv` and `employees.csv` from `case-studies/harborline-marine/data/`.",
      steps: [
        "Filter `payments.csv` for rows where **Created By** equals **Approved By**. Look the clerk up in `employees.csv` and note each payment's date.",
        "Mark which of those dates fall in the June to September supervisor gap.",
        "Sort payments by vendor and date. Find any vendor with three or more payments between 9,000 and 9,999 within ten days.",
        "Match each payment to `bank.csv` by payment number. List payments that never cleared and payments where the bank amount differs from the recorded amount.",
        "For PAY-2026-0006, write the three explanations you would consider and the one document that would decide.",
      ],
      deliver: "A payment-controls worksheet with your exceptions, before you compare them with Noesi's findings.",
    },
    noesi: {
      coverage: "full",
      summary: "This lesson's tests are Noesi's strongest ground: it tests every payment for self-approval, splitting, bank clearing, ledger posting and the document chain. It reports exceptions; it does not decide whether any of them is fraud.",
      does: [
        "`ap.segregation_of_duties` flags payments with the same creator and approver, or no approver.",
        "`ap.split_payment_review` groups payments to one vendor below the approved **split threshold** within a window of days (both are engagement policies you set). Its limit: \"A cluster is advisory and requires business-purpose review.\"",
        "`cash.bank_clearing` compares every payment with the bank (2% tolerance); `gl.payment_posting` checks every payment reached the ledger at the right amount.",
        "`ap.document_chain` checks order, voucher and payment agree in amount and date order. Its limit: \"Document-chain coherence does not authenticate any document.\"",
      ],
      where: ["Workbench → Runs & Findings", "Workbench → Coverage (split policies)", "Studio → Exceptions"],
      doesNot: [
        "It does not examine check images, signatures or endorsements, so it cannot tell an altered check from a keying error.",
        "It does not watch changes to vendor bank accounts.",
        "It never concludes intent; every finding waits for your disposition.",
      ],
      tryIt: "Start with --demo and run all four payment procedures. Compare Noesi's findings with your worksheet, then look for payments that appear in more than one.",
    },
  },
];

/** Planned lessons, shown on the track page until they are written. */
export const FRAUD_COMING: [string, string][] = [
  ["F5", "Following one person"],
  ["F6", "Corruption and kickbacks in purchasing"],
  ["F7", "Following the money"],
  ["F8", "Data analysis for fraud detection"],
  ["F9", "Preventing it next time"],
];
