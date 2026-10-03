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
| ~~B3~~ done | Role `Prior_statements` (line, amount as reported): prior ratios and averages (inventory turnover) without a comparative TB; given both, disagreements are flagged. Limit: account movements still need the TB's prior column, and revision impact does not yet mark analytics stale when this file changes. |

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
agent):** checks renumbered 4267–4433 without a break (June 4411–4426;
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
E1 pushed (a541e50, James's go); E3 done. Left in Phase 1: **E2**, James
working Oceanview by hand in his Workbench. Open decisions for James sit in
the parking lot (Benford minimum and default; "map all" offering raw files).

### Done on 2026-09-29
Codex's F1-F3 fixes; seldom-used accounts measured within the period;
duplicate bills needs the supplier's invoice number; `je_manual_sources`;
Codex's fraud-readiness review and its three fixes; tests not performed on
the Runs screen. Kestrel's fraud and journal-entry results agree with the key.

## Phase 2: the Kestrel Learn app
Starts after Phase 1. Details in `docs/LEARN-KESTREL-PLAN.md`: a copy of the
Learn app with the same layout; 13 modules, one per audit area (idea, by
hand, in Noesi, compare with the key); Kestrel's own documents; new videos,
scripts first, James approves scripts and credits before voicing.

## Parking lot
- Inventory matching (Codex, 2026-09-29): later count tags for an item can
  carry conflicting identity data that is dropped, and description
  differences are never a finding. Known limits; changing identity rules
  needs a policy decision, not a quick patch.
- Stale accruals, checks to vendors with no bills, employee/vendor shared
  addresses (the finish-line check lists them).
- PRODUCTION-READINESS P0/P1 (real-client use): after Phase 2 and a real user.
- Partner report sign-off (Codex's patch broke 17 tests; the print button covers it).
- Depth pass from AUDIT-FRAME-PLAN (Benford, declining-balance depreciation,
  sample projection for additions, adjusted covenants).
- Wiring the cycles into the structural layer (agreed as later, 2026-09-26).
- Benford minimum population (2 Oct): set at 1,000, from memory of Nigrini,
  source not verified. At 1,000 Kestrel tests nothing (3 "not tested" open
  findings on the demo); at 100 all three Kestrel groups fail. James to decide.
- Benford default-off: non-Kestrel engagements show "left out without a
  reason" until a default is chosen (HANDOFF_2026-10-02-fixes.md, M5).
- Lesson checker (C4): accepts a number from another line of the same module.
- Open from the 2 Oct review: L1-L3, L5, L6, check runs with no bank-account
  column, "Paycheck" name unverified (HANDOFF_2026-10-02-fixes.md "Not done").
- Second round of 2 Oct fixes (C1-C3) committed without a second-agent
  check, by James's decision: no more check rounds.
- Sources: "map all" offers the raw files a built schedule was made from
  (Kestrel: both Trial Balance exports and Unpaid Bills). One click now maps
  and confirms them (before D9 stage 3 they waited at approval); loading
  still needs its own step. Seen 2 Oct; leave such files out of "map all".
- Oceanview's offline scripts (run_full.py, run_noesi.py, workflow_full.py)
  still call the signing key and the lock removed in D9 stage 2, so they do
  not run; the Workbench's Oceanview loader (load_workbench.py) was fixed.
- Studio's Harborline lessons still teach chairs, locks and concurrence.
- apps/learn-kestrel-streamlit/learn.html is a built page that still shows
  Kestrel's old June check numbers (renumbered 2 Oct); rebuild it if that
  app is kept.
- Regenerating Kestrel rewrites six .xlsx files with identical cell values
  but different bytes (openpyxl version); harmless, seen 2 Oct.

## Rules
- Never fit the engine to a case; test fixes on invented data.
- Oceanview content never enters the public repo.
- One of Claude or Codex works at a time; one review at the end of a batch.
- Ask James before any push.
