// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Artifact, BatchOutcome, Client, Coverage, Engagement, Finding, Readiness,
  Run, Sad, Sources, WorkflowDocument, Blocker,
  ApControlBuilt, ApControlCandidates, TrialBalanceBuilt, TrialBalanceCandidates, Extraction, RecipeReport, WorkbookPreview,
} from "./api";
import { amountsInWords, cents } from "./lib/words";
import { csvName, downloadCsv } from "./lib/csv";

interface ScreenProps {
  client: Client;
  eid: string;
  onError: (exc: unknown) => void;
  /** The client's name, for file names of downloads. */
  clientName?: string;
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

// ------------------------------------------- screen: sources and mappings

const ROLES = [
  "Vendors", "Employees", "Purchase_orders", "Vouchers", "Payments",
  "Value_flows", "Bank", "GL", "Goods_receipts", "AP_control_balance",
];

export function SourcesScreen({ client, eid, onError }: ScreenProps) {
  const load = useCallback(() => client.sources(eid), [client, eid]);
  const { data, reload } = useLoader<Sources>(load, onError);
  const fileInput = useRef<HTMLInputElement>(null);
  const folderInput = useRef<HTMLInputElement>(null);
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
  // before anything is mapped — including "map all".
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

  // Files the workbench can store as evidence; a folder's other files
  // (hidden files, Office lock files, anything else) are skipped and named.
  const ACCEPTED = /\.(csv|txt|xlsx|xls|pdf|json|png|jpe?g)$/i;

  async function uploadFiles(input: React.RefObject<HTMLInputElement>) {
    const all = Array.from(input.current?.files ?? []);
    if (!all.length) return;
    const files = all.filter((f) => ACCEPTED.test(f.name) && !f.name.startsWith(".")
                                    && !f.name.startsWith("~$"));
    const skipped = all.filter((f) => !files.includes(f)).map((f) => f.name);
    // One bad or already-stored file never stops the rest; each is named.
    const failed: string[] = [];
    for (const file of files) {
      try { await client.uploadSource(eid, file); }
      catch (exc) { failed.push(`${file.name}: ${exc instanceof Error ? exc.message : exc}`); }
    }
    if (input.current) input.current.value = "";
    const notes = [...(skipped.length ? [`skipped (not a data file): ${skipped.join(", ")}`] : []),
                   ...failed];
    if (notes.length) onError(new Error(notes.join("; ")));
    reload();
  }
  const upload = () => uploadFiles(fileInput);

  // The role a mapping would use: an explicit choice beats the filename
  // suggestion. A file is done mapping *for a role* once an active spec maps
  // it as that role; it may still feed another role (one QuickBooks report
  // can hold bills and purchase orders).
  // A file already mapped shows a role it is mapped as, never a fresh
  // filename guess: "Transaction_List_by_Vendor" once guessed Vendors and
  // "map all" would have mapped it again (30 Sep 2026).
  const activeSpecs = (data?.mapping_specs ?? []).filter((s) => s.status !== "superseded");
  const mappedAs = new Set(activeSpecs.map((s) => `${s.artifact_id}|${s.role}`));
  const rolesOf = (a: Artifact) =>
    activeSpecs.filter((s) => s.artifact_id === a.artifact_id).map((s) => s.role);
  const chosenRole = (artifact: Artifact) =>
    mapRole[artifact.artifact_id] ?? rolesOf(artifact)[0] ?? artifact.inferred_role ?? "";
  const mapped = (a: Artifact) => mappedAs.has(`${a.artifact_id}|${chosenRole(a)}`);
  // The batch takes only files with no mapping yet; a second role for a mapped
  // file is always a deliberate, one-at-a-time choice.
  const mappable = (data?.artifacts ?? []).filter(
    (a) => a.state === "promoted" && !mapped(a) && chosenRole(a) && !rolesOf(a).length);
  const normalizedSpecs = new Set(
    (data?.datasets ?? []).map((d) => d.mapping_spec_id));
  // A role that already has data needs your replace/add choice
  // (K3), so those specs are loaded one at a time, never in the batch.
  const rolesWithData = new Set((data?.datasets ?? []).map((d) => d.role));
  const normalizable = (data?.mapping_specs ?? []).filter(
    (s) => s.status === "approved" && !normalizedSpecs.has(s.spec_id)
           && !rolesWithData.has(s.role));

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
                  {(data?.roles ?? ROLES).map((role) => (
                    <option key={role} value={role}>{role.replace(/_/g, " ")}</option>))}
                </select>
                {rolesOf(artifact).length > 0 ? (
                  <div className="note">
                    mapped as {rolesOf(artifact).map((r) => r.replace(/_/g, " ")).join(", ")}
                  </div>
                ) : artifact.inferred_from === "columns" && !mapRole[artifact.artifact_id] && (
                  <div className="note">guessed from its columns: check it</div>
                )}
              </td>
              <td>
                {!mapped(artifact) && (
                  <button className="action"
                          disabled={!chosenRole(artifact)}
                          title="Map this file's columns to the role and confirm it; then load it below"
                          onClick={act(() => client.confirmMapping(
                            eid, chosenRole(artifact), artifact.artifact_id,
                            extractionFor(artifact)))}>
                    confirm mapping
                  </button>
                )}
                {isWorkbook(artifact) && !mapped(artifact) && (
                  <button className="action" onClick={() => openBook(artifact)}>
                    {books[artifact.artifact_id] ? "sheet ✓" : "choose sheet"}
                  </button>
                )}
              </td>
            </tr>
          ))}
          {(data?.artifacts ?? []).filter((a) => books[a.artifact_id]
            && !mapped(a)).map((artifact) => (
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
        <input type="file" ref={fileInput} accept=".csv,.txt,.xlsx,.xls,.pdf,.json,.png,.jpg,.jpeg" multiple />
        <button className="action" type="submit">upload sources</button>
        {" "}
        <label className="action">
          upload a folder
          <input type="file" ref={folderInput} style={{ display: "none" }}
                 {...{ webkitdirectory: "", directory: "" }}
                 onChange={() => void uploadFiles(folderInput)} />
        </label>
        {mappable.length > 0 && (
          <button className="action" type="button"
                  onClick={batch(() => client.confirmMappings(
                    eid, mappable.map((a) => ({
                      artifact_id: a.artifact_id, role: chosenRole(a),
                      extraction: extractionFor(a) }))))}>
            map all ({mappable.length})
          </button>
        )}
      </form>
      <p className="note">
        Select several exports at once — CSV or Excel (.xlsx); roles are
        suggested from the filenames, and each suggestion stays overridable
        above. For a workbook, choose the sheet and the row that holds the
        column headings; reading stops at the first blank row, so a totals
        block below the data is left out, and the mapping says so. Check each
        mapping below (fields mapped, headings left unmapped, fields refused)
        before you load it. A PDF or an
        image (a confirmation reply, a scanned invoice) is kept unaltered as
        evidence with its SHA-256 fingerprint; it is not mapped.
      </p>

      <TrialBalancePanel client={client} eid={eid} onError={onError} onBuilt={reload}
                         artifactCount={data?.artifacts.length ?? 0} />
      <ApControlPanel client={client} eid={eid} onError={onError} onBuilt={reload}
                      artifactCount={data?.artifacts.length ?? 0} />

      <h3>Mappings (confirm → load)</h3>
      {normalizable.length > 1 && (
        <form className="inline" onSubmit={(e) => e.preventDefault()}>
          <button className="action" type="button"
                  onClick={batch(() => client.normalizeBatch(
                    eid, normalizable.map((s) => s.spec_id)))}>
            load all confirmed ({normalizable.length})
          </button>
        </form>
      )}
      <table className="dense">
        <thead>
          <tr><th>Role</th><th>Status</th><th>Mapped by</th>
              <th>Mapped</th><th>Unmapped headers</th><th>Refused fields</th><th>Source</th><th /></tr>
        </thead>
        <tbody>
          {(data?.mapping_specs ?? []).map((spec) => (
            <tr key={spec.spec_id}>
              <td>{spec.role}</td>
              <td className={`status ${spec.status === "approved" ? "ok" : "pending"}`}>
                {spec.status === "approved" ? "confirmed"
                  : spec.status === "proposed" ? "not confirmed (from before 2 Oct)"
                  : spec.status}
              </td>
              <td><code>{spec.approved_by || spec.proposed_by}</code></td>
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
                          onClick={act(() => client.confirmPendingMapping(eid, spec.spec_id))}>
                    confirm
                  </button>
                )}
                {spec.status === "approved" && !normalizedSpecs.has(spec.spec_id)
                  && !rolesWithData.has(spec.role) && (
                  <button className="action"
                          onClick={act(() => client.normalize(eid, spec.spec_id))}>
                    load
                  </button>
                )}
                {spec.status === "approved" && !normalizedSpecs.has(spec.spec_id)
                  && rolesWithData.has(spec.role) && (
                  <>
                    <div className="note">{spec.role} already has data. This file:</div>
                    <button className="action" title="a revised file: the current data stops being used"
                            onClick={act(() => client.normalize(eid, spec.spec_id, "replace"))}>
                      replaces it
                    </button>{" "}
                    <button className="action" title="more rows of the same kind, e.g. another bank account"
                            onClick={act(() => client.normalize(eid, spec.spec_id, "add"))}>
                      adds to it
                    </button>
                  </>
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
                {dataset.load_mode === "add" && (
                  <div className="note">added: read together with the earlier {dataset.role} file(s)</div>
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
        Datasets are rebuilt from the immutable artifact through the confirmed
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

/** Notes recorded on a file in use, kept in view where procedures are chosen and run. */
function SourceNotes({ notes }: { notes?: Coverage["source_notes"] }) {
  if (!notes?.length) return null;
  return (
    <div className="error-bar">
      Check the data in use before relying on these results:
      <ul>
        {notes.map((n, i) => <li key={i}>{n.role} ({n.file}): {n.note}</li>)}
      </ul>
    </div>
  );
}

export function CoverageScreen({ client, eid, onError, clientName = "" }: ScreenProps) {
  const load = useCallback(async () => {
    const [coverage, workflow] = await Promise.all([
      client.coverage(eid), client.workflow(eid)]);
    return { ...coverage, decisions: workflow.document.procedures ?? {} };
  }, [client, eid]);
  const { data, reload } = useLoader<Coverage & {
    decisions: NonNullable<WorkflowDocument["procedures"]>;
  }>(load, onError);
  const [excluding, setExcluding] = useState("");
  const [reason, setReason] = useState("");
  const setPolicy = (name: string, value: string) => {
    client.updateWorkflow(eid, "policy", { name, value })
      .then(reload).catch(onError);
  };
  const choose = (procedureId: string, selected: boolean, rationale = "") => {
    client.updateWorkflow(eid, "procedure_selection",
                          { procedure_id: procedureId, selected, rationale })
      .then(() => { setExcluding(""); setReason(""); reload(); })
      .catch(onError);
  };
  if (!data) return <p className="note">Compiling coverage…</p>;
  const decision = (pid: string, fallback: boolean) =>
    data.decisions[pid] ?? { selected: fallback, rationale: "", decided_by: "" };
  return (
    <>
      <h2>Procedure coverage</h2>
      <SourceNotes notes={data.source_notes} />
      <p className="note">
        A procedure that cannot run, or that the audit does not need (for example
        the confirmation methods not chosen), is left out by the partner with a
        reason. The reason goes into the engagement record; readiness lists a
        procedure left out without one, and a blocked or partial one still included.
      </p>
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
        <span className="metric">
          <b>{data.procedures.filter((r) => !decision(r.procedure_id, r.selected).selected).length}</b>
          left out
        </span>
        <button className="action" type="button"
                title="every procedure: in the audit or left out, whether it could run, and why not"
                onClick={() => downloadCsv(csvName(clientName, "coverage"),
                  ["Procedure", "Procedure id", "Cycle", "Status", "In the audit",
                   "Reason left out", "Population", "Missing data", "Missing fields",
                   "Missing settings", "Limitations"],
                  data.procedures.map((r) => {
                    const d = decision(r.procedure_id, r.selected);
                    return [r.name, r.procedure_id, r.cycle, r.status,
                      d.selected ? "included" : "left out", d.rationale, r.population,
                      r.missing_roles.join("; "),
                      Object.entries(r.missing_fields ?? {}).map(([role, fs]) => `${role}: ${fs.join(", ")}`).join("; "),
                      r.missing_policies.join("; "), r.limitations];
                  }))}>
          download (CSV)
        </button>
      </div>
      <table className="dense">
        <thead>
          <tr><th>Procedure</th><th>Cycle</th><th>Status</th><th>In the audit</th>
              <th>Population</th><th>Missing</th><th>Limitations</th></tr>
        </thead>
        <tbody>
          {data.procedures.map((row) => {
            const d = decision(row.procedure_id, row.selected);
            return (
            <tr key={row.procedure_id} className={d.selected ? "" : "skipped"}>
              <td><b>{row.name}</b><br /><code>{row.procedure_id}</code></td>
              <td>{row.cycle}</td>
              <td><span className={`status ${row.status}`}>{row.status}</span></td>
              <td>
                {d.selected ? (
                  <span className="status ok">included</span>
                ) : (
                  <>
                    <span className="status pending">left out</span>
                    <div className="note">
                      {d.rationale
                        ? <>{d.rationale}{d.decided_by && <> ({d.decided_by})</>}</>
                        : <b>no reason recorded yet: readiness needs one</b>}
                    </div>
                  </>
                )}
                {excluding === row.procedure_id ? (
                  <form className="inline"
                        onSubmit={(e) => { e.preventDefault(); choose(row.procedure_id, false, reason.trim()); }}>
                    <input value={reason} autoFocus size={28}
                           placeholder="why leave it out? (10+ characters)"
                           onChange={(e) => setReason(e.target.value)} />
                    <button className="action" type="submit"
                            disabled={reason.trim().length < 10}>
                      {d.selected ? "leave out" : "save reason"}
                    </button>
                    <button className="action" type="button"
                            onClick={() => { setExcluding(""); setReason(""); }}>
                      cancel
                    </button>
                  </form>
                ) : (
                  <div>
                    <button className="action"
                            title="Partner: leave this procedure out of the audit, with the reason"
                            onClick={() => { setExcluding(row.procedure_id); setReason(d.rationale); }}>
                      {d.selected ? "leave out…" : d.rationale ? "change reason" : "give reason"}
                    </button>
                    {!d.selected && (
                      <>{" "}
                        <button className="action" onClick={() => choose(row.procedure_id, true)}>
                          include
                        </button>
                      </>
                    )}
                  </div>
                )}
              </td>
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
            );
          })}
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

// A run can complete while some of its tests did not run (a policy not set,
// a column not supplied). Say which, and why, next to the run: a completed
// run with nothing found is not a clean result for a test that never ran.
function RunDetails({ summary }: { summary: Record<string, unknown> }) {
  const notPerformed = (summary.not_performed ?? {}) as Record<string, string>;
  const skipped = Object.entries(notPerformed);
  const rest = Object.entries(summary).filter(([key]) => key !== "not_performed");
  // Built only when opened: a run's details can list hundreds of rows.
  const [open, setOpen] = useState(false);
  const show = (value: unknown) =>
    typeof value === "object" && value !== null
      ? JSON.stringify(value, null, 1) : String(value);
  return (
    <>
      {skipped.length > 0 && (
        <div className="not-performed">
          <b>Not performed ({skipped.length}):</b>
          <ul>
            {skipped.map(([test, why]) => (
              <li key={test}><code>{test}</code>: {why}</li>
            ))}
          </ul>
        </div>
      )}
      {rest.length > 0 && (
        <details className="run-details"
                 onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
          <summary>run details</summary>
          {open && <table className="dense">
            <tbody>
              {rest.map(([key, value]) => (
                <tr key={key}>
                  <th><code>{key}</code></th>
                  <td><pre>{show(value)}</pre></td>
                </tr>
              ))}
            </tbody>
          </table>}
        </details>
      )}
    </>
  );
}

export function RunsScreen({ client, eid, onError, clientName = "" }: ScreenProps) {
  const load = useCallback(async () => {
    const [{ runs }, { findings }, coverage] = await Promise.all([
      client.runs(eid), client.findings(eid), client.coverage(eid),
    ]);
    return { runs, findings, coverage };
  }, [client, eid]);
  const { data, reload } = useLoader(load, onError);
  const [procedureId, setProcedureId] = useState("");
  const [noteDraft, setNoteDraft] = useState<Record<string, string>>({});
  const [onlyProc, setOnlyProc] = useState("");
  const [onlyStatus, setOnlyStatus] = useState("");
  const [latestOnly, setLatestOnly] = useState(true);
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const [bulkStatus, setBulkStatus] = useState("");
  const [bulkNote, setBulkNote] = useState("");
  const [bulkBusy, setBulkBusy] = useState(false);

  const act = (work: () => Promise<unknown>) => () => {
    work().then(reload).catch(onError);
  };

  const executable = (data?.coverage.procedures ?? [])
    .filter((row) => row.status === "executable");
  // Plain names from coverage; the code stays beside it, small.
  const nameOf: Record<string, string> = {};
  for (const row of data?.coverage.procedures ?? []) nameOf[row.procedure_id] = row.name;
  const named = (pid: string) => nameOf[pid] ?? pid;

  // The latest completed run of each procedure: its findings are current;
  // an earlier run's are superseded by the rerun (hidden only while the box
  // is ticked, and counted when hidden).
  const latestRun: Record<string, string> = {};
  for (const run of data?.runs ?? []) {
    if (run.status !== "error") latestRun[run.procedure_id] = run.run_id;
  }
  const all = data?.findings ?? [];
  const fromLatest = all.filter((f) => latestRun[f.procedure_id] === f.run_id);
  const current = latestOnly ? fromLatest : all;
  const earlier = all.length - fromLatest.length;
  const procs = Object.entries(current.reduce<Record<string, number>>((acc, f) => {
    acc[f.procedure_id] = (acc[f.procedure_id] ?? 0) + 1; return acc;
  }, {})).sort();
  const isOpen = (f: Finding) => ["undisposed", "follow_up"].includes(f.disposition.status);
  const shown = current.filter((f) => (!onlyProc || f.procedure_id === onlyProc)
    && (!onlyStatus || (onlyStatus === "open" ? isOpen(f) : f.disposition.status === onlyStatus)));

  async function disposeSelected() {
    setBulkBusy(true);
    const failed: string[] = [];
    const done = new Set<string>();
    for (const f of shown.filter((x) => picked.has(x.finding_uid))) {
      if (done.has(f.finding_uid)) continue;
      done.add(f.finding_uid);
      try {
        await client.setDisposition(eid, f.finding_uid, bulkStatus, bulkNote.trim(),
                                    f.disposition.version);
      } catch (exc) {
        failed.push(`${f.procedure_id} ${f.verdict.reason.slice(0, 40)}: `
                    + `${exc instanceof Error ? exc.message : exc}`);
      }
    }
    setBulkBusy(false);
    setPicked(new Set()); setBulkStatus(""); setBulkNote("");
    if (failed.length) onError(new Error(`${failed.length} not saved: ${failed.join("; ")}`));
    reload();
  }

  return (
    <>
      <h2>Procedure runs</h2>
      <SourceNotes notes={data?.coverage.source_notes} />
      <form className="inline"
            onSubmit={(e) => {
              e.preventDefault();
              act(() => client.runProcedure(eid, procedureId, {}))();
            }}>
        <select value={procedureId} onChange={(e) => setProcedureId(e.target.value)}>
          <option value="">choose executable procedure…</option>
          {executable.map((row) => (
            <option key={row.procedure_id} value={row.procedure_id}>
              {row.name}
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
          <tr><th>Procedure</th><th>Status</th><th>Run by</th>
              <th>Error</th><th>Details</th></tr>
        </thead>
        <tbody>
          {(data?.runs ?? []).map((run: Run) => (
            <tr key={run.run_id}>
              <td><b>{named(run.procedure_id)}</b><br /><code>{run.procedure_id}</code></td>
              <td><span className={`status ${run.status}`}>{run.status}</span></td>
              <td><code>{run.executed_by}</code></td>
              <td className="note">{run.error || "—"}</td>
              <td><RunDetails summary={run.summary ?? {}} /></td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Findings and dispositions</h3>
      <form className="inline" onSubmit={(e) => e.preventDefault()}>
        <select value={onlyProc} onChange={(e) => { setOnlyProc(e.target.value); setPicked(new Set()); }}>
          <option value="">every procedure ({current.length})</option>
          {procs.map(([pid, n]) => <option key={pid} value={pid}>{named(pid)} ({n})</option>)}
        </select>
        <select value={onlyStatus} onChange={(e) => { setOnlyStatus(e.target.value); setPicked(new Set()); }}>
          <option value="">any disposition</option>
          <option value="open">open (undisposed or follow up)</option>
          <option value="undisposed">undisposed</option>
          {DISPOSITIONS.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
        <label className="note">
          <input type="checkbox" checked={latestOnly}
                 onChange={(e) => { setLatestOnly(e.target.checked); setPicked(new Set()); }} /> latest run of each procedure only
        </label>
        <span className="note">
          showing {shown.length} of {all.length}
          {latestOnly && earlier > 0 && <> ({earlier} from earlier runs hidden)</>}
        </span>
        <button className="action" type="button" disabled={!shown.length}
                title="the findings shown, with the filters above, for your own working papers"
                onClick={() => downloadCsv(csvName(clientName, "findings"),
                  ["Procedure", "Procedure id", "Verdict", "Assertion", "Class", "Finding",
                   "Magnitude", "Disposition", "Note", "Disposed by",
                   "Run", "Earlier run", "Receipt", "Evidence"],
                  shown.map((f) => [named(f.procedure_id), f.procedure_id, f.verdict.verdict,
                    f.tags.assertion, f.tags.class, f.verdict.reason, f.verdict.score,
                    f.disposition.status, f.disposition.note, f.disposition.proposed_by,
                    f.run_id,
                    latestRun[f.procedure_id] !== f.run_id ? "yes" : "", f.verdict.receipt_id,
                    JSON.stringify(f.verdict.evidence ?? {})]))}>
          download shown (CSV)
        </button>
      </form>
      {picked.size > 0 && (
        <form className="inline panel" onSubmit={(e) => { e.preventDefault(); void disposeSelected(); }}>
          <b>{picked.size} selected:</b>
          <select value={bulkStatus} onChange={(e) => setBulkStatus(e.target.value)}>
            <option value="">dispose as…</option>
            {DISPOSITIONS.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
          <input value={bulkNote} size={40} placeholder="note for each (10+ characters)"
                 onChange={(e) => setBulkNote(e.target.value)} />
          <button className="action" type="submit"
                  disabled={!bulkStatus || bulkNote.trim().length < 10 || bulkBusy}>
            {bulkBusy ? "saving…" : "apply to each"}
          </button>
          <button className="action" type="button" onClick={() => setPicked(new Set())}>clear</button>
          <span className="note">
            Each finding gets its own disposition, journaled as usual.
          </span>
        </form>
      )}
      <table className="dense">
        <thead>
          <tr><th>
                <input type="checkbox" aria-label="select all shown"
                       checked={shown.length > 0 && shown.every((f) => picked.has(f.finding_uid))}
                       onChange={(e) => setPicked(e.target.checked
                         ? new Set(shown.map((f) => f.finding_uid)) : new Set())} />
              </th><th>Procedure</th><th>Verdict</th><th>Assertion</th><th>Class</th>
              <th>Reason</th><th>Magnitude</th><th>Disposition</th><th>Note</th>
              <th /></tr>
        </thead>
        <tbody>
          {shown.map((finding: Finding) => (
            <tr key={`${finding.run_id}/${finding.finding_uid}`}>
              <td>
                <input type="checkbox" checked={picked.has(finding.finding_uid)}
                       onChange={() => setPicked((prev) => {
                         const next = new Set(prev);
                         if (next.has(finding.finding_uid)) next.delete(finding.finding_uid);
                         else next.add(finding.finding_uid);
                         return next;
                       })} />
              </td>
              <td><b>{named(finding.procedure_id)}</b><br /><code>{finding.procedure_id}</code>
                {latestRun[finding.procedure_id] !== finding.run_id
                  && <div className="note">earlier run</div>}</td>
              <td>{finding.verdict.verdict}</td>
              <td><code>{finding.tags.assertion}</code></td>
              <td>{finding.tags.class}</td>
              <td>{amountsInWords(finding.verdict.reason)}
                {Object.keys(finding.verdict.evidence ?? {}).length > 0 && (
                  <details className="run-details">
                    <summary>evidence</summary>
                    <pre>{JSON.stringify(finding.verdict.evidence, null, 1)}</pre>
                  </details>
                )}</td>
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
              <td><code>{short(finding.verdict.receipt_id)}</code></td>
            </tr>
          ))}
        </tbody>
      </table>
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
        <span className="metric">
          <b>{sad.disposed} of {sad.candidates}</b>misstatement candidates disposed
        </span>
        <span className="metric"><b>{sad.total_unadjusted.toLocaleString()}</b>disposed as unadjusted</span>
        <span className="metric"><b>{sad.total_adjusted.toLocaleString()}</b>disposed as adjusted</span>
        <span className="metric">
          <b className={`status ${sad.conclusion === "material" ? "broken"
            : sad.conclusion === "immaterial" ? "ok" : "pending"}`}>
            {sad.conclusion ?? "open"}
          </b>
          conclusion
        </span>
      </div>
      <p className="note">
        The figures above count only the misstatement candidates disposed so far
        ({sad.disposed} of {sad.candidates}; other findings are on Runs &amp; Findings);
        the conclusion stays open until every one is disposed and no waiver is
        above clearly trivial.
        {sad.schedule && <> The misstatement schedule below is a different
          figure: the evaluated total by statement line, from the misstatement
          procedure's last run.</>}
      </p>
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
            assert
          </button>
          <span className="note">
            Zero datasets means no procedure ever gated this engagement; say
            why on the record before readiness can pass.
          </span>
        </form>
      )}
      <table className="dense">
        <thead><tr><th>Unadjusted item</th><th>Reason</th><th>Amount</th></tr></thead>
        <tbody>
          {sad.unadjusted.map((line) => (
            <tr key={line.finding_id}>
              <td><code>{line.finding_id}</code></td>
              <td>{amountsInWords(line.reason)}</td>
              <td>{cents(line.amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Misstatement schedule, by statement line</h3>
      {sad.schedule ? (
        <>
          <p className="note">{sad.schedule.note}.</p>
          <table className="dense">
            <thead><tr><th>Line</th><th>Signed effect</th><th /></tr></thead>
            <tbody>
              {Object.entries(sad.schedule.lines).map(([line, amount]) => (
                <tr key={line}>
                  <td>{line.replace(/_/g, " ")}</td>
                  <td>{cents(amount)}</td>
                  <td className={`status ${sad.schedule!.material_lines.includes(line) ? "broken" : "ok"}`}>
                    {sad.schedule!.material_lines.includes(line) ? "at or above materiality" : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ) : (
        <p className="note">
          No misstatement schedule has been evaluated (completion.uncorrected_misstatements
          has not run); the summary above is the disposed findings only.
        </p>
      )}

      <h3>Materiality</h3>
      <p>
        {workflow.materiality.amount > 0
          ? workflow.materiality.amount.toLocaleString() : "not set"}
        {workflow.materiality.basis && <span className="note"> — {workflow.materiality.basis}</span>}
        <span className="note"> (set on Planning &amp; Risk)</span>
      </p>

    </>
  );
}

// ---------------------------------------- readiness blockers, in plain words

/** What each readiness code means, and the tab where it is cleared. A code
 *  missing here still shows, by its code, so nothing is ever hidden. */
const BLOCKERS: Record<string, [string, string | null]> = {
  MATERIALITY_NOT_SET: ["Materiality is not set.", "Planning & Risk"],
  RISKS_UNASSESSED: ["Some risks have no level assessed.", "Planning & Risk"],
  HIGH_RISKS_WITHOUT_RESPONSE: ["A high or significant risk has no planned response.", "Planning & Risk"],
  HIGH_RISKS_WITHOUT_PROCEDURE: ["A high or significant risk has no procedure linked to answer it.", "Planning & Risk"],
  CONTROLS_UNASSESSED: ["Some controls are not assessed (no screen for this yet).", null],
  CONTROL_RELIANCE_UNSUPPORTED: ["Reliance is placed on a control not assessed as effective (no screen for this yet).", null],
  SELECTED_PROCEDURES_BLOCKED: ["Procedures in the audit cannot run: data missing. Load it, or leave them out with a reason.", "Coverage"],
  SELECTED_PROCEDURES_PARTIAL: ["Procedures in the audit can run only in part. Supply what is missing, or leave them out with a reason.", "Coverage"],
  SELECTED_PROCEDURES_PENDING_RUN: ["Procedures in the audit have not run yet.", "Runs & Findings"],
  PROCEDURE_EXCLUSIONS_WITHOUT_RATIONALE: ["Procedures are left out with no reason recorded.", "Coverage"],
  EVIDENCE_REVIEW_PENDING: ["Evidence received waits for review (no screen for this yet).", null],
  EXTRACTION_APPROVAL_PENDING: ["Source extractions wait for approval (no screen for this yet).", null],
  TRANSFORMATION_APPROVAL_PENDING: ["Source transformations wait for approval (no screen for this yet).", null],
  MISSTATEMENTS_UNRESOLVED: ["Misstatements are not yet disposed.", "Runs & Findings"],
  SUBSTANTIVE_ITEMS_UNRESOLVED: ["Review items are not yet disposed.", "Runs & Findings"],
  FINDINGS_OPEN: ["Findings are undisposed or marked for follow-up.", "Runs & Findings"],
  WAIVERS_ABOVE_TRIVIAL_THRESHOLD: ["Findings above clearly trivial are waived; waiving is only for trivial amounts.", "Runs & Findings"],
  SCOPE_ITEMS_UNRESOLVED: ["Scope refusals are not yet resolved (no screen for this yet).", null],
  NO_DATA_WITHOUT_PARTNER_ASSERTION: ["No data is loaded; the partner must say why no data-dependent procedure applies.", "SAD & Completion"],
  DECISION_TRAIL_BROKEN: ["The journal's hash chain does not verify. Suspect the record.", null],
};

/** The readiness gate's report implication, in words (an unknown code shows as it is). */
const IMPLICATIONS: Record<string, string> = {
  not_ready: "not ready: the items below are open",
  qualified_or_disclaimer_consideration: "consider a qualified opinion or a disclaimer (scope limitation)",
  qualified_or_adverse_consideration: "consider a qualified or adverse opinion (material misstatement)",
  unmodified_opinion_candidate: "an unmodified opinion is possible",
};

/** A blocker's items in words. Findings arrive as internal keys
 *  (`audit_procedure_run|["payroll.register_tests", "e16", ...]`); they are
 *  counted by procedure, largest first, so the list says where the open work
 *  is. Any other item shows as it is. */
export function itemsInWords(items: string[]): string {
  const byProcedure = new Map<string, number>();
  const other: string[] = [];
  for (const item of items) {
    const match = /^[a-z_]+\|(\[.*\])$/.exec(item);
    let procedure: unknown = null;
    if (match) {
      try { procedure = (JSON.parse(match[1]) as unknown[])[0]; } catch { procedure = null; }
    }
    // Only a real procedure id ("payroll.register_tests") is grouped; any
    // other key shape shows as it is, so nothing is miscounted.
    if (typeof procedure === "string" && /^[a-z_]+\.[a-z_]+$/.test(procedure)) {
      byProcedure.set(procedure, (byProcedure.get(procedure) ?? 0) + 1);
    } else other.push(item);
  }
  const counted = [...byProcedure.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([procedure, n]) => `${procedure}: ${n}`);
  return [...counted, ...other].join(", ");
}

export function BlockerList({ blockers, onNavigate }: {
  blockers: Blocker[];
  onNavigate?: (tab: string) => void;
}) {
  return (
    <table className="dense">
      <thead><tr><th>Still open</th><th>Count</th><th>Where</th><th>Items</th></tr></thead>
      <tbody>
        {blockers.map((blocker) => {
          const [text, tab] = BLOCKERS[blocker.code] ?? [blocker.code, null];
          return (
            <tr key={blocker.code}>
              <td>{text}<div className="note"><code>{blocker.code}</code></div></td>
              <td>{blocker.count}</td>
              <td>
                {tab && onNavigate
                  ? <button className="action" onClick={() => onNavigate(tab)}>go to {tab}</button>
                  : <span className="note">—</span>}
              </td>
              <td className="note">{itemsInWords(blocker.items ?? [])}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

// ---------------------------------------------- screen 6: export the record

export function ExportScreen({ client, engagement, onError, onNavigate }: {
  client: Client;
  engagement: Engagement;
  onError: (exc: unknown) => void;
  onNavigate?: (tab: string) => void;
}) {
  const eid = engagement.engagement_id;
  const load = useCallback(() => client.readiness(eid), [client, eid]);
  const { data: readiness } = useLoader<Readiness>(load, onError);
  const stamp = () => new Date().toISOString().slice(0, 10);

  function save(content: string, type: string, name: string) {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([content], { type }));
    link.download = name;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  async function downloadRecord() {
    try {
      const packet = await client.exportRecord(eid);
      save(JSON.stringify(packet, null, 2), "application/json",
           `record-${engagement.client_name}-${engagement.period_end}-${stamp()}.json`);
    } catch (exc) { onError(exc); }
  }

  async function saveWorkpaper() {
    try {
      const html = await client.workpaperHtml(eid);
      save(html, "text/html",
           `working-paper-${engagement.client_name}-${engagement.period_end}-${stamp()}.html`);
    } catch (exc) { onError(exc); }
  }

  if (!readiness) return <p className="note">Deriving readiness…</p>;
  return (
    <>
      <h2>Completion readiness</h2>
      <div className="panel">
        <span className="metric">
          <b className={`status ${readiness.ready ? "ok" : "broken"}`}>
            {readiness.ready ? "READY" : "NOT READY"}
          </b>
          for an opinion
        </span>
        <span className="metric">
          <b>{IMPLICATIONS[readiness.report_implication] ?? readiness.report_implication}</b>
          what it means for the report
        </span>
      </div>
      {readiness.blockers.length > 0 && (
        <BlockerList blockers={readiness.blockers} onNavigate={onNavigate} />
      )}

      <h3>Export</h3>
      <p className="note">
        The record as it stands now: sources, mappings, runs, findings,
        dispositions, the summary of misstatements, readiness and the draft
        opinion. It is not signed. Noesi supplements the audit; your firm's
        own review and sign-off stay outside it. Each export is written to
        the journal with its digest.
      </p>
      <form className="inline" onSubmit={(e) => e.preventDefault()}>
        <button className="action" onClick={() => void downloadRecord()}>
          download the record (JSON)
        </button>
        <button className="action" onClick={() => void saveWorkpaper()}>
          save working paper (HTML)
        </button>
      </form>
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

/** A QuickBooks recipe's checks, shown with the mapping before it is loaded. */
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

/** The trial balance from QuickBooks Trial Balance exports: QuickBooks gives
 *  one date per report, so this period's and the prior period's are joined
 *  by account into one schedule with a Prior Balance column. Building it
 *  stores the schedule as an ordinary source file, then mapped and loaded
 *  like any other. Shown only when a Trial Balance export exists. */
function TrialBalancePanel({ client, eid, onError, onBuilt, artifactCount }: {
  client: Client; eid: string; onError: (e: Error) => void;
  onBuilt: () => void; artifactCount: number;
}) {
  const [found, setFound] = useState<TrialBalanceCandidates | null>(null);
  const [current, setCurrent] = useState("");
  const [prior, setPrior] = useState("");
  const [built, setBuilt] = useState<TrialBalanceBuilt | null>(null);
  const reportError = useRef(onError);
  reportError.current = onError;
  useEffect(() => {
    client.trialBalanceCandidates(eid).then((c) => {
      setFound(c);
      // Newest date first as this period; the next one back as the prior.
      const byDate = [...c.trial_balances].sort((a, b) => (b.as_of ?? "").localeCompare(a.as_of ?? ""));
      setCurrent((prev) => prev || byDate[0]?.artifact_id || "");
      setPrior((prev) => prev || byDate[1]?.artifact_id || "");
    }).catch((e) => reportError.current(e));
  }, [client, eid, artifactCount]);
  if (!found || !found.trial_balances.length) return null;
  const label = (a: TrialBalanceCandidates["trial_balances"][number]) =>
    `${a.original_name} (${a.as_of ?? a.period ?? "undated"})`;
  const build = () => client.buildTrialBalance(eid, current, prior)
    .then((result) => { setBuilt(result); onBuilt(); }).catch(onError);
  return (
    <div className="ap-control">
      <h3>Trial balance from QuickBooks</h3>
      <p className="note">
        QuickBooks exports a trial balance for one date. Choose this period's
        export and, for prior-year comparisons, last year's; each is footed
        against its TOTAL first. The result is saved as a "Trial balance"
        source file, which you then map and load like any other,
        and map its accounts to statement lines under "Trial balance lines" on
        Scope &amp; Policies.
      </p>
      <form className="inline" onSubmit={(e) => { e.preventDefault(); void build(); }}>
        <label>This period{" "}
          <select value={current} onChange={(e) => {
            // The file chosen as this period cannot stay chosen as the prior.
            setCurrent(e.target.value);
            if (prior === e.target.value) setPrior("");
          }}>
            {found.trial_balances.map((a) => <option key={a.artifact_id} value={a.artifact_id}>{label(a)}</option>)}
          </select>
        </label>{" "}
        <label>Prior period{" "}
          <select value={prior} onChange={(e) => setPrior(e.target.value)}>
            <option value="">none</option>
            {found.trial_balances.filter((a) => a.artifact_id !== current).map((a) =>
              <option key={a.artifact_id} value={a.artifact_id}>{label(a)}</option>)}
          </select>
        </label>{" "}
        <button className="action" type="submit">build trial balance</button>
      </form>
      {built && (
        <div className="recipe-summary">
          {built.accounts} accounts as of {built.as_of}
          {built.prior_as_of ? `, with prior balances as of ${built.prior_as_of}` : ", no prior column"}.
          {built.notes.map((n) => <div key={n} className="note">Check: {n}.</div>)}
        </div>
      )}
    </div>
  );
}

/** The AP subledger-to-ledger tie from two QuickBooks exports: Unpaid Bills
 *  (the subledger) and the General Ledger (the control account). Building it
 *  stores a schedule as an ordinary source file, which is then mapped and
 *  loaded like any other. Shown only when both kinds exist. */
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
        then map and load like any other.
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
