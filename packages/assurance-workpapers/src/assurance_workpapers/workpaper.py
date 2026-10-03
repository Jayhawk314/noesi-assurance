# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Render one self-contained HTML workpaper from an evidence packet.

A document, not an application: inline styles, no scripts, nothing loaded
from anywhere. Every table row traces to content in the packet.
"""

from __future__ import annotations

import html
import json


def _esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def _row(cells: list, tag: str = "td") -> str:
    inner = "".join(f"<{tag}>{_esc(cell)}</{tag}>" for cell in cells)
    return f"<tr>{inner}</tr>"


def _cents(value) -> str:
    """An amount to the cent with thousands commas; anything else as it is."""
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "" if value is None else str(value)


def _table(headers: list[str], rows: list[list]) -> str:
    head = _row(headers, "th")
    body = "".join(_row(row) for row in rows)
    return f"<table>{head}{body}</table>"


_STYLE = """
body { font-family: Georgia, serif; margin: 2rem auto; max-width: 60rem;
       color: #1a1a1a; }
h1 { font-size: 1.5rem; border-bottom: 2px solid #1a1a1a; }
h2 { font-size: 1.1rem; margin-top: 2rem; }
table { border-collapse: collapse; width: 100%; font-size: 0.85rem;
        font-family: system-ui, sans-serif; }
th { text-align: left; border-bottom: 2px solid #444; padding: 4px 8px; }
td { border-bottom: 1px solid #ccc; padding: 4px 8px; vertical-align: top; }
code { font-size: 0.75rem; word-break: break-all; }
.limits { background: #f6f3e8; border: 1px solid #d8cfa8; padding: 1rem;
          font-size: 0.85rem; }
.meta { font-family: system-ui, sans-serif; font-size: 0.85rem; }
"""


def render_workpaper(packet: dict) -> str:
    engagement = packet["engagement"]
    manifest = packet.get("manifest") or {}
    seal = packet.get("seal", {})
    sad = packet.get("summary_of_audit_differences", {})
    provenance = f"""
The record as it stood at {_esc(packet['generated'])}; unsigned. It supplements
 the audit file; the firm's own review and sign-off are outside it.<br>
Record manifest digest <code>{_esc(packet.get('manifest_digest', ''))}</code><br>
Packet digest <code>{_esc(seal.get('packet_digest', 'unsealed'))}</code>"""
    trail = manifest.get("journal_check")
    if trail is not None and trail.get("ok") is not True:
        provenance += (
            "<br><b>Decision trail BROKEN</b> at journal entry "
            f"{_esc(trail.get('break_at_seq'))}: an entry was edited outside the "
            "Workbench, so this record's history cannot be relied on.")

    sections = [f"""
<h1>Working paper — {_esc(engagement['client_name'])}
 (FYE {_esc(engagement['period_end'])})</h1>
<p class="meta">
Packet {_esc(packet['packet_version'])} · generated {_esc(packet['generated'])}
 · software {_esc(packet['software'])}<br>{provenance}
</p>"""]

    opinion = packet.get("opinion")
    if opinion:
        # "Opinion" only once the file is ready and the partner's judgments
        # are recorded; before that it is a draft, whatever it settles to.
        settled = opinion.get("opinion") if opinion.get("status") != "not_ready" else None
        label = (settled or opinion.get("proposed_opinion", "")).replace("_", " ")
        recorded = opinion.get("recorded_decisions") or {}
        open_decisions = opinion.get("decisions_required") or []
        sections.append(
            "<h2>Opinion</h2>"
            f"<p><b>{'Opinion' if settled else 'Draft opinion (not settled)'}: "
            f"{_esc(label)}</b>"
            + (" — with a going-concern section" if opinion.get("going_concern_section")
               else "") + "</p>"
            "<h3>Basis</h3><ul>"
            + "".join(f"<li>{_esc(b)}</li>" for b in opinion.get("basis", []))
            + "</ul>"
            + f"<p class='meta'>Uncorrected misstatements: "
              f"{_esc(_cents(opinion.get('misstatements', {}).get('amount')))} on "
              f"{_esc(str(opinion.get('misstatements', {}).get('largest_line', '')).replace('_', ' '))} against "
              f"materiality {_esc(_cents(opinion.get('materiality')))}. Source: "
              f"{_esc(opinion.get('misstatements', {}).get('source'))}.</p>"
            + ("<h3>Partner's decisions</h3>" + _table(
                ["Decision", "Answer", "Reason", "Decided by"],
                [[k.replace("_", " "), v.get("answer", "").replace("_", " "),
                  v.get("note", ""), v.get("decided_by", "")]
                 for k, v in recorded.items()]) if recorded else "")
            + ("<h3>Still to decide</h3><ul>"
               + "".join(f"<li>{_esc(d['decision'].replace('_', ' '))}: "
                         f"{_esc(d['why'])}</li>" for d in open_decisions) + "</ul>"
               if open_decisions else "")
            + f"<p class='meta'>{_esc(opinion.get('note', ''))}</p>")
        if opinion.get("status") == "not_ready":
            # Before the file is ready no opinion is supported yet, whatever the
            # ladder proposes: say so above everything else in the section.
            blockers = opinion.get("readiness_blockers") or []
            sections[-1] = sections[-1].replace(
                "<h2>Opinion</h2>",
                "<h2>Opinion</h2><div class='limits'><b>NOT READY.</b> The evidence "
                "does not yet support any opinion; what follows is where the "
                "record points so far. Still open: "
                + (_esc(", ".join(f"{b.get('code')} ({b.get('count')})"
                                  for b in blockers))
                   or "the partner's decisions listed under Still to decide")
                + ".</div>", 1)

    scope = packet.get("scope")
    if scope:
        materiality = scope.get("materiality") or {}
        sections.append("<h2>Scope and settings</h2>" + _table(
            ["Item", "Value"],
            [["Period", f"{scope.get('period_start') or '12 months to'} – "
                        f"{scope.get('period_end')}"],
             ["Materiality", f"{materiality.get('amount')} "
                             f"({materiality.get('basis', '')})"],
             ["Audit areas", ", ".join(c.replace('_', ' ')
                                       for c in scope.get("cycles", [])) or "payables"]]
            + [[f"setting: {k.replace('_', ' ')}", v]
               for k, v in sorted((scope.get("policies") or {}).items())]))

    # The risk assessment and how each risk is answered. A linked procedure
    # that did not run answers nothing; readiness names it, and so does this.
    risks = [r for r in manifest.get("risks", []) if not r.get("archived")]
    if risks:
        not_performed = []
        for blocker in (opinion or {}).get("readiness_blockers") or []:
            if blocker.get("code") == "HIGH_RISK_RESPONSES_NOT_PERFORMED":
                not_performed = list(blocker.get("items") or [])
        rows = []
        for r in risks:
            title = r.get("title") or r.get("risk_id")
            linked = r.get("procedure_ids") or []
            if isinstance(linked, str):
                linked = json.loads(linked or "[]")
            prefix = f"{title}: "      # a title may itself hold ": "
            gaps = [item[len(prefix):] for item in not_performed
                    if item.startswith(prefix)]
            rows.append([
                title + (" (fraud risk)" if r.get("fraud") else ""),
                r.get("assertion", ""), r.get("level", ""), r.get("response", ""),
                ", ".join(linked) or "none linked",
                "; ".join(gaps) or "—"])
        sections.append("<h2>Risks of material misstatement</h2>" + _table(
            ["Risk", "Assertion", "Level", "Planned response", "Responding procedures",
             "Responses that did not run"], rows))

    sections.append("<h2>Source inventory</h2>" + _table(
        ["File", "SHA-256", "Bytes", "State"],
        [[a["original_name"], a["sha256"][:16] + "…", a["size_bytes"],
          a["state"]] for a in manifest.get("artifacts", [])]))

    # One user confirms a mapping (D9). Old records may show a proposer and a
    # different approver; the confirmer is whoever confirmed it last.
    specs = {m["spec_id"]: m for m in manifest["mapping_specs"]}
    sections.append("<h2>Confirmed mappings and datasets</h2>" + _table(
        ["Role", "Mapping", "Confirmed by", "Rows in/loaded/rejected", "Control total"],
        [[d["role"],
          {"approved": "confirmed", "proposed": "not confirmed"}.get(
              specs.get(d["mapping_spec_id"], {}).get("status", "?"),
              specs.get(d["mapping_spec_id"], {}).get("status", "?")),
          (specs.get(d["mapping_spec_id"], {}).get("approved_by")
           or specs.get(d["mapping_spec_id"], {}).get("proposed_by") or "?"),
          f"{d['rows_in']}/{d['rows_loaded']}/{d['rows_rejected']}",
          d["control_total"]]
         for d in manifest.get("datasets", [])]))

    sections.append("<h2>Procedures executed</h2>" + _table(
        ["Procedure", "Status", "Run by", "Findings", "Result digest"],
        [[r["procedure_id"], r["status"], r["executed_by"],
          len(r["findings"]), r["result_digest"][:16] + "…"]
         for r in packet.get("runs", [])]))

    if packet.get("procedures_not_run"):
        sections.append("<h2>Procedures not executed</h2>" + _table(
            ["Procedure", "Reason"],
            [[p["procedure_id"], p["reason"]]
             for p in packet["procedures_not_run"]]))

    finding_rows = []
    for run in packet.get("runs", []):
        for finding in run["findings"]:
            uid = (f"{finding['domain']}|"
                   + json.dumps(finding["key"], ensure_ascii=False))
            disposition = packet.get("dispositions", {}).get(uid, {})
            judged = disposition.get("proposed_by", "")
            finding_rows.append([
                run["procedure_id"], finding["verdict"],
                finding.get("reason", ""),
                finding.get("score"),
                disposition.get("status", "undisposed"),
                disposition.get("note", ""),
                judged,
                finding["receipt_id"][:16] + "…"])
    sections.append("<h2>Findings and dispositions</h2>" + (
        _table(["Procedure", "Verdict", "Reason", "Magnitude", "Disposition",
                "Note", "Judged by", "Receipt"], finding_rows)
        if finding_rows else "<p>No findings.</p>"))

    sections.append("<h2>Summary of audit differences</h2>" + _table(
        ["Measure", "Value"],
        [["Overall materiality", sad.get("overall_materiality")],
         ["Clearly trivial", sad.get("clearly_trivial")],
         ["Total unadjusted", sad.get("total_unadjusted")],
         ["Total adjusted", sad.get("total_adjusted")],
         ["Conclusion", sad.get("conclusion")]]))

    sections.append(
        "<h2>Limitations</h2>"
        f"<div class='limits'>{_esc(packet.get('limits', ''))}</div>")
    sections.append(
        "<h2>Checking this record</h2><p class='meta'>Reperform the integrity "
        "checks offline with <code>assurance_workpapers.packet."
        "verify_packet(packet)</code> against the JSON record this document "
        "was rendered from (Export → download the record).</p>")

    return ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>Working paper — {_esc(engagement['client_name'])}</title>"
            f"<style>{_STYLE}</style></head><body>"
            + "".join(sections) + "</body></html>")
