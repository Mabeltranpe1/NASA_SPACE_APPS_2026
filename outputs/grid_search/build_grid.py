"""Build region files for the systematic grid search (2x2 degree areas, selected 1x1 tiles only)."""
import sys, os, re, time, numpy as np, pandas as pd
os.chdir("/root/work"); sys.path.insert(0, "src")
import build_earth as be
S = pd.read_csv("/root/selected_tiles.csv")
have = {p[:-4] for p in os.listdir("data/raw/COP90") if p.endswith(".tif")}
def tname(a, o): return f"{'N' if a>=0 else 'S'}{abs(a):02d}_00_{'E' if o>=0 else 'W'}{abs(o):03d}_00"
S["tile"] = [tname(a, o) for a, o in zip(S.tlat, S.tlon)]
S["downloaded"] = S.tile.isin(have)
S["alat"] = (np.floor(S.tlat / 2) * 2).astype(int); S["alon"] = (np.floor(S.tlon / 2) * 2).astype(int)
def slug(s): return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
rows = []
part = [a for a in sys.argv[1:] if "/" in a]
only = [a for a in sys.argv[1:] if "/" not in a]
k, K = map(int, part[0].split("/")) if part else (0, 1)
for i, ((alat, alon), g) in enumerate(S[S.downloaded].groupby(["alat", "alon"])):
    country = g.country.value_counts().index[0]
    name = f"{slug(country)}_{abs(alat):02d}{'n' if alat>=0 else 's'}_{abs(alon):03d}{'e' if alon>=0 else 'w'}"
    reasons = sorted({r.split("_")[0] if not r.startswith("named") else r for w in g.why for r in w.split(";") if r})
    known = "yes" if g.known.fillna("").ne("").any() else "no"
    near = "; near " + g.known.dropna().iloc[0] if known == "yes" else ""
    why = f"Grid search {country}: {len(g)} of 4 tiles ({', '.join(reasons)}){near}"
    rows.append(dict(name=name, west=alon, south=alat, east=alon + 2, north=alat + 2, dem="cop90", known=known, why=why))
    out = f"data/regions/{name}.csv"
    if os.path.exists(out) or (only and name not in only) or i % K != k:
        continue
    t0 = time.time()
    grid = be.make_grid(alon, alat, alon + 2, alat + 2)
    lat, lon = be.cell_centres(*grid)
    layers = {}
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        layers.update(be.terrain(grid, "cop90"))
        layers.update(be.surface_layers(grid, lat, lon))
    table = pd.DataFrame({"region": name, "lat": lat.ravel().round(3), "lon": lon.ravel().round(3)})
    for key in ["elev_m", "slope_deg", "roughness"] + be.SURFACE + ["water_frac"]:
        table[key] = layers[key].ravel()
    keep = table["elev_m"].notna() & (table["water_frac"].fillna(1) <= 0.5)
    table[keep].round(be.ROUNDING).to_csv(out, index=False)
    print(f"{name}: {keep.sum()} cells, {time.time()-t0:.1f}s", flush=True)
pd.DataFrame(rows).to_csv("/root/grid_catalog_rows.csv", index=False)
print("areas", len(rows))
