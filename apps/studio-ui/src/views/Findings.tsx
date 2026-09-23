// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Exceptions: one card per finding, judged in plain words.
 *  The five dispositions are the server's; the studio only explains them.
 *  Above clearly trivial a judgment is a proposal until someone else concurs,
 *  and the server refuses a proposer concurring with themselves. */

import { useState } from "react";
import { Client, Finding } from "../../../workbench-ui/src/api";
import { Bundle, currentFindings, money } from "../data";

const CHOICES: { status: string; label: string; help: string }[] = [
  { status: "cleared", label: "Explained — no misstatement", help: "You investigated and it is fine. Say why." },
  { status: "unadjusted", label: "Real difference, not corrected", help: "Goes on the SAD against materiality." },
  { status: "adjusted", label: "Real difference, client corrected it", help: "Recorded, but no longer uncorrected." },
  { status: "waived", label: "Too small to matter", help: "Below clearly trivial and not qualitatively significant." },
  { status: "follow_up", label: "Still open", help: "Blocks completion until resolved." },
];

type Filter = "todo" | "concur" | "all";

export function Findings({ bundle, client, actingRoles, perform, busy }: {
  bundle: Bundle; client: Client; actingRoles: string[]; busy: string;
  perform: (label: string, work: () => Promise<unknown>) => Promise<void>;
}) {
  const all = currentFindings(bundle);
  const todo = all.filter((f) => f.disposition.status === "undisposed");
  const concur = all.filter((f) => f.awaiting_concurrence);
  const [filter, setFilter] = useState<Filter>(todo.length ? "todo" : concur.length ? "concur" : "all");
  const shown = filter === "todo" ? todo : filter === "concur" ? concur : all;
  const canJudge = actingRoles.length > 0;
  const canConcur = actingRoles.some((r) => r === "reviewer" || r === "partner");

  return (
    <div>
      <div className="filters">
        <button className={filter === "todo" ? "on" : ""} onClick={() => setFilter("todo")}>
          Need a judgment <span className="count">{todo.length}</span></button>
        <button className={filter === "concur" ? "on" : ""} onClick={() => setFilter("concur")}>
          Awaiting concurrence <span className="count">{concur.length}</span></button>
        <button className={filter === "all" ? "on" : ""} onClick={() => setFilter("all")}>
          All <span className="count">{all.length}</span></button>
        <span className="muted">Clearly trivial: {money(bundle.sad.clearly_trivial)} — judgments above it need a second person.</span>
      </div>
      {!shown.length && <p className="muted empty">Nothing here.</p>}
      <div className="finding-list">
        {shown.map((f) => (
          <FindingCard key={`${f.run_id}${f.finding_uid}`} finding={f} canJudge={canJudge}
                       canConcur={canConcur} busy={busy}
                       onSave={(status, note) => perform("judge", () => client.setDisposition(
                         bundle.engagement.engagement_id, f.finding_uid, status, note, f.disposition.version))}
                       onConcur={() => perform("concur", () => client.concurDisposition(
                         bundle.engagement.engagement_id, f.finding_uid, f.disposition.version))} />
        ))}
      </div>
    </div>
  );
}

function FindingCard({ finding, canJudge, canConcur, busy, onSave, onConcur }: {
  finding: Finding; canJudge: boolean; canConcur: boolean; busy: string;
  onSave: (status: string, note: string) => void; onConcur: () => void;
}) {
  const v = finding.verdict;
  const [status, setStatus] = useState(finding.disposition.status === "undisposed" ? "" : finding.disposition.status);
  const [note, setNote] = useState(finding.disposition.note);
  const changed = status !== finding.disposition.status || note !== finding.disposition.note;
  const current = CHOICES.find((c) => c.status === finding.disposition.status);
  return (
    <article className={`finding ${finding.disposition.status}`}>
      <header>
        <span className="amount">{v.score !== null ? money(v.score) : "no amount"}</span>
        <span className="what">{finding.tags.assertion || finding.procedure_id}</span>
        <span className="key">{Array.isArray(v.key) ? v.key.slice(1).join(" · ") : String(v.key)}</span>
        {finding.requires_concurrence && <span className="badge warn">above trivial</span>}
      </header>
      <p className="reason">{v.reason}</p>
      <div className="judged">
        {current
          ? <>Judged: <b>{current.label}</b>{finding.disposition.proposed_by && <> by {finding.disposition.proposed_by}</>}
              {finding.disposition.concurred_by && <> · concurred by {finding.disposition.concurred_by}</>}</>
          : <span className="muted">Not judged yet</span>}
      </div>
      {canJudge && (
        <div className="judge">
          <div className="choices" role="radiogroup" aria-label="Disposition">
            {CHOICES.map((c) => (
              <label key={c.status} className={status === c.status ? "on" : ""} title={c.help}>
                <input type="radio" name={`d-${finding.run_id}-${finding.finding_uid}`} value={c.status}
                       checked={status === c.status} onChange={() => setStatus(c.status)} />
                {c.label}
              </label>
            ))}
          </div>
          <textarea placeholder="Why? (this note goes in the workpaper)" value={note}
                    onChange={(e) => setNote(e.target.value)} rows={2} />
          <div className="row">
            <button className="primary" disabled={!status || !note.trim() || !changed || !!busy}
                    onClick={() => onSave(status, note.trim())}>Save judgment</button>
            {finding.awaiting_concurrence && canConcur && (
              <button className="secondary" disabled={!!busy} onClick={onConcur}>Concur</button>
            )}
            {status && <span className="muted">{CHOICES.find((c) => c.status === status)?.help}</span>}
          </div>
        </div>
      )}
    </article>
  );
}
