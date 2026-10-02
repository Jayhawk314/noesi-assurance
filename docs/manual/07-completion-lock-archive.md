# Chapter 7 — Completion, the record, and the archive

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

Noesi supplements the audit; it does not assemble or sign the audit file.
The firm's own archive, review and sign-off stay where they are. What
Noesi adds is a record of the testing that can be checked.

**Readiness** (Export tab, and SAD & Completion) derives every open item
by name, each a fact about the data, the procedures and the findings:
undisposed findings, procedures in the audit that could not run or have
not run, missing materiality, unexplained deselections, and a broken
decision trail. There are no boxes to tick: the completion work
(subsequent events, going concern, representations) is done through its
procedures. Red readiness is the list working, not an error — each item
names exactly what is outstanding.

**Export** (any chair, any time) downloads the **record**: one JSON file
carrying a manifest of every entity (file digests, mappings, dataset
reconciliations, runs, dispositions, risks, team, and the journal position
it was taken at), every run with its findings and seals, the dispositions,
the SAD, readiness, the scope and the draft opinion. Each export is written
to the hash-chained journal with its digest. Anyone can re-check the record
**offline** with `assurance_workpapers.packet.verify_packet`: every finding
receipt, every run seal, the manifest and the packet itself must re-hash,
and the decision trail must have verified when the record was made. A
record exported over a broken trail (a journal entry edited outside the
Workbench) still downloads, but it says so on the working paper and its
offline check fails: it never reads as verified.
The **working paper** is a static HTML rendering of the same record.

What the check does not prove is written inside the record: it is not
signed, so it shows the record is internally consistent (a corrupted or
partly edited file fails), but someone able to edit it could recompute the
digests. It does not prove who produced it, that the client's source
documents are authentic or complete, or when it was made. Keep the
exported record in the firm's archive like any other working paper.

(Until 1 October 2026 the Workbench also locked and signed engagements.
That was removed: a sign-off is the firm's act, not the tool's. An
engagement locked before then was reopened by the upgrade; its old lock
rows are kept as history.)

## In Kestrel

1. Review the adjusted trial balance, the final misstatement schedule, the
   July transaction leads, going-concern indicators, and the representation
   letter, through their procedures' results.
2. Read the draft opinion as a proposal. The missing representation drives
   its current direction, while pervasiveness and the going-concern conclusion
   remain explicit partner decisions. Do not resolve either by editing the
   case data to make the screen green.
3. Clear or follow up every finding, run every selected procedure,
   record the partner decisions, and watch readiness explain what remains.
   Export the record and find the scope limitations, policies, line mapping,
   dispositions and opinion decisions in it.
4. **Then check it.** Run `verify_packet` on the exported file; change one
   amount in it and run it again, and see which check names the edit.

One caution to carry back to practice: a record that checks proves the
*file's* consistency, not the audit's quality. A tidy record of thin work
is still thin work — which is why every chapter before this one exists.
