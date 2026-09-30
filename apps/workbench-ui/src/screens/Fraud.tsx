// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Fraud: AU-C 240 in one place — the fraud risks the team marked, every
 *  test that looks for a fraud scheme, and what those tests found.
 *  It gathers; it concludes nothing. A test that could not run on these
 *  records is shown as untested, never as clean. Acting on a finding
 *  (disposing, following up) happens on Runs & Findings, as usual. */

import { useCallback } from "react";
import { Client, FraudTest, FraudView } from "../api";
import { useResource } from "../lib/useResource";

const COVERAGE: Record<string, [string, string]> = {
  executable: ["ok", "can run"],
  partial: ["pending", "partly"],
  blocked: ["bad", "cannot run"],
  unsupported: ["bad", "not available"],
  not_available: ["bad", "not available"],
};

const money = (value: number | null | undefined) =>
  value === null || value === undefined ? "—"
    : value.toLocaleString(undefined, { minimumFractionDigits: 2,
                                        maximumFractionDigits: 2 });

function CanRun({ t }: { t: FraudTest }) {
  const [cls, label] = COVERAGE[t.coverage] ?? ["pending", t.coverage];
  return <span className={`pill ${cls}`}>{label}</span>;
}

export function FraudScreen({ client, eid, onError: _onError }: {
  client: Client;
  eid: string;
  onError: (exc: unknown) => void;
}) {
  const load = useCallback(() => client.fraud(eid), [client, eid]);
  const { data, error, reload } = useResource<FraudView>(load);

  if (error) return <div className="error-bar">{error}</div>;
  if (!data) return <p className="note">Gathering the fraud work…</p>;
  const { tests, risks, findings, summary, presumed_risks } = data;
  const scheme = Object.fromEntries(tests.map((t) => [t.procedure_id, t.scheme]));

  return (
    <>
      <div className="panel">
        <h3>Fraud (AU-C 240) <button className="action" onClick={reload}>refresh</button></h3>
        <p className="note">
          {summary.fraud_risks} fraud risk{summary.fraud_risks === 1 ? "" : "s"} marked ·{" "}
          {summary.run} of {summary.tests} fraud tests run ·{" "}
          {summary.partly} can run only in part ·{" "}
          {summary.cannot_run} cannot run on these records ·{" "}
          {summary.findings} finding{summary.findings === 1 ? "" : "s"},{" "}
          <b>{summary.open_findings} still open</b>
        </p>
        <p className="note">
          This tab gathers the fraud work; it concludes nothing. A test that could
          not run is untested, not clean. Whether fraud occurred is the auditor's
          judgment.
        </p>
      </div>

      <div className="panel">
        <h3>Fraud risks</h3>
        <ul className="note">
          {presumed_risks.map((p) => <li key={p}>{p}</li>)}
        </ul>
        {risks.length === 0 ? (
          <p className="note">
            No risk is marked as a fraud risk yet. Mark them on <b>Planning &amp; Risk</b>
            {" "}(the "fraud risk" box).
          </p>
        ) : (
          <table className="dense">
            <thead><tr><th>Risk</th><th>Assertion</th><th>Level</th>
              <th>Responding procedures</th><th>Concurrence</th></tr></thead>
            <tbody>
              {risks.map((r) => (
                <tr key={r.risk_id}>
                  <td>{r.title}{r.rationale && <div className="note">{r.rationale}</div>}</td>
                  <td><code>{r.assertion}</code></td>
                  <td>{r.level}</td>
                  <td>{r.procedure_ids.length
                    ? r.procedure_ids.map((p) => <div key={p}><code>{p}</code></div>)
                    : <span className="status bad">none linked</span>}</td>
                  <td>{r.concurred_by ? `concurred by ${r.concurred_by}`
                    : r.requires_concurrence ? <span className="status pending">awaiting</span> : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="panel">
        <h3>Fraud tests</h3>
        <table className="dense">
          <thead><tr><th>Scheme</th><th>Procedure</th><th>On these records</th>
            <th>Last run</th><th>Findings</th><th>Why not / limits</th></tr></thead>
          <tbody>
            {tests.map((t) => (
              <tr key={t.procedure_id}>
                <td>{t.scheme}<div className="note">{t.basis}</div></td>
                <td><code>{t.procedure_id}</code>{!t.in_scope && <div className="note">not in scope</div>}</td>
                <td><CanRun t={t} /></td>
                <td>{t.last_run ? `${t.last_run.status}, ${t.last_run.at.slice(0, 10)}`
                  : <span className="note">not run</span>}</td>
                <td>{t.findings}{t.open > 0 && <span className="status pending"> ({t.open} open)</span>}</td>
                <td className="note">
                  {t.missing.length > 0 && <div>needs: {t.missing.join(", ")}</div>}
                  {t.limitations}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel">
        <h3>What the fraud tests found</h3>
        {findings.length === 0 ? (
          <p className="note">No fraud-test findings yet (or no fraud test has run).</p>
        ) : (
          tests.filter((t) => t.findings > 0).map((t) => {
            const mine = findings.filter((f) => f.procedure_id === t.procedure_id);
            return (
              <details key={t.procedure_id}>
                <summary>
                  <b>{scheme[t.procedure_id]}</b> — {mine.length} finding{mine.length === 1 ? "" : "s"}
                  {t.open > 0 && <span className="status pending"> ({t.open} open)</span>}{" "}
                  <code>{t.procedure_id}</code>
                </summary>
                <table className="dense">
                  <thead><tr><th>Finding</th><th>Magnitude</th><th>Disposition</th></tr></thead>
                  <tbody>
                    {mine.map((f) => (
                      <tr key={f.finding_uid}>
                        <td>{f.verdict.reason}</td>
                        <td>{f.verdict.score === null || f.verdict.score === undefined ? "—" : f.procedure_id === "ap.vendor_relational_twins" ? `similarity ${f.verdict.score}` : money(f.verdict.score)}</td>
                        <td><span className={`status ${f.disposition.status === "undisposed" || f.disposition.status === "follow_up" ? "pending" : "ok"}`}>
                          {f.disposition.status}</span>
                          {f.disposition.note && <div className="note">{f.disposition.note}</div>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            );
          })
        )}
        <p className="note">Magnitude is the finding's dollar amount, except for vendor twins, where it is how alike the two vendors are (1 = identical). Dispose or follow up each finding on <b>Runs &amp; Findings</b>.</p>
      </div>
    </>
  );
}
