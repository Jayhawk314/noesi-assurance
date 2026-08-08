// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** The manual, rendered in-app: chapter list plus server-rendered HTML.
 *  The HTML comes from the workbench's own renderer over first-party
 *  markdown (escaped before markup), so injecting it here introduces no
 *  content the repo does not already control. Cross-chapter links carry
 *  data-chapter attributes; clicks are intercepted to stay in-app. */

import { useCallback, useEffect, useState } from "react";
import { Client } from "../api";

export function ManualScreen({ client, onError }: {
  client: Client;
  onError: (exc: unknown) => void;
}) {
  const [chapters, setChapters] =
    useState<{ name: string; title: string }[]>([]);
  const [current, setCurrent] = useState("");
  const [body, setBody] = useState<{ title: string; html: string } | null>(null);

  useEffect(() => {
    client.manualChapters()
      .then(({ chapters: list }) => {
        setChapters(list);
        setCurrent((now) => now || list[0]?.name || "");
      })
      .catch(onError);
  }, [client, onError]);

  useEffect(() => {
    if (!current) return;
    client.manualChapter(current)
      .then(({ title, html }) => setBody({ title, html }))
      .catch(onError);
  }, [client, current, onError]);

  const intercept = useCallback((event: React.MouseEvent) => {
    const anchor = (event.target as HTMLElement).closest("a[data-chapter]");
    if (!anchor) return;
    event.preventDefault();
    setCurrent(anchor.getAttribute("data-chapter") ?? "");
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="manual">
      <nav className="manual-nav">
        {chapters.map((chapter) => (
          <button key={chapter.name}
                  className={chapter.name === current ? "active" : ""}
                  onClick={() => { setCurrent(chapter.name); window.scrollTo(0, 0); }}>
            {chapter.title}
          </button>
        ))}
      </nav>
      <article className="manual-content" onClick={intercept}
               dangerouslySetInnerHTML={{ __html: body?.html ?? "" }} />
    </div>
  );
}
