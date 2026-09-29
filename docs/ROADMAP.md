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

**What it is for now (Claude's determination, 2026-09-29):** the realistic
near-term use is teaching. So "finish the Workbench" has a concrete finish
line, not "any audit":

> **Every one of the 13 Kestrel Learn modules (LEARN-KESTREL-PLAN) runs in
> the Workbench and matches the answer key, from files as a learner would
> load them. Oceanview runs privately as the check that nothing is fitted
> to Kestrel.**

Work that does not move that line goes to the parking lot, however useful.
Real-client readiness (PRODUCTION-READINESS P0: logins, encryption,
archives) is not on this path yet.

1. **Phase 1: finish the Workbench** to the finish line above.
2. **Phase 2: the Kestrel Learn app** (a copy of the Streamlit Learn app),
   with new ElevenLabs videos when credits are available.

## Phase 1: finish the Workbench

### 0. The finish-line check (done 2026-09-29)
`case-studies/kestrel-valley-cycle/instructor/finish_line_check.py` seeds
the demo as `--demo` does and compares all 13 modules with the key; it
writes `FINISH-LINE-REPORT.md` and exits 1 on any unexplained difference.
**149 of 155 lines match, 0 unexplained** (141 of 153 before the key
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

### C. QuickBooks imports (waits for James's real exports)
Checked: only payables recipes exist today (bill payments, transactions by
vendor, unpaid bills, vendor list). Kestrel's Journal, trial balance, aging,
inventory and bank rec are hand-prepared in the demo seed.

- C1. A real QuickBooks Journal export, then the Journal import built to it.
- C2. Recipes for trial balance, A/R aging, inventory valuation, bank reconciliation.

### D. Screens
Checked: cycles and policies, period start, and the Draft Opinion screens
exist. The Runs screen shows tests not performed (2026-09-29). Nothing
further planned.

### E. Close-out
- E1. Push to GitHub (James approves).
- E2. James works Oceanview by hand in his Workbench (loaded 2026-09-29);
  anything he hits goes to the private friction log, then to section B.
- E3. Decide the fraud lessons Kestrel cannot teach (self-approved payments,
  round-tripped money): add those schemes to Kestrel, or keep those lessons
  on Harborline.

**Order:** A and B now (no outside dependency) → E1 → C when exports arrive
→ E2/E3 alongside. Phase 1 is done when A, B, C and E are done.

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

## Rules
- Never fit the engine to a case; test fixes on invented data.
- Oceanview content never enters the public repo.
- One of Claude or Codex works at a time; one review at the end of a batch.
- Ask James before any push.
