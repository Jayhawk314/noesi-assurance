# Independent check, 2 Oct 2026: the uncommitted fixes in HANDOFF_2026-10-02-fixes.md

Checker: Claude, a fresh session that did not build these fixes. Report only. Nothing
in the code was changed, committed or pushed. Probe scripts are in the session
scratchpad, not the repo. During the planting test `lessons.ts` was edited and then
restored with `git checkout`; `git status` shows it clean.

## The handoff's claims, rerun

| Claim | Result | How |
|---|---|---|
| 525 tests pass | **confirmed** | `python -m pytest tests -q` gives `525 passed` |
| Finish line 162/164, 0 unexplained, 35 procedures | **confirmed** | `finish_line_check.py` (it needs the package `src` dirs on PYTHONPATH when run directly) |
| check-lessons passes | **confirmed** | 13 modules, 102 answers; 9 fraud lessons, 37 answers |
| Three apps typecheck and build | **confirmed** | `tsc --noEmit` exit 0 and `npm run build` exit 0 for workbench-ui, studio-ui and learn-kestrel-ui |
| H1: a broken trail exports, but the record fails its check | **confirmed** | code read; the 3 new tests pass; the manifest digest covers `journal_check`, so editing it breaks `manifest_ok` |
| M1: checks split by kind and bank account | **confirmed, with one weakness (C1)** | probes: Check plus Paycheck makes two runs with no false gap; a payroll gap in the register is found; signed-amount Journal reuse is found |
| M1: Kestrel unchanged | **confirmed** | seeded demo: disbursements from the Journal, 157 checks 4001-4433, 16 gaps, 276 missing, 0 reused; payroll from the register, 352 rows with no number |
| M2: 0 false findings in 200 Benford-true trials | **confirmed** | my own 200 trials of 5,000 amounts: 0 findings (199 close, 1 acceptable) |
| M2: still finds real nonconformity | **confirmed** (not claimed in the handoff) | 5,000 amounts with 8% invented at 9,000-9,999 give nonconformity with digit 9 named and 1 finding |
| M2: journal amounts counted once | **confirmed** | 1,500 two-line entries, either debit/credit or signed amounts, give 1,500 amounts |
| M3: a lesson's numbers must come from its own part of the key | **confirmed** | 2,514.51, 15,650.37 and 777,777.77 planted in all 13 lessons. Every one was refused, except 15,650.37 in Completion and The opinion, where it belongs |
| M4: manual ch. 2 | **confirmed** | diff read |
| M5: Kestrel shows Benford as not tested | **confirmed** | 3 REFUSAL findings: journal lines 492, bills 100, payments 115, each below 1,000 |

## Problems found

**C1. A check can be put under the wrong bank account (confirmed; low to medium).**
The rule "the account the check credits most" picks a non-bank account when another
credit line is larger than the bank credit. That can happen in QuickBooks: a check with
a negative line, such as a vendor credit or a refund. Probe: checks 2001-2007 on 10100,
where check 2006 credits 700 to "1400 Vendor credit" and 300 to 10100. The result is a
false gap at 2006 in the 10100 run, plus a one-check run named
"disbursements, account 1400 vendor credit". A check credited to two bank accounts shows
the same false gap. QuickBooks cannot draw one check on two accounts, so that case is
less realistic. Each such check makes one false gap, not thousands. A possible fix is
to prefer, among a check's credited accounts, the one most of the other checks use. Not
checked on Oceanview or a real QuickBooks file.

**C2. The Kestrel demo now has 3 more open findings (confirmed; for James to know).**
The three "not tested" Benford refusals are undisposed, so the demo's
`FINDINGS_OPEN` count includes them. They are honest. Also, the run's `population`
shows 707 (and coverage shows 1,020) even though 0 amounts were tested, so a screen
that says "707 items" could read as "707 tested". I have not checked how this looks on
screen.

**C3. Wrong reason text (confirmed by code reading; cosmetic).** A v5 packet whose
`journal_check` has been removed reports "not recorded (packet made before 2 Oct 2026)".
The check still fails correctly; only the reason given is wrong.

**C4. A limit of the lesson checker (by design; low).** A number from another line of
the same module, or for an ask such as `payables.segregation_of_duties` from anywhere
in `payables`, still passes. That is much tighter than before, but it does not prove
that the figure is the right line.

## For James's Benford decision (M5)

With amounts counted once and a probe-only minimum of 100 (the demo is not changed),
Kestrel gives nonconformity in all three populations:
- journal lines: 492 amounts, MAD 0.0335, digits 7 (54 against 28.5) and 9 (60 against 22.5);
- bills: 100 amounts, MAD 0.070;
- payments: 115 amounts, MAD 0.076.

At the 1,000 minimum, the demo shows none of this. The handoff cites Nigrini for the
1,000 figure. I did not check that source this session.

## Not checked

The on-screen look of any of this (no browser was used). Oceanview. A real QuickBooks
Journal. Whether "Paycheck" is QuickBooks' name for the transaction type. The handoff's
"not done" list (L1-L6, Benford's default) is still open.
