// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Overview: the purchase-to-pay cycle as a picture, the exceptions by test,
 *  and the uncorrected total against materiality. */

import { Bundle, ViewId, currentFindings, latestRuns, money } from "../data";
import { MaterialityRuler } from "./MaterialityRuler";

type Anchor = { edge: [string, string] } | { node: string };

/** Where each procedure's result is drawn on the cycle. */
const ANCHORS: Record<string, { label: string; at: Anchor }> = {
  "ap.voucher_po_reference": { label: "PO exists", at: { edge: ["Purchase_orders", "Vouchers"] } },
  "ap.three_way_receipt_match": { label: "3-way match", at: { edge: ["Goods_receipts", "Vouchers"] } },
  "ap.payment_voucher_reference": { label: "Voucher exists", at: { edge: ["Vouchers", "Payments"] } },
  "ap.document_chain": { label: "Chain coheres", at: { node: "Vouchers" } },
  "cash.bank_clearing": { label: "Cleared bank", at: { edge: ["Payments", "Bank"] } },
  "gl.payment_posting": { label: "Posted to GL", at: { edge: ["Payments", "GL"] } },
  "ap.subledger_gl_balance_tie": { label: "Subledger ties", at: { edge: ["GL", "AP_control_balance"] } },
  "ap.vendor_relational_twins": { label: "Twin vendors", at: { node: "Vendors" } },
  "ap.segregation_of_duties": { label: "Two people", at: { edge: ["Employees", "Payments"] } },
  "ap.split_payment_review": { label: "Split payments", at: { node: "Payments" } },
  "forensic.closed_value_flow": { label: "Round trips", at: { node: "Value_flows" } },
};

const NODES: Record<string, { x: number; y: number; label: string }> = {
  Vendors: { x: 70, y: 70, label: "Vendors" },
  Purchase_orders: { x: 230, y: 70, label: "Purchase orders" },
  Goods_receipts: { x: 390, y: 200, label: "Goods received" },
  Vouchers: { x: 390, y: 70, label: "Invoices (vouchers)" },
  Payments: { x: 580, y: 70, label: "Payments" },
  Bank: { x: 770, y: 70, label: "Bank" },
  GL: { x: 770, y: 200, label: "General ledger" },
  AP_control_balance: { x: 930, y: 200, label: "AP control" },
  Employees: { x: 580, y: 200, label: "Employees" },
  Value_flows: { x: 70, y: 200, label: "Value flows" },
};

const CHAIN: [string, string][] = [
  ["Vendors", "Purchase_orders"], ["Purchase_orders", "Vouchers"],
  ["Goods_receipts", "Vouchers"], ["Vouchers", "Payments"],
  ["Payments", "Bank"], ["Payments", "GL"], ["GL", "AP_control_balance"],
  ["Employees", "Payments"],
];

export function Overview({ bundle, onView }: { bundle: Bundle; onView: (v: ViewId) => void }) {
  const rows = new Map<string, number>();
  const versions = new Map<string, number>();
  for (const d of bundle.sources.datasets) {
    rows.set(d.role, d.rows_loaded);
    versions.set(d.role, (versions.get(d.role) ?? 0) + 1);
  }
  const latest = latestRuns(bundle.runs);
  const stale = new Set((bundle.impact?.stale_runs ?? []).map((r) => r.procedure_id));
  const findings = currentFindings(bundle);
  const byProc = new Map<string, number>();
  for (const f of findings) byProc.set(f.procedure_id, (byProc.get(f.procedure_id) ?? 0) + 1);
  const coverage = new Map(bundle.coverage.procedures.map((p) => [p.procedure_id, p]));

  const testState = (pid: string) => {
    const run = latest.get(pid);
    if (stale.has(pid)) return "stale";
    if (!run) return coverage.get(pid)?.status === "executable" ? "ready" : "blocked";
    if (run.status === "error") return "error";
    return (byProc.get(pid) ?? 0) > 0 ? "exceptions" : "clean";
  };

  const chips = Object.entries(ANCHORS).map(([pid, { label, at }]) => {
    let x: number, y: number;
    if ("edge" in at) {
      const a = NODES[at.edge[0]], b = NODES[at.edge[1]];
      x = (a.x + b.x) / 2; y = (a.y + b.y) / 2;
    } else {
      x = NODES[at.node].x; y = NODES[at.node].y - 46;
    }
    return { pid, label, x, y, above: !("edge" in at), state: testState(pid),
             count: byProc.get(pid) ?? 0 };
  });

  return (
    <div className="grid">
      {bundle.impact && bundle.impact.summary.revised_files > 0 && (
        <button className="alert warn wide" onClick={() => onView("changes")}>
          <b>The client replaced {bundle.impact.revisions.map((r) => r.role).join(", ")}.</b>{" "}
          {bundle.impact.summary.stale_runs} test(s) and {bundle.impact.summary.judgments_to_revisit} of
          your judgment(s) rest on the old version — see what changed →
        </button>
      )}

      <section className="card wide">
        <h3>The purchase-to-pay cycle</h3>
        <p className="muted">Boxes are the client's records (rows loaded). Circles are the tests on each link:
          green clean, amber exceptions found, grey not run yet, striped built on a replaced file.</p>
        <svg viewBox="0 -10 1000 270" className="cycle" role="img"
             aria-label="Purchase-to-pay cycle with test results">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0,0 L10,5 L0,10 z" className="arrowhead" />
            </marker>
            <pattern id="stripes" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <rect width="3" height="6" className="stripe" />
            </pattern>
          </defs>
          {CHAIN.map(([from, to]) => {
            const a = NODES[from], b = NODES[to];
            return <line key={`${from}${to}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                         className="link" markerEnd="url(#arrow)" />;
          })}
          {Object.entries(NODES).map(([role, n]) => {
            const loaded = rows.has(role);
            return (
              <g key={role} className={`node ${loaded ? "loaded" : "missing"}`}>
                <rect x={n.x - 66} y={n.y - 22} width={132} height={44} rx={10} />
                <text x={n.x} y={n.y - 3} textAnchor="middle" className="node-label">{n.label}</text>
                <text x={n.x} y={n.y + 13} textAnchor="middle" className="node-sub">
                  {loaded ? `${rows.get(role)} rows` : "not loaded"}
                  {(versions.get(role) ?? 0) > 1 ? " · revised" : ""}
                </text>
              </g>
            );
          })}
          {chips.map((c) => (
            <g key={c.pid} className={`chip ${c.state}`}>
              <title>{`${c.label}: ${c.state}${c.count ? `, ${c.count} exception(s)` : ""}`}</title>
              <circle cx={c.x} cy={c.y} r={13} />
              {c.state === "stale" && <circle cx={c.x} cy={c.y} r={13} fill="url(#stripes)" />}
              <text x={c.x} y={c.y + 4} textAnchor="middle" className="chip-count">
                {c.state === "clean" ? "✓" : c.state === "exceptions" ? c.count : c.state === "error" ? "!" : "·"}
              </text>
              <text x={c.x} y={c.above ? c.y - 18 : c.y + 27} textAnchor="middle"
                    className="chip-label">{c.label}</text>
            </g>
          ))}
        </svg>
      </section>

      <section className="card">
        <h3>Exceptions by test</h3>
        <ExceptionBars bundle={bundle} />
        <button className="link" onClick={() => onView("findings")}>Judge them →</button>
      </section>

      <section className="card">
        <h3>Uncorrected total vs materiality</h3>
        <MaterialityRuler sad={bundle.sad} />
        <p className="muted">
          Uncorrected differences so far: <b>{money(bundle.sad.total_unadjusted)}</b>
          {bundle.sad.conclusion && <> — currently <b>{bundle.sad.conclusion}</b></>}.
          Only exceptions you judge <i>unadjusted</i> count here.
        </p>
      </section>
    </div>
  );
}

const DISPOSITION_ORDER = ["undisposed", "follow_up", "unadjusted", "adjusted", "waived", "cleared"];

function ExceptionBars({ bundle }: { bundle: Bundle }) {
  const findings = currentFindings(bundle);
  if (!findings.length) return <p className="muted">No exceptions yet — run the tests first.</p>;
  const groups = new Map<string, Map<string, number>>();
  for (const f of findings) {
    const g = groups.get(f.procedure_id) ?? new Map<string, number>();
    g.set(f.disposition.status, (g.get(f.disposition.status) ?? 0) + 1);
    groups.set(f.procedure_id, g);
  }
  const max = Math.max(...[...groups.values()].map((g) => [...g.values()].reduce((a, b) => a + b, 0)));
  return (
    <div className="bars">
      {[...groups.entries()].sort((a, b) => sum(b[1]) - sum(a[1])).map(([pid, g]) => (
        <div className="bar-row" key={pid}>
          <span className="bar-label">{ANCHORS[pid]?.label ?? pid}</span>
          <span className="bar-track">
            {DISPOSITION_ORDER.filter((s) => g.has(s)).map((s) => (
              <span key={s} className={`seg ${s}`} style={{ width: `${(100 * (g.get(s) ?? 0)) / max}%` }}
                    title={`${g.get(s)} ${s.replace("_", " ")}`} />
            ))}
          </span>
          <span className="bar-n">{sum(g)}</span>
        </div>
      ))}
      <div className="legend">
        {DISPOSITION_ORDER.map((s) => <span key={s}><i className={`seg ${s}`} />{s.replace("_", " ")}</span>)}
      </div>
    </div>
  );
}

const sum = (g: Map<string, number>) => [...g.values()].reduce((a, b) => a + b, 0);
