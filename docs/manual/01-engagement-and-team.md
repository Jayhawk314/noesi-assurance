# Chapter 1 — The engagement and the team

*Noesi has one user per engagement; the team's review happens outside it.*

## In practice

An audit is performed by an **engagement team** with defined
responsibilities. The engagement partner takes overall responsibility for
the engagement and its quality (AU-C 220); work is prepared by one person
and reviewed by another; and nobody signs off on their own work. This
separation is not bureaucracy — it is the mechanism by which an audit firm
turns one person's work into something the firm is willing to stand behind.

Three roles cover the minimum shape of that discipline:

- **Preparer** — performs the work: obtains data, runs procedures, drafts
  conclusions.
- **Reviewer** — examines the preparer's work and either concurs or sends
  it back. The reviewer must not be the preparer.
- **Partner** — accepts the engagement, assigns the team, resolves what the
  review escalates, and takes final responsibility: approving reviewed
  work, signing the completed file.

Everything of consequence must be attributable: who did it, when, in what
capacity (AU-C 230 requires documentation sufficient for an experienced
auditor to understand who performed and who reviewed the work).

## In the workbench

**One user per engagement.** Noesi supplements an audit; it is not the
firm's audit software. So it has no chairs, roles or approvals (removed
2 Oct 2026). Whoever runs the session does every step, and the header shows
who that is. **Creating an engagement** (client name + period end) records
you as its user.

The preparer–reviewer–partner discipline above still matters, but it
happens in the firm's own review, outside Noesi. A second login on the same
laptop would be the same person twice, and Noesi would rather not pretend
otherwise. What Noesi does keep is the trail: every action is journaled
under the user who did it, and appears that way in the exported record, so
a reviewer can see exactly who did what and when.

**The journal.** Every accepted command writes a domain event linked by
hash to its predecessor. This chain is the engagement's decision trail; if
it breaks, completion readiness says so (`DECISION_TRAIL_BROKEN`). You do not have to do anything to maintain it —
you only need to know it is there, because it is what makes "who did what,
when" a property of the record rather than a claim.

Steps:

1. Start: `noesi-workbench` (or `--demo` for the pre-loaded case).
2. Create the engagement; the header shows the user it is recorded under.

## In Kestrel

With `--demo`, the engagement **Kestrel Valley Cycle Supply (demo)** arrives
loaded under the session's user. Loading it by hand instead: create a
June 30, 2026 engagement and set the period start to July 1, 2025 before
scoping the cycles.
