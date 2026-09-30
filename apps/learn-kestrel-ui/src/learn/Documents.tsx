// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** "The documents": what an auditor actually reads at Kestrel, where the
 *  figure sits, and what to check. One purchase followed from the vendor list
 *  to the misstatement schedule, then the year-end records. Same layout as
 *  the Harborline documents page; every figure comes from the case files. */

import { Fragment } from "react";
import { DUPLICATE } from "./records";
import { CHAIN, Field, PAPERS, Paper, Row } from "./papers";

function Mark({ n }: { n?: number }) {
  return n ? <span className="pmark" aria-label={`note ${n}`}>{n}</span> : null;
}

function FieldLine({ field }: { field: Field }) {
  return (
    <div className={`pfield ${field.tone ?? ""}`}>
      <span className="plabel">{field.label}</span>
      <span className="pvalue">{field.value}<Mark n={field.mark} /></span>
    </div>
  );
}

function PaperView({ paper }: { paper: Paper }) {
  const numericFrom = paper.table?.numericFrom ?? 99;
  return (
    <div className="paper">
      <div className="paper-head">
        <div>
          <div className="issuer">{paper.issuer}</div>
          {paper.issuerLine && <div className="issuer-line">{paper.issuerLine}</div>}
        </div>
        <div className="doc-title">
          {paper.docTitle}
          {paper.docNumber && <div className="doc-number">{paper.docNumber}</div>}
        </div>
      </div>
      {paper.meta && <div className="pmeta">{paper.meta.map((f) => <FieldLine key={f.label} field={f} />)}</div>}
      {paper.table && (
        <div className="table-wrap"><table className="ptable">
          <thead><tr>{paper.table.head.map((h, i) => (
            <th key={i} className={i >= numericFrom ? "num" : ""}>{h}</th>
          ))}</tr></thead>
          <tbody>{paper.table.rows.map((row: Row, i) => (
            <tr key={i} className={row.highlight ?? ""}>
              {row.cells.map((cell, j) => (
                <td key={j} className={j >= numericFrom ? "num" : ""}>
                  {cell}{j === row.cells.length - 1 && <Mark n={row.mark} />}
                </td>
              ))}
            </tr>
          ))}</tbody>
        </table></div>
      )}
      {paper.totals && <div className="ptotals">{paper.totals.map((f) => <FieldLine key={f.label} field={f} />)}</div>}
      {paper.signatures && (
        <div className="psigs">{paper.signatures.map((f) => (
          <div key={f.label} className={`psig ${f.tone ?? ""}`}>
            <div className="sig-line">{f.value}<Mark n={f.mark} /></div>
            <div className="sig-label">{f.label}</div>
          </div>
        ))}</div>
      )}
      {paper.footer && <div className="pfooter">{paper.footer}</div>}
    </div>
  );
}

export function Documents() {
  const trail = PAPERS.filter((p) => p.group === "trail");
  const yearend = PAPERS.filter((p) => p.group === "yearend");
  return (
    <main className="lesson documents">
      <nav className="crumbs"><a href="#/learn">Course</a> › The documents</nav>
      <header className="lesson-head">
        <div className="next-kicker">Reference · the paper trail</div>
        <h1>The documents you will read, and where the figures are</h1>
        <p className="big-q">Follow one Kestrel purchase from the vendor list to the misstatement schedule,
          then read the year-end records the audit turns on.</p>
        <p>Kestrel keeps its books in QuickBooks Online, so its “documents” are mostly QuickBooks reports and
          the client's and team's schedules. Every figure here is read from the case files. Numbered markers
          point at the figure to look at; the notes beside each document say what to do with it.</p>
      </header>

      <section className="lesson-section">
        <h2>How auditors work a document trail</h2>
        <div className="direction">
          <div><b>Vouch</b> — start from the <b>record</b> (the ledger, the payment list) and go <b>back</b> to
            the source document. Proves the recorded item is real → <b>occurrence / existence</b>.</div>
          <div><b>Trace</b> — start from the <b>source document</b> (the order, the invoice) and go <b>forward</b> to
            the record. Proves real items were recorded → <b>completeness</b>.</div>
        </div>
        <p className="muted small">Common tick marks (firms vary): ✓ agreed to source · F footed · CF cross-footed ·
          ⓥ vouched · ⓣ traced · ✗ exception, see note.</p>
      </section>

      <nav className="chain" aria-label="The purchase trail">
        {CHAIN.map((step, i) => (
          <Fragment key={step.id}>
            {i > 0 && <span className="chain-link" title={step.test}>→<span className="chain-test">{step.test}</span></span>}
            <a className="chain-step" href={`#doc-${step.id}`} onClick={(e) => { e.preventDefault();
              document.getElementById(`doc-${step.id}`)?.scrollIntoView({ behavior: "smooth" }); }}>
              <span className="chain-n">{i + 1}</span>{step.label}
            </a>
          </Fragment>
        ))}
      </nav>
      <p className="muted small chain-caption">Each arrow names what compares the two documents. What no test can
        check: whether an invoice is genuine, whether the goods arrived, and whether a supplier will refund.
        That stays with your eyes and your questions.</p>

      <h2 className="group-title">One purchase, paid twice — the case data</h2>
      <p className="muted">Moraine Cycle Components, invoice {DUPLICATE.num}. Watch the vendor names.</p>
      {trail.map((paper) => <DocSection key={paper.id} paper={paper} />)}

      <h2 className="group-title">The year-end records</h2>
      <p className="muted">The reconciliation, payables, payroll, fixed assets, the month after year end, and
        management's representations.</p>
      {yearend.map((paper) => <DocSection key={paper.id} paper={paper} />)}

      <div className="lesson-foot">
        <a className="secondary" href="#/learn">← Course</a>
        <a className="secondary" href="#/learn/trace">Follow the duplicate →</a>
        <a className="secondary" href="#/learn/5">Module 5: Payables →</a>
      </div>
    </main>
  );
}

function DocSection({ paper }: { paper: Paper }) {
  return (
    <section className="doc" id={`doc-${paper.id}`}>
      <div className="doc-kicker">
        <span className="doc-n">{paper.n}</span>
        <b>{paper.kind}</b>
        <span className="cov full">Case data</span>
        <span className="muted small">Source: {paper.source}</span>
      </div>
      <div className="doc-grid">
        <PaperView paper={paper} />
        <aside className="doc-notes">
          <h3>What to look at</h3>
          {paper.notes.map((note) => (
            <div key={note.title} className="dnote">
              {note.mark ? <span className="pmark">{note.mark}</span>
                : <span className="pmark general" title="General note">•</span>}
              <div>
                <b>{note.title}</b>{note.assertion && <span className="assertion">{note.assertion}</span>}
                <div>{note.text}</div>
              </div>
            </div>
          ))}
          <div className="doc-noesi"><span className="noesi-mark">In Noesi</span> {paper.noesi}</div>
          <div className="small muted">Modules: {paper.lessons.map((n, i) => (
            <Fragment key={n}>{i > 0 && ", "}<a href={`#/learn/${n}`}>{n}</a></Fragment>
          ))}</div>
        </aside>
      </div>
    </section>
  );
}
