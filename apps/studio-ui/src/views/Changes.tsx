// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** What changed: the replaced file, drawn as a cascade — file → tests →
 *  exceptions → your judgments — so the reach of one correction is visible
 *  at once. Read-only; every action happens through the normal steps. */

import { ImpactCard } from "../../../workbench-ui/src/api";
import { Bundle, money } from "../data";

const CHANGE: Record<ImpactCard["change"], [string, string]> = {
  new_after_revision: ["bad", "new exception"],
  resolved_by_revision: ["ok", "disappears"],
  amount_changed: ["warn", "amount moves"],
};
const ACTION: Record<ImpactCard["action"], string> = {
  dispose: "Judge it",
  revisit_disposition: "Revisit your judgment",
  reassess_disposition: "Reassess your judgment",
  none_after_rerun: "Clears when you rerun",
};

export function Changes({ bundle }: { bundle: Bundle }) {
  const impact = bundle.impact;
  if (!impact || !impact.revisions.length) {
    return (
      <div className="card">
        <h3>No replaced files</h3>
        <p className="muted">When the client sends a corrected file, load it in the Workbench
          (Sources &amp; Mappings). This view then shows every test, exception and judgment
          that rested on the old version — before you change anything.</p>
      </div>
    );
  }
  const cards = impact.cards;
  const judged = cards.filter((c) => c.action === "revisit_disposition" || c.action === "reassess_disposition");

  // Column layout for the cascade.
  const colX = [90, 330, 590, 850];
  const rowH = 46;
  const files = impact.revisions;
  const runs = impact.stale_runs;
  const height = Math.max(files.length, runs.length, cards.length, judged.length, 1) * rowH + 60;
  const y = (i: number, n: number) => 50 + i * rowH + ((Math.max(files.length, runs.length, cards.length, judged.length, 1) - n) * rowH) / 2;

  return (
    <div className="grid">
      <section className="card wide">
        <h3>How far one corrected file reaches</h3>
        <p className="muted">Nothing below has changed yet. Rerun the tests to bring them up to date, then revisit each judgment.</p>
        <svg viewBox={`0 0 1000 ${height}`} className="cascade" role="img" aria-label="Revision cascade">
          {["Replaced file", "Tests built on it", "Exceptions that move", "Your judgments"].map((t, i) => (
            <text key={t} x={colX[i]} y={22} textAnchor="middle" className="col-title">{t}</text>
          ))}
          {runs.map((run, ri) => files.filter((f) => run.changed_inputs.includes(f.role)).map((f) => {
            const fi = files.indexOf(f);
            return <path key={`${f.role}${run.run_id}`} className="flow"
                         d={curve(colX[0] + 80, y(fi, files.length), colX[1] - 90, y(ri, runs.length))} />;
          }))}
          {cards.map((card, ci) => {
            const ri = runs.findIndex((r) => r.procedure_id === card.procedure_id);
            return ri < 0 ? null : <path key={`r${ci}`} className={`flow ${CHANGE[card.change][0]}`}
                                         d={curve(colX[1] + 90, y(ri, runs.length), colX[2] - 110, y(ci, cards.length))} />;
          })}
          {judged.map((card, ji) => {
            const ci = cards.indexOf(card);
            return <path key={`j${ji}`} className="flow bad"
                         d={curve(colX[2] + 110, y(ci, cards.length), colX[3] - 90, y(ji, judged.length))} />;
          })}
          {files.map((f, i) => (
            <Box key={f.role} x={colX[0]} y={y(i, files.length)} w={160} cls="file"
                 title={f.role} sub={`${f.diff.added.length} added · ${f.diff.changed.length} changed · ${f.diff.removed.length} removed`} />
          ))}
          {runs.map((r, i) => (
            <Box key={r.run_id} x={colX[1]} y={y(i, runs.length)} w={180} cls={`run ${r.status}`}
                 title={r.procedure_id.replace(/^[a-z]+\./, "")} sub={`${r.findings_before} → ${r.findings_after} exceptions`} />
          ))}
          {cards.map((c, i) => (
            <Box key={`c${i}`} x={colX[2]} y={y(i, cards.length)} w={220} cls={`chg ${CHANGE[c.change][0]}`}
                 title={`${keyText(c)}`} sub={`${CHANGE[c.change][1]} · ${money(c.amount_change)}`} />
          ))}
          {judged.map((c, i) => (
            <Box key={`j${i}`} x={colX[3]} y={y(i, judged.length)} w={180} cls="judg"
                 title={`${c.disposition}${c.concurred ? " (concurred)" : ""}`} sub={ACTION[c.action]} />
          ))}
        </svg>
      </section>

      {files.map((f) => (
        <section className="card" key={f.role}>
          <h3>{f.role}: {f.before.file} → {f.after.file}</h3>
          <p className="muted">{f.diff.rows_before} → {f.diff.rows_after} rows · net {money(f.diff.net_amount_change)}</p>
          <ul className="diff">
            {f.diff.added.map((r) => <li key={`a${r.key}`} className="add">+ {r.key} <b>{money(r.amount)}</b> <Sig s={r.significance} /></li>)}
            {f.diff.removed.map((r) => <li key={`r${r.key}`} className="del">− {r.key} <b>{money(r.amount)}</b> <Sig s={r.significance} /></li>)}
            {f.diff.changed.map((r) => (
              <li key={`c${r.key}`} className="mod">~ {r.key}: {(r.fields ?? []).map((x) => `${x.field} ${String(x.before)} → ${String(x.after)}`).join("; ")}
                {" "}<b>{money(r.amount_change)}</b> <Sig s={r.significance} /></li>
            ))}
          </ul>
          <p className="muted">The tests only see what they test. A new row can matter even when no exception moves — look at every addition yourself.</p>
        </section>
      ))}

      <section className="card">
        <h3>What to do, exception by exception</h3>
        {cards.map((c, i) => (
          <div key={i} className={`todo ${CHANGE[c.change][0]}`}>
            <b>{ACTION[c.action]}</b> — {keyText(c)} ({c.procedure_id})
            <div className="muted">{c.what_it_means}</div>
          </div>
        ))}
        <p className="muted small">{impact.limits}</p>
      </section>
    </div>
  );
}

function Sig({ s }: { s: string }) {
  const label: Record<string, string> = {
    none: "no effect", below_trivial: "below trivial",
    above_trivial: "above trivial", above_performance: "above performance",
  };
  return <span className={`badge ${s}`}>{label[s] ?? s}</span>;
}

function Box({ x, y, w, title, sub, cls }: { x: number; y: number; w: number; title: string; sub: string; cls: string }) {
  return (
    <g className={`box ${cls}`}>
      <rect x={x - w / 2} y={y - 18} width={w} height={36} rx={8} />
      <text x={x} y={y - 2} textAnchor="middle" className="box-title">{title}</text>
      <text x={x} y={y + 12} textAnchor="middle" className="box-sub">{sub}</text>
    </g>
  );
}

const curve = (x1: number, y1: number, x2: number, y2: number) =>
  `M${x1},${y1} C${(x1 + x2) / 2},${y1} ${(x1 + x2) / 2},${y2} ${x2},${y2}`;

const keyText = (c: ImpactCard) =>
  Array.isArray(c.key) ? c.key.slice(1).map(String).join(" · ") : String(c.key);
