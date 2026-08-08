# Brief for an independent review

This document is the entry point for a reviewer — human or AI session —
who did **not** build this software and is asked to inspect it before it
is used in anger. It was written by the builder, which is exactly why you
should treat everything in it, and everything else in this repository, as
**claims under test**, not facts.

## Ground rules

1. **You are an inspector, not a repair crew.** Find and report; do not
   fix. A finding you quietly fixed is a finding the record never shows.
   The single exception: you may write your report file (see Deliverable).
2. **Verify, don't summarize.** A claim is confirmed only when you ran the
   command and saw the output. Distinguish in your report between
   *confirmed* (you reproduced it), *contradicted* (you reproduced the
   opposite), and *not checked*.
3. **Do not push, do not commit to main, do not amend history.** Leave the
   working tree as you found it apart from your report file.
4. **The repo's own memory/docs are the auditee.** `docs/ARCHITECTURE.md`,
   `docs/PRODUCTION-READINESS.md`, the manual, and any AI session memory
   describe what the builder *believes*. Your job is to find where belief
   and behavior diverge.

## What this software claims (the things worth attacking)

Each of these is a designed invariant. Each has failed at least once
during development, so none is beyond question:

1. **Honesty about capability.** Coverage reconciles against the executor
   registry: nothing is reported "executable" unless an engine actually
   runs it, and refusals (missing roles/fields/policies) are explicit.
   Attack: feed partial data and check coverage never overclaims.
2. **Reperformance is the read path.** Normalized data is rebuilt from the
   immutable artifact through the approved mapping on every read and
   digest-verified. Attack: tamper with a vault file or the control DB and
   confirm the workbench *refuses* rather than serves unverifiable data.
3. **Separation of duties is server-side.** Proposer cannot approve their
   own mapping; executor cannot review their own run; disposition proposer
   cannot concur with themselves; only the partner locks. Attack: drive
   the HTTP API directly (ignore the UI) with `X-Acting-Principal` and try
   every self-approval.
4. **The lock is evidence, not decoration.** Lock = signed manifest
   anchored to a hash-chained journal; unlock = supersession with a
   permanent reason, never deletion; export refuses when verification
   fails; packets re-verify offline. Attack: mutate post-lock state and
   check drift is named; verify a packet with an independent script.
5. **The API boundary is hardened.** Bearer token on every request (reads
   included), Host/Origin checks, body limits, security headers,
   loopback-only. Attack: unauthenticated reads, forged Origin, oversize
   bodies, path traversal on static files.
6. **The teaching case is honest.** `case-studies/harborline-marine/`
   plants 40 exceptions; `instructor/verify_run.py` reproduces what the
   engine finds. Attack: reconcile engine findings against
   `instructor/ANSWER-KEY.md` — including the one planted difference that
   is *designed* to stay silent (the sub-tolerance bank-clearing drift);
   confirm the docs say so rather than overclaim recall.
7. **Licensing and provenance are consistent.** LICENSE.md (PolyForm
   Noncommercial 1.0.0), one identical header on every source file,
   README disclaimers, `docs/PROVENANCE.md` for the ported code. Attack:
   find a file that escaped, or a public claim the license text does not
   support.

## How to run everything

```
python -m pytest tests -q                      # full suite (150 at handoff)
cd apps/workbench-ui && npm install && npm run build && cd ../..
python -m workbench_api --data <SCRATCH_DIR> --port 8471 --demo
python case-studies/harborline-marine/instructor/verify_run.py
```

The workspace packages are wired by `conftest.py` for pytest; for the two
non-pytest commands set `PYTHONPATH` to the `packages/*/src` directories
plus `apps/workbench-api` (or pip-install the packages per the README).
Use a scratch `--data` directory; never point the server at real data.

## Where the known gaps are already admitted

`docs/PRODUCTION-READINESS.md` is the builder's own gap list (P0/P1/P2).
Two uses for it: (a) anything failing that is *already listed there* is
context, not a discovery — cite it; (b) the sharper question is what
belongs on that list and isn't there.

## Deliverable

Write `docs/reviews/REVIEW-<yyyy-mm-dd>.md` containing:

- **Scope**: what you checked and what you did not.
- **Findings**, ordered by severity, each with: the claim it contradicts,
  exact reproduction steps (commands + output), and impact stated in
  audit-practice terms where applicable (what a CPA relying on this would
  get wrong).
- **Confirmations**: claims you actively tried to break and could not,
  with the commands used — silence is not confirmation.
- **Not checked**: explicitly.
- A one-paragraph **overall verdict**: what this software may honestly be
  used for today, and what it must not be used for yet.

Leave the report uncommitted unless asked. The builder addresses findings
in a separate session; you do not.
