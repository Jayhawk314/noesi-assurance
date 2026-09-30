// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** "Excel for audit": guided exercises on the Kestrel case files, in the
 *  Harborline page's layout. The answers are read from the answer key
 *  (excelData.ts); do each in Excel before opening the answer. */

import { EXERCISES } from "./excelData";

export function ExcelAudit() {
  return (
    <main className="lesson">
      <nav className="crumbs"><a href="#/learn">Course</a> › Excel for audit</nav>
      <header className="lesson-head">
        <div className="next-kicker">Hands-on · about 3 hours in total</div>
        <h1>Excel for audit</h1>
        <p className="big-q">Can I run the audit tests myself in a spreadsheet, and get the same answers as Noesi?</p>
        <p>{EXERCISES.length} exercises on the Kestrel files, each teaching one Excel skill through one audit test.
          Do each in Excel first, check your answer, then compare with Noesi. That order, judgment before the
          tool, is how the course is meant to be worked.</p>
      </header>

      <section className="lesson-section">
        <h2>Setting up, free</h2>
        <ol className="steps">
          <li>Go to <b>office.com</b>, sign in with an Outlook (Microsoft) account, and open <b>Excel</b>. Excel on the web is free and does everything these exercises need.</li>
          <li>Upload the files from <code>case-studies/kestrel-valley-cycle/data/</code> (or download them from the GitHub repository). If Excel on the web limits editing of a .csv file, save a copy as .xlsx and work in that.</li>
          <li>The QuickBooks exports (<code>quickbooks/*.xlsx</code>) open as they came from QuickBooks: a few title lines, then the header row. Column letters below assume each file's own column order.</li>
        </ol>
        <p className="muted small">Google Sheets and LibreOffice Calc also work; XLOOKUP and COUNTIFS exist in both, with small differences in menus.</p>
      </section>

      {EXERCISES.map((ex, i) => (
        <section key={ex.skill} className="lesson-section">
          <h2><span className="sec-n">{i + 1}</span>{ex.skill}</h2>
          <p><b>Audit test:</b> {ex.audit}{ex.audit.endsWith("?") ? "" : "."} <span className="muted">File: <code>{ex.file}</code></span></p>
          <ol className="steps">{ex.steps.map((s) => <li key={s}>{s}</li>)}</ol>
          {ex.formula && <p><b>Formula:</b> <code>{ex.formula}</code></p>}
          <details className="finding-evidence">
            <summary>Check your answer</summary>
            <p>{ex.answer}</p>
            <p className="muted"><b>Compare with Noesi:</b> {ex.noesi} <a href={`#/learn/${ex.module}`}>Module {ex.module}</a></p>
          </details>
        </section>
      ))}

      <p className="muted fine">Answers are the case's answer key. The web version of Excel cannot run macros
        (VBA) or Power Pivot; nothing here needs them.</p>
      <div className="lesson-foot">
        <a className="secondary" href="#/learn">← Course</a>
        <a className="secondary" href="#/learn/documents">The documents →</a>
      </div>
    </main>
  );
}
