# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The finish-line check (ROADMAP step 0): run the Kestrel demo through the
Workbench and compare each Learn module's results with the answer key.

The demo is seeded exactly as ``python -m workbench_api --demo`` seeds it
(``workbench_api.demo.seed_kestrel``: the real service path, three chairs,
every executable procedure run). Each line of the key the Workbench can be
asked about is compared with what the Workbench produced:

- ``match``: the Workbench gives the key's answer;
- ``differs``: it gives another answer; the reason is stated;
- ``not in Noesi``: the Workbench does not produce this answer; the reason
  is stated.

A known difference is pinned: its reason and the exact Workbench value it
gives (or that it gives none). A difference with nothing pinned, or a
pinned one whose Workbench value has moved, prints as UNEXPLAINED and makes
the script exit 1: that is new information, not a known gap.

    .venv\\Scripts\\python case-studies\\kestrel-valley-cycle\\instructor\\finish_line_check.py

It writes FINISH-LINE-REPORT.md next to itself.
"""

from __future__ import annotations

import json
import sys
import tempfile
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPORT = HERE / "FINISH-LINE-REPORT.md"
K1 = json.loads((HERE / "answer_key.json").read_text(encoding="utf-8"))
KP = json.loads((HERE / "answer_key_payables.json").read_text(encoding="utf-8"))
K2 = json.loads((HERE / "answer_key_part2.json").read_text(encoding="utf-8"))
K3 = json.loads((HERE / "answer_key_part3.json").read_text(encoding="utf-8"))

MODULES = ["Engagement setup", "Planning", "Journal entries", "Revenue and receivables",
           "Payables", "Cash", "Inventory", "Payroll", "Property and equipment",
           "Debt, equity, accruals", "Estimates and related parties", "Completion",
           "The opinion"]


class _Missing:
    def __repr__(self):
        return "—"


NOT_IN = _Missing()          # the Workbench gives no answer for this line


def _dec(value):
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def same(key, got) -> bool:
    """Numbers compare at the key's precision; sets and lists as sets of
    lower-case text; anything else as lower-case text."""
    if isinstance(key, (set, frozenset, list, tuple)):
        norm = lambda xs: {str(x).strip().lower() for x in xs}  # noqa: E731
        return got is not NOT_IN and norm(key) == norm(got or [])
    if isinstance(key, bool) or isinstance(got, bool):
        return key == got
    k, g = _dec(key), _dec(got)
    if k is not None and g is not None:
        return g.quantize(Decimal(1).scaleb(min(k.as_tuple().exponent, 0))) == k
    return str(key).strip().lower() == str(got).strip().lower()


class Check:
    """A known difference is pinned: its reason and the exact Workbench value
    it is known to give (``expect``, or NOT_IN). Any other value, or a
    difference with nothing pinned, is UNEXPLAINED."""

    def __init__(self):
        self.rows: list[dict] = []
        self.module = ""

    def __call__(self, item, key, got, why="", expect=None):
        status = ("not in Noesi" if got is NOT_IN else
                  "match" if same(key, got) else "differs")
        if status == "match":
            why = ""
        elif not why or expect is None:
            why = "UNEXPLAINED"
        elif not (got is NOT_IN if expect is NOT_IN else
                  got is not NOT_IN and same(expect, got)):
            why = (f"UNEXPLAINED: the known difference was Workbench {expect!r}; "
                   f"it is now {got!r}")
        self.rows.append({"module": self.module, "item": item, "key": key, "got": got,
                          "status": status, "why": why})


def seed():
    """The demo engagement, as ``--demo`` seeds it, in a scratch store."""
    sys.path.insert(0, str(ROOT / "apps" / "workbench-api"))
    from assurance_application.service import WorkbenchService
    from assurance_artifacts.vault import ArtifactVault
    from assurance_persistence.database import connect, migrate
    from assurance_persistence.legacy_import import ensure_tenant
    from workbench_api.demo import seed_kestrel

    scratch = Path(tempfile.mkdtemp(prefix="kestrel-finish-line-"))
    conn = connect(scratch / "control.db")
    migrate(conn)
    svc = WorkbenchService(conn, ArtifactVault(scratch / "vault"),
                           ensure_tenant(conn, "finish-line"))
    outcome = seed_kestrel(svc, "demo-partner")
    return svc, outcome


def gather(svc, eid) -> dict:
    runs = {r["procedure_id"]: r["summary"] for r in svc.runs(eid)}
    findings = defaultdict(list)
    for f in svc.findings(eid):
        findings[f["procedure_id"]].append(f["verdict"])
    datasets = defaultdict(list)
    for d in svc.sources(eid)["datasets"]:
        datasets[d["role"]].append(d)
    coverage = {r["procedure_id"]: r for r in svc.coverage(eid)["procedures"]}
    return {"runs": runs, "findings": findings, "datasets": datasets,
            "coverage": coverage, "opinion": svc.draft_opinion(eid),
            "workflow": svc.workflow_document(eid)[0], "team": svc.team(eid),
            "sad": svc.sad(eid)}


def compare(d: dict) -> Check:  # noqa: C901 — one block per module, read top to bottom
    runs, fnd, ds, cov = d["runs"], d["findings"], d["datasets"], d["coverage"]
    c = Check()

    def run(pid):
        return runs.get(pid) or {}

    def with_test(pid, test):
        """Findings of one procedure whose key ends with ``test``."""
        return [v for v in fnd.get(pid, []) if str(v["key"][-1]) == test]

    def has(pid, *parts):
        return any(all(str(p).lower() in [str(k).lower() for k in v["key"]] for p in parts)
                   for v in fnd.get(pid, []))

    def loaded(role):
        return sum(x["rows_loaded"] for x in ds.get(role, []))

    def set_aside(role):
        return sum(x["rows_rejected"] for x in ds.get(role, []))

    def ran(pid):
        return pid in runs

    def status(pid):
        return (cov.get(pid) or {}).get("status", "absent")

    # ---- 1 Engagement setup
    c.module = MODULES[0]
    wf = d["workflow"]
    mat = (wf.get("materiality") or {})
    c("materiality", K1["materiality"], mat.get("amount", NOT_IN))
    c("period start", K2["period"]["start"], (wf.get("period") or {}).get("start", NOT_IN))
    c("period end", K1["period_end"], wf.get("fye", NOT_IN))
    roles = {t["role"] for t in d["team"]}
    c("team: partner, preparer, reviewer", ["partner", "preparer", "reviewer"], roles)
    c("every file loads (none refused)", 0, len(d.get("refused", [])))

    # ---- 2 Planning
    c.module = MODULES[1]
    pm = K1["planning.performance_materiality"]
    s = run("planning.performance_materiality")
    c("PM allocated", pm["allocated_total"], s.get("allocated", NOT_IN))
    c("PM cap (2.0 x materiality)", pm["cap"], s.get("ceiling", NOT_IN))
    c("PM over the cap by", pm["exceeds_cap_by"],
      -_dec(s["headroom"]) if "headroom" in s else NOT_IN)
    tba = K1["fs.trial_balance_analytics"]
    s = run("fs.trial_balance_analytics")
    c("trial balance foots", tba["tb_foots"], s.get("debits") == s.get("credits"))
    c("trial balance debits", K1["summary"]["tb_2026_debits"], s.get("debits", NOT_IN))
    flagged = {m["account"].split(" ")[0] for m in tba["movements_flagged"]}
    got = {v["key"][2] for v in fnd.get("fs.trial_balance_analytics", [])
           if v["key"][1] == "movement"}
    c("movements flagged (10% or 15,000)", sorted(flagged), sorted(got))
    now = (s.get("current") or {})
    before = (s.get("prior") or {})
    r26, r25 = tba["ratios"]["2026"], tba["ratios"]["2025"]
    for label, key, block in (("2026", r26, now), ("2025", r25, before)):
        ratios, figs = block.get("ratios") or {}, block.get("figures") or {}
        c(f"{label} current ratio", key["current_ratio"], ratios.get("current_ratio", NOT_IN))
        c(f"{label} quick ratio", key["quick_ratio"], ratios.get("quick_ratio", NOT_IN))
        c(f"{label} gross margin %", key["gross_margin_pct"],
          _dec(ratios["gross_margin"]) * 100 if ratios.get("gross_margin") else NOT_IN)
        c(f"{label} net revenue", key["net_revenue"], figs.get("net_sales", NOT_IN))
        c(f"{label} pretax income", key["pretax_income"],
          figs.get("income_before_taxes", NOT_IN))
    c("2026 cost of sales", r26["cost_of_sales"],
      (s.get("line_totals") or {}).get("cost_of_sales", NOT_IN))
    c("2026 inventory turnover (average inventory)", r26["inventory_turnover"],
      (now.get("ratios") or {}).get("inventory_turnover", NOT_IN))
    c("2026 sales to year-end net receivables", r26["sales_to_receivables"],
      (now.get("ratios") or {}).get("sales_to_receivables", NOT_IN))

    # ---- 3 Journal entries
    c.module = MODULES[2]
    je = KP["je_testing"]
    s = run("je.journal_entry_testing")
    c("transactions in the Journal", KP["journal"]["transactions"], s.get("population", NOT_IN))
    c("lines in the Journal", KP["journal"]["lines"],
      ds["Journal_entries"][0]["rows_loaded"] if ds.get("Journal_entries") else NOT_IN)
    for test in ("posted_after_period_end", "weekend_or_holiday", "round_amount",
                 "unauthorized_user", "seldom_used_account"):
        c(f"{test.replace('_', ' ')}: entries", je[test]["entries"],
          [v["key"][1] for v in with_test("je.journal_entry_testing", test)])
    nd = with_test("je.journal_entry_testing", "no_description")
    c("no description: count", je["no_description"]["count"],
      len(nd) + len(s.get("no_description_not_manual_entries") or []))
    manual = [v["key"][1] for v in nd]
    c("manual entries without a description", ["journal entry 1052"],
      [m.split(" ", 1)[1] for m in manual])
    rare = set()
    for v in with_test("je.journal_entry_testing", "seldom_used_account"):
        rare.update(v["evidence"].get("accounts", []))
    c("seldom-used accounts", KP["je_seldom_used_accounts"], sorted(rare))
    pc = KP["je_population_completeness"]
    s = run("je.population_completeness")
    c("every account rolls forward", pc["every_account_rolls_forward"],
      s.get("exceptions") == 0 if s else NOT_IN)
    c("closed to", pc["closed_to"], s.get("closed_to", NOT_IN))
    c("prior-year closing amount", pc["prior_year_closing_amount"],
      s.get("prior_year_closing_amount", NOT_IN))

    # ---- 4 Revenue and receivables
    c.module = MODULES[3]
    lt = K1["ar.listing_tie"]
    s = run("ar.listing_tie")
    c("aging total", lt["aging_total"], s.get("listing_total", NOT_IN))
    c("A/R per trial balance", lt["tb_accounts_receivable"], s.get("gl_total", NOT_IN))
    c("aging to ledger difference found", True, has("ar.listing_tie", "listing_to_gl"))
    c("credit balance: Summit Loop Racing", True,
      has("ar.listing_tie", "credit_balance", "summit loop racing"))
    # The learner reperforms from the aging as exported (Ridgeback still on
    # it); the key's re-run-aging figures are the corrected scenario, for
    # discussion, and are not something the Workbench is given.
    c("allowance required (aging as loaded)", lt["as_loaded"]["allowance_required"],
      s.get("allowance_required", NOT_IN))
    c("allowance recorded", lt["allowance_recorded"], s.get("allowance_recorded", NOT_IN))
    c("allowance short (aging as loaded)", lt["as_loaded"]["allowance_shortfall"],
      _dec(s["allowance_required"]) - _dec(s["allowance_recorded"])
      if "allowance_required" in s else NOT_IN)
    cf = K1["ar.confirmations_nonstatistical"]
    s = run("ar.confirmations_nonstatistical")
    c("key items", len(cf["key_items"]), s.get("significant", NOT_IN))
    c("sample items", len(cf["sample_items"]), s.get("sampled", NOT_IN))
    c("key-item misstatement", cf["key_known_misstatement"], s.get("known_misstatement", NOT_IN))
    c("misstatements counted (timing and customer error left out)",
      ["big sky pedal co.", "bitterroot wheelworks"],
      [v["key"][-1] for v in fnd.get("ar.confirmations_nonstatistical", [])
       if v["key"][1] == "client_misstatement"])
    c("sample book value", cf["sample_book"], s.get("sample_value", NOT_IN))
    loaded_cf = cf["as_loaded"]
    c("remainder book value (aging as loaded)", loaded_cf["remainder_book"],
      s.get("stratum_value", NOT_IN))
    c("projected misstatement (aging as loaded)", loaded_cf["projected_remainder"],
      s.get("projected_sample_misstatement", NOT_IN))
    c("total likely misstatement (aging as loaded)", loaded_cf["total_likely"],
      s.get("projected_total", NOT_IN))
    c("below tolerable", True,
      _dec(s["projected_total"]) < _dec(cf["tolerable"]) if s else NOT_IN)

    # ---- 5 Payables
    c.module = MODULES[4]
    c("vendors", KP["vendors"]["count"], loaded("Vendors"))
    c("vendor twins", True, has("ap.vendor_relational_twins", "Moraine Cycle Components",
                                "Moraine Cycle Components, Inc."))
    c("bills (loaded + set aside)", KP["bills"]["count"],
      loaded("Vouchers") + set_aside("Vouchers"))
    c("bills without a number (set aside at load)", len(KP["bills_without_number"]),
      set_aside("Vouchers"))
    c("bill payments", KP["bill_payments"]["count"], loaded("Payments"))
    c("bill payments total", KP["bill_payments"]["total"],
      ds["Payments"][0]["control_total"] if ds.get("Payments") else NOT_IN)
    c("duplicate bill MC-25009", True, has("ap.duplicate_bills", "mc25009"))
    c("split bills: Hyalite total", KP["split_bills"]["total"],
      next((v["reason"].split(" total ")[1].split(" ")[0]
            for v in fnd.get("ap.split_payment_review", [])
            if "Hyalite" in str(v["key"])), NOT_IN))
    c("short payment on check 4425 (left open)", KP["short_payment"]["left_open"],
      next((abs(_dec(v["reason"].split(" listed at ")[1].split(" ")[0])
                - _dec(v["reason"].rsplit(" for ", 1)[1]))
            for v in with_test("cash.bank_reconciliation", "4425")
            if "cleared_amount_differs" in v["key"]), NOT_IN))
    c("PO overrun: Summit Tire PO 1021", True,
      NOT_IN if not ran("ap.voucher_po_reference") else has("ap.voucher_po_reference", "1021"),
      "QuickBooks' Transaction List by Vendor carries no PO link on a bill (the "
      "PO number is only in the memo), so voucher-to-PO tests are partial "
      f"({status('ap.voucher_po_reference')}); roadmap C", expect=NOT_IN)
    c("checks without bills: DM Consulting 4,500", True, NOT_IN,
      "no procedure tests direct checks to vendors that never billed; the "
      "Payments loaded are bill payments only (parking lot: depth pass)", expect=NOT_IN)
    c("A/P subledger ties to the ledger", KP["ap_subledger_to_ledger"]["difference"],
      NOT_IN if not ran("ap.subledger_gl_balance_tie") else "0.00",
      "the A/P control schedule is built from Unpaid Bills and a General Ledger "
      "export; Kestrel has a trial balance, not a General Ledger export "
      f"({status('ap.subledger_gl_balance_tie')}); roadmap C", expect=NOT_IN)
    c("three-way match not testable", "blocked", status("ap.three_way_receipt_match"))
    c("segregation of duties not testable", "partial", status("ap.segregation_of_duties"))
    c("duplicate's misstatement", KP["misstatement_from_duplicate"]["amount"],
      next((v["reason"].split(" likely recorded twice")[0].rsplit(" ", 1)[1]
            for v in fnd.get("ap.duplicate_bills", [])
            if " likely recorded twice" in v["reason"]), NOT_IN))

    # ---- 6 Cash
    c.module = MODULES[5]
    br = K1["cash.bank_reconciliation"]
    accts = run("cash.bank_reconciliation").get("accounts") or {}
    for name in ("checking", "payroll"):
        a = accts.get(name) or {}
        tot = a.get("totals") or {}
        c(f"{name}: statement ending", br[name]["statement_ending"],
          tot.get("bank_balance", NOT_IN))
        c(f"{name}: book balance", br[name]["register_balance"],
          tot.get("book_balance", NOT_IN))
        c(f"{name}: reconciliation refoots", br[name]["refoots"],
          a.get("adjusted_bank") == a.get("adjusted_book") if a else NOT_IN)
    c("check 4421 did not clear by 07-15", True,
      has("cash.bank_reconciliation", "outstanding_not_cleared", "4421"))
    c("check 4425 cleared at another amount", True,
      has("cash.bank_reconciliation", "cleared_amount_differs", "4425"))
    slow = [x["amount"] for x in br["deposits_in_transit"] if x["exceeds_dit_max_days"]]
    c("deposits in transit cleared slowly", slow,
      (accts.get("checking") or {}).get("deposits_cleared_slowly", NOT_IN))
    for t, verdict in K1["cash.interbank_transfers"].items():
        c(f"transfer {t}", verdict.startswith("EXCEPTION"),
          has("cash.interbank_transfers", t.lower(), "kiting"))

    # ---- 7 Inventory
    c.module = MODULES[6]
    it = K1["inventory.count_listing_trace"]
    s = run("inventory.count_listing_trace")
    c("listing total", it["listing_total"], s.get("listed_total", NOT_IN))
    c("tags (loaded + void set aside)", it["tags_total"],
      loaded("Inventory_count") + set_aside("Inventory_count"))
    c("void tags set aside", len(it["void_tags"]), set_aside("Inventory_count"))
    c("quantity differences", [q["sku"] for q in it["quantity_differences"]],
      s.get("details_differ", NOT_IN))
    c("listed, not counted", [q["sku"] for q in it["listed_not_counted"]],
      s.get("listed_not_counted", NOT_IN))
    c("counted, not listed", [q["sku"] for q in it["counted_not_listed"]],
      s.get("counted_not_listed", NOT_IN))
    pp = K1["inventory.pricing_projection"]
    s = run("inventory.pricing_projection")
    c("pricing sample recorded", pp["sample_recorded"], s.get("sample_value", NOT_IN))
    c("net overstatement in sample", pp["net_overstatement_in_sample"],
      s.get("net_sample_misstatement", NOT_IN))
    c("items with differences", list(pp["items_with_differences"]),
      [v["key"][-1] for v in fnd.get("inventory.pricing_projection", [])
       if v["key"][1] == "price_difference"])
    c("projected to the listing", pp["projected_to_listing"],
      s.get("projected_misstatement", NOT_IN))

    # ---- 8 Payroll
    c.module = MODULES[7]
    py = K2["payroll"]
    s = run("payroll.register_to_ledger")
    c("register gross", py["register_gross"], s.get("register_gross", NOT_IN))
    c("wages per ledger", py["tb_wages_60100"], s.get("ledger_wages", NOT_IN))
    c("difference", py["difference"], s.get("difference", NOT_IN))
    ghost = [v for v in with_test("payroll.register_tests", "not_on_employee_master")
             if v["key"][1] == py["ghost_employee"]["id"].lower()]
    c("ghost employee E16: payments", py["ghost_employee"]["payments"], len(ghost))
    c("paid after termination: E12", True,
      has("payroll.register_tests", "e12", "paid_after_termination"))
    c("shared bank account: E03, E09", True,
      has("payroll.register_tests", "e03,e09", "shared_bank_account"))
    c("net pay error: E05", True, has("payroll.register_tests", "e05", "net_pay_differs"))
    c("bookkeeper's address is a vendor's (DM Consulting)", True, NOT_IN,
      "no procedure compares employee and vendor addresses (parking lot: depth "
      "pass, 'vendor sharing an address with an employee')", expect=NOT_IN)

    # ---- 9 Property and equipment
    c.module = MODULES[8]
    pe = K2["ppe"]
    s = run("ppe.rollforward")
    for item, field in (("beginning_cost", "beginning_cost"), ("additions", "additions"),
                        ("disposals", "disposals"), ("ending_cost", "ending_cost"),
                        ("accumulated", "accumulated_depreciation")):
        c(item.replace("_", " "), pe[item], s.get(field, NOT_IN))
    s = run("ppe.depreciation_recompute")
    c("depreciation per register", pe["depreciation_register"],
      s.get("register_total", NOT_IN))
    c("FA-06 depreciation differs by", pe["depreciation_differs"]["difference"],
      next((_dec(v["evidence"]["recorded"]) - _dec(v["evidence"]["recomputed"]) for v in
            with_test("ppe.depreciation_recompute", "depreciation_differs")
            if v["key"][1] == "fa-06"), NOT_IN))
    s = run("ppe.additions_vouching")
    c("additions vouched in full, no exceptions", True,
      (s.get("coverage") == "1.0000" and s.get("exceptions") == 0) if s else NOT_IN)

    # ---- 10 Debt, equity, accruals
    c.module = MODULES[9]
    loan = K2["debt_equity"]["loan"]
    s = run("debt.rollforward_and_interest")
    c("loan beginning", loan["beginning"], s.get("beginning_debt", NOT_IN))
    c("loan ending", loan["ending"], s.get("ending_debt", NOT_IN))
    c("interest within tolerance (4.8% < 10%)", 0, s.get("exceptions", NOT_IN))
    c("current-ratio covenant breached", True, has("debt.covenants", "breached"))
    c("members' capital does not tie", True,
      has("equity.rollforward", "members' capital", "ending_to_ledger"))
    c("retained earnings ties", False, has("equity.rollforward", "retained earnings"))
    s = run("accruals.rollforward")
    c("accruals and prepaids tie to the ledger", 0, s.get("exceptions", NOT_IN))
    ac = K2["accruals"]
    for name, key in (("insurance premium", ac["insurance_recompute"]),
                      ("audit fee", ac["audit_fee_recompute"])):
        c(f"{name} recompute differs by", key["difference"],
          next((v["reason"].rsplit("difference ", 1)[1].rstrip(")")
                for v in with_test("accruals.recompute", "recompute_differs")
                if v["key"][1] == name), NOT_IN))
    c("not recomputed", ac["not_recomputed"],
      run("accruals.recompute").get("not_recomputed", NOT_IN))
    stale = [v["key"][1] for v in fnd.get("accruals.rollforward", [])
             if v["key"][-1] == "unchanged"]
    c("stale accrual: Accrued payroll unchanged all year", ["accrued payroll"],
      stale or NOT_IN,
      "the rollforward tests that each item foots and ties; it does not point "
      "out a balance with no activity all year (parking lot)", expect=NOT_IN)

    # ---- 11 Estimates and related parties
    c.module = MODULES[10]
    es = K3["estimates"]
    c("estimates missed beyond 20%",
      [i["estimate"] for i in es["items"] if i["beyond_20pct"]],
      [v["key"][1] for v in with_test("estimates.retrospective_review", "outcome_differs")])
    c("bias indicator (all missed one way)", es["bias_indicator"],
      has("estimates.retrospective_review", "one_direction"))
    c("related party: Summit Loop Racing is a customer", True,
      has("related_parties.matching", "summit loop racing", "customer"))
    c("related party: Jo Kestrel on the payroll (E01)", True,
      has("related_parties.matching", "jo kestrel", "e01"))
    c("DM Consulting not findable by matching management's list", False,
      has("related_parties.matching", "dm consulting"))

    # ---- 12 Completion
    c.module = MODULES[11]
    se = K3["subsequent_events"]
    leads = " ".join(v["reason"] for v in fnd.get("completion.subsequent_events", []))
    for amount, what in (("30000.00", "JE 1071 settlement"), ("25000.00", "check 4429"),
                         ("40000.00", "payroll funding transfer"),
                         ("33580.90", "deposit"), ("27904.15", "deposit")):
        c(f"subsequent-event lead: {what} {amount}", True, amount in leads)
    c(f"unrecorded liability: check {se['unrecorded_liability']['check']}",
      se["unrecorded_liability"]["amount"],
      NOT_IN if not ran("ap.unrecorded_liabilities_search") else "",
      "the search needs payments linked to bills and the auditor's inspection "
      f"results ({status('ap.unrecorded_liabilities_search')}); the July "
      "check is below the subsequent-events threshold; roadmap C", expect=NOT_IN)
    rl = K3["representation_letter"]
    c("representation missing", rl["missing"],
      [v["key"][1] for v in with_test("completion.representation_letter", "not_obtained")])
    c("letter not dated the report date", rl["not_dated_report_date"],
      has("completion.representation_letter", "not_dated_report_date"))
    fm = K3["final_misstatements"]
    s = run("completion.uncorrected_misstatements")
    for line, amount in fm["totals"].items():
        c(f"uncorrected misstatements: {line}", amount,
          (s.get("totals") or {}).get(line.lower().replace(" ", "_"), NOT_IN))
    c("above materiality on Current Assets", fm["above_materiality"],
      has("completion.uncorrected_misstatements", "current_assets"))
    schedule = d["sad"].get("schedule") or {}
    largest = fm["largest_line"].lower().replace(" ", "_")
    c("summary of misstatements (SAD) carries the schedule's largest line", fm["largest"],
      abs(_dec((schedule.get("lines") or {}).get(largest, "0")))
      if schedule else NOT_IN)
    c("summary of misstatements (SAD) lines at materiality", [largest],
      schedule.get("material_lines", NOT_IN) if schedule else NOT_IN)
    gc = K3["going_concern"]
    s = run("completion.going_concern_indicators")
    for item in ("working_capital", "net_income", "equity", "current_ratio"):
        c(f"going concern: {item.replace('_', ' ')}", gc[item], s.get(item, NOT_IN))
    c("going-concern indicator: current ratio below floor", True,
      has("completion.going_concern_indicators", "current_ratio_below_floor"))
    at = K1["fs.adjusted_trial_balance"]
    s = run("fs.adjusted_trial_balance")
    c("adjusting entries balance", at["entries_balance"],
      s.get("adjusted_debits") == s.get("adjusted_credits") if s else NOT_IN)
    for account, pair in at["changed_accounts"].items():
        c(f"adjusted {account}", pair["adjusted"],
          (s.get("adjusted_balances") or {}).get(account.split(" ")[0], NOT_IN))

    # ---- 13 The opinion
    c.module = MODULES[12]
    op = d["opinion"]
    do = K3["draft_opinion"]
    c("proposed opinion", do["proposal"], op.get("proposed_opinion", NOT_IN))
    basis = " ".join(op.get("basis") or [])
    c("basis: related-parties representation not provided", True,
      "related_parties" in basis)
    c("basis: misstatements above materiality on current assets", True,
      "current_assets" in basis and fm["largest"] in basis)
    decisions = {x["decision"]: x["why"] for x in op.get("decisions_required") or []}
    c("decision: going-concern conclusion (incl. covenant breach)", True,
      "covenant_breached" in decisions.get("going_concern_conclusion", ""))
    c("decision: re-date the representation letter", True,
      "correct_the_representation_letter" in decisions)
    return c


def report(c: Check, outcome: dict) -> str:
    by = defaultdict(list)
    for r in c.rows:
        by[r["module"]].append(r)
    totals = defaultdict(int)
    for r in c.rows:
        totals[r["status"]] += 1
    fmt = lambda v: "—" if v is NOT_IN else (  # noqa: E731
        ", ".join(map(str, v)) if isinstance(v, (list, set, tuple)) else str(v))
    lines = ["# Kestrel finish-line check",
             "",
             "*Written by `finish_line_check.py` (ROADMAP step 0). It seeds the "
             "Workbench demo through the real service path, as `--demo` does, and "
             "compares each Learn module with `answer_key*.json`. Do not edit by "
             "hand; re-run the script.*",
             "",
             f"**{totals['match']} match, {totals['differs']} differ, "
             f"{totals['not in Noesi']} not in Noesi** "
             f"({outcome.get('procedures_run')} procedures run).",
             "",
             "| # | Module | Match | Differ | Not in Noesi |",
             "|---|---|---|---|---|"]
    for i, m in enumerate(MODULES, 1):
        rows = by[m]
        n = lambda s: sum(r["status"] == s for r in rows)  # noqa: E731
        lines.append(f"| {i} | {m} | {n('match')} | {n('differs')} | {n('not in Noesi')} |")
    for i, m in enumerate(MODULES, 1):
        rows = by[m]
        lines += ["", f"## {i}. {m}", ""]
        good = [r["item"] for r in rows if r["status"] == "match"]
        if good:
            lines.append("Matches: " + "; ".join(good) + ".")
        for r in rows:
            if r["status"] != "match":
                lines += ["", f"- **{r['status']}: {r['item']}.** Key {fmt(r['key'])}; "
                              f"Workbench {fmt(r['got'])}. Why: {r['why']}."]
    return "\n".join(lines) + "\n"


def main() -> int:
    svc, outcome = seed()
    data = gather(svc, outcome["engagement_id"])
    data["refused"] = outcome.get("refused", [])
    c = compare(data)
    REPORT.write_text(report(c, outcome), encoding="utf-8")
    for r in c.rows:
        if r["status"] != "match":
            print(f"[{r['status']:<12}] {r['module']}: {r['item']} — {r['why']}")
    unexplained = [r for r in c.rows if r["why"].startswith("UNEXPLAINED")]
    print(f"\n{sum(r['status'] == 'match' for r in c.rows)} of {len(c.rows)} match; "
          f"{len(unexplained)} unexplained. Report: {REPORT.name}")
    return 1 if unexplained else 0


if __name__ == "__main__":
    sys.exit(main())
