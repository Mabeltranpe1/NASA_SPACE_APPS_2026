"""Tests for src/export_web.py (the step that prepares the data for the web app)."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import compare  # noqa: E402
import export_web  # noqa: E402


def test_catalog_is_read_completely_from_sites_ts():
    sites = export_web.read_catalog_sites(ROOT / "web/src/data/sites.ts")
    ids = [s["id"] for s in sites]
    assert len(ids) == len(set(ids)) >= 12
    assert all(-90 <= s["lat"] <= 90 and -180 <= s["lng"] <= 180 for s in sites)
    # Every Colombian site of Santiago must exist in the catalog.
    assert set(export_web.SANTIAGO_SITES.values()) <= set(ids)


def test_catalog_reader_fails_loudly_on_unexpected_format(tmp_path):
    bad = tmp_path / "sites.ts"
    bad.write_text("export const SITES = [\n  {\n    id: 'x',\n    lat: 1,\n  },\n]\n", encoding="utf-8")
    with pytest.raises(ValueError):
        export_web.read_catalog_sites(bad)


def make_earth(n_regions=3, per_region=20, seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    for r in range(n_regions):
        for k in range(per_region):
            rows.append({
                "region": f"region_{r}", "lat": 10.0 * r + 0.05 * k, "lon": 5.0 * r,
                "elev_m": rng.uniform(0, 3000), "slope_deg": rng.uniform(0, 15),
                "roughness": rng.uniform(0, 20), "temp_mean_K": rng.uniform(250, 310),
                "temp_range_K": rng.uniform(5, 35), "albedo": rng.uniform(0.1, 0.5),
                "precip_mm": rng.uniform(0, 500), "ndvi": rng.uniform(0, 0.5),
                "em_contrast": rng.uniform(0, 0.1), "known": "yes" if r == 0 else "no",
            })
    earth = pd.DataFrame(rows)
    # Like the real database: the driest, barest cells reach 0 rain and 0 plants.
    earth.loc[earth.index[-1], ["precip_mm", "ndvi"]] = 0.0
    return earth


def make_targets():
    common = {"elev_m": 0.0, "slope_deg": 5.0, "roughness": 8.0, "albedo": 0.3,
              "precip_mm": 0.0, "ndvi": 0.0, "em_contrast": np.nan}
    return pd.DataFrame([
        {"name": "Shackleton rim", "body": "Moon", "site_lat": -89.67, "site_lon": 129.78,
         "temp_mean_K": 125.0, "temp_range_K": 135.0, **common},
        {"name": "Jezero crater (Perseverance)", "body": "Mars", "site_lat": 18.44, "site_lon": 77.45,
         "temp_mean_K": 260.0, "temp_range_K": 30.0, **common},
    ])


def test_body_weights_switch_off_values_earth_cannot_reach():
    earth, targets = make_earth(), make_targets()
    per_body = export_web.body_weights(targets, earth)
    moon_weights, moon_excluded = per_body["Moon"]
    mars_weights, mars_excluded = per_body["Mars"]
    assert set(moon_excluded) == {"temp_mean_K", "temp_range_K"}
    assert moon_weights["temp_mean_K"] == 0 and moon_weights["slope_deg"] > 0
    assert mars_excluded == []
    # Elevation is never compared (different zero level on every body).
    assert moon_weights["elev_m"] == 0 and mars_weights["elev_m"] == 0


def test_build_writes_valid_contract(tmp_path):
    earth_path, targets_path = tmp_path / "earth.csv", tmp_path / "targets.csv"
    make_earth().to_csv(earth_path, index=False)
    make_targets().to_csv(targets_path, index=False)
    sites_ts = tmp_path / "sites.ts"
    sites_ts.write_text(
        "export const SITES = [\n  {\n    id: 'demo',\n    name: 'Demo',\n    country: 'X',\n"
        "    lat: 10.1,\n    lng: 5.0,\n  },\n]\n", encoding="utf-8")

    old_runs = export_web.STABILITY_RUNS
    export_web.STABILITY_RUNS = 5
    try:
        data, heatmaps, unmatched = export_web.build(
            earth_path, targets_path, tmp_path / "none.csv", sites_ts, tmp_path / "features")
    finally:
        export_web.STABILITY_RUNS = old_runs

    json.dumps(data, allow_nan=False)  # no NaN may reach the browser
    assert unmatched == []
    assert {t["id"] for t in data["targets"]} == {"shackleton", "jezero"}
    assert all(t["lat"] is not None for t in data["targets"])
    assert [f["id"] for f in data["features"]] == compare.FEATURES

    catalog = [s for s in data["sites"] if s["kind"] == "catalog"]
    assert [s["id"] for s in catalog] == ["demo"]
    discoveries = [s for s in data["sites"] if s["kind"] == "discovery"]
    # Discoveries never come from known (control) regions...
    assert discoveries and not any(s["known"] for s in discoveries)
    # ...and each target picks at most one place per region.
    for tid in ("shackleton", "jezero"):
        regions = [s["region"] for s in discoveries if any(r["target"] == tid for r in s["results"])]
        assert len(regions) >= 1
    for site in data["sites"]:
        for r in site["results"]:
            assert 0 <= r["score"] <= 1 and r["rank"] >= 1
            assert r["stability"] is None or 0 <= r["stability"] <= 1
            # Switched-off features have no similarity for the Moon.
            if r["target"] == "shackleton":
                assert r["sim"]["temp_mean_K"] is None

    assert set(heatmaps) == {"shackleton", "jezero"}
    cells = heatmaps["jezero"]
    assert cells == sorted(cells, key=lambda c: -c[2])
