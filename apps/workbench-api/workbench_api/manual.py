# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Serve ``docs/manual`` inside the workbench: an owned markdown renderer.

The manual is first-party content, but every line is HTML-escaped before
inline markup is applied — the renderer never passes raw input through.
It supports exactly the constructs the manual uses (headings to ###, flat
bulleted and numbered lists with wrapped continuation lines, pipe tables,
fenced code, bold/italic/code/links) and treats anything else as a
paragraph. A chapter that needs a new construct gets it added here
deliberately, not guessed at.

Chapter links (``[…](03-….md)``) are rewritten to in-app anchors the UI
intercepts, so the manual cross-references itself without leaving the
workbench. Chapter names are validated against a strict pattern and the
actual directory listing — no dots-and-slashes path business ever reaches
the filesystem.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

_CHAPTER_NAME = re.compile(r"^[0-9A-Za-z][0-9A-Za-z_-]*\.md$")
_HEADING = re.compile(r"^(#{1,3})\s+(.*)$")
_ORDERED = re.compile(r"^\d+\.\s+(.*)$")
_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_TABLE_RULE = re.compile(r"^[\s|:\-]+$")


def default_manual_dir() -> Path:
    """The in-repo manual; absent in installed-package deployments."""
    return Path(__file__).resolve().parents[3] / "docs" / "manual"


def list_chapters(manual_dir: Path) -> list[dict]:
    """Reading order: the README (front matter) first, then the chapters."""
    if not manual_dir.is_dir():
        raise FileNotFoundError(
            f"the manual is not present in this deployment ({manual_dir})")
    names = sorted(p.name for p in manual_dir.glob("*.md")
                   if _CHAPTER_NAME.match(p.name))
    names.sort(key=lambda name: (name != "README.md", name))
    chapters = []
    for name in names:
        text = (manual_dir / name).read_text(encoding="utf-8")
        heading = next((line[2:].strip() for line in text.splitlines()
                        if line.startswith("# ")), name)
        chapters.append({"name": name, "title": heading})
    return chapters


def render_chapter(manual_dir: Path, name: str) -> dict:
    if not _CHAPTER_NAME.match(name or "") or not (manual_dir / name).is_file():
        raise KeyError(f"manual chapter {name!r}")
    text = (manual_dir / name).read_text(encoding="utf-8")
    title = next((line[2:].strip() for line in text.splitlines()
                  if line.startswith("# ")), name)
    return {"name": name, "title": title, "html": render_markdown(text)}


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    stash: list[str] = []

    def code(match: re.Match) -> str:
        stash.append(f"<code>{match.group(1)}</code>")
        return f"\x00{len(stash) - 1}\x00"

    text = _INLINE_CODE.sub(code, text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)

    def link(match: re.Match) -> str:
        label, href = match.group(1), match.group(2)
        if _CHAPTER_NAME.match(href):
            return (f'<a href="#manual/{href}" data-chapter="{href}">'
                    f"{label}</a>")
        if href.startswith(("http://", "https://")):
            return (f'<a href="{href}" target="_blank" '
                    f'rel="noopener noreferrer">{label}</a>')
        return label  # other repo-relative paths: keep the words, drop the link

    text = _LINK.sub(link, text)
    for index, fragment in enumerate(stash):
        text = text.replace(f"\x00{index}\x00", fragment)
    return text


def _is_block_start(line: str) -> bool:
    return (line.startswith(("#", "|", "```", "- "))
            or bool(_ORDERED.match(line)))


def _list_items(lines: list[str], i: int, matcher) -> tuple[list[str], int]:
    """Collect items plus their indented continuation lines."""
    items: list[str] = []
    while i < len(lines):
        match = matcher(lines[i])
        if match:
            items.append(match)
        elif items and lines[i].startswith(" ") and lines[i].strip():
            items[-1] += " " + lines[i].strip()
        else:
            break
        i += 1
    return items, i


def _table(rows: list[str]) -> str:
    def cells(row: str) -> list[str]:
        return [cell.strip() for cell in row.strip().strip("|").split("|")]

    header = "".join(f"<th>{_inline(cell)}</th>" for cell in cells(rows[0]))
    body = []
    for row in rows[1:]:
        if _TABLE_RULE.match(row):
            continue
        body.append("<tr>" + "".join(
            f"<td>{_inline(cell)}</td>" for cell in cells(row)) + "</tr>")
    return (f"<table><thead><tr>{header}</tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table>")


def render_markdown(source: str) -> str:
    lines = source.splitlines()
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            block = []
            i += 1
            while i < n and not lines[i].startswith("```"):
                block.append(html.escape(lines[i], quote=False))
                i += 1
            i += 1  # closing fence
            out.append("<pre><code>" + "\n".join(block) + "</code></pre>")
            continue
        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(_table(rows))
            continue
        if line.startswith("- "):
            items, i = _list_items(
                lines, i, lambda l: l[2:].strip() if l.startswith("- ") else None)
            out.append("<ul>" + "".join(
                f"<li>{_inline(item)}</li>" for item in items) + "</ul>")
            continue
        if _ORDERED.match(line):
            items, i = _list_items(
                lines, i,
                lambda l: m.group(1) if (m := _ORDERED.match(l)) else None)
            out.append("<ol>" + "".join(
                f"<li>{_inline(item)}</li>" for item in items) + "</ol>")
            continue
        paragraph = []
        while i < n and lines[i].strip() and not _is_block_start(lines[i]):
            paragraph.append(lines[i].strip())
            i += 1
        out.append(f"<p>{_inline(' '.join(paragraph))}</p>")
    return "\n".join(out)
