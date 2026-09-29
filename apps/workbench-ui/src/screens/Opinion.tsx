// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Draft Opinion: the opinion the engagement's evidence points to, with its
 *  basis and the decisions only the partner can make. Read-only: it never
 *  issues an opinion. */

import { useCallback } from "react";
import { Client, DraftOpinion } from "../api";
import { useResource } from "../lib/useResource";

const LABEL: Record<string, string> = {
  unmodified: "Unmodified (clean)",
  qualified_or_adverse: "Qualified or adverse",
  qualified_or_disclaimer: "Qualified or disclaimer",
  qualified_adverse_or_disclaimer: "Qualified, adverse or disclaimer",
  disclaimer: "Disclaimer of opinion",
};

const words = (name: string) => name.replace(/_/g, " ");

export function OpinionScreen({ client, eid }: {
  client: Client;
  eid: string;
  onError: (exc: unknown) => void;
}) {
  const load = useCallback(() => client.draftOpinion(eid), [client, eid]);
  const { data, error, reload } = useResource<DraftOpinion>(load);
  if (error) return <div className="error-bar">{error}</div>;
  if (!data) return <p className="note">Loading…</p>;
  const ready = data.status === "draft_for_partner";

  return (
    <>
      <div className="panel">
        <h3>
          Draft opinion: {LABEL[data.proposed_opinion] ?? words(data.proposed_opinion)}{" "}
          <button className="small" onClick={reload}>refresh</button>
        </h3>
        <p className={`status ${ready ? "ok" : "pending"}`}>
          {ready ? "Ready for the partner's review" : "Not ready: see below"}
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
          <ul>
            {data.decisions_required.map((d) => (
              <li key={d.decision}><b>{words(d.decision)}</b>: {d.why}</li>
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
