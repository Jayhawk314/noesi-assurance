// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** A module's teaching video. Served with the built app (base /kestrel/), it plays from
 *  public/videos/. The single-file Streamlit page has nowhere to hold a video, so there it plays
 *  the same committed file from the public repository through the jsDelivr CDN (as Harborline's
 *  Learn does). A module without a video keeps the placeholder. */
import type { Lesson } from "./types";

type Video = NonNullable<Lesson["video"]>;
const LOCAL = "/kestrel/videos/";
const HOSTED = "https://cdn.jsdelivr.net/gh/Jayhawk314/noesi-assurance@main/apps/learn-kestrel-ui/public/videos/";

function base(): string {
  try { return window.location.pathname.startsWith("/kestrel/") ? LOCAL : HOSTED; }
  catch { return HOSTED; }
}

export function LessonVideo({ title, video }: { title: string; video?: Video }) {
  if (!video) {
    return (
      <section className="lesson-video placeholder" aria-label={`Video placeholder: ${title}`}>
        <div className="lesson-video-head">
          <b>Watch</b> <span>{title}</span> <span className="muted">· video coming</span>
        </div>
        <div className="video-slot">The video for this module is not made yet.</div>
      </section>
    );
  }
  const at = base();
  return (
    <section className="lesson-video" aria-label={`Video: ${video.title}`}>
      <div className="lesson-video-head">
        <b>Watch</b> <span>{video.title}</span> <span className="muted">· {video.minutes} min</span>
      </div>
      {/* preload="none": nothing downloads until Play. */}
      <video controls preload="none" playsInline src={at + video.file}
             poster={video.poster ? at + video.poster : undefined}>
        Your browser can’t play this video.
      </video>
      <p className="lesson-video-credits">
        Not playing? <a href={at + video.file} target="_blank" rel="noreferrer">Open the video in a new tab</a>.
      </p>
      <p className="lesson-video-credits">{video.credits}</p>
    </section>
  );
}
