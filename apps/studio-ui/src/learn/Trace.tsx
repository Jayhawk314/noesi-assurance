// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** One case amount followed from a business event toward the statements.
 * The boundary between observed records and a teaching entry stays visible. */
import { useState } from "react";
import ledger from "../../../../case-studies/harborline-marine/learning/trace-ledger.json";

const money = (value: string) => `$${Number(value).toLocaleString("en-US", {
  minimumFractionDigits: 2, maximumFractionDigits: 2,
})}`;
const source = ledger.source;

type Stage = {
  title: string;
  amount: string;
  status: string;
  question: string;
  evidenceHeading: string;
  observed: string[];
  meaning: string;
  limit: string;
  source: string;
};

const stages: Stage[] = [
  {
    title: "The business event", amount: `${money(source.ordered)} ordered`, status: "Source records",
    question: "What did Harborline agree to buy, and what was accepted?",
    evidenceHeading: "What the records show",
    observed: [
      `${source.purchase_order} orders ${money(source.ordered)} of security services from Kingfisher Security Services.`,
      `${source.receipt} records ${money(source.accepted)} of services accepted.`,
      `${source.voucher} bills ${money(source.billed)}. The bill exceeds the accepted amount by ${money(source.unresolved_difference)}.`,
    ],
    meaning: "An order is a commitment, not by itself an expense or a payable. The receipt and bill raise the question of how much service was actually delivered and should be recognized.",
    limit: `These case extracts do not prove that the service was delivered beyond the recorded acceptance, or explain the ${money(source.unresolved_difference)} difference.`,
    source: "purchase_orders.csv row 10 · goods_receipts.csv row 10 · vouchers.csv row 10",
  },
  {
    title: "The accounting entry", amount: `${money(source.billed)} billed`, status: "Teaching model",
    question: "If the full bill were recorded on account, what would move?",
    evidenceHeading: "What the accounting model shows",
    observed: [
      "A typical entry for accepted services is debit expense and credit Accounts Payable.",
      `Using the billed amount would put ${money(source.billed)} on each side of that entry.`,
      `The ${money(source.unresolved_difference)} gap must be investigated before treating the billed amount as supported expense.`,
    ],
    meaning: "The debit describes the cost of services; the credit records the obligation to pay. This is an explanation of double-entry accounting, not an entry found in Harborline's GL extract.",
    limit: "The supplied GL extract contains AP payment postings, not the invoice-side expense or payable posting. We cannot verify that this proposed entry was made, or which expense account was used.",
    source: "vouchers.csv row 10 · gl.csv scope: AP account 2000 payment postings",
  },
  {
    title: "Payment and ledger", amount: `${money(source.paid)} paid`, status: "Observed with a limit",
    question: "Did Harborline pay the bill, and what reached the AP ledger?",
    evidenceHeading: "What the records show",
    observed: [
      `${source.payment} records a ${money(source.paid)} check dated March 16, 2026.`,
      "BNK-00008 shows that amount clearing the bank on March 22.",
      `GL-00008 records a ${money(source.paid)} posting to AP account 2000 for that payment.`,
    ],
    meaning: "For an ordinary bill payment, debit AP to reduce the obligation and credit Cash to reduce the asset. The extract supports the AP payment posting and independent bank clearing.",
    limit: "The GL extract does not label the posting as a debit or include the cash-side line. The debit/credit explanation is a model. Bank clearing shows money left; it does not establish that the original bill was valid or matched the services received.",
    source: "payments.csv row 10 · bank.csv row 9 · gl.csv row 9",
  },
  {
    title: "Toward the statements", amount: "No verified single-item link", status: "Evidence stops here",
    question: "Where would this transaction appear in the financial statements?",
    evidenceHeading: "What we can connect",
    observed: [
      "An accepted security-services cost would ordinarily affect an expense on the income statement.",
      "An unpaid bill would affect Accounts Payable on the balance sheet; this bill was paid in March, before the December year end.",
      "The case provides a year-end AP control balance of $2,750,019.42 and a subledger balance of $2,731,569.42, an $18,450.00 difference.",
    ],
    meaning: "Individual entries roll into account balances, which feed the statements. The year-end AP comparison is an aggregate control check, not a trace of this paid invoice into the closing balance.",
    limit: "The case has no full trial balance or financial statements, and no expense-side posting for this invoice. We cannot prove its income-statement effect or tie it to a statement line.",
    source: "ap_control_balance.csv row 2 · missing: expense GL, full trial balance, statements",
  },
  {
    title: "What we can conclude", amount: `${money(source.unresolved_difference)} difference`, status: "Finding, not conclusion",
    question: "What is supported, and what still needs a person to decide?",
    evidenceHeading: "What the records show",
    observed: [
      `Ordered and billed: ${money(source.billed)}. Accepted: ${money(source.accepted)}. Difference: ${money(source.unresolved_difference)}.`,
      "The full bill was paid, cleared the bank, and has an AP payment posting.",
      "Noesi's three-way match flags the difference between the voucher and recorded receipt.",
    ],
    meaning: "The records support an exception worth investigating. A reviewer would seek the service acceptance detail, ask about the difference, and decide whether a correction or further work is needed.",
    limit: "A matched payment is not proof that the expense was proper. The automated finding is not a misstatement conclusion or an audit opinion.",
    source: "Harborline source records · three-way-match result in the verified case run",
  },
];

export function Trace() {
  const [active, setActive] = useState(0);
  const [answer, setAnswer] = useState<number | null>(null);
  const step = stages[active];

  return (
    <main className="lesson trace-page">
      <nav className="crumbs"><a href="#/learn">Course</a> › Follow a number</nav>
      <header className="lesson-head">
        <div className="next-kicker">Harborline Marine · one purchase</div>
        <h1>Where did {money(source.billed)} go?</h1>
        <p className="big-q">Can I trace this number from the business event to the financial statement—and explain what I know about it?</p>
        <p>Follow one purchase through the records. Each step separates what the case actually contains from an accounting explanation and from evidence we still need.</p>
      </header>

      <nav className="trace-steps" aria-label="Stages of the number trail">
        {stages.map((item, index) => (
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

      {active === 3 && <TeachingLedger />}

      {active === 1 && (
        <section className="lesson-section trace-practice">
          <h2>Try the entry</h2>
          <p>If the full bill for services were recorded on account, which account would be credited?</p>
          <div className="trace-choices">
            {["Security-services expense", "Accounts Payable", "Cash"].map((choice, index) => (
              <button key={choice} type="button" className={answer === index ? "selected" : ""}
                      aria-pressed={answer === index} onClick={() => setAnswer(index)}>{choice}</button>
            ))}
          </div>
          {answer !== null && <p className={answer === 1 ? "trace-answer right" : "trace-answer wrong"}>
            {answer === 1 ? "Yes." : answer === 0 ? "Not quite: the expense is the debit side." : "Not quite: nothing has been paid yet, so Cash does not move."} Debit the service expense and credit Accounts Payable for an accepted amount. The exact amount here needs investigation because the receipt is {money(source.unresolved_difference)} lower than the bill. This entry is a teaching example; the invoice posting is absent from the extract.
          </p>}
        </section>
      )}

      <div className="lesson-foot trace-footer">
        <button className="secondary" type="button" disabled={active === 0}
                onClick={() => setActive(active - 1)}>← Previous</button>
        <a className="secondary" href="#/learn/documents">See the underlying documents</a>
        <button className="primary" type="button" disabled={active === stages.length - 1}
                onClick={() => setActive(active + 1)}>Next →</button>
      </div>
    </main>
  );
}

function TeachingLedger() {
  const statement = ledger.statement_excerpt;
  return (
    <section className="lesson-section trace-ledger">
      <span className="trace-status">Illustration, not Harborline's books</span>
      <h2>Now finish the path in a tiny practice ledger</h2>
      <p>{ledger.assumption} We add a {money(ledger.journal[0].lines[0].debit)} opening cash balance so the example can show a balanced trial balance and statement excerpt. These entries were generated from {ledger.source.voucher} and {ledger.source.payment}; they are <b>not</b> in the supplied Harborline GL.</p>

      <h3>1. Journal: record the events</h3>
      <div className="table-wrap"><table>
        <thead><tr><th>Date / event</th><th>Account</th><th>Debit</th><th>Credit</th></tr></thead>
        <tbody>{ledger.journal.flatMap((event) => event.lines.map((line, index) => (
          <tr key={`${event.event}-${line.account}`}>
            <td>{index === 0 ? <>{event.date}<br />{event.event}</> : ""}</td>
            <td>{line.account}</td>
            <td className="trace-money">{line.debit ? money(line.debit) : ""}</td>
            <td className="trace-money">{line.credit ? money(line.credit) : ""}</td>
          </tr>
        )))}</tbody>
      </table></div>
      <p className="muted small">A debit or credit describes which side of an account changes. Every entry has equal total debits and credits.</p>

      <h3>2. Trial balance: collect each account's ending amount</h3>
      <div className="table-wrap"><table>
        <thead><tr><th>Account</th><th>Debit balance</th><th>Credit balance</th></tr></thead>
        <tbody>{ledger.trial_balance.map((row) => (
          <tr key={row.account}><td>{row.account}</td>
            <td className="trace-money">{row.debit ? money(row.debit) : "—"}</td>
            <td className="trace-money">{row.credit ? money(row.credit) : "—"}</td></tr>
        ))}</tbody>
      </table></div>

      <h3>3. Statement excerpt: see where those balances go</h3>
      <div className="trace-statements">
        <div><b>Income statement</b>
          <p>Security-services expense: {money(statement.income_statement.security_services_expense)}</p>
          <p>Result in this isolated example: {money(statement.income_statement.net_loss)} loss</p>
        </div>
        <div><b>Balance sheet</b>
          <p>Cash: {money(statement.balance_sheet.cash)} · Accounts Payable: {money(statement.balance_sheet.accounts_payable)}</p>
          <p>Equity: {money(statement.balance_sheet.opening_equity)} opening less {money(statement.balance_sheet.current_loss)} loss = {money(statement.balance_sheet.ending_equity)} ending</p>
        </div>
      </div>
      <p className="callout watch"><b>The open question:</b> the recorded receipt is {money(ledger.source.accepted)}, leaving {money(ledger.source.unresolved_difference)} of the billed expense unsupported by that receipt. This example shows how booking the full bill would flow; it does not decide the correct adjustment.</p>
    </section>
  );
}
