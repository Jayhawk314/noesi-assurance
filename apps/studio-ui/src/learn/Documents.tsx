// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** "The documents": what an auditor actually reads, where the figure sits,
 *  and what to check. One real Harborline purchase traced end to end, the
 *  year-end balances, then illustrative documents the case has no data for. */

import { Fragment } from "react";
import { CHAIN, Field, PAPERS, Paper, Row } from "./paperTrail";

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
    <div className={`paper ${paper.illustrative ? "illustrative" : ""}`}>
      {paper.illustrative && <div className="stamp">ILLUSTRATIVE</div>}
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
      {paper.addressee && (
        <div className="addressee">{paper.addressee.map((line) => <div key={line}>{line}</div>)}</div>
      )}
      <div className="pmeta">{paper.meta.map((f) => <FieldLine key={f.label} field={f} />)}</div>
      {paper.body && <div className="pbody">{paper.body.map((p) => <p key={p}>{p}</p>)}</div>}
      {paper.table && (
        <table className="ptable">
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
        </table>
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
  const real = PAPERS.filter((p) => !p.illustrative);
  const illustrative = PAPERS.filter((p) => p.illustrative);
  return (
    <main className="lesson documents">
      <nav className="crumbs"><a href="#/learn">Course</a> › The documents</nav>
      <header className="lesson-head">
        <div className="next-kicker">Reference · the paper trail</div>
        <h1>The documents you will read, and where the figures are</h1>
        <p className="big-q">Follow one real Harborline purchase from order to ledger, then the year-end
          balances, then the documents the case has no data for.</p>
        <p>Every figure in documents 1–8 comes from the Harborline case files. Anything the files do
          not contain is marked <i>not in the extract</i> or <i>illustrative</i>. Numbered markers point
          at the figure to look at; the notes beside each document say what to do with it.</p>
      </header>

      <section className="lesson-section">
        <h2>How auditors work a document trail</h2>
        <div className="direction">
          <div><b>Vouch</b> — start from the <b>record</b> (the ledger, the payment list) and go <b>back</b> to
            the source document. Proves the recorded item is real → <b>occurrence / existence</b>.</div>
          <div><b>Trace</b> — start from the <b>source document</b> (the receiving report) and go <b>forward</b> to
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
      <p className="muted small chain-caption">Each arrow names the Noesi test that compares the two documents.
        What no test can check: whether a signature is genuine, whether a document is authentic, and whether
        the goods were ever really there. That stays with your eyes.</p>

      <h2 className="group-title">One purchase, end to end — real case data</h2>
      <p className="muted">Kingfisher Security Services, PO-2026-0009. Watch the amounts: this transaction
        carries a real exception.</p>
      {real.map((paper) => <DocSection key={paper.id} paper={paper} />)}

      <h2 className="group-title">Documents the case has no data for — illustrative</h2>
      <p className="muted">Receivables, bank confirmations, inventory counts and management's representations.
        Names and amounts are invented for teaching and labelled so.</p>
      {illustrative.map((paper) => <DocSection key={paper.id} paper={paper} />)}

      <div className="lesson-foot">
        <a className="secondary" href="#/learn">← Course</a>
        <a className="secondary" href="#/learn/trace">Follow $4,325.33 →</a>
        <a className="secondary" href="#/learn/6">Lesson 6: Accounts payable →</a>
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
        <span className={`cov ${paper.illustrative ? "none" : "full"}`}>
          {paper.illustrative ? "Illustrative" : "Real case data"}
        </span>
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
          <div className="small muted">Lessons: {paper.lessons.map((n, i) => (
            <Fragment key={n}>{i > 0 && ", "}<a href={`#/learn/${n}`}>{n}</a></Fragment>
          ))}</div>
        </aside>
      </div>
    </section>
  );
}
