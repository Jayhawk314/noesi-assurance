# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""controls.attribute_evaluation — evaluate tests of controls per attribute.

Input rows are the engagement team's attribute-test results (what was
tested, how many items, how many deviations). The engine computes:

- statistical: the exact CUER at the stated risk of overreliance, and the
  AICPA-method planned sample size for the stated EPER/TER;
- nonstatistical: SER + the auditor's estimated sampling risk.

It then compares CUER with TER. CUER above TER means the planned reliance
on that control is not supported; the auditor decides the consequence
(higher control risk, more substantive work) — the engine does not.
"""

from __future__ import annotations

from decimal import Decimal

from procedures_cycles import sampling
from procedures_cycles.common import dec, receipt, records, source_ref, text


def _rate(value) -> float | None:
    d = dec(value)
    if d is None:
        return None
    return float(d / 100) if d >= 1 else float(d)


def attribute_evaluation(tables: dict, policies: dict):
    pid = "controls.attribute_evaluation"
    findings, rows_out = [], []
    rows = records(tables, "Attribute_tests")
    for r in rows:
        attribute = text(r.get("attribute"))
        method = text(r.get("method")).lower() or "statistical"
        n = dec(r.get("sample_size"))
        k = dec(r.get("deviations"))
        ter = _rate(r.get("tolerable_rate"))
        risk = _rate(r.get("risk"))
        eper = _rate(r.get("expected_rate"))
        missing = [name for name, v in (("sample_size", n), ("deviations", k),
                                        ("tolerable_rate", ter)) if v is None]
        if method.startswith("stat") and risk is None:
            missing.append("risk")
        if method.startswith("non") and dec(r.get("estimated_sampling_risk")) is None:
            missing.append("estimated_sampling_risk")
        if missing:
            findings.append(receipt(pid, (attribute, "incomplete"), "AMBIGUOUS",
                                    f"attribute {attribute}: cannot evaluate without "
                                    f"{', '.join(missing)}",
                                    {"finding_class": "REFUSAL", "cycle": "controls"}))
            continue
        n, k = int(n), int(k)
        row = {"attribute": attribute, "method": method, "sample_size": n,
               "deviations": k, "tolerable_rate": ter}
        if method.startswith("non"):
            result = sampling.nonstatistical_attribute(
                n, k, _rate(r.get("estimated_sampling_risk")))
            cuer = Decimal(repr(result["cuer"]))
            row.update({"sample_exception_rate": result["sample_exception_rate"],
                        "estimated_sampling_risk": result["estimated_sampling_risk"],
                        "cuer": cuer})
        else:
            cuer = sampling.attribute_cuer(n, k, risk) / 100
            row.update({"risk": risk, "cuer": cuer})
        if eper is not None and risk is not None:
            # The attribute table sizes a sample for either method; a
            # nonstatistical plan uses it as its guide.
            planned = sampling.attribute_sample_size(eper, ter, risk)
            row["table_sample_size"] = planned
            if planned is not None and n < planned:
                findings.append(receipt(
                    pid, (attribute, "sample_below_plan"), "TENSION",
                    f"attribute {attribute}: {n} items tested, fewer than the "
                    f"{planned} the plan (EPER {eper:.1%}, TER {ter:.1%}) calls for",
                    {"finding_class": "CONJECTURE", "cycle": "controls",
                     "source_rows": [source_ref("Attribute_tests", r, "attribute")]}))
        reliance = cuer <= Decimal(repr(ter))
        row["reliance_supported"] = reliance
        rows_out.append(row)
        findings.append(receipt(
            pid, (attribute,), "AGREE" if reliance else "TENSION",
            (f"attribute {attribute}: CUER {cuer:.1%} ≤ TER {ter:.1%}; planned reliance "
             "is supported" if reliance else
             f"attribute {attribute}: CUER {cuer:.1%} exceeds TER {ter:.1%}; planned "
             "reliance is not supported — reassess control risk"),
            {"finding_class": "COMPOSES" if reliance else "CONJECTURE",
             "kind": "control", "cycle": "controls", **row,
             "source_rows": [source_ref("Attribute_tests", r, "attribute")],
             "limits": "the CUER speaks to the rate of deviation, not its cause; "
                       "each deviation still needs qualitative evaluation"}))
    return findings, {"population": len(rows), "attributes": rows_out,
                      "not_supported": [x["attribute"] for x in rows_out
                                        if not x["reliance_supported"]],
                      "exceptions": sum(1 for f in findings if f.verdict != "AGREE")}
