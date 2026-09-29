# Noesi roadmap

*Read this first. Every piece of work should map to a line below; anything
that does not goes in the parking lot, not into the Workbench. Updated
2026-09-29.*

## Direction

Noesi's Workbench is a tool that **supplements any audit**. It is
calibrated on two full audits, **Kestrel Valley** (public teaching case)
and **Oceanview** (purchased, private), and is **never fitted to either**:
a problem a case exposes is fixed generically and tested on invented data.

Two phases, in order:

1. **Finish the Workbench** against Kestrel and Oceanview.
2. **Then the Kestrel Learn app** (Streamlit), with new videos once
   ElevenLabs credits are available.

## Phase 1 — Finish the Workbench

Done means: both audits run end to end through the Workbench, their
results agree with the answer keys where the data allows, and wherever the
data does not allow a test, the Workbench says so rather than passing.

| # | Item | Status |
|---|---|---|
| 1.1 | Kestrel full audit runs through the Workbench and lands on the key's draft opinion | Done (demo; test_kestrel_demo) |
| 1.2 | Kestrel fraud and journal-entry tests agree with the key | Done 2026-09-29 (twins, duplicate bill, split bills, all six JE criteria; JE 1052 with `je_manual_sources`) |
| 1.3 | Oceanview full audit runs privately; gaps logged in its friction log, fixed generically | Done through run 3; loaded in James's Workbench for hand work |
| 1.4 | Honesty on screen: tests not performed are shown with the reason | Done 2026-09-29 (Runs screen) |
| 1.5 | Independent review of the engine changes | Done 2026-09-29 (docs/reviews/REVIEW-2026-09-29-fraud-readiness.md, all findings fixed) |
| 1.6 | Push local commits to GitHub | **Open** — James runs `git push origin main` |
| 1.7 | James works Oceanview by hand in the Workbench; what he hits goes into the Oceanview friction log | **Open** — James |
| 1.8 | Real QuickBooks exports (Journal, trial balance, aging, inventory, bank rec) and recipes built to them | **Open** — waits for real exports from James |
| 1.9 | Decide Kestrel's fraud coverage for teaching: add self-approved payments and a round-trip value flow to Kestrel, or teach those two lessons (F4, F7) on Harborline | **Open** — James's decision |

When 1.6–1.9 are done, Phase 1 is done.

## Phase 2 — Kestrel Learn app

Starts after Phase 1. The plan is in `docs/LEARN-KESTREL-PLAN.md`.

- Copy the current Noesi Learn Streamlit app for Kestrel (same layout; the
  case, documents, lessons and videos change). Harborline stays online by
  link and is never deleted.
- One module per audit area: the idea, by hand, in Noesi, compare with the
  key.
- New ElevenLabs videos, about 20 or more. Scripts first; James approves
  the scripts and the credits before any voicing.
- The fraud track moves to Kestrel according to decision 1.9.

## Parking lot (not now)

- Partner report sign-off (Codex's patch; broke 17 tests). The Draft
  Opinion print button covers the need for now.
- Other Workbench screen polish not needed by Phase 1's definition of done.

## Rules

- Kestrel calibrates the engine for all audits; never fit the engine to a case.
- Oceanview content (names, numbers, files) never enters the public repo.
- One of Claude or Codex works at a time; reviews come at the end of a
  piece of work, not in the middle.
- Ask James before any push.
