"""
Small automatic checks for src/compare.py.

Run them with:
    python tests/test_compare.py
(They also work with pytest, if you install it later.)

All numbers here are invented; they only test that the maths behaves.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import compare  # noqa: E402


def make_tables():
    """Three fake Earth cells and one fake target that is a copy of cell 0."""
    earth = pd.DataFrame({
        "lat": [0.0, 10.0, 20.0],
        "lon": [0.0, 10.0, 20.0],
        "elev_m": [1000.0, 2000.0, 50.0],
        "slope_deg": [5.0, 10.0, 1.0],
        "roughness": [0.3, 0.5, 0.1],
        "temp_mean_K": [220.0, 260.0, 300.0],
        "temp_range_K": [80.0, 40.0, 10.0],
        "albedo": [0.2, 0.3, 0.1],
        "precip_mm": [5.0, 200.0, 2000.0],
    })
    target = earth.iloc[[0]].drop(columns=["lat", "lon"]).copy()
    target.insert(0, "name", "Twin of cell 0")
    target.insert(1, "body", "Mars")
    return earth, target.reset_index(drop=True)


def test_identical_cell_scores_one():
    earth, targets = make_tables()
    best = compare.compare_all(earth, targets).iloc[0]
    assert best["rank"] == 1 and best["lat"] == 0.0
    assert np.isclose(best["score"], 1.0)


def test_scores_are_between_0_and_1_and_sorted():
    earth, targets = make_tables()
    scores = compare.compare_all(earth, targets)["score"].to_numpy()
    assert ((scores >= 0) & (scores <= 1)).all()
    assert (np.diff(scores) <= 0).all()


def test_weight_zero_switches_a_feature_off():
    earth, targets = make_tables()
    earth.loc[0, "elev_m"] = 9000.0  # cell 0 now differs from the target only here
    with_elev = compare.compare_all(earth, targets)
    without_elev = compare.compare_all(earth, targets, weights={"elev_m": 0})
    cell0 = lambda table: table[table["lat"] == 0.0].iloc[0]
    assert cell0(with_elev)["score"] < 1.0
    assert np.isclose(cell0(without_elev)["score"], 1.0)
    assert without_elev["sim_elev_m"].isna().all()


def test_empty_target_feature_is_skipped():
    earth, targets = make_tables()
    targets.loc[0, "precip_mm"] = np.nan  # e.g. no rain on the Moon
    result = compare.compare_all(earth, targets)
    assert result["sim_precip_mm"].isna().all()
    assert np.isclose(result.iloc[0]["score"], 1.0)


def test_missing_earth_value_cannot_win():
    earth, targets = make_tables()
    earth.loc[1, "albedo"] = np.nan
    strict = compare.compare_all(earth, targets)
    assert strict[strict["lat"] == 10.0]["score"].isna().all()   # excluded by default
    assert strict.iloc[-1]["lat"] == 10.0                        # and ranked last
    relaxed = compare.compare_all(earth, targets, min_coverage=0.8)
    assert relaxed["score"].notna().all()


def test_both_scalings_find_the_twin():
    earth, targets = make_tables()
    for scaling in ("tolerance", "robust"):
        best = compare.compare_all(earth, targets, scaling=scaling).iloc[0]
        assert best["lat"] == 0.0 and np.isclose(best["score"], 1.0)


def test_tolerance_scale_is_physical():
    earth, targets = make_tables()
    targets.loc[0, "temp_mean_K"] = 220.0 + compare.TOLERANCE["temp_mean_K"]
    cell0 = compare.compare_all(earth, targets).query("lat == 0.0").iloc[0]
    assert np.isclose(cell0["sim_temp_mean_K"], np.exp(-1))


def test_worst_match_names_the_broken_feature():
    earth, targets = make_tables()
    earth.loc[0, "temp_mean_K"] = 300.0
    result = compare.compare_all(earth, targets)
    assert result[result["lat"] == 0.0].iloc[0]["worst_match"] == "temp_mean_K"


def test_row_order_of_targets_does_not_matter():
    earth, targets = make_tables()
    other = targets.copy()
    other["name"] = "Hot wet place"
    other[["temp_mean_K", "precip_mm"]] = [300.0, 2000.0]
    two = pd.concat([other, targets])  # index is 0, 0 on purpose
    result = compare.compare_all(earth, two)
    twin = result[result["target"] == "Twin of cell 0"].iloc[0]
    assert twin["lat"] == 0.0 and np.isclose(twin["score"], 1.0)


def test_top_keeps_only_the_best_rows():
    earth, targets = make_tables()
    assert len(compare.compare_all(earth, targets, top=2)) == 2


def test_bad_weights_are_rejected():
    for bad in ({"elev_m": -1}, {"not_a_feature": 1}):
        try:
            compare.build_weights(bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad} should have been rejected")


def test_sensitivity_is_repeatable_and_twin_is_always_top():
    earth, targets = make_tables()
    first = compare.weight_sensitivity(earth, targets, top=1, runs=50)
    second = compare.weight_sensitivity(earth, targets, top=1, runs=50)
    assert first.equals(second)
    assert first.iloc[0]["lat"] == 0.0 and first.iloc[0]["top_share"] == 1.0


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\nAll {len(tests)} tests passed.")
