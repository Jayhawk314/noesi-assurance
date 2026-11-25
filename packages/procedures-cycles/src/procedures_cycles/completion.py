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
from procedures_cycles.statements import LINES, _totals, apply_adjusting_entries, ratios


def subsequent_events(tables: dict, policies: dict):
    pid = "completion.subsequent_events"
    pe, until = report_window(policies)
    threshold = dec(policies.get("se_threshold"))
    if threshold is None:
        raise PolicyError("policy 'se_threshold' is not set; the size of a subsequent "
                          "transaction worth examining is the auditor's call")
    inside = lambda d: d is not None and pe < d <= until
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
    # Payments after period end may sit in the year's Payments or in the
    # register of payments after year end (Subsequent_payments, 25 Nov 2026);
    # both are read. A register line that repeats a Payments line (same
    # number, date and amount) is the same payment and examined once; any
    # other line is examined, as every Payments line always was.
    in_payments = {(key_text(p.get("payment_number")), day(p.get("payment_date")),
                    money(p.get("payment_amount")))
                   for p in records(tables, "Payments")}
    for role, payment in ([("Payments", p) for p in records(tables, "Payments")]
                          + [("Subsequent_payments", p)
                             for p in records(tables, "Subsequent_payments")]):
        paid = day(payment.get("payment_date"))
        if not inside(paid):
            continue
        if role == "Subsequent_payments" and (
                key_text(payment.get("payment_number")), paid,
                money(payment.get("payment_amount"))) in in_payments:
            continue
        number = key_text(payment.get("payment_number"))
        reviewed["payments"] += 1
        amount = money(payment.get("payment_amount"))
        # the same number in Payments with another date or amount: a second
        # lead under its own key, so the two never merge
        kind = ("payment_in_register" if role == "Subsequent_payments"
                and number in {n for n, _, _ in in_payments} else "payment")
        if abs(amount) >= threshold:
            findings.append(receipt(
                pid, (number, kind), "TENSION",
                f"payment {number} of {abs(amount)} on {paid}, after period end, to "
                f"{text(payment.get('vendor_number')) or 'an unnamed payee'} — does it "
                "settle a liability that existed at period end, or signal a new event?",
                {"finding_class": "CONJECTURE", "cycle": "completion", "date": paid,
                 "amount": amount,
                 "source_rows": [source_ref(role, payment, "payment_number")]},
                abs(amount)))
    if not any(reviewed.values()):
        findings.append(receipt(
            pid, ("no_subsequent_records",), "AMBIGUOUS",
            f"no journal entries or payments dated after {pe} and on or before "
            f"{until} are loaded; the subsequent period has not been examined",
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
    # The statements being reported are the adjusted ones: when adjusting
    # entries are loaded, the indicators are judged after them (AU-C 570
    # evaluates the entity's actual condition, not the unaudited books). The
    # figures before the adjustments stay in the result, and an indicator the
    # adjustments raise or clear is named.
    entries = records(tables, "Adjusting_entries")
    applied = apply_adjusting_entries(tb, entries) if entries else None
    if applied and applied["not_applied"]:
        named = [f"{p[1]} ({'does not balance' if p[0] == 'unbalanced_entry' else f'account {p[2]} is not on the trial balance'})"
                 for p in applied["not_applied"]]
        findings.append(receipt(
            pid, ("adjustments_not_applied",), "AMBIGUOUS",
            f"{len(named)} adjusting entry problem(s) left out of the adjusted figures, so the "
            f"indicators may be incomplete: {'; '.join(named[:12])}",
            {"finding_class": "REFUSAL", "cycle": "completion",
             "not_applied": [list(map(str, p)) for p in applied["not_applied"]]}))
    has_prior = any(r.get("prior_balance") not in (None, "") for r in tb)

    def measure(rows):
        current = ratios(_totals(rows, "balance"))
        t = _totals(rows, "balance")
        out = {"working_capital": money(current["figures"]["current_assets"]
                                        - t["current_liabilities"]),
               "equity": current["figures"]["equity"],
               "net_income": money(current["figures"]["income_before_taxes"]
                                   - t["income_tax"]),
               "current_ratio": current["ratios"]["current_ratio"], "prior_net": None}
        if has_prior:
            pt = _totals(rows, "prior_balance")
            prior = ratios(pt)
            out["prior_net"] = money(prior["figures"]["income_before_taxes"] - pt["income_tax"])
        return out

    def indicators(m):
        """(key, reason, amount, evidence) for each condition, in a fixed order."""
        found = []
        wc, equity, net, ratio = (m["working_capital"], m["equity"], m["net_income"],
                                  m["current_ratio"])
        if wc < 0:
            found.append(("negative_working_capital",
                          f"current liabilities exceed current assets by {-wc}", wc,
                          {"working_capital": wc}))
        if equity < 0:
            found.append(("equity_deficit", f"equity is a deficit of {-equity}", equity,
                          {"equity": equity}))
        if net < 0:
            found.append(("net_loss", f"the period shows a net loss of {-net}", net,
                          {"net": net}))
            if m["prior_net"] is not None and m["prior_net"] < 0:
                found.append(("recurring_losses",
                              f"losses in both years ({-m['prior_net']} last year, {-net} "
                              "this year)", net, {"prior_net": m["prior_net"]}))
        if floor is not None and ratio is not None and ratio < floor:
            found.append(("current_ratio_below_floor",
                          f"the current ratio is {ratio}, below {floor}", None,
                          {"ratio": ratio}))
        return found

    before = measure(tb)
    judged = measure(applied["rows"]) if applied else before
    basis = "after adjusting entries" if applied else "unadjusted trial balance"
    before_keys = [i[0] for i in indicators(before)]
    for key, reason, amount, evidence in indicators(judged):
        if applied and key not in before_keys:
            reason += " (only after the adjusting entries)"
        findings.append(receipt(pid, (key,), "TENSION", reason + " — evaluate whether "
                                "substantial doubt exists about the entity's ability to "
                                "continue as a going concern (AU-C 570)",
                                {"finding_class": "CONJECTURE", "cycle": "completion",
                                 "basis": basis, **evidence}, amount))
    judged_keys = [i[0] for i in indicators(judged)]
    stats = {"population": len(tb), "basis": basis,
             "working_capital": judged["working_capital"], "equity": judged["equity"],
             "net_income": judged["net_income"], "current_ratio": judged["current_ratio"],
             "unclassified_accounts": len(unclassified),
             "indicators": len(judged_keys),
             "exceptions": len(findings)}
    if applied:
        stats.update({
            "adjusting_entries": applied["entries"],
            "before_adjustments": {k: before[k] for k in (
                "working_capital", "equity", "net_income", "current_ratio")},
            "raised_by_adjustments": [k for k in judged_keys if k not in before_keys],
            "cleared_by_adjustments": [k for k in before_keys if k not in judged_keys]})
    return findings, stats


# AU-C 580 written representations every audit needs. Only a row coded to
# one of these counts: the code is the auditor's reviewed reading that the
# sentence makes the representation. Wording is matched only to *suggest* a
# code (every group of words present), never to accept one, because a
# sentence can name a representation and deny it (re-review RR1).
# AU-C 580.25: these (paragraphs .10-.11) not provided means a disclaimer or
# withdrawal; any other is a judgment (AU-C 580, 705).
BASIC_REPRESENTATIONS = frozenset({"fs_responsibility", "internal_control", "all_information",
                                   "all_transactions_recorded"})

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


def _names(value) -> list[str]:
    """Signer entries, split on commas, semicolons and 'and'."""
    raw = text(value).replace(";", ",").replace(" and ", ",").replace(" & ", ",")
    return [" ".join(part.split()).lower() for part in raw.split(",") if part.strip()]


def _coded(row: dict) -> str | None:
    code = key_text(row.get("code")).replace(" ", "_")
    return code if code in REQUIRED_REPRESENTATIONS else None


def _suggested_code(row: dict) -> str | None:
    wording = " ".join(text(row.get("representation")).lower().split())
    for candidate in _ORDER:                   # most specific wording first
        if all(any(word in wording for word in group)
               for group in REQUIRED_REPRESENTATIONS[candidate]):
            return candidate
    return None


def representation_letter(tables: dict, policies: dict):
    pid = "completion.representation_letter"
    _, report_date = report_window(policies)
    # Who must sign is the auditor's decision (management with the
    # appropriate responsibilities). A letter is signed only when each of
    # them appears as a signer entry, exactly; free text such as "signature
    # pending" or "CEO (unsigned)" can never satisfy it (re-review RRR1).
    required_signers = _names(policies.get("rep_signers"))
    if not required_signers:
        raise PolicyError("policy 'rep_signers' is not set; name who must sign the "
                          "letter (e.g. 'CEO, CFO')")
    rows = records(tables, "Representations")
    findings, values, unrecognized = [], {}, []
    suggestions: dict[str, list[str]] = {}
    for row in rows:
        code = _coded(row)
        if code is None:
            wording = text(row.get("representation"))[:80]
            hint = _suggested_code(row)
            if hint:
                suggestions.setdefault(hint, []).append(wording)
            else:
                unrecognized.append(wording)
            continue
        # Only a clear yes counts: blank, pending or unknown is not obtained.
        value = text(row.get("obtained")).lower()
        values.setdefault(code, []).append("obtained" if value in _AFFIRMATIVE
                                           else (value or "blank"))
    for code in REQUIRED_REPRESENTATIONS:
        seen = values.get(code, [])
        if seen and all(v == "obtained" for v in seen):
            continue
        if not seen:
            state = "not in the letter"
            if code in suggestions:
                state += (" as a coded representation; uncoded wording that may be it: "
                          + "; ".join(repr(w) for w in suggestions[code][:2])
                          + " — read it and code it if it makes the representation")
        elif "obtained" in seen:
            state = f"recorded both obtained and {sorted(set(seen) - {'obtained'})}"
        else:
            state = f"marked {sorted(set(seen))}, not obtained"
        basic = code in BASIC_REPRESENTATIONS
        effect = ("AU-C 580.25 requires a disclaimer or withdrawal when this one is not "
                  "provided" if basic else
                  "discuss it with management, re-evaluate management's integrity, and "
                  "decide the effect on the opinion (AU-C 580, 705)")
        findings.append(receipt(
            pid, (code, "not_obtained"), "CLASH",
            f"required representation {code.replace('_', ' ')} is {state} — a scope "
            f"limitation; {effect}",
            {"finding_class": "PROVED_EXCEPTION", "cycle": "completion",
             "representation": code, "status": seen or "missing",
             "requires_disclaimer": basic,
             "uncoded_candidates": suggestions.get(code, [])}))
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
    signers = sorted({n for r in rows for n in _names(r.get("signed_by"))})
    missing = [s for s in required_signers if s not in signers]
    if missing:
        findings.append(receipt(
            pid, ("letter", "unsigned"), "CLASH",
            f"the letter is not signed by {', '.join(missing)} (recorded signers: "
            f"{', '.join(signers) or 'none'})",
            {"finding_class": "PROVED_EXCEPTION", "cycle": "completion",
             "required_signers": required_signers, "signers": signers}))
    stats = {"population": len(rows), "required": len(REQUIRED_REPRESENTATIONS),
             "obtained": sum(1 for v in values.values()
                             if v and all(x == "obtained" for x in v)),
             "signed_by": signers, "report_date": report_date,
             "uncoded_suggestions": suggestions,
             "unrecognized_rows": unrecognized, "exceptions": len(findings)}
    return findings, stats
