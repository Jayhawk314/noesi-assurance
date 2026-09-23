# Chapter 7 — Completion, lock, and the archive

## In practice

Completion is a checklist with teeth. Before the report is released the
team performs final analytical review, evaluates subsequent events
(AU-C 560), considers going concern, obtains written representations
(AU-C 580), concludes on evidence sufficiency, and completes the
engagement-level review. After release, the file is **assembled** — a
complete, final set of documentation — within 60 days (AU-C 230). PCAOB
AS 1215 allowed 45 days; the amended AS 1215, effective December 15, 2026,
requires assembly within 14 days of the report release date.

After assembly, the rules harden:

- Nothing is deleted or discarded before the retention period ends
  (5 years AICPA, 7 PCAOB).
- Changes are still possible — files get reopened for subsequent discovery
  of facts, for inspection findings, for administrative corrections — but
  every change must document **the specific reason, by whom, and when**,
  and the original record must survive intact.

An archive you can quietly edit is not an archive. The professional
standard is that the record of *what the file said when you signed it*
outlives any later amendment.

## In the workbench

**Readiness** (SAD & Completion tab) derives every blocker by name:
unapproved runs, undisposed findings, incomplete stages, missing
materiality, unexplained deselections, the six completion checks (each
needing a note or evidence, not just a tick), and a broken decision trail.
Red readiness is the gate working, not an error — each blocker names
exactly what is outstanding.

**Lock** (partner chair, green gate required). One transaction: engagement
status → locked; a deterministic **manifest** of every covered entity
(artifact digests, mapping approvals, dataset reconciliations, run
receipts, dispositions, team) is frozen, anchored to the current head of
the hash-chained journal, and its digest **signed** with the partner's key.
What the signature does and does not prove is written inside the manifest
itself — it binds a principal's key to exactly that byte set; it does not
authenticate the client's source documents or provide trusted time.

**Verify** re-derives everything on demand: the manifest against live
state (drift is named section by section), the signature, the journal
chain. **Export** refuses unless verification passes *right now*, then
produces the **evidence packet** — self-contained JSON carrying the lock,
every run with its findings and seals, dispositions, the SAD, and all
public keys needed to re-verify **offline** with
`assurance_workpapers.packet.verify_packet`. The **workpaper** is a
static HTML rendering of the same packet.

**Reopening = supersession, never deletion.** Unlock requires the partner
chair and a *specific written reason* (ten characters minimum — it becomes
a permanent part of the record, inside the journal's hash chain). The
superseded lock keeps its manifest, signature, and journal anchor forever
and is re-verified on every read. Work after reopening flows through the
same review gates — a reperformed procedure is a new run that must be
reviewed and approved again — and the next lock signs a manifest that
**names its predecessor and the reason it was set aside**. The packet and
workpaper carry the full amendment history. This is AU-C 230's
post-assembly rule, made structural.

## In Harborline

1. Work the six completion checks with real notes (the final-analytical
   and evidence-sufficiency notes can reference your assignment memos).
2. Watch readiness drain to green as each blocker clears, then lock as
   the partner chair. Export the packet; open the workpaper; find your
   scope limitations and your disposition notes in it.
3. **Then reopen it.** Give a real reason — say, *"Client delivered a
   corrected AP control balance after archiving; reperforming the
   control-account tie."* Reperform `ap.subledger_gl_balance_tie`, try to
   lock again immediately, and read the refusal: the rerun is unreviewed.
   Review and approve it through the chairs, re-lock, re-export — and look
   at the packet's **lock amendment history**: both generations of the
   lock, both signatures, your reason, and both runs with their review
   chains. That is what "nothing is ever quietly edited" looks like as a
   data structure.

One caution to carry back to practice: the lock proves the *file's*
integrity, not the audit's quality. A signed archive of thin work is
still thin work — which is why every chapter before this one exists.
