// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Noesi Studio — the visual practitioner view.
 *
 *  The Workbench (at /) is the full-control instrument and the teaching
 *  surface. The Studio answers two questions at a glance: where is this
 *  engagement, and what is the next step. It reads the same server records
 *  and sends the same journaled commands — it only arranges them visually.
 *  One user per engagement (D9 stage 3, 2 Oct 2026): there are no chairs. */

import { useCallback, useEffect, useState } from "react";
import { Client, Engagement } from "../../workbench-ui/src/api";
import { Bundle, NextStep, Stage, ViewId, journey, loadBundle } from "./data";
import { Overview } from "./views/Overview";
import { Findings } from "./views/Findings";
import { Changes } from "./views/Changes";
import { Conclude } from "./views/Conclude";

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
  const [view, setView] = useState<ViewId>("overview");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  const onError = useCallback((exc: unknown) => {
    setError(exc instanceof Error ? exc.message : String(exc));
  }, []);

  useEffect(() => {
    client.session().then((s) => setSessionPrincipal(s.principal_id)).catch(onError);
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
        {sessionPrincipal && (
          <span className="chair" title="Every step is recorded under this user">
            user <code>{sessionPrincipal}</code>
          </span>
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
              <NextStepCard next={next} bundle={bundle} client={client}
                            busy={busy} perform={perform} onView={setView} />
            )}
            {!next && (
              <div className="next done-all">
                <div className="next-kicker">Complete</div>
                <h2>Nothing is open.</h2>
                <p>Export the record from the Workbench (Export tab); anyone can check it offline.</p>
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
              <Findings bundle={bundle} client={client} perform={perform} busy={busy} />
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

function NextStepCard({ next, bundle, client, busy, perform, onView }: {
  next: NextStep; bundle: Bundle; client: Client;
  busy: string; perform: (label: string, work: () => Promise<unknown>) => Promise<void>;
  onView: (v: ViewId) => void;
}) {
  const eid = bundle.engagement.engagement_id;
  const [amount, setAmount] = useState("");
  const action = next.action;

  let button: JSX.Element | null = null;
  if (action) {
    switch (action.kind) {
      case "run":
        button = (
          <button className="primary" disabled={!!busy} onClick={() => perform("run", async () => {
            for (const pid of action.procedureIds) await client.runProcedure(eid, pid, {});
          })}>{busy === "run" ? "Running…" : `Run ${action.procedureIds.length}`}</button>
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
        {button}
      </div>
    </section>
  );
}
