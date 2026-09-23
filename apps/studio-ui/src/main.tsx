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
  // Without a session (a static host, an embed) only the course exists.
  if (!client) return <Learn route={route.startsWith("/learn") ? route : "/learn"} standalone />;
  if (route.startsWith("/learn")) return <Learn route={route} />;
  return <Studio client={client} />;
}

createRoot(document.getElementById("root")!).render(<StrictMode><Root /></StrictMode>);
