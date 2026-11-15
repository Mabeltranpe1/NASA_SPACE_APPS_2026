import pandas as pd, numpy as np, re
T = pd.read_csv("/root/tiles.csv")
SKIP = {"China","Russia","Iran","Iraq","Syria","Yemen","Afghanistan","Saudi Arabia","United Arab Emirates","Oman","Kuwait","Qatar","Jordan","Israel","Lebanon","Bahrain","Palestine","North Korea","Antarctica"}
T["skip"] = T.country.isin(SKIP) | T.known.str.contains("avoid", na=False)
base = ~T.skip & ~T.covered & (T.albedo < 0.55)
arid = base & (T.precip < 300) & (T.ndvi < 0.25)
semi = base & (T.precip < 500) & (T.ndvi < 0.35)
sel = pd.Series("", index=T.index)
# 1. best tiles by climate/surface screening (full coverage), within semi-arid land
for b, n in [("mars", 400), ("moon", 250)]:
    top = T[semi].sort_values(f"{b}90", ascending=False).head(n).index
    sel[top] = sel[top] + f"top_{b};"
# 2. coarse checkerboard over all arid land
cb = arid & ((T.tlat + T.tlon) % 2 == 0)
sel[cb[cb].index] += "grid;"
# 3. places named by the user / classic geology, full coverage
NAMED = {  # west south east north
 "richat": (-13, 20, -10, 23), "patagonia": (-72, -51, -65, -40), "tierra_del_fuego": (-70, -55, -65, -52),
 "andes_peru_bolivia": (-73, -19, -67, -13), "ustyurt": (54, 42, 59, 46), "kyzylkum": (61, 40, 66, 44),
 "karakum_darvaza": (57, 38, 62, 42), "betpak_dala": (68, 44, 72, 47), "puna_south": (-69, -30, -66, -27),
}
for k, (w, s, e, n) in NAMED.items():
    m = base & (T.tlon >= w) & (T.tlon < e) & (T.tlat >= s) & (T.tlat < n)
    sel[m[m].index] += f"named_{k};"
T["why"] = sel
S = T[sel != ""].copy()
S.to_csv("/root/selected_tiles.csv", index=False)
print("tiles", len(S)); print(S.why.str.split(";").explode().str.replace(r"named_.*","named",regex=True).value_counts().to_string())
print(S.country.value_counts().head(40).to_string())
