# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The in-app manual: owned renderer, strict chapter naming, real content."""

import pytest

from workbench_api.manual import (
    default_manual_dir, list_chapters, render_chapter, render_markdown,
)


def test_renderer_covers_the_manual_constructs():
    html = render_markdown(
        "# Title\n\n"
        "## Section\n\n"
        "A paragraph with **bold**, *italic*, and `code`.\n\n"
        "- first item\n"
        "- second item\n"
        "  wraps onto a continuation line\n\n"
        "1. **Upload** the file\n"
        "2. Approve it\n\n"
        "| Col A | Col B |\n"
        "|---|---|\n"
        "| a1 | b1 |\n\n"
        "```\ncode block\n```\n")
    assert "<h1>Title</h1>" in html
    assert "<h2>Section</h2>" in html
    assert "<strong>bold</strong>" in html and "<em>italic</em>" in html
    assert "<code>code</code>" in html
    assert "<li>second item wraps onto a continuation line</li>" in html
    assert "<ol><li><strong>Upload</strong> the file</li>" in html
    assert "<th>Col A</th>" in html and "<td>b1</td>" in html
    assert "<pre><code>code block</code></pre>" in html


def test_renderer_escapes_html_and_rewrites_chapter_links():
    html = render_markdown(
        "Angle <brackets> & ampersands stay text.\n\n"
        "See [chapter three](03-evidence-and-ingestion.md) and "
        "[the tracker](../PRODUCTION-READINESS.md) and "
        "[a site](https://example.com).\n")
    assert "<brackets>" not in html and "&lt;brackets&gt;" in html
    assert 'data-chapter="03-evidence-and-ingestion.md"' in html
    # Repo-relative links outside the manual keep their words, not a link.
    assert "../PRODUCTION-READINESS.md" not in html and "the tracker" in html
    assert 'rel="noopener noreferrer"' in html


def test_real_manual_lists_and_renders():
    chapters = list_chapters(default_manual_dir())
    names = [c["name"] for c in chapters]
    assert names[0] == "README.md"          # front matter reads first
    assert "06-findings-dispositions-sad.md" in names
    rendered = render_chapter(default_manual_dir(),
                              "06-findings-dispositions-sad.md")
    assert rendered["title"].startswith("Chapter 6")
    assert "<h2>" in rendered["html"]


def test_chapter_names_cannot_traverse():
    for hostile in ("../LICENSE.md", "..%2F..%2Fsecret.md", "a/b.md",
                    ".hidden.md", ""):
        with pytest.raises(KeyError):
            render_chapter(default_manual_dir(), hostile)
