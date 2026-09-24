# Chapter 3 — Evidence and ingestion

## In practice

Audit evidence (AU-C 500) is evaluated on **relevance** and
**reliability**, and reliability depends on source and provenance:
independently obtained evidence (a bank feed) outranks management-prepared
schedules; and evidence you can trace back to its origin outranks evidence
you cannot. Practically, fieldwork starts with a **PBC list** (prepared by
client): the auditor requests specific populations, records what arrived,
and — just as important — records what did *not*.

Two habits distinguish professional data handling:

1. **Preserve the original.** You work on transformed copies, but the file
   the client actually sent is retained unaltered; anyone must be able to
   re-derive your working population from it.
2. **Review the transformation.** Mapping a client's column headings onto
   your working schema is itself audit work — a wrong mapping silently
   corrupts every procedure downstream — so it is prepared by one person
   and approved by another.

And a rule that sounds obvious until the deadline pressure arrives: **you
are not obliged to treat a population as complete because it was
provided.** Absence of evidence is a finding of its own.

Client-prepared reports deserve one more habit: **foot them before you
rely on them.** Footing means re-adding a report's columns yourself and
comparing your totals with the ones printed on it; a report whose detail
does not add up to its own totals is not yet evidence of anything. The most
important total in payables is the **subledger balance**: the unpaid-bills
report should equal the Accounts Payable balance in the general ledger. If
they differ, a bill is missing from one of them, which is a completeness
question.

## In the workbench

The **Sources & Mappings** flow implements exactly those habits:

1. **Upload** (preparer chair). The file's bytes go into a
   content-addressed vault — SHA-256 identity, never modified, never
   deleted (retirement is a tombstone). This is the original-evidence rule
   made structural. The same file uploaded twice is refused, and the
   message names the earlier upload.
2. **Propose a mapping** (preparer). The header detector proposes the
   column mapping for the declared role (Payments, Vendors, …). Two lists
   on the proposal deserve attention: *unmapped headers* (columns the
   schema does not use) and **refused fields** (canonical fields the file
   simply does not contain). A refused field is an audit fact — data the
   client did not provide — not a software complaint.
3. **Approve** (reviewer chair). The mapping is a durable, reviewed
   transformation object. You cannot approve your own proposal.
4. **Normalize** (preparer). Rows load through the approved mapping;
   required-field failures are quarantined ("set aside") with reasons, not
   silently dropped; a Decimal control total accumulates. Check the
   reconciliation: rows in = rows loaded + rows rejected, always. The
   datasets table says why rows were set aside and which sheet rows they
   are, and the Flow Map shows a record set whose every row was set aside
   in red, not as data supplied. Procedures read one dataset per role, the
   latest; an earlier load of the same role is marked "not used".

### Excel workbooks

Excel workbooks (.xlsx) are read directly. Choose the sheet and the row
that holds the column headings; the tool suggests one and previews the
first rows.

- Reading stops at the first blank row, so a totals block below the data
  is left out, and the proposal says how many non-blank rows it ignored.
- The sheet and heading row become part of the reviewed mapping, and each
  record's `source_row` points at the real sheet row.
- Legacy .xls files and damaged workbooks are refused with instructions;
  the original bytes stay in the vault either way.

### QuickBooks Online reports

QuickBooks does not export flat tables. A report exported to Excel has a
title block, then groups (a row holding only a vendor or bank-account name,
its detail rows, and a "Total for …" row), then a grand TOTAL and a
timestamp. The workbench recognizes four standard reports as soon as they
are uploaded and offers a **recipe** for each role the report can feed:

| Report | Can be read as |
|---|---|
| Bill Payment List | Payments |
| Transaction List by Vendor | Vouchers, Payments or Purchase_orders (you choose) |
| Unpaid Bills | Vouchers |
| Vendor Contact List | Vendors |

A report with a single recipe has it chosen for you; one with several
leaves the role blank until you pick. What a recipe does:

- **Foots the report.** Every subtotal and grand total is recomputed from
  the detail rows, for every amount column, before the subtotal rows are
  dropped. A total that disagrees is shown to the reviewer beside the
  mapping, never absorbed.
- **Flattens the groups.** The group name (vendor or paying account) goes
  onto every row as a column.
- **Keeps only what the role is about** (bills for Vouchers, bill payments
  for Payments) and counts every transaction type it left out.
- **Makes payments positive.** QuickBooks signs an amount by the paying
  account: a check is negative in the bank, a card payment positive on the
  card. Payments load as positive paid amounts; the as-exported amount
  stays in the row and the signs seen per account are reported.
- **Warns before approval** when rows will be set aside, for example
  "5 of 5 rows have no voucher_number (Num is blank)".

What QuickBooks does not export is refused, not invented:

- A bill usually has no number unless someone typed the vendor's invoice
  number, so such bills are set aside.
- Vendors are known by name only.
- No standard vendor report says which bill each payment settled. Bills and
  Applied Payments shows them side by side with nothing linking them, so it
  gets no recipe.
- The General Ledger export nests sub-accounts, so it has no mapping
  recipe. It is recognized and labelled, so a filename guess cannot map it
  as a flat table; its use is the AP tie below.

A report with customized columns is not recognized; map it the ordinary
way. The recipe is part of the reviewed mapping and its digest. Once a
mapping is loaded it shows "loaded ✓": the file and the approved mapping
cannot change, so loading it again would only repeat the same rows, and
the workbench refuses to.

### The AP subledger-to-ledger tie

When both an **Unpaid Bills** export and a **General Ledger** export are
uploaded, Sources shows a panel to build the **AP control balance**:

1. The subledger balance is Unpaid Bills' grand-total open balance; the
   ledger balance is the Accounts Payable account's ending balance
   (Beginning Balance plus the period's activity). Both reports are footed
   first, and one that does not foot is refused.
2. The result is saved as a small schedule,
   `AP control balance <date> - QuickBooks.csv`, whose provenance names
   both exports by SHA-256. It
   states the dates of both sides and flags when they differ from each
   other or from the engagement's period end, so you confirm the tie
   compares like with like.
3. You propose, approve and load the schedule like any other file, and
   the **AP subledger-to-GL control-account tie** procedure can then run.
   A difference becomes a finding; agreement is recorded as a clean run.

**Bulk loading batches the clicks, never the review.** A real engagement
arrives as ten files, not one. Select them all in one upload; the
workbench suggests each file's role from its name (`bank.csv` → Bank,
`ap_invoices.csv` → Vouchers) and refuses to guess when a name is
ambiguous — a suggestion you can override before proposing. **Propose
all** files in one pass, the reviewer chair **approves all** proposals in
one pass, and the preparer **normalizes all** approved mappings in one
pass. Each file still gets its own proposal, its own approval, its own
reconciliation, and its own journal entry; a file that fails (a damaged
workbook, an unrecognizable name) is reported individually and never
blocks the rest.

**Reperformance is the read path.** The workbench does not store your
normalized table as the working copy. Every time any screen needs the
data, it re-derives the table from the immutable artifact through the
approved mapping and verifies the result against the recorded digest — and
refuses to serve data it cannot reproduce. What you see is always what the
evidence still supports.

## In Harborline

Load all ten files from `data/` in one bulk pass — every Harborline
filename infers its role, so the suggestions should match the walkthrough
exactly (or start from `--demo`, which performs this whole chapter through
the three chairs, batch path included). All ten load with **zero
rejected rows** — and two mappings refuse fields:

- `Purchase_orders` refuses `created_on` / `approved_on` — the PO extract
  genuinely lacks approval timestamps. This is scope limitation #1 in the
  audit plan, discovered independently by the tool at ingestion.
- `Value_flows` refuses `flow_type`.

Write the PO refusal down now, the way you would on a real engagement. In
chapter 7 it belongs in the workpaper's limitations, and the engagement
brief told you it was coming: management did not provide approval
timestamps, and nothing downstream can conjure them.
