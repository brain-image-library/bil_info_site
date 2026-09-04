from pathlib import Path
import tempfile
from scripts.check_links import find_broken_links


def _write(root: Path, rel: str, body: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def test_reports_missing_internal_link():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root, "a.html", '<a href="/missing.html">go</a>')
        broken = find_broken_links(root)
        assert any("missing.html" in b.target for b in broken)


def test_ignores_external_links():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root, "a.html", '<a href="https://example.com/x">x</a>')
        assert find_broken_links(root) == []


def test_finds_existing_internal_link():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root, "a.html", '<a href="/b.html">b</a>')
        _write(root, "b.html", 'ok')
        assert find_broken_links(root) == []


def test_handles_anchor_only_links():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root, "a.html", '<a href="#section">jump</a>')
        assert find_broken_links(root) == []


def test_ignores_mailto_and_tel():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write(root, "a.html", '<a href="mailto:x@y">x</a><a href="tel:5551234">tel</a>')
        assert find_broken_links(root) == []
