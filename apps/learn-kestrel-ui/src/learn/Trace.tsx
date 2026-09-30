// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** One Kestrel amount followed from the business event toward the statements.
 *  The layout is the Harborline trace page's; the boundary between observed
 *  records and a teaching entry stays visible. */
import { useState } from "react";
import { money } from "./records";
import { CORRECTION, HEADLINE, STAGES } from "./traceData";

export function Trace() {
  const [active, setActive] = useState(0);
  const [answer, setAnswer] = useState<number | null>(null);
  const step = STAGES[active];

  return (
    <main className="lesson trace-page">
      <nav className="crumbs"><a href="#/learn">Course</a> › Follow a number</nav>
      <header className="lesson-head">
        <div className="next-kicker">Kestrel Valley · one invoice</div>
        <h1>Where did {HEADLINE} go?</h1>
        <p className="big-q">Can I trace this number from the business event to the financial statements, and explain what I know about it?</p>
        <p>Follow one supplier invoice through the records. Each step separates what the case actually contains from an accounting explanation and from evidence we still need.</p>
      </header>

      <nav className="trace-steps" aria-label="Stages of the number trail">
        {STAGES.map((item, index) => (
          <button key={item.title} type="button" className={active === index ? "active" : ""}
                  aria-current={active === index ? "step" : undefined} onClick={() => setActive(index)}>
            <span className="trace-step-number">{index + 1}</span>
            <span>{item.title}</span>
          </button>
        ))}
      </nav>

      <section className="lesson-section trace-detail" aria-live="polite">
        <div className="trace-detail-top">
          <span className="trace-status">{step.status}</span>
          <strong>{step.amount}</strong>
        </div>
        <h2>{step.question}</h2>
        <div className="trace-detail-grid">
          <div>
            <h3>{step.evidenceHeading}</h3>
            <ul>{step.observed.map((fact) => <li key={fact}>{fact}</li>)}</ul>
            <p className="trace-source"><b>Source:</b> {step.source}</p>
          </div>
          <div>
            <h3>What it means</h3>
            <p>{step.meaning}</p>
            <h3>What we cannot establish here</h3>
            <p>{step.limit}</p>
          </div>
        </div>
      </section>

      {active === 3 && (
        <section className="lesson-section trace-practice">
          <span className="trace-status">Teaching model, not Kestrel's books</span>
          <h2>Try the correction</h2>
          <p>The supplier owes Kestrel a refund for the invoice paid twice. Which account is debited to record it?</p>
          <div className="trace-choices">
            {["Accounts Payable", "A receivable from the supplier", "Cash"].map((choice, index) => (
              <button key={choice} type="button" className={answer === index ? "selected" : ""}
                      aria-pressed={answer === index} onClick={() => setAnswer(index)}>{choice}</button>
            ))}
          </div>
          {answer !== null && (
            <>
              <p className={answer === 1 ? "trace-answer right" : "trace-answer wrong"}>
                {answer === 1 ? "Yes." : answer === 0 ? "Not quite: the payable was already cleared when the check was paid."
                  : "Not quite: no money has come back yet, so Cash does not move."} The refund is an amount the
                supplier owes, so it is a receivable; the credit reduces the cost that was recorded twice.
              </p>
              <div className="table-wrap"><table>
                <thead><tr><th>Account</th><th>Debit</th><th>Credit</th></tr></thead>
                <tbody>
                  <tr><td>{CORRECTION.debit}</td><td className="trace-money">{money(CORRECTION.amount)}</td><td /></tr>
                  <tr><td>{CORRECTION.credit}</td><td /><td className="trace-money">{money(CORRECTION.amount)}</td></tr>
                </tbody>
              </table></div>
            </>
          )}
        </section>
      )}

      <div className="lesson-foot trace-footer">
        <button className="secondary" type="button" disabled={active === 0}
                onClick={() => setActive(active - 1)}>← Previous</button>
        <a className="secondary" href="#/learn/documents">See the underlying documents</a>
        <button className="primary" type="button" disabled={active === STAGES.length - 1}
                onClick={() => setActive(active + 1)}>Next →</button>
      </div>
    </main>
  );
}
