# Chapter 1 — The engagement and the team

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

**Creating an engagement** (client name + period end) makes the acting
principal its **partner**. The partner assigns other principals as
`preparer` and `reviewer` on the **Team** tab.

**Chairs.** The pilot runs on one machine with one operator. The header's
**acting as** control switches which principal your actions are performed
as. The gates treat chairs exactly as they would treat separate people: a
proposal's author cannot approve it, a run's executor cannot review it, a
reviewer cannot approve their own review. Every action is journaled under
the chair that performed it and appears that way on the signed workpaper.

Understand what this does and does not mean. On a single laptop, chair
separation is *procedural*, not *personal* — the same human sits in every
chair. That is acceptable for teaching and for a sole practitioner
role-playing the discipline (the same way one signs different boxes on a
paper workpaper), and the tool states it openly rather than pretending
otherwise. A real multi-person deployment replaces chairs with per-person
authentication ([production tracker §1](../PRODUCTION-READINESS.md)).

**The journal.** Every accepted command writes a domain event linked by
hash to its predecessor. This chain is the engagement's decision trail; if
it breaks, completion readiness blocks (`DECISION_TRAIL_BROKEN`) and the
engagement cannot lock. You do not have to do anything to maintain it —
you only need to know it is there, because it is what makes "who did what,
when" a property of the record rather than a claim.

Steps:

1. Start: `noesi-workbench` (or `--demo` for the pre-loaded case).
2. Create the engagement while acting as the principal who should be
   partner.
3. Team tab → add a preparer and a reviewer principal.
4. Practice switching chairs in the header; watch the roles chip update.

## In Harborline

The case is designed for exactly three chairs. With `--demo`, the
engagement **Harborline Marine Group (demo)** arrives with `demo-preparer`
and `demo-reviewer` already assigned and the session principal as partner.
Loading it by hand instead: create the engagement as your partner chair
and assign the two other chairs yourself — the case walkthrough
([`03-walkthrough.md`](../../case-studies/harborline-marine/docs/03-walkthrough.md))
gives the exact sequence.

Try to approve one of your own mapping proposals while sitting in the
preparer chair. The refusal you get is the point: the server enforces the
discipline; the UI merely reflects it.
