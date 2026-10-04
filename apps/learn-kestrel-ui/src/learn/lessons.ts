// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** The Kestrel Learn modules (docs/LEARN-KESTREL-PLAN.md), in engagement
 *  order. All thirteen are written.
 *
 *  No figure is typed here. Each "ask" names a line of the finish-line check
 *  (`row`) and, where that line is yes/no, a path into the answer key (`key`);
 *  the compare step reads both from kestrel-key.json. */

import { Coming, Lesson } from "./types";

const DEMO_START = "Start the Workbench with the Kestrel demo: `python -m workbench_api --demo`, open the address it prints, and open **Kestrel Valley Cycle Supply (demo)**. (Without `--demo`, choose Kestrel under **load teaching case**.)";

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
      "Name the three roles on an engagement team and why they are kept apart",
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
        heading: "The team, and where review happens",
        blocks: [
          { p: "Quality management expects the work to be **prepared** by one person, **reviewed** by another, and **signed off** by the partner. The separation is the point: a reviewer who also prepared the work is checking their own answer." },
          { watch: "Noesi supplements the audit, so it has one user per engagement and no review or sign-off steps. The team's review happens in the firm, outside Noesi. A second login on the same laptop would be the same person twice, and Noesi does not pretend otherwise." },
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
        why: "The value of review is a second person. The same person in both roles is one look, recorded twice." },
    ],
    byHand: {
      files: ["quickbooks/Trial_Balance_2026-06-30.xlsx", "quickbooks/Trial_Balance_2025-06-30.xlsx", "the Policies table in the case README.md"],
      intro: "Set up the engagement as the partner would, from the client's exports and the partner's approved policies.",
      steps: [
        "Open this year's trial balance. Read the **As of** line under the title: that is the period end.",
        "Open the prior year's trial balance. The period starts the day after its **As of** date.",
        "Read the partner's approved materiality in the Policies table of the case README.",
        "Write down the three roles an engagement team needs, and who at the firm may hold each.",
      ],
      asks: [
        { label: "Period start", row: "period start" },
        { label: "Period end", row: "period end" },
        { label: "Materiality", row: "materiality" },
      ],
    },
    inNoesi: {
      procedures: ["Scope & Policies", "Planning & Risk", "Sources & Mappings"],
      steps: [
        DEMO_START,
        "**Header:** see the one user every step is recorded under.",
        "**Scope & Policies:** read the period start, the audit areas switched on, and every policy set for this engagement. The firm's approval of audit judgments happens outside Noesi.",
        "**Planning & Risk:** read materiality and its basis (SAD & Completion shows it too).",
        "**Sources & Mappings:** check that every file loaded and none was refused. Note which files say they were **prepared by hand** from the case files (the count tags, the reconciliations, the auditor's schedules), and that the trial balance was **built from QuickBooks' own exports**.",
      ],
    },
    keyModule: "Engagement setup",
    noesi: {
      coverage: "partial",
      summary: "Noesi records the frame (period, materiality, areas, policies) and holds every procedure to it. Choosing them stays with the auditor.",
      does: [
        "Keeps materiality, the period and the policies on the engagement record, journaled with who changed what and when.",
        "Shows each file's provenance, including files prepared by hand from an export.",
      ],
      where: ["Workbench → Scope & Policies", "Workbench → Planning & Risk", "Workbench → Sources & Mappings"],
      doesNot: [
        "It does not decide acceptance, independence or materiality; it records the auditor's decisions.",
        "It has no engagement-letter or independence checklist.",
        "It has no review or sign-off steps: one user per engagement, and the team's review happens in the firm.",
      ],
    },
  },

  {
    n: 2,
    slug: "planning",
    title: "Planning",
    phase: "Planning",
    question: "Where in the statements could a material misstatement hide, and how much error can each area carry?",
    minutes: 35,
    objectives: [
      "Foot a trial balance and compare it with the prior year before relying on it",
      "Flag movements that pass the partner's thresholds and say which assertion each puts at risk",
      "Compute the ratios a planning review reads, for both years",
      "Check performance materiality allocated across areas against the partner's cap",
    ],
    sections: [
      {
        heading: "Planning analytics point the work",
        blocks: [
          { p: "Before testing, the auditor reads the trial balance against last year. Accounts that moved a lot, or did not move when they should have, are where to look first. The point is not to explain every change yet; it is to choose where the testing goes." },
          { p: "A movement is flagged when it passes the partner's thresholds: a percentage of last year's balance, an amount, or (as here) either one. Each flag carries the assertion it puts at risk. An asset that grew may not exist; a liability that shrank may be incomplete; revenue that grew may not have occurred." },
          { watch: "Analytics on an unfooted trial balance are analytics on the wrong numbers. Foot it first: total debits must equal total credits." },
        ],
      },
      {
        heading: "Ratios as a second look",
        blocks: [
          { terms: [
            ["Current ratio", "Current assets over current liabilities: can the business pay what falls due within the year?"],
            ["Quick ratio", "The same, leaving out inventory and prepaids: cash and receivables only."],
            ["Gross margin", "Sales less cost of sales, over sales. A margin that moves without a business reason can mean cutoff or costing errors."],
            ["Inventory turnover", "Cost of sales over average inventory: how often stock is sold and replaced."],
            ["Sales to receivables", "Net sales over year-end net receivables. A drop can mean slow collection, or sales that are not real."],
          ] },
        ],
      },
      {
        heading: "Performance materiality by area",
        blocks: [
          { p: "Materiality is one figure for the statements. Performance materiality sets a lower figure for each area, so that small undetected errors across areas do not add up past materiality. The partner caps the total allocated at a multiple of materiality; an allocation above the cap is a planning decision for the partner to revisit, not a test result." },
        ],
      },
      {
        heading: "Kestrel at planning",
        blocks: [
          { kestrel: "Kestrel's two trial balance exports, this year's and last year's, are joined by account into one schedule. Each account is mapped once to a statement line so the ratios can be read. The partner's thresholds are in the case README and the allocation in `auditor/performance_materiality.csv`." },
        ],
      },
    ],
    standards: [
      ["AU-C 300", "Planning an audit"],
      ["AU-C 315", "Understanding the entity and assessing the risks of material misstatement"],
      ["AU-C 320", "Materiality in planning and performing an audit, including performance materiality"],
      ["AU-C 520", "Analytical procedures, including those used in planning"],
    ],
    check: [
      { q: "Accounts receivable rose sharply while sales were flat. Which assertion does that put at risk first?",
        options: ["Completeness of receivables", "Existence of receivables, and occurrence of the sales behind them", "Presentation of equity", "Nothing until year end"],
        answer: 1,
        why: "An asset that grew faster than the activity behind it may include amounts that are not real. Existence is what confirmations then test." },
      { q: "Performance materiality allocated across the areas adds up to more than the partner's cap. What is it?",
        options: ["A misstatement to book", "A planning decision for the partner to revisit", "Proof that materiality is wrong", "Nothing; caps are guidance"],
        answer: 1,
        why: "The allocation is the auditor's own plan, not the client's numbers. Over the cap means the plan allows more undetected error than the partner accepted." },
    ],
    byHand: {
      files: ["quickbooks/Trial_Balance_2026-06-30.xlsx", "quickbooks/Trial_Balance_2025-06-30.xlsx", "auditor/tb_line_mapping.csv", "auditor/performance_materiality.csv", "the Policies table in the case README.md"],
      intro: "Do the planning review a senior would do on the first day, from the two trial balance exports.",
      steps: [
        "Foot this year's trial balance: total the **Debit** and **Credit** columns and compare them with the **TOTAL** row.",
        "Put both years side by side by account number. For each account, compute the change and the change as a percentage of last year.",
        "Flag every account whose change passes either threshold in the Policies table.",
        "Using `auditor/tb_line_mapping.csv`, total each statement line for both years, then compute net revenue, cost of sales and pretax income.",
        "Compute the current ratio, quick ratio and gross margin for both years, and this year's inventory turnover (on average inventory) and sales to year-end net receivables.",
        "Total the allocations in `auditor/performance_materiality.csv` and compare the total with the cap: materiality times the allocation multiple.",
      ],
      asks: [
        { label: "Does the trial balance foot?", row: "trial balance foots" },
        { label: "Total debits", row: "trial balance debits" },
        { label: "Accounts flagged", row: "movements flagged (10% or 15,000)" },
        { label: "This year's net revenue", row: "2026 net revenue" },
        { label: "This year's pretax income", row: "2026 pretax income" },
        { label: "This year's current ratio", row: "2026 current ratio" },
        { label: "This year's gross margin %", row: "2026 gross margin %" },
        { label: "Last year's current ratio", row: "2025 current ratio" },
        { label: "Inventory turnover", row: "2026 inventory turnover (average inventory)" },
        { label: "Performance materiality allocated", row: "PM allocated" },
        { label: "The cap", row: "PM cap (2.0 x materiality)" },
        { label: "Over the cap by", row: "PM over the cap by" },
      ],
    },
    inNoesi: {
      procedures: ["fs.trial_balance_analytics", "planning.performance_materiality"],
      steps: [
        DEMO_START,
        "**Sources & Mappings:** the trial balance was **built from both QuickBooks exports**, this year's and last year's, each footed against its TOTAL before they were joined. Read its provenance.",
        "**Scope & Policies:** under **Trial balance lines**, see how each account maps to a statement line. An account with no line is listed and left out of the ratios, never guessed.",
        "**Runs & Findings:** read **fs.trial_balance_analytics**: the footing, the ratios for both years, and one finding per flagged movement with the assertion at risk.",
        "Read **planning.performance_materiality**: the total allocated, the cap, and the finding that the allocation is over it.",
      ],
    },
    keyModule: "Planning",
    noesi: {
      coverage: "full",
      summary: "Noesi foots the trial balance, flags every movement past the partner's thresholds with its assertion, computes the planning ratios for both years, and checks the performance-materiality allocation against the cap.",
      does: [
        "Builds the comparative trial balance from QuickBooks' own exports, refusing one that does not foot.",
        "Flags every movement that passes the thresholds, and names the assertion it puts at risk.",
        "Computes the ratios from the statement lines the team mapped, and lists any account left without a line.",
      ],
      where: ["Workbench → Sources & Mappings", "Workbench → Scope & Policies", "Workbench → Planning & Risk", "Workbench → Runs & Findings"],
      doesNot: [
        "It does not explain a movement: the explanation comes from the client and is corroborated by the auditor.",
        "It does not set the thresholds, materiality or the allocation; it applies the partner's.",
        "It does not assess risk overall: the flags feed the auditor's risk assessment; they are not the assessment.",
      ],
    },
  },

  {
    n: 3,
    slug: "journal-entries",
    title: "Journal entries",
    phase: "Fieldwork",
    question: "Did anyone push the books where they should not go, through an entry nobody would question?",
    minutes: 40,
    objectives: [
      "Prove the Journal is the whole population before testing it",
      "Test every entry for the traits of management override",
      "Tell a manual entry from one QuickBooks made for a transaction",
    ],
    sections: [
      {
        heading: "Why every audit tests journal entries",
        blocks: [
          { p: "Management can override controls that work well for everyone else, most easily by posting a journal entry. Because that risk is present in every entity, the standards require journal entries to be tested in every audit, not only when something looks wrong." },
          { p: "The test starts with **completeness of the population**: the Journal must hold every entry that moved the balances. Roll each account forward: last year's closing balance plus this year's lines must equal this year's balance. Income and expense accounts start from zero, because last year's result was closed to equity." },
        ],
      },
      {
        heading: "The traits of an override",
        blocks: [
          { list: [
            "**Posted after the period end** but dated inside it.",
            "**On a weekend or a holiday**, when nobody is reviewing.",
            "**Round amounts**, which look like estimates, not invoices.",
            "**By someone who does not normally post**, such as an owner.",
            "**To an account seldom used**, where nobody looks.",
            "**With no description**, so nobody can tell what it is for.",
          ] },
          { watch: "A trait is a reason to look, not a finding of fraud. Most flagged entries have an ordinary explanation; the work is to get it and corroborate it." },
        ],
      },
      {
        heading: "Manual or system",
        blocks: [
          { p: "QuickBooks records invoices, bills, checks and deposits as transactions with their own types. A **Journal Entry** is typed by hand. Many system transactions carry no description and mean nothing by it; a manual entry with no description is a different matter. The partner's policy names which transaction types count as manual." },
        ],
      },
      {
        heading: "Kestrel's Journal",
        blocks: [
          { kestrel: "Kestrel's QuickBooks Journal is exported with **Created on** and **Created by** added, so the posting date and the user can be tested. Each transaction's lines sit under its transaction ID and close with a **Total for** row. Dana Merritt, the bookkeeper, is the authorized user." },
        ],
      },
    ],
    standards: [
      ["AU-C 240", "The auditor's responsibilities relating to fraud, including testing journal entries for management override"],
      ["AU-C 330", "Performing audit procedures in response to assessed risks"],
      ["AU-C 500", "Audit evidence, including the completeness of information the entity produces"],
    ],
    check: [
      { q: "Why roll every account forward before testing the entries?",
        options: ["To compute the ratios", "To prove the Journal holds every entry that moved the balances, so the tests run on the whole population", "To find round amounts", "QuickBooks requires it"],
        answer: 1,
        why: "An override posted outside the file you were given cannot be found in it. The roll-forward proves the file is the whole population." },
      { q: "An invoice has no description. A Journal Entry has none either. Which matters more?",
        options: ["The invoice", "The Journal Entry: it is typed by hand, and a manual entry with no explanation is a trait of override", "Neither", "Both equally"],
        answer: 1,
        why: "System transactions often carry no description. A manual entry with none leaves no record of why it was made." },
    ],
    byHand: {
      files: ["quickbooks/Journal.xlsx", "quickbooks/Trial_Balance_2026-06-30.xlsx", "quickbooks/Trial_Balance_2025-06-30.xlsx"],
      intro: "Test the year's Journal for completeness, then for the traits of override.",
      steps: [
        "Count the transactions (one per **Total for** row) and the lines.",
        "Roll each balance-sheet account forward: last year's balance plus this year's debits less credits must equal this year's balance. Find the equity account last year's result was closed to, and the amount.",
        "Add a column with the date part of **Created on**. Filter for entries dated on or before the period end but created after it.",
        "Add a weekday column (`=WEEKDAY(date)`) and filter for Saturday and Sunday.",
        "Filter **Created by** for anyone other than the authorized user.",
        "Filter amounts at or above the round-amount threshold that are exact multiples of the round unit.",
        "Count how many transactions use each account. List the accounts used by only a few, and the entries that hit them.",
        "Count the transactions with a blank **Description**. Then filter to **Journal Entry** and find the manual one.",
      ],
      asks: [
        { label: "Transactions in the Journal", row: "transactions in the Journal" },
        { label: "Lines in the Journal", row: "lines in the Journal" },
        { label: "Does every account roll forward?", row: "every account rolls forward" },
        { label: "Last year's result was closed to", row: "closed to" },
        { label: "Posted after the period end", row: "posted after period end: entries" },
        { label: "Posted by someone other than the authorized user", row: "unauthorized user: entries" },
        { label: "Seldom-used accounts", row: "seldom-used accounts" },
        { label: "Transactions with no description", row: "no description: count" },
        { label: "The manual entry with no description", row: "manual entries without a description" },
      ],
    },
    inNoesi: {
      procedures: ["je.population_completeness", "je.journal_entry_testing"],
      steps: [
        DEMO_START,
        "**Sources & Mappings:** the Journal loads **raw** from QuickBooks' export. Read the lines loaded; each transaction is named by date, type, number and name.",
        "**Runs & Findings:** read **je.population_completeness**: every account rolls forward, and the account and amount last year was closed with.",
        "Read **je.journal_entry_testing**: one finding per entry and trait. Filter by test to see each list.",
      ],
    },
    keyModule: "Journal entries",
    noesi: {
      coverage: "full",
      summary: "Noesi proves the Journal is complete by rolling every account forward, then tests every entry for the traits of override.",
      does: [
        "Loads QuickBooks' Journal export raw, with every transaction's debits and credits footed.",
        "Rolls every account from last year's trial balance through the Journal to this year's.",
        "Flags entries posted late, on weekends or holidays, in round amounts, by an unauthorized user, to seldom-used accounts, or manual with no description.",
      ],
      where: ["Workbench → Sources & Mappings", "Workbench → Runs & Findings"],
      doesNot: [
        "It does not explain a flagged entry or judge whether it was proper: that takes inquiry and the documents behind it.",
        "It needs **Created on** and **Created by** added to the export; without them the late-posting and user tests cannot run.",
        "It does not choose the thresholds or the authorized users; the partner does.",
      ],
    },
  },

  {
    n: 4,
    slug: "revenue-and-receivables",
    title: "Revenue and receivables",
    phase: "Fieldwork",
    question: "Are the receivables real, owed in the amounts shown, and likely to be collected?",
    minutes: 45,
    objectives: [
      "Tie the aged receivables listing to the ledger, and explain a difference before testing from it",
      "Recompute the allowance from the partner's aging rates",
      "Evaluate confirmation results: count only true misstatements, and project the sample",
    ],
    sections: [
      {
        heading: "Start with the listing",
        blocks: [
          { p: "Every receivables test draws from the aged listing, so the listing must agree with the ledger first. A difference is not automatically a misstatement: a listing run before the last entries of the year will not agree. Find out why before testing from it." },
          { p: "Read the listing for **credit balances** too. A customer owing a negative amount is a liability (a prepayment or overpayment), not a receivable." },
        ],
      },
      {
        heading: "The allowance is an estimate",
        blocks: [
          { p: "The allowance for doubtful accounts reduces receivables to what will be collected. Here the partner approved a rate for each aging bucket. Multiply each bucket by its rate, add them up, and compare with the allowance recorded." },
        ],
      },
      {
        heading: "Confirmations",
        blocks: [
          { p: "A confirmation asks the customer directly what they owe. Large balances are confirmed in full as **key items**; a **sample** is drawn from the rest. Not every difference is a misstatement:" },
          { terms: [
            ["Timing difference", "A payment or invoice in transit at year end. Not a misstatement."],
            ["Customer error", "The customer's records are wrong. Not a misstatement."],
            ["Client misstatement", "Kestrel's books are wrong. This counts."],
          ] },
          { p: "Key-item misstatements count in full. Sample misstatements are projected to the rest of the population they came from. The total likely misstatement is compared with the tolerable misstatement for receivables." },
        ],
      },
      {
        heading: "Kestrel's receivables",
        blocks: [
          { kestrel: "Kestrel's A/R Aging Summary comes straight from QuickBooks. The confirmation replies are summarized in `auditor/confirmations.csv`, each classified. The aging rates and the tolerable misstatement are in the Policies table." },
        ],
      },
    ],
    standards: [
      ["AU-C 505", "External confirmations"],
      ["AU-C 530", "Audit sampling, including projecting misstatements"],
      ["AU-C 540", "Auditing accounting estimates, such as the allowance"],
      ["AU-C 450", "Evaluating misstatements identified during the audit"],
    ],
    check: [
      { q: "A customer confirms a lower balance because their payment was in the mail at year end. Is it a misstatement?",
        options: ["Yes, for the difference", "No: it is a timing difference", "Yes, projected to the population", "Only if it is a key item"],
        answer: 1,
        why: "The receivable was real at year end; the cash was in transit. Counting it would overstate the misstatement." },
      { q: "The aging total does not agree with the ledger. What first?",
        options: ["Book the difference", "Find out why: a listing run before the last entries of the year will not agree", "Ignore it below materiality", "Confirm every customer"],
        answer: 1,
        why: "A difference is a question about the listing, not yet a misstatement in the books. Test from a listing you can tie." },
    ],
    byHand: {
      files: ["quickbooks/AR_Aging_Summary.xlsx", "quickbooks/Trial_Balance_2026-06-30.xlsx", "auditor/confirmations.csv", "the Policies table in the case README.md"],
      intro: "Tie the aging, recompute the allowance and evaluate the confirmations, all on the aging as it was exported.",
      steps: [
        "Foot the aging and compare its total with accounts receivable on this year's trial balance.",
        "Scan the aging for a customer with a negative balance.",
        "Multiply each aging bucket's total by its rate in the Policies table and add them up. Compare with the allowance account on the trial balance.",
        "In `confirmations.csv`, count the key items and the sample items. Total the client misstatements among the key items.",
        "Note which customers' differences are client misstatements, leaving out timing differences and customer errors.",
        "Project the sample's misstatement: its misstatement over its book value, times the book value of the remainder it was drawn from. Add the key items' misstatement for the total likely misstatement, and compare with tolerable.",
      ],
      asks: [
        { label: "Aging total", row: "aging total" },
        { label: "A/R per the trial balance", row: "A/R per trial balance" },
        { label: "Customer with a credit balance", row: "credit balance: Summit Loop Racing" },
        { label: "Allowance required", row: "allowance required (aging as loaded)" },
        { label: "Allowance recorded", row: "allowance recorded" },
        { label: "Allowance short by", row: "allowance short (aging as loaded)" },
        { label: "Key items", row: "key items" },
        { label: "Key-item misstatement", row: "key-item misstatement" },
        { label: "Customers whose differences count", row: "misstatements counted (timing and customer error left out)" },
        { label: "Projected misstatement", row: "projected misstatement (aging as loaded)" },
        { label: "Total likely misstatement", row: "total likely misstatement (aging as loaded)" },
        { label: "Below tolerable?", row: "below tolerable" },
      ],
    },
    inNoesi: {
      procedures: ["ar.listing_tie", "ar.confirmations_nonstatistical"],
      steps: [
        DEMO_START,
        "**Sources & Mappings:** the A/R Aging Summary loads **raw** from QuickBooks' export, footed against its TOTAL row.",
        "**Coverage:** see that the nonstatistical confirmation method is the one in the audit, and the other methods are left out with a reason.",
        "**Runs & Findings:** read **ar.listing_tie**: the aging against the ledger, the credit balance, and the allowance recomputed.",
        "Read **ar.confirmations_nonstatistical**: key items, sample, the misstatements counted, the projection, and the comparison with tolerable.",
      ],
    },
    keyModule: "Revenue and receivables",
    noesi: {
      coverage: "partial",
      summary: "Noesi ties the aging to the ledger, recomputes the allowance, and evaluates the confirmation results the team recorded.",
      does: [
        "Loads QuickBooks' A/R Aging Summary raw and foots it.",
        "Finds the difference with the ledger and any credit balances.",
        "Recomputes the allowance from the partner's rates, and projects the confirmation sample, counting only client misstatements.",
      ],
      where: ["Workbench → Sources & Mappings", "Workbench → Coverage", "Workbench → Runs & Findings"],
      doesNot: [
        "It does not send confirmations or read the replies: the team records each reply and its classification.",
        "It does not explain why the aging disagrees with the ledger. Here the aging was run before a year-end write-off; re-running it is the client's job, and the corrected figures are in the key for discussion.",
        "It does not read aging exports grouped by sub-customer yet; that layout is refused, not guessed.",
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
        "It ties Unpaid Bills to the trial balance's Accounts Payable balance; with no General Ledger export it cannot show the ledger's detail behind that balance.",
        "It cannot inspect an invoice, ask the supplier, or judge whether a payment was authorized. A finding is a lead; the follow-up is yours.",
      ],
    },
  },

  {
    n: 6,
    slug: "cash",
    title: "Cash",
    phase: "Fieldwork",
    question: "Is the cash at year end really there, counted once, in the right period?",
    minutes: 40,
    objectives: [
      "Refoot a bank reconciliation and trace its items to the bank's next statement",
      "Find an outstanding check that never clears and one that clears at another amount",
      "Test transfers between accounts for cash counted twice",
    ],
    sections: [
      {
        heading: "The reconciliation is the client's; the test is yours",
        blocks: [
          { p: "A bank reconciliation explains the difference between the bank's balance and the books' at year end: checks written but not yet cashed (**outstanding checks**) and deposits made but not yet credited (**deposits in transit**). Refoot it first: the bank balance adjusted for its items must equal the book balance adjusted for its own." },
          { p: "Then test the items against the bank's statement for the weeks after year end, the **cutoff statement**. An outstanding check should clear soon, at the amount listed. A deposit in transit should arrive within a few days." },
          { watch: "An outstanding check that never clears may never have been sent, and the cash it \"spent\" may be sitting in the account, or gone somewhere else." },
        ],
      },
      {
        heading: "Transfers and kiting",
        blocks: [
          { p: "A transfer between two of the client's accounts leaves one and arrives in the other. If the books record the arrival before the year end but the departure after it, the same cash sits in both accounts at year end. That pattern is called **kiting**, and it overstates cash." },
          { p: "For each transfer near year end, compare four dates: disbursed and received, per the books and per the bank. Received in this year while disbursed in the next is the exception." },
        ],
      },
      {
        heading: "Kestrel's cash",
        blocks: [
          { kestrel: "Kestrel has two accounts at First Prairie Bank: checking and payroll checking. QuickBooks prints its reconciliation reports as PDF; the case gives them as spreadsheets. The bank's cutoff statement and the auditor's transfer schedule are in `bank/` and `auditor/interbank_transfers.csv`. The partner's policy says how many days a deposit may take to clear." },
        ],
      },
    ],
    standards: [
      ["AU-C 330", "Performing audit procedures in response to assessed risks"],
      ["AU-C 500", "Audit evidence, including information obtained from a third party such as a bank"],
      ["AU-C 240", "The auditor's responsibilities relating to fraud, such as kiting"],
    ],
    check: [
      { q: "Transfer T-0701 is recorded as received in the books on the last day of the year and as disbursed the next day. What is wrong?",
        options: ["Nothing; transfers net to zero", "The same cash sits in both accounts at year end, so cash is overstated", "The bank made an error", "Only the payroll account is affected"],
        answer: 1,
        why: "Receiving in one year and disbursing in the next counts the money twice on the year-end balance sheet." },
      { q: "An outstanding check has not cleared two weeks after year end. What next?",
        options: ["Nothing; it will clear", "Follow up: find out whether it was sent, to whom, and why it has not been cashed", "Remove it from the reconciliation", "Book it as revenue"],
        answer: 1,
        why: "A check that never clears may never have been mailed. The follow-up tells you whether the cash really left." },
    ],
    byHand: {
      files: ["quickbooks/Checking_Reconciliation.xlsx", "quickbooks/Payroll_Checking_Reconciliation.xlsx", "bank/first_prairie_xxxx2208_2026-07-01_to_2026-07-15.csv", "auditor/interbank_transfers.csv", "the Policies table in the case README.md"],
      intro: "Refoot both reconciliations, test their items against the cutoff statement, and test the transfers.",
      steps: [
        "For each reconciliation, note the statement ending balance and the book balance. Refoot: bank plus deposits in transit less outstanding checks must equal the book balance.",
        "Trace each outstanding check to the cutoff statement. Note any that has not cleared, and any that cleared at a different amount.",
        "Trace each deposit in transit to the cutoff statement. Count the days it took and compare with the policy.",
        "For each transfer in `interbank_transfers.csv`, compare the books' and the bank's disbursed and received dates with the year end.",
      ],
      asks: [
        { label: "Checking: statement ending balance", row: "checking: statement ending" },
        { label: "Checking: book balance", row: "checking: book balance" },
        { label: "Does the checking reconciliation refoot?", row: "checking: reconciliation refoots" },
        { label: "Payroll: book balance", row: "payroll: book balance" },
        { label: "Check that did not clear", row: "check 4421 did not clear by 07-15", key: "part1.cash.bank_reconciliation.outstanding_check_not_cleared_by_07-15.0.check" },
        { label: "Did check 4425 clear at another amount?", row: "check 4425 cleared at another amount" },
        { label: "Deposit in transit that cleared slowly", row: "deposits in transit cleared slowly" },
        { label: "Transfer T-0701", row: "transfer T-0701" },
        { label: "Transfer T-0630", row: "transfer T-0630" },
      ],
    },
    inNoesi: {
      procedures: ["cash.bank_reconciliation", "cash.interbank_transfers"],
      steps: [
        DEMO_START,
        "**Sources & Mappings:** the reconciliations, the cutoff statement and the transfer schedule load as files **prepared by hand** from the case files. QuickBooks gives its reconciliation report only as PDF, which the Workbench does not read yet.",
        "**Runs & Findings:** read **cash.bank_reconciliation**: each account refooted, and findings for the check that did not clear, the check that cleared at another amount, and the slow deposit.",
        "Read **cash.interbank_transfers**: the exception on the transfer counted in both accounts.",
      ],
    },
    keyModule: "Cash",
    noesi: {
      coverage: "partial",
      summary: "Noesi refoots each reconciliation, traces its items to the cutoff statement, and tests transfers for cash counted twice.",
      does: [
        "Refoots each account's reconciliation from its items.",
        "Traces outstanding checks and deposits in transit to the cutoff statement, flagging checks not cleared, checks cleared at another amount, and deposits slower than the policy.",
        "Compares each transfer's four dates and flags one received this year and disbursed next.",
      ],
      where: ["Workbench → Sources & Mappings", "Workbench → Runs & Findings"],
      doesNot: [
        "It does not read QuickBooks' reconciliation report, which QuickBooks gives only as PDF: the reconciliation is loaded as a prepared schedule (roadmap C).",
        "It does not obtain the cutoff statement or a bank confirmation: the auditor gets them from the bank.",
        "It does not decide what a check that never cleared means: the follow-up is yours.",
      ],
    },
  },

  {
    n: 7,
    slug: "inventory",
    title: "Inventory",
    phase: "Fieldwork",
    question: "Is the stock on the listing really there, in the quantities shown, at the right cost?",
    minutes: 40,
    objectives: [
      "Trace the count to the listing both ways, and set aside a void tag",
      "Tell a counting error from stock correctly left off the listing",
      "Project a pricing sample to the whole listing",
    ],
    sections: [
      {
        heading: "Count to listing, and listing to count",
        blocks: [
          { p: "The auditor attends the year-end count and keeps a record of the tags. Afterwards the tags are compared with the client's final inventory listing in both directions. **Count to listing** tests completeness: everything counted should be on the listing. **Listing to count** tests existence: everything listed should have been counted." },
          { p: "Every tag must be accounted for, including **void** tags, which are set aside with a reason, not dropped." },
          { watch: "Not every difference is an error. Stock counted but not listed may belong to someone else, such as consignment goods held for a supplier, and be correctly excluded. Find out before you adjust." },
        ],
      },
      {
        heading: "Pricing",
        blocks: [
          { p: "Quantities are half the balance; cost is the other half. For a sample of items, compare the recorded unit cost with the supplier's invoice. Project the sample's net misstatement to the listing, and compare with the tolerable misstatement for inventory." },
        ],
      },
      {
        heading: "Kestrel's inventory",
        blocks: [
          { kestrel: "Kestrel's Inventory Valuation Summary comes straight from QuickBooks. The count tags are in `client/count_tags_2026-06-30.csv`, and the pricing sample, with the vendor invoice for each item, is in `auditor/pricing_tests.csv`." },
        ],
      },
    ],
    standards: [
      ["AU-C 501", "Specific considerations for selected items, including attendance at the physical inventory count"],
      ["AU-C 530", "Audit sampling, including projecting misstatements"],
      ["AU-C 450", "Evaluating misstatements identified during the audit"],
    ],
    check: [
      { q: "An item was counted but is not on the listing. It is consignment stock held for a supplier. What is it?",
        options: ["An understatement to book", "Correctly excluded: the goods belong to someone else", "A void tag", "An overstatement"],
        answer: 1,
        why: "Consignment goods are not the client's inventory. Leaving them off the listing is right." },
      { q: "An item is on the listing but was not counted, because it shipped before the count. What does that suggest?",
        options: ["The count was wrong", "The listing still carries goods already sold: inventory overstated and cost of sales understated", "Nothing", "The supplier is at fault"],
        answer: 1,
        why: "Goods shipped but not relieved from inventory stay on the listing at cost. That is an existence error." },
    ],
    byHand: {
      files: ["quickbooks/Inventory_Valuation_Summary.xlsx", "client/count_tags_2026-06-30.csv", "auditor/pricing_tests.csv", "the Policies table in the case README.md"],
      intro: "Trace the count to the listing both ways, then evaluate the pricing sample.",
      steps: [
        "Foot the Inventory Valuation Summary and compare with its TOTAL row.",
        "Count the tags, including the void one. Set the void tag aside.",
        "Total the counted quantity for each SKU across all its tags and compare with the listing's quantity.",
        "List the SKUs that are listed but have no tag, and the SKUs that have a tag but are not listed.",
        "In `pricing_tests.csv`, total the recorded cost of the sample, and the net difference between recorded and audited cost.",
        "Project the net difference: over the sample's recorded cost, times the listing total.",
      ],
      asks: [
        { label: "Listing total", row: "listing total" },
        { label: "Tags, including the void one", row: "tags (loaded + void set aside)" },
        { label: "SKU with a quantity difference", row: "quantity differences" },
        { label: "Listed, not counted", row: "listed, not counted" },
        { label: "Counted, not listed", row: "counted, not listed" },
        { label: "Pricing sample: recorded cost", row: "pricing sample recorded" },
        { label: "Net overstatement in the sample", row: "net overstatement in sample" },
        { label: "Items priced wrongly", row: "items with differences" },
        { label: "Projected to the listing", row: "projected to the listing" },
      ],
    },
    inNoesi: {
      procedures: ["inventory.count_listing_trace", "inventory.pricing_projection"],
      steps: [
        DEMO_START,
        "**Sources & Mappings:** the Inventory Valuation Summary loads **raw** from QuickBooks' export, footed against its TOTAL. The count tags and the pricing sample load as files prepared from the case files; the void tag shows as set aside, with its reason.",
        "**Runs & Findings:** read **inventory.count_listing_trace**: quantity differences, listed not counted, and counted not listed.",
        "Read **inventory.pricing_projection**: the sample, the items priced wrongly, and the projection to the listing.",
      ],
    },
    keyModule: "Inventory",
    noesi: {
      coverage: "partial",
      summary: "Noesi traces the count to the listing both ways and projects the pricing sample, from QuickBooks' own valuation report.",
      does: [
        "Loads QuickBooks' Inventory Valuation Summary raw and foots it.",
        "Traces every tag to the listing and every listed item to the tags, with void tags set aside, not dropped.",
        "Projects the pricing sample's net misstatement to the listing.",
      ],
      where: ["Workbench → Sources & Mappings", "Workbench → Runs & Findings"],
      doesNot: [
        "It does not attend the count or inspect the goods: the tags are the auditor's record of what was seen.",
        "It does not decide whether stock counted but not listed belongs to the client; consignment goods are correctly excluded, and only inquiry tells you so.",
        "It does not read valuation reports grouped by category yet; that layout is refused, not guessed.",
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
        "Recomputes depreciation for every asset under the policy's convention (Kestrel's register is all straight line).",
        "Reports the share of additions vouched and any vouching exception the team recorded.",
      ],
      where: ["Workbench → Scope & Policies", "Workbench → Runs & Findings (PP&E)"],
      doesNot: [
        "It cannot see an asset: existence is physical inspection.",
        "It does not read invoices; it reads the team's vouching record of them.",
        "It does not judge useful lives, salvage values or impairment. It recomputes straight line and declining balance; other methods are listed as not recomputed.",
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
        "Note in **Sources & Mappings** that the trial balance (built from QuickBooks' two Trial Balance exports) and the July journal load raw from QuickBooks, and that the adjusting entries are the team's own schedule.",
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

export const COMING: Coming[] = [];
