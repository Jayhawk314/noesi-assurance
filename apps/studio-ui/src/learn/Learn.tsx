// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** "Learn the audit": ten lessons from acceptance to the report.
 *
 *  Routes (hash): #/learn (course home), #/learn/<n> (a lesson),
 *  #/learn/map (the process-to-Noesi map). Static content; needs no
 *  session. Progress is a per-browser convenience in localStorage and the
 *  page works without it. */

import { Fragment, useEffect, useMemo, useState } from "react";
import { Documents } from "./Documents";
import { Trace } from "./Trace";
import { LESSONS } from "./lessons";
import { displayOrder } from "./shuffle";
import { Block, Lesson, Question } from "./types";

type Progress = Record<string, { read: number; answers: Record<number, number>; done: boolean }>;
const STORE = "noesi-learn-progress-v1";

function loadProgress(): Progress {
  try { return JSON.parse(localStorage.getItem(STORE) || "{}") as Progress; } catch { return {}; }
}
function saveProgress(p: Progress) {
  try { localStorage.setItem(STORE, JSON.stringify(p)); } catch { /* private mode: in-memory only */ }
}

/** **bold** only; everything else is plain text (no HTML injection). */
function Rich({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return <>{parts.map((part, i) =>
    part.startsWith("**") ? <strong key={i}>{part.slice(2, -2)}</strong>
      : part.startsWith("`") ? <code key={i}>{part.slice(1, -1)}</code>
      : <Fragment key={i}>{part}</Fragment>)}</>;
}

const PHASES: Lesson["phase"][] = ["Planning", "Fieldwork", "Completion"];
const COVERAGE_LABEL = { full: "Noesi covers this step", partial: "Noesi covers part of this", none: "Not in Noesi yet" };

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

export function Learn({ route, standalone = false }: { route: string; standalone?: boolean }) {
  const [progress, setProgress] = useState<Progress>(loadProgress);
  const update = (slug: string, change: Partial<Progress[string]>) => {
    setProgress((prev) => {
      const current = prev[slug] ?? { read: 0, answers: {}, done: false };
      const next = { ...prev, [slug]: { ...current, ...change } };
      saveProgress(next);
      return next;
    });
  };

  const parts = route.split("/").filter(Boolean); // ["learn", "3"]
  const target = parts[1];
  const lesson = LESSONS.find((l) => String(l.n) === target);

  useEffect(() => { window.scrollTo(0, 0); }, [route]);

  return (
    <div className="studio learn" onClickCapture={followHashLinks}>
      <header className="bar">
        <a className="brand" href="#/learn">Noesi <b>Learn</b></a>
        <span className="engagement-name">The audit, from acceptance to the report</span>
        <span className="spacer" />
        <a className="to-workbench" href="#/learn/documents">The documents</a>
        <a className="to-workbench" href="#/learn/trace">Follow a number</a>
        <a className="to-workbench" href="#/learn/map">Course map</a>
        {!standalone && <a className="to-workbench" href="#/">Studio ↗</a>}
        {!standalone && <a className="to-workbench" href="/">Workbench ↗</a>}
      </header>
      {target === "map" ? <CourseMap progress={progress} />
        : target === "documents" ? <Documents />
        : target === "trace" ? <Trace />
        : lesson ? <LessonPage lesson={lesson} progress={progress[lesson.slug]}
                               onUpdate={(c) => update(lesson.slug, c)} />
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
        <h1>Learn the audit by doing one</h1>
        <p>Ten lessons follow one financial-statement audit from the decision to accept the client
          to the signed report — the order every integrated audit case uses. Each lesson teaches the
          step, checks your understanding as you go, gives you a hands-on task on the
          <b> Harborline Marine</b> case files, and ends with a reminder of what Noesi does for that
          step — and what it does not.</p>
        <div className="hero-actions">
          <a className="primary" href={`#/learn/${next.n}`}>{done ? `Continue with lesson ${next.n}` : "Start lesson 1"}</a>
          <a className="secondary" href="#/learn/documents">See the documents</a>
          <a className="secondary" href="#/learn/trace">Follow a number</a>
          <span className="muted">{done} of {LESSONS.length} lessons complete</span>
        </div>
        <div className="progress big"><div style={{ width: `${(100 * done) / LESSONS.length}%` }} /></div>
      </section>

      {PHASES.map((phase) => (
        <section key={phase} className="phase">
          <h2>{phase}</h2>
          <div className="lesson-grid">
            {LESSONS.filter((l) => l.phase === phase).map((l) => {
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

      <p className="muted fine">The course is original teaching material built on the AICPA clarified
        standards (AU-C sections) and Noesi's own fictional Harborline Marine case. Standards citations
        anchor further reading; they are not a substitute for the standards. Research notes and sources:
        <code> docs/learn/CURRICULUM.md</code>.</p>
    </main>
  );
}

function LessonPage({ lesson, progress, onUpdate }: {
  lesson: Lesson; progress?: Progress[string]; onUpdate: (c: Partial<Progress[string]>) => void;
}) {
  const total = lesson.sections.length;
  const read = Math.min(progress?.read ?? 1, total) || 1;
  const answers = progress?.answers ?? {};
  const allAnswered = lesson.check.every((_, i) => answers[i] !== undefined);
  const finishedReading = read >= total;
  const index = LESSONS.indexOf(lesson);
  const prev = LESSONS[index - 1];
  const next = LESSONS[index + 1];

  return (
    <main className="lesson">
      <nav className="crumbs">
        <a href="#/learn">Course</a> › {lesson.phase} › Lesson {lesson.n}
      </nav>
      <header className="lesson-head">
        <div className="next-kicker">Lesson {lesson.n} of {LESSONS.length} · {lesson.phase} · ~{lesson.minutes} min</div>
        <h1>{lesson.title}</h1>
        <p className="big-q">{lesson.question}</p>
        <div className="objectives">
          <b>You will be able to</b>
          <ul>{lesson.objectives.map((o) => <li key={o}>{o}</li>)}</ul>
        </div>
        <div className="step-dots" aria-label={`${read} of ${total} sections read`}>
          {lesson.sections.map((s, i) => <span key={s.heading} className={i < read ? "on" : ""} title={s.heading} />)}
          <span className={allAnswered ? "on quiz" : "quiz"} title="Check your understanding" />
          <span className={progress?.done ? "on noesi" : "noesi"} title="In Noesi" />
        </div>
      </header>

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
            <h2>Standards behind this lesson</h2>
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

          <section className="lesson-section task">
            <h2>Do it: {lesson.task.title}</h2>
            <p><Rich text={lesson.task.intro} /></p>
            <ol>{lesson.task.steps.map((s) => <li key={s}><Rich text={s} /></li>)}</ol>
            <p className="deliver"><b>Deliver:</b> {lesson.task.deliver}</p>
          </section>

          {allAnswered ? (
            <NoesiBox lesson={lesson} />
          ) : (
            <p className="muted locked">Answer the questions above to unlock the Noesi reminder for this lesson.</p>
          )}

          <div className="lesson-foot">
            {prev ? <a className="secondary" href={`#/learn/${prev.n}`}>← Lesson {prev.n}</a> : <span />}
            {allAnswered && !progress?.done && (
              <button className="primary" onClick={() => onUpdate({ done: true })}>Mark lesson complete</button>
            )}
            {progress?.done && <span className="done-flag">✓ Lesson complete</span>}
            {next ? <a className="secondary" href={`#/learn/${next.n}`}>Lesson {next.n} →</a>
              : <a className="secondary" href="#/learn/map">Course map →</a>}
          </div>
        </>
      )}
    </main>
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
  if ("harborline" in block) {
    return <aside className="callout harborline"><div className="callout-k">At Harborline</div><Rich text={block.harborline} /></aside>;
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

function NoesiBox({ lesson }: { lesson: Lesson }) {
  const { noesi } = lesson;
  return (
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
        </div>
        <div>
          <h3>Where</h3>
          <ul>{noesi.where.map((w) => <li key={w}>{w}</li>)}</ul>
          <h3>What it does not do</h3>
          <ul className="not">{noesi.doesNot.map((d) => <li key={d}><Rich text={d} /></li>)}</ul>
        </div>
      </div>
      {noesi.tryIt && <p className="try"><b>Try it:</b> <Rich text={noesi.tryIt} /></p>}
    </section>
  );
}

function CourseMap({ progress }: { progress: Progress }) {
  const rows = useMemo(() => LESSONS, []);
  return (
    <main className="lesson">
      <nav className="crumbs"><a href="#/learn">Course</a> › Course map</nav>
      <header className="lesson-head">
        <div className="next-kicker">Summary</div>
        <h1>The audit process, and where Noesi fits</h1>
        <p className="big-q">One view of all ten steps: the question each answers, the standards behind it,
          and how much of it the system carries.</p>
      </header>
      <div className="table-wrap"><table className="map">
        <thead><tr><th>#</th><th>Step</th><th>The question</th><th>Key standards</th><th>Noesi</th></tr></thead>
        <tbody>
          {rows.map((l) => (
            <tr key={l.slug} className={progress[l.slug]?.done ? "done" : ""}>
              <td>{progress[l.slug]?.done ? "✓" : l.n}</td>
              <td><a href={`#/learn/${l.n}`}>{l.title}</a><div className="muted small">{l.phase}</div></td>
              <td>{l.question}</td>
              <td className="small">{l.standards.map(([ref]) => ref).join("; ")}</td>
              <td><span className={`cov ${l.noesi.coverage}`}>{COVERAGE_LABEL[l.noesi.coverage]}</span>
                <div className="small muted">{l.noesi.summary}</div></td>
            </tr>
          ))}
        </tbody>
      </table></div>
      <section className="lesson-section">
        <h2>How to read this</h2>
        <p>Noesi is strongest where the audit is <b>records and judgment trails</b>: planning decisions,
          accounts-payable testing across whole populations, dispositions, review, and completion. It is
          absent where the audit is <b>physical or external</b>: confirmations, inventory counts, and
          inspecting documents. The course teaches every step because the audit needs every step; the
          map shows honestly which ones the tool helps with today.</p>
      </section>
    </main>
  );
}
