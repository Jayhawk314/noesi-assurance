# Independent review, 2 Oct 2026: commits 4f4bcb7..a8bc3d1

Reviewer: Claude (a fresh session; did not build this work). Report only:
nothing was fixed, committed or pushed. Probe scripts lived in the session
scratchpad, not the repo. The working tree is unchanged apart from this file
(checked with `git status`: no tracked file modified).

Labels: **confirmed** = I reproduced it with a command this session;
**contradicted** = I reproduced the opposite; **not checked** = I did not.

## Scope

Checked: the D9 removals (service, API routes, readiness, migration 12,
the packet and its offline check, the Workbench, Studio and Learn builds, the
manual), the three forensic tests (code read in full and probed with
invented edge cases and on the Kestrel demo data), the finish-line check, the
Learn lesson checker, and the handoff's claims.

Not checked: see the end.

## Rerun of the handoff's claims

| Claim | Result | How |
|---|---|---|
| 518 tests pass | **confirmed** | `python -m pytest tests -q` → `518 passed in 49.59s` |
| Finish line 162/164, 0 unexplained | **confirmed** | `finish_line_check.py` → `162 of 164 match; 0 unexplained` (the 2 left: Summit Tire PO 1021, check 4433, both roadmap C) |
| Workbench and Studio typecheck and build | **confirmed** | `npx tsc --noEmit` exit 0 and `npm run build` OK for workbench-ui, studio-ui and learn-kestrel-ui |
| Learn lessons 2, 3, 4, 6, 7 tie to the key | **confirmed as far as the checker goes** | `check-lessons: 13 modules, 102 answers, all tied to the key`. But the checker is weak; see M3 |
| Learn key file is generated, not typed | **confirmed** | `export_key.py` rewrote `kestrel-key.json` byte-identical to the committed file (`git diff` empty) |
| Kestrel check sequence: 16 gaps (4142-4390 and short runs) | **confirmed** | 16 gaps, 276 missing numbers, 0 reused, checks 4001-4433 |
| Kestrel Benford: nonconformity, digits 7 and 9 in excess | **confirmed** | journal lines: 1,020 amounts, MAD 0.0345; digit 7: 108 vs 59.2 (z 6.48); digit 9: 120 vs 46.7 (z 10.91) |
| Kestrel vendor-employee compares names only | **confirmed** | `fields_compared: ['name']`, 0 findings |
| Benford default-off makes readiness say "left out without a reason" | **confirmed** | domain `readiness()` with Benford default-off and no rationale → `PROCEDURE_EXCLUSIONS_WITHOUT_RATIONALE` |
| "Seen on screen (Chrome, demo)" | **not checked** | no browser used |

## Findings, most severe first

### H1. Export no longer refuses a broken journal, and the offline check then says "verified" (confirmed)

**Claim it contradicts:** D9 was to remove sign-offs only. Roadmap D9 stage 2:
"Evidence digests ... stay: they prove the data, not a sign-off." The
journal's hash chain is the same kind of integrity evidence. Before a8bc3d1,
`export_packet` refused unless `verify_lock` passed, and that included
`journal_ok` (old `service.py` line 2249-2255: "export refused: the lock does
not verify ... journal_ok=..."). That refusal went with the lock, and nothing
replaced it.

**Reproduction** (scratchpad `probe_d9.py`): create an engagement, run
`UPDATE domain_event SET payload='{"forged":true}' WHERE event_seq=1`, then
`export_record`:
```
export SUCCEEDED; verify_packet: True ; readiness blockers in packet: ['DECISION_TRAIL_BROKEN']
```
The break is recorded inside the packet's readiness block and the working
paper mentions it. But `verify_packet()`, the "offline check" the manual and
README point readers to, returns `verified: True`, and the export itself is
journaled on top of the broken chain.

**Impact:** a reader who checks the record the documented way is told it
verifies, even though the decision trail it came from was edited. This is a
data-integrity check that D9 did not mean to remove.

(For contrast, tampering with a vault file still blocks export:
`VaultIntegrityError blob ... hashes to ...`. So evidence-file digests survived
D9; only the journal check was lost.)

### M1. The check-number test pools every bank account and payroll checks into one sequence (confirmed)

`forensic.check_number_sequence`, Journal path. `_is_check` matches any
transaction type containing "check", so **"Payroll Check"** and **"Paycheck"**
count as disbursement checks. The Journal path also ignores the bank account
each check is drawn on, although the Journal carries an `account` field.

Reproduction (scratchpad `probe_forensic.py`):
- Two bank accounts (checks 1001-1010 and 5001-5005):
  `disbursements checks: 3990 numbers 1011-5000 not in the records`.
- "Check" 1001-1003 plus "Paycheck" 2001-2003 in the Journal, with the payroll
  register holding 2001-2003: `997 numbers 1004-2000 not in the records`.
  The payroll checks also show up in both sequences (disbursements 1001-2003,
  6 checks; payroll 2001-2003).

This is not hypothetical for QuickBooks clients. Kestrel itself pays payroll
from a separate account: its "Payroll Check" entries post to 10200, and
disbursements post to 10100. Kestrel only escapes the problem because its 72
"Payroll Check" lines carry no document number. The contract's limitations
text admits gaps "between" several accounts loaded as one run, but not that
payroll checks get pooled, and the test gives the auditor no way to split the
runs.

**Impact:** a false "thousands of checks missing" lead on an ordinary
two-account client. A real gap inside one account is still reported, but it
gets lost among the false ones.

### M2. Benford raises a finding on about 1 in 5 perfectly conforming populations, and journal lines are counted twice (confirmed)

- I drew 200 trials of 5,000 amounts from a true Benford distribution. All 200
  were rated close (197) or acceptable (3) conformity, yet **40 of 200** raised
  a finding. The reason: a finding fires on any single digit with z > 1.96,
  with no correction for testing 9 digits. Nigrini himself warns that z-tests
  are over-sensitive at large N, and that MAD should decide conformity.
- "Journal lines" takes `debit or credit` per line, so a two-line entry puts
  the same amount in the test twice. 5 two-line transactions gave
  `amounts tested 10`. That double counting inflates n and every z-score by
  about √2.
- The MAD bands (0.006 / 0.012 / 0.015) and the expected proportions match
  Nigrini (2012) table 7.1. The z formula with continuity correction is
  right. **Confirmed correct.**

**Impact:** "close conformity" populations get flagged, which teaches users to
ignore the test.

### M3. The Learn lesson checker accepts any number found anywhere in the key, the same failure mode as 30 Sep (confirmed)

`apps/learn-kestrel-ui/scripts/check-lessons.mjs` collects every number in
`kestrel-key.json` into one set. Lesson prose passes if each figure appears
somewhere in that set, not on the line the lesson is about. Text inside
backticks is skipped entirely, and so are single digits. Measured: 290
distinct numbers are accepted, and **both 2,514.51 (the key's part 1) and
15,650.37 (the final figure) pass**. That is exactly the confusion behind the
30 Sep incident in AGENT-WARNINGS §1. The *asks* are tied to specific key
paths, which is good. The prose of the five new modules is only checked this
loosely.

**Impact:** "all tied to the key" overstates what the checker proves for
lesson text. I did not read all the new prose against the key by hand
(not checked).

### M4. The manual still tells users to mark stages complete, which was removed in D9 stage 1 (confirmed)

`docs/manual/02-planning-materiality-risk.md` lines 73-75: "Mark the **risk
assessment** and **controls** stages complete ... both are readiness gates
(`RISK_ASSESSMENT_NOT_COMPLETE`, `CONTROLS_NOT_COMPLETE`)." Neither code exists
in `readiness.py` any more. The handoff says the manual was updated for
D9, and this passage was missed. Related, already admitted in handoff
item 5: Studio's Learn lessons still teach lock, concurrence and run review
(e.g. `apps/studio-ui/src/learn/lessons-planning.ts:226` "Readiness refuses
the lock over ... `RISKS_AWAITING_CONCURRENCE`"). Studio's `Conclude.tsx`
keeps labels for five removed codes. That is harmless dead code.

### M5. Benford default-off: every engagement gets a blocker; the Kestrel demo leaves the test out (confirmed; decision for James)

- With `default_selected=False` and no rationale, readiness reports
  `PROCEDURE_EXCLUSIONS_WITHOUT_RATIONALE` on every engagement except the
  Kestrel seed (handoff item 3, confirmed). A new user's first readiness
  screen shows a blocker the user never caused.
- The Kestrel seed excludes Benford with the rationale "not yet in the Kestrel
  answer key (roadmap D10)". The reason is visible on screen and disclosed in
  the handoff, so this is **not** hidden. But the public demo does not show a
  real result (strong nonconformity) because the key has no line for it.
  Under AGENT-WARNINGS §1, whether that is acceptable is James's call, not an
  agent's. Note that the check-number test, which also has no key lines, *is*
  shown on the demo with its 16 accidental gaps. The two tests are treated
  inconsistently.

### L1. Migration 12 reopens locked engagements silently (confirmed)

`UPDATE engagement SET status='open' WHERE status='locked'` emits no journal
event. Probe: events before/after migration `4 4`, journal ok. An engagement
that was locked becomes open, and its own trail does not say when or why
(only the old lock rows remain). Low, because locks were removed by decision,
but it is a status change with no trail entry.

### L2. Vendor-employee: masked numbers match, phone formats miss, some names skipped silently (confirmed)

- Bank accounts need only 4 digits, so masked `****4821` and `XXXX4821`
  match. That gives false leads when exports carry only the last four digits.
- Phone `555-1234` and `(415) 555-1234` do not match.
- An employee master with `first_name`/`last_name` columns and no `name`
  column: those employees are left out of the name comparison, while the
  stats still list `name` as compared. In the probe, employee E3 ("Ann Lee",
  split fields) was not compared, and nothing said so.
- Name matching is reasonable otherwise: word order ignored, single initials
  dropped, company noise words removed. Nothing in the code is Kestrel-
  specific.

### L3. Payments fall back to `payment_number` as a check number (confirmed mechanically)

When `check_number` is blank, the payment's own record number is used. A
numeric internal ID (1, 2, ...) next to a real check 4001 gives
`3999 numbers 2-4000 not in the records`. Whether real exports carry numeric
internal payment IDs: not checked.

### L4. Journal checks without a number vanish from the stats (confirmed)

On the payment path, an unnumbered check counts as `not_numbered`. On the
Journal path it is filtered out before counting. On Kestrel the "Payroll
Check" lines are not counted anywhere (`rows: 157, not_numbered: 0`). This
contradicts the forensic module's own rule that what is not tested is said.

### L5. The check-sequence contract requires `Payments` even when the Journal is the source (code reading only, not reproduced)

`{"Payments": ("payment_number",)}` is the contract's required role, so a
client with a Journal and no payment file would show the test as blocked,
although the engine could run on the Journal alone.

### L6. Stale text and dead code (confirmed by grep)

`sad.requires_concurrence` is unused outside tests that assert its absence.
The `service.py:113` docstring still mentions concurrence.
`docs/INDEPENDENT-REVIEW.md` invariants 3 and 4 still describe run review,
concurrence, the partner-only lock and "export refuses when verification
fails". The next reviewer will be sent to attack features that no longer
exist.

## Confirmations (tried to break, could not)

- **Mapping separation of duties survives.** A principal holding both preparer
  and reviewer proposed a mapping and then tried to approve it →
  `SeparationOfDutiesError: the preparing principal may not approve their own
  work` (service level; the HTTP path not separately driven).
- **Evidence digests survive.** Editing a vaulted CSV blocks export with
  `VaultIntegrityError`.
- **The journal hash chain survives** as a check: `verify_journal` and the
  `DECISION_TRAIL_BROKEN` readiness blocker still work. Only the export
  refusal went (H1).
- **No dangling API calls.** Every path in `apps/workbench-ui/src/api.ts` has a
  matching `case` in `server.py`. `/lock` and `/unlock` return 404 (tested in
  `test_api_server.py`). Studio typechecks against the Workbench client.
- **The packet's limits are honest.** `PACKET_LIMITS` says plainly that the
  packet is unsigned, that anyone can recompute it, and that it does not prove
  authorship or time.
- **Readiness kept its fact-based gates:** materiality, risks
  unassessed/without response/without procedure, blocked/partial/pending
  procedures, exclusions without rationale, no-data assertion, waivers above
  trivial, unresolved scope, broken trail. The removals (stages, completion
  checks, review, concurrence) are the ones D9 named.
- **The forensic tests are not fitted to Kestrel.** No case names, numbers or
  accounts in `forensic.py`. The Benford constants are published.
- **Removed tests were lock-specific.** The one non-lock removal,
  `test_optimistic_version_conflict_raises`, tested `set_status`, which no
  longer exists. `ConflictError` is still tested in
  `test_transactional_spine.py`.
- **The finish-line change is harmless.** `roles` went from a set to a sorted
  list, which fixes the order a set prints in. The comparison itself is
  unchanged.

## Question for James (not a defect)

D9 removed the six completion checks: final analytics, subsequent events,
going concern, management representations, evidence sufficiency, engagement
review. They were ticked boxes, so removing them follows the supplement rule.
But the readiness view and the exported record now say nothing about these
areas at all. A supplement that "shows what it could not test" might list them
as *not tested by Noesi*, rather than let them disappear.

## Not checked

- On-screen claims (Chrome): no browser used.
- QuickBooks fixes M2, M3, L1-L5, L7, L8: their tests pass in the suite. I did
  not attack them further.
- Self-approval over HTTP with `X-Acting-Principal` (checked at the service
  level only).
- Oceanview; Studio at runtime; real pre-D9 databases (migration 12 tested on
  a synthetic locked row only).
- The prose of Learn modules 2, 3, 4, 6, 7 read by hand against the key.

## Verdict

The D9 removal is clean where it was aimed: nothing dangles in the API, the
UIs or the tests, and evidence digests and mapping separation of duties
survive. One integrity check was lost along the way (H1). The forensic tests
are general and honestly worded. But the check-number test will mislead on
any client with more than one bank account or numbered payroll checks (M1),
and Benford will cry wolf on clean data (M2). Use them today as teaching
demos on Kestrel, not as leads on a real client. Fix first: H1, then M1 and
M2.
