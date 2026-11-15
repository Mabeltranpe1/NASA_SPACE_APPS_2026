"""
export_web.py - Turn the comparison results into the JSON files the web app reads.

It does NOT change how similarity is computed: it calls compare.py (Marco's
comparator) and only decides WHAT goes to the web and in which format.
Data contract: docs/VISUALIZACION_COMPARACION.md.

Inputs (defaults):
    data/earth_all.csv.gz     Expanded Earth grid, one row per 0.05 deg cell (Marco)
    data/targets.csv          Moon and Mars sites (Marco)
    data/regions_catalog.csv  description of each Earth region (Marco)
    web/src/data/sites.ts     catalog sites shown in the app (their lat/lng)
    data/features/*.csv       detailed characterization of the Colombian
                              sites at 200 m (Santiago)

Outputs (web/public/data/):
    comparisons.json          catalog sites + best little-known places
                              ("discoveries"), with every target's result
    heatmap/<target>.json     the best Earth cells for one target (map layer)
    global-rankings.json      original Marco top 200 with navigation references
    science/                 regional observations, original PAI and source assets

Rules applied here (explained in docs/DATOS_WEB.md):
    1. Elevation is never compared: each body measures height from a
       different zero level (sea level, areoid, reference sphere).
    2. A feature is switched off for a body (Moon or Mars) when the typical
       value of its sites is outside the range found on Earth by more than
       one tolerance (e.g. the Moon at 125 K). Earth cannot reproduce it, so
       the app shows it as a limit of the analogy instead of letting it
       decide the score.
    3. Discoveries are chosen per REGION (best cell of each little-known
       region), so one very good region cannot fill the whole list.

Example:
    python src/export_web.py
"""

import argparse
import gzip
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare  # noqa: E402
from scientific_catalog import build_science, validate_comparison_contract  # noqa: E402
from science_metadata import GLOBAL_COMMIT, SCIENCE_COMMIT, WEB_COMMIT  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# 1. Settings
# ---------------------------------------------------------------------------

# Weights used for the web, on top of compare.DEFAULT_WEIGHTS.
WEB_WEIGHTS = {"elev_m": 0.0, "em_contrast": 0.5}

# A target value further than this many tolerances outside Earth's range
# switches that feature off for that body (rule 2).
OUT_OF_RANGE_TOLERANCES = 1.0

DISCOVERIES_PER_TARGET = 6      # best little-known regions kept per target
HEATMAP_CELLS = 2500            # best cells per target in the map layer
CATALOG_MAX_DEG = 0.1           # catalog site -> nearest grid cell (~11 km)
STABILITY_RUNS = 100            # random weight variations
STABILITY_SPREAD = 0.5          # each weight x U(0.5, 1.5)
STABILITY_TOP = 500             # "stays in the top N cells of the planet"

# Moon/Mars target name -> id used by the web (homologue ids in sites.ts).
TARGET_IDS = {
    "Shackleton rim": "shackleton",
    "de Gerlache rim": "de-gerlache",
    "Haworth rim": "haworth",
    "Faustini rim": "faustini",
    "Mons Mouton summit": "mons-mouton",
    "Shackleton floor (shadow)": "shackleton-floor",
    "Jezero crater (Perseverance)": "jezero",
    "Gale crater (Curiosity)": "gale",
    "Elysium Planitia (InSight)": "elysium",
    "Meridiani Planum (Opportunity)": "meridiani",
    "Gusev crater (Spirit)": "gusev",
    "Chryse Planitia (Viking 1)": "chryse",
    "Utopia Planitia (Viking 2)": "utopia",
    "Vastitas Borealis (Phoenix)": "phoenix",
    "Arcadia Planitia (human candidate)": "arcadia",
}

BODY_IDS = {"moon": "luna", "luna": "luna", "mars": "marte", "marte": "marte"}

# Santiago's region names -> catalog ids in web/src/data/sites.ts.
SANTIAGO_SITES = {
    "Tatacoa": "tatacoa",
    "La_Guajira": "la-guajira",
    "Nevado_del_Ruiz": "nevado-del-ruiz",
    "Nevado_Santa_Isabel": "nevado-santa-isabel",
    "Volcan_Purace": "volcan-purace",
    "La_Candelaria": "la-candelaria",
}

# Metadata shown in the app. Keys must match compare.FEATURES.
# "range" is the fixed axis used to draw the real values.
EARTH_DEM = "NASADEM / Copernicus, a 200 m"
FEATURE_META = {
    "elev_m": {"label": "Elevación", "unit": "m", "dimension": "terreno", "range": [-6000, 6000],
               "source_earth": EARTH_DEM,
               "source_target": {"luna": "LRO LOLA", "marte": "HRSC + MOLA, 200 m"}},
    "slope_deg": {"label": "Pendiente", "unit": "°", "dimension": "terreno", "range": [0, 30],
                  "source_earth": EARTH_DEM,
                  "source_target": {"luna": "LRO LOLA, a 200 m", "marte": "HRSC + MOLA, 200 m"}},
    "roughness": {"label": "Rugosidad", "unit": "m", "dimension": "terreno", "range": [0, 40],
                  "source_earth": EARTH_DEM,
                  "source_target": {"luna": "LRO LOLA, a 200 m", "marte": "HRSC + MOLA, 200 m"}},
    "temp_mean_K": {"label": "Temperatura media", "unit": "K", "dimension": "temperatura", "range": [0, 350],
                    "source_earth": "MODIS MOD11C3 (LST)",
                    "source_target": {"luna": "LRO Diviner", "marte": "Mars Climate Database v6.2 (modelo)"}},
    "temp_range_K": {"label": "Amplitud térmica", "unit": "K", "dimension": "temperatura", "range": [0, 160],
                     "source_earth": "MODIS MOD11C3 (LST)",
                     "source_target": {"luna": "LRO Diviner", "marte": "Mars Climate Database v6.2 (modelo)"}},
    "albedo": {"label": "Albedo", "unit": "", "dimension": "geologia", "range": [0, 1],
               "source_earth": "MODIS MCD43C3",
               "source_target": {"luna": "LRO LOLA (albedo normal)", "marte": "MGS TES"}},
    "precip_mm": {"label": "Precipitación anual", "unit": "mm", "dimension": "agua_hielo", "range": [0, 3000],
                  "source_earth": "GPM IMERG / MERRA-2 (|lat| ≥ 60°)",
                  "source_target": {"luna": "0 (no llueve)", "marte": "0 (no llueve)"}},
    "ndvi": {"label": "Vegetación (NDVI)", "unit": "", "dimension": "habitabilidad", "range": [-0.2, 1],
             "source_earth": "MODIS MOD13C2",
             "source_target": {"luna": "0 (sin plantas)", "marte": "0 (sin plantas)"}},
    "em_contrast": {"label": "Tipo de roca (emisividad)", "unit": "", "dimension": "geologia", "range": [-0.1, 0.3],
                    "source_earth": "ASTER GED",
                    "source_target": {"luna": "CF: equivalente bibliográfico calibrado (±0.026–0.039)", "marte": "CF: equivalente bibliográfico calibrado (±0.026–0.039)"}},
}


# ---------------------------------------------------------------------------
# 2. Small helpers
# ---------------------------------------------------------------------------

def num(value, digits=8):
    """JSON-safe number: NaN/inf/None become null."""
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return round(value, digits)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")


def target_id(name):
    return TARGET_IDS.get(name, slug(name))


def cell_id(lat, lon):
    return f"cell_{lat:.3f}_{lon:.3f}"


def region_label(name):
    """'north_greenland' -> 'North Greenland'."""
    return str(name).replace("_", " ").title()


def read_catalog_sites(path):
    """
    Read id, name, lat and lng of each catalog site from web/src/data/sites.ts,
    so the coordinates live in one place only (the web catalog).
    """
    text = Path(path).read_text(encoding="utf-8")
    pattern = re.compile(
        r"\n  \{\n    id: '([^']+)',\n    name: '([^']+)',\n    country: '([^']+)',\n"
        r"    lat: (-?[\d.]+),\n    lng: (-?[\d.]+),")
    sites = [{"id": m[0], "name": m[1], "country": m[2], "lat": float(m[3]), "lng": float(m[4])}
             for m in pattern.findall(text)]
    declared = len(re.findall(r"\n  \{\n    id: '", text))
    if len(sites) != declared:
        raise ValueError(f"{path}: read {len(sites)} of {declared} sites. "
                         "Keep the id, name, country, lat, lng order of the existing entries.")
    return sites


def nearest_cell(earth, lat, lng, max_deg):
    """Index of the Earth cell closest to (lat, lng), or None if further than max_deg."""
    dlat = earth["lat"].to_numpy() - lat
    dlon = (earth["lon"].to_numpy() - lng + 180) % 360 - 180
    dist = np.hypot(dlat, dlon * math.cos(math.radians(lat)))
    i = int(np.argmin(dist))
    return i if dist[i] <= max_deg else None


# ---------------------------------------------------------------------------
# 3. Weights per target (rules 1 and 2)
# ---------------------------------------------------------------------------

def body_weights(targets, earth):
    """
    Weights per body and the features switched off for that body (rule 2).

    A feature is switched off for a body when the TYPICAL value of its targets
    (the median) is outside the range found on Earth by more than
    OUT_OF_RANGE_TOLERANCES tolerances. Deciding per body, not per target,
    keeps all the sites of one body comparable with each other.
    Returns {body: (weights dict, excluded list)}.
    """
    out = {}
    for body, group in targets.groupby("body"):
        weights = {**compare.DEFAULT_WEIGHTS, **WEB_WEIGHTS}
        excluded = []
        for feature in compare.FEATURES:
            values = group[feature].dropna()
            if values.empty or weights.get(feature, 0) == 0:
                continue
            value = values.median()
            low, high = earth[feature].min(), earth[feature].max()
            if feature in compare.LOG_FEATURES:
                value, low, high = np.log1p(value), np.log1p(low), np.log1p(high)
            tol = compare.TOLERANCE[feature] * OUT_OF_RANGE_TOLERANCES
            if value < low - tol or value > high + tol:
                weights[feature] = 0.0
                excluded.append(feature)
        out[body] = (weights, excluded)
    return out


# ---------------------------------------------------------------------------
# 4. Scores for one target over the whole Earth grid
# ---------------------------------------------------------------------------

def score_target(earth_scaled, target_scaled, weights):
    w = compare.build_weights(weights)
    return compare.score_cells(earth_scaled, target_scaled, w)


def global_rank(score):
    """Rank 1 = best cell. Cells without a score get the last ranks."""
    order = np.argsort(-np.nan_to_num(score, nan=-1.0), kind="stable")
    rank = np.empty(len(score), dtype=int)
    rank[order] = np.arange(1, len(score) + 1)
    return rank


def stability(earth_scaled, target_scaled, weights, cells, rng):
    """
    Share of random weight variations in which each cell in `cells` stays in
    the top STABILITY_TOP cells of the planet. Same idea as
    compare.weight_sensitivity, measured only for the cells we export.
    """
    base = compare.build_weights(weights)
    active = (base > 0) & np.isfinite(target_scaled)
    if not active.any():
        raise ValueError("No active feature for weight sensitivity")
    base = base[active]
    valid = np.isfinite(earth_scaled[:, active]).all(axis=1)
    squares = np.nan_to_num(earth_scaled[:, active] - target_scaled[active]) ** 2
    inside = np.zeros(len(cells))
    for _ in range(STABILITY_RUNS):
        # Draw all feature factors, as in the original algorithm, including inactive ones.
        factors = rng.uniform(1 - STABILITY_SPREAD, 1 + STABILITY_SPREAD, size=len(compare.FEATURES))[active]
        w = base * factors
        score = np.exp(-np.sqrt(np.einsum("ij,j->i", squares, w) / w.sum()))
        score[~valid] = -np.inf
        n = min(STABILITY_TOP, len(score))
        cutoff = np.partition(score, len(score) - n)[len(score) - n]
        n_above = int(np.count_nonzero(score > cutoff))
        tied = np.flatnonzero(score == cutoff)[:n - n_above]
        # Preserve stable row-order ties without sorting all 691k cells on every run.
        last_tied = tied[-1] if len(tied) else -1
        inside += np.isfinite(score[cells]) & ((score[cells] > cutoff) | ((score[cells] == cutoff) & (cells <= last_tied)))
    return inside / STABILITY_RUNS


# ---------------------------------------------------------------------------
# 5. Santiago's characterization of the Colombian sites
# ---------------------------------------------------------------------------

def read_csv_if_exists(path):
    path = Path(path)
    return pd.read_csv(path) if path.exists() else None


def santiago_characterization(features_dir):
    """
    Detailed 10 x 10 km characterization of the Colombian sites (Santiago),
    keyed by catalog id. Descriptive only: it does not enter the score.
    """
    features_dir = Path(features_dir)
    topo = read_csv_if_exists(features_dir / "planetary_features.csv")
    env = read_csv_if_exists(features_dir / "environmental_features.csv")
    spec = read_csv_if_exists(features_dir / "spectral_features.csv")
    emit = read_csv_if_exists(features_dir / "emit_availability.csv")
    pai = read_csv_if_exists(features_dir.parent / "results" / "analog_ranking.csv")

    def row(df, region, planet="earth"):
        if df is None:
            return None
        hit = df[(df["region"] == region) & (df.get("planet", planet) == planet)]
        return hit.iloc[0] if len(hit) else None

    out = {}
    for region, site_id in SANTIAGO_SITES.items():
        info = {"source": "Santiago (feature/planetary-analysis)", "window_km": 10, "status": "experimental"}
        t = row(topo, region)
        if t is not None:
            info["topography"] = {
                "resolution_m": num(t["resolution_m"], 0),
                "elevation_mean_m": num(t["elevation_mean_m"], 1),
                "relief_p90_p10_m": num(t["relief_p90_p10_m"], 1),
                "slope_mean_deg": num(t["slope_mean_deg"], 2),
                "slope_p90_deg": num(t["slope_p90_deg"], 2),
                "tri_mean_m": num(t["tri_mean_m"], 1),
                "flat_terrain_pct": num(t["flat_terrain_pct"], 1),
                "source": "NASADEM",
            }
        e = row(env, region)
        if e is not None:
            info["environment"] = {
                "lst_day_mean_K": num(e["lst_day_mean_c"] + 273.15, 1),
                "lst_night_mean_K": num(e["lst_night_mean_c"] + 273.15, 1),
                "thermal_range_mean_K": num(e["thermal_range_mean_c"], 1),
                "ndvi_mean": num(e["ndvi_mean"], 3),
                "annual_precipitation_mm": num(e["annual_precipitation_mm"], 0),
                "bare_ground_pct": num(e["bare_ground_pct"], 1),
                "snow_ice_pct": num(e["snow_ice_pct"], 1),
                "water_pct": num(e["water_pct"], 1),
                "period": f"{e['period_start']} – {e['period_end_exclusive']}",
                "source": "MODIS MOD11A1/MOD13Q1, CHIRPS, ESA WorldCover (GEE)",
            }
        s = row(spec, region)
        if s is not None:
            info["spectral"] = {
                "iron_oxide_ratio": num(s["iron_oxide_ratio_mean"], 3),
                "hydroxyl_ratio": num(s["hydroxyl_ratio_mean"], 3),
                "bare_soil_index": num(s["bare_soil_index_mean"], 3),
                "valid_coverage_pct": num(s["spectral_coverage_pct"], 1),
                "low_vegetation_pct": num(s["low_vegetation_valid_pct"], 1),
                "source": "Sentinel-2 L2A (2025)",
            }
        m = row(emit, region)
        if m is not None:
            info["mineralogy"] = {"status": "provisional", "emit_granules": int(m["emit_granules"])}
        if pai is not None:
            best = (pai[pai["candidate"] == f"earth_{region}"]
                    .sort_values("PAI", ascending=False)
                    .assign(body=lambda d: d["target"].str.split("_").str[0]))
            info["topographic_index"] = [
                {"target": r["target"].split("_", 1)[1].replace("_", " "),
                 "body": BODY_IDS.get(r["body"], r["body"]), "pai": num(r["PAI"], 1)}
                for _, r in best.groupby("body", sort=False).head(1).iterrows()
            ]
        if region == "La_Guajira":
            info["quality_flags"] = ["ventana costera: puede incluir mar (provisional)"]
        out[site_id] = info
    return out


# ---------------------------------------------------------------------------
# 6. Build everything
# ---------------------------------------------------------------------------

def is_synthetic(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return "SYNTHETIC" in f.readline().upper()


def build(earth_path, targets_path, regions_path, sites_ts, features_dir, seed=0):
    earth, targets = compare.load_inputs(earth_path, targets_path)
    regions = pd.read_csv(regions_path, comment="#") if Path(regions_path).exists() else None
    region_why = dict(zip(regions["name"], regions["why"])) if regions is not None else {}
    known = (earth["known"] == "yes").to_numpy() if "known" in earth.columns else np.zeros(len(earth), bool)
    region_col = earth["region"].to_numpy() if "region" in earth.columns else np.full(len(earth), "")

    earth_scaled, targets_scaled = compare.scale_together(earth, targets)
    rng = np.random.default_rng(seed)

    # Catalog sites -> nearest grid cell.
    catalog = read_catalog_sites(sites_ts)
    site_cells = {}      # site id -> cell index
    site_info = {}       # site id -> fields for the JSON
    unmatched = []
    for s in catalog:
        i = nearest_cell(earth, s["lat"], s["lng"], CATALOG_MAX_DEG)
        if i is None:
            unmatched.append(s["id"])
            continue
        site_cells[s["id"]] = i
        site_info[s["id"]] = {"kind": "catalog", "name": s["name"]}

    # Retain all 200 places from Marco's published full-environment ranking in the
    # canonical site catalog, so opening that ranking keeps map/comparison controls.
    top_path = Path(earth_path).parent / "top200_analogos.csv"
    if top_path.exists():
        top = pd.read_csv(top_path)
        grid_indices = {(round(a, 6), round(o, 6)): i for i, (a, o) in enumerate(zip(earth["lat"], earth["lon"]))}
        for row in top.to_dict("records"):
            key = (round(row["earth_lat"], 6), round(row["earth_lon"], 6))
            if key not in grid_indices:
                raise ValueError(f"Published global ranking cell {key} is missing from {earth_path}; use the expanded gzip database")
            i = grid_indices[key]
            sid = cell_id(row["earth_lat"], row["earth_lon"])
            site_cells.setdefault(sid, i)
            site_info.setdefault(sid, {"kind": "discovery", "name": region_label(row["earth_region"]), "note": row.get("region_description")})

    per_body = body_weights(targets, earth)
    per_target = []
    heatmaps = {}
    for pos, (_, t) in enumerate(targets.iterrows()):
        print(f"Scoring {t['name']} on {len(earth):,} original global cells", flush=True)
        weights, excluded = per_body[t["body"]]
        score, sims = score_target(earth_scaled, targets_scaled[pos], weights)
        rank = global_rank(score)
        tid = target_id(t["name"])

        # Discoveries: best cell of each little-known region (rule 3).
        free = ~known & np.isfinite(score)
        best_by_region = (pd.DataFrame({"i": np.flatnonzero(free), "region": region_col[free],
                                        "score": score[free]})
                          .sort_values("score", ascending=False)
                          .drop_duplicates("region")
                          .head(DISCOVERIES_PER_TARGET))
        for i, region in zip(best_by_region["i"], best_by_region["region"]):
            sid = cell_id(earth["lat"].iat[i], earth["lon"].iat[i])
            site_cells.setdefault(sid, int(i))
            site_info.setdefault(sid, {"kind": "discovery", "name": region_label(region),
                                       "note": region_why.get(region)})

        top = np.argsort(-np.nan_to_num(score, nan=-1.0), kind="stable")[:HEATMAP_CELLS]
        heatmaps[tid] = [[num(earth["lat"].iat[i], 3), num(earth["lon"].iat[i], 3), num(score[i], 3)]
                         for i in top]
        per_target.append({"pos": pos, "id": tid, "row": t, "weights": weights, "excluded": excluded,
                           "score": score, "rank": rank})

    # Results of every exported site for every target.
    cells = np.array(list(site_cells.values()))
    ids = list(site_cells.keys())
    results = {sid: [] for sid in ids}
    for tg in per_target:
        print(f"Sensitivity {tg['row']['name']}: {STABILITY_RUNS} runs", flush=True)
        stab = stability(earth_scaled, targets_scaled[tg["pos"]], tg["weights"], cells, rng)
        _, exported_sims = score_target(earth_scaled[cells], targets_scaled[tg["pos"]], tg["weights"])
        for k, (sid, i) in enumerate(zip(ids, cells)):
            if not np.isfinite(tg["score"][i]):
                continue
            sim = {f: num(exported_sims[k, j]) for j, f in enumerate(compare.FEATURES)}
            used = {f: v for f, v in sim.items() if v is not None}
            results[sid].append({
                "target": tg["id"],
                "score": num(tg["score"][i]),
                "sim": sim,
                "best_match": max(used, key=used.get) if used else None,
                "worst_match": min(used, key=used.get) if used else None,
                "rank": int(tg["rank"][i]),
                "stability": num(stab[k], 3),
            })

    characterization = santiago_characterization(features_dir)
    sites = []
    for sid, i in site_cells.items():
        row = earth.iloc[i]
        entry = {
            "id": sid,
            **site_info[sid],
            "lat": num(row["lat"], 3),
            "lng": num(row["lon"], 3),
            "region": str(region_col[i]) or None,
            "known": bool(known[i]),
            "values": {f: num(row[f]) for f in compare.FEATURES},
            "results": results[sid],
        }
        if sid in characterization:
            entry["characterization"] = characterization[sid]
        entry = {k: v for k, v in entry.items() if v is not None}
        sites.append(entry)

    target_list = [{
        "id": tg["id"],
        "body": BODY_IDS.get(str(tg["row"]["body"]).lower(), str(tg["row"]["body"]).lower()),
        "name": str(tg["row"]["name"]),
        "lat": num(tg["row"].get("site_lat"), 3),
        "lng": num(tg["row"].get("site_lon"), 3),
        "area": tg["row"].get("area") if isinstance(tg["row"].get("area"), str) else None,
        "values": {f: num(tg["row"][f]) for f in compare.FEATURES},
        "excluded": tg["excluded"],
        "best_score": num(np.nanmax(tg["score"])),
    } for tg in per_target]

    weights = {**compare.DEFAULT_WEIGHTS, **WEB_WEIGHTS}
    data = {
        "version": "3",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "synthetic": is_synthetic(earth_path) or is_synthetic(targets_path),
        "n_cells": int(len(earth)),
        "n_regions": int(len(set(region_col))),
        "stability_runs": STABILITY_RUNS,
        "stability_top": STABILITY_TOP,
        "features": [
            {"id": f, **FEATURE_META.get(f, {"label": f, "unit": "", "dimension": "terreno"}),
             "default_weight": float(weights.get(f, 0.0))}
            for f in compare.FEATURES
        ],
        "targets": target_list,
        "sites": sites,
        "method": {"id": "web-comparable-dimensions-v3", "equation": "exp(-sqrt(sum(w*d²)/sum(w)))", "scaling": "physical tolerances; log1p precipitation", "excluded_policy": "per-body outside terrestrial range; see each target.excluded", "global_cell_source": str(Path(earth_path).name), "regional_science_replaces_global_cells": False},
        "provenance": {"global_commit": GLOBAL_COMMIT, "science_commit": SCIENCE_COMMIT, "web_base_commit": WEB_COMMIT},
    }
    return data, heatmaps, unmatched


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
                    encoding="utf-8")
    return path.stat().st_size


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--earth", default=str(ROOT / "data/earth_all.csv.gz"))
    parser.add_argument("--targets", default=str(ROOT / "data/targets.csv"))
    parser.add_argument("--regions", default=str(ROOT / "data/regions_catalog.csv"))
    parser.add_argument("--sites-ts", default=str(ROOT / "web/src/data/sites.ts"))
    parser.add_argument("--features", default=str(ROOT / "data/features"))
    parser.add_argument("--out-dir", default=str(ROOT / "web/public/data"))
    parser.add_argument("--stability-runs", type=int, default=100)
    args = parser.parse_args(argv)

    if args.stability_runs < 1:
        parser.error("--stability-runs must be positive")
    global STABILITY_RUNS
    STABILITY_RUNS = args.stability_runs
    data, heatmaps, unmatched = build(args.earth, args.targets, args.regions, args.sites_ts, args.features)
    out = Path(args.out_dir)
    science = build_science(args.features, Path(args.features).parent / "results", Path(args.features).parent / "processed", out / "science", pd.read_csv(args.targets))
    studies = {s["site_id"]: s for s in science["studies"] if s.get("site_id")}
    for site in data["sites"]:
        if site["id"] in studies:
            study = studies[site["id"]]
            site["science_ref"] = {"id": study["id"], "url": study["url"], "name": study["name"]}
    for target in data["targets"]:
        target["science_refs"] = science["target_associations"].get(target["name"], [])
    data["science_index_url"] = "/data/science/index.json"
    data["global_rankings_url"] = "/data/global-rankings.json"
    top_path = Path(args.earth).parent / "top200_analogos.csv"
    if top_path.exists():
        top = pd.read_csv(top_path)
        top["site_id"] = [cell_id(a, o) for a, o in zip(top["earth_lat"], top["earth_lon"])]
        top["target_id"] = top["best_site"].map(target_id)
        write_json(out / "global-rankings.json", {
            "version": "1.0.0", "n_cells": data["n_cells"], "n_regions": data["n_regions"],
            "source_commit": GLOBAL_COMMIT, "source_sha256": hashlib.sha256(top_path.read_bytes()).hexdigest(),
            "model": {"id": "marco-global-full-environment", "weights": {**compare.DEFAULT_WEIGHTS, "elev_m": 0, "em_contrast": .5}, "excluded_moon_average": ["Shackleton floor (shadow)"], "separation_km": 300, "note": "Original global full-environment scores; different from the web comparable-dimensions score and from PAI"},
            "rows": json.loads(top.to_json(orient="records", double_precision=15)),
        })
    validate_comparison_contract(data)
    size = write_json(out / "comparisons.json", data)
    heat_dir = out / "heatmap"
    for old in heat_dir.glob("*.json") if heat_dir.exists() else []:
        old.unlink()
    heat_size = sum(write_json(heat_dir / f"{tid}.json", {"target": tid, "cells": cells})
                    for tid, cells in heatmaps.items())

    kinds = pd.Series([s["kind"] for s in data["sites"]]).value_counts().to_dict()
    print(f"Wrote {out / 'comparisons.json'} ({size / 1024:.0f} KB): {len(data['targets'])} targets, "
          f"sites {kinds}, synthetic={data['synthetic']}")
    print(f"Wrote {len(heatmaps)} heatmap files ({heat_size / 1024:.0f} KB in total)")
    for body, excluded in sorted({(t["body"], tuple(t["excluded"])) for t in data["targets"]}):
        if excluded:
            print(f"  {body}: switched off (outside Earth's range): {', '.join(excluded)}")
    if unmatched:
        print(f"Catalog sites outside the Earth grid (no data yet): {', '.join(unmatched)}")


if __name__ == "__main__":
    main()
