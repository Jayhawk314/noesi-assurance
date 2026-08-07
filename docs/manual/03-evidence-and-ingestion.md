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

## In the workbench

The **Sources & Mappings** flow implements exactly those habits:

1. **Upload** (preparer chair). The file's bytes go into a
   content-addressed vault — SHA-256 identity, never modified, never
   deleted (retirement is a tombstone). This is the original-evidence rule
   made structural. Excel workbooks are refused at the next step with
   instructions to export CSV — the workbook bytes still stay in the vault
   as evidence of what was received.
2. **Propose a mapping** (preparer). The header detector proposes the
   column mapping for the declared role (Payments, Vendors, …). Two lists
   on the proposal deserve attention: *unmapped headers* (columns the
   schema does not use) and **refused fields** (canonical fields the file
   simply does not contain). A refused field is an audit fact — data the
   client did not provide — not a software complaint.
3. **Approve** (reviewer chair). The mapping is a durable, reviewed
   transformation object. You cannot approve your own proposal.
4. **Normalize** (preparer). Rows load through the approved mapping;
   required-field failures are quarantined with reasons, not silently
   dropped; a Decimal control total accumulates. Check the reconciliation:
   rows in = rows loaded + rows rejected, always.

**Reperformance is the read path.** The workbench does not store your
normalized table as the working copy. Every time any screen needs the
data, it re-derives the table from the immutable artifact through the
approved mapping and verifies the result against the recorded digest — and
refuses to serve data it cannot reproduce. What you see is always what the
evidence still supports.

## In Harborline

Load all ten files from `data/` with the roles listed in the walkthrough
(or start from `--demo`, which performs this whole chapter through the
three chairs). All ten load with **zero rejected rows** — and two mappings
refuse fields:

- `Purchase_orders` refuses `created_on` / `approved_on` — the PO extract
  genuinely lacks approval timestamps. This is scope limitation #1 in the
  audit plan, discovered independently by the tool at ingestion.
- `Value_flows` refuses `flow_type`.

Write the PO refusal down now, the way you would on a real engagement. In
chapter 7 it belongs in the workpaper's limitations, and the engagement
brief told you it was coming: management did not provide approval
timestamps, and nothing downstream can conjure them.
