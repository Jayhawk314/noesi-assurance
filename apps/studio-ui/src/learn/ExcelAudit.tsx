// Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
/** "Excel for audit": eight guided exercises on the Harborline case files.
 *  Every answer below was computed from case-studies/harborline-marine/data
 *  on 2026-09-23; the case is generated from a fixed seed, and the oracle
 *  test guards the planted items these answers name. */

type Exercise = {
  skill: string;
  audit: string;
  file: string;
  steps: string[];
  formula?: string;
  answer: string;
  noesi: string;
};

const EXERCISES: Exercise[] = [
  {
    skill: "Tables, filters and a helper column",
    audit: "Segregation of duties: payments entered and approved by the same person",
    file: "payments.csv",
    steps: [
      "Click any cell, then Home → Format as Table. Tick \"My table has headers\".",
      "In the first empty column (I), type the heading Same person. In I2 enter the formula below; the table fills it down.",
      "Use the filter arrow on Same person and show only TRUE.",
    ],
    formula: "=F2=G2",
    answer: "5 payments: PAY-2026-0007 and 0049 (E231), PAY-2026-0013, 0055 and 0064 (E227). Look the IDs up in employees.csv: both are AP clerks.",
    noesi: "ap.segregation_of_duties finds the same five.",
  },
  {
    skill: "SUM and footing",
    audit: "Foot the population before you test it",
    file: "payments.csv",
    steps: [
      "Select the Payment Amount column and read the Sum on the status bar at the bottom.",
      "Write it into a cell with the formula below so the footing is documented.",
    ],
    formula: "=SUM(D2:D124)",
    answer: "123 payments totalling 2,745,950.03.",
    noesi: "Workbench → Sources & Mappings: the Payments dataset's control total should be the same figure. If yours differs, find out why before testing anything.",
  },
  {
    skill: "COUNTIF and duplicate highlighting",
    audit: "Shell and duplicate vendors: one tax ID, two vendor numbers",
    file: "vendors.csv",
    steps: [
      "Select the Tax ID column, then Home → Conditional Formatting → Highlight Cells Rules → Duplicate Values.",
      "In column F enter the formula below and filter it for values greater than 1.",
    ],
    formula: "=COUNTIF(D:D,D2)",
    answer: "3 tax IDs used twice, 6 vendors: V1038/V1039 (12-8850638), V1040/V1041 (49-6339233), V1042/V1043 (10-5530008).",
    noesi: "ap.vendor_relational_twins finds these pairs by name similarity. Noesi does not read tax IDs, so your spreadsheet adds evidence the tool cannot.",
  },
  {
    skill: "IF with AND",
    audit: "Payments just under the $10,000 approval limit",
    file: "payments.csv",
    steps: [
      "In a new column enter the formula below, then filter it for check.",
      "Sort the filtered rows by Vendor Number, then Payment Date.",
    ],
    formula: "=IF(AND(D2>=9000,D2<10000),\"check\",\"\")",
    answer: "7 payments. Five are to V1042 between September 14 and 22 (9,850, 9,720, 9,905, 9,640, 9,880; total 48,995). The other two (PAY-2026-0027 to V1005, PAY-2026-0054 to V1026) are single payments: an amount near the limit is not a split by itself; a cluster is.",
    noesi: "ap.split_payment_review, with the split threshold and window policies approved, reports the V1042 cluster only.",
  },
  {
    skill: "XLOOKUP across two sheets",
    audit: "Bank clearing: did every payment clear, and for the recorded amount?",
    file: "payments.csv + bank.csv",
    steps: [
      "Copy all of bank.csv into a new sheet in the same workbook and name the sheet bank.",
      "Back on payments, enter the first formula below in column I (Bank amount).",
      "In column J enter the second formula (Difference). Filter for not found, then for differences that are not zero.",
    ],
    formula: "=XLOOKUP(A2,bank!B:B,bank!C:C,\"not found\")    then    =IF(ISNUMBER(I2),I2-D2,\"\")",
    answer: "4 payments have no matching row in the bank file: PAY-2026-0001, 0038, 0052, 0116. 2 cleared for a different amount: PAY-2026-0006 (bank 20,787.69 vs 20,084.72, +702.97) and PAY-2026-0025 (16,774.78 vs 16,625.15, +149.63).",
    noesi: "cash.bank_clearing reports the four and PAY-2026-0006, but stays silent on PAY-2026-0025: 0.9% is inside its stated 2% tolerance. Your spreadsheet sees it; decide whether it matters.",
  },
  {
    skill: "SUMIF and COUNTIF by vendor",
    audit: "How much went to one vendor, in how many payments?",
    file: "payments.csv",
    steps: [
      "Type V1042 in an empty cell (say N2).",
      "Next to it enter the two formulas below.",
    ],
    formula: "=SUMIF(C:C,N2,D:D)    and    =COUNTIF(C:C,N2)",
    answer: "V1042 received 115,274.08 in 9 payments.",
    noesi: "Noesi has no vendor summary; this is your own analytic. It sets up the next exercise.",
  },
  {
    skill: "PivotTable",
    audit: "Analytics: where does the money go, and when?",
    file: "payments.csv",
    steps: [
      "Add a Month column with the formula below.",
      "Insert → PivotTable. Rows: Vendor Number. Columns: Month. Values: Sum of Payment Amount. Add Count of Payment Number too.",
      "Sort vendors by total, largest first.",
    ],
    formula: "=TEXT(E2,\"yyyy-mm\")",
    answer: "Top three by total: V1008 186,779.32, V1001 127,603.70, V1039 124,337.49. V1039 is one of the look-alike vendors from exercise 3. V1042 shows 5 payments in 2026-09.",
    noesi: "No pivot in Noesi; this is how you form expectations before running procedures.",
  },
  {
    skill: "Date filters and a lookup that should fail",
    audit: "Cutoff: payments after year end, and what they paid for",
    file: "payments.csv + vouchers.csv",
    steps: [
      "Filter Payment Date for dates after 12/31/2026.",
      "Copy vouchers.csv into a sheet named vouchers. Look up the payment's voucher with the formula below.",
    ],
    formula: "=XLOOKUP(B2,vouchers!A:A,vouchers!D:D,\"not found\")",
    answer: "One payment: PAY-2026-0055, dated January 8, 2027, for voucher VCH-2026-9336, which is not found in the voucher file. It is also one of E227's self-approved payments (exercise 1).",
    noesi: "ap.payment_voucher_reference flags the missing voucher; the date is yours to connect to the search for unrecorded liabilities.",
  },
];

export function ExcelAudit() {
  return (
    <main className="lesson">
      <nav className="crumbs"><a href="#/learn">Course</a> › <a href="#/learn/fraud">Fraud track</a> › Excel for audit</nav>
      <header className="lesson-head">
        <div className="next-kicker">Hands-on · about 3–4 hours in total</div>
        <h1>Excel for audit</h1>
        <p className="big-q">Can I run the audit tests myself in a spreadsheet, and get the same answers as Noesi?</p>
        <p>Eight exercises on the Harborline files, each teaching one Excel skill through one audit test.
          Do each in Excel first, check your answer, then compare with Noesi. That order, judgment before the
          tool, is how the case was built to be learned.</p>
      </header>

      <section className="lesson-section">
        <h2>Setting up, free</h2>
        <ol className="steps">
          <li>Go to <b>office.com</b>, sign in with an Outlook (Microsoft) account, and open <b>Excel</b>. Excel on the web is free and does everything these exercises need.</li>
          <li>Upload the files from <code>case-studies/harborline-marine/data/</code> (or download them from the GitHub repository). If Excel on the web limits editing of a .csv file, save a copy as .xlsx and work in that.</li>
          <li>Keep one workbook per exercise, or one workbook with a sheet per file. Column letters below assume the file's own column order.</li>
        </ol>
        <p className="muted small">Google Sheets and LibreOffice Calc also work; XLOOKUP and PivotTables exist in both, with small differences in menus.</p>
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
            <p className="muted"><b>Compare with Noesi:</b> {ex.noesi}</p>
          </details>
        </section>
      ))}

      <p className="muted fine">Answers were computed from the case files and are fixed by the case's seed. The web
        version of Excel cannot run macros (VBA) or Power Pivot; nothing here needs them.</p>
      <div className="lesson-foot">
        <a className="secondary" href="#/learn/fraud">← Fraud track</a>
        <a className="secondary" href="#/learn/fraud/4">Lesson F4: payment tampering →</a>
      </div>
    </main>
  );
}
