# Independent review of 04d3c5f and c38d567

Reviewed 3 October 2026 against the local committed code. This is a code and
targeted-test review, not a full Workbench validation.

## Reproducible issue

`04d3c5f` changed `render_workpaper` to read only the new `by_risk` field of
`HIGH_RISK_RESPONSES_NOT_PERFORMED`. A previously exported packet can carry
the older `items` list without `by_risk`. Rendering that packet now leaves
the risk's “Responses that did not run” cell blank, even though the blocker
names `rev.sales_cutoff (not run)`.

Reproduced with an invented minimal v4-shaped packet passed to
`assurance_workpapers.workpaper.render_workpaper`: `opinion.readiness_blockers`
contained `items: ["Sales: rev.sales_cutoff (not run)"]`; the rendered risk
row contained `<td>rev.sales_cutoff</td><td>—</td>`. This is a compatibility
issue for rendering older records. Current Workbench exports now include
`by_risk`, so this reproduction does not establish a defect in newly made
working papers. A fallback must avoid assigning one title's gap to two risks
with the same title.

## Checked without a reproduced issue

- Read every changed line in both commits and traced the run classification
  through stored `procedure_run.findings`, `runs()`, the Fraud view, coverage,
  and readiness. `_how_much_tested` refuses to infer testing from a generic
  source-row `population`; its targeted invented-data tests pass. It still
  classifies a completed run with no refusal finding as `all`; this is a
  convention of the current run contract, not proof that every intended
  population was tested. No contrary run was reproduced in this review.
- Traced `c38d567`'s download: the UI receives a `Blob` from the export
  response and passes the same blob to the download link. The API serializes
  the packet with Python `json.dumps`; the UI no longer parses and reserializes
  it. The existing browser evidence in the finish map reports a verified
  download, but this review has not independently repeated that browser check.
- Ran `python -m pytest tests/unit/test_fraud_view.py
  tests/unit/test_draft_workpaper.py -q`: 12 passed. This does not exercise
  the browser, old packet rendering, or a general invented-data engagement.

## At the time of this review, not checked yet

Full test suite, general UI journey, persisted state after each click,
archive/restore, folder upload, all-screen wording, and client-data custody.
Those remain the next finish-map items.

## Later follow-up in this session

The ordinary invented-data browser journey later downloaded a 10,263-byte
record from the UI; offline `verify_packet` returned `verified: True` and all
individual checks true. The same check passed on a 10,690-byte browser
download from a restored invented store. The older-packet rendering issue was
fixed locally and covered by `test_older_packet_keeps_its_unperformed_response_visible`.
The subsequent work and remaining checks are recorded in
`docs/WORKBENCH-FINISH-VERIFICATION-2026-10-03.md`.
