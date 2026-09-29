# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Inventory: count-to-listing tracing and pricing-test projection.

inventory.count_listing_trace compares the whole count record with the whole
final listing, both directions — completeness (every counted item is listed)
and existence (every listed item was counted) — and checks that identifying
details agree. Doing all items, rather than every k-th, is what software
adds; the observation of the count itself stays the auditor's.

inventory.pricing_projection projects the net pricing misstatement found in
the sample to the listing population (ratio method) and reports the
allowance for sampling risk against the approved tolerable misstatement.
"""

from __future__ import annotations

from procedures_cycles import sampling
from procedures_cycles.common import (
    CENT, ZERO, dec, key_text, money, policy_decimal, receipt, records, source_ref, text,
)


def _norm(value) -> str:
    return " ".join(text(value).lower().split())


def _listing_value(row: dict):
    cost = dec(row.get("cost"))
    if cost is not None:
        return cost
    qty, unit = dec(row.get("quantity")), dec(row.get("unit_cost"))
    return qty * unit if qty is not None and unit is not None else None


def count_listing_trace(tables: dict, policies: dict):
    pid = "inventory.count_listing_trace"
    listing_rows = records(tables, "Inventory_listing")
    count_rows = records(tables, "Inventory_count")
    findings = []

    def index(rows, role):
        out: dict[str, dict] = {}
        for r in rows:
            key = key_text(r.get("stock_number"))
            if key in out:
                findings.append(receipt(pid, (role, "duplicate", key), "CLASH",
                                        f"stock number {key} appears more than once on the "
                                        f"{role.replace('_', ' ').lower()}",
                                        {"finding_class": "PROVED_EXCEPTION",
                                         "cycle": "inventory",
                                         "source_rows": [source_ref(role, r, "stock_number")]}))
            out.setdefault(key, r)
        return out

    listing = index(listing_rows, "Inventory_listing")
    # An item counted in several places has several tags; that is normal,
    # and its count is their sum. What must not repeat is a tag itself (the
    # same tag entered twice is double-counted).
    counted: dict[str, dict] = {}
    tags_per_item: dict[str, int] = {}
    seen_tags: dict[str, dict] = {}
    for r in count_rows:
        tag = key_text(r.get("tag_number"))
        if tag and tag in seen_tags:
            findings.append(receipt(pid, ("Inventory_count", "duplicate_tag", tag), "CLASH",
                                    f"count tag {tag} appears more than once on the "
                                    "inventory count — counted twice?",
                                    {"finding_class": "PROVED_EXCEPTION", "cycle": "inventory",
                                     "source_rows": [source_ref("Inventory_count", seen_tags[tag],
                                                                "tag_number"),
                                                     source_ref("Inventory_count", r,
                                                                "tag_number")]}))
            continue
        if tag:
            seen_tags[tag] = r
        key = key_text(r.get("stock_number"))
        tags_per_item[key] = tags_per_item.get(key, 0) + 1
        if key not in counted:
            counted[key] = dict(r)
            continue
        total, more = dec(counted[key].get("quantity")), dec(r.get("quantity"))
        counted[key]["quantity"] = (None if total is None or more is None
                                    else total + more)
    several_tags = sorted(k for k, n in tags_per_item.items() if n > 1)
    not_listed = sorted(set(counted) - set(listing))
    not_counted = sorted(set(listing) - set(counted))
    for key in not_listed:
        findings.append(receipt(pid, ("counted_not_listed", key), "ORPHAN",
                                f"item {key} was counted but is not on the final listing "
                                "— completeness", {"finding_class": "EXPECTED_BUT_MISSING",
                                                   "cycle": "inventory",
                                                   "assertion": "completeness"}))
    for key in not_counted:
        value = _listing_value(listing[key])
        findings.append(receipt(pid, ("listed_not_counted", key), "ORPHAN",
                                f"item {key} is on the final listing ({value}) but was not "
                                "counted — existence", {"finding_class": "EXPECTED_BUT_MISSING",
                                                        "cycle": "inventory",
                                                        "assertion": "existence"},
                                value))
    mismatched, description_only = [], []
    for key in sorted(set(listing) & set(counted)):
        a, b = listing[key], counted[key]
        diffs = [f for f in ("description", "model")
                 if _norm(a.get(f)) and _norm(b.get(f)) and _norm(a.get(f)) != _norm(b.get(f))]
        # K7: count tags carry shorthand ("Carbon bar"); with the stock number
        # matched, a description that differs alone is recorded, not a lead.
        # A model or quantity difference still is.
        if diffs == ["description"] and not (
                dec(a.get("quantity")) is not None and dec(b.get("quantity")) is not None
                and dec(a.get("quantity")) != dec(b.get("quantity"))):
            description_only.append({"item": key, "count": text(b.get("description")),
                                     "listing": text(a.get("description"))})
            continue
        qa, qb = dec(a.get("quantity")), dec(b.get("quantity"))
        if qa is not None and qb is not None and qa != qb:
            diffs.append("quantity")
        if diffs:
            mismatched.append(key)
            findings.append(receipt(
                pid, ("details_differ", key), "TENSION",
                f"item {key}: {', '.join(diffs)} differ between count "
                f"({', '.join(text(b.get(f)) for f in diffs)}) and listing "
                f"({', '.join(text(a.get(f)) for f in diffs)})",
                {"finding_class": "CONJECTURE", "cycle": "inventory",
                 "source_rows": [source_ref("Inventory_listing", a, "stock_number"),
                                 source_ref("Inventory_count", b, "stock_number")]}))
    extension_errors = 0
    for key, r in listing.items():
        qty, unit, cost = dec(r.get("quantity")), dec(r.get("unit_cost")), dec(r.get("cost"))
        if None not in (qty, unit, cost) and                 (qty * unit).quantize(CENT) != cost.quantize(CENT):
            extension_errors += 1
            findings.append(receipt(pid, ("extension", key), "CLASH",
                                    f"item {key}: {qty} × {unit} ≠ {cost}",
                                    {"finding_class": "PROVED_EXCEPTION",
                                     "cycle": "inventory"}, qty * unit - cost))
    total = sum((v for r in listing.values() if (v := _listing_value(r)) is not None), ZERO)
    return findings, {"population": len(listing_rows), "counted": len(count_rows),
                      "listed_total": total, "counted_not_listed": not_listed,
                      "listed_not_counted": not_counted, "details_differ": mismatched,
                      "items_with_several_tags": several_tags,
                      "description_differs_only": description_only,
                      "extension_errors": extension_errors, "exceptions": len(findings)}


def pricing_projection(tables: dict, policies: dict):
    pid = "inventory.pricing_projection"
    tm = policy_decimal(policies, "inventory_tolerable_misstatement")
    tests = records(tables, "Pricing_tests")
    listing = records(tables, "Inventory_listing")
    findings = []
    population = sum((v for r in listing if (v := _listing_value(r)) is not None), ZERO)
    listed = {key_text(r.get("stock_number")): r for r in listing}
    net = ZERO
    for t in tests:
        key = key_text(t.get("stock_number"))
        recorded, audited = dec(t.get("recorded_cost")), dec(t.get("audited_cost"))
        if key not in listed:
            findings.append(receipt(pid, ("not_on_listing", key), "ORPHAN",
                                    f"priced item {key} is not on the final listing",
                                    {"finding_class": "EXPECTED_BUT_MISSING",
                                     "cycle": "inventory"}))
        if recorded is None or audited is None:
            findings.append(receipt(pid, ("incomplete", key), "AMBIGUOUS",
                                    f"priced item {key} lacks a recorded or audited cost",
                                    {"finding_class": "REFUSAL", "cycle": "inventory"}))
            continue
        diff = recorded - audited
        net += diff
        if diff:
            findings.append(receipt(pid, ("price_difference", key), "CLASH",
                                    f"item {key}: recorded {recorded}, supported cost "
                                    f"{audited} (overstatement positive: {diff})",
                                    {"finding_class": "PROVED_EXCEPTION", "cycle": "inventory",
                                     "source_rows": [source_ref("Pricing_tests", t,
                                                                "stock_number")]}, diff))
    sample_value = sum((money(t.get("recorded_cost")) for t in tests), ZERO)
    declared = dec(policies.get("pricing_sample_value"))
    basis = "recomputed from the pricing-test rows"
    if declared is not None and declared != sample_value:
        basis = ("taken from the approved policy pricing_sample_value; the rows supplied "
                 f"total {sample_value} — only exceptions may have been entered")
        sample_value = declared
    if not sample_value:
        findings.append(receipt(pid, ("no_sample",), "AMBIGUOUS",
                                "no sample value to project from",
                                {"finding_class": "REFUSAL", "cycle": "inventory"}))
        return findings, {"population": len(listing), "exceptions": len(findings)}
    projected = sampling.ratio_projection(net, sample_value, population)
    allowance = sampling.allowance_for_sampling_risk(tm, projected)
    within = abs(projected) < tm
    findings.append(receipt(
        pid, ("evaluation",), "AGREE" if within else "CLASH",
        (f"projected pricing misstatement {projected} leaves an allowance of {allowance} "
         f"against tolerable {tm}; adequacy is the auditor's judgment" if within else
         f"projected pricing misstatement {projected} reaches tolerable {tm}"),
        {"finding_class": "COMPOSES" if within else "PROVED_EXCEPTION", "cycle": "inventory",
         "net_sample_misstatement": net, "sample_value": sample_value,
         "sample_value_basis": basis, "population_value": population,
         "projected_misstatement": projected, "allowance_for_sampling_risk": allowance},
        projected))
    return findings, {"population": len(listing), "tested": len(tests),
                      "net_sample_misstatement": net, "sample_value": sample_value,
                      "sample_value_basis": basis, "population_value": population,
                      "projected_misstatement": projected,
                      "allowance_for_sampling_risk": allowance,
                      "exceptions": sum(1 for f in findings if f.verdict != "AGREE")}
