# Verified run — what the engine actually did

> Do not distribute with the student materials.

The whole case was loaded through `WorkbenchService` on **7 August 2026**
(reproducible any time with `instructor/verify_run.py`) and the output
recorded here verbatim. `ANSWER-KEY.md` says what was *planted*; this file
says what the software *found*. Where they differ, this file is the authority
on the tool's behaviour.

> An earlier verified run (6 August 2026) recorded a coverage defect: 10
> procedures compiled "executable" but only 6 had executors, and the
> split-payment threshold could not reach a run. Both are fixed — coverage is
> now reconciled against the executor registry (a contract with no executor
> reports `unsupported`), all 11 procedures execute, and approved engagement
> policies flow into runs automatically.

## Ingestion — all ten roles, zero rejected rows

| Role | Loaded | Rejected | Refused fields |
|---|---:|---:|---|
| Vendors | 44 | 0 | — |
| Employees | 13 | 0 | — |
| Purchase_orders | 123 | 0 | `created_on`, `approved_on` |
| Goods_receipts | 119 | 0 | — |
| Vouchers | 123 | 0 | — |
| Payments | 123 | 0 | — |
| Bank | 119 | 0 | — |
| GL | 120 | 0 | — |
| AP_control_balance | 1 | 0 | — |
| Value_flows | 51 | 0 | `flow_type` |

The two refusals are intentional and are the case's built-in scope
limitations. Header detection mapped every other canonical field with no
manual intervention.

## Coverage — and the policies that unlock it

Before any policy is approved: **10 executable, 1 partial** (the split
review needs `split_threshold`). With the partner approving two engagement
policies via the workflow document —

- `split_threshold = 10000` (required; the client's approval limit)
- `split_window_days = 9` (optional; the engine's default of 0 tests
  same-day splits only, and the planted cluster spans nine days)

— coverage compiles **11 executable, 0 partial, 0 blocked, 0 unsupported**,
and all 11 runs complete:

| Procedure | Status | Findings |
|---|---|---:|
| `ap.document_chain` | ✅ completed | 15 |
| `ap.payment_voucher_reference` | ✅ completed | 3 |
| `ap.segregation_of_duties` | ✅ completed | 5 |
| `ap.split_payment_review` | ✅ completed | 1 |
| `ap.subledger_gl_balance_tie` | ✅ completed | 1 |
| `ap.three_way_receipt_match` | ✅ completed | 10 |
| `ap.vendor_relational_twins` | ✅ completed | 3 |
| `ap.voucher_po_reference` | ✅ completed | 3 |
| `cash.bank_clearing` | ✅ completed | 5 |
| `forensic.closed_value_flow` | ✅ completed | 1 |
| `gl.payment_posting` | ✅ completed | 5 |

**52 findings total** (51 row/pair findings + the one population-level
control observation inside `ap.document_chain` is counted in its 15).

## Planted versus found

| Procedure | Planted | Found | Reconciles? |
|---|---:|---:|---|
| `ap.payment_voucher_reference` | 3 | 3 | Exact |
| `ap.voucher_po_reference` | 3 | 3 | Exact |
| `ap.segregation_of_duties` | 5 | 5 | Exact — all five self-approvals, no false positives |
| `ap.vendor_relational_twins` | 3 | 3 | Exact — the three identity pairs, no false positives |
| `ap.split_payment_review` | 1 | 1 | Exact — the V1042 nine-day cluster, 48,995.00 |
| `ap.subledger_gl_balance_tie` | 1 | 1 | Exact — variance 18,450.00 |
| `gl.payment_posting` | 5 | 5 | Exact — 3 unposted, 2 amount drift |
| `forensic.closed_value_flow` | 1 | 1 | Exact — the Bayview/Meridian ring |
| `cash.bank_clearing` | 6 | 5 | By design — one is inside tolerance |
| `ap.three_way_receipt_match` | 7 | 10 | By design — three arrive from another defect |
| `ap.document_chain` | 5 | 15 | By design — see below |

### Bank clearing: one planted difference is deliberately silent

`bank_gl_closure` matches amounts within a **2% tolerance**:

```python
abs(paid - bank_amt) / abs(bank_amt) > amount_tolerance   # _TOLERANCE = 0.02
```

So the case plants two clearing differences that straddle the band — one at
3.5% (reported) and one at 0.9% (absorbed). The 0.9% item produces no finding,
and that is the correct behaviour.

The lesson: **a silent procedure means "within tolerance", not "nothing
there".** A student who reconciles the bank column by hand will find a
difference the tool never mentions. Whether a sub-2% clearing difference
matters is an auditor's call, not the engine's.

> This was originally an accident. The first run planted random drifts and one
> happened to land at 1.42%, producing an unexplained 5-versus-6. The generator
> now sets both percentages explicitly so the outcome is designed rather than
> lucky.

### Split payments: the window is an audit parameter, not a default

With the engine's default (`split_window_days = 0`, same-day clusters only)
the split review runs clean — the planted cluster spreads its five payments
across nine days precisely so crude same-day detection misses it. Setting the
window to 9 surfaces one TENSION: *5 payments to vendor V1042 between
2026-09-14 and 2026-09-22 total 48995.0 around threshold 10000.0*. The tool
never picks a window silently; choosing one (and defending it) is the
auditor's judgment. That is Assignment 7's real content.

### Three-way match finds three more than were planted

The three vouchers planted for `ap.voucher_po_reference` cite a purchase order
that does not exist. With no reachable PO there is also no reachable goods
receipt, so they surface here as ORPHANs too. One underlying defect, two
procedures.

This is Assignment 4's hidden question. Whether it is one finding or two — and
whether counting the amount twice would overstate the SAD — is judgment the
tool does not make.

### Document chain: five planted, fifteen reported

The chain triage escalates *any* incoherent chain, so its 15 findings are:

- **5 planted for it**: 3 payment/voucher amount differences (all 18%) and
  2 date-order violations — every one reported.
- **3 cross-findings**: the payments citing nonexistent vouchers
  (planted for `ap.payment_voucher_reference`) escalate as ORPHANs.
- **3 cross-findings**: the vouchers citing nonexistent POs
  (planted for `ap.voucher_po_reference`) escalate as ORPHANs.
- **3 cross-findings**: self-approved payments (planted for
  `ap.segregation_of_duties`) escalate as TENSIONs where self-approval is
  the only anomaly; two more self-approvals ride along on chains already
  escalated for missing vouchers.
- **1 population-level control observation**: *5 of 123 payments (4.1%) were
  created and approved by the same actor.*

The same underlying defect appearing in two procedures' output is realistic —
reconciling overlap without double-counting exposure is exactly the SAD
discipline the case teaches.

## Reproducing

```
python case-studies/harborline-marine/generate.py
.venv\Scripts\python case-studies\harborline-marine\instructor\verify_run.py
```

The verify script loads `data/` through the service with three principals
(partner, preparer, reviewer — separation of duties makes a single-principal
run impossible), approves both policies, runs everything coverage marks
executable, and prints every finding for line-by-line reconciliation against
`ANSWER-KEY.md`.
