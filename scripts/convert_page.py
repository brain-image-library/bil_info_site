"""One-shot conversion helper for BS4→BS5 + Jekyll layout migration.

Reads a legacy page:
    <html><head>...</head><body class="bg">
      <div id="topmenu"></div><script>$(...)</script>
      <BODY CONTENT>
      <div id="bottomfooter"></div><script>$(...)</script>
      <script src="/js/..."></script>
    </body></html>

Extracts BODY CONTENT, applies bs4_to_bs5 rewrites, wraps in a container
+ content-card, and prepends Jekyll front matter.

This helper is used once during the modernization pass; not intended for
long-term use.

Usage:
    python3 scripts/convert_page.py <file.html> <Title> <Description>
"""
from __future__ import annotations

import sys
from pathlib import Path

from bs4 import BeautifulSoup

from scripts.bs4_to_bs5 import rewrite_html


def extract_body(html: str) -> str:
    """Return the inner content of the page's <div class="jumbotron..."> element,
    stripped of nav/footer chrome. If no jumbotron is present, fall back to
    <body> contents minus chrome scripts."""
    soup = BeautifulSoup(html, "html.parser")

    # Preferred path: content lives inside <div class="jumbotron ...">.
    jumbo = soup.find("div", class_="jumbotron")
    if jumbo is not None:
        return "".join(str(c) for c in jumbo.children).strip()

    body = soup.body
    if body is None:
        return html

    # Fallback: strip chrome nodes and known scripts, return remaining body.
    for div_id in ("topmenu", "bottomfooter"):
        node = body.find("div", id=div_id)
        if node:
            node.decompose()
    for script in list(body.find_all("script")):
        text = script.string or ""
        src = script.get("src", "") or ""
        if 'menu.html' in text or 'footer.html' in text:
            script.decompose()
        elif any(dead in src for dead in ("jquery", "popper", "/js/bootstrap.min.js")):
            script.decompose()
    # Drop leading empty spacer paragraphs.
    for div in list(body.find_all("div", class_="container", recursive=False)):
        inner = div.get_text(strip=True)
        if not inner and not div.find(["img", "iframe", "form", "input", "button"]):
            div.decompose()
    return "".join(str(c) for c in body.children).strip()


def wrap(body_html: str, *, title: str, description: str) -> str:
    """Wrap the rewritten body in a Jekyll page with front matter."""
    return (
        "---\n"
        f"layout: default\n"
        f"title: {title}\n"
        f"description: {description}\n"
        "---\n\n"
        '<div class="container my-5">\n'
        '  <div class="content-card">\n'
        f"{body_html}\n"
        "  </div>\n"
        "</div>\n"
    )


def convert(path: Path, title: str, description: str) -> None:
    src = path.read_text(encoding="utf-8")
    body = extract_body(src)
    body = rewrite_html(body)
    out = wrap(body, title=title, description=description)
    path.write_text(out, encoding="utf-8")
    print(f"converted {path}")


def main(argv: list) -> int:
    if len(argv) < 3:
        print("usage: convert_page.py <file.html> <title> <description>", file=sys.stderr)
        return 2
    convert(Path(argv[0]), argv[1], argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
