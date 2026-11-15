from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]      # project root
WORK = ROOT / "outputs" / "grid_search"          # intermediate files of the grid search
import sys, numpy as np, pandas as pd
sys.path.insert(0, str(ROOT / "src"))
import os; os.chdir(ROOT)
import screen_global as sg, compare
t = pd.read_csv("data/targets.csv", comment="#")
parts = []
for north in range(90, -90, -sg.BAND):
    lat, lon, layers = sg.load_band(north, north - sg.BAND)
    out = None
    for body, g in t.groupby("body", sort=False):
        if body == "Moon": g = g[g["name"] != "Shackleton floor (shadow)"] if "name" in g else g
        land, score = sg.score_band(layers, g, compare.DEFAULT_WEIGHTS)
        if out is None:
            out = pd.DataFrame({"lat": lat[land], "lon": lon[land]})
            for n in sg.USED: out[n] = layers[n][land]
        out[f"s_{body.lower()}"] = score
    parts.append(out.astype("float32")); print(north, len(out), flush=True)
pd.concat(parts, ignore_index=True).to_parquet(WORK / "cells.parquet")
