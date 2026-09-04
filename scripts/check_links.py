"""Find broken internal <a href> links in a directory of HTML files.

Only internal links (starting with `/`, or a bare filename) are checked.
External `http(s)://`, `mailto:`, `tel:`, `javascript:`, and pure `#anchor`
links are ignored.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup


@dataclass
class BrokenLink:
    source: str
    target: str


def _is_internal(href: str) -> bool:
    if not href:
        return False
    if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:")):
        return False
    if href.startswith("#"):
        return False
    return True


def _normalize(root: Path, source: Path, href: str) -> Path:
    parsed = urlparse(href)
    path = parsed.path
    if not path:
        return source
    if path.startswith("/"):
        return (root / path.lstrip("/")).resolve()
    return (source.parent / path).resolve()


def find_broken_links(root: Path) -> list[BrokenLink]:
    broken: list[BrokenLink] = []
    root = root.resolve()
    for html_file in root.rglob("*.html"):
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not _is_internal(href):
                continue
            target = _normalize(root, html_file, href)
            if target.is_file():
                continue
            if target.is_dir() and (target / "index.html").is_file():
                continue
            broken.append(BrokenLink(source=str(html_file.relative_to(root)),
                                     target=href))
    return broken


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("_site")
    if not root.exists():
        print(f"ERROR: {root} does not exist. Run `bundle exec jekyll build` first.")
        return 2
    broken = find_broken_links(root)
    if broken:
        for b in broken:
            print(f"BROKEN {b.source} → {b.target}")
        return 1
    print(f"OK: no broken internal links in {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
