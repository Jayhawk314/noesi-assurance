# Noesi run findings: Kestrel parts 2 and 3

**Run date:** 2026-09-29, with the engine unchanged at `a5c57f5`.
**Keys:** `answer_key_part2.json` (`5905c16`) and `answer_key_part3.json`
(`fc7f89d`).

**Reproduce:**
`.venv\Scripts\python case-studies\kestrel-valley-cycle\instructor\run_parts23.py`

**Setup:**
- The trial balance is the hand-prepared one (pass B), because the
  QuickBooks export does not load yet (K8).
- The July journal is the only journal loaded. The journal-entry and
  population-completeness results below therefore test a July-only
  population against the full-year trial balance. This is a limit of the
  run's setup, not an engine finding.

## Agrees with the key

**Payroll**
- Register gross ties to the wage account 60100 (486,300.00).
- The ghost employee E16 is found on all 24 payments.
- E12 is flagged as paid after termination, beyond the 15-day grace.
- E03 and E09 are flagged for sharing a bank account.

**PP&E**
- The rollforward ties.
- FA-06 depreciation is overstated by 300.
- The addition vouches clean.

**Debt and equity**
- The loan rollforward and interest agree.
- The current-ratio covenant is breached.
- Members' capital does not tie (5,000).
- Retained earnings foots and ties.

**Accruals**
- The rollforward ties.
- The insurance recompute differs (267.62), and so does the audit fee
  (2,604.18).
- Software and accrued payroll are listed as not recomputed.

**Estimates**
- Three misses beyond 20% are flagged.
- All misses leaning one way is flagged as a bias indicator.

**Related parties**
- Summit Loop Racing is matched as a customer.
- Jo Kestrel is matched to employee E01 by address.

**Subsequent events**
- The 30,000 settlement (JE 1071) is found.
- The 25,000 check 4429 is found.

**Representation letter**
- The related-parties representation is reported missing.
- The letter is flagged as not dated as of the report date.

**Uncorrected misstatements**
- Current assets total 15,650.37, above materiality; this matches the key
  to the cent.

**Draft opinion**
- It proposes a **disclaimer**, as the key expects.

## Breaks

| # | Severity | What happened | Key says |
|---|---|---|---|
| C1 | Medium | The draft opinion lists "letter" as a missing representation. Letter-level problems (dating, signature) are mixed in with the representations themselves, so the basis sentence names a non-representation. **A bug in the opinion code.** | Missing: related_parties only. The dating is a separate letter issue. |
| C2 | High | The payroll net-pay check was **silently not performed**. The "Taxes Withheld" column is not recognized, and with no deductions mapped the check skips without saying so. The E05 error (net 100 high) is not found. | E05, 2025-10-15, over by 100 |
| C3 | Medium | The draft opinion requires no going-concern decision. Its indicators come only from the going-concern procedure, which refuses Kestrel's trial balance (K8); the covenant breach (debt.covenants) is not treated as an indicator. | A going-concern conclusion is required (covenant breached, current ratio below 1.20) |
| C4 | Medium | Subsequent events misses the 40,000 transfer and the two July deposits (33,580.90 and 27,904.15), all above the 10,000 threshold. This is part 1's journal layout issue (J1): lines without a Num are merged or lost. | 5 transactions above threshold |
| C5 | Low | The undisclosed related party DM Consulting is not found. This is the known limit of list matching (depth pass: vendor sharing an address with an employee). | Undisclosed; bookkeeper's address |
| C6 | Low | The misstatement summary raises 11 "likely below identified" tensions (K13, the "Likely" column convention). | none |

## Proposed fixes (for approval; none made)

1. **C1:** separate letter problems from missing representations in the draft
   opinion.
2. **C2:** add "taxes withheld" as a synonym, and report the net-pay check as
   not performed when no deductions are mapped.
3. **C3:** treat a breached debt covenant as a going-concern indicator in the
   draft opinion (AU-C 570 lists it).
4. **C4:** waits for the real QuickBooks Journal export (J1).
