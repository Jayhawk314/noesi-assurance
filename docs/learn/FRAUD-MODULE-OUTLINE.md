# Fraud in payables — a CFE-aligned Learn track (outline for review)

*Drafted 2026-09-23 and approved with the recommendations below. F1–F6
are written (`apps/studio-ui/src/learn/lessons-fraud.ts`, route
`/studio/#/learn/fraud`); F7–F9 are planned. The format follows
`CURRICULUM.md`: teach the concept, work it on Harborline, then say what
Noesi does and does not do.*

## Purpose and honest scope

A short track that teaches **how occupational fraud works in purchasing
and payables, and how it is detected**, using Harborline's planted schemes
as the practice population. It supports study for the Certified Fraud
Examiner (CFE) exam. It is **not** a CFE prep course: it covers the parts of
the exam that a payables data set can teach, and it says which parts it
leaves to ACFE's own materials.

## The CFE exam, as checked on 2026-09-23

A new version of the exam, based on ACFE's 2024 Job Task Analysis, launched
on **2026-06-02**. It has **three sections** (the older exam had four):

| Section | Questions | Time |
|---|---:|---:|
| 1. Fraud Schemes and Financial Crimes | 120 | 2.5 h |
| 2. Fraud Investigations and Legal Issues | 120 | 2.5 h |
| 3. Fraud Prevention and Deterrence | 70 | 1.5 h |

Sources: ACFE, *About the CFE Exam* and the *2026 CFE Exam Content Outline*
(acfe.com/cfe-credential/about-the-cfe-exam; acfe.com/examoutline). Not
confirmed from ACFE's current pages: the passing score for the new version.
Check it before a lesson states one.

**What this track can cover, by exam domain** (weights are each domain's
share of its section, from the 2026 outline):

| Section · domain | Weight | Covered here |
|---|---:|---|
| S1 · Fraudulent disbursements (billing, payment tampering) | 13% | **Yes**, the core: F3, F4, F5 |
| S1 · Procurement fraud | 8% | Partly: F4, F6 (no bid data in the case) |
| S1 · Corruption | 6% | Partly: F6 (concepts; case has leads, not proof) |
| S1 · Money laundering | 7% | Partly: F7 (layering pattern only) |
| S1 · Accounting concepts; financial statement fraud | 6%; 4% | Partly: F1, F7 |
| S2 · Data analysis and reporting tools | 5% | **Yes**: F8 |
| S2 · Tracing assets | 5% | Partly: F7 |
| S2 · Basic principles of evidence; collecting evidence | 7%; 11% | Partly: F5 (documentary evidence, custody) |
| S3 · Understanding financial crime (fraud triangle) | 10% | **Yes**: F1 |
| S3 · Fraud risk assessment | 20% | **Yes**: F2 |
| S3 · Auditors' and management's fraud responsibilities | 11%; 6% | **Yes**: F2, F9 |
| S3 · Fraud prevention programs; fraud risk management | 16%; 14% | Partly: F9 |

**Left to ACFE's materials, stated in the track:** payroll, expense and
register schemes; cash receipts; the industry domains (insurance, health
care, securities, tax, bankruptcy, cyber, identity theft, financial
institution, consumer, government); interviewing and admission-seeking
interviews; covert operations; the law, prosecutions, civil actions and
testifying; ethics for fraud examiners (15% of section 3). Most of section 2
is legal and investigative work that a data set cannot teach.

## Design rules

1. **Original content.** Lessons name ACFE's categories (the Fraud Tree's
   three branches, the fraud triangle) but do not reproduce ACFE text,
   the Fraud Examiners Manual, or exam questions.
2. **A finding is a lead, not proof of fraud.** Every lesson separates what
   the records show, what it could mean (fraud *or* an innocent error), and
   what evidence would tell them apart. Noesi's own limitation text is quoted.
3. **Auditor vs fraud examiner.** A financial-statement auditor looks for
   material misstatement (AU-C 240); a fraud examiner investigates a
   specific allegation to a conclusion. The track keeps saying which hat a
   step belongs to.
4. Same lesson shape as the course: question, sections, check-your-
   understanding with explanations, a hands-on task on real case files, and
   a closing **In Noesi** box including what it does not do.

## Lesson map

| # | Lesson | Big question | CFE domains | Harborline hook (verified in case files) | Noesi tie-in |
|---|---|---|---|---|---|
| F1 | Why fraud happens | What turns an employee into a fraudster, and how is fraud classified? | S3 understanding financial crime; S1 accounting concepts | The AP supervisor left in June and was not replaced until September; approval limits were "handled informally" (engagement brief). Opportunity and rationalization, in the client's own words. | None directly. The risk register is introduced for F2. |
| F2 | Fraud risk assessment | Where could fraud happen here, and which controls would stop it? | S3 fraud risk assessment (20%), auditors' and management's responsibilities, COSO | The brief's three changes (supervisor gap; vendor setup moved to purchasing in April; receiving moved to scanners) each become a fraud risk with inherent vs residual risk. AU-C 240: revenue and management override as presumed risks. | Risk register: assertion, level, rationale, linked procedures; concurrence for high/significant risks. |
| F3 | Billing schemes and shell vendors | How does fake or duplicated billing get paid? | S1 fraudulent disbursements (billing), procurement | Three look-alike vendor pairs share a tax ID and remit city: V1038/V1039 "Harbor/Harbour Marine Supply", V1040/V1041, V1042/V1043. VCH-2026-9338 re-bills PO-2026-0013 one week later (Assignment 11). | `ap.vendor_relational_twins` flags the pairs. **Noesi has no duplicate-invoice test**; students find 9338 from the data, as the answer key expects. |
| F4 | Payment tampering, self-approval and split payments | How are payment controls bypassed? | S1 fraudulent disbursements (payment tampering), procurement | Five payments entered and approved by the same AP clerk (E227 Alice Bergeron, E231 Ken Nakashima); three fall inside the supervisor gap. V1042 receives payments of 9,640 to 9,905 in September, just under the $10,000 approval limit (cluster 48,995). Payments exceed their vouchers (PAY-0016, 0093, 0109); two precede their vouchers. | `ap.segregation_of_duties`, `ap.split_payment_review` (needs the approved threshold policy), `ap.document_chain`. |
| F5 | Following one person | When do separate exceptions become a case worth investigating? | S2 planning a fraud examination, basic principles of evidence, collecting evidence | E227's trail: self-approved PAY-2026-0013 paid the duplicate invoice VCH-2026-9338; self-approved PAY-2026-0055 (dated 2027-01-08) cites VCH-2026-9336, which is not in the voucher population. Predication: enough to open an examination, not to accuse. | Findings and receipts; the evidence vault (SHA-256, never altered) as chain of custody; the journal. Noesi never concludes intent. |
| F6 | Corruption and kickbacks in purchasing | How do bribes and conflicts of interest show up in payables data? | S1 corruption, procurement fraud | Overpayments against vouchers (F4) as a possible kickback funding pattern, taught as one hypothesis among several. The case has no bid records or employee–vendor relationships, and the lesson says so. | `ap.document_chain` gives the amounts. **No bid-rigging or conflict-of-interest test**: stated honestly. |
| F7 | Following the money | How do you trace funds that leave and come back? | S2 tracing assets; S1 money laundering (layering), financial statement fraud | 48,500 leaves Harborline as "consulting" to Bayview Advisory Partners on 2026-11-03, moves to Meridian Holdings LC on 11-05, and returns to Harborline on 11-07. It could be round-tripping, disguised financing, or legitimate; the lesson asks what evidence separates them. | `forensic.closed_value_flow`: a coherent round trip is a lead; the completeness of the flow population bounds what it proves. |
| F8 | Data analysis for fraud detection | How do you test every transaction and read the results well? | S2 data analysis and reporting tools; S3 prevention (continuous monitoring) | 52 findings across 11 procedures for 40 planted exceptions (cross-findings). PAY-2026-0025 differs from the bank by under 2% and is deliberately silent: silence means "within tolerance", not "nothing there". | Full-population procedures, coverage and refusals, stated tolerances. **No Benford test**: a spreadsheet task on `payments.csv` (123 rows, too few for a reliable Benford result, which is itself a lesson). |
| F9 | Preventing it next time | Which controls would have stopped each scheme, and who is told? | S3 fraud prevention programs, fraud risk management, management's responsibilities | Map every F3–F7 scheme to the control that failed (vendor master review, independent payment approval, approval-limit monitoring, three-way match) and draft the control-deficiency letter (AU-C 265). | Completion, dispositions and the SAD; Noesi does not write the management letter. |

## Hands-on tasks (one per lesson, all on real case files)

- F1: classify ten short scheme descriptions onto the Fraud Tree's three branches.
- F2: build a fraud risk register for AP from the brief; rate inherent and residual risk.
- F3: sort `vendors.csv` by tax ID and name; find the pairs before running Noesi.
- F4: filter `payments.csv` for creator = approver, then for amounts 9,000–9,999 by vendor.
- F5: build a one-page timeline of E227's transactions; list the evidence you would request next.
- F6: write two innocent and two fraudulent explanations for PAY-2026-0016's overpayment, and what evidence would decide between them.
- F7: draw the Bayview–Meridian flow; list the records that would confirm or dismiss round-tripping.
- F8: run a first-digit (Benford) count on payment amounts in a spreadsheet and explain why 123 rows is too few.
- F9: write the control-deficiency letter points.

## Open questions for James

1. **Separate track or lessons 11+?** Recommendation: a separate "Fraud in
   payables" track on the Learn home page, so the main audit course stays
   ten lessons.
2. **How much exam prep?** Should the track add short reading-only lessons
   for the domains it cannot practice (ethics, interviewing, law), or just
   point to ACFE's materials? Recommendation: point to ACFE and keep the
   track hands-on.
3. **More planted schemes?** Harborline has no payroll, expense, bid or
   conflict-of-interest data. Adding a scheme means regenerating the case
   and its answer key (`generate.py`), which the oracle test then freezes.
   Recommendation: not for the first version.
4. **Lesson length.** The main course runs 20–40 minutes per lesson. Keep
   that?

## Standards facts checked for the lessons (2026-09-23)

- **SAS No. 151**, *The Auditor's Responsibilities Relating to Fraud in an
  Audit of Financial Statements*, approved by the ASB in August 2026,
  supersedes AU-C 240 for audits of periods ending on or after
  **2028-12-15**, early implementation permitted. It applies a fraud lens
  to AU-C 315 risk assessment, requires understanding any whistleblower
  program, and expands responses and communications; the definition of
  fraud and the auditor's objective are unchanged. Sources: Journal of
  Accountancy (2026-08), AICPA news release. Harborline's FY2026 audit is
  taught under AU-C 240.
- ACFE *Occupational Fraud 2026: A Report to the Nations*: 2,402 cases in
  143 countries and territories; losses over $3.4 billion; median loss
  $104,000; asset misappropriation 90% of cases (median $100,000),
  corruption 45% ($150,000), financial statement fraud 6% ($1,000,000).
  Source: ACFE Insights blog, key findings.
- Noesi's risk register (checked in code): assertions accuracy,
  authorization, completeness, cutoff, occurrence; levels unassessed to
  significant; readiness blocks on unassessed risks and on high or
  significant risks without a response or linked procedure.

## Decisions (2026-09-23)

Separate track; point to ACFE for law, interviewing and ethics; no new
planted schemes in version 1; lessons of 20–40 minutes.

## Before each remaining lesson is written

- Confirm the new exam's passing score and any section-specific rules on acfe.com.
- Re-check every Harborline reference above against `data/` and
  `instructor/PLANTED-EXCEPTIONS.json` at build time (the oracle test
  guards them).
- Quote Noesi's procedure limitations from `procedures_ap/contracts.py`,
  not from memory.

## Found in the data while writing F5–F6 (2026-09-24)

Recomputed from `data/*.csv` and `revision/vouchers_revised.csv`; both are
now taught in the lessons.

- **Phantom-voucher shape.** PAY-2026-0013 and PAY-2026-0055 (E227,
  self-approved) each pay the vendor and amount of a real voucher that
  E227 entered and approved (VCH-2026-0013, 0055), but cite a voucher
  number absent from the file (9338, 9336); the real vouchers have no
  payment. PAY-2026-0100 (E218 / E102, vendor V1038) has the same shape.
  On all five self-approved payments the clerk also approved the purchase
  order (E227: PO-0013, 0055, 0064; E231: PO-0007, 0049).
- **Identical overpayment rate.** The three payments above their vouchers
  (PAY-2026-0016, 0093, 0109) are each exactly 18.000% over; PO, receipt
  and voucher agree in each case, and bank and GL carry the paid amount.
