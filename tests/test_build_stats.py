from scripts.build_stats import merge_species, filter_modalities, build_output


def test_merge_species_combines_synonyms():
    raw = [
        {"name": "human", "count": 100},
        {"name": "homo sapiens", "count": 50},
        {"name": "mouse", "count": 10000},
        {"name": "rat", "count": 200},
    ]
    merged = merge_species(raw)
    by_name = {row["name"]: row["count"] for row in merged}
    assert by_name["Human"] == 150
    assert by_name["Mouse"] == 10000
    assert by_name["Rat"] == 200
    assert "human" not in by_name and "homo sapiens" not in by_name


def test_merge_species_rolls_macaques_to_genus():
    """CSV groups all macaques (pig-tailed, rhesus, crab-eating) under 'Macaque'."""
    raw = [
        {"name": "pig-tailed macaque", "count": 43},
        {"name": "rhesus macaque",     "count": 74},
        {"name": "crab-eating macaque","count": 12},
        {"name": "macaca mulatta",     "count": 175},
        {"name": "macaca nemestrina",  "count": 291},
        {"name": "macaque",            "count": 22},
    ]
    merged = merge_species(raw)
    by_name = {row["name"]: row["count"] for row in merged}
    assert by_name["Macaque"] == 43 + 74 + 12 + 175 + 291 + 22


def test_merge_species_passthrough_unknown():
    raw = [{"name": "wombat", "count": 5}]
    merged = merge_species(raw)
    assert merged == [{"name": "Wombat", "count": 5}]


def test_merge_species_sorts_descending():
    raw = [
        {"name": "rat", "count": 10},
        {"name": "mouse", "count": 100},
        {"name": "human", "count": 50},
    ]
    merged = merge_species(raw)
    counts = [row["count"] for row in merged]
    assert counts == sorted(counts, reverse=True)


def test_filter_modalities_drops_na_and_zero():
    raw = [
        {"name": "cell morphology", "count": 5282},
        {"name": "#N/A", "count": 5},
        {"name": "morphology", "count": 0},
    ]
    filtered = filter_modalities(raw)
    names = [row["name"] for row in filtered]
    assert "#N/A" not in names
    # cell morphology is bucketed into "Morphology"
    assert "Morphology" in names


def test_filter_modalities_groups_imaging_bucket():
    raw = [
        {"name": "population imaging", "count": 4779},
        {"name": "cell type distribution", "count": 172},
        {"name": "cell counting", "count": 114},
        {"name": "receptor mapping", "count": 111},
        {"name": "expression characterization", "count": 53},
    ]
    filtered = filter_modalities(raw)
    by_name = {r["name"]: r["count"] for r in filtered}
    assert by_name["Imaging"] == 4779 + 172 + 114 + 111 + 53


def test_filter_modalities_folds_unknown_to_other():
    raw = [{"name": "brand new technique", "count": 42}]
    filtered = filter_modalities(raw)
    assert filtered == [{"name": "Other", "count": 42}]


def test_build_output_shape():
    endpoint = {
        "dataset_count": 14225,
        "species": [{"name": "mouse", "count": 10000}, {"name": "human", "count": 100}],
        "modalities": [{"name": "cell morphology", "count": 5000}],
        "consortiums": [{"label": "BICCN", "value": "BICCN", "count": 10000}],
    }
    out = build_output(endpoint, generated_at="2026-08-21T06:00:00Z")
    assert out["generated_at"] == "2026-08-21T06:00:00Z"
    assert out["source"] == "https://api.brainimagelibrary.org/stats?type=all"
    assert out["headline"]["datasets"] == 14225
    assert out["headline"]["consortia"] == 1
    assert out["headline"]["species"] == len(out["species"])
    assert out["headline"]["modalities"] == len(out["modalities"])
    assert out["species"][0]["name"] == "Mouse"
