import sys, numpy as np, pandas as pd
sys.path.insert(0, "/root/work/src")
import os; os.chdir("/root/work")
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
pd.concat(parts, ignore_index=True).to_parquet("/root/cells.parquet")
