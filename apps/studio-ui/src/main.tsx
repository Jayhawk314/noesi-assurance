// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Client } from "../../workbench-ui/src/api";
import { Studio } from "./Studio";
import { Learn } from "./learn/Learn";
import "./studio.css";
import "./learn/learn.css";

// Same session-token handshake as the Workbench: the server rewrites the
// placeholder in the page it serves.
const PLACEHOLDER = ["__NOESI", "SESSION", "TOKEN__"].join("_");
const token = document.querySelector('meta[name="noesi-session"]')
  ?.getAttribute("content")?.trim() ?? "";
const client = token && token !== PLACEHOLDER ? new Client(token) : null;

function useHashRoute(): string {
  const read = () => window.location.hash.replace(/^#/, "") || "/";
  const [route, setRoute] = useState(read);
  useEffect(() => {
    const onChange = () => setRoute(read());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}

function Root() {
  const route = useHashRoute();
  // The course is static teaching content: it needs no session.
  if (route.startsWith("/learn")) return <Learn route={route} />;
  if (client) return <Studio client={client} />;
  return (
    <div className="studio"><main className="picker">
      <h1>Noesi Studio</h1>
      <p className="alert bad">This page was served without a session token. Start the
        workbench with <code>noesi-workbench</code> and open the studio address it prints.</p>
      <p><a href="#/learn">You can still open the course: Learn the audit →</a></p>
    </main></div>
  );
}

createRoot(document.getElementById("root")!).render(<StrictMode><Root /></StrictMode>);
