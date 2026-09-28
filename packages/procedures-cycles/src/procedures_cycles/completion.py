# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Completion procedures: subsequent events, going-concern indicators, and
the management representation letter.

Each turns a completion checkbox into evidence the engine can examine. The
conclusions stay the auditor's: whether a subsequent event is adjusting or
disclosed (AU-C 560), whether substantial doubt exists (AU-C 570), and what
a missing representation means for the report (AU-C 580) — the engine
supplies the leads and the gaps.
"""

from __future__ import annotations

from decimal import Decimal

from procedures_cycles.common import (
    ZERO, PolicyError, dec, day, key_text, money, policy_date, receipt, records,
    report_window, source_ref, text,
)
from procedures_cycles.journal import _entries, _line_amount
from procedures_cycles.statements import LINES, _totals, ratios


def subsequent_events(tables: dict, policies: dict):
    pid = "completion.subsequent_events"
    pe = policy_date(policies, "period_end")
    threshold = dec(policies.get("se_threshold"))
    if threshold is None:
        raise PolicyError("policy 'se_threshold' is not set; the size of a subsequent "
                          "transaction worth examining is the auditor's call")
    until = day(policies.get("report_date"))
    inside = lambda d: d is not None and d > pe and (until is None or d <= until)
    findings = []
    reviewed = {"journal_entries": 0, "payments": 0}
    for entry_id, lines in sorted(_entries(records(tables, "Journal_entries")).items()):
        dated = min((d for d in (day(x.get("entry_date")) for x in lines) if d),
                    default=None)
        if not inside(dated):
            continue
        reviewed["journal_entries"] += 1
        debits = sum((a for a in (_line_amount(x) for x in lines) if a and a > 0), ZERO)
        if debits >= threshold:
            accounts = sorted({key_text(x.get("account")) for x in lines})
            memo = next((text(x.get("description")) for x in lines
                         if text(x.get("description"))), "")
            findings.append(receipt(
                pid, (entry_id, "journal_entry"), "TENSION",
                f"entry {entry_id} on {dated}, after period end: {money(debits)} to "
                f"{', '.join(accounts)}" + (f" ({memo})" if memo else "")
                + " — evidence of a condition at period end (adjust) or a new one "
                  "(disclose if material)?",
                {"finding_class": "CONJECTURE", "cycle": "completion", "date": dated,
                 "amount": debits, "accounts": accounts,
                 "source_rows": [source_ref("Journal_entries", x, "entry_id")
                                 for x in lines]}, debits))
    for payment in records(tables, "Payments"):
        paid = day(payment.get("payment_date"))
        if not inside(paid):
            continue
        reviewed["payments"] += 1
        amount = money(payment.get("payment_amount"))
        if abs(amount) >= threshold:
            number = key_text(payment.get("payment_number"))
            findings.append(receipt(
                pid, (number, "payment"), "TENSION",
                f"payment {number} of {abs(amount)} on {paid}, after period end, to "
                f"{text(payment.get('vendor_number')) or 'an unnamed payee'} — does it "
                "settle a liability that existed at period end, or signal a new event?",
                {"finding_class": "CONJECTURE", "cycle": "completion", "date": paid,
                 "amount": amount,
                 "source_rows": [source_ref("Payments", payment, "payment_number")]},
                abs(amount)))
    if not any(reviewed.values()):
        findings.append(receipt(
            pid, ("no_subsequent_records",), "AMBIGUOUS",
            f"no journal entries or payments dated after {pe}"
            + (f" and on or before {until}" if until else "")
            + " are loaded; the subsequent period has not been examined",
            {"finding_class": "REFUSAL", "cycle": "completion"}))
    stats = {"population": sum(reviewed.values()), "reviewed": reviewed,
             "period_end": pe, "report_date": until, "threshold": threshold,
             "exceptions": len(findings)}
    return findings, stats


def going_concern_indicators(tables: dict, policies: dict):
    pid = "completion.going_concern_indicators"
    tb = records(tables, "Trial_balance")
    floor = dec(policies.get("gc_current_ratio_floor"))
    findings = []
    unclassified = sorted({key_text(r.get("account")) for r in tb
                           if text(r.get("line")).lower() not in LINES})
    if unclassified:
        findings.append(receipt(
            pid, ("unclassified_accounts",), "AMBIGUOUS",
            f"{len(unclassified)} account(s) have no recognized statement line and are "
            f"left out, so the indicators may be incomplete: "
            f"{', '.join(unclassified[:12])}",
            {"finding_class": "REFUSAL", "cycle": "completion",
             "accounts": unclassified}))
    has_prior = any(r.get("prior_balance") not in (None, "") for r in tb)
    years = {"current": ratios(_totals(tb, "balance"))}
    if has_prior:
        years["prior"] = ratios(_totals(tb, "prior_balance"))

    def figure(year, name):
        return years[year]["figures"][name]

    t = _totals(tb, "balance")
    working_capital = money(figure("current", "current_assets") - t["current_liabilities"])
    equity = figure("current", "equity")
    net = money(figure("current", "income_before_taxes") - t["income_tax"])

    def indicator(key, reason, amount=None, **evidence):
        findings.append(receipt(pid, (key,), "TENSION", reason + " — evaluate whether "
                                "substantial doubt exists about the entity's ability to "
                                "continue as a going concern (AU-C 570)",
                                {"finding_class": "CONJECTURE", "cycle": "completion",
                                 **evidence}, amount))

    if working_capital < 0:
        indicator("negative_working_capital",
                  f"current liabilities exceed current assets by {-working_capital}",
                  working_capital, working_capital=working_capital)
    if equity < 0:
        indicator("equity_deficit", f"equity is a deficit of {-equity}", equity,
                  equity=equity)
    if net < 0:
        indicator("net_loss", f"the period shows a net loss of {-net}", net, net=net)
        if has_prior:
            pt = _totals(tb, "prior_balance")
            prior_net = money(figure("prior", "income_before_taxes") - pt["income_tax"])
            if prior_net < 0:
                indicator("recurring_losses",
                          f"losses in both years ({-prior_net} last year, {-net} this "
                          "year)", net, prior_net=prior_net)
    ratio = years["current"]["ratios"]["current_ratio"]
    if floor is not None and ratio is not None and ratio < floor:
        indicator("current_ratio_below_floor",
                  f"the current ratio is {ratio}, below {floor}", ratio=ratio)
    stats = {"population": len(tb), "working_capital": working_capital,
             "equity": equity, "net_income": net,
             "current_ratio": ratio, "unclassified_accounts": len(unclassified),
             "indicators": len([f for f in findings if f.verdict == "TENSION"]),
             "exceptions": len(findings)}
    return findings, stats


# AU-C 580 written representations every audit needs. A letter that lists
# them without these codes is read by wording: every group must appear (any
# word within a group), so the sentence has to make the representation, not
# merely mention its subject. Codes remain the reliable way to identify one.
REQUIRED_REPRESENTATIONS: dict[str, tuple[tuple[str, ...], ...]] = {
    "fs_responsibility": (("responsib",), ("financial statements",)),
    "internal_control": (("responsib",), ("internal control",)),
    "all_information": (("provided", "made available", "access"),
                        ("all information", "all records", "all relevant information",
                         "all financial records")),
    "all_transactions_recorded": (("all transactions",), ("recorded", "reflected")),
    "fraud": (("fraud",), ("knowledge", "aware", "disclosed", "informed")),
    "fraud_allegations": (("allegation",), ("fraud",)),
    "laws_regulations": (("noncompliance", "non-compliance", "violation"),
                         ("laws", "regulations")),
    "uncorrected_misstatements": (("uncorrected misstatements",),
                                  ("immaterial", "not material")),
    "litigation_claims": (("litigation", "claims"),
                          ("disclosed", "aware", "accounted", "no ")),
    "estimates": (("estimates",), ("reasonable", "appropriate")),
    "related_parties": (("related part",),
                        ("disclosed", "identified", "accounted", "made known")),
    "subsequent_events": (("subsequent",), ("event", "occurred"), ("adjust", "disclos")),
}
_ORDER = ("fraud_allegations", "uncorrected_misstatements", "related_parties",
          "subsequent_events", "internal_control", "litigation_claims",
          "laws_regulations", "all_transactions_recorded", "all_information",
          "estimates", "fraud", "fs_responsibility")
_AFFIRMATIVE = {"yes", "y", "true", "obtained", "received", "provided", "signed", "x"}
_NOT_A_SIGNER = {"no", "none", "unsigned", "not signed", "n/a", "na", "-", "pending",
                 "tbd", "unknown", "to follow"}


def _code_of(row: dict) -> str | None:
    code = key_text(row.get("code")).replace(" ", "_")
    if code in REQUIRED_REPRESENTATIONS:
        return code
    wording = " ".join(text(row.get("representation")).lower().split())
    for candidate in _ORDER:                   # most specific wording first
        if all(any(word in wording for word in group)
               for group in REQUIRED_REPRESENTATIONS[candidate]):
            return candidate
    return None


def representation_letter(tables: dict, policies: dict):
    pid = "completion.representation_letter"
    _, report_date = report_window(policies)
    rows = records(tables, "Representations")
    findings, status, unrecognized = [], {}, []
    for row in rows:
        code = _code_of(row)
        if code is None:
            unrecognized.append(text(row.get("representation"))[:80])
            continue
        value = text(row.get("obtained")).lower()
        # Only a clear yes counts: blank, pending or unknown is not obtained.
        if value in _AFFIRMATIVE or status.get(code) == "obtained":
            status[code] = "obtained"
        else:
            status[code] = value or "blank"
    for code in REQUIRED_REPRESENTATIONS:
        state = status.get(code)
        if state == "obtained":
            continue
        findings.append(receipt(
            pid, (code, "not_obtained"), "CLASH",
            f"required representation {code.replace('_', ' ')} is "
            + (f"marked {state!r}, not obtained" if state else "not in the letter")
            + " — a scope limitation; AU-C 580 requires a disclaimer or withdrawal "
              "when required representations are not provided",
            {"finding_class": "PROVED_EXCEPTION", "cycle": "completion",
             "representation": code, "status": state or "missing"}))
    dates = sorted({d for d in (day(r.get("dated")) for r in rows) if d})
    if not dates:
        findings.append(receipt(pid, ("letter", "undated"), "CLASH",
                                "the representation letter carries no date",
                                {"finding_class": "PROVED_EXCEPTION",
                                 "cycle": "completion"}))
    elif dates != [report_date]:
        findings.append(receipt(
            pid, ("letter", "not_dated_report_date"), "CLASH",
            f"the letter is dated {', '.join(str(d) for d in dates)}; it must be dated "
            f"as of the report date {report_date}",
            {"finding_class": "PROVED_EXCEPTION", "cycle": "completion",
             "dates": dates, "report_date": report_date}))
    signers = sorted({text(r.get("signed_by")) for r in rows
                      if text(r.get("signed_by"))
                      and text(r.get("signed_by")).lower() not in _NOT_A_SIGNER})
    if not signers:
        findings.append(receipt(pid, ("letter", "unsigned"), "CLASH",
                                "no one is recorded as signing the representation letter",
                                {"finding_class": "PROVED_EXCEPTION",
                                 "cycle": "completion"}))
    stats = {"population": len(rows), "required": len(REQUIRED_REPRESENTATIONS),
             "obtained": sum(1 for v in status.values() if v == "obtained"),
             "signed_by": signers, "report_date": report_date,
             "unrecognized_rows": unrecognized, "exceptions": len(findings)}
    return findings, stats
