// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Scope & Policies: which audit areas this engagement covers, the period
 *  it covers, and the auditor's settings each area needs. All three are the
 *  partner's decisions; the server refuses them from any other chair. The
 *  list of areas, procedures and settings comes from the server
 *  (GET /api/cycles), so this screen never drifts from the engine. */

import { useCallback, useState } from "react";
import { Client, CycleArea, CycleCatalog, WorkflowDocument } from "../api";
import { useResource } from "../lib/useResource";

const AREA_LABEL: Record<string, string> = {
  planning: "Planning", controls: "Tests of controls",
  journal_entries: "Journal entries", receivables: "Revenue and receivables",
  payables: "Payables (additional procedures)", payroll: "Payroll",
  cash: "Cash", inventory: "Inventory", ppe: "Property and equipment",
  debt_equity: "Debt and equity", accruals: "Accruals and prepaids",
  estimates: "Estimates and related parties", completion: "Completion",
};

const words = (name: string) => name.replace(/_/g, " ");

export function ScopeScreen({ client, eid, onError }: {
  client: Client;
  eid: string;
  onError: (exc: unknown) => void;
}) {
  const loadCatalog = useCallback(() => client.cycleCatalog(), [client]);
  const loadDoc = useCallback(() => client.workflow(eid), [client, eid]);
  const catalog = useResource<CycleCatalog>(loadCatalog);
  const doc = useResource<{ document: WorkflowDocument; version: number }>(loadDoc);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [start, setStart] = useState<string | null>(null);

  if (catalog.error) return <div className="error-bar">{catalog.error}</div>;
  if (doc.error) return <div className="error-bar">{doc.error}</div>;
  if (!catalog.data || !doc.data) return <p className="note">Loading…</p>;

  const document = doc.data.document;
  const inScope = new Set(document.cycles ?? []);
  const policies = document.policies ?? {};
  const periodStart = start ?? document.period?.start ?? "";

  const save = (section: string, values: Record<string, unknown>) =>
    client.updateWorkflow(eid, section, values).then(doc.reload).catch(onError);

  function toggle(area: CycleArea) {
    const next = new Set(inScope);
    if (next.has(area.scope)) next.delete(area.scope); else next.add(area.scope);
    void save("cycles", { cycles: [...next] });
  }

  function savePolicy(name: string) {
    const value = (draft[name] ?? "").trim();
    if (!value) return;
    void save("policy", { name, value }).then(() =>
      setDraft((d) => { const n = { ...d }; delete n[name]; return n; }));
  }

  const PolicyRow = ({ name, required }: { name: string; required: boolean }) => (
    <tr>
      <td>{words(name)}{required && <span className="status pending"> required</span>}</td>
      <td><code>{policies[name] ?? "—"}</code></td>
      <td>
        <input value={draft[name] ?? ""} placeholder="new value"
               onChange={(e) => setDraft({ ...draft, [name]: e.target.value })} />
        {" "}
        <button className="action" disabled={!(draft[name] ?? "").trim()}
                onClick={() => savePolicy(name)}>set</button>
      </td>
    </tr>
  );

  return (
    <>
      <div className="panel">
        <h3>Period</h3>
        <p className="note">
          The period's first day. Leave it empty for the twelve months ending at
          period end; set it for a first year or a changed year end.
        </p>
        <form className="inline" onSubmit={(e) => { e.preventDefault(); void save("period", { start: periodStart }); }}>
          <input value={periodStart} placeholder="YYYY-MM-DD"
                 onChange={(e) => setStart(e.target.value)} />{" "}
          <button className="action" type="submit">save period start</button>
        </form>
      </div>

      <div className="panel">
        <h3>Audit areas in scope</h3>
        <p className="note">
          Switch an area on to see its procedures in Coverage and Runs. Switching
          one off retires its settings (kept in the record, not reused).
        </p>
        <table className="dense">
          <thead><tr><th>Area</th><th>Procedures</th><th /></tr></thead>
          <tbody>
            {catalog.data.areas.map((area) => (
              <tr key={area.scope}>
                <td>{AREA_LABEL[area.scope] ?? words(area.scope)}</td>
                <td>{area.procedures.map((p) => p.title).join(" · ")}</td>
                <td>
                  <label>
                    <input type="checkbox" checked={inScope.has(area.scope)}
                           onChange={() => toggle(area)} /> in scope
                  </label>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {catalog.data.areas.filter((a) => inScope.has(a.scope)
        && (a.required_policies.length || a.optional_policies.length)).map((area) => (
        <div className="panel" key={`${area.scope}-policies`}>
          <h3>{AREA_LABEL[area.scope] ?? words(area.scope)}: settings</h3>
          <table className="dense">
            <thead><tr><th>Setting</th><th>Current</th><th>Change</th></tr></thead>
            <tbody>
              {area.required_policies.map((n) => <PolicyRow key={n} name={n} required />)}
              {area.optional_policies.map((n) => <PolicyRow key={n} name={n} required={false} />)}
            </tbody>
          </table>
        </div>
      ))}
    </>
  );
}
