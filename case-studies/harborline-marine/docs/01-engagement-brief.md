# Engagement brief — Harborline Marine Group, Inc.

*Fictional client. Any resemblance to a real company is coincidental.*

## The client

Harborline Marine Group sells, services, and winter-stores recreational and
light commercial vessels from four locations on the mid-Atlantic coast, with a
parts warehouse in Norfolk. It has been family-held since 1987; the founder's
two children hold 71% of the common stock between them and a regional private
investor holds the rest.

| | |
|---|---|
| Fiscal year end | 31 December 2026 |
| Revenue | $42.4 million |
| Total assets | $28.1 million |
| Accounts payable at year end | $2.73 million |
| Employees | 146 |
| Accounting system | Mid-market ERP, migrated from QuickBooks in March 2024 |

## Why there is an audit

Harborline's operating line of credit was increased to $6 million in 2025. The
lender's covenant requires audited financial statements within 120 days of year
end, along with a minimum current ratio of 1.25.

This is the third annual audit. The prior two were unmodified.

## What changed this year

Three things make accounts payable the area of interest:

1. **The AP supervisor left in June** and was not replaced until September. For
   roughly eleven weeks, the two remaining AP clerks processed and released
   payments without a dedicated approver, and management has acknowledged that
   approval limits were "handled informally" during that period.

2. **A new vendor onboarding process** was introduced in April, moving vendor
   master maintenance from the controller's office into the purchasing
   department. Purchasing now creates vendors and raises purchase orders.

3. **The parts warehouse changed receiving procedures** in the second half of
   the year, moving from paper receiving tickets to scanner-based entry. The
   controller notes that "a handful" of receipts from the transition weeks may
   not have made it into the system.

## What management has given you

A year-end extract from the ERP, exported to CSV:

- the vendor master,
- an employee list for the purchasing and AP functions,
- all purchase orders, goods receipts, vouchers, and payments for the year,
- the bank disbursement feed for the operating account,
- general ledger postings to the AP control account (2000),
- the year-end AP subledger and control-account balances,
- a counterparty value-flow extract the controller prepared last year at the
  lender's request, and has continued producing.

## What management has *not* given you

Named explicitly, because the tool will ask:

- Vendor bank-detail change logs.
- The approval-limit policy in force during the June–September gap.
- Purchase-order approval timestamps (`created_on` / `approved_on` are absent
  from the PO extract).
- Any documentation for the value-flow extract's completeness.

You are not obliged to accept the population as complete simply because it was
provided. Recording what you could not obtain is part of the work.
