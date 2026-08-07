# Walkthrough — running the case in the workbench

Load the Harborline case into Noesi and work it end to end. Roughly 45
minutes. Read `04-assignments.md` first if you would rather form your own
expectation before the tool gives you one — that is the better learning
order. For the full pairing of tool steps with the audit process they
implement, read this alongside the manual (`docs/manual/` at the repo
root).

> **Shortcut:** `noesi-workbench --demo` performs steps 1–5 for you through
> the real three-chair path and opens with coverage green. Use it when you
> want to start at step 6. This walkthrough does everything by hand once,
> because the ingestion review is worth experiencing.

## 0. Chairs, not restarts

The workbench authenticates one local operator and lets you act as any
principal via the **acting as** control in the header. Separation of duties
is enforced server-side against the *acting chair*: whoever proposes a
mapping cannot approve it, whoever runs a procedure cannot review it. You
will switch chairs several times in this walkthrough — the header always
shows which one you are sitting in, and every action is journaled under it.

## 1. Build and start

```
cd apps\workbench-ui && npm install && npm run build && cd ..\..
.venv\Scripts\noesi-workbench --data .\case-run
```

Open the address it prints. The served page carries its own session token —
there is nothing to paste.

## 2. Create the engagement (partner chair)

Client name **Harborline Marine Group**, period end **2026-12-31**.

Creating it makes your current chair the partner. On the **Team** tab, add:

| Principal | Role |
|---|---|
| `u:preparer` | preparer |
| `u:reviewer` | reviewer |

## 3. Upload and map (switch to `u:preparer`)

On **Sources & Mappings**, upload all ten files from `data/`, then propose
a mapping for each with the role below. The header detector does the column
work; you are confirming its proposal, not typing it.

| File | Role |
|---|---|
| `vendors.csv` | Vendors |
| `employees.csv` | Employees |
| `purchase_orders.csv` | Purchase_orders |
| `goods_receipts.csv` | Goods_receipts |
| `vouchers.csv` | Vouchers |
| `payments.csv` | Payments |
| `bank.csv` | Bank |
| `gl.csv` | GL |
| `ap_control_balance.csv` | AP_control_balance |
| `value_flows.csv` | Value_flows |

**Look at the refusals.** Two mappings refuse fields, and both are real
audit facts rather than software problems:

- `Purchase_orders` refuses `created_on` and `approved_on` — the
  timestamps are genuinely absent, exactly as the engagement brief said.
- `Value_flows` refuses `flow_type`.

Record the PO refusal. It is scope limitation #1 from the audit plan, and
the tool has now found it independently.

## 4. Approve the mappings (switch to `u:reviewer`)

Approve all ten. Try approving one while still sitting in the preparer
chair first — the refusal is the separation-of-duties gate working.

## 5. Normalize (switch to `u:preparer`)

Normalize each approved spec. Check the reconciliation on each: **rows in
should equal rows loaded, with zero rejected**, for all ten files. If
anything is rejected, the mapping is wrong.

## 6. Read the flow map

Open the **Flow Map** tab. Every box should now be green with a row count —
the whole purchase-to-pay cycle, and on each arrow, whether the procedure
testing that link can run. Click a box to see what it unlocks; click an
arrow to see the procedures on it.

## 7. Set the engagement policies (partner chair)

Coverage reads **10 executable, 1 partial**: the split-payment review needs
the client's approval threshold. On the **Coverage** tab set:

- `split_threshold` = **10000** — Harborline's written policy requires a
  second signature above $10,000.
- `split_window_days` = **9** — your testing window. The engine's default
  is 0 (same-day clusters only), and a clerk splitting invoices to dodge a
  signature has no reason to write every check the same afternoon. Nine
  days is a judgment, not a fact — Assignment 7 asks you to defend it.

Coverage moves to **11 executable**. Approved policies apply to every run
automatically.

## 8. Run the procedures (preparer chair)

Run all eleven. All eleven complete. Expected findings:

| Procedure | Findings |
|---|---|
| `ap.document_chain` | 15 |
| `ap.payment_voucher_reference` | 3 |
| `ap.segregation_of_duties` | 5 |
| `ap.split_payment_review` | 1 |
| `ap.subledger_gl_balance_tie` | 1 |
| `ap.three_way_receipt_match` | 10 |
| `ap.vendor_relational_twins` | 3 |
| `ap.voucher_po_reference` | 3 |
| `cash.bank_clearing` | 5 |
| `forensic.closed_value_flow` | 1 |
| `gl.payment_posting` | 5 |

**52 findings** — and three deliberate lessons hiding in the counts:

1. **Bank clearing shows 5, not 6.** One planted difference sits at 0.9%,
   inside the engine's 2% tolerance, and produces no finding — correctly.
   A silent procedure means *within tolerance*, not *nothing there*.
   Reconcile the bank column by hand and you will find what the tool never
   mentions; deciding whether it matters is your call.
2. **Three-way match shows 10, not 7.** The three vouchers citing phantom
   POs have no reachable goods receipt either, so one defect surfaces in
   two procedures. Whether that is one finding or two on the SAD is
   Assignment 4's hidden question.
3. **The split review found its cluster only because you set the window.**
   Re-run it after clearing `split_window_days` and watch it go silent on
   the same data. Same population, different parameter, different
   evidence — which is why the parameter is documented as a policy.

## 9. Disposition the findings

Every finding needs a disposition with a written note:

- `cleared` — investigated, no misstatement (the note says why)
- `unadjusted` — a real difference the client will not fix (flows to SAD)
- `adjusted` — the client corrected it
- `waived` — below clearly trivial *and* not qualitatively significant
- `follow_up` — unresolved; blocks completion until it is not

Mind the distinction the tool will not make for you: a payment that never
cleared the bank is a $20,000 *exposure*; the *misstatement* is whatever
the investigation concludes — possibly zero, if it cleared in January. And
watch the cross-findings from lesson 2: clear one side by reference to the
other, or you will double-count ~27,000 on the SAD.

## 10. Review, complete, lock

Runs walk `completed → reviewed → approved`: review each as `u:reviewer`,
approve as the partner chair (the tool refuses to let the same chair do
both — including the chair that executed).

On **SAD & Completion**: set materiality **420000** (performance
materiality and clearly-trivial derive automatically — check them against
the audit plan), mark both stages complete, and work the six completion
checks with real notes. Readiness stays red until every blocker clears —
read the blockers; each names exactly what is outstanding. That is the
gate working, not an error.

As the partner chair, **lock**. Export the evidence packet and open the
workpaper: your scope limitations, disposition notes, review chains, and
the signed manifest are all in it, and the packet re-verifies offline.

## 11. Optional but recommended: reopen it

Real files get reopened; do it once here so the mechanics are familiar.
As partner, unlock with a specific reason (it becomes a permanent part of
the record). Reperform one procedure, watch the re-lock refuse until the
rerun is reviewed and approved, then re-lock and re-export. The packet now
carries a **lock amendment history**: both lock generations, both
signatures, and your reason. Nothing was deleted — that is the point.

## What you should have at the end

- Ten normalized datasets, zero rejected rows.
- A documented scope limitation for the missing PO approval timestamps.
- 52 tool findings, each disposed with a written note, reconciled to your
  own spreadsheet work from the assignments.
- Two engagement policies set and defended (threshold, window).
- A signed, offline-verifiable evidence packet — and, if you did step 11,
  a verifiable amendment history behind it.
- An honest limitations section that says what this audit did *not* cover.
