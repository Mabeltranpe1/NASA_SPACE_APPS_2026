import sys, os; os.chdir("/root/work"); sys.path.insert(0, "src")
import pandas as pd, compare, make_results as mr
earth, targets = compare.load_inputs("data/earth_all.csv", "data/targets.csv")
earth = earth[earth["known"] != "yes"].reset_index(drop=True)
results = compare.compare_all(earth, targets, weights=mr.WEIGHTS)
best = results.sort_values(["target", "rank"]).drop_duplicates(["target", "region"])
by_region = pd.concat([mr.spread_out(g, 5, mr.MIN_SEPARATION_KM) for _, g in best.groupby("target", sort=False)])
by_region = by_region.drop(columns=["water_frac", "known", "sim_elev_m", "target_elev_m"], errors="ignore")
by_region.round(4).to_csv("data/results_per_target_top_regions.csv", index=False)
