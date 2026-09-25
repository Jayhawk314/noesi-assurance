// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Lessons 1–4: planning the audit. Sources: docs/learn/CURRICULUM.md. */

import { Lesson } from "./types";

export const PLANNING: Lesson[] = [
  {
    n: 1,
    slug: "acceptance",
    title: "Client acceptance and the terms of the engagement",
    phase: "Planning",
    question: "Should we do this audit at all — and on what terms?",
    minutes: 20,
    objectives: [
      "Explain why a firm decides whether to accept or continue a client before any audit work",
      "List what acceptance considers: integrity, independence, competence, and risk",
      "Describe what the engagement letter must establish",
      "Know what changes when a firm replaces another auditor",
    ],
    sections: [
      {
        heading: "Why the audit starts with a decision, not a test",
        blocks: [
          { p: "An audit is a firm putting its name on someone else's numbers. Before any testing, the firm decides whether it **can** and **should** take that risk. A bad client — one whose management lacks integrity, or whose affairs the firm cannot competently audit — is a risk no amount of fieldwork repairs." },
          { p: "U.S. firms now run this decision inside a **quality management system**. SQMS No. 1 (firm level) and SAS No. 146 (the engagement partner's responsibilities, in AU-C 220) apply to engagements for periods beginning on or after December 15, 2025. Acceptance and continuance of clients is one of the areas every firm must set quality objectives for." },
        ],
      },
      {
        heading: "What acceptance and continuance weigh",
        blocks: [
          { terms: [
            ["Integrity of management", "Is there reason to believe management would mislead the auditor, override controls, or pressure the firm? Prior disputes, regulatory trouble and sudden auditor changes are signals."],
            ["Independence and ethics", "Does anyone on the team, or the firm, hold a financial interest, a family tie, or a non-audit service that impairs independence in fact or appearance?"],
            ["Competence and capacity", "Does the firm have people who know the industry and the time to staff the job before the deadline?"],
            ["Engagement risk", "Who relies on the statements (lenders, investors)? How exposed is the firm if the audit fails?"],
          ] },
          { p: "For an existing client this is repeated every year as **continuance**. It is not a formality: circumstances change, and so does the risk." },
        ],
      },
      {
        heading: "Changing auditors",
        blocks: [
          { p: "If another firm audited last year, the new (successor) auditor makes inquiries of the predecessor — with the client's permission — about management integrity, disagreements, and the reasons for the change. AU-C 510 then requires evidence that the **opening balances** carry no material misstatement into the current year." },
          { watch: "A client that refuses permission to talk to the predecessor has told you something important. Treat it as a reason to decline, not a paperwork gap." },
        ],
      },
      {
        heading: "The engagement letter",
        blocks: [
          { p: "AU-C 210 requires agreement on the **terms of the engagement**, normally in an engagement letter, before work begins. It establishes the preconditions for an audit:" },
          { list: [
            "the objective and scope of the audit and the financial reporting framework (for example U.S. GAAP);",
            "**management's responsibilities** — for the financial statements, for internal control, and for giving the auditor access to all information and people;",
            "the auditor's responsibilities and the inherent limitations of an audit (reasonable, not absolute, assurance);",
            "the expected form of the report, and practical matters such as timing and fees.",
          ] },
          { p: "If management will not accept its responsibilities, the preconditions for an audit are not present and the firm should not accept." },
        ],
      },
      {
        heading: "Harborline, as a continuing client",
        blocks: [
          { harborline: "This is Harborline's **third annual audit**; the prior two opinions were unmodified. Its lender raised the credit line to $6 million and requires audited statements **within 120 days** of year end plus a current ratio of at least 1.25. That covenant is the reason the audit exists — and a reason for care: a covenant is an incentive to present results favourably." },
          { p: "Continuance questions worth asking this year: the AP supervisor left and was not replaced for eleven weeks; approval limits were 'handled informally'. None of that makes Harborline unauditable — but it changes the risk the firm is accepting, and the plan in Lessons 2–4 must answer it." },
        ],
      },
    ],
    standards: [
      ["SQMS 1 / SAS 146 (AU-C 220)", "Firm quality management; the engagement partner's responsibility for quality, including acceptance and continuance"],
      ["AU-C 210", "Terms of engagement and the preconditions for an audit"],
      ["AU-C 510", "Opening balances in initial audits; predecessor–successor communication"],
    ],
    check: [
      { q: "Management refuses to acknowledge responsibility for internal control in the engagement letter. What follows?",
        options: ["Accept, but add more substantive testing", "The preconditions for an audit are not present; the firm should not accept", "Accept and disclose it in the report", "Ask the lender to sign instead"],
        answer: 1,
        why: "AU-C 210 makes management's acknowledgement of its responsibilities a precondition. Extra testing cannot substitute for it." },
      { q: "Why repeat the acceptance decision every year for a continuing client?",
        options: ["Standards require a new engagement letter format each year", "Circumstances and risk change — integrity concerns, independence, or capacity can arise after the first year", "It is only required for public companies", "To renegotiate the fee"],
        answer: 1,
        why: "Continuance is a fresh judgment on current facts. Harborline's supervisor vacancy is exactly the kind of new fact it considers." },
      { q: "A successor auditor's inquiries of the predecessor require…",
        options: ["nothing — they are automatic", "the client's permission", "the lender's permission", "a court order"],
        answer: 1,
        why: "The predecessor owes the client confidentiality; the client must authorize the communication. A refusal is itself a warning sign." },
    ],
    task: {
      title: "Write the continuance memo",
      intro: "Using only the engagement brief (case-studies/harborline-marine/docs/01-engagement-brief.md):",
      steps: [
        "List every fact in the brief that bears on management integrity, independence, competence or engagement risk.",
        "For each, say whether it argues for continuing, against, or for continuing with specific responses.",
        "Conclude in two sentences: continue or not, and what the plan must address because of it.",
      ],
      deliver: "A one-page continuance memo.",
    },
    noesi: {
      coverage: "partial",
      summary: "Noesi records who is accountable for the engagement and enforces the separation that quality management depends on. The acceptance decision itself stays with you.",
      does: [
        "**Creating an engagement** (client name and period end) makes the person who creates it its **partner**.",
        "The partner assigns a **preparer** and a **reviewer** on the Team tab; readiness blocks the lock until both are assigned (`TEAM_ASSIGNMENTS_INCOMPLETE`).",
        "Every action is written to a **hash-chained journal** — who did what, in which chair, and when — which is the attributable trail quality management expects.",
      ],
      where: ["Workbench → engagement list (create)", "Workbench → Team tab (partner chair)", "Studio → top bar, 'Sitting as' shows your chair"],
      doesNot: [
        "It has no acceptance or independence checklist and records no engagement letter. The production-readiness list names this as a gap.",
        "On one laptop, chairs are role-play: the same person sits in each. The tool says so rather than pretending otherwise.",
      ],
      tryIt: "Start with --demo, open the Workbench Team tab, and see the three chairs the case assigns.",
    },
  },

  {
    n: 2,
    slug: "understanding-and-analytics",
    title: "Understanding the entity and preliminary analytics",
    phase: "Planning",
    question: "Where could these financial statements be wrong — and why?",
    minutes: 30,
    objectives: [
      "Describe the risk-assessment procedures AU-C 315 requires",
      "Use preliminary analytical procedures to find unexpected relationships",
      "Separate inherent risk from control risk, as SAS 145 requires",
      "Recognize the two fraud risks presumed in every audit",
    ],
    sections: [
      {
        heading: "Risk assessment comes before testing",
        blocks: [
          { p: "You cannot decide what to test until you know where misstatement could hide. AU-C 315 — rewritten by **SAS 145**, effective for periods ending on or after December 15, 2023 — requires risk-assessment procedures: **inquiry** of management and others, **analytical procedures**, and **observation and inspection**. Their output is the set of **risks of material misstatement (RMM)** at the financial-statement level and at the **assertion** level." },
          { p: "You build an understanding of the entity and its environment: its industry and regulation, how it makes money, its financing (Harborline's covenant), its accounting policies, and its **system of internal control**." },
        ],
      },
      {
        heading: "Assertions — what exactly could be wrong",
        blocks: [
          { p: "Management's statements carry implicit claims called **assertions**. Risks and procedures are both expressed against them." },
          { table: { head: ["Transactions (e.g. purchases)", "Balances (e.g. accounts payable)"], rows: [
            ["Occurrence — it really happened", "Existence — it really exists"],
            ["Completeness — nothing left out", "Completeness — nothing left out"],
            ["Accuracy — right amounts", "Accuracy, valuation and allocation"],
            ["Cutoff — right period", "Rights and obligations"],
            ["Classification", "Classification"],
            ["Presentation", "Presentation"],
          ] } },
          { p: "For a liability like accounts payable the dangerous direction is usually **understatement** — so **completeness** is the key assertion. For assets and revenue, **existence/occurrence** usually is." },
        ],
      },
      {
        heading: "Preliminary analytical procedures",
        blocks: [
          { p: "Analytics compare recorded amounts with an **expectation** — prior year, budget, industry, or a relationship between accounts. At planning they are a searchlight, not evidence: they point to accounts that moved unexpectedly or failed to move when they should have." },
          { steps: [
            "Form the expectation first (for example: AP should rise roughly with purchases).",
            "Compare to the recorded figure.",
            "Where the difference is significant, ask why — and record it as a possible risk.",
          ] },
          { p: "Useful ratios for a payables cycle: **days payable outstanding** (AP ÷ cost of sales × 365), AP to purchases, and the current ratio. A current ratio sitting just above a covenant floor deserves a second look." },
        ],
      },
      {
        heading: "Inherent risk and control risk, separately",
        blocks: [
          { p: "SAS 145 requires you to assess **inherent risk** (how susceptible an assertion is to misstatement before controls — complexity, judgment, change, incentive) and **control risk** (whether controls would prevent or detect it) **separately**. If you do not plan to test controls, control risk is at the maximum and the RMM equals the inherent-risk assessment." },
          { p: "It also adds a **stand-back**: after identifying risks, look again at every material class of transactions, balance and disclosure that you did not flag, and ask whether that conclusion is still right." },
        ],
      },
      {
        heading: "Fraud is presumed in two places",
        blocks: [
          { p: "AU-C 240 presumes a fraud risk in **revenue recognition** (you may overcome it only with documented reasons) and treats **management override of controls** as a risk in every audit, answered in part by testing journal entries. The team also discusses, together, how and where fraud could occur — the **brainstorming** session." },
          { watch: "Fraud needs pressure, opportunity and rationalization. A covenant supplies pressure; an eleven-week approval gap supplies opportunity." },
        ],
      },
      {
        heading: "Harborline's facts, turned into risks",
        blocks: [
          { harborline: "Three changes this year: (1) the **AP supervisor left in June** and was not replaced until September — payments went out without a dedicated approver; (2) **vendor creation moved into purchasing** in April — the people who raise POs can now create the vendors they pay; (3) the **warehouse switched to scanners** mid-year, and the controller expects some receipts never reached the system." },
          { p: "Each is a risk at an assertion: (1) **authorization** of payments; (2) **occurrence** — fictitious or duplicate vendors; (3) **occurrence and accuracy** — paying for goods never received. Lesson 4 turns them into a plan." },
        ],
      },
    ],
    standards: [
      ["AU-C 315 (SAS 145)", "Understanding the entity; identifying and assessing RMM; separate inherent and control risk; stand-back"],
      ["AU-C 520", "Analytical procedures"],
      ["AU-C 240", "Fraud: presumed revenue risk, management override, brainstorming"],
    ],
    check: [
      { q: "For accounts payable, which assertion is usually the highest risk?",
        options: ["Existence", "Completeness", "Presentation", "Rights and obligations"],
        answer: 1,
        why: "Liabilities are more often understated than overstated — an unrecorded invoice makes results look better. Completeness is the usual focus." },
      { q: "Under SAS 145, if you will not test controls over an assertion, the RMM is…",
        options: ["low, because substantive tests will catch everything", "assessed at the inherent-risk level (control risk at maximum)", "not assessed at all", "equal to detection risk"],
        answer: 1,
        why: "With no controls reliance, control risk is maximum, so the combined RMM equals the inherent-risk assessment." },
      { q: "A preliminary analytical procedure shows AP flat while purchases rose 20%. What is it?",
        options: ["Evidence that AP is fairly stated", "A misstatement to put on the SAD", "A signal of possible understatement to investigate — a risk, not a conclusion", "Irrelevant at planning"],
        answer: 2,
        why: "At planning, analytics direct attention. Flat AP against rising purchases suggests unrecorded liabilities — a completeness risk to test." },
    ],
    task: {
      title: "Build the risk table",
      intro: "Using the engagement brief and the vendors.csv and payments.csv files:",
      steps: [
        "For each of Harborline's three changes, write the risk, the assertion it threatens, and whether it is inherent, control, or both.",
        "Add the two presumed fraud risks and say how each applies (or does not) to Harborline.",
        "Do the stand-back: name one material area you did not flag and justify leaving it unflagged.",
      ],
      deliver: "A risk table: risk · assertion · inherent/control · why.",
    },
    noesi: {
      coverage: "partial",
      summary: "Noesi keeps the assertion-level risk register as recorded judgment. It does not do analytics or grade risks for you.",
      does: [
        "The **Planning & Risk** tab records each risk with its **assertion**, a **level** (unassessed, low, moderate, high, significant), your rationale and your planned response.",
        "A **high or significant** risk is a proposal until a second person concurs. Changing it voids the concurrence.",
        "Readiness refuses the lock over `RISKS_UNASSESSED`, `HIGH_RISKS_WITHOUT_RESPONSE`, `HIGH_RISKS_WITHOUT_PROCEDURE` and `RISKS_AWAITING_CONCURRENCE`.",
      ],
      where: ["Workbench → Planning & Risk (any team chair records; reviewer or partner concurs)"],
      doesNot: [
        "It has no preliminary-analytics or ratio engine. You compute those in a spreadsheet.",
        "It stores your combined risk level. It deliberately does not show separate inherent and control dials: that decomposition is your judgment, recorded in the rationale.",
        "It does not identify fraud risks or run journal-entry tests.",
      ],
      tryIt: "Record 'Payments released without approval during the vacancy' at the authorization assertion, level significant, then try to concur with it from the same chair.",
    },
  },

  {
    n: 3,
    slug: "materiality",
    title: "Materiality and audit risk",
    phase: "Planning",
    question: "How large a mistake would change a reader's decision?",
    minutes: 25,
    objectives: [
      "Set overall materiality on a defensible benchmark",
      "Derive performance materiality and the clearly-trivial threshold",
      "Use the audit risk model to decide how much work a risk demands",
      "Explain qualitative materiality",
    ],
    sections: [
      {
        heading: "Materiality is about the reader",
        blocks: [
          { p: "AU-C 320: misstatements are **material** if they could reasonably influence the economic decisions users make on the statements. So start with the user. Harborline's key user is its **lender**, watching revenue and a current-ratio covenant." },
          { p: "Materiality is set at planning, revisited as the audit proceeds, and documented with its **basis** and **rationale**." },
        ],
      },
      {
        heading: "Choosing a benchmark",
        blocks: [
          { p: "Firms use rules of thumb — these are practice conventions, **not** requirements of the standard:" },
          { table: { head: ["Benchmark", "Typical range", "When it fits"], rows: [
            ["Pre-tax income", "~5%", "Stable, profitable entities"],
            ["Revenue", "~0.5%–1%", "Thin or volatile profit; users focused on activity"],
            ["Total assets", "~1%–2%", "Asset-heavy entities, some lenders' focus"],
            ["Equity", "~1%–5%", "Investment-type entities"],
          ] } },
          { harborline: "The plan uses **1% of revenue**: 1% × $42.4m ≈ $424,000, rounded to **$420,000** — the measure the lender's covenant tracks and the most stable across Harborline's three audited years." },
        ],
      },
      {
        heading: "Two derived thresholds do the daily work",
        blocks: [
          { terms: [
            ["Performance materiality", "Set below overall (commonly 50%–75%) to leave headroom for misstatements you do not find and for aggregation. You design procedures to it. Harborline: 75% × 420,000 = **$315,000**."],
            ["Clearly trivial", "Below this, misstatements need not be accumulated — unless qualitatively significant. Commonly ~5% of overall. Harborline: **$21,000**."],
          ] },
          { watch: "An unauthorized $500 payment is not 'trivial' — it is evidence about a control. Qualitative factors (fraud, covenants, related parties, a small error that flips a loss to a profit) can make a small amount material." },
        ],
      },
      {
        heading: "The audit risk model",
        blocks: [
          { p: "**Audit risk** is the risk of issuing a clean opinion on materially misstated statements. It combines the **risk of material misstatement** (inherent × control — the client's condition, which you assess) with **detection risk** (that your procedures miss it — the part you control)." },
          { p: "The practical rule: **the higher the RMM, the lower the detection risk you can accept**, so the more persuasive and extensive your procedures must be — more independent evidence, larger samples or whole populations, work nearer year end. A **significant risk** needs a response designed specifically for it." },
        ],
      },
    ],
    standards: [
      ["AU-C 320", "Materiality in planning and performing an audit; performance materiality"],
      ["AU-C 450", "Clearly trivial threshold; evaluating misstatements"],
      ["AU-C 315 / 330", "Risk of material misstatement and the response to it"],
    ],
    check: [
      { q: "Overall materiality is $420,000 and performance materiality is 75% of it. What is performance materiality?",
        options: ["$21,000", "$105,000", "$315,000", "$420,000"],
        answer: 2,
        why: "75% × 420,000 = 315,000. It sits below overall to leave room for undetected and aggregated misstatement." },
      { q: "A $9,000 unauthorized payment, below clearly trivial ($21,000). Accumulate it?",
        options: ["No — it is below clearly trivial", "Yes — it is qualitatively significant (authorization failure, possible fraud)", "Only if the client agrees", "Only at year end"],
        answer: 1,
        why: "Clearly trivial means clearly inconsequential by size *and* nature. An unauthorized payment is significant by nature." },
      { q: "You assess RMM as high. Detection risk must be…",
        options: ["higher", "lower — so procedures become more extensive and persuasive", "unchanged", "zero"],
        answer: 1,
        why: "Audit risk is held acceptably low; higher RMM leaves less room, so detection risk must fall." },
    ],
    task: {
      title: "Defend the benchmark",
      intro: "The plan chose 1% of revenue.",
      steps: [
        "Compute materiality on 1% of total assets ($28.1m) and compare with $420,000.",
        "Argue which benchmark better serves the lender, citing the covenant.",
        "Name two qualitative factors at Harborline that could make an amount under $21,000 matter.",
      ],
      deliver: "A half-page materiality memo: benchmark, amount, derived thresholds, qualitative factors.",
    },
    noesi: {
      coverage: "full",
      summary: "Materiality is entered once, and every later judgment is measured against it automatically.",
      does: [
        "Set **materiality with its basis and rationale** on the Workbench SAD & Completion tab. In Studio it is the first 'Next step'.",
        "The tool **derives performance materiality (75%) and clearly trivial (5%)**. Both appear on the SAD and the workpaper.",
        "Clearly trivial decides which judgments need a **second person's concurrence**: dispositions above it are proposals until concurred.",
        "Readiness refuses the lock while `MATERIALITY_NOT_SET`.",
      ],
      where: ["Studio → Next step 'Set materiality' (partner chair)", "Workbench → SAD & Completion", "Studio → Overview → materiality ruler"],
      doesNot: [
        "It does not choose the benchmark or the percentage. It applies fixed 75% and 5% derivations, which you should check against your firm's methodology.",
        "It does not evaluate qualitative materiality. When you waive something, you are asserting it is not qualitatively significant.",
      ],
      tryIt: "Enter 420000 and check that the ruler shows $21,000 and $315,000.",
    },
    video: {
      file: "learn-3-how-big-a-mistake.mp4",
      poster: "learn-3-how-big-a-mistake.jpg",
      title: "How big a mistake?",
      minutes: 2,
      credits: "Narration: ElevenLabs voice “Guy”. Screens: Noesi Studio and Learn on the Harborline demo. Photos from Wikimedia Commons: Jernej Furman (CC BY 2.0); Jim.henderson (CC BY-SA 4.0).",
    },
  },

  {
    n: 4,
    slug: "controls-and-plan",
    title: "Internal control and the audit plan",
    phase: "Planning",
    question: "Which controls can we rely on, and what will we test?",
    minutes: 30,
    objectives: [
      "Document a transaction cycle and its key controls",
      "Decide between a controls-reliance and a substantive approach",
      "Link each risk to a responsive procedure (AU-C 330)",
      "Communicate control deficiencies appropriately",
    ],
    sections: [
      {
        heading: "Understand the cycle before you test it",
        blocks: [
          { p: "The purchases-and-payments (**purchase-to-pay**) cycle: a **purchase order** is approved, goods are **received** (receiving report), the vendor's **invoice (voucher)** is matched to the PO and receipt, the payment is **approved and released**, it **clears the bank**, and it **posts to the general ledger**." },
          { p: "You document it — narrative, flowchart, or walkthrough of one transaction end to end — and identify the **key controls**: the checks that, if they work, prevent or detect misstatement at an assertion." },
          { table: { head: ["Control", "Assertion it protects"], rows: [
            ["Vendor master changes approved by someone outside purchasing", "Occurrence (no fictitious vendors)"],
            ["Three-way match of PO, receipt and invoice before payment", "Occurrence, accuracy"],
            ["Payment above a limit needs a second signature", "Authorization"],
            ["Monthly reconciliation of the AP subledger to the GL", "Completeness, accuracy"],
          ] } },
        ],
      },
      {
        heading: "Rely on controls, or go substantive?",
        blocks: [
          { p: "If controls are well designed and you intend to rely on them, you **test their operating effectiveness** (Lesson 5) and may reduce substantive work. If they are weak — or testing them costs more than it saves — you assess control risk at maximum and rely on **substantive procedures**." },
          { harborline: "Harborline's AP controls were compromised this year: no dedicated approver for eleven weeks, vendor creation in the same department that raises POs, receiving in transition. A **substantive approach** across full populations is the natural response — which is what the audit plan chooses." },
        ],
      },
      {
        heading: "Every risk gets a response",
        blocks: [
          { p: "AU-C 330 requires procedures **responsive** to each assessed risk at the assertion level. The discipline: a procedure earns its place by the risk it answers, not by being easy to run." },
          { table: { head: ["Risk", "Assertion", "Response"], rows: [
            ["Payments released without approval", "Authorization", "Test segregation of duties across all payments"],
            ["Fictitious / duplicate vendors", "Occurrence", "Screen the vendor master for near-duplicates; trace to payments"],
            ["Paying for goods never received", "Occurrence", "Three-way match PO, voucher, receipt"],
            ["Payments structured below the limit", "Authorization", "Cluster payments by vendor and date against $10,000"],
            ["Subledger does not support the GL", "Completeness", "Reconcile subledger to GL control account 2000"],
          ] } },
        ],
      },
      {
        heading: "Telling management about weaknesses",
        blocks: [
          { p: "Control deficiencies you identify are evaluated for severity. **Significant deficiencies** and **material weaknesses** must be communicated **in writing** to management and those charged with governance (AU-C 265) — whether or not they caused a misstatement." },
          { watch: "A control that failed is a finding even when no dollar error resulted. The approval gap is reportable on its own." },
        ],
      },
    ],
    standards: [
      ["AU-C 315", "Understanding internal control; identifying controls relevant to the audit"],
      ["AU-C 330", "Responses to assessed risks; tests of controls vs substantive procedures"],
      ["AU-C 265", "Communicating internal control related matters"],
    ],
    check: [
      { q: "Controls over approvals failed for part of the year. The most defensible approach is…",
        options: ["Test the controls anyway and rely on them", "Assess control risk at maximum for that period and respond substantively", "Skip the area — it was only eleven weeks", "Ask management to certify the payments"],
        answer: 1,
        why: "You cannot rely on a control that did not operate. Substantive testing — ideally of the whole population — answers the risk." },
      { q: "The three-way match protects mainly which assertions?",
        options: ["Presentation and classification", "Occurrence and accuracy", "Rights and obligations", "Cutoff only"],
        answer: 1,
        why: "It confirms the goods were ordered and received (occurrence) at the invoiced amount (accuracy) before paying." },
      { q: "A significant deficiency caused no misstatement. Communicate it?",
        options: ["No — no harm was done", "Yes, in writing (AU-C 265)", "Only verbally", "Only if the client asks"],
        answer: 1,
        why: "AU-C 265 requires written communication of significant deficiencies and material weaknesses regardless of whether they caused misstatement." },
    ],
    task: {
      title: "Draw the cycle and the plan",
      intro: "Use the ten files in data/ and the audit plan (docs/02-audit-plan.md).",
      steps: [
        "Sketch the purchase-to-pay flow and mark each file on it.",
        "Mark where each of the four controls in this lesson should operate and whether Harborline's brief says it did.",
        "For each of your Lesson 2 risks, write the responsive procedure and the files it needs.",
      ],
      deliver: "A one-page cycle diagram and a risk-to-procedure matrix.",
    },
    noesi: {
      coverage: "full",
      summary: "Noesi's procedure library, risk linking and coverage compiler are the audit plan in executable form.",
      does: [
        "Each of the **eleven procedure contracts** states its cycle, its **assertions**, the data and policies it needs, and its **limitations**.",
        "On Planning & Risk you **link procedures to each risk**. The screen offers the procedures whose contract addresses the same assertion.",
        "**Coverage** compiles every contract against the data you actually loaded: executable, partial (a field or policy is missing), blocked (a file is missing), or unsupported (no executor exists in this build).",
        "**Policies** such as `split_threshold = 10000` are recorded as engagement decisions. Deselecting a procedure requires a written rationale.",
        "Studio's Overview draws the purchase-to-pay cycle with each test placed on the link it checks.",
      ],
      where: ["Workbench → Coverage (policies: partner chair)", "Workbench → Planning & Risk (link procedures)", "Studio → Overview (cycle picture)"],
      doesNot: [
        "It does not document or walk through controls, and it does not test operating effectiveness by sampling. The controls stage is marked complete by you.",
        "It does not write the AU-C 265 communication.",
      ],
      tryIt: "Load the ten Harborline files by hand (the --demo seed pre-approves the policies), open Coverage before setting split_threshold — 10 executable, 1 partial — then set it to 10000 and watch the split review become executable.",
    },
    video: {
      file: "learn-4-eleven-weeks-without-an-approver.mp4",
      poster: "learn-4-eleven-weeks-without-an-approver.jpg",
      title: "Eleven weeks without an approver",
      minutes: 2,
      credits: "Narration: ElevenLabs voice “Guy”. Screens: Noesi Workbench, Studio and Learn on the Harborline demo; the engagement brief.",
    },
  },
];
