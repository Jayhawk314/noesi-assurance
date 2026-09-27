# Cycles rollout: what was built, what it changes, what is left

*Written 2026-09-26. The plan for taking the new cycle procedures from engine code to
something a learner can use with QuickBooks and Excel. Nothing here is pushed or live
yet. Read with [CYCLES-DESIGN.md](CYCLES-DESIGN.md) (how the engine works, and its
provenance and limits), [CYCLES-STATUS-SUMMARY.md](CYCLES-STATUS-SUMMARY.md) (short
handoff), and [EXPANSION-PLAN.md](EXPANSION-PLAN.md).*

## 1. Where things stand (local, not pushed)

| Commit | What |
|---|---|
| `c7c37cd` | `packages/procedures-cycles`: 14 procedures across planning, controls sampling, receivables, the payables search, cash, inventory and completion. Sampling math checked against the AICPA tables. Opt-in per engagement. |
| `8e41b68` | Generic checks found by practice: allowance recompute, slow deposit-in-transit flag, conclusion-by-reference, systematic pick cap. The engine refuses typed-in sample values. Workflow key `cycles` (not `scope`). Provenance note. |
| `22a59ff` | **Readiness fix:** a finding left undisposed or marked follow-up now blocks the lock (`FINDINGS_OPEN`); before, non-dollar findings slipped through. **Migration 8:** the risk register takes all ten assertions. |
| `ba0d60e` | Studio label for `FINDINGS_OPEN`; Learn standalone rebuilt. |
| Uncommitted engineering follow-up | Addressed all five findings in `docs/reviews/REVIEW-2026-09-26.md`: zero-row refusal, server-side scope enforcement, complete inspection of every selected disbursement line, declared package dependency, and customer-grain A/R confirmation evaluation. Awaiting re-review and commit. |

Tests: 260 pass. The eleven AP contracts and their golden bundles are unchanged.

**Tested so far:** one published practice case, run end to end privately (all ten
assignments). The engine reproduced that case's own worked figures. The run also
found the readiness hole above.

**Not tested:** any real client export, and any case not written from that one. The
data shapes follow a textbook layout (see §3). This is the main risk.

## 2. Effect on the live app and Learn today

None until pushed. After a push, with no cycles switched on (every existing engagement):

- Harborline still runs the eleven AP procedures and still gives **52 findings**.
- **New behaviour:** a Harborline file now needs a decision on every finding before the
  lock. That is 45 non-dollar findings on top of the 7 on the SAD. The walkthrough
  already says "every finding needs a disposition"; the code now enforces it. The
  Workbench has a disposition control on every finding, so the lock is reachable.
- The risk-register dropdown shows ten assertions instead of five (cosmetic in videos).

## 3. What must change before learners can use the cycles with QuickBooks

The cycle roles were built around textbook-shaped workpapers. QuickBooks exports look
different:

| QuickBooks report | Its shape | Engine expects today | Change needed |
|---|---|---|---|
| Trial Balance | Debit and Credit columns | balance + DR/CR side | accept debit/credit columns |
| A/R Aging Summary/Detail | 5 buckets: Current, 1–30, 31–60, 61–90, 91+ | confirmation procedures now aggregate detail rows to customer balance; allowance still has 4 fixed buckets | any number of named buckets; allowance rates per bucket |
| Inventory Valuation Summary | item, qty on hand, avg cost, asset value | one row per unique stock number | quantity-based trace; several count tags per item summed |
| Reconciliation report | cleared / uncleared transactions | an item-typed reconciliation list | build the reconciliation items from the report |

QuickBooks import recipes today cover payables only (Bill Payment List, Transaction
List by Vendor, Unpaid Bills, vendor list).

## 4. Adds and edits

**Add (new):**
1. QuickBooks recipes: Trial Balance, A/R Aging, Inventory Valuation, Reconciliation.
2. A Workbench screen to switch cycles on and set their policies (tolerable
   misstatement, allowance rates, sampling risk, search threshold, DIT days).
3. Demo data for receivables, cash and inventory, so lessons can show them.
4. New lesson steps: QuickBooks export → Excel check → Noesi, per cycle.

**Edit (existing):**
1. The cycle engine's roles (§3), which are not live, so this is cheap now.
2. The QuickBooks module (`procedures_ap/quickbooks.py`) for the new report types.
3. The "What Noesi does" panels and badges in lessons 2, 5, 6, 7, 8, 9, 10; EXPANSION-PLAN;
   matching manual chapters.
4. Six videos, one scene each (§5).

**Untouched:** the eleven AP procedures and golden tests, Harborline's existing data
and answer key, lesson audit-method content, and the fraud track (F1–F9).

**Order:** second test case (QuickBooks-shaped) → engine edits → recipes → Workbench
screen → demo data → lesson panels → videos last, so each is redone once.

## 5. Videos: which lines break, and when

These lines become false **only when the cycles are usable in the app**. Edit them then,
with the lesson text, not before.

| Video | Line that becomes false | Scene |
|---|---|---|
| L2 Understanding and analytics | "Noesi runs no analytics." | 9 |
| L5 Sampling | "Noesi does no sampling." | 9 |
| L6 Unrecorded liabilities | "Noesi has no search for unrecorded liabilities." | 9 |
| L7 Receivables | "doesn't audit revenue or receivables yet… no confirmation tracking, no aging or allowance tools" | 7 |
| L8 Cash | "Noesi is not a bank reconciliation tool. It doesn't track deposits in transit…" | 9 |
| L9 Inventory | "no count, cutoff, pricing or obsolescence procedures" (count tracing and pricing now exist; cutoff and obsolescence do not) | 8 |

Still accurate: L1, L3, L4, L10 (scene 7 shows a fresh file, which has no findings),
and all of F1–F9. "Eleven procedures, fifty-two findings" (L5, F8) stays true for Harborline.

**Method:** re-voice only the named scene and splice it in. Estimate: 6 × 300–400
characters ≈ 400–500 ElevenLabs credits (≈0.2/character), before any new clips.
As always: words approved, then cost approved, before any voicing.

## 6. Open engine items (from the practice run)

- Two misstatement summaries disagree: the Noesi SAD (unsigned magnitudes, no projection)
  and `completion.uncorrected_misstatements` (signed, projected, by statement line). Merge them.
- Clearly trivial is hard-coded at 5% of materiality; firms set their own posting
  threshold. Make it a policy.
- Inventory turnover needs prior-year balances; allow prior-year statement figures as input.
- The cycles do not feed the structural layer (graph / Dempster–Shafer / fusion). Wiring
  them in is a separate, later step, agreed 2026-09-26.
- Unified tagging (`unified._cycle_of`) does not yet read a receipt's `evidence.cycle`, so
  cycle findings show as "unassigned" in the unified view.

## 7. Before anything is pushed

1. A second test case written independently of the practice case, with QuickBooks-shaped data.
2. Re-review the engineering response to the five findings in
   [the 2026-09-26 independent review](reviews/REVIEW-2026-09-26.md). The first review is
   complete and the fixes are implemented locally, but the remediation has not yet had
   an independent pass.
3. Decide whether the stricter lock (every finding decided) ships alone first, since it
   changes the Harborline flow even with no cycles on.
