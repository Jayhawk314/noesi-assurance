# Noesi run findings: Kestrel part 1 (payables and the journal)

**Run date:** 2026-09-29, with the engine unchanged at `7dbb2c8`.
**Key:** `answer_key_payables.json` at `c3da828`.

**Reproduce:**
`.venv\Scripts\python case-studies\kestrel-valley-cycle\instructor\run_part1.py`

## Agrees with the key

- **Vendors:** all 16 load. The look-alike pair *Moraine Cycle Components* /
  *Moraine Cycle Components, Inc.* is found.
- **Bills** (QuickBooks recipe):
  - 100 load. The two without an invoice number are set aside and named.
  - The total, 3,328,206.64, equals the key's 3,330,775.30 less those two
    (2,568.66).
- **Payments** (QuickBooks recipe): all 115 load, and the total,
  3,285,040.78, equals the key.
- **Split bills:** the three Hyalite Fabrication bills, paid on 2025-11-14,
  are found.
- **Journal entries:**
  - The owner's entry is flagged as posted by a user not on the authorized
    list.
  - The two weekend entries (JE 1047, check 4421) are found.

## Breaks

| # | Severity | What happened | Key says |
|---|---|---|---|
| J1 | High | The journal loaded 358 of 1,468 rows. The QuickBooks Journal layout prints the date and Num only on a transaction's first line, so continuation lines are set aside for a blank entry ID. | 461 transactions, 1,006 lines |
| J2 | High | 357 entries are reported **unbalanced**. Entries are keyed by Num, which is blank for deposits, transfers and payroll and repeats across types, so unrelated lines merge. | none are unbalanced |
| J3 | Medium | The posted-after-period-end test is not performed. "Create date" is not recognised as the posted date. | JE 1066 (dated 6/30, entered 7/10) |
| J4 | Medium | Round amounts: 2 found, key says 4. Seldom-used accounts: 6 found, key says 7. No description: 176 found, key says 177. All three follow from J1 and J2. | 4 / 7 / 177 |
| P1 | Fixed | One stored file can feed a second role. The engine could already do it, but the Workbench screen and bulk propose skipped any file that was already mapped. They now skip only the same role. The 36 purchase orders load, matching the key. PO-to-bill matching stays partial: the bill export carries no PO number (only a memo). | 36 POs; one bill is 12% over its PO |
| P2 | Fixed | New generic check ap.duplicate_bills (payables scope; tested on invented data). It finds the Moraine invoice recorded twice for 18,432.50 under the look-alike vendor. | duplicate MC invoice, 18,432.50 |
| P3 | Low | The subledger-to-ledger tie is blocked: there is no General Ledger export in part 1. | unpaid bills 287,640.18 = TB |
| P4 | Info | Payment-to-bill and segregation-of-duties checks are partial: QuickBooks exports name neither the bill paid nor an approver. This is inherent, and the key says so. | not testable |

The DM Consulting checks (no bills, the bookkeeper's address) and the 90
short payment belong to part 3's related-party and completion work.

## Proposed fixes (for approval; none made)

1. **A QuickBooks Journal recipe (J1–J4).** Waiting for a real QuickBooks Journal export: Kestrel's Journal layout is modeled, and building to it would fit the engine to the case. Carry the date, type, Num and name
   down to continuation lines. Key each entry by those four together, and
   read Create date and Created by.
2. **Let one stored file feed several recipes (P1).** Done.
3. **A duplicate-bill check (P2).** Done.
