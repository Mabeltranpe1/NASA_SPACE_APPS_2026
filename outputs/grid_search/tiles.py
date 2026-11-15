import sys, numpy as np, pandas as pd, shapefile
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
sys.path.insert(0, "/root/work/src"); import screen_global as sg
c = pd.read_parquet("/root/cells.parquet")
c["tlat"] = np.floor(c.lat).astype(int); c["tlon"] = np.floor(c.lon).astype(int)
g = c.groupby(["tlat","tlon"])
T = g.agg(n=("lat","size"), precip=("precip_mm","median"), ndvi=("ndvi","median"), albedo=("albedo","median"), temp=("temp_mean_K","median")).reset_index()
for b in ["mars","moon"]:
    T[f"{b}90"] = g[f"s_{b}"].quantile(0.9).values
T = T[T.n >= 40]   # >=10% land
r = shapefile.Reader("/root/ne/ne_50m_admin_0_countries")
names = [rec["ADMIN"] for rec in r.records()]; geoms = [shape(s.__geo_interface__) for s in r.shapes()]
tree = STRtree(geoms)
def country(la, lo):
    p = Point(lo, la); idx = tree.query(p)
    for i in idx:
        if geoms[i].contains(p): return names[i]
    i = tree.nearest(p); return names[i]
# country by majority of land cells would be better; use centroid of land cells
cent = g[["lat","lon"]].mean().reset_index()
T = T.merge(cent, on=["tlat","tlon"])
T["country"] = [country(a, o) for a, o in zip(T.lat, T.lon)]
T["known"] = [sg.nearest_known(a+0.5, o+0.5) for a, o in zip(T.tlat, T.tlon)]
cat = pd.read_csv("/root/work/data/regions_catalog.csv", comment="#")
def covered(a, o):
    return ((cat.west <= o) & (cat.east >= o+1) & (cat.south <= a) & (cat.north >= a+1)).any()
T["covered"] = [covered(a, o) for a, o in zip(T.tlat, T.tlon)]
T.to_csv("/root/tiles.csv", index=False)
print(len(T), "land tiles")
