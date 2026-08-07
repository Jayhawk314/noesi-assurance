# Walkthrough — running the case in the workbench

Load the Harborline case into Noesi and watch coverage compile. Roughly 30
minutes. Read `04-assignments.md` first if you would rather form your own
expectation before the tool gives you one — that is the better learning order.

## 0. Know this before you start

**The workbench binds one principal per process.** The audit domain enforces
separation of duties: whoever proposes a mapping may not approve it. Because
the running process authenticates as exactly one person, you must **restart the
server under a different `--principal` to change hats.** There is no in-app user
switch.

This is a real limitation of the current build, not a quirk of the case. Plan
for it: you will restart three times.

## 1. Build and start

```
cd apps\workbench-ui && npm install && npm run build && cd ..\..
.venv\Scripts\python -m workbench_api --principal "u:partner" --data .\case-run
```

Open the address it prints. The page carries its own session token — there is
nothing to paste.

## 2. Create the engagement (as partner)

Client name **Harborline Marine Group**, period end **2026-12-31**.

Creating it makes `u:partner` the partner. On the **Team** tab, add:

| Principal | Role |
|---|---|
| `u:preparer` | preparer |
| `u:reviewer` | reviewer |

Note the engagement id from the URL or the engagement list; you will come back
to the same `--data` directory each restart.

## 3. Upload and map (as preparer)

Restart:

```
.venv\Scripts\python -m workbench_api --principal "u:preparer" --data .\case-run
```

On **Sources & Mappings**, upload all ten files from `data/`, then propose a
mapping for each with the role below. The header detector does the column work;
you are confirming its proposal, not typing it.

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

**Look at the refusals.** Two mappings refuse fields, and both are real audit
facts rather than software problems:

- `Purchase_orders` refuses `created_on` and `approved_on` — the timestamps are
  genuinely absent, exactly as the engagement brief said.
- `Value_flows` refuses `flow_type`.

Record the PO refusal. It is scope limitation #1 from the audit plan, and the
tool has now found it independently.

## 4. Approve the mappings (as reviewer)

Restart as `u:reviewer` and approve all ten. You cannot approve your own work,
which is why this is a separate step and a separate person.

## 5. Normalize (as preparer)

Restart as `u:preparer` and normalize each approved spec. Check the
reconciliation on each: **rows in should equal rows loaded, with zero
rejected**, for all ten files. If anything is rejected, the mapping is wrong.

Expected control totals worth noting in your workpaper:

- Vouchers: the AP subledger figure you will tie out later.
- Payments: total disbursements for the year.

## 6. Read the flow map

Open the **Flow Map** tab. Every box should now be green with a row count. This
is the moment the case pays off — you can see the whole purchase-to-pay cycle
and, on each arrow, whether the procedure testing that link can run.

Click a box to see what it unlocks. Click an arrow to see the procedures on it.

## 7. Run the procedures — and meet the wall

Coverage will report **10 executable, 1 partial**. That is optimistic. When you
actually run them, only six complete:

| Procedure | What happens |
|---|---|
| `cash.bank_clearing` | ✅ completes — 5 findings |
| `gl.payment_posting` | ✅ completes — 5 findings |
| `ap.subledger_gl_balance_tie` | ✅ completes — 1 finding |
| `ap.three_way_receipt_match` | ✅ completes — 10 findings |
| `forensic.closed_value_flow` | ✅ completes — 1 finding |
| `ap.split_payment_review` | ⚠️ partial — needs a `split_threshold` policy, and there is no way to set one |
| `ap.payment_voucher_reference` | ❌ errors — no executor registered |
| `ap.voucher_po_reference` | ❌ errors — no executor registered |
| `ap.document_chain` | ❌ errors — no executor registered |
| `ap.segregation_of_duties` | ❌ errors — no executor registered |
| `ap.vendor_relational_twins` | ❌ errors — no executor registered |

**This is the most important lesson in the case.** Coverage claims a procedure
is executable when all it has verified is that the *data* is present. It does
not check that an executor exists. A tool whose whole pitch is honesty about
what it can prove is, here, overclaiming.

For the five that error, do the work in LibreOffice instead —
`04-assignments.md` covers each one. That is not a consolation prize: an
auditor's judgment does not depend on a vendor shipping a feature.

## 8. Disposition the findings

On **Runs & Findings** you should have 22 findings from the six working
procedures. Every one needs a disposition:

- `cleared` — investigated, no misstatement
- `unadjusted` — a real difference the client will not fix (flows to the SAD)
- `adjusted` — the client corrected it
- `waived` — below clearly trivial and not qualitatively significant
- `follow_up` — unresolved at this stage

Write a note on every one. "Cleared" with no reason is not documentation.

Mind the distinction the tool will not make for you: a payment that never
cleared the bank is a $20,000 *exposure*, but the *misstatement* is whatever the
investigation concludes — possibly zero, if it cleared in January.

## 9. Review, complete, lock

Runs must go `completed → reviewed → approved`, and separation of duties applies
again, so reviewing means another restart as `u:reviewer`.

Then on **SAD & Completion**: set materiality to **420000**, mark the stages,
and work the six completion checks. Readiness will stay red until every blocker
clears — read them; each names exactly what is outstanding.

Finally, as `u:partner`, lock. Locking signs a snapshot and cannot be undone.
Export the evidence packet and open the workpaper.

## What you should have at the end

- Ten normalized datasets, zero rejected rows.
- A documented scope limitation for the missing PO approval timestamps.
- 22 tool findings, each disposed with a written note.
- Five procedures performed manually because the software could not run them.
- A signed, offline-verifiable evidence packet.
- An honest limitations section that says what this audit did *not* cover.
