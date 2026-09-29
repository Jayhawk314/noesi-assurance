// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Draft Opinion: the opinion the engagement's evidence points to, its
 *  basis, and the judgments only the partner can make. The partner records
 *  each judgment here (with a reason, kept in the signed record); once all
 *  are recorded, the draft settles to one opinion. It never issues one. */

import { useCallback, useState } from "react";
import { Client, DraftOpinion } from "../api";
import { useResource } from "../lib/useResource";

const LABEL: Record<string, string> = {
  unmodified: "Unmodified (clean)",
  qualified: "Qualified",
  adverse: "Adverse",
  qualified_or_adverse: "Qualified or adverse",
  qualified_or_disclaimer: "Qualified or disclaimer",
  qualified_adverse_or_disclaimer: "Qualified, adverse or disclaimer",
  disclaimer: "Disclaimer of opinion",
};

const words = (name: string) => name.replace(/_/g, " ");

export function OpinionScreen({ client, eid, onError }: {
  client: Client;
  eid: string;
  onError: (exc: unknown) => void;
}) {
  const load = useCallback(() => client.draftOpinion(eid), [client, eid]);
  const { data, error, reload } = useResource<DraftOpinion>(load);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});
  if (error) return <div className="error-bar">{error}</div>;
  if (!data) return <p className="note">Loading…</p>;
  const ready = data.status === "draft_for_partner";
  const settled = data.opinion ?? data.proposed_opinion;

  function record(decision: string) {
    client.updateWorkflow(eid, "opinion_decision", {
      decision, answer: answers[decision], note: notes[decision] ?? "",
    }).then(reload).catch(onError);
  }

  return (
    <>
      <div className="panel">
        <h3>
          {data.opinion ? "Opinion" : "Draft opinion"}: {LABEL[settled] ?? words(settled)}
          {data.going_concern_section && " — with a going-concern section"}{" "}
          <button className="small" onClick={reload}>refresh</button>{" "}
          <button className="small" onClick={() => window.print()}>print</button>
        </h3>
        <p className={`status ${ready ? "ok" : "pending"}`}>
          {ready ? "Ready for the partner's sign-off" : "Not ready: see below"}
        </p>
        <p className="note">{data.note}</p>
      </div>

      <div className="panel">
        <h3>Basis</h3>
        <ul>{data.basis.map((b) => <li key={b}>{b}</li>)}</ul>
        <p className="note">
          Uncorrected misstatements: {data.misstatements.amount} on{" "}
          {words(data.misstatements.largest_line)} against materiality{" "}
          {data.materiality}. Source: {data.misstatements.source}.
        </p>
      </div>

      {data.decisions_required.length > 0 && (
        <div className="panel">
          <h3>Decisions the partner must record</h3>
          {data.decisions_required.map((d) => {
            const options = data.decision_answers[d.decision];
            return (
              <div key={d.decision} className="decision">
                <p><b>{words(d.decision)}</b>: {d.why}</p>
                {options ? (
                  <form className="inline" onSubmit={(e) => { e.preventDefault(); record(d.decision); }}>
                    <select value={answers[d.decision] ?? ""}
                            onChange={(e) => setAnswers({ ...answers, [d.decision]: e.target.value })}>
                      <option value="">choose…</option>
                      {options.map((o) => <option key={o} value={o}>{words(o)}</option>)}
                    </select>{" "}
                    <input value={notes[d.decision] ?? ""} placeholder="reason (kept in the signed record)"
                           onChange={(e) => setNotes({ ...notes, [d.decision]: e.target.value })} />{" "}
                    <button className="action" type="submit"
                            disabled={!answers[d.decision] || (notes[d.decision] ?? "").trim().length < 10}>
                      record decision
                    </button>
                  </form>
                ) : (
                  <p className="note">Resolved by correcting the evidence, not by a decision.</p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {Object.keys(data.recorded_decisions ?? {}).length > 0 && (
        <div className="panel">
          <h3>Decisions recorded</h3>
          <ul>
            {Object.entries(data.recorded_decisions).map(([k, v]) => (
              <li key={k}><b>{words(k)}</b>: {words(v.answer)} — {v.note}{" "}
                <span className="note">({v.decided_by})</span></li>
            ))}
          </ul>
        </div>
      )}

      {data.readiness_blockers.length > 0 && (
        <div className="panel">
          <h3>Still open before the engagement can close</h3>
          <ul>
            {data.readiness_blockers.map((b) => (
              <li key={b.code}><code>{b.code}</code>{b.count ? ` (${b.count})` : ""}</li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}
