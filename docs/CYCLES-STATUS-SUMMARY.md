# Expanded audit flow: current status

*Status on 2026-09-26. This is the short handoff; see
[CYCLES-ROLLOUT.md](CYCLES-ROLLOUT.md) for the detailed plan and
[the independent review](reviews/REVIEW-2026-09-26.md) for findings and evidence.*

## Where we are

The private Oceanview practice-case run is complete across all ten assignments. It was
used to discover missing capabilities and exercise the expanded engine. Oceanview's
case content and judgments remain in the private repository; none were copied here.

That work produced 14 opt-in procedures covering:

- planning and preliminary analytics;
- controls sampling;
- receivables and confirmation evaluation;
- the search for unrecorded liabilities;
- cash and bank reconciliations;
- inventory count tracing and pricing;
- adjusted trial balance and completion.

An independent review found five problems: empty populations could appear clean, cycle
scope could be bypassed, a partly inspected multi-line check could appear inspected,
the new package dependency was undeclared, and A/R detail rows were evaluated at the
wrong grain. All five fixes are implemented locally. The cycle engine identifier is now
`cycles-v2`, the full suite reports **260 passing tests**, and `pip check` reports no
broken requirements.

The fixes have not yet received an independent re-review. Nothing is pushed or released.

## Oceanview versus Harborline

Oceanview is complete as the first private practice run, but it is not enough evidence
to ship the expanded flow. The procedures were developed while working that one case,
so a second independently written case is still required to expose overfitting.

Harborline, the public teaching case, has not been expanded. Its learner-facing flow
still has:

- 11 AP procedures;
- 52 findings;
- the existing lessons, examples, and videos.

If the current local readiness change ships, Harborline will require a recorded decision
on every finding before lock. That means roughly 45 additional non-dollar decisions on
top of the seven SAD items. We still need to decide whether this stricter lock should
ship separately from the cycle rollout.

## Are the lessons and videos accurate?

Yes, for the current released learner experience. The new cycle procedures are not yet
available through the learner-facing app, so the existing limitation statements remain
accurate in context.

Once the expanded flow is usable in the app, six video scenes will need new lines:

- L2: analytics;
- L5: sampling;
- L6: unrecorded liabilities;
- L7: receivables and confirmations;
- L8: bank reconciliations;
- L9: inventory count tracing and pricing.

Do not change those videos yet. Update them last, after the app workflow and lesson text
are stable, so the estimated 400–500 ElevenLabs credits are spent only once.

## What happens next

1. Independently re-review the five engineering fixes.
2. Write the QuickBooks-shaped second case and freeze its answer key before running
   Noesi.
3. Run the unchanged engine and record every break or disagreement without bending the
   case to fit it.
4. Make the justified engine and data-shape changes.
5. Add QuickBooks recipes for trial balance, A/R aging, inventory valuation, and bank
   reconciliation reports.
6. Add the Workbench screen for cycle selection and cycle policies.
7. Add public demo data for the new cycles.
8. Update the app lessons, manual, and explanatory panels.
9. Re-record the six affected video scenes last.
10. Run the final regression and release review before any push.

## Immediate decision

The next action is the independent re-review. If it passes, proceed to the
QuickBooks-shaped second case. Do not update the learner lessons or videos until the new
workflow is stable and actually available in the app.

## Projected expansion timeline

A realistic projection is **3–5 focused weeks**. If the work is intermittent, or the
second case exposes substantial engine problems, allow **6–8 weeks**.

| Phase | Estimated effort | Result |
|---|---:|---|
| Independent re-review | 1–2 days | Confirm the five fixes or return new findings |
| QuickBooks-shaped case and frozen answer key | 2–4 days | Independent expected results written before Noesi runs |
| Run the unchanged engine | 1–2 days | Every break and disagreement recorded |
| Engine and data-shape corrections | 3–6 days | Trial balance, A/R, inventory and reconciliation inputs handled honestly |
| QuickBooks import recipes | 3–5 days | Realistic exports enter the approved ingestion path |
| Workbench cycle UI and policies | 3–5 days | Learners can select cycles and set approved policies |
| Demo data and integration testing | 2–4 days | New procedures can be demonstrated through the full flow |
| App lessons and manual | 2–4 days | Learner content matches the working application |
| Video scene replacement and QA | 1–3 days | Six affected scenes updated and checked |
| Final regression and release review | 1–2 days | Evidence for the final release decision |

These phases may overlap where safe, but lessons and videos deliberately remain near
the end because they depend on the final application behavior and wording.

## When lesson work starts

Draft the new lesson structure after the QuickBooks-shaped case has exposed the final
workflow. Do not finalize or publish the lesson changes until:

- the justified engine changes are complete;
- the QuickBooks recipes work through normal ingestion;
- the Workbench cycle-selection and policy screen exists;
- the public demo data completes the full flow successfully.

On the focused schedule above, lesson drafting begins around week 2 or 3 and final app
lesson updates occur around weeks 3 or 4.

## When video work starts and when to buy credits

Video work comes last, provisionally around weeks 4 or 5. The current plan is not to
replace six complete videos. It is to replace one affected scene in each of L2, L5, L6,
L7, L8 and L9, then splice those scenes into the existing videos.

The preliminary voice estimate remains **about 400–500 ElevenLabs credits**, before any
additional clips requested later. Do not buy credits yet. Purchase them only after:

1. the application workflow is stable;
2. the final lesson wording is approved;
3. the six replacement scripts are approved;
4. their exact character count has been calculated;
5. the resulting credit cost is approved.

This ordering is intended to avoid paying to voice lines that later need another edit.

## What is required to finish

Required for the learner-facing expansion:

- independent re-review of the five fixes;
- the independent QuickBooks-shaped case and answer key;
- engine corrections justified by that case;
- QuickBooks import recipes;
- the cycle-selection and policy UI;
- public cycle demo data;
- resolution of the two competing misstatement summaries;
- app lesson, manual and explanatory-panel updates;
- six video scene replacements;
- full regression and release review;
- a decision on whether Harborline's stricter lock ships separately.

Important work that may follow the first learner release if its limits are stated:

- a configurable clearly-trivial threshold;
- fuller prior-year balance support;
- structural graph and fusion integration;
- a real-client pilot alongside a licensed CPA.
