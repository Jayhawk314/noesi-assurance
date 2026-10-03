# Chapter 4 — Coverage and scoping

## In practice

Between "here is the data" and "run the tests" sits a scoping question
auditors answer implicitly on every engagement: **which of the planned
procedures can actually be performed with the evidence obtained?** A
procedure needs specific populations with specific fields; if the client's
extract lacks them, the honest options are to request better data, perform
an alternative procedure, or record a scope limitation — never to quietly
pretend the test was done.

Some procedures also need an **engagement-level parameter** that is an
audit decision, not a data fact: an approval threshold, a testing window.
Those parameters must be set deliberately and documented, because the
procedure's meaning depends on them.

## In the workbench

The **Coverage** tab compiles every procedure contract against the data
actually normalized and the policies actually set, and reports one of
four statuses — each an honest, distinct claim:

| Status | Claim |
|---|---|
| `executable` | Required data present, required policies set, an executor registered — this will run |
| `partial` | Data present but fields or a required policy are missing |
| `blocked` | A required population was not supplied at all |
| `unsupported` | **This build has no executor for the contract.** No amount of data changes it; no evidence request is generated for it |

The fourth status is the tool's most important honesty commitment:
*"the data supports it" and "this software can run it" are different
claims*, and coverage refuses to conflate them. (Historical note: an
earlier build conflated exactly this — coverage said `executable` for five
procedures that then failed at runtime. The reconciliation against the
executor registry exists because of that defect.)

**Evidence requests.** Missing roles, fields, and policies are grouped
into a request list — effectively the incremental PBC list, each item
annotated with the procedures it would unlock. Received evidence changes
coverage once you load it: upload the file, confirm its mapping and load it
on Sources & Mappings. Coverage then recompiles. A newly supported procedure
shows as executable but has not run, because receiving a file is not
execution.

**Policies.** Engagement policies are set on Scope & Policies (or the
workflow API) and take effect for every subsequent run: the run inherits the
value set and records it in its manifest. The catalog names each
procedure's required and optional policies. Examples include a split-payment
threshold and window, allowance rates by aging bucket, journal-entry
authorization and round-amount thresholds, sampling tolerable misstatement,
bank-clearing days, analytics thresholds, and the report date. They are audit
judgments, never values the engine should infer from the desired answer.

**Deselection.** A procedure you will not perform is deselected *with a
rationale*, which travels to the workpaper ("procedures not executed").

## In Kestrel

The demo scopes the full audit and records the auditor's policies.
Read Coverage before reading any findings. It should distinguish executable
procedures from procedures blocked by genuinely absent populations and from
alternative sampling methods that were not selected. In particular, missing
receiving and approver evidence remains visible; it is not hidden by the fact
that other payables procedures can run.

Change one judgment in a scratch engagement and watch coverage respond. For
example, omit the five allowance rates and `ar.listing_tie` can still tie the
aging to the ledger, but it cannot claim to have recomputed management's
allowance method. The important lesson is not a fixed count of green rows;
it is that every green row can explain the data and judgment that make it
executable.
