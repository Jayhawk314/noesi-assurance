# Fraud tab vs the answer key (Kestrel), 30 Sep 2026

*Checked by Claude. Not yet reviewed by a second agent.*

**How:** seeded Kestrel exactly as `finish_line_check.py` does (`seed()`, commit 7cfb3fe),
read `fraud_view()` (what the Fraud tab shows), and compared every finding with
`answer_key_payables.json` and `answer_key_part2.json` by hand. `finish_line_check.py`
checks the other direction (does the Workbench find what the key lists); this checks
whether everything the tab shows is in the key.

**Result: 51 findings. 48 match the key exactly. 3 are not in the key.** No finding
contradicts the key.

## Matches (48)

| Test | Tab | Key | |
|---|---|---|---|
| Vendor twins | Moraine Cycle Components / Moraine Cycle Components, Inc. | same pair | ✓ |
| Duplicate bills | MC-25009, 18,432.50 twice | MC-25009, 18,432.50 | ✓ |
| Split payments | Hyalite Fabrication, 3 payments on 2025-11-14, 7,325.00 | Hyalite, 7,325.00 | ✓ |
| Payments without bills | DM Consulting 4,500.00 | DM Consulting 4,500.00 | ✓ |
| Journal entries (16) | posted after period end 1 (1066); weekend 2 (1047, 4421); round amount 4 (4039, 1047, deposit, transfer); unauthorized user 1 (1047, Jo Kestrel); seldom-used account 7; manual entry with no description 1 (1052) | the same entries in every test | ✓ |
| Seldom-used accounts | 10900, 15000, 21000, 23000, 32000, 51000, 65000 | same 7 | ✓ |
| Payroll (28) | E16 not on the master, 24 payments (16 × 692.33 + 8 × 733.03 = 16,941.52); E12 paid 2026-03-02 after termination; E03/E09 share a bank account; E05 net pay over by 100.00 on 2025-10-15; E07 Dana Merritt at DM Consulting's address | E16 24 payments, 16,941.52; E12 2026-03-02; E03/E09; E05 100.00; E07/DM Consulting | ✓ |

Journal "no description": the key counts 177 entries with no description in total, but
lists only 1052 as a *manual* one; the demo's policy tests manual entries only
(`je_manual_sources`), so 1 is the matching figure.

## Not in the key (3), `ap.payments_without_bills`

| Payee | Tab | What the case data shows |
|---|---|---|
| First Prairie Bank | 63,750.00 in 13 payments | `data/client/debt_schedule.csv`: LOC-2208 principal 50,000.00 + interest 13,750.00 = 63,750.00. Loan payments; a bank sends no bill. |
| Rocky Mountain Racking | 14,500.00 in 1 payment | `data/auditor/additions_vouching.csv`: FA-01, 14,500.00, capitalized, inv 7731. An equipment purchase. |
| Idaho State Tax Commission | 117,600.86 in 11 payments | **Not checked**: no schedule in the case data supports it. Probably tax remittances (a guess). |

These are not software bugs as far as checked: the test's claim ("paid, and sent no bill
in the period") is true of each. They are findings the auditor would clear with a reason.
The key simply doesn't list them. Adding them to the key as "expected, cleared" items is
James's decision (it changes the key, not the engine).

## Also seen

- **Fraud risks: 0.** The Kestrel demo registers no risks, so the tab's "fraud risks" panel
  is empty (gaps doc item 12).
- **Header count leaves out partial tests.** The header reads "7 of 11 fraud tests run · 1
  cannot run on these records". The other 3 (payment-to-bill reference, document chain,
  segregation of duties) are "partly" and did not run; they show in the table but not in
  that sentence. A wording fix, not a wrong number.
- **Journal completeness:** no exceptions, closed to 32000 — as the key says (the accuracy
  check already tests this).
