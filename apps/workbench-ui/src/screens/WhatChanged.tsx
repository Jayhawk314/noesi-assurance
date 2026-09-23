// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** What Changed: a newer client file and everything it reaches.
 *  Read-only. The report compares the newest file for each role with the
 *  one before it, names the runs whose inputs moved, and shows — per
 *  finding — what a rerun would change and which judgment to revisit.
 *  Acting on it (rerun, re-review, re-dispose) happens on the other tabs,
 *  under the right chair, journaled as usual. */

import { useCallback } from "react";
import { Client, Impact, ImpactCard, Significance } from "../api";
import { useResource } from "../lib/useResource";

const SIGNIFICANCE: Record<Significance, [string, string]> = {
  none: ["idle", "no dollar effect"],
  below_trivial: ["ok", "below clearly trivial"],
  above_trivial: ["pending", "above clearly trivial"],
  above_performance: ["bad", "above performance materiality"],
};

const ACTION_LABEL: Record<ImpactCard["action"], string> = {
  dispose: "needs a disposition",
  revisit_disposition: "revisit your disposition",
  reassess_disposition: "reassess your disposition",
  none_after_rerun: "clears on rerun",
};

const CHANGE_LABEL: Record<ImpactCard["change"], string> = {
  new_after_revision: "new",
  resolved_by_revision: "disappears",
  amount_changed: "amount moves",
};

const money = (value: number | null | undefined) =>
  value === null || value === undefined ? "—"
    : value.toLocaleString(undefined, { minimumFractionDigits: 2,
                                        maximumFractionDigits: 2 });

function Sig({ level }: { level: Significance }) {
  const [cls, label] = SIGNIFICANCE[level];
  return <span className={`pill ${cls}`}>{label}</span>;
}

export function WhatChangedScreen({ client, eid, onError: _onError }: {
  client: Client;
  eid: string;
  onError: (exc: unknown) => void;
}) {
  const load = useCallback(() => client.impact(eid), [client, eid]);
  const { data, error, reload } = useResource<Impact>(load);

  if (error) return <div className="error-bar">{error}</div>;
  if (!data) return <p className="note">Comparing file versions…</p>;
  const { summary, revisions, stale_runs, cards, thresholds } = data;

  if (!revisions.length) {
    return (
      <div className="panel">
        <h3>What changed</h3>
        <p className="note">
          No client file has been replaced yet. When the client sends a
          corrected file, upload and normalize it on <b>Sources &amp;
          Mappings</b>; this tab then shows every run, finding and judgment
          that rested on the old version.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="panel">
        <h3>What changed <button className="small" onClick={reload}>refresh</button></h3>
        <p className="note">
          {summary.revised_files} revised file{summary.revised_files === 1 ? "" : "s"} ·{" "}
          {summary.stale_runs} stale run{summary.stale_runs === 1 ? "" : "s"} ·{" "}
          {summary.affected_findings} finding{summary.affected_findings === 1 ? "" : "s"} move ·{" "}
          <b>{summary.judgments_to_revisit}</b> judgment{summary.judgments_to_revisit === 1 ? "" : "s"} to revisit ·{" "}
          SAD unadjusted would move {money(summary.sad_effect.unadjusted)}{" "}
          <Sig level={summary.significance} />
        </p>
        <p className="note">
          Thresholds: clearly trivial {money(thresholds.clearly_trivial)} ·
          performance {money(thresholds.performance)} · overall {money(thresholds.materiality)}
          {!thresholds.materiality && " — set materiality on SAD & Completion; until then every change is treated as above trivial."}
        </p>
      </div>

      {revisions.map((rev) => (
        <div className="panel" key={rev.role}>
          <h3>{rev.role}: {rev.before.file} → {rev.after.file}</h3>
          <p className="note">
            {rev.diff.rows_before} → {rev.diff.rows_after} rows, matched on{" "}
            {rev.diff.key_fields.join(" + ")} · net {money(rev.diff.net_amount_change)}{" "}
            <Sig level={rev.diff.significance} />
          </p>
          <table>
            <thead><tr><th>Row</th><th>Change</th><th>Amount effect</th><th /></tr></thead>
            <tbody>
              {rev.diff.added.map((row) => (
                <tr key={`a${row.key}`}><td>{row.key}</td><td>added</td>
                  <td>{money(row.amount)}</td><td><Sig level={row.significance} /></td></tr>
              ))}
              {rev.diff.removed.map((row) => (
                <tr key={`r${row.key}`}><td>{row.key}</td><td>removed</td>
                  <td>{money(row.amount)}</td><td><Sig level={row.significance} /></td></tr>
              ))}
              {rev.diff.changed.map((row) => (
                <tr key={`c${row.key}`}><td>{row.key}</td>
                  <td>{(row.fields ?? []).map((f) =>
                    `${f.field}: ${String(f.before)} → ${String(f.after)}`).join("; ")}</td>
                  <td>{money(row.amount_change)}</td><td><Sig level={row.significance} /></td></tr>
              ))}
            </tbody>
          </table>
          {rev.diff.duplicate_keys.length > 0 && (
            <div className="error-bar">
              Duplicate keys in a version: {rev.diff.duplicate_keys.join(", ")}
            </div>
          )}
        </div>
      ))}

      <div className="panel">
        <h3>Runs built on the old file</h3>
        <table>
          <thead><tr><th>Procedure</th><th>Input that moved</th><th>Findings</th><th>Status</th><th>What to do</th></tr></thead>
          <tbody>
            {stale_runs.map((run) => (
              <tr key={run.run_id}>
                <td>{run.procedure_id}</td>
                <td>{run.changed_inputs.join(", ")}</td>
                <td>{run.findings_before} → {run.findings_after}</td>
                <td className={`status ${run.status}`}>{run.status}</td>
                <td>{run.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="panel">
        <h3>Findings whose standing moves</h3>
        {cards.length === 0 && <p className="note">Rerunning changes no finding.</p>}
        {cards.map((card) => (
          <div className="impact-card" key={`${card.procedure_id}${card.finding_uid}`}>
            <div className="impact-head">
              <span className={`pill ${card.change === "new_after_revision" ? "bad"
                : card.change === "resolved_by_revision" ? "ok" : "pending"}`}>
                {CHANGE_LABEL[card.change]}
              </span>
              <b>{card.procedure_id}</b> · {JSON.stringify(card.key)}
              <Sig level={card.significance} />
            </div>
            <div className="impact-body">
              <div>{money(card.amount_before)} → {money(card.amount_after)} · your judgment:{" "}
                <b>{card.disposition}</b>{card.concurred && " (concurred)"}</div>
              <div><b>{ACTION_LABEL[card.action]}.</b> {card.what_it_means}</div>
              {card.reason && <div className="note">{card.reason}</div>}
            </div>
          </div>
        ))}
        <p className="note">{data.limits}</p>
      </div>
    </>
  );
}
