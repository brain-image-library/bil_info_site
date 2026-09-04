"""Fetch BIL /stats?type=all, normalize, write data/stats.json.

Run locally: python3 scripts/build_stats.py
Called by:   .github/workflows/stats.yml (daily)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

API_URL = "https://api.brainimagelibrary.org/stats?type=all"
TIMEOUT = 15
OUTPUT_PATH = Path("data/stats.json")

# Canonical display bucket -> list of lowercase raw endpoint modality names.
# Any raw modality not listed here falls through to "Other" and is logged.
# Source: BICCN technique-stats grouping (technique_biccn_stats.csv, 2026-09-04).
MODALITY_MERGE: dict[str, list[str]] = {
    "Morphology":              ["cell morphology"],
    "Imaging":                 ["population imaging", "cell type distribution",
                                "cell counting", "receptor mapping",
                                "expression characterization"],
    "Anatomy/Morphology":      ["connectivity", "anatomy", "histology imaging",
                                "anatomy/morphology", "morphology"],
    "Spatial transcriptomics": ["spatial transcriptomics"],
    "Other":                   ["other", "functional/sensory"],
}


# Canonical display bucket -> list of lowercase raw endpoint species names.
# Unknown species pass through with title-case applied.
# Source: species_simplified_stats.csv (2026-09-04). Note "Macaque" is a genus-
# level rollup grouping pig-tailed / rhesus / crab-eating macaques.
SPECIES_MERGE: dict[str, list[str]] = {
    "Mouse":           ["mouse", "mus musculus"],
    "Human":           ["human", "homo sapiens"],
    "Macaque":         ["macaque", "pig-tailed macaque", "rhesus macaque",
                        "crab-eating macaque", "macaca nemestrina",
                        "macaca mulatta", "macaca fascicularis"],
    "Marmoset":        ["marmoset", "common marmoset", "callithrix jacchus"],
    "Rat":             ["rat", "rattus norvegicus"],
    "Fruit fly":       ["fruit fly", "drosophila melanogaster"],
    "Ant":             ["ant", "clonal raider ant", "ooceraea biroi"],
    "Zebrafish":       ["zebrafish", "danio rerio"],
    "Sea squirt":      ["sea squirt", "ciona robusta"],
    "Squirrel monkey": ["squirrel monkey", "common squirrel monkey",
                        "saimiri sciureus"],
    "Spider":          ["spider", "feather-legged spider", "uloborus diversus"],
}


def _lookup_canonical(raw_name: str) -> str | None:
    """Return the canonical display name if `raw_name` matches any merge entry."""
    raw_lower = raw_name.strip().lower()
    for canonical, aliases in SPECIES_MERGE.items():
        if raw_lower in aliases:
            return canonical
    return None


def merge_species(raw: list[dict]) -> list[dict]:
    """Fold synonyms per SPECIES_MERGE; unknown names pass through title-cased.

    Returns rows sorted by count descending.
    """
    totals: dict[str, int] = {}
    for row in raw:
        name = row["name"]
        count = int(row["count"])
        canonical = _lookup_canonical(name)
        if canonical is None:
            display = name.strip().title()
            print(
                f"NOTE: species '{name}' not in SPECIES_MERGE; passing through as '{display}'",
                file=sys.stderr,
            )
        else:
            display = canonical
        totals[display] = totals.get(display, 0) + count

    merged = [{"name": name, "count": count} for name, count in totals.items()]
    merged.sort(key=lambda r: r["count"], reverse=True)
    return merged


def _lookup_modality_bucket(raw_name: str) -> str:
    """Return the canonical modality bucket for a raw name; unknowns go to 'Other'."""
    raw_lower = raw_name.strip().lower()
    for canonical, aliases in MODALITY_MERGE.items():
        if raw_lower in aliases:
            return canonical
    return "Other"


def filter_modalities(raw: list[dict]) -> list[dict]:
    """Drop `#N/A` and zero-count entries, then regroup by MODALITY_MERGE."""
    totals: dict[str, int] = {}
    for row in raw:
        name = row["name"].strip()
        count = int(row["count"])
        if name == "#N/A" or count == 0:
            continue
        bucket = _lookup_modality_bucket(name)
        if bucket == "Other" and name.lower() not in MODALITY_MERGE["Other"]:
            # Log so new/unexpected modality names are visible in workflow output.
            print(
                f"NOTE: modality '{name}' not in MODALITY_MERGE; folded into 'Other'",
                file=sys.stderr,
            )
        totals[bucket] = totals.get(bucket, 0) + count
    merged = [{"name": name, "count": count} for name, count in totals.items()]
    merged.sort(key=lambda r: r["count"], reverse=True)
    return merged


def build_output(endpoint: dict, *, generated_at: str) -> dict:
    """Compose the final data/stats.json document."""
    species = merge_species(endpoint["species"])
    modalities = filter_modalities(endpoint["modalities"])
    consortia = endpoint["consortiums"]  # endpoint uses "consortiums" spelling
    return {
        "generated_at": generated_at,
        "source": API_URL,
        "headline": {
            "datasets":   int(endpoint["dataset_count"]),
            "consortia":  len(consortia),
            "species":    len(species),
            "modalities": len(modalities),
        },
        "species":    species,
        "modalities": modalities,
        "consortia":  consortia,
    }


def _validate_endpoint_shape(payload: dict) -> None:
    """Exit non-zero if the endpoint payload is missing required keys."""
    required = {"dataset_count", "species", "modalities", "consortiums"}
    missing = required - set(payload)
    if missing:
        print(f"ERROR: endpoint payload missing keys: {sorted(missing)}", file=sys.stderr)
        raise SystemExit(2)


def main() -> int:
    try:
        r = requests.get(API_URL, timeout=TIMEOUT)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: fetch failed: {e}", file=sys.stderr)
        return 1

    try:
        payload = r.json()
    except ValueError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 1

    _validate_endpoint_shape(payload)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = build_output(payload, generated_at=generated_at)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, OUTPUT_PATH)
    print(f"OK: wrote {OUTPUT_PATH} (datasets={out['headline']['datasets']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
