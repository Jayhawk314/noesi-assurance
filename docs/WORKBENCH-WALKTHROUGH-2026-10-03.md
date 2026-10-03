# Workbench walkthrough, 3 Oct 2026 (AGENT-WARNINGS §2 every-page check)

Claude, on a fresh `--demo` Kestrel store in a scratch folder (37 procedures
run). All twelve tabs were opened in Chrome and their text read. **How:**
page text via the browser, not screenshots; full screenshots kept timing out,
so **layout was not checked**. **Not clicked:** buttons that change data
(dispose, run, leave out, set, archive/delete, upload), "run details",
"evidence", the Flow Map's other cycle tabs, and Studio.

## Fixed the same day (Claude; tests on invented data; checked on a fresh demo
through the service, not yet seen on screen)
- 1: readiness now counts open findings by the procedure that found them
  (`by_procedure`); the Workbench and Studio show that, so the round trip
  reads `forensic.closed_value_flow: 1`. Finding uids are unchanged (the
  `rockwood_structural` domain stays inside them, and in the exported record).
- 2: the Fraud view keeps refusals apart ("ran but did not test", with the
  reason); Kestrel's fraud findings 60 → 57, Benford "not tested".
- 3, 4, 5, 6, 7: wording and amounts to the cent.
Still open: 8-13, and layout and data-changing buttons not checked.

## Possible software bugs (fix before videos)
1. **Raw internal key with the old case name on screen.** Draft Opinion and
   Export list an open item as
   `rockwood_structural|["directed_round_trip", 1, "entity:Kestrel Valley Cycle Supply, LLC"]`.
   The round-trip finding's uid starts with the domain `rockwood_structural`
   (`procedures_ap/structural.py:252`, `fusion.py:179`, `triage.py:94,138`,
   `unified.py:45`); the screens group open items by the uid's prefix.
   Changing the domain changes finding uids, so stored dispositions and the
   golden baselines need a plan. Not fixed.
2. **Fraud tab counts "not tested" as findings.** "Amounts that do not look
   natural — 3 findings (3 open)" are the Benford test's three refusals (each
   population is below the 1,000 minimum). The header's "60 findings" includes
   them. This overstates what the fraud tests found. Not fixed.

## Stale wording (one-user change)
3. "left out by the partner": Flow Map header badge and the Coverage intro.
4. "Approved engagement policies apply automatically via coverage." (Runs).

## Smaller display issues
5. Amounts not to the cent: `620.0`, `231.0`, `-36.0` (confirmations, pricing).
6. "overstatement positive: -36.0" for an understatement (pricing test).
7. "shares a address" (related-party matching).
8. Raw names shown to the user: `Trial_balance` etc. in the mappings table;
   `decisions_required`, `not_dated_report_date` in Draft Opinion and the
   working paper; readiness codes (`SELECTED_PROCEDURES_BLOCKED`) beside the
   plain words; the cycle `journal_entries` in "Not on the map".
9. The four forensic tests are "not on the map" (no Flow Map cycle).
10. "SAD & Completion" shows no completion section, only the SAD.
11. No backup button; backup is command-line only (by design for restore).

## Demo content gaps (matter for videos, not bugs)
12. The demo records **no risks**: Planning & Risk's table and the Fraud tab's
    risk section are empty, though the Fraud tab names the two presumed risks.
13. All 118 findings are undisposed, so dispositions and the SAD's disposed
    figures show zero unless done live.

## Checked and right
- SAD misstatement schedule shown: 15,650.37 / 5,335.82 / 10,614.55 / 300.00
  / 0.00, matching the final figures AGENT-WARNINGS quotes from the key
  (visual match, not a script check; the finish-line check covers them).
- Every mapping confirmed by the one user; rows set aside are explained.
- Coverage states each procedure's limits; blocked and partial procedures
  show as readiness items on Draft Opinion and Export.
- Working paper on the demo: no "Approved"; 33 mappings "confirmed"; "signed"
  appears only to say the record is unsigned.
