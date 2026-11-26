# Noesi roadmap

*Read this first. Direction set by Claude 2026-09-29 after reading the strategy and readiness documents; items built 2026-09-29 from the project's own plans
(LEARN-KESTREL-PLAN, AUDIT-FRAME-PLAN, CYCLES-ROLLOUT, the Kestrel run
findings, the Oceanview friction log) and checked against the code that
day. Every piece of work should map to a line below; anything else goes in
the parking lot.*

## Direction

The Workbench is a general audit tool: it supplements an audit and never
claims more than it can prove. It is calibrated on two full audits,
**Kestrel Valley** (public) and **Oceanview** (purchased, private), and
**never fitted to either**: what a case exposes is fixed generically and
tested on invented data.

**The goal (James, 2026-09-30; this replaces "Claude's determination" of
29 Sep that the goal was teaching):** Noesi-Assurance is finished software
that supplements a complete human audit, with a fraud and forensic
accounting module. The Workbench is that software. The case studies
(Kestrel, Oceanview, Harborline), the Learn apps and the videos are means to
that end: the cases calibrate the Workbench, Kestrel is also the public case
the Learn app and videos teach on. Videos come only after the Workbench is
finished.

**Why the project exists, and the rule that follows (James, 2 Oct 2026):**
James built Noesi both as a real product and to learn. He worked Amanda
Dalton's integrated audit practice case (Oceanview) for his accountancy
certificate in 2019 and found it useful. Harborline was modeled on that kind
of case; Oceanview was later bought so the software could practice on it
privately; Kestrel is a public remake that differs enough to be a demo and
lesson. So learning is a real purpose, alongside the product.

The rule for the Workbench: it is a supplement, not the audit. **Saying how
uncertain a result is, and where it could be wrong, matters more than locks,
sign-offs and holds.** Those belong to real audit software, which Noesi might
become later, not first. A check or a hold earns its place only if it makes
the supplement better: protecting the integrity of the data and the record,
or stopping a result from claiming more than it can show. Draft verdicts
(the opinion, the SAD conclusion) stay, but they must show their limits and
how they could be wrong.

The measurable check on the way there stays the same:

> **Every one of the 13 Kestrel Learn modules (LEARN-KESTREL-PLAN) runs in
> the Workbench and matches the answer key, from files as a learner would
> load them. Oceanview runs privately as the check that nothing is fitted
> to Kestrel.**

That check must stay green, but it is not the whole goal: work that makes
the Workbench a more complete audit supplement (coverage of the audit, the
fraud and forensic module, what it shows and what it says it could not
test) is on the path. Real-client readiness (PRODUCTION-READINESS P0:
logins, encryption, archives) is James's call when the Workbench is done.

**30 Sep 2026, page-by-page check of every tab (Claude):** fixed and
committed: coverage applies the auditor's include/leave-out choices
everywhere (the confirmation method Kestrel uses showed as "left out");
readable open items, amounts, procedure names and settings; A/P tie from the
trial balance (no GL export needed); performance materiality as a setting;
CSV downloads of findings and coverage; Flow Map for every cycle; findings
tagged with the assertion their procedure states. Accuracy check 162 of 164
(the 2 left wait on real QuickBooks exports). Open, needing James: see
docs/FULL-SYSTEM-STATUS-2026-09-30.md, "Decisions still yours".

1. **Phase 1: finish the Workbench** to the finish line above.
2. **Phase 2: the Kestrel Learn app** (a copy of the Streamlit Learn app),
   with new ElevenLabs videos when credits are available.

## Phase 1: finish the Workbench

### 0. The finish-line check (done 2026-09-29)
`case-studies/kestrel-valley-cycle/instructor/finish_line_check.py` seeds
the demo as `--demo` does and compares all 13 modules with the key; it
writes `FINISH-LINE-REPORT.md` and exits 1 on any unexplained difference.
**152 of 155 lines match, 0 unexplained** (the 3 left wait on QuickBooks exports, section C) (141 of 153 before the key
decisions below). Fixed from it: quick ratio
(cash and receivables only), allowance reported to the cent, and the
demo's policies (movement rule "or", manual journal sources, holidays).
Also fixed, from Codex's audit: a confirmed credit balance no longer enters
the confirmation sample; one reconciliation item covers one transfer.

Decided (James, via Codex, 2026-09-29): the key now carries Ridgeback's
as-loaded figures (allowance 6,887.38; projection 914.41) beside the
re-run-aging ones, labelled; the key's A/R ratio is sales to year-end net
receivables (16.41), the engine's metric. The checker pins every known
difference to its exact Workbench value, so a moved value fails.
Known limit: `ar.confirmations_difference` still counts a confirmed credit
balance in its sample (Kestrel does not use that method).

What still differs, and where it goes:
- PO overrun, A/P subledger tie, unrecorded liability: section C.
- Checks without bills, employee/vendor shared address, stale accrual
  (no activity all year): parking lot (depth pass).
- SAD vs the completion procedure: fixed by B2 (the check now matches).

### A. Engine breaks Kestrel found that are still open
From `case-studies/kestrel-valley-cycle/instructor/NOESI-RUN-FINDINGS.md`.
Fixed already: K1, K2, K3, K5, K8, K13; K4, K6, K10, K11 (`4b4549c`).

| Item | What | Severity |
|---|---|---|
| ~~K4~~ done `4b4549c` | A file with no mapped fields still "loads" | Medium |
| ~~K6~~ done `4b4549c` | Count tags compared one by one, not summed per item | Medium |
| ~~K10~~ done `4b4549c` | Reconciling items without a check number cannot be matched | Medium |
| ~~K11~~ done `4b4549c` | An account with no cutoff statement reads as "did not clear" | Medium |
| ~~K7~~ done `02601eb` | Count descriptions compared with listing descriptions | Low |
| ~~K9~~ done `02601eb` | Movement threshold rule (AND/OR) not a policy | Low |
| ~~K12~~ done `02601eb` | Confirmation projection population | Low |
| ~~K14~~ done `02601eb` | Payables-only procedures show in a cycles-only scope | Low |

### B. Engine gaps Oceanview found that are still open
From the private friction log and CYCLES-ROLLOUT §6.

| Item | What |
|---|---|
| ~~B1~~ done | Policy `clearly_trivial_pct` (5% unset), one rate for the SAD, concurrence and revision impact; set on the Scope screen. |
| ~~B2~~ done | The SAD carries the evaluated misstatement schedule (signed, by line) and cannot conclude "immaterial" while a line reaches materiality; the schedule's "material" verdict is no longer counted as one more misstatement. |
| ~~B3~~ done | Role `Prior_statements` (line, amount as reported): prior ratios and averages (inventory turnover) without a comparative TB; given both, disagreements are flagged. Limit: account movements still need the TB's prior column. (Revision impact now marks the analytics stale when this file changes: 26 Nov 2026.) |

### C. QuickBooks imports
30 Sep 2026 (Claude): real exports taken from James's QuickBooks Online
Accountant company, holding a few invented Kestrel-style transactions
(`tests/fixtures/quickbooks/kestrel_qbo/`). Not committed or pushed yet.

- ~~C1~~ done (local). Journal recipes, default layout and with Created on /
  Created by, built on the real export; entries named by date, type, Num and
  name, told apart by QuickBooks' transaction ID when two would share a name.
- C2. Trial balance, A/R aging summary and inventory valuation recipes done
  (local), plus a builder joining this year's and last year's Trial Balance
  exports (QuickBooks exports one date per report). Kestrel's files
  regenerated in the real layouts and loaded raw by the demo seed: the
  finish-line check is 162/164, 0 unexplained, as before.
  **Open:** the bank reconciliation. QuickBooks offers the Reconciliation
  Report only as PDF (no Excel), so its import needs the PDF (James to save
  one from the reconciled checking account) and stays hand-prepared.
- Found on the real files and fixed: QuickBooks' Excel titles abbreviate
  months ("As of Jun 30, 2026") and whole-month periods name no day
  ("April-June, 2026"); both read as undated, so a real General Ledger was
  refused by the A/P tie. Coverage now counts a trial balance's statement line
  as supplied by the line mapping (a QuickBooks trial balance has no line
  column).
- Still open from C: PO overrun and unrecorded liability (the 2 finish-line
  lines): they need bills linked to POs and payments, which none of these
  reports carry.
- **C closed 2 Oct 2026 (James):** the real exports in
  `tests/fixtures/quickbooks/kestrel_qbo/` are all the QuickBooks material
  there is; no QuickBooks company holds a complete Kestrel set to export
  more from. So: the bank reconciliation stays a hand-prepared schedule
  (QuickBooks gives that report only as PDF, and no real one exists to build
  a reader from; a reader built from a guessed layout would be fitting, not
  testing). The PO overrun and the unrecorded liability stay as known gaps,
  pinned in the finish-line check as "not in Noesi" with their reasons.
  Reopen C only if a real Reconciliation Report PDF, or an export linking
  bills to POs and payments, becomes available.

### D. Screens
Checked: cycles and policies, period start, and the Draft Opinion screens
exist. The Runs screen shows tests not performed (2026-09-29).

Added 2026-09-30 (James), from `docs/WORKBENCH-GAPS-2026-09-30.md` items 1-4:
what stops a learner finishing Kestrel in the Workbench.
- D1. Coverage: exclude or include a procedure, with a required reason
  (partner). Without it the lock cannot be reached from the screens.
- D2. Lock & Export: readiness blockers in plain words, each linked to the
  tab that clears it.
- D3. Materiality on Planning & Risk: benchmark, percentage, amount and
  reason; performance materiality and clearly trivial shown beside it.
- D4. Completion checks and stages: reopen (undo). The sign-off and the
  required notes built on 30 Sep were removed the same day (James: Noesi is a
  supplement to an audit, not audit software; no sign-offs or approval steps).

D1-D4 done 2026-09-30 (7cfb3fe). Added the same day (James: "complete the
other roadmap things, toward the videos"):
- D5. The accuracy check compares every line of the SAD's schedule (was the
  largest only). Done: 157/160, 0 unexplained.
- D6. SAD page: the headline counts disposed findings only, and says so
  beside the schedule; an open conclusion is no longer shown green (gap 9).
- D7. Runs & Findings: filter by procedure and disposition, latest run only
  (earlier runs counted when hidden), select several and dispose each with
  one note (concurrence still one by one), evidence per finding (gap 4).
- D8. Working paper before the lock: a DRAFT, marked, unsigned, never an
  export; saved as an HTML file, since a link cannot carry the session (gap 5).

Dropped 30 Sep (James): the other gaps (Flow Map, undo on Sources/Team,
activity log, evidence request status, fraud-risk button). **Rule: Noesi is a
supplement. Build only what tests client data or shows what the tests found
and could not test. No sign-offs, signatures, approval or file-management
features.**

### D9. Remove the approval features (James decided 1 Oct 2026: remove)
The supplement rule above. Three stages, each finished, tested and checked
against the finish line before the next:
1. Run review/approve (`review_run`, run statuses reviewed/approved),
   disposition and risk concurrence (`concur_disposition`, `concur_risk`,
   `requires_concurrence`), and "mark done" on stages and completion checks:
   out of the service, API and screens. Who ran each test, and when, stays
   on record. The lock's readiness gates that read them go too.
   **Done 1 Oct 2026:** service, API, readiness, persistence, screens,
   manual and tests (530 pass; finish line 162/164). Seen on screen: Runs &
   Findings, SAD & Completion, Planning & Risk (the risk table with rows was
   not seen: the demo records no risks). DB columns (reviewed_by,
   approved_by, concurred_by) stay unused so old records still read; runs
   reviewed or approved before today keep that status.
2. The signed lock, unlock and signed packet (`lock`, `unlock`,
   `verify_lock`, `_require_unlocked` everywhere): removed. The engagement
   record stays downloadable, unsigned. Evidence digests (files and
   datasets) stay: they prove the data, not a sign-off.
   **Done 2 Oct 2026:** lock, unlock, signatures, key store and the
   cryptography dependency gone; the record (packet v4, unsigned, with its
   manifest and digests) exports any time and is journaled; migration 12
   reopens locked engagements (old lock rows kept as history); Lock &
   Export is now Export; Studio's Review and Sign-off stages replaced by
   Export (stage 1 had broken Studio; fixed here). 518 tests pass; finish
   line 162/164. Seen on screen: Export tab, export and working-paper
   endpoints on the full demo, Studio journey. Not changed: Studio's
   Harborline Learn lessons still teach lock and concurrence.
3. Chairs: one user per engagement. `assign_team`, the X-Acting-Principal
   switcher and role checks go; proposing and approving a mapping become one
   "confirm mapping" step (checking the columns map right is a data check,
   not a sign-off). About 52 test files assign chairs and 34 approve
   mappings. The finish-line line "team: partner, preparer, reviewer" and
   Learn module 1's "three chairs" section are reworded with it.
   **Done 2 Oct 2026 (Claude, local, not reviewed by a second agent):**
   role checks, `assign_team`, the team route, the X-Acting-Principal header
   (now ignored), the readiness team gate and the mapping separation check
   are gone; `confirm_source_mapping` maps and confirms in one step; a
   mapping proposed before today can still be confirmed (`confirm_pending`).
   The real count was 20 test files, not 52. Workbench and Studio lose the
   chair switcher and the Team tab; manual ch. 1, 3, 7, 8 and Learn module 1
   reworded; the finish-line line now reads "one user on record" (the Learn
   key file regenerated: that line only). 529 tests pass; finish line
   162/164, 0 unexplained; check-lessons passes; the three apps build. Seen
   on screen: engagement list and Sources & Mappings on a throwaway Kestrel
   demo (33 mappings confirmed, header shows the user). Not changed:
   Studio's Harborline lessons still teach chairs; `require_separation` and
   `ingest.approve_mapping` stay as unused domain helpers; the DB keeps the
   `principal_assignment` table and the stored status 'approved'.

### D10. Forensic tests (James decided 1 Oct 2026: all three, extend the key)
Done 1 Oct (c13ba96): `forensic.check_number_sequence`,
`forensic.vendor_employee_match`, `forensic.benford_first_digit`, general to
any client, tested on invented data. Open: Kestrel's key lines for them.
Kestrel's Journal numbers its checks with 16 gaps the generator left by
accident (4142-4390 and short runs after 4390); the case's numbering must be
made sequential, keeping every check number the key names, before a
planted gap means anything. Plant with it: one vendor matching an employee
by bank account, and the E3 schemes below.
**Kestrel lines done 2 Oct 2026 (Claude, local, not reviewed by a second
agent):** checks renumbered 4266–4433 without a break (June 4411–4426;
4421, 4425, 4429, 4433 kept; four routine July checks added), one planted
gap 4422–4424; a vendor named after employee E08, Owen Pike Hauling
(5,925.00, freight budget moved from Velo, trial balances unchanged). **By
name, not bank account:** QuickBooks' Vendor Contact List carries no bank
account, so a bank-account match cannot come from Kestrel's exports. Key
lines in answer_key_part3.json `forensic` and answer_key_payables.json
`vendor_employee_match`; check_key.py re-derives both from the files
(21/21); five new finish-line lines all match (167/169, 0 unexplained).

### E. Close-out
- E1. Push to GitHub (James approves).
- E2. James works Oceanview by hand in his Workbench (loaded 2026-09-29);
  anything he hits goes to the private friction log, then to section B.
  **Engine pass done 2 Oct 2026 (Claude, Run 4 in the private log):** the
  full Oceanview audit runs on the current product (one user, export
  verified offline); readiness holds only on the three follow-ups the case
  gives no evidence to close, as in Runs 2-3; the forensic check sequence is
  clean on a second, independently written case. No engine defect found.
  The hand pass stays James's, for learning; it is not a product blocker.
- E3. Decided 1 Oct 2026: add both schemes (self-approved payments,
  round-tripped money) to Kestrel, the public case, with key lines.
  **Done 2 Oct 2026 (Claude, local, not reviewed by a second agent):**
  - Engine: new role `Payment_approvals` and procedure
    `forensic.self_approved_payments` (payables): an approval or signature
    log kept apart from the payment register, as such evidence arrives; it
    lists payments approved by their preparer and payments with no approver.
    Tested on invented data.
  - Engine fix: the round-trip test named the client "Rockwood" (an old
    case) for every client. It now uses a neutral name. This changed no
    result: a payment's outflow ends at a vendor node no flow leaves, so
    every leg of a round trip must be in Value_flows (stated in the code).
  - Kestrel: `auditor/check_signatures.csv` (96 checks; Dana Merritt
    prepared and signed the three DM Consulting checks) and
    `auditor/flow_of_funds.csv` (Kestrel → Gallatin Display Works →
    Summit Loop Racing → Kestrel, 9,800, May 2026). Trial balances
    unchanged. Key lines in answer_key_payables.json; check_key.py 24/24;
    finish line 172/174, 0 unexplained (five new lines match).
  - `ap.segregation_of_duties` stays partial on Kestrel: QuickBooks'
    payment exports carry no approver; the new procedure reads the log.

**Order:** A and B now (no outside dependency) → D1-D4 → E1 → C when exports arrive
→ E2/E3 alongside. Phase 1 is done when A, B, C and E are done.
**Status 2 Oct 2026:** A, B, D1-D10 done; C closed as it stands (above);
E1 pushed (a541e50, James's go); E3 done; E2's engine pass done (Run 4);
the depth pass and inventory count-tag follow-up are done; P0 2.3 backup and
restore is built with an offline command and independent review fixes.
**Phase 1 is done for the product.** James's hand pass of Oceanview is for
his learning, not a blocker. The 2 Oct review is closed (L2, L5, L6 fixed;
L1, L3 accepted). Phase 2's lessons exist; its videos wait for James's
script and credit approvals. Product work goes on with the depth pass
(parking lot, AUDIT-FRAME-PLAN).

**3 Oct qualification:** Later Workbench walkthroughs found and fixed real
UI and export defects after the statement above. Do not use “Phase 1 done”
as a current product-readiness verdict. The remaining verification order and
client-data boundary are in `docs/WORKBENCH-FINISH-MAP-2026-10-03.md`.
Videos remain paused until that Workbench finish map is checked.

**Current Phase 1 exit checks (3 Oct):** independent review of `04d3c5f`
and `c38d567`; a complete invented-data engagement through the ordinary
Workbench UI (upload, mapping, run, disposition, reopen, verified download);
and a screen-by-screen check for truthful tested/untested wording and usable
actions. Reproduce suspected issues before fixing them. The Kestrel 174/176
check stays a calibration check, not a replacement for these exit checks.
Client-data custody requirements remain in `docs/PRODUCTION-READINESS.md`.

**3 Oct follow-up, local and unreviewed:** `docs/WORKBENCH-FINISH-VERIFICATION-2026-10-03.md`
records the independent commit review, an invented-data UI journey, a
reproduced stale-result bug and local fix, an older-packet compatibility fix,
and an invented-store backup/restore drill. Full tests and the Kestrel
calibration pass. A second agent reviewed the new code and found three stale
result gaps, which received general fixes and invented-data regressions.
**25 Nov follow-up:** the clicked Vouchers replacement/What Changed check passes on a fresh invented
engagement, including rerun from What Changed and retention of the stale historical run. Reproducible
script, reviewed screenshots and limits: `docs/WORKBENCH-REPLACEMENT-CHECK-2026-11-25.md`.
Do not treat this bounded check or the earlier Phase 1 status as a product-readiness verdict.
**26 Nov follow-up:** a full clicked pass on the Kestrel demo (every tab, every Flow Map cycle, all five
disposition types with notes kept after reload, every Draft Opinion decision, export verified offline):
`docs/WORKBENCH-WALKTHROUGH-2026-11-26.md`, with its fixes and what it did not cover.

### Done on 2026-09-29
Codex's F1-F3 fixes; seldom-used accounts measured within the period;
duplicate bills needs the supplier's invoice number; `je_manual_sources`;
Codex's fraud-readiness review and its three fixes; tests not performed on
the Runs screen. Kestrel's fraud and journal-entry results agree with the key.

**Walkthrough 3 Oct 2026 (AGENT-WARNINGS §2):** every tab read on a fresh
Kestrel demo; list in docs/WORKBENCH-WALKTHROUGH-2026-10-03.md. Two possible
bugs (a raw `rockwood_structural` key on Draft Opinion and Export; the Fraud
tab counts Benford's "not tested" as findings) and stale "partner"/"Approved"
wording are to be fixed before videos. Layout and data-changing buttons were
not checked. **Both bugs and the stale wording fixed 3 Oct** (see that file).

## Phase 2: the Kestrel Learn app
Resumes only after the current Phase 1 exit checks above. Details in
`docs/LEARN-KESTREL-PLAN.md`: a copy of the
Learn app with the same layout; 13 modules, one per audit area (idea, by
hand, in Noesi, compare with the key); Kestrel's own documents; new videos,
scripts first, James approves scripts and credits before voicing.

## Parking lot
The single list of open items is `docs/OPEN-ITEMS.md`.
- **26 Nov 2026, from OPEN-ITEMS:** the search checks a `recorded_account` against the trial balance when one is
  loaded (the account must exist; a credit smaller than the liability is a lead); What Changed compares every table a
  run read, so a revised `Prior_statements` marks the analytics stale (and the two graph screens after a vouchers
  revision, which the Runs screen already did); the Flow Map draws the search's new inputs, vendor statements, bank
  confirmations and last year's statements; the stale-run status reads "finished, on the old file". Invented-data
  tests; 656 pass; Kestrel 175/177; Starlight passes (account 2200 covers the December sales tax).
- **Fixed 25 Nov 2026: going concern on the adjusted figures** (one of the 4 Oct "possible software bugs").
  `completion.going_concern_indicators` read the trial balance before the adjusting entries, though Learn module 12
  already taught "recomputed from the adjusted figures". When `Adjusting_entries` are loaded it now applies them
  (shared helper `apply_adjusting_entries`, also used by `fs.adjusted_trial_balance`), keeps the figures before them,
  names indicators the adjustments raise or clear, and refuses by name an entry it cannot apply (REFUSAL, like
  unclassified accounts; it counts as a possible scope limitation until dispositioned). Independent review found
  two defects, both fixed with regressions: last year's signs on a Dr/Cr side-column TB, and an account on two TB
  rows (which also gave `fs.adjusted_trial_balance` a false "does not foot"). Kestrel key: working capital
  61,622.55, net income 326,229.12, equity 177,972.55, current ratio 1.1258 (1.1291 before; still below 1.20, still
  "one point one three" in m12's narration, so no re-voice). Starlight: no indicators either way. 638 tests;
  finish line 175/177. m12 re-rendered 25 Nov with 1.1258 on screen and frames checked (7c3434b).
- **Built 25 Nov 2026: the search for unrecorded liabilities with its own inputs.** New roles `Subsequent_payments`
  (the register after year end) and `Unpaid_bills` (the year-end listing); `ap.unrecorded_liabilities_search` uses
  each when loaded and otherwise reads Payments and Vouchers as before (Kestrel unchanged, 175/177). A register row
  dated by year end, or undated, is refused by name. The inspection may carry `recorded_account` for a liability
  recorded outside payables (sales tax). `completion.subsequent_events` also reads the register, once per payment
  number. Starlight runs the search in Noesi: 10 payments selected, CHK-2372 (Gulf Restoration 8,740) unrecorded,
  asserted against its key. Tests on invented data (`tests/unit/test_unrecorded_liabilities_roles.py`). Independent review
  found six problems, five fixed with regressions: coverage, the executor and the engine now choose input sets by one
  rule (rows and mapped fields; the closest set named when none serves, so older inputs are told only what they lack);
  the subsequent-events review examines a register line once only when it repeats a Payments line exactly; a refused
  register row is not also an orphan; the new roles take no file from Payments or Vouchers (not guessed from headings;
  QuickBooks' Unpaid Bills stays Vouchers). Kept as designed and stated: an amount traced to another account is not
  re-proved.
- **Fixed 25 Nov 2026, the two remaining 4 Oct possible bugs.** (1) A QuickBooks recipe version change made coverage,
  readiness, the draft opinion and four other reads fail for the whole engagement (reproduced on the Kestrel demo);
  now the one file is set aside (`SourceNeedsRemapError`) and named in coverage's source notes until mapped again.
  (2) The Kestrel demo labelled all six hand-prepared files "from the QuickBooks export"; each now names its source.
  651 tests; finish line 175/177.
  **Not done:** Kestrel's check 4433 stays "not in Noesi". Kestrel has no auditor's inspection worksheet for July,
  and building one would add new auditor evidence to the public case.
- **Second Starlight review, 24 Nov 2026:** bank confirmations refuse missing/unreadable account, balance or date; zero remains a valid balance. Internal-control responsibility is a basic representation under AU-C 580.10(b). A fixed disclaimer keeps every basis reason but needs no further modification judgments. Work refusals remain visible; the auditor can record `not_material` when their possible effects do not justify modifying the opinion. Supplier references prefer the whole reference, using digits only as a fallback and refusing an ambiguous match only when used. Regression tests use invented data.
- **Fixed 24 Nov 2026 (James: "fix everything first"): refused representations.** The draft opinion had treated
  any refused representation as an automatic disclaimer. Now only the basic ones of AU-C 580.25 (paragraphs .10-.11:
  responsibility for the statements and internal control, all information provided, all transactions recorded) force a disclaimer; any
  other (for example related parties) adds the partner decision `effect_of_refused_representation` (not pervasive:
  qualified; pervasive or integrity in doubt: disclaimer). AU-C 580.10(b) includes internal-control responsibility, verified against the AICPA published standard on 24 Nov 2026.
  Source: https://downloads.ctfassets.net/rb9cdnjh59cm/6SZYDorUSdWM3sjctjPnOL/d2cb13701145f8699624298a1b875c8a/ps-au-c-sections.pdf Kestrel: the draft now proposes qualified, adverse or disclaimer; the key's view (integrity
  in doubt, given the related-party round trip) is still a disclaimer. Key part 3, finish line (175 of 177), Learn
  lessons and key, standalone learn.html, manual chapter 7, Code Atlas and README updated; 610 tests.
  **Done 25 Nov 2026 (James: credits approved):** video m13 rewritten (script v2, facts 14/14), scenes 1, 4 and 5
  re-voiced, re-rendered from new captures; m12 re-rendered for the adjusted going-concern figures. Both wired into Learn.
- **Candidate (Starlight, 24 Nov 2026):** `ap.unrecorded_liabilities_search` reads the Payments role as the payments
  after year end, so an engagement that loads the year's own payments (for the duplicate, sequence and approval tests)
  cannot also run the search. A separate role for subsequent payments would let one engagement do both. Not built.
- Deposit test hardened after the independent review (24 Nov 2026): cash matched by whole word (a cashier's check or a
  cash letter is not cash); undated cash and untyped rows are refused and counted, never grouped or dropped. 608 tests.
- **Engine gaps from the Starlight teaching case (`../noesi-vice-keys/starlight`), fixed
  24 Nov 2026 (James: "fix noesi-assurance too")**, generically and tested on invented data
  (`tests/unit/test_engine_gaps_2026_11_24.py`), never fitted to the case:
  (1) the round-trip screen's amount tolerance and window are settings
  (`value_flow_amount_tolerance_pct`, `value_flow_window_days`; 2% and 30 days when empty,
  so default runs and the golden bundle are unchanged); (2) payroll register tests read the
  account each payment went to (register field `bank_account`): accounts paid for more than
  one employee, including people missing from the master, and pay sent to an account other
  than the master's; (3) a new cash test, `cash.deposit_structuring` (role *Deposits*,
  policy `structuring_threshold`, optional `structuring_band_pct`; off until chosen): one
  day's cash deposits under the line that add up to more than it, and a pile-up just under
  the line. Tests 605 pass; Kestrel finish line unchanged at 174/176. **Built later the same day:**
  `ap.vendor_statement_reconciliation` (role *Vendor statements*) and `cash.bank_confirmation` (role *Bank
  confirmations*; 8.8's cash half), both off until chosen so existing engagements are unchanged.
- **Team roles, review and sign-off (James, 4 Oct 2026): maybe one day.** Noesi has one user per
  engagement and no preparer/reviewer/partner roles, review steps or sign-offs (decided 2 Oct: a
  supplement, not audit software; see THE-REAL-GOAL.md). If Noesi grows toward full audit software,
  these could come back as real features: separate logins per role, review notes, sign-off with a
  date, and locks after sign-off. Learn module 1 teaches the roles as audit knowledge and says the
  review happens in the firm, outside Noesi; update it if the features are added.
- ~~Inventory matching (Codex, 2026-09-29): later count tags for an item can
  carry conflicting identity data that is dropped~~ **fixed 2 Oct:** each
  later tag is compared with the item's first: a different model is a lead
  (`tags_disagree`), a different description alone is recorded
  (`tag_descriptions_differ`), as K7 does for count against listing.
  Kestrel unchanged (174/176).
- ~~Stale accruals, checks to vendors with no bills, employee/vendor shared
  addresses~~ **done** (checked 2 Oct: `accruals.recompute` stale accrual,
  `ap.payments_without_bills`, `payroll.register_tests` address match; each
  matches on the Kestrel finish line).
- **Codex depth review (docs/reviews/REVIEW-2026-10-02-depth-codex.md) fixed
  2 Oct:** a vouching row with no result is not vouched (1); a zero adjusted
  denominator is "not measurable after the adjustments" (2); the breach
  follows the adjusted figures and says its basis (3); an add-back needs its
  note (4); the trailing basis needs a real twelve months, day to day (5).
- **PRODUCTION-READINESS P0 2.3 done 2 Oct:** one verified backup zip carries
  the SQLite snapshot and exactly its named vault blobs; restore refuses a
  damaged/missing/mismatched database or vault and never overwrites a store.
  Offline `create`, `verify`, and `restore` commands are tested on invented
  data. Independent review fixed malformed manifests escaping as raw errors
  and a sibling `.part` file being overwritten. The manifest is unsigned, so
  it detects damage/mismatch, not deliberate whole-backup forgery. The
  readiness document is rewritten for the one-user, no-sign-off supplement;
  encryption and the other remaining local-use controls stay there.
- Partner report sign-off (Codex's patch broke 17 tests; the print button covers it).
- Depth pass from AUDIT-FRAME-PLAN (Benford, declining-balance depreciation,
  sample projection for additions, adjusted covenants). **Benford done**
  (D10). **Declining balance done 2 Oct:** double declining and 150% by
  name, plain "declining balance" with the policy
  `ppe_declining_balance_factor`; on the register's implied opening book
  value, never below salvage, no switch to straight line (stated limit).
  Tested on invented data (worked by hand). **Additions projection done
  2 Oct:** key items in full, the vouched sample below the threshold
  projected by ratio, likely misstatement against `ppe_tolerable_misstatement`
  (representativeness stated as a limit). **Adjusted covenants done 2 Oct:**
  each covenant measured again after the adjusting entries (a change in
  compliance is a finding), agreement add-backs with a note, and a
  trailing-twelve-month basis measured only on a twelve-month period.
  Kestrel: current ratio 1.1291 before, 1.1258 after (key line added;
  finish line 174/176). **The depth pass is done.**
- Wiring the cycles into the structural layer (agreed as later, 2026-09-26).
- **Batch review (docs/reviews/REVIEW-2026-10-02-batch.md) fixed 2 Oct:**
  M1 (a file or mapping from another engagement could be confirmed and
  loaded: now refused as not found); M2 (a voided check, lines with no
  amounts, joins its bank's run and is counted as voided, not missing; the
  QuickBooks void layout is the reviewer's understanding, not seen in a
  real export); M3 (nothing numbered anywhere is "not tested", never a clean
  result); L1 (the Journal is the check sequence's required input, payments
  the alternative); L2 (a disposal with cleared accumulated depreciation is
  not recomputed); L3 ("200%" read as 2; factors outside 1-3 refused); L4
  (approval logs grouped by payment, co-signed checks not flagged, missing
  preparer flagged); L5 (one-word names counted); L6 (first check 4266;
  the signature log is the year to 30 June; check_key checks first and
  last); L7 wording. Left as history: old engagements' `principal_assignment`
  rows still fill a display-only "reviewer" slot in readiness's team.
- **Benford decided 2 Oct (Claude, James: "you decide"):** the demo's
  minimum stays 1,000. **Checked 26 Nov 2026:** Nigrini's own 2012
  conference slides (ACFE, p. 10) say Benford "works best on datasets with
  > 1,000 records"; the mean absolute deviation bands (0.006 / 0.012 /
  0.015) match Nigrini (2012, table 7.1) as cited by independent papers. Leaving
  out amounts under 10 is Noesi's own choice, stated in the contract; no Nigrini
  source for it was found, so the code no longer attributes it to him. Below it the test says "not tested" rather than judge a hundred
  amounts on bands meant for large populations; a "fail" at 100 would be a
  false lead. The test is now **in by default** for every engagement, so it
  no longer reads "left out without a reason"; Coverage asks the auditor for
  the minimum, which stays the auditor's choice.
- Lesson checker (C4): accepts a number from another line of the same module.
- From the 2 Oct review: **L2 and L6 fixed 2 Oct** (masked numbers not
  compared and counted, phones on their last seven digits, first/last
  names joined; dead `requires_concurrence` removed, INDEPENDENT-REVIEW.md
  invariants 3-4 rewritten for one user and the unsigned record). **L5
  fixed 2 Oct** (contracts may name alternative input sets; the check
  sequence runs on the Journal alone; coverage says which set serves).
  **Accepted as stated limits (decided 2 Oct):** L1 (migration 12 reopened
  locked engagements with no journal line: it has already run on existing
  stores, and a line written now would carry the wrong date; the old lock
  rows remain as history); L3 (payments fall back to `payment_number` as the
  check number: QuickBooks' Bill Payment List puts the check number in Num,
  which maps there; a numeric internal ID would show as a gap, which the
  finding's wording already allows). Also: check runs with no bank-account
  column, "Paycheck" name unverified.
- Second round of 2 Oct fixes (C1-C3) committed without a second-agent
  check, by James's decision: no more check rounds.
- ~~Sources: "map all" offered the raw files a built schedule was made from~~
  **Fixed 2 Oct:** a schedule's source exports (named in its provenance) are
  marked "used to build …" and left out of "map all"; their own button still
  maps them. Tested on the Kestrel seed (the two Trial Balance exports and
  Unpaid Bills, nothing else). Seen on screen 26 Nov.
- ~~Oceanview's offline scripts do not run~~ **Checked 26 Nov:** run_noesi.py and
  run_full.py run (no lock or signing calls remain); workflow_full.py is a module
  run_full imports. run_full.py now writes UTF-8 so a redirected run does not fail.
- ~~Studio's Harborline lessons still teach chairs, locks and concurrence.~~ **Fixed
  26 Nov** (4099ebc, 03290c2); the Harborline videos still narrate them (OPEN-ITEMS 1.4).
- ~~apps/learn-kestrel-streamlit/learn.html shows old check numbers~~ **Checked 26 Nov:**
  rebuilt from source, byte-identical; already current.
- Regenerating Kestrel rewrites six .xlsx files with identical cell values
  but different bytes (openpyxl version); harmless, seen 2 Oct.

## Rules
- Never fit the engine to a case; test fixes on invented data.
- Oceanview content never enters the public repo.
- One of Claude or Codex works at a time; one review at the end of a batch.
- Ask James before any push.
