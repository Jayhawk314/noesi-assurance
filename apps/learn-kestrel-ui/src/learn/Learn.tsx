// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** "Learn the audit" on Kestrel Valley Cycle Supply: one module per audit
 *  area, each in four steps (the idea, by hand, in Noesi, compare with the
 *  key). The layout is the Harborline Learn app's (apps/studio-ui).
 *
 *  Routes (hash): #/learn (course home), #/learn/<n> (a module),
 *  #/learn/map (the course map), #/learn/documents, #/learn/trace,
 *  #/learn/excel, #/learn/fraud (the fraud track), #/learn/fraud/<n>. Static content; needs no session. Progress
 *  is a per-browser convenience in localStorage and the page works without it. */

import { Fragment, useEffect, useState } from "react";
import { Documents } from "./Documents";
import { ExcelAudit } from "./ExcelAudit";
import { agrees, findRow, keyAt, moduleRows } from "./keyData";
import { LessonVideo } from "./LessonVideo";
import { FRAUD_LESSONS } from "./lessons-fraud";
import { COMING, LESSONS } from "./lessons";
import { displayOrder } from "./shuffle";
import { Trace } from "./Trace";
import { Block, Coming, Lesson, Question } from "./types";

type Entry = {
  read: number; answers: Record<number, number>; done: boolean;
  mine?: Record<number, string>; submitted?: boolean;
};
type Progress = Record<string, Entry>;
const STORE = "noesi-learn-kestrel-progress-v1";

function loadProgress(): Progress {
  try { return JSON.parse(localStorage.getItem(STORE) || "{}") as Progress; } catch { return {}; }
}
function saveProgress(p: Progress) {
  try { localStorage.setItem(STORE, JSON.stringify(p)); } catch { /* private mode: in-memory only */ }
}

/** **bold** and `code` only; everything else is plain text (no HTML injection). */
function Rich({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return <>{parts.map((part, i) =>
    part.startsWith("**") ? <strong key={i}>{part.slice(2, -2)}</strong>
      : part.startsWith("`") ? <code key={i}>{part.slice(1, -1)}</code>
      : <Fragment key={i}>{part}</Fragment>)}</>;
}

const PHASES: Lesson["phase"][] = ["Planning", "Fieldwork", "Completion"];
const COVERAGE_LABEL = { full: "Noesi covers this step", partial: "Noesi covers part of this", none: "Not in Noesi yet" };
const STATUS_LABEL = { match: "agrees with the key", differs: "differs", "not in Noesi": "not in Noesi" };

/** Follow in-app "#/…" links by setting location.hash directly. A plain
 *  fragment link resolves against the document's base URL, which inside an
 *  embedding frame (e.g. Streamlit's srcdoc iframe) is the host page — the
 *  click would load the host into the frame instead of changing lessons. */
function followHashLinks(event: React.MouseEvent) {
  const anchor = (event.target as HTMLElement).closest("a");
  const href = anchor?.getAttribute("href");
  if (!href || !href.startsWith("#/") || event.metaKey || event.ctrlKey) return;
  event.preventDefault();
  if (window.location.hash !== href) window.location.hash = href;
}

type Item = { kind: "lesson"; lesson: Lesson } | { kind: "coming"; coming: Coming };
const ALL: Item[] = [
  ...LESSONS.map((lesson) => ({ kind: "lesson" as const, lesson })),
  ...COMING.map((coming) => ({ kind: "coming" as const, coming })),
].sort((a, b) => num(a) - num(b));
function num(item: Item) { return item.kind === "lesson" ? item.lesson.n : item.coming.n; }
function phaseOf(item: Item) { return item.kind === "lesson" ? item.lesson.phase : item.coming.phase; }

export function Learn({ route }: { route: string }) {
  const [progress, setProgress] = useState<Progress>(loadProgress);
  const update = (slug: string, change: Partial<Entry>) => {
    setProgress((prev) => {
      const current = prev[slug] ?? { read: 0, answers: {}, done: false };
      const next = { ...prev, [slug]: { ...current, ...change } };
      saveProgress(next);
      return next;
    });
  };

  const parts = route.split("/").filter(Boolean);
  const target = parts[1];
  const fraud = target === "fraud";
  const track = fraud ? FRAUD_TRACK : MAIN_TRACK;
  const lesson = track.lessons.find((l) => String(l.n) === (fraud ? parts[2] : target));

  useEffect(() => { window.scrollTo(0, 0); }, [route]);

  return (
    <div className="studio learn" onClickCapture={followHashLinks}>
      <header className="bar">
        <a className="brand" href="#/learn">Noesi <b>Learn</b></a>
        <span className="engagement-name">Kestrel Valley Cycle Supply, year ended June 30, 2026</span>
        <span className="spacer" />
        <a className="to-workbench" href="#/learn/documents">The documents</a>
        <a className="to-workbench" href="#/learn/trace">Follow a number</a>
        <a className="to-workbench" href="#/learn/excel">Excel for audit</a>
        <a className="to-workbench" href="#/learn/map">Course map</a>
        <a className="to-workbench" href="#/learn/fraud">Fraud track</a>
        {/* The manual, "How Noesi works" and the Code Atlas, on GitHub (the manual's front page links all three). */}
        <a className="to-workbench" href="https://github.com/Jayhawk314/noesi-assurance/blob/main/docs/manual/README.md"
           target="_blank" rel="noreferrer">Manual</a>
      </header>
      {target === "map" ? <CourseMap progress={progress} />
        : target === "documents" ? <Documents />
        : target === "trace" ? <Trace />
        : target === "excel" ? <ExcelAudit />
        : lesson ? <LessonPage lesson={lesson} track={track} progress={progress[lesson.slug]}
                               onUpdate={(c) => update(lesson.slug, c)} />
        : fraud ? <FraudHome progress={progress} />
        : <Home progress={progress} />}
    </div>
  );
}

function Home({ progress }: { progress: Progress }) {
  const done = LESSONS.filter((l) => progress[l.slug]?.done).length;
  const next = LESSONS.find((l) => !progress[l.slug]?.done) ?? LESSONS[0];
  return (
    <main className="learn-home">
      <section className="hero">
        <div className="next-kicker">A self-paced course</div>
        <h1>Learn the audit on Kestrel Valley</h1>
        <p>One module per audit area of <b>Kestrel Valley Cycle Supply</b>, a bicycle-parts distributor
          that keeps its books in QuickBooks Online. Each module has four steps: <b>the idea</b>, the work
          <b> by hand</b> on Kestrel's own files, the same work <b>in Noesi</b>, and a <b>compare</b> step
          that shows the answer key once you have written your answers, and says plainly what Noesi
          cannot do.</p>
        <div className="hero-actions">
          <a className="primary" href={`#/learn/${next.n}`}>{done ? `Continue with module ${next.n}` : `Start module ${LESSONS[0].n}`}</a>
          <a className="secondary" href="#/learn/documents">See the documents</a>
          <a className="secondary" href="#/learn/trace">Follow a number</a>
          <a className="secondary" href="#/learn/excel">Excel for audit</a>
          <span className="muted">{done} of {LESSONS.length} modules complete · {COMING.length} coming</span>
        </div>
        <div className="progress big"><div style={{ width: `${(100 * done) / LESSONS.length}%` }} /></div>
      </section>

      {PHASES.map((phase) => (
        <section key={phase} className="phase">
          <h2>{phase}</h2>
          <div className="lesson-grid">
            {ALL.filter((item) => phaseOf(item) === phase).map((item) => {
              if (item.kind === "coming") {
                const c = item.coming;
                return (
                  <div key={c.n} className="lesson-tile coming">
                    <span className="tile-n">{c.n}</span>
                    <span className="tile-title">{c.title}</span>
                    <span className="tile-meta"><span className="muted">coming</span></span>
                  </div>
                );
              }
              const l = item.lesson;
              const p = progress[l.slug];
              return (
                <a key={l.slug} className={`lesson-tile ${p?.done ? "done" : ""}`} href={`#/learn/${l.n}`}>
                  <span className="tile-n">{p?.done ? "✓" : l.n}</span>
                  <span className="tile-title">{l.title}</span>
                  <span className="tile-q">{l.question}</span>
                  <span className="tile-meta">
                    <span className={`cov ${l.noesi.coverage}`}>{COVERAGE_LABEL[l.noesi.coverage]}</span>
                    <span className="muted">~{l.minutes} min</span>
                  </span>
                </a>
              );
            })}
          </div>
        </section>
      ))}

      <section className="phase">
        <h2>Fraud</h2>
        <div className="lesson-grid">
          <a className="lesson-tile" href="#/learn/fraud">
            <span className="tile-n">F</span>
            <span className="tile-title">Fraud at Kestrel</span>
            <span className="tile-q">Why fraud happens, fraud risk assessment, and the schemes planted in
              Kestrel's records: a twin vendor, a shell-like vendor, split bills, a ghost employee, an
              owner's weekend entry, and cash counted twice.</span>
            <span className="tile-meta"><span className="muted">{FRAUD_LESSONS.length} lessons</span></span>
          </a>
        </div>
      </section>

      <p className="muted fine">Original teaching material on the fictional Kestrel Valley case
        (<code>case-studies/kestrel-valley-cycle</code>). Every figure in the compare steps is the case's
        answer key, checked against the Workbench by <code>finish_line_check.py</code>. Standards
        citations anchor further reading; they are not a substitute for the standards.</p>
    </main>
  );
}

/** A set of lessons with its own numbering, home and labels. */
interface Track {
  lessons: Lesson[];
  base: string;      // hash prefix of a lesson: `${base}/${n}`
  home: string;
  homeLabel: string;
  prefix: string;    // shown before the lesson number: "" or "F"
  noun: string;      // "Module" or "Lesson"
  total: number;
  end: { href: string; label: string };
}
const MAIN_TRACK: Track = {
  lessons: LESSONS, base: "#/learn", home: "#/learn", homeLabel: "Course", prefix: "", noun: "Module",
  total: ALL.length, end: { href: "#/learn/map", label: "Course map →" },
};
const FRAUD_TRACK: Track = {
  lessons: FRAUD_LESSONS, base: "#/learn/fraud", home: "#/learn/fraud", homeLabel: "Fraud track",
  prefix: "F", noun: "Lesson", total: FRAUD_LESSONS.length,
  end: { href: "#/learn/fraud", label: "Fraud track →" },
};

function LessonPage({ lesson, track, progress, onUpdate }: {
  lesson: Lesson; track: Track; progress?: Entry; onUpdate: (c: Partial<Entry>) => void;
}) {
  const total = lesson.sections.length;
  const read = Math.min(progress?.read ?? 1, total) || 1;
  const answers = progress?.answers ?? {};
  const allAnswered = lesson.check.every((_, i) => answers[i] !== undefined);
  const finishedReading = read >= total;
  const submitted = !!progress?.submitted;
  const index = track.lessons.indexOf(lesson);
  const prev = track.lessons[index - 1];
  const next = track.lessons[index + 1];
  const label = (l: Lesson) => `${track.noun} ${track.prefix}${l.n}`;

  return (
    <main className="lesson">
      <nav className="crumbs">
        <a href={track.home}>{track.homeLabel}</a> › {lesson.phase} › {label(lesson)}
      </nav>
      <header className="lesson-head">
        <div className="next-kicker">{label(lesson)} of {track.total} · {lesson.phase} · ~{lesson.minutes} min</div>
        <h1>{lesson.title}</h1>
        <p className="big-q">{lesson.question}</p>
        <div className="objectives">
          <b>You will be able to</b>
          <ul>{lesson.objectives.map((o) => <li key={o}>{o}</li>)}</ul>
        </div>
        <div className="step-dots" aria-label={`${read} of ${total} sections read`}>
          {lesson.sections.map((s, i) => <span key={s.heading} className={i < read ? "on" : ""} title={s.heading} />)}
          <span className={allAnswered ? "on quiz" : "quiz"} title="Check your understanding" />
          <span className={submitted ? "on quiz" : "quiz"} title="By hand" />
          <span className={progress?.done ? "on noesi" : "noesi"} title="Compare with the key" />
        </div>
      </header>

      <LessonVideo title={lesson.title} video={lesson.video} />

      <h2 className="step-title"><span className="step-k">Step 1</span> The idea</h2>
      {lesson.sections.slice(0, read).map((section, i) => (
        <section key={section.heading} className="lesson-section">
          <h2><span className="sec-n">{i + 1}</span>{section.heading}</h2>
          {section.blocks.map((block, j) => <BlockView key={j} block={block} />)}
        </section>
      ))}

      {!finishedReading && (
        <button className="primary continue" onClick={() => onUpdate({ read: read + 1 })}>
          Continue: {lesson.sections[read].heading} →
        </button>
      )}

      {finishedReading && (
        <>
          <section className="lesson-section standards">
            <h2>Standards behind this module</h2>
            <table><tbody>
              {lesson.standards.map(([ref, what]) => <tr key={ref}><th>{ref}</th><td>{what}</td></tr>)}
            </tbody></table>
          </section>

          <section className="lesson-section quiz">
            <h2>Check your understanding</h2>
            {lesson.check.map((q, i) => (
              <QuestionView key={q.q} n={i + 1} question={q} chosen={answers[i]}
                            onChoose={(choice) => onUpdate({ answers: { ...answers, [i]: choice } })} />
            ))}
          </section>

          <h2 className="step-title"><span className="step-k">Step 2</span> By hand</h2>
          <ByHand key={lesson.slug} lesson={lesson} progress={progress} onUpdate={onUpdate} />

          <h2 className="step-title"><span className="step-k">Step 3</span> In Noesi</h2>
          <section className="lesson-section task">
            <p>Run the same work in the Workbench and read what it finds. Procedures and screens for this
              module: {lesson.inNoesi.procedures.map((p, i) => <Fragment key={p}>{i ? ", " : ""}<code>{p}</code></Fragment>)}.</p>
            <ol>{lesson.inNoesi.steps.map((s) => <li key={s}><Rich text={s} /></li>)}</ol>
          </section>

          <h2 className="step-title"><span className="step-k">Step 4</span> Compare with the key</h2>
          {submitted ? <Compare lesson={lesson} mine={progress?.mine ?? {}} />
            : <p className="muted locked">Write down your answers in step 2 and press “Show the key”.
                The key stays hidden until you do.</p>}

          <div className="lesson-foot">
            {prev ? <a className="secondary" href={`${track.base}/${prev.n}`}>← {label(prev)}</a> : <span />}
            {submitted && allAnswered && !progress?.done && (
              <button className="primary" onClick={() => onUpdate({ done: true })}>Mark {track.noun.toLowerCase()} complete</button>
            )}
            {progress?.done && <span className="done-flag">✓ {track.noun} complete</span>}
            {next ? <a className="secondary" href={`${track.base}/${next.n}`}>{label(next)} →</a>
              : <a className="secondary" href={track.end.href}>{track.end.label}</a>}
          </div>
        </>
      )}
    </main>
  );
}

function ByHand({ lesson, progress, onUpdate }: {
  lesson: Lesson; progress?: Entry; onUpdate: (c: Partial<Entry>) => void;
}) {
  const [draft, setDraft] = useState<Record<number, string>>(progress?.mine ?? {});
  const submitted = !!progress?.submitted;
  const written = lesson.byHand.asks.every((_, i) => (draft[i] ?? "").trim() !== "");
  return (
    <section className="lesson-section task">
      <p><Rich text={lesson.byHand.intro} /></p>
      <p className="small"><b>Files</b> (in <code>case-studies/kestrel-valley-cycle/data</code>):{" "}
        {lesson.byHand.files.map((f, i) => <Fragment key={f}>{i ? ", " : ""}<code>{f}</code></Fragment>)}</p>
      <ol>{lesson.byHand.steps.map((s) => <li key={s}><Rich text={s} /></li>)}</ol>
      <div className="answers">
        <b>Your answers</b>
        {lesson.byHand.asks.map((ask, i) => (
          <label key={ask.label} className="answer">
            <span>{ask.label}</span>
            <input type="text" value={draft[i] ?? ""} disabled={submitted}
                   onChange={(e) => setDraft({ ...draft, [i]: e.target.value })} />
          </label>
        ))}
      </div>
      {submitted ? (
        <p className="muted small">Answers saved.{" "}
          <button className="link" onClick={() => onUpdate({ submitted: false })}>Change them</button></p>
      ) : (
        <button className="primary" disabled={!written}
                onClick={() => onUpdate({ mine: draft, submitted: true })}>Show the key</button>
      )}
    </section>
  );
}

function Compare({ lesson, mine }: { lesson: Lesson; mine: Record<number, string> }) {
  const rows = lesson.keyLines
    ? lesson.keyLines.map(([module, item]) => findRow(module, item)).filter((r): r is NonNullable<typeof r> => !!r)
    : moduleRows(lesson.keyModule);
  const { noesi } = lesson;
  return (
    <>
      <section className="lesson-section">
        <h2>Your answers, Noesi, and the key</h2>
        <div className="table-wrap"><table>
          <thead><tr><th>Question</th><th>You</th><th>Noesi</th><th>Key</th></tr></thead>
          <tbody>{lesson.byHand.asks.map((ask, i) => {
            const row = findRow(ask.module ?? lesson.keyModule, ask.row);
            const key = (ask.key ? keyAt(ask.key) : row?.key === "yes" ? row.item : row?.key) ?? "?";
            const noesiValue = !row ? "?" : row.status === "not in Noesi" ? "not in Noesi"
              : row.status === "match" ? (ask.key ? "the same" : row.noesi) : row.noesi;
            const ok = agrees(mine[i] ?? "", key);
            return (
              <tr key={ask.label}>
                <td>{ask.label}</td>
                <td className={ok ? "agree" : ""}>{mine[i] ?? ""}{ok ? " ✓" : ""}</td>
                <td className={row?.status === "match" ? "" : "gap"}>{noesiValue}</td>
                <td><b>{key}</b></td>
              </tr>
            );
          })}</tbody>
        </table></div>
        <p className="muted small">A ✓ marks an answer that reads the same as the key. Where yours differs,
          find out why before you move on: the key is worked from the same files.</p>
      </section>

      <section className="lesson-section">
        <h2>Everything the key checks in this {lesson.keyLines ? "lesson" : "module"}</h2>
        <div className="table-wrap"><table>
          <thead><tr><th>Line of the key</th><th>Key</th><th>Noesi</th><th /></tr></thead>
          <tbody>{rows.map((r) => (
            <tr key={r.item}>
              <td>{r.item}{r.why && <div className="small muted">{r.why}</div>}</td>
              <td>{r.key}</td>
              <td>{r.noesi}</td>
              <td className={r.status === "match" ? "agree" : "gap"}>{STATUS_LABEL[r.status]}</td>
            </tr>
          ))}</tbody>
        </table></div>
        <p className="muted small">“yes” means the line holds as written. The Workbench values are from the
          demo engagement, as <code>finish_line_check.py</code> produced them.</p>
      </section>

      <section className={`noesi-box ${noesi.coverage}`}>
        <div className="noesi-head">
          <span className="noesi-mark">In Noesi</span>
          <span className={`cov ${noesi.coverage}`}>{COVERAGE_LABEL[noesi.coverage]}</span>
        </div>
        <p className="noesi-summary">{noesi.summary}</p>
        <div className="noesi-cols">
          <div>
            <h3>What it does for this step</h3>
            <ul>{noesi.does.map((d) => <li key={d}><Rich text={d} /></li>)}</ul>
            <h3>Where</h3>
            <ul>{noesi.where.map((w) => <li key={w}>{w}</li>)}</ul>
          </div>
          <div>
            <h3>What Noesi cannot do</h3>
            <ul className="not">{noesi.doesNot.map((d) => <li key={d}><Rich text={d} /></li>)}</ul>
          </div>
        </div>
      </section>
    </>
  );
}

function BlockView({ block }: { block: Block }) {
  if ("p" in block) return <p><Rich text={block.p} /></p>;
  if ("list" in block) return <ul>{block.list.map((x) => <li key={x}><Rich text={x} /></li>)}</ul>;
  if ("steps" in block) return <ol className="steps">{block.steps.map((x) => <li key={x}><Rich text={x} /></li>)}</ol>;
  if ("terms" in block) {
    return (
      <dl className="terms">
        {block.terms.map(([term, def]) => (
          <div key={term}><dt>{term}</dt><dd><Rich text={def} /></dd></div>
        ))}
      </dl>
    );
  }
  if ("table" in block) {
    return (
      <div className="table-wrap"><table>
        <thead><tr>{block.table.head.map((h) => <th key={h}>{h}</th>)}</tr></thead>
        <tbody>{block.table.rows.map((row, i) => (
          <tr key={i}>{row.map((cell, j) => <td key={j}><Rich text={cell} /></td>)}</tr>
        ))}</tbody>
      </table></div>
    );
  }
  if ("kestrel" in block) {
    return <aside className="callout kestrel"><div className="callout-k">At Kestrel</div><Rich text={block.kestrel} /></aside>;
  }
  return <aside className="callout watch"><div className="callout-k">Watch for</div><Rich text={block.watch} /></aside>;
}

function QuestionView({ n, question, chosen, onChoose }: {
  n: number; question: Question; chosen?: number; onChoose: (i: number) => void;
}) {
  const answered = chosen !== undefined;
  return (
    <div className="question">
      <p className="q"><b>{n}.</b> {question.q}</p>
      <div className="options" role="radiogroup">
        {displayOrder(question.options.join("|"), question.options.length).map((i) => {
          const option = question.options[i];
          const cls = !answered ? "" : i === question.answer ? "right" : i === chosen ? "wrong" : "dim";
          return (
            <button key={option} role="radio" aria-checked={chosen === i} className={`option ${cls}`}
                    disabled={answered} onClick={() => onChoose(i)}>{option}</button>
          );
        })}
      </div>
      {answered && (
        <p className={`why ${chosen === question.answer ? "right" : "wrong"}`}>
          <b>{chosen === question.answer ? "Correct." : "Not quite."}</b> {question.why}
        </p>
      )}
    </div>
  );
}

function CourseMap({ progress }: { progress: Progress }) {
  return (
    <main className="lesson">
      <nav className="crumbs"><a href="#/learn">Course</a> › Course map</nav>
      <header className="lesson-head">
        <div className="next-kicker">Summary</div>
        <h1>The Kestrel audit, and where Noesi fits</h1>
        <p className="big-q">All {ALL.length} modules: the question each answers, the standards behind it,
          and how much of it the Workbench carries.</p>
      </header>
      <div className="table-wrap"><table className="map">
        <thead><tr><th>#</th><th>Module</th><th>The question</th><th>Key standards</th><th>Noesi</th></tr></thead>
        <tbody>
          {ALL.map((item) => {
            if (item.kind === "coming") {
              const c = item.coming;
              return (
                <tr key={c.n} className="coming">
                  <td>{c.n}</td>
                  <td>{c.title}<div className="muted small">{c.phase}</div></td>
                  <td colSpan={3}><span className="cov none">coming</span>
                    <div className="small muted">{c.waitsFor}</div></td>
                </tr>
              );
            }
            const l = item.lesson;
            return (
              <tr key={l.slug} className={progress[l.slug]?.done ? "done" : ""}>
                <td>{progress[l.slug]?.done ? "✓" : l.n}</td>
                <td><a href={`#/learn/${l.n}`}>{l.title}</a><div className="muted small">{l.phase}</div></td>
                <td>{l.question}</td>
                <td className="small">{l.standards.map(([ref]) => ref).join("; ")}</td>
                <td><span className={`cov ${l.noesi.coverage}`}>{COVERAGE_LABEL[l.noesi.coverage]}</span>
                  <div className="small muted">{l.noesi.summary}</div></td>
              </tr>
            );
          })}
        </tbody>
      </table></div>
      <section className="lesson-section">
        <h2>How to read this</h2>
        <p>Noesi is strongest where the audit is <b>records and judgment trails</b>: whole-population tests,
          recomputation, tie-outs, and the completion schedules. It is absent where the audit is
          <b> physical or external</b>: observing, confirming with outsiders, inspecting documents, and the
          partner's judgment. The modules marked “coming” wait for the Workbench to load QuickBooks'
          own exports for their files; they will be written once it does.</p>
      </section>
    </main>
  );
}

function FraudHome({ progress }: { progress: Progress }) {
  const done = FRAUD_LESSONS.filter((l) => progress[l.slug]?.done).length;
  const next = FRAUD_LESSONS.find((l) => !progress[l.slug]?.done) ?? FRAUD_LESSONS[0];
  return (
    <main className="learn-home">
      <nav className="crumbs"><a href="#/learn">Course</a> › Fraud at Kestrel</nav>
      <section className="hero">
        <div className="next-kicker">The fraud track</div>
        <h1>Fraud at Kestrel</h1>
        <p>How occupational fraud works and how it is found, worked on the schemes planted in Kestrel's
          records. Each lesson has the same four steps as the modules: the idea, by hand, in Noesi, and
          compare with the key. A finding is always a lead, never proof of fraud.</p>
        <div className="hero-actions">
          <a className="primary" href={`#/learn/fraud/${next.n}`}>{done ? `Continue with lesson F${next.n}` : "Start lesson F1"}</a>
          <a className="secondary" href="#/learn/excel">Excel for audit</a>
          <a className="secondary" href="#/learn/documents">The documents</a>
          <span className="muted">{done} of {FRAUD_LESSONS.length} lessons complete</span>
        </div>
        <div className="progress big"><div style={{ width: `${(100 * done) / FRAUD_LESSONS.length}%` }} /></div>
      </section>

      <section className="phase">
        <h2>Lessons</h2>
        <div className="lesson-grid">
          {FRAUD_LESSONS.map((l) => {
            const p = progress[l.slug];
            return (
              <a key={l.slug} className={`lesson-tile ${p?.done ? "done" : ""}`} href={`#/learn/fraud/${l.n}`}>
                <span className="tile-n">{p?.done ? "✓" : `F${l.n}`}</span>
                <span className="tile-title">{l.title}</span>
                <span className="tile-q">{l.question}</span>
                <span className="tile-meta">
                  <span className={`cov ${l.noesi.coverage}`}>{COVERAGE_LABEL[l.noesi.coverage]}</span>
                  <span className="muted">~{l.minutes} min</span>
                </span>
              </a>
            );
          })}
        </div>
      </section>

      <p className="muted fine">What Kestrel cannot teach: it has no payments approved by the person who
        entered them, and no money sent out to a related party and brought back. Those schemes are not
        planted in this case, and the track does not invent them. Original teaching material; it does not
        reproduce ACFE text.</p>
    </main>
  );
}
