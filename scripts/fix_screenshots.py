"""Constrain unconstrained screenshot <img> tags across all pages.

Applies BS5 responsive image styling to screenshot-style images that come
from HackMD/Word/imgur exports and would otherwise render at native size
and overflow the content card. Skips:

- Images explicitly marked as inline emoji (class="emoji")
- Images with an author-set width/height attribute (they were sized on purpose)

Usage:
    python3 scripts/fix_screenshots.py                # all *.html at repo root
    python3 scripts/fix_screenshots.py path/to/page.html [more.html ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

from bs4 import BeautifulSoup

# HackMD adds these "handled" classes as UI hooks; they carry no meaning here.
HACKMD_NOISE = {"offline-handled", "error-handled", "image-toolbar-handled"}


def constrain(soup: BeautifulSoup) -> int:
    fixed = 0
    # Skip images that live inside layout components that already style them.
    SKIP_ANCESTORS = {"feature-card", "hero", "logo", "site-footer", "stat-grid"}
    for img in soup.find_all("img"):
        classes = img.get("class", []) or []
        if "emoji" in classes:
            continue
        if img.get("width") or img.get("height"):
            continue
        # Skip images inside container components that style them themselves.
        skip = False
        for anc in img.parents:
            anc_classes = set(anc.get("class", []) if hasattr(anc, "get") else [])
            if anc_classes & SKIP_ANCESTORS:
                skip = True
                break
        if skip:
            continue
        # Strip HackMD "handled" noise and any prior sizing style.
        classes = [c for c in classes if c not in HACKMD_NOISE and c != "responsive"]
        # Skip if already fluid-styled.
        if "img-fluid" not in classes:
            classes += ["img-fluid", "rounded-3", "shadow-sm", "my-3", "d-block", "mx-auto"]
            fixed += 1
        img["class"] = classes
        img["style"] = "max-width:800px;"
        img["loading"] = img.get("loading") or "lazy"
    return fixed


def main(argv: list[str]) -> int:
    if argv:
        paths = [Path(a) for a in argv]
    else:
        paths = [p for p in Path(".").glob("*.html") if p.name != "datasets.html"]
        paths += list(Path("software").glob("*.html"))
    total = 0
    for p in paths:
        if not p.exists():
            print(f"SKIP: {p} (not found)")
            continue
        soup = BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser")
        n = constrain(soup)
        if n:
            p.write_text(str(soup), encoding="utf-8")
            print(f"fixed {n:3d} img(s) in {p}")
            total += n
    print(f"\nTotal: {total} images constrained.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
