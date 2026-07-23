import { useCallback, useEffect, useState } from "react";
import { ApiError, Client, Engagement } from "./api";
import {
  CoverageScreen, LockScreen, RunsScreen, SadScreen, SourcesScreen,
  TeamScreen,
} from "./screens";

const TABS = [
  "Team", "Sources & Mappings", "Coverage", "Runs & Findings",
  "SAD & Completion", "Lock & Export",
] as const;
type Tab = (typeof TABS)[number];

export function App() {
  const [client, setClient] = useState<Client | null>(null);
  if (!client) return <TokenGate onReady={setClient} />;
  return <Workbench client={client} />;
}

function TokenGate({ onReady }: { onReady: (client: Client) => void }) {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");

  async function connect() {
    const candidate = new Client(token.trim());
    try {
      await candidate.listEngagements();
      onReady(candidate);
    } catch (exc) {
      setError(exc instanceof ApiError && exc.status === 401
        ? "That token was not accepted."
        : `Could not reach the workbench API: ${String(exc)}`);
    }
  }

  return (
    <div className="token-gate panel">
      <h2>Noesi Assurance Workbench</h2>
      <p className="note">
        Paste the session token the workbench printed at startup. It is held
        in memory only.
      </p>
      <form className="inline" onSubmit={(e) => { e.preventDefault(); void connect(); }}>
        <input type="password" value={token} placeholder="session token"
               onChange={(e) => setToken(e.target.value)} size={40} autoFocus />
        <button className="action" type="submit" disabled={!token.trim()}>
          Connect
        </button>
      </form>
      {error && <div className="error-bar">{error}</div>}
    </div>
  );
}

function Workbench({ client }: { client: Client }) {
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [selected, setSelected] = useState<Engagement | null>(null);
  const [tab, setTab] = useState<Tab>("Team");
  const [error, setError] = useState("");
  const [newClient, setNewClient] = useState("");
  const [newPeriod, setNewPeriod] = useState("");

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
          <span>
            {selected.client_name} — FYE {selected.period_end}{" "}
            <span className={`status ${selected.status === "locked" ? "ok" : "pending"}`}>
              [{selected.status}]
            </span>
          </span>
        )}
        <span className="who">local session</span>
      </header>
      <main>
        {error && (
          <div className="error-bar" onClick={() => setError("")}>
            {error} <em>(click to dismiss)</em>
          </div>
        )}
        {!selected ? (
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
                              onClick={() => { setSelected(engagement); setTab("Team"); }}>
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
              Creating an engagement makes this session's principal its
              partner.
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
                        onError={report} onChanged={refresh} />
          </>
        )}
      </main>
    </>
  );
}

function ScreenBody({ tab, client, engagement, onError, onChanged }: {
  tab: Tab;
  client: Client;
  engagement: Engagement;
  onError: (exc: unknown) => void;
  onChanged: () => Promise<void>;
}) {
  const eid = engagement.engagement_id;
  switch (tab) {
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
