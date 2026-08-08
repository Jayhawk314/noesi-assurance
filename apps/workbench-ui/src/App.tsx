// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
import { useCallback, useEffect, useState } from "react";
import { Client, Engagement, TeamMember } from "./api";
import {
  CoverageScreen, LockScreen, RunsScreen, SadScreen, SourcesScreen,
  TeamScreen,
} from "./screens";
import { FlowMapScreen } from "./screens/FlowMap";
import { ManualScreen } from "./screens/Manual";
import { useTheme } from "./lib/theme";

const TABS = [
  "Flow Map", "Team", "Sources & Mappings", "Coverage", "Runs & Findings",
  "SAD & Completion", "Lock & Export",
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

  const refresh = useCallback(async () => {
    try {
      const { engagements: list } = await client.listEngagements();
      setEngagements(list);
      setSelected((current) =>
        current
          ? list.find((e) => e.engagement_id === current.engagement_id) ?? null
          : null);
    } catch (exc) {
      setError(String(exc));
    }
  }, [client]);

  useEffect(() => { void refresh(); }, [refresh]);

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
                      </button>
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
  switch (tab) {
    case "Flow Map":
      return <FlowMapScreen client={client} eid={eid} onError={onError}
                            onGoToSources={() => onNavigate("Sources & Mappings")} />;
    case "Team":
      return <TeamScreen client={client} eid={eid} onError={onError} />;
    case "Sources & Mappings":
      return <SourcesScreen client={client} eid={eid} onError={onError} />;
    case "Coverage":
      return <CoverageScreen client={client} eid={eid} onError={onError} />;
    case "Runs & Findings":
      return <RunsScreen client={client} eid={eid} onError={onError} />;
    case "SAD & Completion":
      return <SadScreen client={client} eid={eid} onError={onError} />;
    case "Lock & Export":
      return <LockScreen client={client} engagement={engagement}
                         onError={onError} onChanged={onChanged} />;
  }
}
