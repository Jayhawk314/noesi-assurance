# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Render one self-contained HTML workpaper from an evidence packet.

A document, not an application: inline styles, no scripts, nothing loaded
from anywhere. Every table row traces to sealed content in the packet.
"""

from __future__ import annotations

import html
import json


def _esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def _row(cells: list, tag: str = "td") -> str:
    inner = "".join(f"<{tag}>{_esc(cell)}</{tag}>" for cell in cells)
    return f"<tr>{inner}</tr>"


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
    lock = packet["lock"]
    seal = packet.get("seal", {})
    sad = packet.get("summary_of_audit_differences", {})

    sections = [f"""
<h1>Assurance workpaper — {_esc(engagement['client_name'])}
 (FYE {_esc(engagement['period_end'])})</h1>
<p class="meta">
Packet {_esc(packet['packet_version'])} · generated {_esc(packet['generated'])}
 · software {_esc(packet['software'])}<br>
Lock signed by <b>{_esc(lock['signature']['signer_principal'])}</b>
 (key <code>{_esc(lock['signature']['key_id'][:16])}…</code>,
 {_esc(lock['signature']['algorithm'])}) at
 {_esc(lock['signature']['signed_at'])}<br>
Lock manifest digest <code>{_esc(lock['digest'])}</code><br>
Packet digest <code>{_esc(seal.get('packet_digest', 'unsealed'))}</code>
</p>"""]

    if packet.get("lock_history"):
        sections.append(
            "<h2>Lock amendment history</h2>"
            "<p class='meta'>Earlier locks were superseded, never deleted. "
            "Each entry keeps its full signed manifest in the packet and the "
            "documented reason for reopening (AU-C 230: changes after file "
            "assembly record the reason, by whom, and when).</p>"
            + _table(
                ["Seq", "Locked (signed by)", "Unlocked (by)", "Reason",
                 "Manifest digest"],
                [[item["sequence"],
                  f"{item.get('locked_at', '')} "
                  f"({(item.get('signature') or {}).get('signer_principal', '—')})",
                  f"{item.get('unlocked_at', '')} ({item.get('unlocked_by', '—')})",
                  item.get("reason", ""),
                  item["digest"][:16] + "…"]
                 for item in packet["lock_history"]]))

    sections.append("<h2>Source inventory</h2>" + _table(
        ["File", "SHA-256", "Bytes", "State"],
        [[a["original_name"], a["sha256"][:16] + "…", a["size_bytes"],
          a["state"]] for a in lock["manifest"].get("artifacts", [])]))

    sections.append("<h2>Approved mappings and datasets</h2>" + _table(
        ["Role", "Mapping status", "Proposed by", "Approved by",
         "Rows in/loaded/rejected", "Control total"],
        [[d["role"],
          next((m["status"] for m in lock["manifest"]["mapping_specs"]
                if m["spec_id"] == d["mapping_spec_id"]), "?"),
          next((m["proposed_by"] for m in lock["manifest"]["mapping_specs"]
                if m["spec_id"] == d["mapping_spec_id"]), "?"),
          next((m["approved_by"] for m in lock["manifest"]["mapping_specs"]
                if m["spec_id"] == d["mapping_spec_id"]), "?"),
          f"{d['rows_in']}/{d['rows_loaded']}/{d['rows_rejected']}",
          d["control_total"]]
         for d in lock["manifest"].get("datasets", [])]))

    sections.append("<h2>Procedures executed</h2>" + _table(
        ["Procedure", "Status", "Executed by", "Reviewed by", "Approved by",
         "Findings", "Result digest"],
        [[r["procedure_id"], r["status"], r["executed_by"],
          r["reviewed_by"] or "—", r["approved_by"] or "—",
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
            if disposition.get("concurred_by"):
                judged += f" / concurred: {disposition['concurred_by']}"
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
        f"<div class='limits'>{_esc(packet.get('limits', ''))}<br><br>"
        f"{_esc(lock['manifest'].get('limits', ''))}</div>")

    sections.append(
        "<h2>Verification</h2><p class='meta'>Reperform every integrity "
        "check offline with <code>assurance_workpapers.packet."
        "verify_packet(packet)</code> against the JSON packet this document "
        "was rendered from. Public keys and signatures are carried in the "
        "packet itself.</p>")

    return ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>Workpaper — {_esc(engagement['client_name'])}</title>"
            f"<style>{_STYLE}</style></head><body>"
            + "".join(sections) + "</body></html>")
