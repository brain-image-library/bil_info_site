from scripts.validate_stats_schema import validate


VALID = {
    "generated_at": "2026-08-21T06:00:00Z",
    "source": "https://api.brainimagelibrary.org/stats?type=all",
    "headline": {"datasets": 14225, "consortia": 4, "species": 1, "modalities": 1},
    "species": [{"name": "Mouse", "count": 100}],
    "modalities": [{"name": "Cell morphology", "count": 100}],
    "consortia": [{"label": "BICCN", "value": "BICCN", "count": 100}],
}


def test_accepts_valid_document():
    assert validate(VALID) == []


def test_rejects_missing_headline():
    bad = dict(VALID); del bad["headline"]
    errs = validate(bad)
    assert any("headline" in e for e in errs)


def test_rejects_wrong_type_in_species():
    bad = dict(VALID); bad["species"] = [{"name": "Mouse", "count": "one hundred"}]
    errs = validate(bad)
    assert any("count" in e for e in errs)


def test_rejects_mismatched_headline_species_length():
    bad = dict(VALID)
    bad["species"] = []
    bad["headline"] = dict(VALID["headline"], species=5)
    errs = validate(bad)
    assert any("species" in e for e in errs)
