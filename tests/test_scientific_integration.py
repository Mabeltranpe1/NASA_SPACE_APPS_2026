"""Integration invariants: physical definitions, provenance and the actual web payload."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import compare
import export_web
import extract_features
import scientific_catalog as science
from science_metadata import SITES, SCIENCE_COMMIT, GLOBAL_COMMIT, PAI_FEATURES, PAI_WEIGHTS


@pytest.fixture(scope="module")
def public():
    root = ROOT / "web/public"
    data = json.loads((root / "data/comparisons.json").read_text(encoding="utf-8"))
    index = json.loads((root / "data/science/index.json").read_text(encoding="utf-8"))
    docs = {s["id"]: json.loads((root / s["url"].lstrip("/")).read_text(encoding="utf-8")) for s in index["studies"]}
    return root, data, index, docs


def source_bytes(ref, path):
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)


def test_global_source_and_all_colombian_cells_are_preserved():
    path = ROOT / "data/earth_all.csv.gz"
    assert path.read_bytes() == source_bytes(GLOBAL_COMMIT, "data/earth_all.csv.gz")
    earth = pd.read_csv(path)
    assert (len(earth), earth.region.nunique()) == (691035, 727)
    assert not earth.duplicated(["lat", "lon"]).any()
    assert len(earth[earth.region == "northern_andes"]) == 79791
    # Marco removed the old uncompressed 43-region table on purpose (e75ecdb); only the .gz is kept.
    assert not (ROOT / "data/earth_all.csv").exists()


def test_original_scientific_inputs_and_figures_unchanged():
    paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", SCIENCE_COMMIT], cwd=ROOT, text=True).splitlines()
    selected = [p for p in paths if p.startswith(("data/features/", "data/results/", "data/figures/", "data/processed/", "data/raw/climate/")) and not p.endswith(".gitkeep")]
    assert len(selected) >= 80
    for path in selected:
        assert (ROOT / path).read_bytes() == source_bytes(SCIENCE_COMMIT, path), path


def test_scientific_null_and_zero_are_distinct():
    assert science.json_value({"missing": np.nan, "zero": 0.0, "flag": False}) == {"missing": None, "zero": 0.0, "flag": False}


def test_six_colombian_profiles_have_authoritative_science(public):
    _, data, index, docs = public
    # The app links a catalog site to its study through index.json (site_id), not through comparisons.json.
    linked = {st["site_id"]: st["id"] for st in index["studies"] if st.get("site_id")}
    assert set(linked) == {s[0] for s in SITES.values()}
    assert len(index["studies"]) == 18
    sites = {s["id"]: s for s in data["sites"]}
    for site_id, study_id in linked.items():
        site = sites[site_id]
        document = docs[study_id]
        assert document["author"]["github"] == "santiago-851"
        assert document["source_commit"] == SCIENCE_COMMIT
        assert len(document["pai"]["results"]) == 12
        assert len(document["sections"]) == 11
        assert document["geometry"]["resolution_m"] == [200, 200]
        assert "elev_m" in site["values"]  # original global observation stays present
        assert "topography" not in site["values"]  # no regional value replaces a grid feature


def test_all_72_pai_scores_are_original_and_not_fused(public):
    _, _, _, docs = public
    actual = [r for d in docs.values() if d["planet"] == "earth" for r in d["pai"]["results"]]
    expected = pd.read_csv(ROOT / "data/results/analog_ranking.csv")
    assert len(actual) == len(expected) == 72
    lookup = {(r["target"], r["candidate"]): r for r in actual}
    for r in expected.to_dict("records"):
        observed = lookup[(r["target"], r["candidate"])]
        assert observed["PAI"] == r["PAI"]
        assert observed["distance"] == r["distance"]
        assert 1 <= observed["rank_among_six"] <= 6


def test_pai_matrix_recalculates_exactly():
    d = pd.read_csv(ROOT / "data/features/planetary_features.csv")
    terrestrial = d.loc[d.planet == "earth", PAI_FEATURES]
    z = ((d[PAI_FEATURES] - terrestrial.mean()) / terrestrial.std(ddof=0)).to_numpy()
    expected = pd.read_csv(ROOT / "data/results/similarity_matrix.csv", index_col=0).to_numpy()
    matrix = 100 / (1 + np.sqrt(np.sum(np.array(PAI_WEIGHTS) * (z[:, None] - z[None, :]) ** 2, axis=2)))
    np.testing.assert_array_equal(matrix, expected)
    # (src/similarity.py is a script that writes figures on import, so it is not imported here.)


def test_original_dem_statistics_are_reproducible_without_writing_figures():
    rows = pd.read_csv(ROOT / "data/features/planetary_features.csv").set_index(["planet", "region"])
    for path in sorted((ROOT / "data/processed").glob("*/*_DEM_200m.tif")):
        result = extract_features.extract_features(path, path.parent.name, save_figure=False)
        expected = rows.loc[(result["planet"], result["region"])]
        for k, value in result.items():
            if k not in {"planet", "region"}:
                assert np.isclose(value, expected[k], rtol=0, atol=5.01e-6), (path.name, k)


def test_coastal_window_and_provisional_mineralogy_are_visible(public):
    _, _, _, docs = public
    guajira = docs["earth_La_Guajira"]
    flags = {f["code"] for f in guajira["quality_flags"]}
    assert {"coastal_water", "emit_provisional", "separate_support"} <= flags
    environment = next(s for s in guajira["sections"] if s["id"] == "environment")
    assert environment["records"][0]["water_pct"] == pytest.approx(47.92280, abs=1e-5)
    quality = next(s for s in guajira["sections"] if s["id"] == "emit_quality")
    assert all(r["marine_mask_applied"] is False and r["l2a_cloud_mask_applied"] is False for r in quality["records"])
    assert "emit_partial" in {f["code"] for f in docs["earth_Volcan_Purace"]["quality_flags"]}


def test_phoenix_remains_unavailable_and_low_coverage(public):
    _, _, _, docs = public
    d = docs["mars_Phoenix"]
    flags = {f["code"] for f in d["quality_flags"]}
    assert {"crism_geometry", "tes_low_coverage", "themis_pilot"} <= flags
    crism = next(s for s in d["sections"] if s["id"] == "crism")
    assert len(crism["records"]) == 9
    assert all(r["quality_status"] == "no_qualified_observation" and r["parameter_mean"] is None for r in crism["records"])
    tes = next(s for s in d["sections"] if s["id"] == "tes")["records"][0]
    assert tes["ti_day_coverage_flag"] == "low_coverage" and tes["ti_day_valid_area_pct"] < 80


def test_lunar_ice_is_always_labeled_as_model(public):
    _, _, _, docs = public
    moon = [d for d in docs.values() if d["planet"] == "moon"]
    assert len(moon) == 6
    assert all("ice_model" in {f["code"] for f in d["quality_flags"]} for d in moon)
    shackleton = next(s for s in docs["moon_Shackleton_Rim"]["sections"] if s["id"] == "diviner")["records"][0]
    assert shackleton["ice_surface_stable_model_area_pct"] == pytest.approx(1.22878, abs=1e-5)


def test_geometric_association_never_matches_by_name(public):
    _, _, _, docs = public
    jezero = docs["mars_Jezero"]
    # Same name but opposite hemisphere is not a match; another body is not a match.
    assert science.footprint_association({"name": "Jezero", "body": "Mars", "site_lat": -50, "site_lon": -50, "area": "disk 10 km"}, jezero) is None
    assert science.footprint_association({"name": "Jezero", "body": "Moon", "site_lat": 18.4447, "site_lon": 77.4508, "area": "disk 10 km"}, jezero) is None
    match = science.footprint_association({"name": "Jezero", "body": "Mars", "site_lat": 18.44, "site_lon": 77.45, "area": "disk 10 km"}, jezero)
    assert match and match["overlap_study_pct"] > 99
    assert match["relation"] == "overlapping_regional_window_distinct_support"


def test_variable_mapping_preserves_incompatible_definitions(public):
    root, _, _, _ = public
    fields = json.loads((root / "data/science/variables.json").read_text(encoding="utf-8"))["fields"]
    assert fields["earth.topography.tri_mean_m"]["compatibility"].startswith("incompatible_definition")
    assert fields["earth.climate.air_temperature_mean_c"]["compatibility"] == "incompatible_air_vs_surface_temperature"
    assert fields["earth.environment.thermal_range_mean_c"]["compatibility"].startswith("paired_day_night")
    assert fields["earth.environment.water_pct"]["source_ids"] == ["worldcover"]
    assert fields["earth.environment.water_pct"]["period"] == "2021"
    for f in fields.values():
        assert f["conversion"] == "none; original value retained"
        assert f["spatial_support"] and f["period"] and f["source_ids"] and f["method"] and f["quality_reference"]


def test_every_exported_reference_and_asset_exists(public):
    root, data, index, docs = public
    science.validate_comparison_contract(data)
    for site in data["sites"]:
        if site.get("science_ref"):
            assert (root / site["science_ref"]["url"].lstrip("/")).is_file()
    for target in data["targets"]:
        assert (root / f"data/heatmap/{target['id']}.json").is_file()
        for ref in target.get("science_refs", []):
            assert (root / ref["url"].lstrip("/")).is_file()
            assert 0 < ref["overlap_study_pct"] <= 100.000001
    for artifact in index["artifacts"]:
        path = root / artifact["url"].lstrip("/")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
    for d in docs.values():
        for r in d["pai"]["results"]:
            assert (root / r["study_url"].lstrip("/")).is_file()


def test_actual_web_payload_uses_expanded_real_database(public):
    _, data, _, _ = public
    assert data["version"] == "3" and data["synthetic"] is False
    assert (data["n_cells"], data["n_regions"]) == (691035, 727)
    assert data["stability_runs"] == 100
    # Regional science never replaces the global cells: no study field inside the scored values.
    assert all(set(s["values"]) <= set(f["id"] for f in data["features"]) for s in data["sites"])
    assert len(data["targets"]) == 31
    assert {"tatacoa", "la-guajira", "la-candelaria", "nevado-del-ruiz", "nevado-santa-isabel", "volcan-purace"} <= {s["id"] for s in data["sites"]}


@pytest.mark.parametrize("mutate", [
    lambda d: d["sites"].append(copy.deepcopy(d["sites"][0])),
    lambda d: d["sites"][0]["results"][0].update(target="absent"),
    lambda d: d.update(synthetic=True),
    lambda d: d["sites"][0]["results"][0].update(score=float("nan")),
])
def test_invalid_contracts_are_rejected(public, mutate):
    _, data, _, _ = public
    invalid = copy.deepcopy(data)
    mutate(invalid)
    with pytest.raises(ValueError):
        science.validate_comparison_contract(invalid)


def test_compressed_input_support_preserves_synthetic_marker(tmp_path):
    import gzip
    p = tmp_path / "sample.csv.gz"
    with gzip.open(p, "wt", encoding="utf-8") as f:
        f.write("# SYNTHETIC\nlat,lon\n0,0\n")
    assert export_web.is_synthetic(p)


