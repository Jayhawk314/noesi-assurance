// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Planning & Risk: the assertion-level risk register and its response
 *  linkage. A risk assessment is auditor *judgment* — the workbench stores
 *  it and names who recorded it. The engine never grades a risk; linking a
 *  procedure is how the response is recorded, and a significant risk with
 *  no procedure answering it is a readiness blocker. */

import { useCallback, useState } from "react";
import { Client, Risk, RiskRegister, Sad, WorkflowDocument } from "../api";
import { useResource } from "../lib/useResource";

const BENCHMARKS = ["total revenue", "total assets", "pretax income", "total expenses", "equity"];

const amount = (value: number | null | undefined) =>
  value === null || value === undefined ? "—"
    : value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** Overall materiality: the benchmark, the percentage applied, the amount,
 *  and why. Performance materiality and clearly trivial follow from it (the
 *  SAD's rates; clearly trivial's rate is set on Scope & Policies). */
function MaterialityPanel({ client, eid, onError }: {
  client: Client; eid: string; onError: (exc: unknown) => void;
}) {
  const load = useCallback(async () => {
    const [{ document }, sad] = await Promise.all([client.workflow(eid), client.sad(eid)]);
    return { m: document.materiality as WorkflowDocument["materiality"], sad: sad as Sad };
  }, [client, eid]);
  const { data, error, reload } = useResource(load);
  const [basis, setBasis] = useState("");
  const [base, setBase] = useState("");
  const [pct, setPct] = useState("");
  const [direct, setDirect] = useState("");
  const [why, setWhy] = useState("");
  if (error) return <div className="error-bar">{error}</div>;
  if (!data) return null;
  const { m, sad } = data;
  const computed = Number(base) > 0 && Number(pct) > 0
    ? Math.round(Number(base) * Number(pct)) / 100 : null;
  const ready = !!basis.trim() && why.trim().length >= 10
    && (computed !== null || Number(direct) > 0);

  function save(e: React.FormEvent) {
    e.preventDefault();
    const values: Record<string, unknown> = { basis: basis.trim(), rationale: why.trim() };
    if (computed !== null) { values.benchmark_amount = base; values.percentage = pct; }
    else values.amount = Number(direct);
    client.updateWorkflow(eid, "materiality", values)
      .then(() => { setBase(""); setPct(""); setDirect(""); setWhy(""); reload(); })
      .catch(onError);
  }

  return (
    <div className="panel">
      <h3>Materiality</h3>
      <p>
        <b>{m.amount > 0 ? amount(m.amount) : "not set"}</b>
        {m.basis && <> — {m.percentage ? `${m.percentage}% of ${m.basis}` : m.basis}
          {m.benchmark_amount && <> ({amount(Number(m.benchmark_amount))})</>}</>}
        {m.rationale && <div className="note">Why: {m.rationale}</div>}
      </p>
      <p className="note">
        Performance materiality {amount(sad.performance_materiality)} · clearly
        trivial {amount(sad.clearly_trivial)} (both rates are set on Scope &amp; Policies).
      </p>
      <form className="inline" onSubmit={save}>
        <input list="benchmarks" value={basis} placeholder="benchmark (e.g. total revenue)"
               size={22} onChange={(e) => setBasis(e.target.value)} />
        <datalist id="benchmarks">
          {BENCHMARKS.map((b) => <option key={b} value={b} />)}
        </datalist>
        <input value={base} placeholder="benchmark amount" size={14}
               onChange={(e) => setBase(e.target.value)} />
        <input value={pct} placeholder="%" size={5}
               onChange={(e) => setPct(e.target.value)} />
        <span className="note">
          {computed !== null ? `= ${amount(computed)}` : "or the amount:"}
        </span>
        {computed === null && (
          <input value={direct} placeholder="amount" size={12}
                 onChange={(e) => setDirect(e.target.value)} />
        )}
        <input value={why} placeholder="why this benchmark and rate (10+ characters)" size={34}
               onChange={(e) => setWhy(e.target.value)} />
        <button className="action" type="submit" disabled={!ready}>set materiality</button>
      </form>
    </div>
  );
}

const LEVEL_CLASS: Record<string, string> = {
  significant: "broken", high: "broken", moderate: "pending",
  low: "ok", unassessed: "pending",
};

export function RiskScreen({ client, eid, onError }: {
  client: Client;
  eid: string;
  onError: (exc: unknown) => void;
}) {
  const load = useCallback(() => client.risks(eid), [client, eid]);
  const { data, error, reload } = useResource<RiskRegister>(load);

  const [title, setTitle] = useState("");
  const [assertion, setAssertion] = useState("");
  const [level, setLevel] = useState("unassessed");
  const [rationale, setRationale] = useState("");
  const [response, setResponse] = useState("");
  const [fraud, setFraud] = useState(false);
  const [procDraft, setProcDraft] = useState<Record<string, string[]>>({});

  const act = (work: () => Promise<unknown>) => () => {
    work().then(reload).catch(onError);
  };

  if (error) return <div className="error-bar">{error}</div>;
  if (!data) return <p className="note">Loading…</p>;
  const { risks, assertions, levels } = data;

  function addRisk(e: React.FormEvent) {
    e.preventDefault();
    act(() => client.assessRisk(eid, {
      title: title.trim(), assertion, level,
      rationale: rationale.trim(), response: response.trim(), fraud,
    }))();
    setTitle(""); setAssertion(""); setLevel("unassessed");
    setRationale(""); setResponse(""); setFraud(false);
  }

  const selected = (r: Risk) => procDraft[r.risk_id] ?? r.procedure_ids;
  function toggleProc(r: Risk, pid: string) {
    const cur = selected(r);
    const next = cur.includes(pid)
      ? cur.filter((p) => p !== pid) : [...cur, pid];
    setProcDraft({ ...procDraft, [r.risk_id]: next });
  }

  return (
    <>
      <MaterialityPanel client={client} eid={eid} onError={onError} />
      <h2>Risk assessment</h2>
      <p className="note">
        Record the risks of material misstatement at the assertion level, then
        link the procedures that respond to each. Judgment is the auditor's;
        a significant risk with no procedure answering it is a readiness blocker.
      </p>

      <form className="inline" onSubmit={addRisk}>
        <input value={title} placeholder="risk (e.g. fictitious vendors)"
               size={28} onChange={(e) => setTitle(e.target.value)} />
        <select value={assertion} onChange={(e) => setAssertion(e.target.value)}>
          <option value="">assertion…</option>
          {assertions.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
        <select value={level} onChange={(e) => setLevel(e.target.value)}>
          {levels.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <input value={rationale} placeholder="rationale" size={22}
               onChange={(e) => setRationale(e.target.value)} />
        <input value={response} placeholder="planned response" size={22}
               onChange={(e) => setResponse(e.target.value)} />
        <label title="AU-C 240: a fraud risk is assessed and answered on its own">
          <input type="checkbox" checked={fraud}
                 onChange={(e) => setFraud(e.target.checked)} /> fraud risk
        </label>
        <button className="action" type="submit"
                disabled={!title.trim() || !assertion}>
          add risk
        </button>
      </form>

      {risks.length === 0 ? (
        <p className="note">No risks recorded yet.</p>
      ) : (
        <table className="dense">
          <thead>
            <tr><th>Risk</th><th>Assertion</th><th>Level</th><th>Response</th>
                <th>Responding procedures</th><th /></tr>
          </thead>
          <tbody>
            {risks.map((r) => (
              <tr key={r.risk_id}>
                <td>{r.fraud && <span className="pill bad" title="fraud risk (AU-C 240)">fraud</span>}{" "}
                    {r.title || <span className="note">untitled</span>}
                    {r.rationale && <div className="note">{r.rationale}</div>}
                    <label className="note">
                      <input type="checkbox" checked={r.fraud}
                             onChange={(e) => act(() => client.assessRisk(eid, {
                               risk_id: r.risk_id, title: r.title,
                               assertion: r.assertion, level: r.level,
                               rationale: r.rationale, response: r.response,
                               expected_version: r.version, fraud: e.target.checked,
                             }))()} /> fraud risk
                    </label></td>
                <td><code>{r.assertion}</code></td>
                <td>
                  <select value={r.level}
                          onChange={(e) => act(() => client.assessRisk(eid, {
                            risk_id: r.risk_id, title: r.title,
                            assertion: r.assertion, level: e.target.value,
                            rationale: r.rationale, response: r.response,
                            expected_version: r.version, fraud: r.fraud,
                          }))()}>
                    {levels.map((l) => <option key={l} value={l}>{l}</option>)}
                  </select>
                  <span className={`status ${LEVEL_CLASS[r.level] ?? "pending"}`}>
                    {r.level}
                  </span>
                </td>
                <td className="note">{r.response || "—"}</td>
                <td>
                  {r.candidate_procedures.map((pid) => (
                    <label key={pid} className="proc-option" title={pid}>
                      <input type="checkbox"
                             checked={selected(r).includes(pid)}
                             onChange={() => toggleProc(r, pid)} />
                      {pid}
                    </label>
                  ))}
                  <button className="action"
                          onClick={act(() => client.linkRiskProcedures(
                            eid, r.risk_id, selected(r), r.version))}>
                    link
                  </button>
                </td>
                <td>
                  <button className="action"
                          onClick={act(() => client.archiveRisk(
                            eid, r.risk_id, r.version))}>
                    archive
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
