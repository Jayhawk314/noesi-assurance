// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** A lesson's teaching video. The file sits beside the Studio build (public/videos/) and is
 *  served by the workbench, so it plays in the local app. The single-file Streamlit copy has
 *  no place to hold a video, so there it says where the video plays instead. */
import type { Lesson } from "./types";

type Video = NonNullable<Lesson["video"]>;
// Studio is served at /studio/ (vite.config base); public/ files land at its root.
const BASE = "/studio/";

export function LessonVideo({ video, standalone }: { video: Video; standalone: boolean }) {
  const src = `${BASE}videos/${video.file}`;
  return (
    <section className="lesson-video" aria-label={`Video: ${video.title}`}>
      <div className="lesson-video-head">
        <b>Watch</b> <span>{video.title}</span> <span className="muted">· {video.minutes} min</span>
      </div>
      {standalone ? (
        <p className="lesson-video-note">
          This lesson has a short video. It plays in the local Noesi app: start the workbench
          and open Studio → Learn.
        </p>
      ) : (
        <video controls preload="metadata" playsInline src={src}
               poster={video.poster ? `${BASE}videos/${video.poster}` : undefined}>
          Your browser can’t play this video.
        </video>
      )}
      <p className="lesson-video-credits">{video.credits}</p>
    </section>
  );
}
