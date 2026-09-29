# Noesi roadmap

*Read this first. Built 2026-09-29 from the project's own plans
(LEARN-KESTREL-PLAN, AUDIT-FRAME-PLAN, CYCLES-ROLLOUT, the Kestrel run
findings, the Oceanview friction log) and checked against the code that
day. Every piece of work should map to a line below; anything else goes in
the parking lot.*

## Direction

The Workbench is a tool that **supplements any audit**. It is calibrated on
two full audits, **Kestrel Valley** (public) and **Oceanview** (purchased,
private), and **never fitted to either**: what a case exposes is fixed
generically and tested on invented data.

1. **Phase 1: finish the Workbench** against both audits.
2. **Phase 2: the Kestrel Learn app** (a copy of the Streamlit Learn app),
   with new ElevenLabs videos when credits are available.

## Phase 1: finish the Workbench

### A. Engine breaks Kestrel found that are still open
From `case-studies/kestrel-valley-cycle/instructor/NOESI-RUN-FINDINGS.md`.
Fixed already: K1, K2, K3, K5, K8, K13; K4, K6, K10, K11 (`4b4549c`).

| Item | What | Severity |
|---|---|---|
| ~~K4~~ done `4b4549c` | A file with no mapped fields still "loads" | Medium |
| ~~K6~~ done `4b4549c` | Count tags compared one by one, not summed per item | Medium |
| ~~K10~~ done `4b4549c` | Reconciling items without a check number cannot be matched | Medium |
| ~~K11~~ done `4b4549c` | An account with no cutoff statement reads as "did not clear" | Medium |
| K7 | Count descriptions compared with listing descriptions | Low |
| K9 | Movement threshold rule (AND/OR) not a policy | Low |
| K12 | Confirmation projection population | Low |
| K14 | Payables-only procedures show in a cycles-only scope | Low |

### B. Engine gaps Oceanview found that are still open
From the private friction log and CYCLES-ROLLOUT §6.

| Item | What |
|---|---|
| B1 | "Clearly trivial" is hard-coded at 5% of materiality (checked: `TRIVIAL_PCT` in `assurance_application`); firms set their own. Make it a policy. |
| B2 | Two misstatement summaries disagree (the SAD and `completion.uncorrected_misstatements`). Merge them. |
| B3 | Inventory turnover needs prior-year figures; allow prior-year statement figures as input. |

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
- Partner report sign-off (Codex's patch broke 17 tests; the print button covers it).
- Depth pass from AUDIT-FRAME-PLAN (Benford, declining-balance depreciation,
  sample projection for additions, adjusted covenants).
- Wiring the cycles into the structural layer (agreed as later, 2026-09-26).

## Rules
- Never fit the engine to a case; test fixes on invented data.
- Oceanview content never enters the public repo.
- One of Claude or Codex works at a time; one review at the end of a batch.
- Ask James before any push.
