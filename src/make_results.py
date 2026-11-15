"""
make_results.py - Make all the result tables again, in one go.

Run it after the database changes (new regions, new variables, new terrain).
Famous analog regions (known = yes in the catalog) are left out, because the
challenge asks for little-known places.

It writes, in data/:
    results_pairs_top20.csv         20 best Earth places for each Moon/Mars site,
                                    with the values of both places side by side
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

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import compare  # noqa: E402

WEIGHTS = {"elev_m": 0, "em_contrast": 0.5}   # elevation not comparable between bodies; rock type = calibrated estimate (docs/COMPOSICION.md)
LEAVE_OUT_OF_OVERALL = {"Moon": ["Shackleton floor (shadow)"]}   # a contrast site, not a base site


def main():
    earth, targets = compare.load_inputs("data/earth_all.csv", "data/targets.csv")
    earth = earth[earth["known"] != "yes"].reset_index(drop=True)
    print(f"Comparing {len(earth):,} little-known Earth places with {len(targets)} Moon/Mars sites ...")
    results = compare.compare_all(earth, targets, weights=WEIGHTS)

    pairs = results[results["rank"] <= 20].drop(
        columns=["water_frac", "known", "sim_elev_m",
                 "target_elev_m"], errors="ignore")
    pairs.round(4).to_csv("data/results_pairs_top20.csv", index=False)

    for body in ("Mars", "Moon"):
        overall = compare.overall_ranking(results[results["body"] == body],
                                          exclude=LEAVE_OUT_OF_OVERALL.get(body, []))
        overall.drop(columns="n_met").head(1000).round(4).to_csv(
            f"data/results_{body.lower()}_overall.csv", index=False)
        per_region = (overall.sort_values(["n_met", "mean_score"], ascending=False)
                      .groupby("region", sort=False).first().reset_index().drop(columns="n_met"))
        per_region.round(4).to_csv(f"data/results_{body.lower()}_new_per_region.csv", index=False)
        print(f"\n{body}: best little-known place of each region")
        print(per_region[["region", "lat", "lon", "mean_score", "conditions_met", "weakest"]]
              .head(10).round(3).to_string(index=False))

        subprocess.run([sys.executable, str(Path(__file__).parent / "seasons.py"),
                        "--overall", f"data/results_{body.lower()}_new_per_region.csv",
                        "--targets", f"data/targets_{body.lower()}.csv",
                        "--out", f"data/seasons_{body.lower()}.csv"],
                       stdout=subprocess.DEVNULL, check=True)
    print("\nAll result tables saved in data/")


if __name__ == "__main__":
    main()
