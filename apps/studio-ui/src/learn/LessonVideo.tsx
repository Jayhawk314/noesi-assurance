// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** A lesson's teaching video. In the local app the workbench serves it from the Studio build
 *  (public/videos/). The single-file Streamlit copy has nowhere to hold a video, so there it
 *  plays the same committed file from the public repository through the jsDelivr CDN. */
import type { Lesson } from "./types";

type Video = NonNullable<Lesson["video"]>;
// Studio is served at /studio/ (vite.config base); public/ files land at its root.
const LOCAL = "/studio/videos/";
const HOSTED = "https://cdn.jsdelivr.net/gh/Jayhawk314/noesi-assurance@main/apps/studio-ui/public/videos/";

export function LessonVideo({ video, standalone }: { video: Video; standalone: boolean }) {
  const base = standalone ? HOSTED : LOCAL;
  return (
    <section className="lesson-video" aria-label={`Video: ${video.title}`}>
      <div className="lesson-video-head">
        <b>Watch</b> <span>{video.title}</span> <span className="muted">· {video.minutes} min</span>
      </div>
      <video controls preload="metadata" playsInline src={base + video.file}
             poster={video.poster ? base + video.poster : undefined}>
        Your browser can’t play this video.
      </video>
      <p className="lesson-video-credits">{video.credits}</p>
    </section>
  );
}
