"""
make_top_analogos.py - Top 100 Earth places for the Moon and 100 for Mars (one per
region, >= 300 km apart), each with its best Moon/Mars site and all the variables.

Run from the project root:  python src/make_top_analogos.py
Writes data/top200_analogos.csv and data/top200_analogos.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import compare  # noqa: E402
import make_results as mr  # noqa: E402
N, SEP = 100, 300   # places per body, minimum distance between places (km)
earth, targets = compare.load_inputs("data/earth_all.csv", "data/targets.csv")
cat = pd.read_csv("data/regions_catalog.csv", comment="#").set_index("name")
FEATS = [f for f in compare.FEATURES if f != "elev_m"] + ["elev_m"]
rows, js = [], {"generated": "2026-11-15", "method": "Earth database: 727 regions (worldwide drylands grid, 0.05 deg cells). "
      "Weights: elev_m 0, em_contrast 0.5, others compare.py defaults. One place per region, places at least "
      f"{SEP} km apart. mean_score = mean over all sites of that body; best_site = the site with the highest score.",
      "features": compare.FEATURES, "places": []}
for body in ["Moon", "Mars"]:
    per_region = pd.read_csv(f"data/results_{body.lower()}_new_per_region.csv")
    top = mr.spread_out(per_region, N, SEP).reset_index(drop=True)
    tg = targets[(targets.body == body) & ~targets.name.isin(mr.LEAVE_OUT_OF_OVERALL.get(body, []))].reset_index(drop=True)
    cells = top[["region", "lat", "lon"]].merge(earth, on=["region", "lat", "lon"], how="left")
    assert cells[FEATS].notna().any(axis=1).all() and len(cells) == len(top)
    res = compare.compare_all(cells.reset_index(drop=True), tg, weights=mr.WEIGHTS)
    for i, p in top.iterrows():
        e = cells.iloc[i]
        r = res[(res.lat == p.lat) & (res.lon == p.lon)].sort_values("score", ascending=False)
        b = r.iloc[0]
        row = {"body": body, "rank": i + 1, "earth_region": p.region,
               "region_description": cat.loc[p.region, "why"] if p.region in cat.index else "",
               "earth_lat": p.lat, "earth_lon": p.lon, "mean_score_all_sites": round(p.mean_score, 4),
               "conditions_met": p.conditions_met, "weakest": p.weakest,
               "best_site": b.target, "site_lat": b.target_lat, "site_lon": b.target_lon, "score_best_site": round(b.score, 4)}
        for f in FEATS:
            row[f"earth_{f}"] = e[f]
        for f in FEATS:
            row[f"site_{f}"] = b[f"target_{f}"]
        for f in compare.FEATURES:
            if f != "elev_m": row[f"sim_{f}"] = round(b[f"sim_{f}"], 4)
        rows.append(row)
        js["places"].append({**{k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in row.items()},
                             "score_per_site": {t: round(s, 4) for t, s in zip(r.target, r.score)}})
out = pd.DataFrame(rows)
out.to_csv("data/top200_analogos.csv", index=False)
json.dump(js, open("data/top200_analogos.json", "w"), ensure_ascii=False, indent=1, default=float)
pd.set_option("display.width", 250)
print(out[["body","rank","earth_region","earth_lat","earth_lon","mean_score_all_sites","conditions_met","best_site","score_best_site"]].to_string(index=False))
