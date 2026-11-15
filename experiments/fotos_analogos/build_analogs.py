"""
Top Earth analogs for the 6 photographed Moon/Mars sites.

Run from the repo root:
    python experiments/fotos_analogos/build_analogs.py

For each target: compare.compare_all (elevation weight 0, top 200 cells) on
the NEW Earth cells (known != 'yes'), keep the best cell per region and take
the top 3 regions; plus the best cell among the KNOWN analog sites.
If maps/ already has an Earth photo for that target + region, list it.
"""
import os
import re
import sys

import pandas as pd

sys.path.insert(0, "src")
import compare  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SITES = ["Jezero crater (Perseverance)", "Gale crater (Curiosity)", "Vastitas Borealis (Phoenix)",
         "Shackleton rim", "de Gerlache rim", "Mons Mouton summit"]
WEIGHTS = {"elev_m": 0}
# top=200 (as asked) only covers 2 regions for the Mars sites, so if a target
# has < 3 regions in its top 200 we widen the search (best cell per region is
# the same either way, top only cuts the list).
TOP = 200


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def earth_photo(target, region):
    """Look for maps/NN_<body>_<target...>_A?_earth_<region>_photo.png."""
    idx = pd.read_csv("maps/index.csv", dtype=str)
    files = os.listdir("maps")
    rows = idx[idx.target == target]
    prefixes = {r.image_twin.rsplit("_B_", 1)[0] for r in rows.itertuples()}
    if not prefixes:  # fall back on the target name
        prefixes = {f.split("_A")[0] for f in files if slug(target.split(" (")[0]) in f}
    for f in sorted(files):
        if f.endswith(f"_earth_{region}_photo.png") and any(f.startswith(p + "_A") for p in prefixes):
            return os.path.join("maps", f)
    return ""


def nearby_photo(region, lat, lon, tol=0.3):
    """Photo made for ANOTHER target but of (almost) the same Earth cell."""
    idx = pd.read_csv("maps/index.csv")
    near = idx[(idx.earth_region == region) & ((idx.earth_lat - lat).abs() <= tol)
               & ((idx.earth_lon - lon).abs() <= tol)]
    for f in near.image_earth:
        photo = os.path.join("maps", f.replace(".png", "_photo.png"))
        if os.path.exists(photo):
            return photo
    return ""


def best_regions(table, n):
    t = table.sort_values("score", ascending=False).drop_duplicates("region")
    return t.head(n)


def main():
    earth, targets = compare.load_inputs("data/earth_all.csv", "data/targets.csv")
    missing = set(SITES) - set(targets.name)
    if missing:
        raise SystemExit(f"not in targets.csv: {missing}")
    targets = targets[targets.name.isin(SITES)].reset_index(drop=True)

    earth_new = earth[earth.known != "yes"].reset_index(drop=True)
    new = compare.compare_all(earth_new, targets, weights=WEIGHTS, top=TOP)
    new["top_used"] = TOP
    short = [t for t, g in new.groupby("target") if g.region.nunique() < 3]
    if short:
        wide = compare.compare_all(earth_new, targets[targets.name.isin(short)].reset_index(drop=True),
                                   weights=WEIGHTS, top=None)
        wide["top_used"] = "all"
        new = pd.concat([new[~new.target.isin(short)], wide], ignore_index=True)
    known = compare.compare_all(earth[earth.known == "yes"].reset_index(drop=True), targets,
                                weights=WEIGHTS, top=TOP)
    rows = []
    for name in SITES:
        for setname, table, n in (("new", new, 3), ("known", known, 1)):
            top = best_regions(table[table.target == name], n)
            for rank, r in enumerate(top.itertuples(), 1):
                rows.append({"target": name, "set": setname, "rank": rank, "region": r.region,
                             "lat": r.lat, "lon": r.lon, "score": round(r.score, 4),
                             "best_match": r.best_match, "worst_match": r.worst_match,
                             "top_used": getattr(r, "top_used", TOP),
                             "earth_photo": earth_photo(name, r.region),
                             "earth_photo_same_cell_other_target":
                                 "" if earth_photo(name, r.region) else nearby_photo(r.region, r.lat, r.lon)})
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(HERE, "analogs.csv"), index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
