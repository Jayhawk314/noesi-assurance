// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Lesson 10: completion and the report. Sources: docs/learn/CURRICULUM.md. */

import { Lesson } from "./types";

export const COMPLETION: Lesson[] = [
  {
    n: 10,
    slug: "completion",
    title: "Completing the audit and the report",
    phase: "Completion",
    question: "Taken together, are the statements fairly presented — and what do we sign?",
    minutes: 40,
    objectives: [
      "Evaluate uncorrected misstatements against materiality",
      "Perform the completion procedures: subsequent events, going concern, representations",
      "Choose the right opinion",
      "Assemble and retain the audit file",
    ],
    sections: [
      {
        heading: "Evaluate the misstatements",
        blocks: [
          { p: "AU-C 450: **accumulate** identified misstatements (except clearly trivial ones), **communicate** them to management and ask for correction, then **evaluate** what remains uncorrected — individually and in aggregate, quantitatively and qualitatively — against materiality. The working paper is the **summary of audit differences (SAD)**." },
          { p: "If uncorrected misstatements approach performance materiality, the risk that undetected misstatement pushes the total over materiality rises. You may need more work, or a harder conversation with management." },
        ],
      },
      {
        heading: "Completion procedures",
        blocks: [
          { terms: [
            ["Final analytical review", "Read the statements as a whole. Do they make sense given everything you learned (AU-C 520)?"],
            ["Subsequent events (AU-C 560)", "Events after year end up to the report date. **Recognized** events give evidence about conditions at year end, such as a customer's bankruptcy in February for a December balance, and are adjusted. **Nonrecognized** events arise afterwards, such as a fire in March, and may need disclosure."],
            ["Going concern (AU-C 570)", "Is there substantial doubt about the entity continuing for **one year after the statements are issued** (or available to be issued)? Covenant breaches and refinancing needs are classic indicators."],
            ["Written representations (AU-C 580)", "Management's letter confirming its responsibilities and key matters, **dated as of the report date**. Refusal is a scope limitation."],
            ["Engagement review", "The partner's and reviewer's final review of the file, and resolution of open points."],
          ] },
          { p: "You also communicate with **those charged with governance** (AU-C 260): significant findings, difficulties, uncorrected misstatements. Written communication of control deficiencies (AU-C 265, from Lesson 4) goes out now if it has not already." },
        ],
      },
      {
        heading: "Choosing the opinion",
        blocks: [
          { table: { head: ["Situation", "Opinion"], rows: [
            ["Fairly presented; sufficient evidence", "**Unmodified** (clean), AU-C 700"],
            ["Material but not pervasive misstatement, or scope limitation", "**Qualified** ('except for'), AU-C 705"],
            ["Material and pervasive misstatement", "**Adverse**"],
            ["Possible effects of a scope limitation material and pervasive", "**Disclaimer** of opinion"],
          ] } },
          { p: "Separately, AU-C 706 **emphasis-of-matter** paragraphs draw attention to properly presented matters, and going-concern doubt has its own required reporting." },
        ],
      },
      {
        heading: "Assembling the file",
        blocks: [
          { p: "After the report is released, the file is **assembled** into its final form within **60 days** (AU-C 230) and retained at least **5 years**. Public-company audits follow PCAOB AS 1215: **7 years** of retention, and an assembly window of 45 days that the amended AS 1215, effective December 15, 2026, shortens to **14 days**. After assembly, nothing is deleted. Any later change records **the specific reason, who made it, and when**, and preserves the original." },
          { harborline: "With the planted exceptions dispositioned honestly, Harborline's uncorrected total stays under $420,000. The interesting output is not the conclusion but the trail behind it: every exception judged with a note, every run tied to the exact files it read." },
        ],
      },
    ],
    standards: [
      ["AU-C 450", "Evaluation of misstatements; the SAD"],
      ["AU-C 560 / 570 / 580", "Subsequent events; going concern; written representations"],
      ["AU-C 260 / 265", "Communication with governance; control deficiencies"],
      ["AU-C 700 / 705 / 706", "Forming the opinion; modifications; emphasis-of-matter"],
      ["AU-C 230 / PCAOB AS 1215", "Documentation: assembly within 60 days (AICPA) or 14 days (PCAOB, amended AS 1215 effective 12/15/2026, previously 45); retention 5 / 7 years"],
    ],
    check: [
      { q: "In February a major customer goes bankrupt. It was already failing at 31 December. This is…",
        options: ["a nonrecognized subsequent event — disclose only", "a recognized subsequent event — adjust the year-end allowance", "irrelevant to the audit", "a going-concern issue for the auditor"],
        answer: 1,
        why: "It gives evidence about a condition that existed at year end, so the statements are adjusted." },
      { q: "Management refuses to sign the representation letter. The effect is…",
        options: ["none — it is a formality", "a scope limitation that affects the opinion", "an adverse opinion automatically", "the auditor signs it instead"],
        answer: 1,
        why: "Written representations are required evidence. Refusal limits scope and normally leads to a disclaimer or withdrawal." },
      { q: "After the file is assembled, a workpaper must be corrected. You…",
        options: ["overwrite the page", "document the reason, who and when, and preserve the original", "start a new file", "cannot change anything, ever"],
        answer: 1,
        why: "AU-C 230 allows post-assembly changes only with that documentation and without deleting the prior record." },
    ],
    task: {
      title: "Complete the file",
      intro: "Using your dispositions from Lesson 6 and the materiality from Lesson 3:",
      steps: [
        "Build the SAD: list uncorrected misstatements and total them against 21,000, 315,000 and 420,000.",
        "Write one line for each completion check: final analytics, subsequent events, going concern, representations, evidence sufficiency, engagement review.",
        "State the opinion you would issue and why, including any limitation you recorded along the way.",
      ],
      deliver: "A completion memo and a draft opinion paragraph.",
    },
    noesi: {
      coverage: "full",
      summary: "Completion is where Noesi names everything still open, then exports a record of the testing that anyone can check. It does not sign or close the audit file.",
      does: [
        "The **SAD** totals unadjusted differences against materiality, performance materiality and clearly trivial, and concludes immaterial or material. It refuses to conclude over undisposed judgments.",
        "**Readiness** names every open item by its fact: findings without a judgment, procedures that could not run or have not run, results left stale by a changed file, missing materiality. Studio's Conclusion view lists them in plain words.",
        "**Export** (any time) downloads the record: every file fingerprint, run, finding, judgment and the journal position, which re-checks **offline** with no tool and no vendor. It is not signed: it proves the record is internally consistent, not who made it.",
        "Since September 2026, with the completion cycle chosen, procedures look at subsequent events, going-concern indicators, the representation letter and the summary of uncorrected misstatements, and **Draft Opinion** shows the opinion the findings support and the decisions it needs from you.",
      ],
      where: ["Studio → Conclusion (SAD, open items)", "Workbench → SAD & Completion", "Workbench → Draft Opinion", "Workbench → Export"],
      doesNot: [
        "It does not decide the opinion or issue the report; the draft is a starting point for your judgment.",
        "It does not assemble, sign or archive the audit file. That is the firm's act. (Until October 2026 it locked and signed engagements; that was removed.)",
        "An internally consistent record proves the **file's** integrity, not the **audit's** quality. A tidy record of thin work is still thin work.",
      ],
      tryIt: "On the Harborline demo, judge a few exceptions and open Export: read the open items, export the record, then rerun one procedure on a corrected file and see the earlier run marked stale.",
    },
    video: {
      file: "learn-10-not-ready-to-sign.mp4",
      poster: "learn-10-not-ready-to-sign.jpg",
      title: "Not ready to sign",
      minutes: 2,
      credits: "Narration: ElevenLabs voice “Guy”. Screens: Noesi Workbench, Studio and Learn on the Harborline demo. PCAOB AS 1215 per pcaobus.org.",
    },
  },
];
