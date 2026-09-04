"""Rewrite Bootstrap 4 attributes and classes to Bootstrap 5 equivalents.

Usage:
    python3 scripts/bs4_to_bs5.py path/to/file.html            # in place
    echo '<div class="ml-1">' | python3 scripts/bs4_to_bs5.py  # stdin

The rewriter walks attributes only (never text nodes or <pre>/<code> contents),
so literal strings like `data-toggle` in example code are preserved.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

DATA_ATTR_MAP = {
    "data-toggle":   "data-bs-toggle",
    "data-target":   "data-bs-target",
    "data-dismiss":  "data-bs-dismiss",
    "data-parent":   "data-bs-parent",
    "data-slide":    "data-bs-slide",
    "data-slide-to": "data-bs-slide-to",
}

# Class token rewrites (whole token, not substring). Empty string means "drop".
CLASS_TOKEN_MAP = {
    "text-left":       "text-start",
    "text-right":      "text-end",
    "float-left":      "float-start",
    "float-right":     "float-end",
    "no-gutters":      "g-0",
    "sr-only":         "visually-hidden",
    "font-italic":     "fst-italic",
    "text-monospace":  "font-monospace",
    "embed-responsive":"ratio",
    "form-row":        "row g-2",
    "custom-select":   "form-select",
    "close":           "btn-close",
    "form-group":      "mb-3",
    "jumbotron":       "content-card",
    "pagejumbotron":   "",
    "mainjumbotron":   "hero",
    "tablejumbotron":  "",
}

CLASS_REGEX_MAP = [
    (re.compile(r"^ml-(\d+|auto)$"), r"ms-\1"),
    (re.compile(r"^mr-(\d+|auto)$"), r"me-\1"),
    (re.compile(r"^pl-(\d+|auto)$"), r"ps-\1"),
    (re.compile(r"^pr-(\d+|auto)$"), r"pe-\1"),
    (re.compile(r"^font-weight-(\w+)$"), r"fw-\1"),
]

BADGE_RE = re.compile(r"^badge-(primary|secondary|success|danger|warning|info|light|dark)$")

FA_MAP = {
    "fa-bars":          "bi-list",
    "fa-search":        "bi-search",
    "fa-download":      "bi-download",
    "fa-external-link": "bi-box-arrow-up-right",
    "fa-envelope":      "bi-envelope",
    "fa-github":        "bi-github",
}


def _rewrite_class_list(tokens):
    """Return the rewritten token list. Handles jumbotron precedence: `jumbotron
    mainjumbotron` becomes `hero` (not `content-card hero`) so the map is
    applied with a second pass that removes generic `content-card` when a
    more specific hero variant is present."""
    out = []
    saw_fa_prefix = False
    saw_bi_icon = False
    saw_mainjumbotron = False
    saw_tablejumbotron = False
    for tok in tokens:
        if tok in ("fa", "fas", "fab", "far"):
            saw_fa_prefix = True
            continue
        if tok == "mainjumbotron":
            saw_mainjumbotron = True
        if tok == "tablejumbotron":
            saw_tablejumbotron = True
        m = BADGE_RE.match(tok)
        if m:
            out.append(f"bg-{m.group(1)}")
            if m.group(1) not in ("light", "warning"):
                out.append("text-white")
            continue
        if tok in FA_MAP:
            saw_bi_icon = True
            out.append(FA_MAP[tok])
            continue
        if tok in CLASS_TOKEN_MAP:
            repl = CLASS_TOKEN_MAP[tok]
            if repl:
                out.extend(repl.split())
            continue
        replaced = False
        for pat, subs in CLASS_REGEX_MAP:
            if pat.match(tok):
                out.append(pat.sub(subs, tok))
                replaced = True
                break
        if replaced:
            continue
        out.append(tok)

    # Jumbotron precedence: mainjumbotron/tablejumbotron override generic content-card.
    if saw_mainjumbotron and "content-card" in out:
        out = [t for t in out if t != "content-card"]
    if saw_tablejumbotron and "content-card" in out:
        out = [t for t in out if t != "content-card"]

    # Ensure "bi" prefix accompanies any bi-* icon token.
    if saw_fa_prefix and saw_bi_icon and "bi" not in out:
        out.insert(0, "bi")

    return out


def rewrite_html(html: str) -> str:
    """Apply all rewrites to a fragment or full document."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(True):
        if any(anc.name in ("pre", "code") for anc in tag.parents):
            continue
        if tag.name in ("pre", "code"):
            # Still rewrite own class attrs; skip descendants (handled by ancestor check).
            pass
        for old, new in DATA_ATTR_MAP.items():
            if tag.has_attr(old):
                tag[new] = tag[old]
                del tag[old]
        if tag.has_attr("class"):
            tag["class"] = _rewrite_class_list(list(tag["class"]))
            if not tag["class"]:
                del tag["class"]
    return str(soup)


def _rewrite_file(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    rewritten = rewrite_html(original)
    if rewritten != original:
        path.write_text(rewritten, encoding="utf-8")
        print(f"rewrote {path}")
    else:
        print(f"unchanged {path}")


def main(argv: list) -> int:
    if not argv:
        sys.stdout.write(rewrite_html(sys.stdin.read()))
        return 0
    for arg in argv:
        for path in Path().glob(arg) if "*" in arg else [Path(arg)]:
            _rewrite_file(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
