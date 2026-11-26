# Open items

One list of what still needs doing across noesi-assurance, noesi-vice-keys
(Starlight) and komposos-labs-videos. Each item records whether it was checked or
only copied from an older note. Move an item to "Closed" with its date and commit
when it is done; never delete it.

Last updated 26 Nov 2026.

## 1. Waiting on James

| # | Item | Why it is open |
|---|------|----------------|
| 1.1 | Push noesi-assurance `main` (3fc61af, 8a863a9, 7c3434b, e690277) | Claude Code's permission check blocked the push. Run `git push origin main` in the repo. |
| 1.2 | Push noesi-vice-keys `main` to noesi-starlight (d8f399a, ae901f2, 1b9a90c) | Same. Confirmed 26 Nov: the remote's main is still 08e8174. |
| 1.3 | komposos-labs-videos has no version history | Not a git repo. The m12/m13 changes exist only on disk, with `_backup_2026-11-25_*` copies. Decide whether it becomes a repo. |

## 2. Real gaps, checked this session

| # | Item | Notes |
|---|------|-------|
| 2.1 | Flow Map does not draw `Subsequent_payments` or `Unpaid_bills`; the search's arrow still points at Payments | Flow Map work was dropped 30 Sep (ROADMAP §D). Fix only if the map is kept. |
| 2.2 | What Changed, "Runs built on the old file": a stale run shows status "completed" | True of the run but reads oddly beside "stale". Wording only. |
| 2.3 | The search takes the auditor's `recorded_account` at its word | Designed limit, stated in the contract: a payment the auditor traced to another account is not re-checked against that account. |
| 2.4 | Kestrel 175/177: PO overrun and July check 4433 "not in Noesi" | Kept on purpose (ROADMAP §C, closed 2 Oct). Reopen only with an export that links bills to POs and payments. |
| 2.5 | `Prior_statements`: revision impact does not mark analytics stale when that file changes | From ROADMAP §B3, stated as a limit. |

## 3. Carried from the roadmap, not rechecked 26 Nov

| # | Item | Source |
|---|------|--------|
| 3.1 | Oceanview's offline scripts (run_full.py, run_noesi.py, workflow_full.py) still call the signing key and the lock removed in D9, so they do not run | ROADMAP parking lot |
| 3.2 | Studio's Harborline lessons still teach chairs, locks and concurrence (removed from the product in D9) | ROADMAP parking lot, D9 |
| 3.3 | apps/learn-kestrel-streamlit/learn.html shows Kestrel's old June check numbers | ROADMAP parking lot. Rebuild it or retire that app. |
| 3.4 | Sources "used to build …" marking: tested on the seed, not checked on screen | ROADMAP parking lot, 2 Oct |
| 3.5 | Benford minimum of 1,000: the source page (Nigrini 2012) was never checked | ROADMAP parking lot, 2 Oct |
| 3.6 | Phase 1 exit checks: a full invented-data engagement through the Workbench UI, and a screen-by-screen wording check | ROADMAP §E, 3 Oct. Parts were done 3 Oct and 25 Nov; there is no full pass on record. |
| 3.7 | Wiring the cycles into the structural layer | ROADMAP parking lot, agreed as later (26 Sep) |
| 3.8 | Partner report sign-off | ROADMAP parking lot. Likely out of scope under the supplement rule (no sign-offs). |

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
