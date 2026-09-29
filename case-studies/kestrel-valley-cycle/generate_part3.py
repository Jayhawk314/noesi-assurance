# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Kestrel Valley, part 3 of the full case: estimates, related parties and
completion (the subsequent period, the representation letter, the final
summary of uncorrected misstatements, going concern, and the opinion the
evidence points to).

Ties to the frozen trial balances and to parts 1 and 2. The key
(instructor/answer_key_part3.json) is computed here in plain Decimal
arithmetic, imports nothing from Noesi, and is committed before any run.

    python case-studies/kestrel-valley-cycle/generate_part3.py
"""

from __future__ import annotations

import csv
import json
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

import generate as g
from generate_payables import CUR, PE, PRI, bal
from payables_outputs import NAMES

D, m, ZERO = Decimal, g.m, Decimal("0")
REPORT_DATE = date(2026, 7, 24)
MATERIALITY = m("15000")


def estimates(key):
    write_offs = bal(CUR, "11900") - bal(PRI, "11900") + bal(CUR, "65000")
    rows = [  # estimate, prior estimate, outcome
        ("Allowance for doubtful accounts", m("12800"), write_offs),
        ("Sales returns reserve", m("5000"), m("6100")),
        ("Accrued audit fee", m("8000"), m("9350")),
        ("Inventory shrinkage reserve", m("4500"), bal(CUR, "51000")),
    ]
    g.write_csv(g.CLIENT / "prior_year_estimates.csv",
                ["Estimate", "Prior Year Estimate", "Actual Outcome"], rows)
    threshold = D("0.20")
    out = []
    for name, prior, outcome in rows:
        pct = ((outcome - prior) / prior).quantize(D("0.001"), rounding=ROUND_HALF_UP)
        out.append({"estimate": name, "prior": str(prior), "outcome": str(outcome),
                    "miss_pct": str(pct * 100), "beyond_20pct": abs(pct) > threshold})
    key["estimates"] = {"hindsight_threshold_pct": "20", "items": out,
                        "all_missed_upward": all(o > p for _, p, o in rows),
                        "bias_indicator": True}


def related_parties(key):
    rows = [  # party, relationship, address
        ("Jo Kestrel", "Managing member", "9 Lindley Pl Bozeman MT 59715"),
        ("Kestrel Holdings LLC", "Owned by the managing member", ""),
        ("Summit Loop Racing", "Owned by the managing member's brother", ""),
    ]
    g.write_csv(g.CLIENT / "related_parties.csv", ["Party", "Relationship", "Address"], rows)
    key["related_parties"] = {
        "listed": [r[0] for r in rows],
        "expected_matches": ["Summit Loop Racing: customer on the A/R aging (credit "
                             "balance -1,840.00)",
                             "Jo Kestrel: employee E01 at the same address (the owner "
                             "on the payroll)"],
        "undisclosed_not_findable_by_matching": {
            "party": "DM Consulting",
            "why": "not on management's list; its address is the bookkeeper's home "
                   "(employee E07) and it was paid 4,500 by checks with no bills. "
                   "Matching management's list cannot find it: the depth-pass item "
                   "'vendor sharing an address with an employee' would."}}


def subsequent_period(key):
    # July 2026 transactions, entered in QuickBooks after period end.
    tx = [  # date, type, num, name, memo, lines, created
        (date(2026, 7, 1), "Transfer", "", "", "Payroll funding",
         [("10200", m("40000")), ("10100", -m("40000"))], date(2026, 7, 1)),
        (date(2026, 7, 1), "Check", "4429", "Payroll Checking", "Transfer to payroll",
         [("10900", m("25000")), ("10100", -m("25000"))], date(2026, 7, 1)),
        (date(2026, 7, 8), "Journal Entry", "1071", "Cycle Tech Legal",
         "Settle distributor dispute (claim from March 2026)",
         [("68000", m("30000")), ("20000", -m("30000"))], date(2026, 7, 8)),
        (date(2026, 7, 10), "Check", "4431", "Big Timber Office Supply", "Supplies",
         [("67000", m("2215")), ("10100", -m("2215"))], date(2026, 7, 10)),
        (date(2026, 7, 15), "Check", "4433", "Velo Freight Lines",
         "June freight (invoice VF-0630)",
         [("66000", m("6100")), ("10100", -m("6100"))], date(2026, 7, 15)),
        (date(2026, 7, 8), "Deposit", "", "", "Customer receipts",
         [("10100", m("33580.90")), ("11000", -m("33580.90"))], date(2026, 7, 8)),
        (date(2026, 7, 14), "Deposit", "", "", "Customer receipts",
         [("10100", m("27904.15")), ("11000", -m("27904.15"))], date(2026, 7, 14)),
    ]
    import openpyxl
    body = []
    for when, kind, num, name, memo, lines, created in sorted(tx, key=lambda t: t[0]):
        for i, (n, a) in enumerate(lines):
            dr, cr = (a, None) if a > 0 else (None, -a)
            body.append((None, when.strftime("%m/%d/%Y") if i == 0 else None,
                         kind if i == 0 else None, num if i == 0 else None,
                         name if i == 0 else None, memo, NAMES[n], dr, cr,
                         created.strftime("%m/%d/%Y") if i == 0 else None,
                         "Dana Merritt" if i == 0 else None))
        total = sum(a for _, a in lines if a > 0)
        body.append((None,) * 7 + (total, total, None, None))
    grand = sum(sum(a for _, a in t[5] if a > 0) for t in tx)
    body.append(("TOTAL",) + (None,) * 6 + (grand, grand, None, None))
    g.write_report(g.QBO / "Journal_2026-07.xlsx", "Journal", "July 1-24, 2026",
                   [None, "Date", "Transaction type", "Num", "Name", "Memo/Description",
                    "Account", "Debit", "Credit", "Create date", "Created by"], body,
                   stamp="Friday, July 24, 2026 09:05 AM GMTZ")
    key["subsequent_events"] = {
        "report_date": REPORT_DATE.isoformat(), "threshold": "10000",
        "expected_leads": [
            "JE 1071 2026-07-08: 30,000 settlement of a dispute from March 2026 — a "
            "condition that existed at period end: adjust (recognize a liability)",
            "check 4429 2026-07-01: 25,000 transfer (the T-0701 kiting item)",
            "transfer 2026-07-01: 40,000 payroll funding (routine)",
            "deposits 33,580.90 and 27,904.15: customer receipts (routine)"],
        "unrecorded_liability": {"check": "4433", "amount": "6100.00",
                                 "why": "June freight paid in July, not in June AP"}}


def representation_letter(key):
    codes = ["fs_responsibility", "internal_control", "all_information",
             "all_transactions_recorded", "fraud", "fraud_allegations",
             "laws_regulations", "uncorrected_misstatements", "litigation_claims",
             "estimates", "subsequent_events"]                 # related_parties missing
    g.write_csv(g.AUDITOR / "representation_letter.csv",
                ["Code", "Representation", "Obtained", "Dated", "Signed By"],
                [(c, c.replace("_", " "), "yes", "2026-07-20", "Jo Kestrel") for c in codes])
    key["representation_letter"] = {"rep_signers": "Jo Kestrel",
                                    "missing": ["related_parties"],
                                    "dated": "2026-07-20",
                                    "report_date": REPORT_DATE.isoformat(),
                                    "not_dated_report_date": True, "signed": True}


def final_misstatements(key):
    with (g.AUDITOR / "uncorrected_misstatements.csv").open(encoding="utf-8") as f:
        base = list(csv.reader(f))
    header, rows = base[0], base[1:]
    k1 = json.loads((g.INSTRUCTOR / "answer_key_payables.json").read_text(encoding="utf-8"))
    k2 = json.loads((g.INSTRUCTOR / "answer_key_part2.json").read_text(encoding="utf-8"))
    dup = m(k1["duplicate_bill"]["amount"])
    ins = m(k2["accruals"]["insurance_recompute"]["difference"])
    fee = m(k2["accruals"]["audit_fee_recompute"]["difference"])
    dep = m(k2["ppe"]["depreciation_differs"]["difference"])
    new = [  # description, ref, identified, likely, CA, NCA, CL, NCL, IBT
        ("Duplicate Moraine invoice paid twice (refund due)", "AP-D", dup, ZERO,
         dup, ZERO, ZERO, ZERO, dup),
        ("Office furniture depreciation overstated", "PPE-D", dep, ZERO, ZERO, dep,
         ZERO, ZERO, dep),
        ("Insurance prepaid over time proportion", "ACC-1", ins, ZERO, -ins, ZERO, ZERO,
         ZERO, -ins),
        ("Audit fee over-accrued", "ACC-2", fee, ZERO, ZERO, ZERO, -fee, ZERO, fee),
        ("June freight not accrued (check 4433)", "SE-1", m("6100"), ZERO, ZERO, ZERO,
         m("6100"), ZERO, -m("6100")),
    ]
    all_rows = rows + [[d, r, *[f"{x:.2f}" for x in rest]] for d, r, *rest in new]
    g.write_csv(g.AUDITOR / "uncorrected_misstatements_final.csv", header, all_rows)
    cols = header[4:]
    totals = {c: sum(m(r[4 + i]) for r in all_rows) for i, c in enumerate(cols)}
    largest = max(totals.items(), key=lambda kv: abs(kv[1]))
    key["final_misstatements"] = {"totals": {k: str(v) for k, v in totals.items()},
                                  "largest_line": largest[0],
                                  "largest": str(abs(largest[1])),
                                  "materiality": str(MATERIALITY),
                                  "above_materiality": abs(largest[1]) > MATERIALITY}


def going_concern(key):
    current = ["10100", "10200", "10300", "10900", "11000", "11900", "12100", "13000"]
    liabilities = ["20000", "21000", "22000", "23000"]
    ca = sum(bal(CUR, n) for n in current)
    cl = -sum(bal(CUR, n) for n in liabilities)
    ni = -sum(bal(CUR, n) for n in (x[0] for x in g.TB) if n[0] in "456")
    equity = -(bal(CUR, "30100") + bal(CUR, "31000") + bal(CUR, "32000")) + ni
    key["going_concern"] = {
        "working_capital": str(ca - cl), "net_income": str(ni), "equity": str(equity),
        "current_ratio": str((ca / cl).quantize(D("0.0001"), rounding=ROUND_HALF_UP)),
        "floor": "1.20", "indicators": ["current_ratio_below_floor",
                                        "debt covenant breached (part 2)"],
        "note": "the engine's going-concern procedure needs its statement-line "
                "vocabulary; Kestrel's lead-schedule labels are refused (K8)"}


def expected_opinion(key):
    key["draft_opinion"] = {
        "proposal": "disclaimer",
        "why": "the related-parties representation is not provided (AU-C 580), "
               "which takes precedence over the uncorrected misstatements above "
               "materiality",
        "also": ["uncorrected misstatements exceed materiality on "
                 f"{key['final_misstatements']['largest_line']} "
                 f"({key['final_misstatements']['largest']})",
                 "going-concern conclusion must be recorded (indicators present)",
                 "the letter must be re-dated as of the report date"]}


def main():
    key = {"case_part": "3 of 3: estimates, related parties, completion",
           "policies": {"estimates_hindsight_pct": "20", "report_date": "2026-07-24",
                        "se_threshold": "10000", "rep_signers": "Jo Kestrel",
                        "gc_current_ratio_floor": "1.20"}}
    estimates(key)
    related_parties(key)
    subsequent_period(key)
    representation_letter(key)
    final_misstatements(key)
    going_concern(key)
    expected_opinion(key)
    (g.INSTRUCTOR / "answer_key_part3.json").write_text(
        json.dumps(key, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: key[k] for k in ("estimates", "final_misstatements",
                                          "going_concern", "draft_opinion")},
                     indent=1, default=str))


if __name__ == "__main__":
    main()
