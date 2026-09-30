// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Learn } from "./learn/Learn";
import "./studio.css";
import "./learn/learn.css";

// The Kestrel course is static teaching content: no session, no server.
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
  return <Learn route={route.startsWith("/learn") ? route : "/learn"} />;
}

createRoot(document.getElementById("root")!).render(<StrictMode><Root /></StrictMode>);
