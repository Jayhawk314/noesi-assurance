# One-time final review: audit-frame additions and Kestrel parts 1–3

**Date:** 2026-09-29  
**Range:** `7dbb2c8..f5d6e61`  
**Method:** report only; no application, case, or test code changed

## Scope and stopping rule

This review covered only:

- the draft opinion in `assurance_domain/opinion.py` and
  `WorkbenchService.draft_opinion()`;
- `ap.duplicate_bills`;
- mapping one stored file once per role;
- the payroll net-pay not-performed refusal;
- the Kestrel parts 1–3 files and answer keys; and
- the C1–C3 fixes in `f5d6e61`.

I report only a wrong clean result, a draft opinion that offers the wrong
outcome for its evidence, or an arithmetically wrong answer key. I did not
reopen the total-row rule, report style, documented limitations, or rows that
are explicitly refused or held for review. Findings are capped at five.

## Findings

### F1 — High: a payroll row can skip net-pay re-performance without the new refusal

`packages/procedures-cycles/src/procedures_cycles/payroll.py:48` performs the
net-pay calculation row by row only when that row has a withholding or
deduction value. The new refusal at line 98 is engagement-wide: it is emitted
only when **no row anywhere** has either value. Consequently, one complete row
makes the procedure appear performed for a second row that has neither input.

**Reproduction:** run `payroll.register_tests` with two employees on the
master and these register values:

```text
Employee, Gross, Tax withheld, Deductions, Net
E1,       1000,  100,          blank,      900
E2,       1000,  blank,        blank,      900
```

Observed result:

```text
findings []
not_performed {}
exceptions 0
```

E2's net pay was not re-performed, yet the completed procedure reports no
finding or not-performed entry. This is the same wrong-clean class as C2, only
on a partly populated register. The refusal must identify every untestable
row, not only an entirely untestable file.

### F2 — High: a scope limitation suppresses the known-misstatement opinion path

The proposal ladder uses mutually exclusive branches at
`assurance_domain/opinion.py:102` and line 109. If any open scope limitation
exists, the draft proposes only `qualified_or_disclaimer` and asks only about
the scope limitation's pervasiveness. A known uncorrected misstatement above
materiality is then omitted from both the basis and the decisions required.

**Reproduction:** provide one open `REFUSAL`, materiality 15,000, and a
completed misstatement summary with Current Assets misstated by 20,000.

Observed result:

```text
proposed_opinion qualified_or_disclaimer
decisions_required [pervasiveness_of_scope_limitation]
misstatements.amount 20000
```

If the scope limitation is material but not pervasive while the known
misstatement is pervasive, `adverse` remains a possible outcome, but the draft
does not offer it or request the misstatement-pervasiveness decision. The
draft must evaluate both modification causes before proposing the available
outcomes; a scope limitation cannot make a known material misstatement cease
to affect the opinion.

### F3 — Medium: a misstatement exactly equal to materiality produces an unmodified draft

At `assurance_domain/opinion.py:76`, materiality is crossed only when
`largest > m`. The completion procedure itself uses `>= materiality`, and the
draft's unmodified basis says the amount is “below materiality.”

**Reproduction:** with no scope limitation, materiality 15,000, and a
completed summary whose Current Assets total is exactly 15,000:

```text
proposed_opinion unmodified
status draft_for_partner
basis: uncorrected misstatements (15000.00) are below materiality (15000)
```

The amount is not below materiality. This is a wrong clean opinion proposal at
the boundary and is inconsistent with the engine that produced the summary.

## Confirmed without a finding

- One stored Transaction List by Vendor successfully maps separately to
  `Vouchers` and `Purchase_orders`; the Kestrel run loads 100 numbered bills
  (two unnumbered rows are explicitly set aside) and 36 purchase orders.
- `ap.duplicate_bills` finds the planted `MC-25009` duplicate for 18,432.50
  under the two Moraine vendor records.
- Kestrel C1 is fixed: `related_parties` is the only missing representation;
  the letter-date problem is a separate required decision.
- Kestrel C2's exact case is fixed: the `Taxes Withheld` heading maps and the
  E05 net-pay error of 100 is found. F1 is the remaining partial-row case.
- Kestrel C3 is fixed: the breached current-ratio covenant requires a
  going-concern conclusion.
- Kestrel's draft proposes `disclaimer`, matching the missing related-parties
  representation in its key.
- I independently recalculated the major Kestrel key figures from the written
  files: bills, payments, unpaid bills, purchase orders, journal transaction
  and line counts, payroll, PP&E, debt, equity, accruals, estimates, and final
  misstatement totals. I found no arithmetic error in the three added keys.

## Required checks

- Full suite: **408 passed** in 26.11 seconds.
- Harborline verifier: **52 findings** across eleven procedures.
- Kestrel core key checker: **13/13 checks agree**.
- `pip check`: **No broken requirements found**.
- Kestrel parts 1 and 2–3 runners completed and reproduced their documented
  results, including the fixed one-file/two-role, duplicate-bill, C1, C2, and
  C3 behavior.

## Verdict

The three answer keys checked out, and the named Kestrel fixes work on their
exact cases. The batch has three real residuals under the agreed stopping
rule: one wrong-clean payroll path and two incorrect draft-opinion paths. No
other issue from this review meets the reporting threshold.

Per the agreed process, this is the sole independent review for the batch; it
does not request another review round after remediation.
