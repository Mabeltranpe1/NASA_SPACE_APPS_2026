"""
make_results.py - Make all the result tables again, in one go.

Run it after the database changes (new regions, new variables, new terrain).
Famous analog regions (known = yes in the catalog) are left out, because the
challenge asks for little-known places.

It writes, in outputs/results/:
    results_pairs_top20.csv         20 best Earth places for each Moon/Mars site,
                                    with the values of both places side by side
    results_per_target_top_regions.csv  best place of the 5 best REGIONS for each
                                    Moon/Mars site (used by maps and the web app)
    results_mars_overall.csv        top 1000 places for all Mars sites together
    results_moon_overall.csv        top 1000 places for all Moon sites together
    results_mars_new_per_region.csv best place of each region (Mars)
    results_moon_new_per_region.csv best place of each region (Moon)
    seasons_mars.csv, seasons_moon.csv   best months for those places

Example:
    python src/make_results.py
"""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import compare  # noqa: E402

WEIGHTS = {"elev_m": 0, "em_contrast": 0.5}   # elevation not comparable between bodies; rock type = calibrated estimate (docs/COMPOSICION.md)
LEAVE_OUT_OF_OVERALL = {"Moon": ["Shackleton floor (shadow)"]}   # a contrast site, not a base site


MIN_SEPARATION_KM = 800   # minimum distance between the 5 regions shown for one site


def spread_out(table, n, min_km):
    """First n rows (already best first) whose places are at least min_km from every row kept before."""
    keep, lat, lon = [], np.radians(table["lat"].to_numpy()), np.radians(table["lon"].to_numpy())
    for i in range(len(table)):
        far = all(6371 * np.arccos(np.clip(np.sin(lat[i]) * np.sin(lat[j]) + np.cos(lat[i]) * np.cos(lat[j])
                                           * np.cos(lon[i] - lon[j]), -1, 1)) >= min_km for j in keep)
        if far:
            keep.append(i)
            if len(keep) == n:
                break
    return table.iloc[keep].assign(region_rank=range(1, len(keep) + 1))


def main():
    Path("outputs/results").mkdir(parents=True, exist_ok=True)
    earth, targets = compare.load_inputs("data/earth_all.csv.gz", "data/targets.csv")
    earth = earth[earth["known"] != "yes"].reset_index(drop=True)
    print(f"Comparing {len(earth):,} little-known Earth places with {len(targets)} Moon/Mars sites ...")
    # One target at a time: the full table (every site x every Earth place) no longer
    # fits in memory with 20+ Moon sites. The tolerance scale does not depend on the
    # other targets, so the scores are exactly the same as comparing all at once.
    keys = [c for c in ("region", "place_hint", "lat", "lon") if c in earth.columns]
    sims = [f"sim_{f}" for f in compare.FEATURES]
    pairs, best, slim = [], [], []
    for i in range(len(targets)):
        res = compare.compare_all(earth, targets.iloc[[i]], weights=WEIGHTS)
        pairs.append(res[res["rank"] <= 20])
        best.append(res.drop_duplicates(["target", "region"]))   # already best first
        part = res[["target", "body"] + keys + ["score"] + sims].copy()
        slim.append(part)
        del res
    slim = pd.concat(slim, ignore_index=True)
    for col in ("target", "body", "region", "place_hint"):
        if col in slim.columns:
            slim[col] = slim[col].astype("category")

    pairs = pd.concat(pairs, ignore_index=True).drop(
        columns=["water_frac", "known", "sim_elev_m",
                 "target_elev_m"], errors="ignore")
    pairs.round(4).to_csv("outputs/results/results_pairs_top20.csv", index=False)

    # Best place of each Earth REGION for every Moon/Mars site (top 5 regions).
    # The top 20 cells are often all in one region; this table gives variety
    # and is what the maps and the web app use.
    # With the worldwide grid many regions are neighbours (2 x 2 degree areas), so we
    # also ask the 5 regions to be at least MIN_SEPARATION_KM apart: 5 DIFFERENT parts
    # of the world instead of 5 squares of the same desert.
    best = pd.concat(best, ignore_index=True).sort_values(["target", "rank"])
    by_region = pd.concat([spread_out(g, 5, MIN_SEPARATION_KM) for _, g in best.groupby("target", sort=False)])
    by_region = by_region.drop(
        columns=["water_frac", "known", "sim_elev_m", "target_elev_m"], errors="ignore")
    by_region.round(4).to_csv("outputs/results/results_per_target_top_regions.csv", index=False)

    for body in ("Mars", "Moon"):
        part = slim[slim["body"] == body].copy()
        for col in ("target", "region", "place_hint"):
            if col in part.columns:
                part[col] = part[col].astype(str)
        overall = compare.overall_ranking(part,
                                          exclude=LEAVE_OUT_OF_OVERALL.get(body, []))
        overall.drop(columns="n_met").head(1000).round(4).to_csv(
            f"outputs/results/results_{body.lower()}_overall.csv", index=False)
        per_region = (overall.sort_values(["n_met", "mean_score"], ascending=False)
                      .groupby("region", sort=False).first().reset_index().drop(columns="n_met"))
        per_region.round(4).to_csv(f"outputs/results/results_{body.lower()}_new_per_region.csv", index=False)
        print(f"\n{body}: best little-known place of each region")
        print(per_region[["region", "lat", "lon", "mean_score", "conditions_met", "weakest"]]
              .head(10).round(3).to_string(index=False))

        subprocess.run([sys.executable, str(Path(__file__).parent / "seasons.py"),
                        "--overall", f"outputs/results/results_{body.lower()}_new_per_region.csv",
                        "--targets", f"data/targets_{body.lower()}.csv",
                        "--out", f"outputs/results/seasons_{body.lower()}.csv"],
                       stdout=subprocess.DEVNULL, check=True)
    print("\nAll result tables saved in outputs/results/")


if __name__ == "__main__":
    main()
