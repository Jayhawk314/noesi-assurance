# Open items

One list of what still needs doing across noesi-assurance, noesi-vice-keys
(Starlight) and komposos-labs-videos. Each item records whether it was checked or
only copied from an older note. Move an item to "Closed" with its date and commit
when it is done; never delete it.

Last updated 27 Nov 2026.

## 1. Waiting on James

| # | Item | Why it is open |
|---|------|----------------|
| 1.1 | Push noesi-assurance `main` | Claude Code's permission check blocked the push. |
| 1.2 | Push noesi-vice-keys `main` to noesi-starlight | Same. |
| 1.5 | Harborline is in this public repository (39 tracked files: `case-studies/harborline-marine`, the Studio course and its videos) | Checked 27 Nov: github.com/Jayhawk314/noesi-assurance answers publicly. James: Harborline is too close to the copyrighted Oceanview case and is not for others. Keep it, move it to a private repository, or remove it (it stays in the public history unless that is rewritten). |

## 2. Known limits, kept by design

| # | Item | Notes |
|---|------|-------|
| 2.1 | Kestrel 175/177: PO overrun and July check 4433 "not in Noesi" | ROADMAP §C, closed 2 Oct. Reopen only with an export that links bills to POs and payments. |
| 2.2 | The search checks a recorded account's existence and credit, not the entry itself | Stated in the contract. An account named in a form the matcher does not read ("Acct 2200") is refused until the worksheet is corrected. |
| 2.3 | Benford leaves out amounts under 10 | Noesi's own choice, stated in the contract; no Nigrini source found for it. |
| 2.4 | `Prior_statements`: account movements still need the trial balance's prior column | ROADMAP §B3. |

## 3. Smaller gaps found 26 Nov

| # | Item | Notes |
|---|------|-------|
| 3.1 | A full keyboard-only pass of every screen | Checked 26 Nov: tabs, Flow Map boxes and arrows (arrows fixed). Forms and tables were not walked by keyboard. |
| 3.2 | Wiring the cycles into the structural layer | ROADMAP parking lot, agreed as later (26 Sep). |

## Closed

| Date | Item | Commit |
|------|------|--------|
| 25 Nov 2026 | Going concern judged on the adjusted figures | 8a863a9 |
| 25 Nov 2026 | Search for unrecorded liabilities with its own inputs; runs for Starlight | 8a863a9, 1b9a90c |
| 25 Nov 2026 | A QuickBooks recipe version change set aside only that file | 8a863a9 |
| 25 Nov 2026 | Kestrel demo provenance names the real source | 8a863a9 |
| 25 Nov 2026 | Starlight Room lines all in the interview notes; bartender June Moon | d8f399a |
| 25 Nov 2026 | M13 lesson lists internal control as a basic representation | 8a863a9 |
| 25 Nov 2026 | Videos m12 (1.1258 on screen) and m13 (opinion judgment) re-rendered; m13 re-voiced | 7c3434b |
| 25 Nov 2026 | Clicked replace + What Changed check | e690277 |
| 26 Nov 2026 | Flow Map draws the search's new inputs, vendor statements, bank confirmations and last year's statements; no unstyled chip for out-of-scope arrows | 693dee4, 3277bb4 |
| 26 Nov 2026 | What Changed: a stale run reads "finished, on the old file" | 693dee4 |
| 26 Nov 2026 | The search checks a recorded account against the trial balance (exists, credit covers it, credit shared across liabilities); two independent reviews, all findings fixed | 693dee4, 3277bb4, 03290c2 |
| 26 Nov 2026 | A revised `Prior_statements` (or any table a run read) marks the run stale in What Changed | 693dee4 |
| 26 Nov 2026 | Oceanview offline scripts run (the roadmap note was stale; `run_full.py` made safe to redirect; private, not in git) | — |
| 26 Nov 2026 | Studio's Harborline course: lock, chairs, concurrence and run review removed; procedures added since named with their cycle and date; fact-checked by a second agent | 4099ebc, 03290c2 |
| 26 Nov 2026 | Kestrel Learn page check numbers: rebuilt from source, byte-identical, so already current | — |
| 26 Nov 2026 | Sources "used to build" marking seen on screen | — |
| 26 Nov 2026 | Benford: 1,000 minimum and the conformity bands checked against Nigrini's sources | aba3eb3 |
| 26 Nov 2026 | Full clicked Workbench walkthrough; layout fixes; working paper names open items in words | d149315, 03290c2 |
| 26 Nov 2026 | Code Atlas refreshed; refresher no longer cuts an excerpt at a multi-line string | a90b06d |
| 26 Nov 2026 | Partner report sign-off: dropped under the supplement rule (no sign-offs, James 30 Sep) | — |
| 26 Nov 2026 | Studio clicked in a browser: course pages carry the course-date notice; journey's Collect no longer reads "32 of 10", Scope's next step names what is missing, the new-data banner says added or replaced | 986a5c9 |
| 26 Nov 2026 | Readiness names which procedures the open misstatements came from | 986a5c9 |
| 26 Nov 2026 | Every Workbench table scrolls in a narrow window (Coverage and Sources ran past the edge at 820 px); dark mode checked | 261e993 |
| 26 Nov 2026 | Flow Map arrows reachable and opened by keyboard (they were mouse only) | 4eaa348 |
| 27 Nov 2026 | komposos-labs-videos under git, local only (media ignored; blender and The Framifold are their own repositories) | a54245f |
| 27 Nov 2026 | Nine Harborline videos: outdated Noesi scenes cut; the September panel blurred where a kept scene shows it; Studio copies, minutes and course note updated (v1 kept) | 48cab72, 9002a88 |
| 27 Nov 2026 | Kestrel videos from 4 Oct spot-checked: 63 Workbench frames, all on the current screens; the 30 Sep silent previews moved to `kestrel/_stale_previews_2026-09-30` | 9002a88 |
