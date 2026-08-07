# Chapter 5 — Executing procedures

## In practice

Substantive procedures produce evidence at the assertion level. Full-
population testing — examining every record rather than a sample — is one
of the genuine advantages data-driven auditing has over manual work, but it
changes how you read results:

- **A silent procedure means "within tolerance", not "nothing there".**
  Every automated comparison has a tolerance; differences inside it produce
  no exception. Whether a sub-tolerance difference matters is the
  auditor's call, so you must know the tolerance to interpret the silence.
- **An exception is not a misstatement.** A payment absent from the bank
  feed is an *exposure* to investigate; the misstatement is whatever the
  investigation concludes — possibly zero, if it cleared in January.
- **One defect can surface in several procedures.** A voucher citing a
  nonexistent PO fails the PO-reference test *and* the three-way match.
  Recognizing shared root causes — and not double-counting the exposure —
  is judgment no engine exercises for you.

Every run of a procedure is itself audit work, so it walks the same
lifecycle as any workpaper: prepared, reviewed, approved, by three
different people.

## In the workbench

Run procedures from **Runs & Findings** or directly from the **Flow Map**
(the purchase-to-pay diagram; each arrow shows the procedures testing that
link). What a run records: a frozen **job manifest** (procedure and engine
versions, a digest of every input table, the effective policies) and a
sealed result. Re-running later is *reperformance* — a new job with its
own sequence number, never an overwrite.

Review lifecycle: the preparer's completed run is **reviewed** by the
reviewer chair, then **approved** by the partner (who must not be the
reviewer). Completion blocks on any run left unapproved.

The eleven procedures, and how to read each:

| Procedure | Assertions | What it does | Read the results knowing |
|---|---|---|---|
| `ap.payment_voucher_reference` | occurrence, accuracy | every payment must cite an observed voucher | absence may be an incomplete voucher export — completeness of the population decides what absence proves |
| `ap.voucher_po_reference` | occurrence, authorization | every PO-citing voucher must reach an observed PO | non-PO spend (rent, utilities) is counted, not flagged |
| `ap.document_chain` | occurrence, accuracy, cutoff | PO → voucher → payment amounts and date order cohere; escalates only anomalous chains | coherence does not authenticate any document; expect cross-findings from reference defects |
| `ap.segregation_of_duties` | authorization | row-level: same creator and approver, or missing approver | field semantics and compensating controls need auditor evaluation |
| `ap.vendor_relational_twins` | occurrence | near-identical vendor identities (name similarity) plus transaction-profile twins | a twin is an investigation lead, not proof of duplication or fraud |
| `ap.three_way_receipt_match` | occurrence, accuracy, authorization | invoiced and paid goods were ordered and received | 2% tolerance on amounts; services and partial deliveries need review |
| `ap.split_payment_review` | authorization | sub-threshold payment clusters per vendor within the chosen window | the window is your parameter; same-day default sees only crude splitting |
| `ap.subledger_gl_balance_tie` | completeness, accuracy | period-end subledger vs GL control account | a cent-level tie-out; any difference is named |
| `cash.bank_clearing` | occurrence, completeness, accuracy | payments clear through the independent bank feed | **2% amount tolerance** — know it before calling the silence clean |
| `gl.payment_posting` | completeness, accuracy, cutoff | payments post to GL at the right amount and period | period mismatches are cutoff exceptions |
| `forensic.closed_value_flow` | occurrence | amount- and time-coherent directed cycles in the value flows | a coherent round trip is a lead; population completeness bounds what it proves |

Every finding arrives as a **receipt**: verdict, reason, the source rows
(with content hashes), the tolerance applied, and a stated limitation —
identified by the hash of its own content. Chapter 6 is about judging them.

## In Harborline

Run all eleven (preparer chair), then review and approve each (reviewer,
then partner chair). Expect **52 findings**, and reconcile them against
your own spreadsheet work from the assignments:

- The three-way match reports **10**, though only 7 receipt problems were
  planted — the three vouchers with phantom POs surface here too. One
  defect, two procedures; Assignment 4 asks whether that is one finding or
  two on the SAD.
- Bank clearing reports **5**, though 6 differences were planted — one sits
  at 0.9%, inside the 2% tolerance, deliberately. The tool is silent about
  it and *correct* to be silent; a student who reconciles the bank column
  by hand finds a difference the tool never mentions. Whether it matters
  is your call, not the engine's.
- The split review finds the planted cluster — five payments to one vendor
  totalling 48,995 across nine days — only because you set the window in
  chapter 4. Re-run it with the default and watch it go silent: same data,
  different parameter, different evidence.
- Segregation of duties flags exactly five self-approved payments. Before
  you disposition them, check their dates against the June–September
  supervisor vacancy from the engagement brief — a cluster with a known
  cause reads very differently from a year-round spread.
