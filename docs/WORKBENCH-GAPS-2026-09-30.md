# Workbench gaps, page by page (Kestrel), 30 Sep 2026

*Written by Claude for James, before building anything. Not yet reviewed by a second agent.*

## How this was checked

- **Read:** the code of every tab (`apps/workbench-ui/src/App.tsx`, `screens.tsx`, `screens/*.tsx`)
  and the server's full route list (`apps/workbench-api/workbench_api/server.py`, `_get`/`_post`).
- **Ran:** a separate Workbench on a fresh scratch folder with `--demo` (port 8399; James's data and
  running Workbench were not touched), then read what each tab shows through the API.
  Kestrel state seen: 31 runs completed, 109 findings (all undisposed), 0 risks, 45 procedures
  (31 executable, 6 partial, 8 blocked), 13 evidence requests, lock NOT READY.
- **Not done:** clicking through the tabs in a browser. What a tab shows is from the code and the
  API, not from screenshots.

"Roadmap" below means a line in `docs/ROADMAP.md`. Section D (Screens) currently says "nothing
further planned"; items marked **D (new)** would need James's OK to be added there.

## Most important first

### 1. Kestrel cannot reach the lock from the screens (blocker)
The lock needs every blocked or partial procedure either run or **excluded with a reason**. The
server accepts that (`update_workflow` section `procedure`: selected + rationale), but **no screen
offers it**. On Kestrel today the readiness gate lists 8 blocked, 4 partial, and 3 AR confirmation
methods "excluded without rationale". None of these can be cleared by clicking. An auditor expects,
on Coverage: "exclude this procedure" with a required reason, and "include again".
Roadmap: **D (new)**. Needed for the finish line (a learner must be able to finish the file).

### 2. Readiness blockers are codes with no way to them
Lock & Export lists `RISK_ASSESSMENT_NOT_COMPLETE`, `FINDINGS_OPEN (92)` and so on as raw codes.
An auditor expects plain words and a link to the tab that clears each one.
Roadmap: **D (new)**.

### 3. Materiality: amount only
SAD & Completion sets one number. The server also stores a **basis** and **rationale**, but the
screen doesn't ask for them. Performance materiality is loaded from a file, not set here. An auditor
expects: benchmark (e.g. revenue, assets), percentage, the resulting amount, performance materiality,
clearly trivial, and a reason, all in one place (Planning).
Roadmap: **D (new)**.

### 4. 109 findings, one dropdown at a time
Runs & Findings shows every finding in one long table. There's no filter by procedure or disposition,
no bulk dispose (e.g. "clear these 28 payroll items, same note"), and no link from a finding to the
rows behind it. An auditor expects: filter, select several, dispose together (concurrence still per
finding above clearly trivial), and open the evidence.
Roadmap: **D (new)**.

### 5. No working paper before lock
"open workpaper" appears only after locking. On the unlocked Kestrel file the endpoint answers
400. The screen's own note also says the link may open "unauthorized" (a new tab carries no session
token; a request without it got 401). An auditor expects to view and print a procedure's working
paper while working, not only at the end.
Roadmap: **D (new)**. Also worth checking whether the locked link works at all.

### 6. Completion checks: "mark done" only
Each check is marked done with the fixed note "performed". There's no box to write what was done
and no undo. Stages (risk assessment, controls) are the same. An auditor expects a note or
conclusion for each, and a reviewer sign-off.
Roadmap: **D (new)**.

### 7. Flow Map shows only purchase-to-pay
The first tab you see draws the payables cycle only (`CYCLE_MAPS[0]`). Kestrel's scope is 12 areas
(receivables, inventory, cash, payroll, and more), so most of its work doesn't appear on the map.
Roadmap: **D (new)**, or park it and open Kestrel on Coverage instead.

### 8. Nothing can be undone on Sources and Team
- Team: assign only. No remove or change of role (no server route either).
- Sources: no reject for a proposed mapping, no withdraw of a wrong file, no download or view of a
  stored file. Only "replace" and "add" when a role already has data.
An auditor who loads the wrong file expects to take it back (with the record kept).
Roadmap: **D (new)**.

### 9. SAD page: headline 0 beside a schedule at materiality
With no finding disposed yet, the headline shows unadjusted **0** and conclusion "open", while the
schedule below shows Current Assets **15,650.37, at or above materiality**. Both are right (the
schedule matches the key's final misstatements; the headline counts only disposed findings). But a
learner will read it as a contradiction. It needs one sentence or a reordering, not a number change.
Roadmap: **D (new)**. Related gap in the accuracy check: `finish_line_check.py` compares only the
SAD's largest line and material lines, not all 5 lines (the misstatements procedure itself is checked
on all 5).

### 10. No record of who did what
The journal exists (the lock verifies it), but no screen shows it. An auditor expects an activity
log: who ran, reviewed, disposed, concurred, and when.
Roadmap: **D (new)**, or parking lot.

### 11. Evidence requests are a list with no status
Coverage lists 13 requests (kind, item, owner, what it unlocks). There's no requested/received status
and nothing to attach the reply to.
Roadmap: parking lot (real-client use), unless the Learn app needs it.

### 12. Fraud tab: read-only
It gathers well, but you can't run the fraud tests from it, and Kestrel's demo has **0 risks**, so the
"fraud risks" panel is empty on Kestrel. An auditor expects "run all fraud tests" and the presumed
risks (revenue, management override) already on the register for Kestrel.
Roadmap: E3 area (fraud). Whether each Kestrel fraud finding matches the key is step 3 of today's work.

### 13. Load-case list
Offers Kestrel and Harborline; no Oceanview. Waits on James's decisions (remove Harborline? add
Oceanview privately?). Roadmap: today's step 4.

## Tabs that look complete for now
- **Scope & Policies:** period start, trial balance line mapping, account overrides, areas in scope,
  settings per area. Nothing missing that I found.
- **What Changed:** fixed yesterday; shows revisions, stale runs and moved findings. Not re-checked
  in a browser today.
- **Draft Opinion:** decisions with reasons, basis, print. Kestrel shows "disclaimer, not ready",
  which follows from the open items above, not checked against the key today.
- **Lock & Export:** lock, verify, unlock with reason, history, evidence packet (except items 2 and 5).

## Suggested order (for James to decide)
1, 2, 3, 6 are what stop a learner finishing Kestrel in the Workbench. 4, 5, 9 make it usable and
clear on screen. 7, 8, 10 are polish. 11 is parked.
