# Clicked evidence replacement check — 25 November 2026

The outstanding replacement/What Changed check from the 3 October finish map
passes on a fresh invented engagement. No product code needed changing.

## Reproduce

Build the Workbench UI with `npm run build` in `apps/workbench-ui`. With
Playwright and its Chromium browser installed in the chosen Python environment,
run from the repository root:

```
python tests/browser/check_replacement.py --out .tmp/replacement-check-new
```

The output directory must not already exist. The script starts its own server
on an OS-selected unused port, with a fresh store inside that directory. It
stops the server on success or failure. It never opens an existing engagement.
The local server log contains a session token; it is not retained in this
document's evidence files. No authentication material is committed.

## Observed and asserted through the UI

| Step | Result |
|---|---|
| Create engagement; upload, confirm mappings and load vouchers/payments | Three vouchers and three matching payments in a fresh invented engagement. |
| Run `ap.payment_voucher_reference` | Completed with zero findings; run is current. |
| Upload revised vouchers and click **replaces it** | V3 is removed. Original source is explicitly marked no longer used. |
| Open Runs & Findings | Original run warns that loaded data changed and it must be rerun. |
| Open What Changed | Three voucher rows become two; V3/800.00 removed; net change -800.00. One stale procedure would move from zero findings to one. The P3/V3 finding is new and needs a disposition. |
| Click **rerun** on What Changed | No pending stale runs remain on that screen. |
| Reopen Runs & Findings | Two completed runs: the original stays historical and stale; the rerun is current. Exactly one current finding names payment P3 and missing voucher V3, amount 800. |

The script reported no uncaught browser page errors. It asserts outcomes and
exits unsuccessfully on a mismatch; its output is not just an observation log.
The Workbench UI build passed. An independent agent reviewed the script,
captured text, result file and screenshots and found no blocking issue.

Evidence from the passing run:

- [What Changed screenshot](evidence/replacement-2026-11-25/what-changed.png)
- [Current finding screenshot](evidence/replacement-2026-11-25/current-finding.png)
- [What Changed text](evidence/replacement-2026-11-25/what-changed.txt)
- [Current finding text](evidence/replacement-2026-11-25/current-finding.txt)

This is a bounded check of replacing Vouchers and reperformance of one
procedure. It does not test saved disposition preservation, other replacement
roles, reopen/export persistence, materiality classifications, console errors
or network failures. No materiality was set: the screen explicitly states its
default significance treatment. It does not establish overall product or
real-client readiness; the remaining finish-map and custody limits still apply.

The initial continuation script incorrectly assumed the newest run appeared
first. The UI preserves the historical run above the rerun; the final check
identifies the current and historical runs by their stale status instead.
