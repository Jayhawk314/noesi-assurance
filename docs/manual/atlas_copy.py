"""Write the Workbench copy of the Code Atlas: apps/learn-kestrel-ui/public/code-atlas.html.

The Workbench serves its pages under a strict Content-Security-Policy (scripts and styles from
its own files only, nothing inline, nothing from other sites). So the copy moves the page's inline
<style> and <script> blocks into code-atlas.css and code-atlas.js, uses the saved
vendor/highlight.min.js (highlight.js 11.9.0, BSD-3-Clause) instead of the CDN, and drops the web
fonts (the page falls back to system fonts). The Atlas itself (docs/manual) is unchanged.
"""
import re
from pathlib import Path


def write_learn_copy(page: Path, root: Path) -> None:
    html = page.read_text(encoding="utf-8")
    dest = root / "apps" / "learn-kestrel-ui" / "public"
    styles = re.findall(r"<style>(.*?)</style>", html, flags=re.S)
    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
    html = re.sub(r"<style>.*?</style>", "", html, flags=re.S)
    html = re.sub(r"<script>.*?</script>", "", html, flags=re.S)
    html = re.sub(r'<link rel="(preconnect|stylesheet)" href="https://fonts\.[^"]+"[^>]*>\n?', "", html)
    cdn = '<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>'
    assert html.count(cdn) == 1, "the Atlas no longer loads highlight.js from cdnjs; update atlas_copy.py"
    assert (dest / "vendor" / "highlight.min.js").is_file(), "vendor/highlight.min.js is missing"
    html = html.replace(cdn, '<link rel="stylesheet" href="code-atlas.css">\n'
                             '<script src="vendor/highlight.min.js"></script>')
    html = html.replace("</body>", '<script src="code-atlas.js"></script>\n</body>') if "</body>" in html \
        else html + '\n<script src="code-atlas.js"></script>\n'
    (dest / "code-atlas.css").write_text("\n".join(styles), encoding="utf-8")
    (dest / "code-atlas.js").write_text("\n".join(scripts), encoding="utf-8")
    (dest / "code-atlas.html").write_text(html, encoding="utf-8")
    print("wrote the Workbench copy: public/code-atlas.html, .css, .js")
