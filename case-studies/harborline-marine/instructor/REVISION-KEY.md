## Assignment 11 — corrected voucher file (revision/vouchers_revised.csv)

Built by `revision/make_revision.py` from `data/vouchers.csv`; verified by
`tests/unit/test_revision_impact.py`.

| Change | Before | After | Effect | Threshold class |
|---|---:|---:|---:|---|
| VCH-2026-9338 added | — | 21,619.99 | +21,619.99 | above clearly trivial |
| VCH-2026-0009 amount | 4,325.33 | 3,244.00 | −1,081.33 | below clearly trivial |
| VCH-2026-0030 amount | 26,751.69 | 26,871.69 | +120.00 | below clearly trivial |

**Stale runs (4):** `ap.document_chain`, `ap.payment_voucher_reference`,
`ap.three_way_receipt_match`, `ap.voucher_po_reference`. The other seven
procedures do not read Vouchers and stay current.

**Finding movements on rerun (3):**

1. `ap.payment_voucher_reference` / PAY-2026-0013 **disappears**: the voucher
   it cited now exists.
2. `ap.three_way_receipt_match` / VCH-2026-0009 **disappears**: the voucher
   now equals receipts.
3. `ap.document_chain` / PAY-2026-0009 **appears**: the payment (4,325.33)
   no longer matches the corrected voucher (3,244.00).

**The intended conclusions:**

- VCH-2026-9338 is a **duplicate invoice** for the purchase already billed as
  VCH-2026-0013: same vendor V1006, same amount, same PO-2026-0013, created
  and self-approved by E227 one week later. PAY-2026-0013 paid 9338 while
  0013's own payment trail should be traced. No procedure detects duplicate
  invoices, so the report is silent; students who only read the report miss
  it. Credit requires spotting it from the diff (Part A step 4).
- VCH-2026-0009's "correction" did not resolve anything. The three-way
  exception moved into a payment/voucher difference: the company paid
  1,081.33 more than the corrected invoice. Correct treatment: a potential
  overpayment/recovery, below clearly trivial but worth reporting to
  management given the control environment.
- VCH-2026-0030 is a genuine keying fix with no finding effect.
- Any disposition recorded on the two disappearing findings must be
  revisited with a note that names the correction. The impact report flags
  both (`revisit_disposition`); if 0009 had been carried as unadjusted, the
  SAD's unadjusted total falls by 1,081.33.
