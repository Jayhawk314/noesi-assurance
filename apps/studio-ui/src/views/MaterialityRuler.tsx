// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** A ruler from zero to overall materiality with the two derived lines
 *  marked, and the uncorrected total drawn against it. */

import { Sad } from "../../../workbench-ui/src/api";
import { money } from "../data";

export function MaterialityRuler({ sad }: { sad: Sad }) {
  const overall = sad.overall_materiality;
  if (!overall) return <p className="muted">Set materiality to see the ruler.</p>;
  const total = Math.abs(sad.total_unadjusted);
  const scale = Math.max(overall, total) * 1.08;
  const pos = (v: number) => `${(100 * v) / scale}%`;
  const level = total > overall ? "bad" : total > (sad.performance_materiality ?? overall)
    ? "warn" : total > sad.clearly_trivial ? "mid" : "ok";
  return (
    <div className="ruler" role="img"
         aria-label={`Uncorrected ${money(total)} against materiality ${money(overall)}`}>
      <div className="ruler-track">
        <div className={`ruler-fill ${level}`} style={{ width: pos(total) }} />
        <Mark at={pos(sad.clearly_trivial)} label="clearly trivial" value={sad.clearly_trivial} />
        {sad.performance_materiality !== null && (
          <Mark at={pos(sad.performance_materiality)} label="performance" value={sad.performance_materiality} />
        )}
        <Mark at={pos(overall)} label="materiality" value={overall} strong />
      </div>
    </div>
  );
}

function Mark({ at, label, value, strong }: { at: string; label: string; value: number; strong?: boolean }) {
  return (
    <div className={`mark ${strong ? "strong" : ""}`} style={{ left: at }}>
      <span className="mark-label">{label}<br /><b>{money(value)}</b></span>
    </div>
  );
}
