"""Validate data/stats.json against the design schema."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def validate(doc: dict) -> list[str]:
    errs: list[str] = []
    for k in ("generated_at", "source", "headline", "species", "modalities", "consortia"):
        if k not in doc:
            errs.append(f"missing top-level key: {k}")
    if "headline" in doc:
        for k in ("datasets", "consortia", "species", "modalities"):
            if k not in doc["headline"]:
                errs.append(f"missing headline.{k}")
            elif not isinstance(doc["headline"][k], int):
                errs.append(f"headline.{k} must be int")
    for coll in ("species", "modalities"):
        rows = doc.get(coll, [])
        for i, row in enumerate(rows):
            if not isinstance(row.get("name"), str):
                errs.append(f"{coll}[{i}].name must be str")
            if not isinstance(row.get("count"), int):
                errs.append(f"{coll}[{i}].count must be int")
        headline_count = doc.get("headline", {}).get(coll)
        if isinstance(headline_count, int) and headline_count != len(rows):
            errs.append(f"headline.{coll}={headline_count} does not match len({coll})={len(rows)}")
    return errs


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/stats.json")
    doc = json.loads(path.read_text(encoding="utf-8"))
    errs = validate(doc)
    if errs:
        for e in errs:
            print(f"SCHEMA ERROR: {e}")
        return 1
    print(f"OK: {path} conforms to schema")
    return 0


if __name__ == "__main__":
    sys.exit(main())
