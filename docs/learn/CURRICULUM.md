# Learn the audit — curriculum plan and research notes

*Written 2026-09-23 before the lessons, as the plan they were built from. The
lessons live in `apps/studio-ui/src/learn/lessons.ts` and render at
`/studio/#/learn`.*

## Purpose

A self-paced course in the typical CPA financial-statement audit, taught as one
integrated engagement from acceptance to the report, the way integrated audit
practice cases (for example Armond Dalton's *Oceanview Marine Company*, ten
assignments from client acceptance to completion) teach it. Each lesson teaches
the audit step first. It ends with a reminder of what Noesi Assurance does for
that step, where, under which chair, and what it does **not** do.

The lessons are **original**. They follow the standard phase order found in
every auditing text and in the AICPA clarified standards. They do not reproduce
any published case's content, documents, or solutions. The running client is
Noesi's own fictional **Harborline Marine Group** (`case-studies/harborline-marine/`).

## Lesson map

| # | Lesson | Core standards | Harborline hook | Noesi tie-in (verified in code) |
|---|---|---|---|---|
| 1 | Client acceptance & terms | SQMS 1 / AU-C 220 (SAS 146), AU-C 210, 510 | Third annual audit; lender needs audited statements in 120 days | Create engagement → creator is partner; Team tab assigns preparer/reviewer; journal |
| 2 | Understanding the entity & preliminary analytics | AU-C 315 (SAS 145), 520, 240 | Supervisor vacancy, vendor onboarding move, receiving change | Risk register (assertion, level, rationale, response); no analytics engine (stated) |
| 3 | Materiality & audit risk | AU-C 320, 315, 450 | 420,000 / 315,000 / 21,000 on 1% of revenue | Materiality on SAD tab; PM 75% and trivial 5% derived; risk concurrence for high/significant |
| 4 | Internal control & the audit plan | AU-C 315, 330, 265 | Four AP control weaknesses → procedures | Contracts carry assertions; risk ↔ procedure linking; coverage statuses; policies |
| 5 | Evidence, sampling & tests of transactions | AU-C 500 (SAS 142), 530, 330 | Full-population tests vs a sample; 52 findings | Upload→map→approve→normalize; reperform-on-read; runs, manifests, review lifecycle |
| 6 | Accounts payable & unrecorded liabilities | AU-C 330, 500, 450 | PAY-2026-0055 paid 2027-01-08 for a voucher not in the population; subledger variance 18,450 | 11 AP procedures; dispositions; concurrence above trivial; What Changed |
| 7 | Revenue & accounts receivable | AU-C 240 (revenue presumption), 330/505 (AR confirmation) | Service and storage revenue (illustrative figures only) | **Not implemented**: no AR contracts; evidence vault can hold documents |
| 8 | Cash | AU-C 505, SAS 150 (effective FY ending ≥ 2028-12-15) | PAY-2026-0028 written 2026-12-31, cleared 2027-01-02 | `cash.bank_clearing` (payments side, 2% tolerance), `gl.payment_posting`; not a full bank rec |
| 9 | Inventory | AU-C 501 | Vessels and Norfolk parts warehouse (illustrative) | **Not implemented**: no inventory contracts; stated honestly |
| 10 | Completion & the report | AU-C 450, 560, 570, 580, 700, 230, 260, 265 | SAD vs 420,000; lock and packet | Six completion checks, readiness blockers, SAD conclusion, signed lock, packet, reopen-with-reason |

## Verified facts used in the lessons

**Standards (checked 2026-09-23):**

- SAS 145 (AU-C 315) is effective for periods ending on or after 2023-12-15. It requires separate assessment of inherent and control risk and adds a "stand-back" requirement. If control risk is at maximum (controls not tested), the RMM equals the inherent risk. Sources: Thomson Reuters, Journal of Accountancy (2022-10), VSCPA.
- SQMS 1 and 2 and SAS 146 (new AU-C 220): firm quality management. SAS 146 applies to periods beginning on or after 2025-12-15 and supersedes the prior AU-C 220. Acceptance and continuance is a required quality objective. Sources: AICPA SAS 146 PDF, Journal of Accountancy (2025-08), Thomson Reuters.
- AU-C 330: if AR is material, the auditor documents the basis for any decision *not* to confirm it. Source: CPA Hall Talk; PCAOB archive for the historical AU 330.
- SAS 150 *External Confirmations* (AICPA, July 2026): a new requirement to confirm cash and cash equivalents held by third parties unless certain conditions exist. Effective for periods ending on or after 2028-12-15, early adoption permitted. Source: Journal of Accountancy, 2026-07.
- AU-C 501: when inventory is material, attend the physical count unless impracticable. Otherwise perform alternative procedures or modify the opinion. Source: CPCON comparison of AS 2510 and AU-C 501.
- AU-C 510: opening balances and predecessor/successor communication. Source: Wiley GAAS guide.
- AU-C 570 (SAS 132): going-concern evaluation period, one year after issuance (or availability for issuance) when the framework sets none. Under U.S. GAAP (ASU 2014-15) management evaluates the same period. Sources: Surgent, EY To the Point.
- AU-C 240: revenue recognition is a presumed fraud risk (overcoming the presumption must be documented). Management override is a risk in every audit, answered in part by journal-entry testing. Sources: Audit Sight, Sawyer Assurance, AU-C 240 text.
- Assertions (AU-C 315): transactions (occurrence, completeness, accuracy, cutoff, classification, presentation); balances (existence, rights and obligations, completeness, accuracy/valuation/allocation, classification, presentation). Sources: Thomson Reuters, Universal CPA Review.
- AU-C 230: assemble the final file within 60 days of the report release date; retain at least 5 years (web-verified 2026-09-23). PCAOB AS 1215: 7-year retention; the assembly window is 45 days, amended to **14 days** in the version effective 2026-12-15 (PCAOB AS 1215 page, fetched 2026-09-23). The Noesi manual (ch. 7, glossary) was corrected to match on 2026-09-23.
- AU-C 580: representations dated as of the auditor's report date. AU-C 265: significant deficiencies and material weaknesses communicated in writing (web-verified 2026-09-23).

**Materiality benchmarks** (1% of revenue, 5% of pre-tax income, and so on) are practice rules of thumb, not requirements of AU-C 320. The lessons say so.

**Noesi functions** were checked against code on 2026-09-23:

- `COMPLETION_CHECKS` in `assurance_domain/readiness.py`: final analytical review, subsequent events, going concern, management representations, evidence sufficiency, engagement review.
- Performance materiality 75% and clearly trivial 5% (`assurance_domain/sad.py`: `PERFORMANCE_PCT`, `TRIVIAL_PCT`).
- Eleven procedure contracts (`procedures_ap/contracts.py`). No AR or inventory contracts exist.
- Revised-evidence impact: `WorkbenchService.revision_impact`, `GET /api/engagements/{id}/impact`.
- Everything else follows the manual (`docs/manual/`), whose claims were spot-checked against `service.py` and `readiness.py`.

## Harborline facts used (from case files)

- The engagement brief supplies revenue 42.4m, total assets 28.1m, AP 2.73m, and 146 employees. It also supplies the covenant (audited statements within 120 days, current ratio ≥ 1.25), that this is the third annual audit, and the three changes: AP supervisor gap June–September, vendor creation moved to purchasing in April, receiving moved to scanners in H2.
- The plan sets materiality 420,000 (1% of revenue), PM 315,000, trivial 21,000, and a $10,000 approval limit.
- `data/`: PAY-2026-0055 dated 2027-01-08 cites the absent VCH-2026-9336 and cleared the bank 2027-01-12. PAY-2026-0028 was written 2026-12-31 and cleared 2027-01-02. AP subledger is 2,731,569.42 and GL control 2,750,019.42 (variance 18,450.00).
- `instructor/ANSWER-KEY.md`: split cluster V1042 totals 48,995 over nine days. The value-flow ring is 48,500 via Meridian Holdings.
- AR and inventory figures in lessons 7 and 9 are **illustrative** and labelled so. The case holds no AR or inventory data.

## Design rules

1. Teach the audit step before the tool. The Noesi box comes last in every lesson.
2. Every lesson has a check-your-understanding quiz with explanations (learn as you go). It also has a hands-on task, which uses real case files where they exist and a judgment exercise where they do not.
3. Each Noesi box says what the tool does *not* do for that step, in the same words the code supports.
4. No lesson claims a Noesi feature that is not in the code. Lessons 7 and 9 say plainly that the tool does not cover them.
