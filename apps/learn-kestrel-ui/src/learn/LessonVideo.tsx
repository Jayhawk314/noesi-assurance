// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** Where a module's video goes. The Kestrel videos are not made yet: scripts
 *  first, then James approves the scripts and the credits before any voicing
 *  (docs/LEARN-KESTREL-PLAN.md). Until then this holds the place. */

export function LessonVideo({ title }: { title: string }) {
  return (
    <section className="lesson-video placeholder" aria-label={`Video placeholder: ${title}`}>
      <div className="lesson-video-head">
        <b>Watch</b> <span>{title}</span> <span className="muted">· video coming</span>
      </div>
      <div className="video-slot">The video for this module is not made yet.</div>
    </section>
  );
}
