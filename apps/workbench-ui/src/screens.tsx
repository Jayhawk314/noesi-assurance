// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Artifact, BatchOutcome, Client, Coverage, Engagement, Finding, Readiness,
  Run, Sad, Sources, TeamMember, WorkflowDocument, LockVerification,
  ApControlBuilt, ApControlCandidates, Extraction, RecipeReport, WorkbookPreview,
} from "./api";

interface ScreenProps {
  client: Client;
  eid: string;
  onError: (exc: unknown) => void;
}

function useLoader<T>(load: () => Promise<T>, onError: (e: unknown) => void) {
  const [data, setData] = useState<T | null>(null);
  const reload = useCallback(() => {
    load().then(setData).catch(onError);
  }, [load, onError]);
  useEffect(() => { reload(); }, [reload]);
  return { data, reload };
}

const short = (digest: string) => `${digest.slice(0, 12)}…`;

// ------------------------------------------------------------ screen 1: team

export function TeamScreen({ client, eid, onError }: ScreenProps) {
  const load = useCallback(async () => (await client.team(eid)).team, [client, eid]);
  const { data: team, reload } = useLoader<TeamMember[]>(load, onError);
  const [principal, setPrincipal] = useState("");
  const [role, setRole] = useState("preparer");

  async function assign() {
    try {
      await client.assignTeam(eid, principal.trim(), role);
      setPrincipal("");
      reload();
    } catch (exc) { onError(exc); }
  }

  return (
    <>
      <h2>Engagement team</h2>
      <table className="dense">
        <thead><tr><th>Principal</th><th>Role</th></tr></thead>
        <tbody>
          {(team ?? []).map((member) => (
            <tr key={`${member.principal_id}/${member.role}`}>
              <td><code>{member.principal_id}</code></td>
              <td>{member.role}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <form className="inline" onSubmit={(e) => { e.preventDefault(); void assign(); }}>
        <input value={principal} placeholder="principal id"
               onChange={(e) => setPrincipal(e.target.value)} />
        <select value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="preparer">preparer</option>
          <option value="reviewer">reviewer</option>
          <option value="partner">partner</option>
        </select>
        <button className="action" type="submit" disabled={!principal.trim()}>
          assign
        </button>
      </form>
      <p className="note">
        Roles are the only authorization input. Preparers ingest and run;
        reviewers approve mappings and review runs; partners approve, assign,
        and lock. Separation of duties is enforced server-side.
      </p>
    </>
  );
}

// ------------------------------------------- screen 2: sources and mappings

const ROLES = [
  "Vendors", "Employees", "Purchase_orders", "Vouchers", "Payments",
  "Value_flows", "Bank", "GL", "Goods_receipts", "AP_control_balance",
];

export function SourcesScreen({ client, eid, onError }: ScreenProps) {
  const load = useCallback(() => client.sources(eid), [client, eid]);
  const { data, reload } = useLoader<Sources>(load, onError);
  const fileInput = useRef<HTMLInputElement>(null);
  const [mapRole, setMapRole] = useState<Record<string, string>>({});
  // Excel sources: the loaded preview and the sheet/header-row choice.
  const [books, setBooks] = useState<Record<string, WorkbookPreview>>({});
  const [pick, setPick] = useState<Record<string, Extraction>>({});
  const isWorkbook = (a: Artifact) => /\.xlsx$/i.test(a.original_name)
    || a.media_type.includes("spreadsheetml");
  const openBook = useCallback((a: Artifact) => {
    client.workbookPreview(eid, a.artifact_id).then((book) => {
      setBooks((prev) => ({ ...prev, [a.artifact_id]: book }));
      const first = book.sheets[0];
      const recipes = first.recipes ?? [];
      // A recognized QuickBooks report decides the role, not the filename:
      // one recipe is preselected; several leave the role for you to choose.
      const only = recipes.length === 1 ? recipes[0] : undefined;
      setPick((prev) => ({ ...prev, [a.artifact_id]: prev[a.artifact_id]
        ?? { sheet: first.sheet,
             header_row: only?.header_row ?? first.suggested_header_row,
             recipe: only?.recipe } }));
      if (recipes.length || first.quickbooks_note) {
        setMapRole((prev) => a.artifact_id in prev ? prev
          : { ...prev, [a.artifact_id]: only?.role ?? "" });
      }
    }).catch(onError);
  }, [client, eid, onError]);
  const extractionFor = (a: Artifact): Extraction | undefined =>
    isWorkbook(a) ? pick[a.artifact_id] : undefined;

  // Read every unmapped workbook once, so recognized reports are offered
  // before anyone proposes — including "propose all".
  const opened = useRef(new Set<string>());
  useEffect(() => {
    for (const a of data?.artifacts ?? []) {
      const mapped = (data?.mapping_specs ?? []).some(
        (s) => s.artifact_id === a.artifact_id && s.status !== "superseded");
      if (isWorkbook(a) && a.state === "promoted" && !mapped
          && !opened.current.has(a.artifact_id)) {
        opened.current.add(a.artifact_id);
        openBook(a);
      }
    }
  }, [data, openBook]);

  const act = (work: () => Promise<unknown>) => () => {
    work().then(reload).catch(onError);
  };

  // Batch calls succeed as a whole while individual items may fail; the
  // per-item errors still deserve the error banner.
  const batch = (work: () => Promise<BatchOutcome>) => () => {
    work().then((outcome) => {
      const failed = outcome.results.filter((r) => r.status === "error");
      if (failed.length) {
        onError(new Error(failed.map(
          (r) => `${r.artifact_id ?? r.spec_id}: ${r.error}`).join("; ")));
      }
      reload();
    }).catch(onError);
  };

  async function upload() {
    const files = Array.from(fileInput.current?.files ?? []);
    if (!files.length) return;
    try {
      for (const file of files) await client.uploadSource(eid, file);
      if (fileInput.current) fileInput.current.value = "";
      reload();
    } catch (exc) { onError(exc); reload(); }
  }

  // The role a proposal would use: an explicit choice beats the filename
  // suggestion. Artifacts already under an active spec are done mapping.
  const chosenRole = (artifact: Artifact) =>
    mapRole[artifact.artifact_id] ?? artifact.inferred_role ?? "";
  const activelyMapped = new Set(
    (data?.mapping_specs ?? [])
      .filter((s) => s.status !== "superseded")
      .map((s) => s.artifact_id));
  const proposable = (data?.artifacts ?? []).filter(
    (a) => a.state === "promoted" && !activelyMapped.has(a.artifact_id)
           && chosenRole(a));
  const proposedSpecs = (data?.mapping_specs ?? [])
    .filter((s) => s.status === "proposed");
  const normalizedSpecs = new Set(
    (data?.datasets ?? []).map((d) => d.mapping_spec_id));
  const normalizable = (data?.mapping_specs ?? []).filter(
    (s) => s.status === "approved" && !normalizedSpecs.has(s.spec_id));

  return (
    <>
      <h2>Source inventory</h2>
      <table className="dense">
        <thead>
          <tr><th>File</th><th>SHA-256</th><th>Bytes</th><th>State</th>
              <th>Map as</th><th /></tr>
        </thead>
        <tbody>
          {(data?.artifacts ?? []).map((artifact) => (
            <tr key={artifact.artifact_id}>
              <td>{artifact.original_name}</td>
              <td><code>{short(artifact.sha256)}</code></td>
              <td>{artifact.size_bytes.toLocaleString()}</td>
              <td className={`status ${artifact.state === "promoted" ? "ok" : "broken"}`}>
                {artifact.state}
              </td>
              <td>
                <select value={chosenRole(artifact)}
                        onChange={(e) => setMapRole({ ...mapRole, [artifact.artifact_id]: e.target.value })}>
                  <option value="">choose role…</option>
                  {ROLES.map((role) => <option key={role} value={role}>{role}</option>)}
                </select>
              </td>
              <td>
                {!activelyMapped.has(artifact.artifact_id) && (
                  <button className="action"
                          disabled={!chosenRole(artifact)}
                          onClick={act(() => client.proposeMapping(
                            eid, chosenRole(artifact), artifact.artifact_id,
                            extractionFor(artifact)))}>
                    propose mapping
                  </button>
                )}
                {isWorkbook(artifact) && !activelyMapped.has(artifact.artifact_id) && (
                  <button className="action" onClick={() => openBook(artifact)}>
                    {books[artifact.artifact_id] ? "sheet ✓" : "choose sheet"}
                  </button>
                )}
              </td>
            </tr>
          ))}
          {(data?.artifacts ?? []).filter((a) => books[a.artifact_id]
            && !activelyMapped.has(a.artifact_id)).map((artifact) => (
            <tr key={`${artifact.artifact_id}-book`}>
              <td colSpan={6}>
                <WorkbookChooser book={books[artifact.artifact_id]}
                                 choice={pick[artifact.artifact_id] ?? {}}
                                 onChange={(c) => setPick((prev) => ({ ...prev, [artifact.artifact_id]: c }))}
                                 onRole={(role) => setMapRole((prev) => ({ ...prev, [artifact.artifact_id]: role }))} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <form className="inline" onSubmit={(e) => { e.preventDefault(); void upload(); }}>
        <input type="file" ref={fileInput} accept=".csv,.txt,.xlsx,.xls" multiple />
        <button className="action" type="submit">upload sources</button>
        {proposable.length > 0 && (
          <button className="action" type="button"
                  onClick={batch(() => client.proposeMappings(
                    eid, proposable.map((a) => ({
                      artifact_id: a.artifact_id, role: chosenRole(a),
                      extraction: extractionFor(a) }))))}>
            propose all ({proposable.length})
          </button>
        )}
      </form>
      <p className="note">
        Select several exports at once — CSV or Excel (.xlsx); roles are
        suggested from the filenames, and each suggestion stays overridable
        above. For a workbook, choose the sheet and the row that holds the
        column headings; reading stops at the first blank row, so a totals
        block below the data is left out, and the proposal says so. Batching
        compresses the clicks, never the review — every proposal still
        crosses the reviewer's approval before it can normalize.
      </p>

      <ApControlPanel client={client} eid={eid} onError={onError} onBuilt={reload}
                      artifactCount={data?.artifacts.length ?? 0} />

      <h3>Mapping specs (proposal → reviewer approval → normalize)</h3>
      {(proposedSpecs.length > 1 || normalizable.length > 1) && (
        <form className="inline" onSubmit={(e) => e.preventDefault()}>
          {proposedSpecs.length > 1 && (
            <button className="action" type="button"
                    onClick={batch(() => client.approveMappings(
                      eid, proposedSpecs.map((s) => s.spec_id)))}>
              approve all proposed ({proposedSpecs.length})
            </button>
          )}
          {normalizable.length > 1 && (
            <button className="action" type="button"
                    onClick={batch(() => client.normalizeBatch(
                      eid, normalizable.map((s) => s.spec_id)))}>
              normalize all approved ({normalizable.length})
            </button>
          )}
        </form>
      )}
      <table className="dense">
        <thead>
          <tr><th>Role</th><th>Status</th><th>Proposed by</th><th>Approved by</th>
              <th>Mapped</th><th>Unmapped headers</th><th>Refused fields</th><th>Source</th><th /></tr>
        </thead>
        <tbody>
          {(data?.mapping_specs ?? []).map((spec) => (
            <tr key={spec.spec_id}>
              <td>{spec.role}</td>
              <td className={`status ${spec.status === "approved" ? "ok" : "pending"}`}>
                {spec.status}
              </td>
              <td><code>{spec.proposed_by}</code></td>
              <td><code>{spec.approved_by || "—"}</code></td>
              <td>{Object.keys(spec.column_map).length} fields</td>
              <td>{spec.unmapped_headers.join(", ") || "—"}</td>
              <td>{spec.refused_fields.join(", ") || "—"}</td>
              <td>{spec.extraction
                ? <>sheet "{spec.extraction.sheet}", headings on row {spec.extraction.header_row}
                    {spec.recipe_report && <RecipeSummary report={spec.recipe_report} />}</>
                : "CSV"}</td>
              <td>
                {spec.status === "proposed" && (
                  <button className="action"
                          onClick={act(() => client.approveMapping(eid, spec.spec_id))}>
                    approve
                  </button>
                )}
                {spec.status === "approved" && !normalizedSpecs.has(spec.spec_id) && (
                  <button className="action"
                          onClick={act(() => client.normalize(eid, spec.spec_id))}>
                    normalize
                  </button>
                )}
                {normalizedSpecs.has(spec.spec_id) && <span className="status ok">loaded ✓</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Normalized datasets</h3>
      <table className="dense">
        <thead>
          <tr><th>Role</th><th>Rows in / loaded / rejected</th>
              <th>Control total</th><th>Output digest</th></tr>
        </thead>
        <tbody>
          {(data?.datasets ?? []).map((dataset) => (
            <tr key={dataset.dataset_id} className={dataset.in_use === false ? "skipped" : ""}>
              <td>{dataset.role}
                {dataset.in_use === false && (
                  <div className="note">not used: a later {dataset.role} load replaces it</div>
                )}
              </td>
              <td>
                {dataset.rows_in} / {dataset.rows_loaded} /{" "}
                <span className={dataset.rows_rejected ? "status broken" : ""}>
                  {dataset.rows_rejected}
                </span>
                {(dataset.rejected_reasons ?? []).map((r) => (
                  <div key={r.reason} className="note">
                    Set aside {r.rows}: {r.reason} (row{r.source_rows.length > 1 ? "s" : ""}{" "}
                    {r.source_rows.join(", ")}{r.rows > r.source_rows.length ? ", …" : ""})
                  </div>
                ))}
              </td>
              <td>{dataset.control_total ?? "—"}</td>
              <td><code>{short(dataset.output_digest)}</code></td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="note">
        Datasets are rebuilt from the immutable artifact through the approved
        mapping on every read and digest-verified — reperformance is the read
        path.
      </p>
    </>
  );
}

// ------------------------------------------------------- screen 3: coverage

function PolicySetter({ policy, onSet }: {
  policy: string;
  onSet: (name: string, value: string) => void;
}) {
  const [value, setValue] = useState("");
  return (
    <form className="inline"
          onSubmit={(e) => {
            e.preventDefault();
            if (value.trim()) onSet(policy, value.trim());
          }}>
      <span>policy: {policy}</span>
      <input value={value} size={9} placeholder="value"
             onChange={(e) => setValue(e.target.value)} />
      <button className="action" type="submit" disabled={!value.trim()}>
        set
      </button>
    </form>
  );
}

export function CoverageScreen({ client, eid, onError }: ScreenProps) {
  const load = useCallback(() => client.coverage(eid), [client, eid]);
  const { data, reload } = useLoader<Coverage>(load, onError);
  const setPolicy = (name: string, value: string) => {
    client.updateWorkflow(eid, "policy", { name, value })
      .then(reload).catch(onError);
  };
  if (!data) return <p className="note">Compiling coverage…</p>;
  return (
    <>
      <h2>Procedure coverage</h2>
      <div className="panel">
        {(["executable", "partial", "blocked"] as const).map((state) => (
          <span key={state} className="metric">
            <b className={`status ${state}`}>{data.summary[state] ?? 0}</b>
            {state}
          </span>
        ))}
        {(data.summary.unsupported ?? 0) > 0 && (
          <span className="metric">
            <b className="status unsupported">{data.summary.unsupported}</b>
            unsupported
          </span>
        )}
        <span className="metric"><b>{data.summary.total ?? 0}</b>total</span>
      </div>
      <table className="dense">
        <thead>
          <tr><th>Procedure</th><th>Cycle</th><th>Status</th><th>Population</th>
              <th>Missing</th><th>Limitations</th></tr>
        </thead>
        <tbody>
          {data.procedures.map((row) => (
            <tr key={row.procedure_id}>
              <td><b>{row.name}</b><br /><code>{row.procedure_id}</code></td>
              <td>{row.cycle}</td>
              <td><span className={`status ${row.status}`}>{row.status}</span></td>
              <td>{row.population ?? "—"}</td>
              <td>
                {row.unsupported_reason && (
                  <div className="note">{row.unsupported_reason}</div>
                )}
                {row.missing_roles.map((role) => <div key={role}>dataset: {role}</div>)}
                {Object.entries(row.missing_fields).map(([role, fields]) => (
                  <div key={role}>fields: {role}.{fields.join(", ")}</div>
                ))}
                {row.missing_policies.map((policy) => (
                  <PolicySetter key={policy} policy={policy} onSet={setPolicy} />
                ))}
              </td>
              <td className="note">{row.limitations}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Evidence requests</h3>
      <table className="dense">
        <thead>
          <tr><th>Kind</th><th>Item</th><th>Owner</th><th>Unlocks</th></tr>
        </thead>
        <tbody>
          {data.evidence_requests.map((request) => (
            <tr key={request.request_id}>
              <td>{request.kind}</td>
              <td>{request.item}</td>
              <td>{request.owner}</td>
              <td>{request.unlocks.join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

// ----------------------------------------------- screen 4: runs and findings

const DISPOSITIONS = ["cleared", "unadjusted", "adjusted", "waived", "follow_up"];

export function RunsScreen({ client, eid, onError }: ScreenProps) {
  const load = useCallback(async () => {
    const [{ runs }, { findings }, coverage] = await Promise.all([
      client.runs(eid), client.findings(eid), client.coverage(eid),
    ]);
    return { runs, findings, coverage };
  }, [client, eid]);
  const { data, reload } = useLoader(load, onError);
  const [procedureId, setProcedureId] = useState("");
  const [noteDraft, setNoteDraft] = useState<Record<string, string>>({});

  const act = (work: () => Promise<unknown>) => () => {
    work().then(reload).catch(onError);
  };

  const executable = (data?.coverage.procedures ?? [])
    .filter((row) => row.status === "executable");

  return (
    <>
      <h2>Procedure runs</h2>
      <form className="inline"
            onSubmit={(e) => {
              e.preventDefault();
              act(() => client.runProcedure(eid, procedureId, {}))();
            }}>
        <select value={procedureId} onChange={(e) => setProcedureId(e.target.value)}>
          <option value="">choose executable procedure…</option>
          {executable.map((row) => (
            <option key={row.procedure_id} value={row.procedure_id}>
              {row.procedure_id}
            </option>
          ))}
        </select>
        <button className="action" type="submit" disabled={!procedureId}>
          run
        </button>
        <span className="note">
          Approved engagement policies apply automatically via coverage.
        </span>
      </form>
      <table className="dense">
        <thead>
          <tr><th>Procedure</th><th>Status</th><th>Executed by</th>
              <th>Reviewed by</th><th>Approved by</th><th>Error</th><th /></tr>
        </thead>
        <tbody>
          {(data?.runs ?? []).map((run: Run) => (
            <tr key={run.run_id}>
              <td><code>{run.procedure_id}</code></td>
              <td><span className={`status ${run.status}`}>{run.status}</span></td>
              <td><code>{run.executed_by}</code></td>
              <td><code>{run.reviewed_by || "—"}</code></td>
              <td><code>{run.approved_by || "—"}</code></td>
              <td className="note">{run.error || "—"}</td>
              <td>
                {run.status === "completed" && (
                  <button className="action"
                          onClick={act(() => client.reviewRun(
                            eid, run.run_id, "reviewed", run.version))}>
                    mark reviewed
                  </button>
                )}
                {run.status === "reviewed" && (
                  <button className="action"
                          onClick={act(() => client.reviewRun(
                            eid, run.run_id, "approved", run.version))}>
                    approve
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Findings and dispositions</h3>
      <table className="dense">
        <thead>
          <tr><th>Procedure</th><th>Verdict</th><th>Assertion</th><th>Class</th>
              <th>Reason</th><th>Magnitude</th><th>Disposition</th><th>Note</th>
              <th>Review</th><th /></tr>
        </thead>
        <tbody>
          {(data?.findings ?? []).map((finding: Finding) => (
            <tr key={finding.finding_uid}>
              <td><code>{finding.procedure_id}</code></td>
              <td>{finding.verdict.verdict}</td>
              <td><code>{finding.tags.assertion}</code></td>
              <td>{finding.tags.class}</td>
              <td>{finding.verdict.reason}</td>
              <td>{finding.verdict.score ?? "—"}</td>
              <td>
                <select value={finding.disposition.status === "undisposed"
                          ? "" : finding.disposition.status}
                        onChange={(e) => act(() => client.setDisposition(
                          eid, finding.finding_uid, e.target.value,
                          noteDraft[finding.finding_uid] ?? finding.disposition.note,
                          finding.disposition.version))()}>
                  <option value="">undisposed</option>
                  {DISPOSITIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </td>
              <td>
                <input value={noteDraft[finding.finding_uid] ?? finding.disposition.note}
                       placeholder="note"
                       onChange={(e) => setNoteDraft({
                         ...noteDraft, [finding.finding_uid]: e.target.value })} />
              </td>
              <td>
                {finding.awaiting_concurrence ? (
                  <button className="action"
                          title="Above clearly-trivial: a second person must concur (reviewer or partner chair)"
                          onClick={act(() => client.concurDisposition(
                            eid, finding.finding_uid,
                            finding.disposition.version))}>
                    concur
                  </button>
                ) : finding.requires_concurrence
                    && finding.disposition.concurred_by ? (
                  <span className="status ok"
                        title={`concurred by ${finding.disposition.concurred_by}`}>
                    concurred
                  </span>
                ) : (
                  <span className="note">—</span>
                )}
              </td>
              <td><code>{short(finding.verdict.receipt_id)}</code></td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="note">
        Dispositions above the clearly-trivial threshold are proposals until
        a second person concurs — the same preparer/reviewer separation as
        runs and mappings. Changing a disposition voids its concurrence.
      </p>
    </>
  );
}

// --------------------------------------- screen 5: SAD, workflow, completion

export function SadScreen({ client, eid, onError }: ScreenProps) {
  const load = useCallback(async () => {
    const [sad, workflow, readiness] = await Promise.all([
      client.sad(eid), client.workflow(eid), client.readiness(eid),
    ]);
    return { sad, workflow: workflow.document, readiness };
  }, [client, eid]);
  const { data, reload } = useLoader(load, onError);
  const [materiality, setMateriality] = useState("");
  const [noDataReason, setNoDataReason] = useState("");

  const act = (work: () => Promise<unknown>) => () => {
    work().then(reload).catch(onError);
  };

  if (!data) return <p className="note">Loading…</p>;
  const { sad, workflow, readiness } = data as {
    sad: Sad; workflow: WorkflowDocument; readiness: Readiness;
  };
  const needsNoDataAssertion = readiness.blockers.some(
    (b) => b.code === "NO_DATA_WITHOUT_PARTNER_ASSERTION");

  return (
    <>
      <h2>Summary of audit differences</h2>
      <div className="panel">
        <span className="metric"><b>{sad.overall_materiality.toLocaleString()}</b>materiality</span>
        <span className="metric"><b>{sad.clearly_trivial.toLocaleString()}</b>clearly trivial</span>
        <span className="metric"><b>{sad.total_unadjusted.toLocaleString()}</b>unadjusted</span>
        <span className="metric"><b>{sad.total_adjusted.toLocaleString()}</b>adjusted</span>
        {sad.concurrence_pending_count > 0 && (
          <span className="metric">
            <b className="status pending">{sad.concurrence_pending_count}</b>
            awaiting concurrence
          </span>
        )}
        <span className="metric">
          <b className={`status ${sad.conclusion === "material" ? "broken" : "ok"}`}>
            {sad.conclusion ?? "open"}
          </b>
          conclusion
        </span>
      </div>
      {needsNoDataAssertion && (
        <form className="inline"
              onSubmit={(e) => {
                e.preventDefault();
                act(() => client.updateWorkflow(eid, "no_data_assertion",
                  { asserted: true, reason: noDataReason }))();
              }}>
          <span className="status pending">no data loaded</span>
          <input value={noDataReason} size={48}
                 placeholder="why no data-dependent procedures apply this period"
                 onChange={(e) => setNoDataReason(e.target.value)} />
          <button className="action" type="submit"
                  disabled={noDataReason.trim().length < 10}>
            assert (partner chair)
          </button>
          <span className="note">
            Zero datasets means no procedure ever gated this engagement; the
            partner must own that on the record before it can lock.
          </span>
        </form>
      )}
      <table className="dense">
        <thead><tr><th>Unadjusted item</th><th>Reason</th><th>Amount</th></tr></thead>
        <tbody>
          {sad.unadjusted.map((line) => (
            <tr key={line.finding_id}>
              <td><code>{line.finding_id}</code></td>
              <td>{line.reason}</td>
              <td>{line.amount.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Materiality</h3>
      <form className="inline"
            onSubmit={(e) => {
              e.preventDefault();
              act(() => client.updateWorkflow(eid, "materiality",
                { amount: Number(materiality) }))();
            }}>
        <span>current: {workflow.materiality.amount.toLocaleString()}</span>
        <input value={materiality} placeholder="new amount"
               onChange={(e) => setMateriality(e.target.value)} />
        <button className="action" type="submit" disabled={!Number(materiality)}>
          set
        </button>
      </form>

      <h3>Stages</h3>
      <table className="dense">
        <thead><tr><th>Stage</th><th>Status</th><th /></tr></thead>
        <tbody>
          {Object.entries(workflow.stages).map(([name, stage]) => (
            <tr key={name}>
              <td>{name}</td>
              <td className={`status ${stage.status === "complete" ? "ok" : "pending"}`}>
                {stage.status}
              </td>
              <td>
                {stage.status !== "complete" && (
                  <button className="action"
                          onClick={act(() => client.updateWorkflow(eid, "stage",
                            { name, status: "complete" }))}>
                    mark complete
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Completion checks ({readiness.completion_done}/{readiness.completion_total})</h3>
      <table className="dense">
        <thead><tr><th>Check</th><th>Done</th><th>Note</th><th /></tr></thead>
        <tbody>
          {Object.entries(workflow.completion).map(([name, check]) => (
            <tr key={name}>
              <td>{name}</td>
              <td className={`status ${check.done ? "ok" : "pending"}`}>
                {check.done ? "done" : "open"}
              </td>
              <td>{check.note}</td>
              <td>
                {!check.done && (
                  <button className="action"
                          onClick={act(() => client.updateWorkflow(eid, "completion",
                            { name, done: true, note: "performed" }))}>
                    mark done
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

// ---------------------------------------------- screen 6: lock and export

export function LockScreen({ client, engagement, onError, onChanged }: {
  client: Client;
  engagement: Engagement;
  onError: (exc: unknown) => void;
  onChanged: () => Promise<void>;
}) {
  const eid = engagement.engagement_id;
  const load = useCallback(async () => {
    const [readiness, lock] = await Promise.all([
      client.readiness(eid), client.lockStatus(eid),
    ]);
    return { readiness, lock };
  }, [client, eid]);
  const { data, reload } = useLoader(load, onError);
  const [unlockReason, setUnlockReason] = useState("");

  async function lockNow() {
    try {
      await client.lock(eid, engagement.version);
      await onChanged();
      reload();
    } catch (exc) { onError(exc); }
  }

  async function unlockNow() {
    try {
      await client.unlock(eid, unlockReason, engagement.version);
      setUnlockReason("");
      await onChanged();
      reload();
    } catch (exc) { onError(exc); }
  }

  async function download() {
    try {
      const packet = await client.exportPacket(eid);
      const blob = new Blob([JSON.stringify(packet, null, 2)],
                            { type: "application/json" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `evidence-packet-${engagement.client_name}-${engagement.period_end}.json`;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (exc) { onError(exc); }
  }

  if (!data) return <p className="note">Deriving readiness…</p>;
  const { readiness, lock } = data as {
    readiness: Readiness; lock: LockVerification;
  };

  return (
    <>
      <h2>Completion readiness</h2>
      <div className="panel">
        <span className="metric">
          <b className={`status ${readiness.ready ? "ok" : "broken"}`}>
            {readiness.ready ? "READY" : "NOT READY"}
          </b>
          gate
        </span>
        <span className="metric"><b>{readiness.report_implication}</b>implication</span>
      </div>
      {readiness.blockers.length > 0 && (
        <table className="dense">
          <thead><tr><th>Blocker</th><th>Count</th><th>Items</th></tr></thead>
          <tbody>
            {readiness.blockers.map((blocker) => (
              <tr key={blocker.code}>
                <td><code>{blocker.code}</code></td>
                <td>{blocker.count}</td>
                <td className="note">{(blocker.items ?? []).join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3>Lock</h3>
      {!lock.locked ? (
        <>
          <p className="note">
            Locking freezes a signed snapshot manifest of every covered
            entity. It requires the partner and a green readiness gate.
          </p>
          <button className="action" disabled={!readiness.ready}
                  onClick={() => void lockNow()}>
            lock engagement
          </button>
        </>
      ) : (
        <>
          <div className="panel">
            <span className="metric">
              <b className={`status ${lock.verified ? "ok" : "broken"}`}>
                {lock.verified ? "VERIFIED" : "FAILED"}
              </b>
              overall
            </span>
            <span className="metric">
              <b className={`status ${lock.snapshot_ok ? "ok" : "broken"}`}>
                {lock.snapshot_ok ? "intact" : `drift: ${(lock.drift ?? []).join(", ")}`}
              </b>
              snapshot
            </span>
            <span className="metric">
              <b className={`status ${lock.signature_ok ? "ok" : "broken"}`}>
                {lock.signature_ok ? "valid" : "invalid"}
              </b>
              signature
            </span>
            <span className="metric">
              <b className={`status ${lock.journal_ok ? "ok" : "broken"}`}>
                {lock.journal_ok ? `${lock.journal_events_checked} events` : "broken"}
              </b>
              journal
            </span>
          </div>
          {lock.signer && (
            <p className="note">
              Signed by <code>{lock.signer.principal}</code> with key{" "}
              <code>{short(lock.signer.key_id)}</code> ({lock.signer.algorithm}){" "}
              at {lock.signer.signed_at}
            </p>
          )}
          {lock.limits && <div className="limits">{lock.limits}</div>}
          <form className="inline" onSubmit={(e) => e.preventDefault()}>
            <button className="action" onClick={() => void download()}>
              download evidence packet (JSON)
            </button>
            <a className="action" style={{ textDecoration: "none", padding: "3px 10px" }}
               href={`/api/engagements/${eid}/workpaper`} target="_blank"
               rel="noreferrer">
              open workpaper
            </a>
          </form>
          <p className="note">
            The workpaper link requires the bearer session; if it opens
            unauthorized, download the packet here and render offline.
          </p>

          <h3>Reopen (supersede the lock)</h3>
          <p className="note">
            Unlocking never deletes anything: this lock, its signature, and
            its journal anchor stay in the record permanently, and the next
            lock names it. The reason is required and becomes part of the
            engagement record (AU-C 230: changes after file assembly document
            the reason, by whom, and when). Requires the partner chair.
          </p>
          <form className="inline"
                onSubmit={(e) => { e.preventDefault(); void unlockNow(); }}>
            <input value={unlockReason} size={48}
                   placeholder="specific reason for reopening (required)"
                   onChange={(e) => setUnlockReason(e.target.value)} />
            <button className="action" type="submit"
                    disabled={unlockReason.trim().length < 10}>
              unlock with reason
            </button>
          </form>
        </>
      )}

      {(lock.history ?? []).length > 0 && (
        <>
          <h3>Lock amendment history</h3>
          <table className="dense">
            <thead>
              <tr><th>Seq</th><th>Locked</th><th>Unlocked</th><th>Reason</th>
                  <th>Integrity</th></tr>
            </thead>
            <tbody>
              {(lock.history ?? []).map((item) => (
                <tr key={item.snapshot_id}>
                  <td>{item.sequence}</td>
                  <td className="note">
                    {item.locked_at}<br />
                    signed by <code>{item.signer ?? "—"}</code>
                  </td>
                  <td className="note">
                    {item.unlocked_at}<br />
                    by <code>{item.unlocked_by}</code>
                  </td>
                  <td>{item.reason}</td>
                  <td>
                    <span className={`status ${item.manifest_ok
                      && item.signature_ok && item.journal_anchor_ok
                      ? "ok" : "broken"}`}>
                      {item.manifest_ok && item.signature_ok
                        && item.journal_anchor_ok
                        ? "verifies" : "FAILS"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="note">
            Superseded locks are re-verified from stored material on every
            read: manifest re-hashes to its digest, the signature still
            binds, and the journal hash chain still contains the head each
            lock was anchored to.
          </p>
        </>
      )}
    </>
  );
}

/** Choose a workbook's sheet and heading row, with the first rows shown so
 *  the choice is visible rather than guessed. The chosen row is highlighted;
 *  rows above it are skipped, and reading stops at the first blank row. */
function WorkbookChooser({ book, choice, onChange, onRole }: {
  book: WorkbookPreview;
  choice: Extraction;
  onChange: (choice: Extraction) => void;
  onRole: (role: string) => void;
}) {
  const sheet = book.sheets.find((s) => s.sheet === choice.sheet) ?? book.sheets[0];
  const headerRow = choice.header_row ?? sheet.suggested_header_row;
  const recipes = sheet.recipes ?? [];
  const recipe = recipes.find((r) => r.recipe === choice.recipe);
  return (
    <div className="workbook-chooser">
      {sheet.quickbooks_note && <p className="recipe-pick note">{sheet.quickbooks_note}</p>}
      {recipes.length > 0 && (
        <p className="recipe-pick">
          <label>QuickBooks report recognized: <b>{recipes[0].report}</b>{" "}
            <select value={choice.recipe ?? ""}
                    onChange={(e) => {
                      const next = recipes.find((r) => r.recipe === e.target.value);
                      onChange({ sheet: sheet.sheet,
                                 header_row: next?.header_row ?? headerRow,
                                 recipe: next?.recipe });
                      if (next) onRole(next.role);
                    }}>
              <option value="">plain mapping (no recipe)</option>
              {recipes.map((r) => <option key={r.recipe} value={r.recipe}>read as {r.role}</option>)}
            </select>
          </label>
          {recipe && <span className="note"> {recipe.note} Group headings become a
            column, subtotal rows are dropped after each is checked against its detail rows.</span>}
        </p>
      )}
      <label>Sheet{" "}
        <select value={sheet.sheet}
                onChange={(e) => {
                  const next = book.sheets.find((s) => s.sheet === e.target.value)!;
                  onChange({ sheet: next.sheet, header_row: next.suggested_header_row });
                }}>
          {book.sheets.map((s) => (
            <option key={s.sheet} value={s.sheet}>{s.sheet} ({s.row_count} rows)</option>
          ))}
        </select>
      </label>{" "}
      <label>Headings on row{" "}
        <input type="number" min={1} max={Math.max(1, sheet.row_count)} value={headerRow}
               disabled={!!recipe}
               onChange={(e) => onChange({ sheet: sheet.sheet, header_row: Number(e.target.value) })} />
      </label>{" "}
      <span className="note">suggested: row {sheet.suggested_header_row}</span>
      <table className="dense preview">
        <tbody>
          {sheet.rows.map((row, i) => (
            <tr key={i} className={i + 1 === headerRow ? "header-pick"
              : i + 1 < headerRow ? "skipped" : ""}>
              <th>{i + 1}</th>
              {row.slice(0, 8).map((cell, j) => <td key={j}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** A QuickBooks recipe's checks, for the reviewer deciding on approval. */
function RecipeSummary({ report }: { report: RecipeReport }) {
  const totals = report.subtotals_checked + (report.grand_total?.length ?? 0);
  const agreed = totals === 1 ? "the total agrees" : totals === 2 ? "both totals agree"
    : `all ${totals} totals agree`;
  const bad = report.totals_disagreeing;
  const leftOut = Object.entries(report.transaction_types ?? {})
    .filter(([, n]) => n.left_out > 0)
    .map(([kind, n]) => `${n.left_out} ${kind}`);
  const signs = Object.entries(report.amount_signs_by_account ?? {})
    .map(([account, n]) => `${account}: ${n.negative} negative, ${n.positive} positive`);
  return (
    <div className="recipe-summary">
      QuickBooks {report.report} recipe: {report.rows_kept} rows kept.{" "}
      {totals > 0 && <span className={`status ${bad.length ? "broken" : "ok"}`}>
        {bad.length
          ? `${bad.length} of ${totals} totals disagree: ${bad.map((t) =>
              `${t.group} ${t.column} (row ${t.sheet_row}) stated ${t.stated ?? "blank"}, detail sums to ${t.computed}`).join("; ")}`
          : `${agreed} with the detail rows`}
      </span>}
      {(report.missing_required ?? []).map((m) => (
        <div key={m.field} className="status broken">
          {m.rows} of {m.of} rows have no {m.field} ({m.heading} is blank) and
          will be set aside when loaded.
        </div>
      ))}
      {leftOut.length > 0 && <div className="note">Left out: {leftOut.join(", ")}.</div>}
      {signs.length > 0 && <div className="note">Amount signs as exported ({signs.join("; ")}); loaded as positive paid amounts.</div>}
    </div>
  );
}

/** The AP subledger-to-ledger tie from two QuickBooks exports: Unpaid Bills
 *  (the subledger) and the General Ledger (the control account). Building it
 *  stores a schedule as an ordinary source file, which is then proposed,
 *  approved and loaded like any other. Shown only when both kinds exist. */
function ApControlPanel({ client, eid, onError, onBuilt, artifactCount }: {
  client: Client; eid: string; onError: (e: Error) => void;
  onBuilt: () => void; artifactCount: number;
}) {
  const [found, setFound] = useState<ApControlCandidates | null>(null);
  const [sub, setSub] = useState("");
  const [ledger, setLedger] = useState("");
  const [built, setBuilt] = useState<ApControlBuilt | null>(null);
  // The parent's error handler is recreated each render; keep it out of the
  // effect's dependencies so an error banner cannot trigger another fetch.
  const reportError = useRef(onError);
  reportError.current = onError;
  useEffect(() => {
    client.apControlCandidates(eid).then((c) => {
      setFound(c);
      setSub((prev) => prev || c.subledger[0]?.artifact_id || "");
      setLedger((prev) => prev || c.ledger[0]?.artifact_id || "");
    }).catch((e) => reportError.current(e));
  }, [client, eid, artifactCount]);
  if (!found || !found.subledger.length || !found.ledger.length) return null;
  const build = () => client.buildApControl(eid, sub, ledger)
    .then((result) => { setBuilt(result); onBuilt(); }).catch(onError);
  return (
    <div className="ap-control">
      <h3>AP subledger-to-ledger tie</h3>
      <p className="note">
        The unpaid-bills total is the AP subledger; the ledger's Accounts
        Payable balance is the control account. Both reports are footed first.
        The result is saved as an "AP control balance" source file, which you
        then propose, approve and load like any other.
      </p>
      <form className="inline" onSubmit={(e) => { e.preventDefault(); void build(); }}>
        <label>Subledger{" "}
          <select value={sub} onChange={(e) => setSub(e.target.value)}>
            {found.subledger.map((a) => <option key={a.artifact_id} value={a.artifact_id}>{a.original_name}</option>)}
          </select>
        </label>{" "}
        <label>Ledger{" "}
          <select value={ledger} onChange={(e) => setLedger(e.target.value)}>
            {found.ledger.map((a) => <option key={a.artifact_id} value={a.artifact_id}>{a.original_name}</option>)}
          </select>
        </label>{" "}
        <button className="action" type="submit">build AP control balance</button>
      </form>
      {built && (
        <div className="recipe-summary">
          Subledger {built.subledger_balance} vs ledger {built.gl_balance} as of{" "}
          {built.period_end}:{" "}
          <span className={`status ${Number(built.difference) === 0 ? "ok" : "broken"}`}>
            difference {built.difference}
          </span>
          {built.notes.map((n) => <div key={n} className="note">Check: {n}.</div>)}
        </div>
      )}
    </div>
  );
}
