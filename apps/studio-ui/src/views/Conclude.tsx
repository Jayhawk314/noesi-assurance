// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Conclusion: the SAD against materiality, and exactly what still stands
 *  between the file and the partner's lock. */

import { Bundle, money } from "../data";
import { MaterialityRuler } from "./MaterialityRuler";

const BLOCKER_TEXT: Record<string, string> = {
  MATERIALITY_NOT_SET: "materiality is not set",
  TEAM_ASSIGNMENTS_INCOMPLETE: "team roles are not all assigned",
  RISKS_UNASSESSED: "risks are not assessed",
  HIGH_RISKS_WITHOUT_RESPONSE: "high risks have no planned response",
  HIGH_RISKS_WITHOUT_PROCEDURE: "high risks have no procedure answering them",
  RISKS_AWAITING_CONCURRENCE: "risk assessments await a second person",
  CONTROLS_UNASSESSED: "controls are not assessed",
  CONTROL_RELIANCE_UNSUPPORTED: "control reliance is not supported by tests",
  SELECTED_PROCEDURES_BLOCKED: "selected procedures cannot run on this data",
  SELECTED_PROCEDURES_PARTIAL: "selected procedures wait on a policy",
  SELECTED_PROCEDURES_PENDING_RUN: "selected procedures have not been run",
  PROCEDURE_RUN_REVIEW_PENDING: "test runs still need review or approval",
  PROCEDURE_EXCLUSIONS_WITHOUT_RATIONALE: "excluded procedures lack a written reason",
  NO_DATA_WITHOUT_PARTNER_ASSERTION: "no data was tested and the partner has not said why",
  EVIDENCE_REVIEW_PENDING: "evidence items await review",
  EXTRACTION_APPROVAL_PENDING: "data extractions await approval",
  TRANSFORMATION_APPROVAL_PENDING: "data transformations await approval",
  MISSTATEMENTS_UNRESOLVED: "exceptions still need a judgment",
  SUBSTANTIVE_ITEMS_UNRESOLVED: "substantive items are unresolved",
  SCOPE_ITEMS_UNRESOLVED: "scope items are unresolved",
  DISPOSITIONS_AWAITING_CONCURRENCE: "judgments above trivial await a second person",
  WAIVERS_ABOVE_TRIVIAL_THRESHOLD: "items were waived that are too large to waive",
  COMPLETION_PROCEDURES_INCOMPLETE: "completion checks are not done",
  COMPLETION_EVIDENCE_MISSING: "completion checks lack a note",
  DECISION_TRAIL_BROKEN: "the decision journal does not verify",
};

const blockerText = (code: string) => BLOCKER_TEXT[code]
  ?? (code.endsWith("_NOT_COMPLETE")
    ? `the ${code.replace("_NOT_COMPLETE", "").toLowerCase()} stage is not marked complete`
    : code.toLowerCase().replace(/_/g, " "));

export function Conclude({ bundle }: { bundle: Bundle }) {
  const { sad, readiness } = bundle;
  return (
    <div className="grid">
      <section className="card wide">
        <h3>Summary of audit differences</h3>
        <MaterialityRuler sad={sad} />
        <div className="stats">
          <Stat label="Uncorrected" value={money(sad.total_unadjusted)} />
          <Stat label="Corrected by client" value={money(sad.total_adjusted)} />
          <Stat label="Still open" value={String(sad.open_count)} />
          <Stat label="Conclusion" value={sad.conclusion ?? "not yet"} tone={sad.conclusion === "material" ? "bad" : sad.conclusion ? "ok" : ""} />
        </div>
        {sad.unadjusted.length > 0 && (
          <table className="sad">
            <thead><tr><th>Uncorrected difference</th><th>Why</th><th className="num">Amount</th></tr></thead>
            <tbody>
              {sad.unadjusted.map((row) => (
                <tr key={row.finding_id}><td>{row.account}</td><td>{row.reason}</td><td className="num">{money(row.amount)}</td></tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card wide">
        <h3>{readiness.ready ? "Ready to lock" : "Before the partner can lock"}</h3>
        {readiness.ready ? (
          <p>Nothing blocks the lock. {readiness.report_implication}</p>
        ) : (
          <ul className="blockers">
            {readiness.blockers.map((b) => (
              <li key={b.code}>
                <b>{b.count}</b> {blockerText(b.code)}
                {b.items && b.items.length > 0 && <div className="muted small">{b.items.slice(0, 4).join(", ")}{b.items.length > 4 ? "…" : ""}</div>}
              </li>
            ))}
          </ul>
        )}
        <p className="muted">Completion checks: {readiness.completion_done} of {readiness.completion_total} done.
          Locking, the completion checklist and the evidence export live in the <a href="/">Workbench</a>.</p>
      </section>
    </div>
  );
}

function Stat({ label, value, tone = "" }: { label: string; value: string; tone?: string }) {
  return <div className={`stat ${tone}`}><div className="stat-v">{value}</div><div className="stat-l">{label}</div></div>;
}
