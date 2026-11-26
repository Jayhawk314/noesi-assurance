# Workbench walkthrough — 26 November 2026

The full clicked pass the 3 Oct exit checks asked for (ROADMAP §E), on the Kestrel demo
(`python -m workbench_api --demo`, a fresh store). Playwright drove the built Workbench UI.
The script was kept outside the repository; its steps are listed here so the pass can be repeated.

## What was clicked, and what happened

| Step | Result |
|---|---|
| Open every tab: Flow Map, Scope & Policies, Planning & Risk, Sources & Mappings, Coverage, Runs & Findings, Fraud, What Changed, SAD & Completion, Draft Opinion, Export | All eleven open. No page errors, no failed requests. |
| Flow Map: every cycle diagram (purchase-to-pay, revenue, cash, inventory, payroll, property/debt/equity, journal and completion) | Drawn; arrows count only procedures in scope; the search's arrows say what blocks it (the closest input set). |
| Sources & Mappings: "used to build" marking | The two Trial Balance exports and Unpaid Bills are marked "used to build …; not in map all". |
| Runs & Findings: one finding each disposed cleared, unadjusted, adjusted, waived, follow_up, each with a note | All five saved; the five notes are still there after a page reload. |
| Draft Opinion: record every decision it asks for, each with a reason | Four recorded (going concern, effect of the refused representation, pervasiveness of misstatement and of scope limitation); the fifth, the representation letter's date, says it is resolved by correcting the evidence, not by a decision. |
| Export: download the record (JSON) | 713 KB; `verify_packet` passes every check (receipts, run seals, manifest, packet digest, journal verified at export with 219 entries). |
| Screen text of every tab | No removed feature (lock, chairs, concurrence, review) and no raw readiness code shown as text. |

## Fixed from this pass

- The findings table clipped its last column; it now scrolls. Identifiers in tables broke mid-word
  ("occurrenc / e"); they now keep words whole.
- What Changed's two tables were unstyled (headers ran together); its refresh button, and Draft Opinion's
  refresh and print buttons, used a class with no style.
- The working paper printed readiness codes ("SELECTED_PROCEDURES_BLOCKED (6)"); it now names them in the
  screens' words.

## Checked afterwards the same day

- Studio (`/studio/`) clicked: course home, course map, fraud track, lesson 10 and the journey. Fixed: the
  journey's Collect stage counted every loaded role against Harborline's ten payables files ("32 of 10");
  Scope's next step read only "Set" when partial procedures lacked fields, not policies; the new-data
  banner said "replaced" for rows added.
- Dark mode (Flow Map, Runs & Findings, Draft Opinion) reads correctly.
- At 820 px wide, Coverage and one Sources table ran past the page edge; every table now scrolls inside
  its own box, and no table overflows on any tab.

## Not covered

- Keyboard-only use.
- Every control on every screen was not exercised: the bulk disposition form, run-only policy values,
  archive and restore (clicked on 3 Oct), and folder upload (3 Oct) were not repeated.
