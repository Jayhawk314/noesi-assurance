// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
import { useCallback, useMemo, useState } from "react";
import { Client, CoverageRow } from "../api";
import {
  CYCLE_MAPS, CycleMap, MapEdge, MapNode, NODE_H, NODE_W, mappedProcedureIds,
} from "../lib/cycleMap";
import { useResource } from "../lib/useResource";
import "../ui/flowmap.css";

// "empty": normalized, but every row was quarantined — the data is not in.
type RoleState = "supplied" | "empty" | "mapped" | "missing";
type ProcState = "executable" | "partial" | "blocked" | "unsupported";

interface Props {
  client: Client;
  eid: string;
  onError: (exc: unknown) => void;
  /** Send the user to the tab that fixes what they just clicked. */
  onGoToSources: () => void;
}

/** Worst status wins: one blocked procedure makes the whole link blocked. */
const RANK: Record<ProcState, number> = {
  executable: 0, partial: 1, blocked: 2, unsupported: 3,
};

export function FlowMapScreen({ client, eid, onError, onGoToSources }: Props) {
  const load = useCallback(async () => {
    const [coverage, sources] = await Promise.all([
      client.coverage(eid), client.sources(eid),
    ]);
    return { coverage, sources };
  }, [client, eid]);
  const { data, loading, error, reload } = useResource(load);
  const [selected, setSelected] = useState<
    { kind: "node"; node: MapNode } | { kind: "edge"; edge: MapEdge } | null
  >(null);
  const [running, setRunning] = useState("");

  const byId = useMemo(() => {
    const index = new Map<string, CoverageRow>();
    for (const row of data?.coverage.procedures ?? []) {
      index.set(row.procedure_id, row);
    }
    return index;
  }, [data]);

  const roleState = useCallback((role: string): RoleState => {
    const sources = data?.sources;
    if (!sources) return "missing";
    const sets = sources.datasets.filter((set) => set.role === role);
    if (sets.some((set) => set.rows_loaded > 0)) return "supplied";
    if (sets.length) return "empty";
    if (sources.mapping_specs.some((spec) => spec.role === role)) return "mapped";
    return "missing";
  }, [data]);

  const rowsFor = useCallback((role: string) => {
    const set = data?.sources.datasets.find((entry) => entry.role === role);
    return set ? set.rows_loaded : null;
  }, [data]);

  const linkState = useCallback((ids: string[]): ProcState | null => {
    const states = ids
      .map((id) => byId.get(id)?.status)
      .filter((value): value is ProcState => value !== undefined);
    if (states.length === 0) return null;
    return states.reduce((worst, next) =>
      RANK[next] > RANK[worst] ? next : worst);
  }, [byId]);

  async function run(procedureId: string) {
    setRunning(procedureId);
    try {
      await client.runProcedure(eid, procedureId, {});
      reload();
    } catch (exc) {
      onError(exc);
    } finally {
      setRunning("");
    }
  }

  if (loading && !data) return <p className="note">Compiling the map…</p>;
  if (error) return <div className="error-bar">{error}</div>;
  if (!data) return null;

  const map = CYCLE_MAPS[0];
  const summary = data.coverage.summary;
  const supplied = map.nodes.filter((n) => roleState(n.role) === "supplied");

  const known = mappedProcedureIds();
  const unmapped = data.coverage.procedures
    .filter((row) => !known.has(row.procedure_id));

  return (
    <>
      <div className="fm-detail-head">
        <h2 style={{ margin: 0 }}>{map.title}</h2>
        <span className="pill idle">
          {supplied.length} of {map.nodes.length} record sets supplied
        </span>
        {summary.executable > 0 && (
          <span className="pill ok">{summary.executable} executable</span>
        )}
        {summary.partial > 0 && (
          <span className="pill pending">{summary.partial} partial</span>
        )}
        {summary.blocked > 0 && (
          <span className="pill bad">{summary.blocked} blocked</span>
        )}
        {summary.unsupported > 0 && (
          <span className="pill bad">{summary.unsupported} unsupported</span>
        )}
      </div>
      <p className="note" style={{ marginBottom: "0.7rem" }}>{map.caption}</p>

      <div className="fm-wrap">
        <Diagram
          map={map}
          roleState={roleState}
          rowsFor={rowsFor}
          linkState={linkState}
          selected={selected}
          onSelect={setSelected}
        />
      </div>

      <div className="fm-legend">
        <span><i className="fm-key supplied" /> data loaded</span>
        <span><i className="fm-key mapped" /> mapped, not yet normalized</span>
        <span><i className="fm-key missing" /> not supplied</span>
        <span><i className="fm-key executable" /> procedure can run</span>
        <span><i className="fm-key partial" /> partial — fields missing</span>
        <span><i className="fm-key blocked" /> blocked — data missing</span>
      </div>

      <div className="fm-detail panel">
        {!selected ? (
          <p className="fm-hint">
            Select a box to see what that data unlocks, or an arrow to see the
            procedures that test the link.
          </p>
        ) : selected.kind === "node" ? (
          <NodeDetail
            node={selected.node}
            state={roleState(selected.node.role)}
            rows={rowsFor(selected.node.role)}
            procedures={(selected.node.procedures ?? [])
              .map((id) => byId.get(id))
              .filter((row): row is CoverageRow => row !== undefined)}
            running={running}
            onRun={run}
            onGoToSources={onGoToSources}
          />
        ) : (
          <EdgeDetail
            edge={selected.edge}
            procedures={selected.edge.procedures
              .map((id) => byId.get(id))
              .filter((row): row is CoverageRow => row !== undefined)}
            running={running}
            onRun={run}
          />
        )}
      </div>

      {unmapped.length > 0 && (
        <>
          <h3>Not on the map</h3>
          <p className="note">
            These procedures are not drawn above — add them to the cycle map
            to place them.
          </p>
          <div className="table-wrap">
            <table className="dense">
              <thead>
                <tr><th>Procedure</th><th>Cycle</th><th>Status</th></tr>
              </thead>
              <tbody>
                {unmapped.map((row) => (
                  <tr key={row.procedure_id}>
                    <td>{row.name}</td>
                    <td>{row.cycle}</td>
                    <td>
                      <span className={`status ${row.status}`}>{row.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}

// ------------------------------------------------------------------ diagram

interface DiagramProps {
  map: CycleMap;
  roleState: (role: string) => RoleState;
  rowsFor: (role: string) => number | null;
  linkState: (ids: string[]) => ProcState | null;
  selected: { kind: "node"; node: MapNode } | { kind: "edge"; edge: MapEdge } | null;
  onSelect: (
    value: { kind: "node"; node: MapNode } | { kind: "edge"; edge: MapEdge },
  ) => void;
}

function Diagram(
  { map, roleState, rowsFor, linkState, selected, onSelect }: DiagramProps,
) {
  const arrowFor = (state: ProcState | null) =>
    `url(#fm-arrow-${state ?? "structural"})`;

  return (
    <svg className="fm-svg" viewBox={`0 0 ${map.width} ${map.height}`}
         role="img"
         aria-label={`${map.title} coverage map`}>
      <defs>
        {(["structural", "executable", "partial", "blocked",
           "unsupported"] as const).map(
          (kind) => (
            <marker key={kind} id={`fm-arrow-${kind}`} viewBox="0 0 10 10"
                    refX="9" refY="5" markerWidth="6" markerHeight="6"
                    orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" className={`fm-head ${kind}`} />
            </marker>
          ))}
      </defs>

      {map.edges.map((edge) => {
        const state = linkState(edge.procedures);
        const kind = state ?? "structural";
        const d = edge.points
          .map(([x, y], index) => `${index === 0 ? "M" : "L"} ${x} ${y}`)
          .join(" ");
        const count = edge.procedures.length;
        return (
          <g key={edge.id} className={`fm-edge ${kind}`}
             onClick={() => count && onSelect({ kind: "edge", edge })}>
            <path className="fm-line" d={d} markerEnd={arrowFor(state)} />
            <path className="fm-hit" d={d} />
            {count > 0 && (
              <>
                <rect className="fm-chip-box"
                      x={edge.labelAt[0] - 14} y={edge.labelAt[1] - 9}
                      width="28" height="18" />
                <text className="fm-chip-text"
                      x={edge.labelAt[0]} y={edge.labelAt[1]}>
                  {count}
                </text>
              </>
            )}
          </g>
        );
      })}

      {map.nodes.map((node) => {
        const state = roleState(node.role);
        const rows = rowsFor(node.role);
        const isSelected = selected?.kind === "node"
          && selected.node.role === node.role;
        return (
          <g key={node.role}
             className={`fm-node ${state}${isSelected ? " selected" : ""}`}
             transform={`translate(${node.x},${node.y})`}
             tabIndex={0} role="button"
             aria-label={`${node.label}: ${state}`}
             onClick={() => onSelect({ kind: "node", node })}
             onKeyDown={(event) => {
               if (event.key === "Enter" || event.key === " ") {
                 event.preventDefault();
                 onSelect({ kind: "node", node });
               }
             }}>
            <rect className="fm-box" width={NODE_W} height={NODE_H} rx="8" />
            <text className="fm-label" x="13" y="26">{node.label}</text>
            <text className="fm-sub" x="13" y="45">
              {state === "supplied"
                ? `${(rows ?? 0).toLocaleString()} rows`
                : state === "empty" ? "0 rows — all set aside"
                : state === "mapped" ? "mapped, not normalized" : "not supplied"}
            </text>
            <circle className="fm-dot" cx={NODE_W - 16} cy="20" />
          </g>
        );
      })}
    </svg>
  );
}

// ------------------------------------------------------------------ details

function ProcedureRow(
  { row, running, onRun }:
  { row: CoverageRow; running: string; onRun: (id: string) => void },
) {
  const gaps = [
    ...(row.unsupported_reason ? [row.unsupported_reason] : []),
    ...row.missing_roles.map((role) => `needs ${role}`),
    ...Object.entries(row.missing_fields).map(
      ([role, fields]) => `${role} is missing ${fields.join(", ")}`),
    ...row.missing_policies.map((policy) => `needs policy ${policy}`),
  ];
  return (
    <div className="fm-proc">
      <div className="fm-proc-head">
        <span className={`pill ${row.status === "executable" ? "ok"
          : row.status === "partial" ? "pending" : "bad"}`}>
          {row.status}
        </span>
        <b>{row.name}</b>
        <span className="spacer" />
        {row.population !== null && (
          <span className="note num">{row.population.toLocaleString()} items</span>
        )}
        {row.status === "executable" && (
          <button className="action primary" disabled={running === row.procedure_id}
                  onClick={() => onRun(row.procedure_id)}>
            {running === row.procedure_id ? "running…" : "run"}
          </button>
        )}
      </div>
      <p className="note" style={{ margin: "0.25rem 0 0" }}>{row.objective}</p>
      {gaps.length > 0 && <p className="fm-gap">Blocked by: {gaps.join("; ")}</p>}
      {row.limitations && <p className="note">{row.limitations}</p>}
    </div>
  );
}

function NodeDetail(
  { node, state, rows, procedures, running, onRun, onGoToSources }: {
    node: MapNode;
    state: RoleState;
    rows: number | null;
    procedures: CoverageRow[];
    running: string;
    onRun: (id: string) => void;
    onGoToSources: () => void;
  },
) {
  return (
    <>
      <div className="fm-detail-head">
        <h3>{node.label}</h3>
        <span className={`pill ${state === "supplied" ? "ok"
          : state === "empty" ? "bad" : state === "mapped" ? "pending" : "idle"}`}>
          {state === "supplied" ? `${(rows ?? 0).toLocaleString()} rows loaded`
            : state === "empty" ? "every row was set aside"
            : state === "mapped" ? "mapped, not normalized" : "not supplied"}
        </span>
        {state !== "supplied" && (
          <button className="action primary" onClick={onGoToSources}>
            {state === "empty" ? "see why in Sources"
              : state === "mapped" ? "finish in Sources" : "upload this data"}
          </button>
        )}
      </div>
      {procedures.length > 0 ? (
        <>
          <p className="note">Procedures that test this data on its own:</p>
          {procedures.map((row) => (
            <ProcedureRow key={row.procedure_id} row={row}
                          running={running} onRun={onRun} />
          ))}
        </>
      ) : (
        <p className="fm-hint">
          No procedure tests this data alone — it is evidence for the links
          drawn from it.
        </p>
      )}
    </>
  );
}

function EdgeDetail(
  { edge, procedures, running, onRun }: {
    edge: MapEdge;
    procedures: CoverageRow[];
    running: string;
    onRun: (id: string) => void;
  },
) {
  const pretty = (role: string) => role.replace(/_/g, " ").toLowerCase();
  return (
    <>
      <div className="fm-detail-head">
        <h3>{pretty(edge.from)} → {pretty(edge.to)}</h3>
        <span className="pill idle">
          {procedures.length} procedure{procedures.length === 1 ? "" : "s"}
        </span>
      </div>
      {procedures.map((row) => (
        <ProcedureRow key={row.procedure_id} row={row}
                      running={running} onRun={onRun} />
      ))}
    </>
  );
}
