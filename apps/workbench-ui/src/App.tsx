// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
import { useCallback, useEffect, useState } from "react";
import { Client, Engagement, TeamMember } from "./api";
import {
  CoverageScreen, LockScreen, RunsScreen, SadScreen, SourcesScreen,
  TeamScreen,
} from "./screens";
import { FlowMapScreen } from "./screens/FlowMap";
import { FraudScreen } from "./screens/Fraud";
import { ManualScreen } from "./screens/Manual";
import { OpinionScreen } from "./screens/Opinion";
import { RiskScreen } from "./screens/Risk";
import { ScopeScreen } from "./screens/Scope";
import { WhatChangedScreen } from "./screens/WhatChanged";
import { useTheme } from "./lib/theme";

const TABS = [
  "Flow Map", "Team", "Scope & Policies", "Planning & Risk", "Sources & Mappings",
  "Coverage", "Runs & Findings", "Fraud", "What Changed", "SAD & Completion", "Draft Opinion",
  "Lock & Export",
] as const;
type Tab = (typeof TABS)[number];

// The workbench rewrites this placeholder in the page it serves. It survives
// only when the built dist is served by something else, which cannot mint a
// token — the shell says so rather than offering a login it cannot satisfy.
const TOKEN_PLACEHOLDER = ["__NOESI", "SESSION", "TOKEN__"].join("_");

const CLIENT = (() => {
  const served = document.querySelector('meta[name="noesi-session"]')
    ?.getAttribute("content")?.trim() ?? "";
  return served && served !== TOKEN_PLACEHOLDER ? new Client(served) : null;
})();

export function App() {
  if (!CLIENT) {
    return (
      <div className="token-gate panel">
        <h2>Noesi Assurance Workbench</h2>
        <div className="error-bar">
          This page was served without a session token. Start the workbench
          with <code>noesi-workbench</code> and open the address it prints.
        </div>
      </div>
    );
  }
  return <Workbench client={CLIENT} />;
}

function Workbench({ client }: { client: Client }) {
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [selected, setSelected] = useState<Engagement | null>(null);
  const [tab, setTab] = useState<Tab>("Flow Map");
  const [error, setError] = useState("");
  const [newClient, setNewClient] = useState("");
  const [newPeriod, setNewPeriod] = useState("");
  const [theme, toggleTheme] = useTheme();
  const [sessionPrincipal, setSessionPrincipal] = useState("");
  const [acting, setActing] = useState("");
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [manualOpen, setManualOpen] = useState(false);
  const [archived, setArchived] = useState<Engagement[]>([]);
  const [showArchived, setShowArchived] = useState(false);
  const [archiving, setArchiving] = useState<string | null>(null);
  const [archiveReason, setArchiveReason] = useState("");
  const [deleting, setDeleting] = useState<Engagement | null>(null);
  const [deleteName, setDeleteName] = useState("");
  const [deleteReason, setDeleteReason] = useState("");
  const [cases, setCases] = useState<{ case: string; title: string }[]>([]);
  const [caseChoice, setCaseChoice] = useState("");
  const [loadingCase, setLoadingCase] = useState(false);
  const refresh = useCallback(async () => {
    try {
      const { engagements: list } = await client.listEngagements();
      setEngagements(list);
      const { engagements: gone } = await client.archivedEngagements();
      setArchived(gone);
      setSelected((current) =>
        current
          ? list.find((e) => e.engagement_id === current.engagement_id) ?? null
          : null);
    } catch (exc) {
      setError(String(exc));
    }
  }, [client]);

  useEffect(() => { void refresh(); }, [refresh]);

  useEffect(() => {
    client.cases()
      .then(({ cases: list }) => { setCases(list); setCaseChoice(list[0]?.case ?? ""); })
      .catch(() => setCases([]));
  }, [client]);

  async function loadCase() {
    try {
      setError(""); setLoadingCase(true);
      await client.loadCase(caseChoice);
      await refresh();
    } catch (exc) { report(exc); } finally { setLoadingCase(false); }
  }

  async function archive(eid: string) {
    try {
      setError("");
      await client.archiveEngagement(eid, archiveReason.trim());
      setArchiving(null); setArchiveReason("");
      await refresh();
    } catch (exc) { report(exc); }
  }

  const norm = (text: string) => text.trim().replace(/\s+/g, " ").toLowerCase();

  async function remove(e: Engagement) {
    try {
      setError("");
      await client.deleteEngagement(e.engagement_id, deleteName, deleteReason.trim());
      setDeleting(null); setDeleteName(""); setDeleteReason("");
      await refresh();
    } catch (exc) { report(exc); }
  }

  const deleteButton = (e: Engagement) => (
    <button className="action" title="Delete this engagement and everything loaded into it"
            onClick={() => { setDeleting(e); setDeleteName(""); setDeleteReason(""); setArchiving(null); }}>
      delete
    </button>
  );

  async function restore(eid: string) {
    try { setError(""); await client.restoreEngagement(eid); await refresh(); }
    catch (exc) { report(exc); }
  }

  const report = (exc: unknown) =>
    setError(exc instanceof Error ? exc.message : String(exc));

  useEffect(() => {
    client.session()
      .then(({ principal_id }) => {
        setSessionPrincipal(principal_id);
        setActing((current) => current || principal_id);
      })
      .catch(report);
  }, [client]);

  // The chairs the operator can sit in: the session default plus everyone
  // assigned to the open engagement. Free text is allowed — a chair that
  // does not hold the required role is refused by the server, loudly.
  useEffect(() => {
    if (!selected) { setTeam([]); return; }
    client.team(selected.engagement_id)
      .then(({ team: members }) => setTeam(members))
      .catch(() => setTeam([]));
  }, [client, selected, engagements]);

  function switchChair(next: string) {
    const principal = next.trim();
    if (!principal || principal === acting) return;
    client.actingAs = principal;
    setActing(principal);
    setError("");
  }

  async function create() {
    try {
      setError("");
      await client.createEngagement(newClient.trim(), newPeriod.trim());
      setNewClient("");
      setNewPeriod("");
      await refresh();
    } catch (exc) { report(exc); }
  }

  return (
    <>
      <header className="app">
        <h1>Noesi Assurance Workbench</h1>
        {selected && (
          <span className="context">
            {selected.client_name} — FYE {selected.period_end}{" "}
            <span className={`status ${selected.status === "locked" ? "ok" : "pending"}`}>
              [{selected.status}]
            </span>
          </span>
        )}
        <ChairSwitcher acting={acting} sessionPrincipal={sessionPrincipal}
                       team={team} onSwitch={switchChair} />
        <button className={`manual-toggle ${manualOpen ? "active" : ""}`}
                onClick={() => setManualOpen((open) => !open)}
                title="The manual: the audit process and the workbench, taught together">
          {manualOpen ? "✕ manual" : "📖 manual"}
        </button>
        <button className="theme-toggle" onClick={toggleTheme}
                aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
                title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}>
          {theme === "dark" ? "☀" : "☾"}
        </button>
      </header>
      <main>
        {error && (
          <div className="error-bar" onClick={() => setError("")}>
            {error} <em>(click to dismiss)</em>
          </div>
        )}
        {manualOpen ? (
          <ManualScreen client={client} onError={report} />
        ) : !selected ? (
          <>
            <h2>Engagements</h2>
            <table className="dense">
              <thead>
                <tr><th>Client</th><th>Period end</th><th>Status</th><th /></tr>
              </thead>
              <tbody>
                {engagements.map((engagement) => (
                  <tr key={engagement.engagement_id}>
                    <td>{engagement.client_name}</td>
                    <td>{engagement.period_end}</td>
                    <td>
                      <span className={`status ${engagement.status === "locked" ? "ok" : "pending"}`}>
                        {engagement.status}
                      </span>
                    </td>
                    <td>
                      <button className="action"
                              onClick={() => { setSelected(engagement); setTab("Flow Map"); }}>
                        open
                      </button>{" "}
                      {archiving === engagement.engagement_id ? (
                        <form className="inline" style={{ display: "inline-flex" }}
                              onSubmit={(e) => { e.preventDefault(); void archive(engagement.engagement_id); }}>
                          <input value={archiveReason} autoFocus
                                 placeholder="why archive? (10+ characters)"
                                 onChange={(e) => setArchiveReason(e.target.value)} />
                          <button className="action" type="submit"
                                  disabled={archiveReason.trim().length < 10}>
                            confirm archive
                          </button>
                          <button className="action" type="button"
                                  onClick={() => { setArchiving(null); setArchiveReason(""); }}>
                            cancel
                          </button>
                        </form>
                      ) : (
                        <button className="action"
                                title="Take it off this list. Nothing is erased; restore brings it back."
                                onClick={() => { setArchiving(engagement.engagement_id); setArchiveReason(""); }}>
                          archive
                        </button>
                      )}{" "}
                      {deleteButton(engagement)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <form className="inline" onSubmit={(e) => { e.preventDefault(); void create(); }}>
              <input value={newClient} placeholder="client name"
                     onChange={(e) => setNewClient(e.target.value)} />
              <input value={newPeriod} placeholder="period end (YYYY-MM-DD)"
                     onChange={(e) => setNewPeriod(e.target.value)} />
              <button className="action" type="submit"
                      disabled={!newClient.trim() || !newPeriod.trim()}>
                create engagement
              </button>
            </form>
            {deleting && (() => {
              const nameOk = norm(deleteName) === norm(deleting.client_name);
              const reasonOk = deleteReason.trim().length >= 10;
              return (
              <form className="panel" onSubmit={(ev) => { ev.preventDefault(); void remove(deleting); }}>
                <h3>Delete {deleting.client_name} (FYE {deleting.period_end})?</h3>
                <p className="note">
                  This removes the engagement and everything loaded into it: files, mappings,
                  runs, findings, team and settings. It cannot be undone. The journal keeps a
                  line saying who deleted it and why. To keep it but hide it, use archive instead.
                </p>
                <p>To confirm, type the client name: <b>{deleting.client_name}</b></p>
                <input value={deleteName} placeholder="type the name to delete" autoFocus style={{ minWidth: "22em" }}
                       onChange={(ev) => setDeleteName(ev.target.value)} />{" "}
                <input value={deleteReason} placeholder="why delete? (10+ characters)" style={{ minWidth: "22em" }}
                       onChange={(ev) => setDeleteReason(ev.target.value)} />{" "}
                <button className="action" type="submit" disabled={!nameOk || !reasonOk}>
                  delete permanently
                </button>{" "}
                <button className="action" type="button" onClick={() => setDeleting(null)}>cancel</button>
                {(!nameOk || !reasonOk) && (
                  <p className="note">
                    {!nameOk && "The name doesn't match yet. "}
                    {!reasonOk && `The reason needs ${10 - deleteReason.trim().length} more characters.`}
                  </p>
                )}
              </form>
              );
            })()}
            {cases.length > 0 && (
              <form className="inline" onSubmit={(e) => { e.preventDefault(); void loadCase(); }}>
                <select value={caseChoice} onChange={(e) => setCaseChoice(e.target.value)}>
                  {cases.map((c) => <option key={c.case} value={c.case}>{c.title}</option>)}
                </select>
                <button className="action" type="submit" disabled={!caseChoice || loadingCase}>
                  {loadingCase ? "loading case…" : "load teaching case"}
                </button>
              </form>
            )}
            {archived.length > 0 && (
              <>
                <button className="action" onClick={() => setShowArchived((v) => !v)}>
                  {showArchived ? "hide" : "show"} archived ({archived.length})
                </button>
                {showArchived && (
                  <table className="dense">
                    <thead><tr><th>Client</th><th>Period end</th><th /></tr></thead>
                    <tbody>
                      {archived.map((e) => (
                        <tr key={e.engagement_id}>
                          <td>{e.client_name}</td><td>{e.period_end}</td>
                          <td><button className="action" onClick={() => void restore(e.engagement_id)}>restore</button>{" "}{deleteButton(e)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </>
            )}
            <p className="note">
              Creating an engagement makes the acting principal (top right)
              its partner. Preparing, reviewing, and approving are separate
              chairs — switch up there when a gate refuses you.
            </p>
          </>
        ) : (
          <>
            <button className="action" onClick={() => { setSelected(null); void refresh(); }}>
              ← all engagements
            </button>
            <nav className="tabs">
              {TABS.map((name) => (
                <button key={name} className={name === tab ? "active" : ""}
                        onClick={() => setTab(name)}>
                  {name}
                </button>
              ))}
            </nav>
            <ScreenBody tab={tab} client={client} engagement={selected}
                        onError={report} onChanged={refresh}
                        onNavigate={setTab} />
          </>
        )}
      </main>
    </>
  );
}

/** One operator, several chairs. Server-side gates treat chairs as people:
 *  a proposal's author cannot approve it, a run's executor cannot review
 *  it. Which chair performed each action is journaled and appears on the
 *  workpaper — switching is explicit and always visible here. */
function ChairSwitcher({ acting, sessionPrincipal, team, onSwitch }: {
  acting: string;
  sessionPrincipal: string;
  team: TeamMember[];
  onSwitch: (principal: string) => void;
}) {
  const [draft, setDraft] = useState(acting);
  useEffect(() => { setDraft(acting); }, [acting]);
  const roles = new Map<string, string[]>();
  if (sessionPrincipal) roles.set(sessionPrincipal, ["session"]);
  for (const member of team) {
    roles.set(member.principal_id,
              [...(roles.get(member.principal_id) ?? []), member.role]);
  }
  const actingRoles = team
    .filter((m) => m.principal_id === acting)
    .map((m) => m.role);
  return (
    <span className="who">
      acting as
      <input className="chair-input" list="chair-options" value={draft}
             aria-label="acting principal"
             onChange={(e) => setDraft(e.target.value)}
             onBlur={() => (draft.trim() ? onSwitch(draft) : setDraft(acting))}
             onKeyDown={(e) => {
               if (e.key === "Enter") {
                 e.preventDefault();
                 onSwitch(draft);
                 (e.target as HTMLInputElement).blur();
               }
             }} />
      <datalist id="chair-options">
        {[...roles.entries()].map(([id, held]) => (
          <option key={id} value={id}>{held.join(", ")}</option>
        ))}
      </datalist>
      {actingRoles.length > 0 && (
        <span className="chair-roles">{actingRoles.join(" · ")}</span>
      )}
    </span>
  );
}

function ScreenBody({ tab, client, engagement, onError, onChanged, onNavigate }: {
  tab: Tab;
  client: Client;
  engagement: Engagement;
  onError: (exc: unknown) => void;
  onChanged: () => Promise<void>;
  onNavigate: (tab: Tab) => void;
}) {
  const eid = engagement.engagement_id;
  const goTo = (name: string) => {
    if ((TABS as readonly string[]).includes(name)) onNavigate(name as Tab);
  };
  switch (tab) {
    case "Flow Map":
      return <FlowMapScreen client={client} eid={eid} onError={onError}
                            onGoToSources={() => onNavigate("Sources & Mappings")} />;
    case "Team":
      return <TeamScreen client={client} eid={eid} onError={onError} />;
    case "Scope & Policies":
      return <ScopeScreen client={client} eid={eid} onError={onError} />;
    case "Planning & Risk":
      return <RiskScreen client={client} eid={eid} onError={onError} />;
    case "Sources & Mappings":
      return <SourcesScreen client={client} eid={eid} onError={onError} />;
    case "Coverage":
      return <CoverageScreen client={client} eid={eid} onError={onError} />;
    case "Runs & Findings":
      return <RunsScreen client={client} eid={eid} onError={onError} />;
    case "Fraud":
      return <FraudScreen client={client} eid={eid} onError={onError} />;
    case "What Changed":
      return <WhatChangedScreen client={client} eid={eid} onError={onError} />;
    case "SAD & Completion":
      return <SadScreen client={client} eid={eid} onError={onError} />;
    case "Draft Opinion":
      return <OpinionScreen client={client} eid={eid} onError={onError} onNavigate={goTo} />;
    case "Lock & Export":
      return <LockScreen client={client} engagement={engagement}
                         onError={onError} onChanged={onChanged} onNavigate={goTo} />;
  }
}
