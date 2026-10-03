# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Accounts receivable: listing tie-out and confirmation evaluation.

Confirmation replies and the classification of each difference (client
misstatement, timing difference, customer error) are auditor evidence. The
engine refuses to evaluate a difference nobody has classified; it never
decides for itself that a difference is "only timing".

Three evaluation methods, one procedure each — the team selects the one its
sampling plan used:
- ar.confirmations_nonstatistical: ratio projection over the stratum below
  tolerable misstatement, individually significant accounts added as found;
- ar.confirmations_mus: monetary-unit sampling upper misstatement limit;
- ar.confirmations_difference: difference estimation confidence limits.
"""

from __future__ import annotations

from decimal import Decimal

from procedures_cycles import sampling
from procedures_cycles.common import (
    ZERO, PolicyError, dec, key_text, money, policy_decimal, policy_rate, receipt,
    records, source_ref, text,
)
from procedures_cycles.statements import _signed

AGING_BUCKETS = ("current", "days_1_30", "days_31_60", "days_61_90", "days_over_90")
CLASSIFICATIONS = ("no_difference", "client_misstatement", "timing", "customer_error",
                   "alternative_procedures")


def listing_tie(tables: dict, policies: dict):
    pid = "ar.listing_tie"
    listing = records(tables, "AR_listing")
    tb = records(tables, "Trial_balance")
    findings = []
    total = sum((money(r.get("balance")) for r in listing), ZERO)
    gl = sum((_signed(r) or ZERO for r in tb
              if text(r.get("line")).lower() == "receivables"), ZERO)
    if total != gl:
        findings.append(receipt(pid, ("listing_to_gl",), "CLASH",
                                f"AR listing totals {total}; the trial balance "
                                f"receivables line is {gl}",
                                {"finding_class": "PROVED_EXCEPTION", "cycle": "receivables",
                                 "listing_total": total, "gl_total": gl}, total - gl))
    customers: set[str] = set()
    aged = 0
    for r in listing:
        cust = key_text(r.get("customer_number"))
        customers.add(cust)
        buckets = [dec(r.get(f)) for f in AGING_BUCKETS]
        if any(b is not None for b in buckets):
            aged += 1
            bucket_sum = sum((b for b in buckets if b is not None), ZERO)
            if bucket_sum.quantize(Decimal("0.01")) != money(r.get("balance")):
                findings.append(receipt(
                    pid, ("aging_does_not_foot", cust), "CLASH",
                    f"customer {cust}: aging buckets total {bucket_sum}, "
                    f"balance {money(r.get('balance'))}",
                    {"finding_class": "PROVED_EXCEPTION", "cycle": "receivables",
                     "source_rows": [source_ref("AR_listing", r, "customer_number")]},
                    bucket_sum - money(r.get("balance"))))

    # A credit memo line on an invoice-detail export is normal; what matters
    # is a customer whose *net* balance is a credit.
    for cust, balance in sorted(_customer_balances(tables).items()):
        if balance < 0:
            findings.append(receipt(
                pid, ("credit_balance", cust), "TENSION",
                f"customer {cust} carries a net credit balance {balance}; "
                "consider reclassification to liabilities",
                {"finding_class": "CONJECTURE", "cycle": "receivables",
                 "net_balance": balance}))
    # The aging carries a 1-30 column (current meaning "not yet due") or not
    # (current meaning 0-30); the allowance rates follow the columns it has.
    # A mapped column still exists when every value in it is blank. Test the
    # records' shape, not their amounts, or a blank 1-30 column silently turns
    # a five-rate method into a four-rate method and shifts every older rate.
    fields = [f for f in AGING_BUCKETS
              if f != "days_1_30" or any(f in r for r in listing)]
    buckets = {f: sum((money(r.get(f)) for r in listing), ZERO) for f in fields}
    stats = {"population": len(listing), "customers": len(customers),
             "listing_total": total, "gl_total": gl,
             "aged_rows": aged, "aging_totals": buckets}
    rates_policy = text(policies.get("ar_allowance_rates"))
    if rates_policy:
        # The client's allowance method, applied to the aging: an estimate
        # the auditor recomputes, not one the engine invents.
        rates = parse_allowance_rates(rates_policy)
        if len(rates) != len(fields):
            raise PolicyError(
                f"ar_allowance_rates has {len(rates)} rates; this aging has "
                f"{len(fields)} columns ({', '.join(fields)}), one rate each")
        # A customer whose net balance is a credit owes nothing to reserve
        # against (it is a liability, flagged above), so it is left out.
        by_customer: dict[str, list[Decimal]] = {}
        for r in listing:
            amounts = by_customer.setdefault(key_text(r.get("customer_number")),
                                             [ZERO] * len(fields))
            for i, f in enumerate(fields):
                amounts[i] += money(r.get(f))
        net = _customer_balances(tables)
        required = sum((amount * rate
                        for cust, amounts in by_customer.items() if net.get(cust, ZERO) > 0
                        for amount, rate in zip(amounts, rates)),
                       ZERO).quantize(Decimal("0.01"))
        recorded = -sum((_signed(r) or ZERO for r in tb
                         if text(r.get("line")).lower() == "allowance"), ZERO)
        stats.update({"allowance_required": required, "allowance_recorded": recorded,
                      "allowance_rates": [str(r) for r in rates]})
        # Reported to the cent (it is the adjusting entry's amount); a
        # difference under a dollar is rounding in the client's booking.
        if abs(required - recorded) >= 1:
            findings.append(receipt(
                pid, ("allowance_estimate",), "CLASH",
                f"allowance recomputed from the aging is {required}; the books carry "
                f"{recorded} — difference {required - recorded}",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "receivables",
                 "assertion": "valuation", "required": required, "recorded": recorded,
                 "limits": "rates are the client's method as approved by the auditor; "
                           "their adequacy is a separate judgment"},
                required - recorded))
    stats["exceptions"] = len(findings)
    return findings, stats


def parse_allowance_rates(value: str) -> list[Decimal]:
    """The partner's allowance rates: four (current, 31-60, 61-90, over 90)
    or five (current, 1-30, 31-60, 61-90, over 90), each between 0 and 1."""
    rates = [dec(x) for x in text(value).replace(";", ",").split(",")]
    if len(rates) not in (4, 5) or any(r is None or not 0 <= r <= 1 for r in rates):
        raise PolicyError("ar_allowance_rates needs four or five rates between 0 and 1, "
                          "one per aging column, oldest last (e.g. '0.03,0.10,0.15,0.30' "
                          "or '0.01,0.02,0.05,0.15,0.40')")
    return rates


def _customer_balances(tables: dict) -> dict[str, Decimal]:
    """Aggregate summary or invoice-detail A/R rows to the confirmation unit."""
    balances: dict[str, Decimal] = {}
    for row in records(tables, "AR_listing"):
        customer = key_text(row.get("customer_number"))
        balances[customer] = balances.get(customer, ZERO) + money(row.get("balance"))
    return balances


def _confirmation_rows(tables: dict, pid: str, findings: list):
    """Join confirmations to the listing; refuse unclassified differences."""
    listing = _customer_balances(tables)
    out = []
    for c in records(tables, "Confirmations"):
        cust = key_text(c.get("customer_number"))
        book = dec(c.get("book_value"))
        listed = listing.get(cust)
        if listed is None:
            findings.append(receipt(pid, ("not_on_listing", cust), "ORPHAN",
                                    f"confirmation for customer {cust}, who is not on the "
                                    "AR listing",
                                    {"finding_class": "EXPECTED_BUT_MISSING",
                                     "cycle": "receivables"}))
            continue
        listed_balance = listed.quantize(Decimal("0.01"))
        if book is None:
            book = listed_balance
        elif book.quantize(Decimal("0.01")) != listed_balance:
            findings.append(receipt(
                pid, ("book_value_mismatch", cust), "CLASH",
                f"customer {cust}: confirmation shows book value {book}, the listing "
                f"{listed_balance}",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "receivables"},
                book - listed_balance))
        confirmed = dec(c.get("confirmed_value"))
        classification = text(c.get("classification")).lower().replace(" ", "_")
        difference = (book - confirmed) if confirmed is not None else None
        stated = dec(c.get("client_misstatement"))
        if stated is not None:
            misstatement = stated
        elif classification.startswith("client"):
            misstatement = difference if difference is not None else None
        elif classification in CLASSIFICATIONS or (difference == 0):
            misstatement = ZERO
        else:
            misstatement = None
        if misstatement is None:
            findings.append(receipt(
                pid, ("unclassified_difference", cust), "AMBIGUOUS",
                f"customer {cust}: difference {difference} has not been classified "
                "(client misstatement, timing, customer error)",
                {"finding_class": "REFUSAL", "cycle": "receivables",
                 "source_rows": [source_ref("Confirmations", c, "customer_number")]}))
            continue
        out.append({"customer": cust, "book": book, "confirmed": confirmed,
                    "difference": difference, "classification": classification or None,
                    "misstatement": misstatement,
                    "stratum": text(c.get("stratum")).lower(), "record": c})
    return out


def _misstatement_findings(pid: str, rows: list[dict], findings: list):
    for row in rows:
        if row["misstatement"]:
            findings.append(receipt(
                pid, ("client_misstatement", row["customer"]), "CLASH",
                f"customer {row['customer']}: client misstatement "
                f"{abs(row['misstatement']):,.2f} "
                f"({'overstatement' if row['misstatement'] > 0 else 'understatement'})",
                {"finding_class": "PROVED_EXCEPTION", "cycle": "receivables",
                 "book_value": row["book"], "confirmed_value": row["confirmed"],
                 "classification": row["classification"],
                 "source_rows": [source_ref("Confirmations", row["record"],
                                            "customer_number")]},
                row["misstatement"]))


def confirmations_nonstatistical(tables: dict, policies: dict):
    pid = "ar.confirmations_nonstatistical"
    tm = policy_decimal(policies, "ar_tolerable_misstatement")
    findings: list = []
    listing = records(tables, "AR_listing")
    customer_balances = _customer_balances(tables)
    rows = _confirmation_rows(tables, pid, findings)
    significant = [r for r in rows if r["book"] > tm]
    # K12: the population projected over is the debit balances; a credit
    # balance owes nothing to sample and is flagged on its own. A confirmed
    # credit balance is kept out of the sample too, or its negative book
    # value shrinks the sample and inflates the projection; its misstatement
    # counts as found, never projected.
    sampled = [r for r in rows if ZERO < r["book"] <= tm]
    credit_confirmed = [r for r in rows if r["book"] <= ZERO]
    stratum_value = sum((balance for balance in customer_balances.values()
                         if ZERO < balance <= tm), ZERO)
    credits_excluded = sorted(c for c, b in customer_balances.items() if b < 0)
    sample_value = sum((r["book"] for r in sampled), ZERO)
    known = sum((r["misstatement"] for r in significant + credit_confirmed), ZERO)
    sample_misstatement = sum((r["misstatement"] for r in sampled), ZERO)
    projected_sample = (sampling.ratio_projection(sample_misstatement, sample_value,
                                                  stratum_value)
                        if sample_value else ZERO)
    total = known + projected_sample
    allowance = sampling.allowance_for_sampling_risk(tm, total)
    _misstatement_findings(pid, rows, findings)
    within = abs(total) < tm
    findings.append(receipt(
        pid, ("evaluation",), "AGREE" if within else "CLASH",
        (f"projected misstatement {total} leaves an allowance for sampling risk of "
         f"{allowance} against tolerable {tm}; whether that allowance is adequate is "
         "the auditor's judgment") if within else
        (f"projected misstatement {total} is at or above tolerable misstatement {tm}"),
        {"finding_class": "COMPOSES" if within else "PROVED_EXCEPTION",
         "cycle": "receivables", "method": "nonstatistical ratio projection",
         "individually_significant_misstatement": known,
         "sample_misstatement": sample_misstatement, "sample_value": sample_value,
         "stratum_value": stratum_value, "projected_sample_misstatement": projected_sample,
         "projected_total": total, "allowance_for_sampling_risk": allowance,
         "limits": "nonstatistical: sampling risk is judged, not measured"},
        total))
    stats = {"population": len(customer_balances), "listing_rows": len(listing),
             "credit_balances_excluded": credits_excluded,
             "credit_balances_confirmed": sorted(r["customer"] for r in credit_confirmed),
             "confirmations": len(rows),
             "significant": len(significant), "sampled": len(sampled),
             "stratum_value": stratum_value, "sample_value": sample_value,
             "known_misstatement": known, "projected_sample_misstatement": projected_sample,
             "projected_total": total, "allowance_for_sampling_risk": allowance,
             "exceptions": sum(1 for f in findings if f.verdict != "AGREE")}
    cf = dec(policies.get("ar_confidence_factor"))
    if cf is not None:
        stats["planned_sample_size"] = sampling.nonstatistical_sample_size(
            stratum_value, tm, cf)
    return findings, stats


def confirmations_mus(tables: dict, policies: dict):
    pid = "ar.confirmations_mus"
    tm = policy_decimal(policies, "ar_tolerable_misstatement")
    risk = policy_rate(policies, "ar_risk_incorrect_acceptance")
    interval = policy_decimal(policies, "mus_interval")
    findings: list = []
    listing = records(tables, "AR_listing")
    customer_balances = _customer_balances(tables)
    rows = _confirmation_rows(tables, pid, findings)
    # A confirmed credit balance is not a sampling unit (a negative book value
    # has no tainting); its misstatement is added in full, like a large item.
    large = [r for r in rows if r["book"] > tm or r["book"] >= interval
             or r["book"] <= ZERO]
    units = [r for r in rows if r not in large]
    taintings = []
    for r in units:
        if r["misstatement"] and r["book"]:
            t = sampling.tainting(r["misstatement"], r["book"])
            r["tainting"] = t
            taintings.append(t)
    large_misstatement = sum((r["misstatement"] for r in large), ZERO)
    result = sampling.mus_evaluate(interval, taintings, risk,
                                   large_item_misstatement=large_misstatement)
    _misstatement_findings(pid, rows, findings)
    uml = result["upper_misstatement_limit"]
    within = uml <= tm
    findings.append(receipt(
        pid, ("evaluation",), "AGREE" if within else "CLASH",
        (f"upper misstatement limit {uml} ≤ tolerable {tm} at {risk:.0%} ARIA"
         if within else f"upper misstatement limit {uml} exceeds tolerable {tm} "
                        f"at {risk:.0%} ARIA"),
        {"finding_class": "COMPOSES" if within else "PROVED_EXCEPTION",
         "cycle": "receivables", "method": "monetary unit sampling",
         "sampling_interval": interval, **{k: v for k, v in result.items()},
         "limits": "overstatement bound only; understatement taintings are listed "
                   "and must be evaluated separately"},
        uml))
    population = sum((balance for balance in customer_balances.values()
                      if ZERO < balance <= tm), ZERO)
    stats = {"population": len(customer_balances), "listing_rows": len(listing),
             "confirmations": len(rows),
             "large_items": len(large), "unit_items": len(units),
             "sampling_interval": interval, "mus_population_value": population,
             **result, "exceptions": sum(1 for f in findings if f.verdict != "AGREE")}
    expected = dec(policies.get("ar_expected_misstatement"))
    if expected is not None and population:
        cf = sampling.round_factor(sampling.mus_confidence_factor(float(expected / tm), risk))
        stats["planned_confidence_factor"] = cf
        stats["planned_sample_size"] = sampling.mus_sample_size(population, tm, float(cf))
    return findings, stats


def confirmations_difference(tables: dict, policies: dict):
    pid = "ar.confirmations_difference"
    tm = policy_decimal(policies, "ar_tolerable_misstatement")
    aria = policy_rate(policies, "ar_risk_incorrect_acceptance")
    findings: list = []
    listing = records(tables, "AR_listing")
    customer_balances = _customer_balances(tables)
    rows = _confirmation_rows(tables, pid, findings)
    z_a = sampling.z_coefficient(aria)
    stats = {"population": len(customer_balances), "listing_rows": len(listing),
             "confirmations": len(rows), "z_a": z_a}
    if len(rows) < 2:
        findings.append(receipt(pid, ("too_few",), "AMBIGUOUS",
                                "difference estimation needs at least two evaluated "
                                "confirmations", {"finding_class": "REFUSAL",
                                                  "cycle": "receivables"}))
        return findings, {**stats, "exceptions": len(findings)}
    # Every sampled account must be itemized, differences or not: the sample
    # size is the number of rows, never a number typed in beside them.
    result = sampling.difference_evaluate(
        [r["misstatement"] for r in rows], len(customer_balances), z_a, tm)
    _misstatement_findings(pid, rows, findings)
    within = result["within_tolerable"]
    findings.append(receipt(
        pid, ("evaluation",), "AGREE" if within else "CLASH",
        (f"confidence limits {result['lower_limit']} to {result['upper_limit']} lie within "
         f"±{tm}" if within else
         f"confidence limits {result['lower_limit']} to {result['upper_limit']} extend "
         f"beyond ±{tm}"),
        {"finding_class": "COMPOSES" if within else "PROVED_EXCEPTION",
         "cycle": "receivables", "method": "difference estimation", **result,
         "limits": "assumes the sampled accounts were selected randomly"},
        result["projected_misstatement"]))
    stats.update(result)
    sd = dec(policies.get("ar_estimated_sd"))
    arir = policies.get("ar_risk_incorrect_rejection")
    expected = dec(policies.get("ar_expected_misstatement"))
    if sd is not None and arir not in (None, "") and expected is not None:
        z_r = sampling.z_coefficient(policy_rate(policies, "ar_risk_incorrect_rejection"),
                                     two_sided=True)
        stats["z_r"] = z_r
        stats["planned_sample_size"] = sampling.difference_sample_size(
            len(customer_balances), sd, z_a, z_r, tm, expected)
    stats["exceptions"] = sum(1 for f in findings if f.verdict != "AGREE")
    return findings, stats
