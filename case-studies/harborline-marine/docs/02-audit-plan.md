# Audit plan — accounts payable and cash disbursements

## Materiality

Set on revenue, the measure the lender's covenant tracks and the one most
stable across Harborline's three audited years.

| | Amount | Basis |
|---|---:|---|
| Overall materiality | 420,000 | 1.0% of revenue ($42.4m) |
| Performance materiality | 315,000 | 75% of overall |
| Clearly trivial threshold | 21,000 | 5% of overall |

Enter **420000** as materiality in the workbench when you reach the SAD screen.

Anything below 21,000 need not be accumulated on the summary of audit
differences unless it is qualitatively significant — an unauthorised payment is
qualitatively significant at any amount.

## Risk assessment

| Risk | Assertion | Why | Response |
|---|---|---|---|
| Payments released without approval during the supervisor vacancy | Authorization | Eleven weeks with no dedicated approver; management admits informal handling | Test segregation of duties across the full payment population, not a sample |
| Fictitious or duplicate vendors created by purchasing | Occurrence | Vendor creation moved to the department that also raises POs — the classic incompatible pairing | Screen the vendor master for relational twins; trace unusual vendors to disbursements |
| Payments for goods never received | Occurrence | Receiving process changed mid-year; controller expects gaps | Three-way match across PO, voucher, and goods receipt |
| Disbursements not recorded, or recorded at the wrong amount | Completeness, Accuracy | Independent bank feed available — use it | Reconcile payments to bank clearing and to GL posting |
| Payments structured below approval limits | Authorization | A natural response to an approval bottleneck | Cluster payments by vendor and date against the threshold |
| AP subledger does not support the control account | Completeness | Standard year-end tie-out | Reconcile subledger to GL control account 2000 |
| Round-trip value flows to related parties | Occurrence | Extract exists and was produced for the lender; unexplained | Screen for closed directed cycles |

## Planned procedures

All eleven procedure contracts in the library are in scope. Coverage will
confirm which the supplied data actually supports.

| Procedure | Tests | Data it needs |
|---|---|---|
| `ap.payment_voucher_reference` | every payment cites a real voucher | Payments, Vouchers |
| `ap.voucher_po_reference` | every voucher cites a real PO | Vouchers, Purchase_orders |
| `ap.document_chain` | PO → voucher → payment amounts and dates cohere | POs, Vouchers, Payments |
| `ap.segregation_of_duties` | entry and approval are different people | Payments |
| `ap.vendor_relational_twins` | no near-duplicate vendor identities | Vendors |
| `cash.bank_clearing` | recorded payments cleared the bank | Payments, Bank |
| `gl.payment_posting` | payments posted to the GL correctly | Payments, GL |
| `ap.subledger_gl_balance_tie` | subledger ties to the control account | AP_control_balance |
| `ap.three_way_receipt_match` | invoiced goods were ordered and received | POs, Vouchers, Goods_receipts |
| `ap.split_payment_review` | no clustering below the approval limit | Payments + `split_threshold` policy |
| `forensic.closed_value_flow` | no closed round trips | Value_flows |

**Approval threshold for the split-payment test: $10,000.** Harborline's written
policy requires a second signature above that amount.

## Scope limitations to record up front

Two are known before fieldwork begins, and both should end up in the
workpaper's limitations section:

1. **PO approval timestamps are absent.** The extract carries `Created By` and
   `Approved By` but no `created_on` / `approved_on`. Approval *sequence* on
   purchase orders therefore cannot be tested — only that two different names
   appear.
2. **Value-flow completeness is unverified.** The extract is management-prepared
   with no reconciliation to an independent source. A closed cycle found in it
   is an investigation lead; the absence of one proves nothing.

## Completion

The engagement cannot be locked until readiness is green. Expect blockers for
unreviewed runs, undisposed findings, and incomplete completion checks — that
is the gate working, not an error.
