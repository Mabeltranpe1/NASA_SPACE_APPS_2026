"""Rankings before (no composition) and after (calibrated em_contrast). Run from the repo root."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, "src")
import compare  # noqa: E402

OUT = Path("outputs/composition")
WEIGHTS = {"elev_m": 0}
LEAVE_OUT = {"Moon": ["Shackleton floor (shadow)"]}

earth, targets = compare.load_inputs("data/earth_all.csv", "data/targets.csv")
earth = earth[earth["known"] != "yes"].reset_index(drop=True)
before_t = targets.copy(); before_t["em_contrast"] = np.nan

runs = {"before": (before_t, WEIGHTS), "after": (targets, WEIGHTS),
        "after_w05": (targets, {**WEIGHTS, "em_contrast": 0.5})}
res = {k: compare.compare_all(earth, t, weights=w, top=15000) for k, (t, w) in runs.items()}

# 1) per target: top-20 regions and top-1 place
rows = []
for name in targets["name"]:
    row = {"target": name}
    for k, r in res.items():
        r = r[r["target"] == name]
        top = r[r["rank"] <= 20]
        row[f"{k}_top1"] = f"{top.iloc[0]['region']} ({top.iloc[0]['lat']:.2f},{top.iloc[0]['lon']:.2f}) {top.iloc[0]['score']:.3f}"
        row[f"{k}_top20_regions"] = ", ".join(top["region"].value_counts().index[:3])
        if k != "before":
            prev = res["before"][res["before"]["target"] == name]
            prev20 = set(zip(prev[prev["rank"] <= 20]["lat"], prev[prev["rank"] <= 20]["lon"]))
            row[f"{k}_overlap20"] = len(prev20 & set(zip(top["lat"], top["lon"])))
    rows.append(row)
per_target = pd.DataFrame(rows)
per_target.to_csv(OUT / "per_target_before_after.csv", index=False)

# 2) overall per body: best place per region, before vs after
for body in ("Moon", "Mars"):
    tabs = {}
    for k, r in res.items():
        ov = compare.overall_ranking(r[r["body"] == body], exclude=LEAVE_OUT.get(body, []))
        reg = ov.groupby("region", sort=False).first().reset_index()
        reg["region_rank"] = np.arange(1, len(reg) + 1)
        tabs[k] = reg.set_index("region")
        ov.drop(columns="n_met").head(200).round(4).to_csv(OUT / f"overall_{body.lower()}_{k}.csv", index=False)
    comp = pd.DataFrame({
        "rank_before": tabs["before"]["region_rank"],
        "score_before": tabs["before"]["mean_score"].round(3),
        "rank_after": tabs["after"]["region_rank"],
        "score_after": tabs["after"]["mean_score"].round(3),
        "sim_em_after": tabs["after"].get("sim_em_contrast", pd.Series(dtype=float)).round(2),
        "rank_after_w05": tabs["after_w05"]["region_rank"],
    }).sort_values("rank_after")
    comp["change"] = comp["rank_before"] - comp["rank_after"]
    comp.to_csv(OUT / f"regions_{body.lower()}_before_after.csv")
    print(f"\n===== {body}: region ranking (best little-known place of each region) =====")
    print(comp.head(15).to_string())

with pd.option_context("display.width", 300, "display.max_colwidth", 60):
    print("\n===== per target: top 1 before / after =====")
    print(per_target[["target", "before_top1", "after_top1", "after_overlap20", "after_w05_overlap20"]].to_string(index=False))
    print(per_target[["target", "before_top20_regions", "after_top20_regions"]].to_string(index=False))
