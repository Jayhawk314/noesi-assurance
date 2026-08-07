# Harborline Marine Group — integrated audit practice case

A complete, fabricated accounts-payable audit you can work end to end: 836 rows
of client data across ten record sets, with **40 exceptions deliberately
planted** and a verified instructor key.

Everything here is fictional. The case is original — written in the tradition of
published integrated audit practice sets, not derived from any of them.

## Who this is for

Two audiences, one case:

- **Learning the audit.** Work the assignments in `docs/04-assignments.md` with
  LibreOffice Calc and the workpaper templates. You never have to run the
  software at all.
- **Learning the workbench.** Follow `docs/03-walkthrough.md` to load the same
  data into Noesi and let the coverage compiler tell you what the data can and
  cannot prove.

Doing both is the point: form your own expectation in a spreadsheet, then see
whether the tool agrees with you.

For the full pairing — each audit-process step taught alongside the workbench
step that implements it, with this case as the running example — read the
**manual** at [`docs/manual/`](../../docs/manual/README.md) in the repo root.

## Folder map

```
data/                 the client's exports — upload these, open these in Calc
docs/
  01-engagement-brief.md    who the client is and why we are here
  02-audit-plan.md          materiality, risks, planned procedures
  03-walkthrough.md         load the case into the workbench, step by step
  04-assignments.md         graded tasks, spreadsheet-first
workpapers/           CSV templates that open directly in LibreOffice Calc
instructor/           answer key and a verified run log — do not distribute
generate.py           rebuilds data/ and the answer key from a fixed seed
```

## The data

| File | Rows | Canonical role |
|---|---:|---|
| `vendors.csv` | 44 | Vendors |
| `employees.csv` | 13 | Employees |
| `purchase_orders.csv` | 123 | Purchase_orders |
| `goods_receipts.csv` | 119 | Goods_receipts |
| `vouchers.csv` | 123 | Vouchers |
| `payments.csv` | 123 | Payments |
| `bank.csv` | 119 | Bank |
| `gl.csv` | 120 | GL |
| `ap_control_balance.csv` | 1 | AP_control_balance |
| `value_flows.csv` | 51 | Value_flows |

All CSV, all UTF-8. LibreOffice Calc opens them directly — accept the default
comma separator.

## Regenerating

```
python case-studies/harborline-marine/generate.py
```

The seed is fixed, so the output is byte-identical every time and the answer key
is rewritten from the same run that writes the data. The key therefore cannot
drift from the population — it is a consequence of the generator, not a claim
about it.

## Before you start: what actually runs today

Verified by loading this case through the engine (see
`instructor/VERIFIED-RUN.md`, which records the run verbatim and is the
authority on tool behaviour). **All eleven procedure contracts execute** —
with two engagement policies the partner must approve first:

- `split_threshold = 10000` (the client's written approval limit), and
- `split_window_days = 9` (the testing window — an audit judgment; the
  engine's default of 0 tests same-day clusters only, and the planted
  cluster spans nine days on purpose).

Expect **52 findings**, reconciling to the 40 planted exceptions plus
documented cross-findings and one deliberate silence inside the 2% clearing
tolerance. The assignments still do every procedure spreadsheet-first —
forming your own expectation before the tool reports is the point of the
case, not a workaround.

> An earlier build of the workbench could execute only six of the eleven
> contracts while coverage claimed ten were runnable, and the threshold
> policy could not be set at all. That defect is fixed (coverage now
> reconciles against the executor registry), but it remains a good story:
> the tool's honesty about its own capability had to be audited too.
