# Final independent review of RR1

**Date:** 2026-09-28  
**Reviewed fix:** `da6a96c` (`778868c..da6a96c`)  
**Current verification HEAD:** `09975ce`  
**Method:** report only; no application or test code changed

## Scope

This review rechecked the last open residual finding, RR1 in
`REVIEW-2026-09-27-residuals.md`: removing a cycle left that cycle's stored
policies and procedure-selection decisions active in the workflow document, so
they silently returned if the cycle was later enabled again.

The two commits after the fix (`ba56586` and `09975ce`) add only the Kestrel
Valley case, its frozen answer key, its unchanged-engine runner, and the run
findings. They do not alter the application fix reviewed here.

## Findings

No findings.

## RR1 result

**Closed.** When a cycle is removed, the service now:

- removes policies that are owned only by cycles no longer in scope;
- removes stored selections for procedures belonging to removed cycles;
- retains those decisions in the workflow's `retired` history, including the
  actor and owning cycle;
- preserves policies still needed by another enabled cycle;
- preserves policies used by the original payables procedures; and
- does not restore retired decisions if the cycle is enabled again.

The original RR1 reproduction now passes. I also attacked the fix with two
cycles enabled and removed separately. That covered a required inventory
policy, an optional inventory policy, an optional cash policy, inventory and
cash procedure selections, and the payables `split_window_days` policy. The
correct decisions were retired at each removal, the payables policy remained,
re-enabling both cycles restored none of the retired decisions, and repeating
the same scope update did not duplicate retirement records.

Existing guards also remain in place: a cycle cannot be removed while an
active risk links one of its procedures or after one of its procedures has run.

## Other confirmations

- The earlier RR2 documentation mismatch is also corrected: the root README
  now states Python 3.12, matching every package's `requires-python` value.
- Full suite: **266 passed** in 23.78 seconds.
- Dependency check: **No broken requirements found**.
- Harborline verifier: **11 executable procedures, 52 findings**.
- The working tree's pre-existing untracked files and excluded directories
  were not read, staged, or modified as part of this review.

## Not reviewed

This was the final RR1 remediation gate, not an independent audit of the new
Kestrel Valley specification, answer key, runner, or K1-K14 conclusions. Their
presence was checked only to establish that the commits after `da6a96c` did not
change application code.

## Verdict

`da6a96c` resolves RR1 without changing the Harborline result. The residual
review gate is clean. Work can proceed from the Kestrel Valley unchanged-engine
findings; those findings should drive any proposed engine edits, with each edit
approved before implementation as required by the rollout plan.
