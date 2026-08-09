// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Planning & Risk: the assertion-level risk register and its response
 *  linkage. A risk assessment is auditor *judgment* — the workbench stores
 *  it, names who proposed it, and (above a moderate level) requires a second
 *  person to concur, the same separation dispositions and runs carry. The
 *  engine never grades a risk; linking a procedure is how the response is
 *  recorded, and a significant risk with no procedure answering it refuses
 *  the lock. */

import { useCallback, useState } from "react";
import { Client, Risk, RiskRegister } from "../api";
import { useResource } from "../lib/useResource";

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
      rationale: rationale.trim(), response: response.trim(),
    }))();
    setTitle(""); setAssertion(""); setLevel("unassessed");
    setRationale(""); setResponse("");
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
      <h2>Risk assessment</h2>
      <p className="note">
        Record the risks of material misstatement at the assertion level, then
        link the procedures that respond to each. Judgment is the auditor's —
        a significant risk is a proposal until a reviewer or partner concurs,
        and a significant risk with no procedure answering it blocks the lock.
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
                <th>Responding procedures</th><th>Concurrence</th><th /></tr>
          </thead>
          <tbody>
            {risks.map((r) => (
              <tr key={r.risk_id}>
                <td>{r.title || <span className="note">untitled</span>}
                    {r.rationale && <div className="note">{r.rationale}</div>}</td>
                <td><code>{r.assertion}</code></td>
                <td>
                  <select value={r.level}
                          onChange={(e) => act(() => client.assessRisk(eid, {
                            risk_id: r.risk_id, title: r.title,
                            assertion: r.assertion, level: e.target.value,
                            rationale: r.rationale, response: r.response,
                            expected_version: r.version,
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
                  {r.awaiting_concurrence ? (
                    <button className="action"
                            title="Significant/high risk: a reviewer or partner (not the proposer) must concur"
                            onClick={act(() => client.concurRisk(
                              eid, r.risk_id, r.version))}>
                      concur
                    </button>
                  ) : r.requires_concurrence && r.concurred_by ? (
                    <span className="status ok"
                          title={`concurred by ${r.concurred_by}`}>concurred</span>
                  ) : r.requires_concurrence ? (
                    <span className="note">needs response first</span>
                  ) : (
                    <span className="note">—</span>
                  )}
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
      <p className="note">
        Changing a risk's level, response, or linked procedures voids any prior
        concurrence — the concurrer agreed to a different judgment.
      </p>
    </>
  );
}
