// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Noesi Studio — the visual practitioner view.
 *
 *  The Workbench (at /) is the full-control instrument and the teaching
 *  surface. The Studio answers three questions at a glance: where is this
 *  engagement, what is the next step, and who has to take it. It reads the
 *  same server records, sends the same journaled commands, and is refused by
 *  the same separation-of-duties gates — it only arranges them visually. */

import { useCallback, useEffect, useState } from "react";
import { Client, Engagement, TeamMember } from "../../workbench-ui/src/api";
import { Bundle, NextStep, Stage, ViewId, journey, loadBundle } from "./data";
import { Overview } from "./views/Overview";
import { Findings } from "./views/Findings";
import { Changes } from "./views/Changes";
import { Conclude } from "./views/Conclude";

const CHAIR_HELP: Record<string, string> = {
  partner: "Partner — sets materiality, approves, signs off",
  preparer: "Preparer — loads data, runs tests, proposes judgments",
  reviewer: "Reviewer — checks the preparer's work",
};

const VIEWS: { id: ViewId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "findings", label: "Exceptions" },
  { id: "changes", label: "What changed" },
  { id: "conclude", label: "Conclusion" },
];

export function Studio({ client }: { client: Client }) {
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [selected, setSelected] = useState<Engagement | null>(null);
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [sessionPrincipal, setSessionPrincipal] = useState("");
  const [acting, setActing] = useState("");
  const [view, setView] = useState<ViewId>("overview");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  const onError = useCallback((exc: unknown) => {
    setError(exc instanceof Error ? exc.message : String(exc));
  }, []);

  useEffect(() => {
    client.session().then((s) => { setSessionPrincipal(s.principal_id); setActing(s.principal_id); })
      .catch(onError);
    client.listEngagements().then(({ engagements: list }) => {
      setEngagements(list);
      if (list.length === 1) setSelected(list[0]);
    }).catch(onError);
  }, [client, onError]);

  const reload = useCallback(async () => {
    if (!selected) return;
    const fresh = (await client.listEngagements()).engagements
      .find((e) => e.engagement_id === selected.engagement_id) ?? selected;
    setBundle(await loadBundle(client, fresh));
  }, [client, selected]);

  useEffect(() => { setBundle(null); reload().catch(onError); }, [reload, onError]);

  const sitAs = (principal: string) => {
    client.actingAs = principal === sessionPrincipal ? "" : principal;
    setActing(principal);
    setError("");
  };

  const perform = async (label: string, work: () => Promise<unknown>) => {
    setBusy(label); setError("");
    try { await work(); } catch (exc) { onError(exc); }
    finally { setBusy(""); await reload().catch(onError); }
  };

  if (!selected) {
    return (
      <div className="studio">
        <header className="bar"><span className="brand">Noesi <b>Studio</b></span></header>
        <main className="picker">
          <h1>Choose an engagement</h1>
          {engagements.map((e) => (
            <button key={e.engagement_id} className="engagement-tile" onClick={() => setSelected(e)}>
              <span className="client">{e.client_name}</span>
              <span className="period">Year end {e.period_end}</span>
              <span className={`badge ${e.status}`}>{e.status}</span>
            </button>
          ))}
          {!engagements.length && (
            <p className="muted">No engagements yet. Create one in the <a href="/">Workbench</a>,
              or start the server with <code>--demo</code>.</p>
          )}
          {error && <div className="alert bad">{error}</div>}
          <a className="engagement-tile learn-tile" href="#/learn">
            <span className="client">Learn the audit</span>
            <span className="period">Ten lessons, acceptance to report</span>
            <span className="badge">course</span>
          </a>
        </main>
      </div>
    );
  }

  const roles = (principal: string) => bundle?.team.filter((m) => m.principal_id === principal)
    .map((m) => m.role) ?? [];
  const { stages, next } = bundle ? journey(bundle) : { stages: [] as Stage[], next: null };

  return (
    <div className="studio">
      <header className="bar">
        <span className="brand">Noesi <b>Studio</b></span>
        <span className="engagement-name">
          {selected.client_name} · year end {selected.period_end}
          {engagements.length > 1 && (
            <button className="link" onClick={() => { setSelected(null); setBundle(null); }}>switch</button>
          )}
        </span>
        <span className="spacer" />
        {bundle && (
          <ChairPicker team={bundle.team} acting={acting} session={sessionPrincipal} onSit={sitAs} />
        )}
        <a className="to-workbench" href="#/learn">Learn the audit</a>
        <a className="to-workbench" href="/">Workbench ↗</a>
      </header>

      {!bundle ? <p className="loading">Reading the engagement…</p> : (
        <div className="layout">
          <nav className="rail" aria-label="Engagement journey">
            {stages.map((stage, index) => (
              <div key={stage.id} className={`stage ${stage.state}`}>
                <div className="dot">{stage.state === "done" ? "✓" : index + 1}</div>
                <div className="stage-text">
                  <div className="stage-title">{stage.title}</div>
                  <div className="stage-q">{stage.question}</div>
                  <Progress value={stage.progress} />
                  <div className="stage-detail">{stage.detail}</div>
                </div>
              </div>
            ))}
          </nav>

          <main className="content">
            {next && (
              <NextStepCard next={next} bundle={bundle} client={client} acting={acting}
                            actingRoles={roles(acting)} busy={busy} perform={perform}
                            onSit={sitAs} onView={setView} />
            )}
            {!next && (
              <div className="next done-all">
                <div className="next-kicker">Complete</div>
                <h2>The engagement is locked and signed.</h2>
                <p>Export the packet from the Workbench to hand it to anyone for offline verification.</p>
              </div>
            )}
            {error && <div className="alert bad" role="alert">{error}</div>}

            <div className="views" role="tablist">
              {VIEWS.map((v) => (
                <button key={v.id} role="tab" aria-selected={view === v.id}
                        className={view === v.id ? "on" : ""} onClick={() => setView(v.id)}>
                  {v.label}
                  {v.id === "changes" && (bundle.impact?.summary.revised_files ?? 0) > 0 && (
                    <span className="count">{bundle.impact?.summary.affected_findings}</span>
                  )}
                </button>
              ))}
            </div>

            {view === "overview" && <Overview bundle={bundle} onView={setView} />}
            {view === "findings" && (
              <Findings bundle={bundle} client={client} actingRoles={roles(acting)}
                        perform={perform} busy={busy} />
            )}
            {view === "changes" && <Changes bundle={bundle} />}
            {view === "conclude" && <Conclude bundle={bundle} />}
          </main>
        </div>
      )}
    </div>
  );
}

function Progress({ value: [done, total] }: { value: [number, number] }) {
  const pct = total ? Math.round((100 * done) / total) : 0;
  return (
    <div className="progress" aria-label={`${done} of ${total}`}>
      <div style={{ width: `${pct}%` }} />
    </div>
  );
}

function ChairPicker({ team, acting, session, onSit }: {
  team: TeamMember[]; acting: string; session: string; onSit: (p: string) => void;
}) {
  const people = new Map<string, string[]>();
  for (const m of team) people.set(m.principal_id, [...(people.get(m.principal_id) ?? []), m.role]);
  if (!people.has(session)) people.set(session, []);
  return (
    <label className="chair">
      <span>Sitting as</span>
      <select value={acting} onChange={(e) => onSit(e.target.value)}>
        {[...people.entries()].map(([principal, rs]) => (
          <option key={principal} value={principal}>
            {rs.length ? rs.map((r) => r[0].toUpperCase() + r.slice(1)).join(" + ") : "no role"} · {principal}
          </option>
        ))}
      </select>
    </label>
  );
}

function NextStepCard({ next, bundle, client, acting, actingRoles, busy, perform, onSit, onView }: {
  next: NextStep; bundle: Bundle; client: Client; acting: string; actingRoles: string[];
  busy: string; perform: (label: string, work: () => Promise<unknown>) => Promise<void>;
  onSit: (p: string) => void; onView: (v: ViewId) => void;
}) {
  const eid = bundle.engagement.engagement_id;
  const [amount, setAmount] = useState("");
  const seated = !next.chair || actingRoles.includes(next.chair);
  const holder = next.chair
    ? bundle.team.find((m) => m.role === next.chair && m.principal_id !== acting)
      ?? bundle.team.find((m) => m.role === next.chair)
    : undefined;
  const version = (runId: string) => bundle.runs.find((r) => r.run_id === runId)?.version ?? 0;
  const action = next.action;

  let button: JSX.Element | null = null;
  if (action && seated) {
    switch (action.kind) {
      case "run":
        button = (
          <button className="primary" disabled={!!busy} onClick={() => perform("run", async () => {
            for (const pid of action.procedureIds) await client.runProcedure(eid, pid, {});
          })}>{busy === "run" ? "Running…" : `Run ${action.procedureIds.length}`}</button>
        );
        break;
      case "review":
      case "approve":
        button = (
          <button className="primary" disabled={!!busy} onClick={() => perform(action.kind, async () => {
            for (const id of action.runIds) {
              await client.reviewRun(eid, id, action.kind === "review" ? "reviewed" : "approved", version(id));
            }
          })}>{busy ? "Working…" : `${action.kind === "review" ? "Mark reviewed" : "Approve"} (${action.runIds.length})`}</button>
        );
        break;
      case "materiality":
        button = (
          <form className="inline" onSubmit={(e) => {
            e.preventDefault();
            perform("materiality", () => client.updateWorkflow(eid, "materiality",
                                                               { amount: Number(amount) }));
          }}>
            <input inputMode="decimal" placeholder="e.g. 420000" value={amount}
                   onChange={(e) => setAmount(e.target.value)} aria-label="Overall materiality" />
            <button className="primary" disabled={!Number(amount) || !!busy}>Set</button>
          </form>
        );
        break;
      case "view":
        button = <button className="primary" onClick={() => onView(action.view)}>Open</button>;
        break;
      case "workbench":
        button = <a className="primary" href="/">Open Workbench → {action.tab}</a>;
        break;
    }
  }

  return (
    <section className={`next stage-${next.stage}`}>
      <div className="next-kicker">Next step</div>
      <h2>{next.headline}</h2>
      <p>{next.why}</p>
      <div className="next-actions">
        {next.chair && !seated && (
          holder ? (
            <button className="secondary" onClick={() => onSit(holder.principal_id)}>
              Sit in the {next.chair} chair ({holder.principal_id})
            </button>
          ) : (
            <span className="muted">No one holds the {next.chair} role yet — add them on the Workbench Team tab.</span>
          )
        )}
        {button}
        {next.chair && <span className="chair-hint">{CHAIR_HELP[next.chair]}</span>}
      </div>
    </section>
  );
}
