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
actually normalized and the policies actually approved, and reports one of
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
coverage only after a preparer validates it and a *different* reviewer
approves the validation; a newly supported procedure becomes
`ready_to_run`, because receiving a file is not execution.

**Policies.** Engagement policies are set on the Coverage screen (or the
workflow API) and take effect for every subsequent run: the run inherits
the approved policy; an explicit per-run value overrides it. Two exist
today:

- `split_threshold` (required by the split-payment review) — the client's
  approval limit.
- `split_window_days` (optional) — how many days a payment cluster may
  span. The default is 0 (same-day only); widening it is an audit judgment
  you make explicitly, never a default the tool picks for you.

**Deselection.** A procedure you will not perform is deselected *with a
rationale*, which travels to the workpaper ("procedures not executed").

## In Harborline

With all ten files loaded, coverage reads **10 executable, 1 partial** —
the split review is partial because `split_threshold` is not yet set.
Harborline's written policy requires a second signature above **$10,000**,
so set `split_threshold = 10000`. Coverage moves to **11 executable**.

Then the judgment call: set `split_window_days = 9` — and be ready to
defend that number, because Assignment 7 will ask you to. Why nine and not
same-day? Because a clerk avoiding a second signature has no reason to
write all the checks on the same afternoon. Why nine and not ninety?
Because the wider the window, the more innocent payment patterns you sweep
in. There is no universally right answer; there is only *your* answer,
documented. That is what "an audit parameter, not a default" means.
