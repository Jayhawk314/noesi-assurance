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
          { p: "In the late 1940s the criminologist Donald Cressey interviewed people imprisoned for embezzlement (his 1950 dissertation, published in 1953 as *Other People's Money*). He found three conditions present together, now called the **fraud triangle**:" },
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
    video: {
      file: "learn-f1-three-conditions.mp4",
      poster: "learn-f1-three-conditions.jpg",
      title: "Three conditions",
      minutes: 3,
      credits: "Narration: ElevenLabs voice “Guy”. Opening photo: Donald Cressey, UCLA Southern Campus yearbook 1960 (public domain), Wikimedia Commons. Screens: Noesi Learn and the Workbench manual. ACFE figures from Occupational Fraud 2026: A Report to the Nations.",
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
    video: {
      file: "learn-f2-where-could-it-happen.mp4",
      poster: "learn-f2-where-could-it-happen.jpg",
      title: "Where could it happen?",
      minutes: 3,
      credits: "Narration: ElevenLabs voice “Guy”. Screens: Noesi Workbench and Learn on the Harborline demo. Photo: Bruce Emmerling, “A dock in Norfolk, VA” (CC BY-SA 4.0), Wikimedia Commons. SAS No. 151 per the AICPA and the Journal of Accountancy (August 2026).",
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
    },    video: {
      file: "learn-f3-one-letter.mp4",
      poster: "learn-f3-one-letter.jpg",
      title: "One letter",
      minutes: 3,
      credits: "Narration: ElevenLabs voice “Guy”. Screens: Noesi Workbench and Learn on the Harborline demo. Photos from Wikimedia Commons: WestLB (public domain); Jean-Pierre Bazard (CC BY-SA 3.0).",
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
          { harborline: "**Bank and ledger:** PAY-2026-0006 is recorded at 20,084.72, but the bank cleared **20,787.69**, 702.97 more. Four payments (PAY-2026-0001, 0038, 0052, 0116) have no matching row in the bank file. Three never posted to the ledger (0008, 0017, 0058), and two posted the wrong amount (0003, 0004). Three payments exceed their vouchers by 4,132 to 5,898 (PAY-2026-0016, 0093, 0109), and two are dated before their vouchers (0018, 0085)." },
          { watch: "PAY-2026-0116 appears twice: its voucher was paid with no receipt (F3) and the payment has no matching row in the bank file. When one transaction fails several independent tests, it moves up the list." },
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
        "Match each payment to `bank.csv` by payment number. List payments with no bank row and payments where the bank amount differs from the recorded amount.",
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
    video: {
      file: "learn-f4-who-was-checking.mp4",
      poster: "learn-f4-who-was-checking.jpg",
      title: "Who was checking?",
      minutes: 3,
      credits: "Narration: ElevenLabs voice “Guy”. Screens: Noesi Workbench and Learn on the Harborline demo. Photos from Wikimedia Commons: Jernej Furman (CC BY 2.0); Jean-Pierre Bazard (CC BY-SA 3.0); Bruce Emmerling and Jim.henderson (CC BY-SA 4.0); WestLB (public domain).",
    },
  },

  {
    n: 5,
    slug: "fraud-following-one-person",
    title: "Following one person",
    phase: "Fraud",
    question: "When do separate exceptions become a case worth investigating, and what do you do next?",
    minutes: 35,
    objectives: [
      "Explain predication: what is enough to open a fraud examination, and why it is not an accusation",
      "Use the fraud theory approach: form a hypothesis from the data, test it, revise it",
      "Build a transaction timeline for one person across orders, bills, payments, bank and ledger",
      "Name the documentary evidence to request next, and how to keep it reliable (chain of custody)",
    ],
    sections: [
      {
        heading: "From exceptions to a pattern",
        blocks: [
          { p: "Lessons F3 and F4 produced a list of exceptions, each tested separately: a missing voucher here, a self-approved payment there. A list like that is sorted by **test**. An investigator sorts it again by **person**, **vendor** and **date**, because a scheme is run by someone, over time, and it leaves traces in more than one test." },
          { p: "Sorting by person does two things. It shows whether one person's exceptions **fit together** into one way of taking money. It also shows the **comparison group**: what everyone else in the same job did. A pattern only means something against that background." },
          { watch: "Sorting by person is not suspecting that person. You are testing whether the exceptions share a cause. The same sort can clear someone as easily as it points at them." },
        ],
      },
      {
        heading: "Predication and the fraud theory approach",
        blocks: [
          { terms: [
            ["Predication", "The facts that would lead a reasonable, trained and prudent professional to believe a fraud has occurred, is occurring or will occur. It is the threshold for **opening** a fraud examination. It is not proof, and it is never announced as an accusation."],
            ["Fraud theory approach", "Analyze the available data; form a hypothesis of what could have happened (the worst case); test it; revise or reject it as evidence comes in. The hypothesis names a scheme, not a guilty person."],
          ] },
          { p: "Fraud examiners work **from the general to the specific**: documents first, then neutral witnesses, then people who may be involved, and the person suspected last. Documents do not change their story when someone learns they are being looked at." },
          { p: "The two hats from Lesson F1 matter here. A **financial-statement auditor** who finds a possible fraud does not investigate it to a conclusion. Under AU-C 240 they evaluate what it means for the audit, including whether management is involved, and **communicate** it to an appropriate level of management, generally at least one level above the people involved, and to those charged with governance when it is material or involves management. A **fraud examiner**, engaged separately, takes the case from predication to a conclusion." },
        ],
      },
      {
        heading: "Evidence that holds up",
        blocks: [
          { list: [
            "**Documentary evidence** is usually the strongest in fraud cases: it was created at the time, by the process, before anyone knew it would matter.",
            "**Third-party records** (bank statements, cleared check images, vendor statements) are stronger than the client's own records, because the client did not create them (AU-C 500).",
            "**Originals over copies.** Get the original, or a copy whose source you can prove. For an electronic file, record where it came from and a fingerprint of its contents.",
            "**Chain of custody**: a record of who obtained each item, when, from where, and who has held it since. A document nobody can account for can be challenged, however damning it looks.",
            "**Do not alter anything.** Mark up copies, never the evidence itself.",
          ] },
        ],
      },
      {
        heading: "Harborline: one clerk's trail",
        blocks: [
          { harborline: "AP clerk **E227 Alice Bergeron** entered 20 of the year's 123 payments, 427,089.28 in total. Seventeen were approved by someone else. Three were approved by E227 herself, and on those three she **also approved the purchase order** and both entered and approved the voucher. Apart from these three and two approved by E231, every purchase order is approved by one of the four approvers (E102, E108, E115, E119). On these three purchases one clerk controlled every step after the buyer's order." },
          { table: {
            head: ["Purchase", "Order (buyer / approver)", "Receipt", "Voucher (E227 / E227)", "Payment (E227 / E227)", "What does not fit"],
            rows: [
              ["PO-2026-0013, V1006 Gulfstream Propulsion, 21,619.99", "May 31 (E312 / **E227**)", "June 8, full amount", "VCH-2026-0013, June 14", "PAY-2026-0013, July 5; bank July 7", "The payment cites **VCH-2026-9338**, which is not in the voucher file. VCH-2026-0013 itself has **no payment**."],
              ["PO-2026-0064, V1022 Windward Chandlery, 13,303.71", "Aug 16 (E318 / **E227**)", "Sept 3, full amount", "VCH-2026-0064, Sept 6", "PAY-2026-0064, Sept 13; bank Sept 15", "Nothing but the approvals: order, receipt, bill and payment agree."],
              ["PO-2026-0055, V1029 Estuary Environmental Testing, 32,208.42", "Nov 9 (E318 / **E227**)", "Nov 28, full amount", "VCH-2026-0055, Dec 5", "PAY-2026-0055, **Jan 8, 2027**; bank Jan 12", "The payment cites **VCH-2026-9336**, not in the voucher file. VCH-2026-0055 has **no payment**. Paid after year end."],
            ],
          } },
          { harborline: "The shape repeats. Twice, E227 recorded a payment to the right vendor for the right amount, but **against a voucher number that does not exist** in the file, while **no payment in the file cites** the real voucher for the same purchase. In the client's corrected file (Assignment 11), 9338 appears: same order, same amount, dated June 21, a week after 0013, also entered and approved by E227. 9336 never appears. If those real vouchers are still open, each is a bill for a purchase already paid, which could be **paid a second time** or overstate what is owed at year end. The payments file alone cannot say whether they are open; the year-end payables list can." },
          { harborline: "**The comparison group.** E231 Ken Nakashima has the same self-approved chains (orders, vouchers and payments on PO-2026-0007 and 0049), but his payments cite their real vouchers. And one other payment has the phantom-voucher shape: PAY-2026-0100 (45,464.75 to V1038, one of the look-alike vendors) cites VCH-2026-9382, while no payment cites VCH-2026-0100. It was entered by a different clerk, E218, and approved by E102. So the shape is not only about one person." },
          { harborline: "**The rest of E227's trail**, from earlier lessons. She entered VCH-2026-0043, which was paid with no receipt, and PAY-2026-0038, which has no matching row in the bank file. Both were approved by other people. She also entered payments to two look-alike vendors (PAY-2026-0087 to V1042, PAY-2026-0088 to V1039), again approved by others. Two of her three self-approved payments fall between July and mid-September, around the supervisor gap (the brief says only that the new supervisor started in September). PAY-2026-0055 came **after** the new supervisor started." },
          { watch: "Is this predication? Probably enough to justify a closer look at these purchases, and enough for an auditor to communicate the matter. It is not a finding of fraud. Innocent readings exist: a system that re-numbers vouchers on edit, a clerk covering an empty approver role on instruction, a voucher-number typo. The evidence below is what separates them." },
        ],
      },
      {
        heading: "What to request next",
        blocks: [
          { p: "Each request tests one innocent reading against one fraudulent one. Ask in the order an examiner would: records first, people last." },
          { list: [
            "The **vendor's invoices and statements** for PO-2026-0013 and 0055, straight from Gulfstream and Estuary Environmental Testing: how many invoices did they send, and how many payments do they show received?",
            "The **cleared check images** or electronic payment details for CHK-20013 and CHK-20055 from the bank: who was paid, and into which account?",
            "The ERP **audit log** for VCH-2026-0013, 0055 and 9338: who created, edited or deleted voucher records, and when. Where did 9336 come from?",
            "The **approval authority** in force: was E227 authorized to approve purchase orders or payments at any point, and by whom?",
            "Whether **VCH-2026-0013 and 0055 are still open** in the year-end AP subledger, and whether either was paid in 2027.",
          ] },
          { p: "Keep a custody log for each item: what it is, who gave it to you, when, and where the original is. In Noesi, upload files through Sources & Mappings so each one is stored unaltered with its SHA-256 fingerprint." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "Evaluating a possible fraud, considering management involvement, and communicating to management and those charged with governance"],
      ["AU-C 500", "Reliability of audit evidence: external over internal, documents over oral, originals over copies"],
      ["CFE exam 2026, section 2", "Planning and conducting a fraud examination; basic principles of evidence (7%); collecting evidence (11%)"],
      ["ACFE", "Predication and the fraud theory approach, the examiner's starting point for any investigation"],
    ],
    check: [
      { q: "What is predication?",
        options: ["Proof that fraud occurred", "The facts that would lead a reasonable, trained professional to believe fraud may have occurred, which justify opening an examination", "A confession", "A court's finding"],
        answer: 1,
        why: "Predication is the threshold for starting, not the conclusion. An examination without it is a fishing expedition; one that treats it as proof has skipped the work." },
      { q: "In what order does a fraud examiner usually gather evidence?",
        options: ["Interview the suspect first, while memories are fresh", "Documents first, then neutral witnesses, then possible participants, and the suspect last", "Only interviews", "Whatever order the client prefers"],
        answer: 1,
        why: "Working from the general to the specific means the documents are secured before anyone involved knows to change or explain them." },
      { q: "PAY-2026-0013 cites a voucher that is not in the file, while VCH-2026-0013 for the same purchase is unpaid. What is the strongest single document to request first?",
        options: ["A statement from E227", "The vendor's own invoices and statement of payments received", "A management representation letter", "The engagement letter"],
        answer: 1,
        why: "The vendor's records come from outside the company and say how many invoices were sent and how many payments arrived. That separates a numbering problem from a second bill." },
      { q: "An auditor finds these facts during a financial-statement audit. What must the auditor do?",
        options: ["Investigate to a conclusion and name the person", "Evaluate the effect on the audit and communicate the matter to an appropriate level of management, and to governance when required", "Ignore it; fraud is not an audit matter", "Report it to the police"],
        answer: 1,
        why: "AU-C 240 requires evaluating and communicating possible fraud. Concluding whether fraud occurred is not the auditor's role; that is for a separate investigation." },
      { q: "E231 also approved his own orders, vouchers and payments, but his payments cite their real vouchers. How does that help the analysis?",
        options: ["It proves E231 is involved too", "It is a comparison group: self-approval alone happens, but the phantom-voucher shape is what sets E227's two payments apart", "It clears E227", "It is irrelevant"],
        answer: 1,
        why: "A pattern only means something against the background. E231 shows the control failure without the phantom voucher. PAY-2026-0100 shows the phantom voucher without E227. Both keep the hypothesis honest." },
    ],
    task: {
      title: "Build E227's timeline and your evidence request",
      intro: "Use `purchase_orders.csv`, `goods_receipts.csv`, `vouchers.csv`, `payments.csv`, `bank.csv` and `gl.csv` from `case-studies/harborline-marine/data/`, and `revision/vouchers_revised.csv`.",
      steps: [
        "Filter every file for rows where E227 appears as creator or approver. Put them on one sheet, sorted by date, with the file each row came from.",
        "For each purchase E227 approved, line up order, receipt, voucher, payment, bank and ledger, and mark each step that does not fit.",
        "Do the same for E231 and for PAY-2026-0100 as comparison cases. Write one sentence on what E227's trail has that theirs does not.",
        "Write your hypothesis as a scheme, not a person (for example, \"payments against unrecorded voucher numbers leave real vouchers open to be paid again\"), and one innocent explanation.",
        "List five documents you would request, who holds each one, and which explanation each would confirm or rule out.",
      ],
      deliver: "A one-page timeline, a hypothesis with its innocent alternative, and an evidence request list with a custody column.",
    },
    noesi: {
      coverage: "partial",
      summary: "Noesi finds each exception on this trail and keeps the evidence unaltered. It does not gather findings by person, build a timeline, or judge what the pattern means.",
      does: [
        "`ap.segregation_of_duties` flags the three self-approved payments; `ap.payment_voucher_reference` flags PAY-2026-0013 and 0055 as citing vouchers not in the file. Its purpose is stated as \"Determine whether every recorded payment references an observed voucher.\"",
        "Files you upload are stored unaltered and identified by their **SHA-256** fingerprint, and every action is written to a **hash-chained journal**: who did what, and when. That is a chain of custody for the audit's own evidence.",
        "A disposition of **follow up** with a note keeps a finding open while you wait for the vendor or the bank, and the note travels with the finding into the SAD.",
      ],
      where: ["Workbench → Runs & Findings", "Workbench → Sources & Mappings", "Workbench → What Changed (for VCH-2026-9338)"],
      doesNot: [
        "It has no view by employee. You build the person-level timeline yourself.",
        "It does not notice that an unpaid voucher and a payment against a missing voucher share a vendor and amount. That match is yours.",
        "It never concludes intent and never names anyone as a suspect.",
      ],
      tryIt: "Start with --demo, run the eleven procedures, and write down every finding reference that involves E227. Compare the list with your timeline: which of your rows did no procedure flag?",
    },
    video: {
      file: "learn-f5-sort-by-person.mp4",
      poster: "learn-f5-sort-by-person.jpg",
      title: "Sort by person",
      minutes: 3,
      credits: "Narration: ElevenLabs voice “Guy”. Screens: Noesi Workbench and Learn on the Harborline demo; the purchase table is drawn from the case files.",
    },
  },

  {
    n: 6,
    slug: "fraud-corruption-kickbacks",
    title: "Corruption and kickbacks in purchasing",
    phase: "Fraud",
    question: "How do bribes and conflicts of interest show up in payables data, and what can the data not show?",
    minutes: 30,
    objectives: [
      "Describe the four kinds of corruption on the Fraud Tree: conflicts of interest, bribery, illegal gratuities and economic extortion",
      "Explain how a kickback is funded, and why the bribe itself rarely appears in the victim's books",
      "Recognize the red flags of corruption in purchasing",
      "Weigh innocent and fraudulent explanations for an overpayment, and name the evidence that decides",
    ],
    sections: [
      {
        heading: "Corruption: the scheme runs through a deal",
        blocks: [
          { p: "In corruption an employee misuses their influence in a business deal to gain a benefit, for themselves or someone else, against their duty to the employer. The Fraud Tree lists four kinds:" },
          { terms: [
            ["Conflicts of interest", "An employee has an undisclosed interest in a deal, such as part ownership of a supplier, and acts on it. The purchasing version is steering orders, or approving higher prices, for a supplier the employee benefits from."],
            ["Bribery", "Offering or accepting something of value to influence a business decision. In purchasing, the two classic forms are **kickbacks** and **bid rigging**."],
            ["Illegal gratuities", "Something of value given **after** a decision, as a reward, with no agreement beforehand. It is still a problem, because it shapes the next decision."],
            ["Economic extortion", "An employee demands payment from a vendor, for example \"pay me or lose the contract\"."],
          ] },
          { p: "Corruption was in **45%** of the cases in the ACFE's 2026 report, with a median loss of **$150,000**, so it is common as well as costly. It is also often found together with a billing scheme, because the bribe has to be paid for somehow." },
        ],
      },
      {
        heading: "How a kickback is funded",
        blocks: [
          { steps: [
            "A vendor and an insider (a buyer, an approver, a clerk) agree on a scheme.",
            "The vendor's invoices are inflated, or the company pays more than the invoice, or it buys more than it needs.",
            "The company pays. The excess leaves the company's bank account **as an ordinary vendor payment**.",
            "The vendor passes part of the excess to the insider, in cash, a gift, a side payment from its own account, or a job for a relative.",
          ] },
          { p: "Step 4 happens **outside the victim's books**. The company's records can show the overpayment in step 3, never the bribe in step 4. That is why corruption is hard to prove from payables data: the data shows the funding, and the benefit is somewhere else." },
          { watch: "Bid rigging needs bid records: who was invited, who bid, how much, who won. Conflicts of interest need relationship data: employee addresses, bank accounts, ownership disclosures. Harborline's files have **neither**. This lesson can teach the overpayment side; the rest you would need from the client or an investigator." },
        ],
      },
      {
        heading: "Red flags in purchasing",
        blocks: [
          { list: [
            "Payments **above the invoice**, or invoices above the order or the market price, with no explanation.",
            "One buyer or approver who consistently favors one vendor, especially a new or sole-source one.",
            "Contracts split, re-scoped or extended to avoid competitive bidding; bids that come in just under the winner, or always in the same order.",
            "A vendor that is paid faster than the others, or whose problems are always excused.",
            "An employee's lifestyle beyond their salary, or a refusal to take vacation or share duties.",
            "Complaints from other vendors that they cannot win work.",
          ] },
          { p: "Most of these are **not in the accounting data**. They come from inquiries, bid files, tips and observation. That is one reason SAS No. 151 asks auditors to understand the entity's whistleblower program." },
        ],
      },
      {
        heading: "Harborline: three payments 18% too high",
        blocks: [
          { harborline: "Three payments exceed their vouchers, and in each case the order, the receipt and the voucher all agree with each other. The payment is the only record that is higher:" },
          { table: {
            head: ["Payment", "Vendor", "Voucher", "Paid", "Excess", "Entered / approved (payment)", "Buyer (order)"],
            rows: [
              ["PAY-2026-0109, Mar 7", "V1008 Inlet Hydraulics", "22,956.30", "27,088.43", "4,132.13", "E204 / E102", "E318"],
              ["PAY-2026-0016, Apr 24", "V1022 Windward Chandlery", "24,169.53", "28,520.05", "4,350.52", "E231 / E102", "E318"],
              ["PAY-2026-0093, Aug 3", "V1013 Northpoint Trailer Manufacturing", "32,766.47", "38,664.43", "5,897.96", "E204 / E119", "E312"],
            ],
          } },
          { harborline: "Each excess is **18% to the cent**: every payment equals its voucher × 1.18, rounded to cents. The bank file shows the full paid amount clearing, and the ledger posted it, so the records say the money left; the bank statement or check image would confirm who received it. No one person appears on all three: buyer E318 and approver E102 each appear on two, but E318 raised 43 of the year's 123 orders and E102 approved 38 of the 123 payments, so that overlap is weak on its own." },
          { watch: "The same percentage three times, across three vendors and two clerks, is unlikely to be chance. But a **systematic** cause can be innocent as easily as fraudulent: a surcharge or tax rule applied in the payment run, or a system setting. The same 18% could also be an agreed kickback rate. The pattern tells you **where** to look, not what you will find." },
        ],
      },
      {
        heading: "Explanations and the evidence that decides",
        blocks: [
          { table: {
            head: ["Explanation", "Kind", "Evidence that would confirm or rule it out"],
            rows: [
              ["A charge billed separately (freight, surcharge, tax) that never reached the voucher", "Innocent", "The vendor's full invoice and statement; the payment-run settings; other payments to the same vendors"],
              ["A payment-system rule or keying template that adds 18%", "Innocent (a control failure)", "The ERP configuration and change log; whether other clerks' payments show the same uplift"],
              ["The vendor refunded the excess, or holds it as a credit", "Innocent, but a recovery is owed", "A vendor statement showing a credit balance; a refund in the bank records"],
              ["The vendor passes the excess to an insider", "Fraudulent (kickback)", "The vendor's records, obtained by an investigator; employee–vendor relationships; lifestyle and bank evidence, all outside the company's books"],
            ],
          } },
          { p: "Notice how many of the answers come from **the vendor**. A vendor statement is cheap to request and separates the first three explanations quickly. Only if the excess is not with the vendor as a credit, and no rule explains it, does the kickback hypothesis get stronger." },
        ],
      },
    ],
    standards: [
      ["ACFE Fraud Tree", "Corruption: conflicts of interest (purchasing and sales schemes), bribery (invoice kickbacks, bid rigging), illegal gratuities, economic extortion"],
      ["CFE exam 2026, section 1", "Corruption (6%); procurement fraud (8%)"],
      ["ACFE Report to the Nations 2026", "Corruption in 45% of cases, median loss $150,000"],
      ["AU-C 240", "Fraud risk factors and the response to identified misstatements that may be the result of fraud"],
    ],
    check: [
      { q: "A buyer approves a vendor's contract and, a month later, receives expensive tickets from the vendor with no agreement beforehand. Which kind of corruption?",
        options: ["Economic extortion", "Illegal gratuity", "Bid rigging", "Conflict of interest"],
        answer: 1,
        why: "Something of value given after the decision, as a reward, without a prior agreement, is an illegal gratuity. With an agreement beforehand, it would be bribery." },
      { q: "Why is a kickback hard to prove from the victim company's payables data?",
        options: ["Kickbacks are always small", "The bribe is paid by the vendor to the insider outside the company's books; the data shows only the overpayment that funds it", "Payables data is never complete", "Kickbacks are legal"],
        answer: 1,
        why: "The company's records show money going to the vendor. What the vendor does with it afterwards is in the vendor's and the insider's records, which an investigator has to obtain." },
      { q: "Three payments are each 18% above their vouchers, to the cent, across three vendors and two clerks. What is the best first reading?",
        options: ["A kickback ring, proven", "A systematic cause, innocent or not; look for what the three have in common (a rule, a person, a setting) and ask the vendors", "Random keying errors", "Nothing; each is below performance materiality"],
        answer: 1,
        why: "Identical percentages suggest a rule rather than chance. Whether that rule is a system setting or an agreed rate is exactly what the evidence has to decide." },
      { q: "Which Harborline data would you need to test for bid rigging?",
        options: ["The payments file", "Bid records: invitations, bids received, amounts and winners; Harborline's files have none", "The bank file", "The general ledger"],
        answer: 1,
        why: "Bid rigging shows in the bidding, not in the payment. Without bid records the test cannot be done from this data, and the workpaper should say so." },
      { q: "What is the cheapest, fastest request that separates the innocent explanations for the 18% excess?",
        options: ["Interview the buyers", "Vendor statements for the three vendors, showing invoices, payments received and any credit balance", "A forensic image of every laptop", "A new engagement letter"],
        answer: 1,
        why: "A vendor statement shows whether the vendor billed a separate charge, holds the excess as a credit, or refunded it. It is external evidence, and it takes one letter per vendor." },
    ],
    task: {
      title: "Two innocent and two fraudulent explanations for PAY-2026-0016",
      intro: "Use `payments.csv`, `vouchers.csv`, `purchase_orders.csv`, `goods_receipts.csv` and `bank.csv` from `case-studies/harborline-marine/data/`.",
      steps: [
        "For PAY-2026-0016, line up the order, receipt, voucher, payment and bank amounts. Compute the excess and its percentage of the voucher.",
        "Find every other payment in the file where the payment exceeds its voucher. Compute the same percentage for each. What do they have in common, and what do they not?",
        "List every payment to V1022 Windward Chandlery. Does the vendor appear elsewhere in this track (Lesson F5)? Does that change your view, and why or why not?",
        "Write two innocent and two fraudulent explanations for PAY-2026-0016's excess.",
        "For each explanation, name the one document that would confirm or rule it out, and who holds it: the client, the vendor, the bank, or only an investigator.",
      ],
      deliver: "A one-page analysis: the three overpayments side by side, four explanations, and the evidence for each.",
    },
    noesi: {
      coverage: "partial",
      summary: "Noesi finds the overpayments that could fund a kickback. It has no test for bid rigging or conflicts of interest, because it has no bid or relationship data to test.",
      does: [
        "`ap.document_chain` flags each payment that exceeds its voucher, with the amounts. Its stated limit: \"Document-chain coherence does not authenticate any document.\"",
        "`cash.bank_clearing` and `gl.payment_posting` show the overpaid amounts clearing in the bank file and posted in the ledger, so the excess is more than a keying error on one record. They do not show who received the money.",
      ],
      where: ["Workbench → Runs & Findings", "Workbench → 📖 manual, chapter 5"],
      doesNot: [
        "It states each excess as a percentage of its voucher, but it does not notice that three findings share the same rate. Connecting them is your analysis.",
        "It has **no bid-rigging, conflict-of-interest or vendor-pricing test**, and no employee–vendor relationship data.",
        "It cannot see anything outside the company's books, which is where a bribe is paid.",
      ],
      tryIt: "Start with --demo, run ap.document_chain, and filter its findings to the overpayments. Add the percentage column yourself in Excel and compare.",
    },
    video: {
      file: "learn-f6-eighteen-percent.mp4",
      poster: "learn-f6-eighteen-percent.jpg",
      title: "Eighteen percent",
      minutes: 3,
      credits: "Narration: ElevenLabs voice “Guy”. Screens: Noesi Workbench and Learn on the Harborline demo; the overpayment table is computed from the case files. ACFE figures from Occupational Fraud 2026: A Report to the Nations.",
    },
  },

  {
    n: 7,
    slug: "fraud-following-the-money",
    title: "Following the money",
    phase: "Fraud",
    question: "Money left and came back. How do you trace it, and what evidence tells a scheme from a normal transaction?",
    minutes: 30,
    objectives: [
      "Explain what tracing funds means and which records it relies on",
      "Describe a round trip, the three stages of money laundering, and why a company might send money out and back",
      "Trace Harborline's 48,500 round trip and test whether the extract it sits in can be trusted",
      "List the evidence that would confirm or dismiss round-tripping, and say which hat, auditor or fraud examiner, each step belongs to",
    ],
    sections: [
      {
        heading: "Tracing: follow each dollar to its next hop",
        blocks: [
          { p: "**Tracing** means following money from where it started to where it ended up, one transfer at a time, using records that show each hop: bank statements, wire and ACH details, cancelled checks, and the ledger entries that recorded them. Each hop answers three questions: **who sent it, who received it, and why**." },
          { p: "The strongest records come from outside the company. A bank statement was produced by the bank, not by the people you may be looking at, so it is better evidence than a spreadsheet the client prepared (AU-C 500 ranks evidence by source for this reason)." },
          { watch: "Keep the two hats apart. An **auditor** asks whether a transaction is recorded, presented and disclosed properly, and whether it points to a material misstatement. A **fraud examiner** follows the money to a conclusion about a specific allegation, and needs predication (Lesson F5) before starting. Most of this lesson is the auditor's work; section 4 says where the examiner would take over." },
        ],
      },
      {
        heading: "Round trips and layering",
        blocks: [
          { p: "A **round trip** is money that leaves an entity and comes back to it, usually through one or more intermediaries, so that it looks like something else on the way back. Money laundering is usually described in three stages, and round trips belong to the middle one:" },
          { terms: [
            ["Placement", "Getting money into the financial system, for example depositing cash."],
            ["Layering", "Moving it through transfers and entities to break the link with its source. Each hop makes the trail longer."],
            ["Integration", "Bringing it back looking legitimate: a loan, a sale, a fee, a refund."],
          ] },
          { p: "A company can send money out and back for several reasons, and only some of them are wrong:" },
          { list: [
            "**Inflating revenue**: the money comes back labeled as a customer payment, so sales look higher than they are. That is financial statement fraud.",
            "**Disguising financing**: a loan dressed up as an operating receipt, or cash parked outside the company over a reporting date to flatter a ratio.",
            "**Taking money out**: an insider owns an intermediary and keeps part of each trip; the full amount returns only on paper.",
            "**Legitimate**: a refund of a prepayment, a genuine cash-management transfer between related companies, a reversal of a payment made in error.",
          ] },
          { p: "The pattern is identical in all four. What separates them is who the intermediaries are, what the paperwork says, and how each leg was recorded." },
        ],
      },
      {
        heading: "Harborline's 48,500",
        blocks: [
          { p: "The counterparty value-flow extract (`value_flows.csv`, 51 rows) holds one closed loop:" },
          { table: {
            head: ["Flow", "From", "To", "Amount", "Date", "Label"],
            rows: [
              ["VF-0049", "Harborline Marine Group", "Bayview Advisory Partners", "48,500.00", "2026-11-03", "consulting"],
              ["VF-0050", "Bayview Advisory Partners", "Meridian Holdings LC", "48,500.00", "2026-11-05", "transfer"],
              ["VF-0051", "Meridian Holdings LC", "Harborline Marine Group", "48,500.00", "2026-11-07", "transfer"],
            ],
          } },
          { p: "Same amount, three hops, four days, and back where it started. Now look for it in the books you were given: **Bayview and Meridian are not in the vendor master, and the 48,500 is not in the payments file, the bank feed for the operating account, or the payables ledger.** Whatever paid the \"consulting\" fee did not run through accounts payable or through the account you can see." },
          { harborline: "The brief says the controller prepared this extract last year at the lender's request, and that there is **no documentation of its completeness**. Try to tie it to the books: none of its 48 ordinary disbursements matches an amount in `payments.csv`. An extract that does not reconcile to the records it claims to summarize is **information produced by the entity** that you cannot yet rely on (AU-C 500). That is a finding in itself, before you ask what the loop means." },
        ],
      },
      {
        heading: "What evidence separates the explanations",
        blocks: [
          { p: "Work from records the client keeps anyway, and from sources outside it:" },
          { steps: [
            "**Find the account.** Ask which bank account paid Bayview and which received Meridian's transfer, and get those bank statements directly from the bank.",
            "**Find the entries.** How was each leg recorded in Harborline's general ledger? A consulting expense going out and revenue or a customer receipt coming back points one way; a loan or a refund points another.",
            "**Test the business purpose.** Ask for the consulting agreement, the invoice, the deliverable and the approval. A 48,500 fee for work nobody can show is a red flag on its own.",
            "**Find out who owns Bayview and Meridian.** Public business registries, the vendor file, and management's list of related parties. If either is connected to an owner or employee, the round trip is a **related-party transaction** that must be identified and disclosed (AU-C 550).",
            "**Weigh it as an unusual transaction.** AU-C 240 asks the auditor to evaluate whether a significant transaction outside the normal course of business has a business rationale, or suggests fraudulent reporting or theft.",
          ] },
          { watch: "Do not contact Bayview or Meridian, and do not accuse anyone. The auditor's route is inquiry of management, then those charged with governance if the answers do not hold up. If fraud is suspected, a fraud examiner, with counsel, takes over the tracing and the interviews." },
        ],
      },
      {
        heading: "What a detected loop does and does not prove",
        blocks: [
          { p: "Noesi's round-trip screen looks for value that returns to where it started through a chain of flows whose amounts agree within **2%** and whose dates fall within **30 days**, in up to four hops. On Harborline it finds this loop and only this loop." },
          { list: [
            "**It proves the pattern exists in the extract**, with the three rows and their fingerprints attached.",
            "**It does not prove the extract is complete.** A loop through a flow that was left out is invisible. The absence of other loops proves nothing.",
            "**It does not prove intent.** In the procedure's own words: \"A coherent cycle is a lead, not an allegation of fraud.\"",
            "**Labels matter.** The screen skips loops labeled as reversals, corrections or intercompany settlements. Harborline's extract has no such label column, so nothing was skipped; in another client's data, ask who assigned the labels.",
          ] },
        ],
      },
    ],
    standards: [
      ["AU-C 500", "Audit evidence: reliability by source; testing information produced by the entity for accuracy and completeness"],
      ["AU-C 550", "Related parties: identifying them, and evaluating and disclosing related-party transactions"],
      ["AU-C 240", "Significant unusual transactions and their business rationale; fraud risk factors"],
      ["Money laundering stages", "Placement, layering, integration (the standard description used by regulators and the CFE exam)"],
    ],
    check: [
      { q: "Which record is the strongest evidence of where Harborline's 48,500 went?",
        options: ["The value-flow extract the controller prepared", "A bank statement obtained directly from the bank", "An email from the controller explaining it", "The consulting fee's description in the extract"],
        answer: 1,
        why: "A bank statement comes from a third party and was obtained by the auditor, so the client could not shape it. The extract and the email are both produced by the people whose work is being tested." },
      { q: "Money moves through two shell companies before returning to the company as a \"customer payment\". Which laundering stage is the chain of transfers?",
        options: ["Placement", "Layering", "Integration", "Structuring"],
        answer: 1,
        why: "Layering is the chain of moves that separates the money from its source. The return as a customer payment is integration." },
      { q: "Noesi finds no other round trips in Harborline's extract. What can you conclude?",
        options: ["There are no other round trips", "Only that the extract, as given, contains no other loop within 2% and 30 days", "That the extract is complete", "That the 48,500 loop is fraud"],
        answer: 1,
        why: "The screen is bounded by the population it was given and its tolerances. The extract's completeness is undocumented, so silence proves nothing beyond it." },
      { q: "You learn that a Harborline director owns Meridian Holdings LC. What does that make the round trip, at a minimum?",
        options: ["Proof of fraud", "A related-party transaction to evaluate and disclose", "Irrelevant, since the money came back", "A cutoff error"],
        answer: 1,
        why: "Ownership by a director makes it a related-party transaction (AU-C 550), whatever its purpose. Whether it is also fraud depends on the rest of the evidence." },
    ],
    task: {
      title: "Trace the loop and test the extract",
      intro: "Use `value_flows.csv`, `payments.csv`, `bank.csv`, `vendors.csv` and the engagement brief.",
      steps: [
        "Draw the Bayview–Meridian loop: three boxes, three arrows, with amount, date and label on each arrow.",
        "Search the vendor master, the payments, the bank feed and the payables ledger for Bayview, Meridian and 48,500. Record where each appears, and where it does not.",
        "Try to tie the extract's 48 ordinary disbursements to `payments.csv` by amount. Write two sentences on what the result means for relying on the extract.",
        "List the records you would request to confirm or dismiss round-tripping, and mark each as auditor's work or fraud examiner's work.",
      ],
      deliver: "A one-page trace: the diagram, a table of where the money appears, and your evidence request list.",
    },
    noesi: {
      coverage: "partial",
      summary: "Noesi finds the loop and keeps the proof of where it came from. Tracing it through bank records, entries and ownership is your work.",
      does: [
        "`forensic.closed_value_flow` screens the whole extract for money that returns to its source (amounts within 2%, dates within 30 days, up to four hops) and reports the Bayview–Meridian loop with its three rows and their SHA-256 fingerprints.",
        "Each finding states its limit: \"A coherent cycle is a lead, not an allegation of fraud.\"",
        "The mapping refuses the extract's missing `flow_type` field instead of guessing, so no loop is skipped as \"legitimate\" on an assumed label.",
      ],
      where: ["Workbench → Runs & Findings (forensic.closed_value_flow)", "Workbench → Sources & Mappings (the Value_flows refusal)"],
      doesNot: [
        "It does not test whether the extract is complete or reconcile it to payments, the bank or the ledger. That tie-out is yours.",
        "It does not look up who owns a counterparty, and it has no related-party list.",
        "It does not follow money outside the company's own records, and it never concludes intent.",
      ],
      tryIt: "Start with --demo, run forensic.closed_value_flow, open the finding and follow its three source rows back to value_flows.csv.",
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
      "Explain why testing the whole population beats sampling for fraud detection",
      "Read a set of findings: overlaps, tolerances, silence and refusals",
      "Run a first-digit (Benford) test and explain when it is and isn't reliable",
      "Say what data analysis can find and what it can never find",
    ],
    sections: [
      {
        heading: "Test everything, not a sample",
        blocks: [
          { p: "A sample is built to estimate an error rate. Fraud is usually rare and deliberate: one self-approved payment in a hundred, placed where a sample is unlikely to land. When the data is available, **testing the whole population** finds every instance of a pattern, and the ACFE's 2026 report associates **proactive data monitoring** with lower losses and faster detection." },
          { p: "Each test is a rule applied to every row: creator equals approver, payment above voucher, vendor names nearly identical, amounts just under a limit. The skill is not running the rules. It is reading what comes back." },
        ],
      },
      {
        heading: "Reading the results",
        blocks: [
          { harborline: "On Harborline, Noesi's 11 procedures return **52 findings** for **40 planted exceptions**. The numbers differ because one problem can trip several tests: VCH-2026-0041 is flagged three times, by the voucher-to-PO check, the three-way match and the document chain." },
          { terms: [
            ["Overlap", "Several findings, one underlying problem. Group them before counting or reporting, or you will overstate the issues and waste review time."],
            ["Tolerance", "Every comparison has one. Noesi's bank match allows 2%, so PAY-2026-0025 (paid 16,625.15, cleared the bank at 16,774.78, a 0.9% difference) is **silent by design**. Silence means \"within tolerance\", not \"nothing there\"."],
            ["Refusal", "A test that cannot run on the data says so, instead of passing quietly. Harborline's purchase orders have no approval timestamps, so approval sequence cannot be tested. A refusal is a scope limit to record, not a clean result."],
            ["False positive", "A finding with an innocent explanation. Every finding needs a disposition from a person; volume without review is noise."],
          ] },
          { watch: "Before you trust a clean result, ask three questions: was the population complete, what tolerance applied, and did anything refuse to run?" },
        ],
      },
      {
        heading: "Benford's law, and its limits",
        blocks: [
          { p: "In many naturally occurring sets of amounts, the first digit is **1** about **30%** of the time, **2** about **18%**, falling to **9** at under **5%**. Invented numbers tend to be spread too evenly, or bunch just under limits. Comparing actual first digits with that curve is **Benford analysis**." },
          { list: [
            "It needs **many** amounts (hundreds at least, ideally thousands) spanning several orders of magnitude.",
            "It fails on amounts with built-in limits or fixed prices: a set of $9,800 invoices is not natural.",
            "A deviation is a **reason to look**, never proof.",
          ] },
          { harborline: "Harborline has **123 payments**. That is too few for a reliable Benford result: random variation alone can move a digit's share by several points. Running it anyway, and saying why the result can't carry weight, is the exercise." },
        ],
      },
      {
        heading: "What data can't find",
        blocks: [
          { p: "Data analysis sees only what was recorded, in the files you were given. It cannot see a bribe paid in cash outside the books (F6), money moved through an account you don't have (F7), a forged signature, or a conversation. It also cannot tell an error from fraud: that takes documents and people." },
          { p: "So analysis finds **leads**. Tips, still the most common way fraud is detected in the ACFE's 2026 report (43% of cases), find what data doesn't. A good program uses both." },
        ],
      },
    ],
    standards: [
      ["AU-C 520", "Analytical procedures: expectations, thresholds for investigating differences"],
      ["AU-C 240", "Responses to fraud risks, including unpredictability and testing of populations"],
      ["ACFE Report to the Nations 2026", "Proactive data monitoring associated with lower losses; tips the most common detection method (43%)"],
    ],
    check: [
      { q: "A procedure reports no findings. What is the right reading?",
        options: ["The area is clean", "No differences beyond the tolerance, in the population supplied, for tests that ran", "The procedure failed", "The population was complete"],
        answer: 1,
        why: "Silence is bounded by the tolerance, the completeness of the data, and whether the test could run at all." },
      { q: "Why do 52 findings correspond to only 40 planted exceptions?",
        options: ["The tool has 12 bugs", "One problem can trip several tests, so findings overlap", "12 exceptions were duplicated in the data", "Tolerances double-count"],
        answer: 1,
        why: "VCH-2026-0041, for one, is flagged by three procedures for one underlying problem. Group overlaps before counting." },
      { q: "Why is a Benford test on Harborline's 123 payments weak evidence?",
        options: ["Benford only works on revenue", "Too few amounts: random variation can swamp the expected pattern", "Payments never follow Benford", "The amounts are in dollars"],
        answer: 1,
        why: "Benford needs a large, natural population. With 123 amounts a few rows can shift a digit's share noticeably." },
    ],
    task: {
      title: "Read the results, and run Benford by hand",
      intro: "Use `payments.csv` and a fresh --demo run.",
      steps: [
        "In a spreadsheet, take the first digit of every payment amount (`=LEFT(TEXT(amount,\"0\"),1)`), count each digit, and compare with 30.1%, 17.6%, 12.5%, 9.7%, 7.9%, 6.7%, 5.8%, 5.1%, 4.6%.",
        "Write two sentences on why the result cannot carry weight with 123 rows.",
        "From the demo run, pick one payment that appears in three or more findings, and explain the single problem behind them.",
        "Find PAY-2026-0025 in the bank feed, compute its difference, and explain why no procedure flagged it.",
      ],
      deliver: "A one-page note: the Benford table with your caveat, one overlap explained, and the silent payment explained.",
    },
    noesi: {
      coverage: "partial",
      summary: "Noesi runs every payables test on the whole population and tells you its tolerances and refusals. It has no Benford test, and it cannot see beyond the files.",
      does: [
        "Eleven full-population procedures, each with a stated tolerance and limitation; coverage shows what can and cannot run on the loaded data.",
        "Refuses fields it cannot map instead of guessing, and records the refusal.",
        "Every finding waits for a person's disposition.",
      ],
      where: ["Workbench → Coverage", "Workbench → Runs & Findings", "Workbench → Sources & Mappings (refusals)"],
      doesNot: [
        "It has no Benford or first-digit test; do it in a spreadsheet.",
        "It does not group overlapping findings into one problem. That is your analysis.",
        "It sees only the files you load, and never concludes intent.",
      ],
      tryIt: "Start with --demo, run all procedures, and open Coverage: note which procedures ran, and which fields were refused.",
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
      "Match each Harborline scheme to the control that failed or was missing",
      "Tell preventive from detective controls",
      "Classify control deficiencies and know who receives them in writing (AU-C 265)",
      "Draft the points of a control-deficiency letter",
    ],
    sections: [
      {
        heading: "Every scheme passed through a gap",
        blocks: [
          { p: "Fraud needs opportunity (F1), and opportunity is a missing or failed control. Looking back at each scheme and naming the control that would have stopped it is how an organization turns a finding into prevention." },
          { table: {
            head: ["Scheme (lesson)", "What happened", "Control that would have stopped it"],
            rows: [
              ["Look-alike vendors (F3)", "Vendor pairs sharing a tax ID and remit city", "Vendor master review: independent set-up, tax-ID and address matching"],
              ["Duplicate invoice (F3)", "VCH-2026-9338 re-bills PO-2026-0013", "Duplicate-invoice check before payment"],
              ["Self-approved payments (F4, F5)", "Creator also approved, some in the supervisor gap", "Independent payment approval, enforced by the system"],
              ["Payments just under $10,000 (F4)", "V1042, 9,640–9,905, clustered in September", "Approval-limit monitoring across payments to one vendor"],
              ["Overpayments at 18% (F6)", "Paid 18% above agreed vouchers", "Three-way match with payment blocked on mismatch"],
              ["Round trip via Bayview (F7)", "48,500 out and back outside AP", "All disbursements through AP; related-party register"],
            ],
          } },
        ],
      },
      {
        heading: "Preventive and detective",
        blocks: [
          { terms: [
            ["Preventive", "Stops it before it happens: a second approver, a system block on a mismatch."],
            ["Detective", "Finds it afterwards: a monthly review of payments under the limit, a data-monitoring report."],
          ] },
          { p: "Good programs combine both. Detective controls work only if someone acts on what they find, and people change their behavior when they know monitoring exists." },
          { watch: "A control on paper that nobody performs prevents nothing. Harborline had an approval limit; during the supervisor gap it was \"handled informally\"." },
        ],
      },
      {
        heading: "Telling management and governance",
        blocks: [
          { p: "AU-C 265 requires the auditor to communicate **in writing** to management and those charged with governance the **significant deficiencies** and **material weaknesses** found in internal control. A material weakness is a deficiency, or combination, where there is a reasonable possibility a material misstatement won't be prevented or detected on time. A significant deficiency is less severe but still merits governance's attention." },
          { p: "The letter describes the deficiency and its possible effects. It does not accuse anyone. Suspected fraud is a separate communication under AU-C 240." },
          { harborline: "The eleven weeks without an approver, combined with self-approved payments that went out in that period, is a strong candidate for a significant deficiency or material weakness in payment authorization." },
        ],
      },
    ],
    standards: [
      ["AU-C 265", "Communicating internal control related matters: significant deficiencies and material weaknesses, in writing"],
      ["AU-C 240", "Communicating suspected fraud to management and governance"],
      ["COSO Internal Control framework", "Control activities, monitoring, and the preventive/detective distinction"],
    ],
    check: [
      { q: "Which control would most directly have stopped the self-approved payments?",
        options: ["A monthly bank reconciliation", "System-enforced independent payment approval", "A vendor master review", "Benford analysis"],
        answer: 1,
        why: "Creator equals approver is prevented by a system rule requiring a different approver." },
      { q: "A monthly report of payments just under the approval limit is…",
        options: ["preventive", "detective", "corrective only", "not a control"],
        answer: 1,
        why: "It finds clusters after payment. It works only if someone reviews and acts on it." },
      { q: "Under AU-C 265, significant deficiencies go to…",
        options: ["only the lender", "management and those charged with governance, in writing", "the regulator", "no one unless material"],
        answer: 1,
        why: "Both significant deficiencies and material weaknesses are communicated in writing to management and governance." },
    ],
    task: {
      title: "Draft the control-deficiency points",
      intro: "Use lessons F3–F7 and the engagement brief.",
      steps: [
        "For each scheme in the table, name the failed control, and mark it preventive or detective.",
        "Classify each as a deficiency, significant deficiency or material weakness, with one sentence of reasoning.",
        "Write the letter points: condition, possible effect, recommendation. No names, no accusations.",
      ],
      deliver: "A one-page draft of control-deficiency letter points.",
    },
    noesi: {
      coverage: "partial",
      summary: "Noesi supplies the evidence behind each deficiency. Classifying deficiencies and writing the letter is yours.",
      does: [
        "Findings, dispositions and the summary of audit differences give each deficiency its evidence and amounts.",
        "The signed, locked workpaper keeps what you concluded and when.",
      ],
      where: ["Workbench → Runs & Findings", "Workbench → SAD & Completion"],
      doesNot: [
        "It does not classify control deficiencies or write the management letter.",
        "It does not design or monitor the client's controls.",
      ],
    },
  },
];

/** Planned lessons, shown on the track page until they are written. */
export const FRAUD_COMING: [string, string][] = [];
