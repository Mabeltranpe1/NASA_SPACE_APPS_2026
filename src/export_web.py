"""
export_web.py - Turn the comparison results into the JSON files the web app reads.

It does NOT change how similarity is computed: it calls compare.py (Marco's
comparator, with the weights of make_results.py) and only decides WHAT goes to
the web and in which format. Data contract: docs/DATOS_WEB.md.

Inputs (defaults):
    data/earth_all.csv.gz     Earth grid, one row per 0.05 deg cell, 727 regions (Marco)
    data/targets.csv          Moon and Mars sites, with rock composition (Marco)
    data/regions_catalog.csv  description of each Earth region (Marco)
    web/src/data/sites.ts     catalog sites shown in the app (their lat/lng)
    data/features/*.csv       detailed characterization of the Colombian
                              sites at 200 m (Santiago, descriptive only)

Outputs (web/public/data/):
    comparisons.json          catalog sites + best little-known places
                              ("discoveries"), with every target's result,
                              the score of each DIMENSION and the ranked lists
    heatmap/<target>.json     the best Earth cells for one target (map layer)

One scoring for everything (catalog, Colombia and discoveries). Rules
(explained in docs/DATOS_WEB.md):
    1. Elevation is never compared: each body measures height from a
       different zero level (sea level, areoid, reference sphere).
    2. A feature is switched off for a body (Moon or Mars) when the typical
       value of its sites is outside the range found on Earth by more than
       one tolerance (e.g. the Moon at 125 K). Earth cannot reproduce it, so
       the app shows it as a limit of the analogy instead of letting it
       decide the score.
    3. Discoveries: best cell of each little-known region, then places at
       least SPREAD_KM apart (Marco's rule in make_top_analogos.py), so one
       very good area cannot fill the whole list.
    4. Besides the overall score, every result has one score per DIMENSION
       (relief, temperature, surface, aridity), computed with the same
       formula on that dimension's features only.

Example:
    python src/export_web.py
"""

import argparse
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
from make_results import LEAVE_OUT_OF_OVERALL, WEIGHTS, spread_out  # noqa: E402
from region_names import region_names  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# 1. Settings
# ---------------------------------------------------------------------------

# Weights: the same as Marco's results (make_results.WEIGHTS): no elevation,
# rock composition at half weight (it is a calibrated estimate on the Moon/Mars).
WEB_WEIGHTS = dict(WEIGHTS)

# A target value further than this many tolerances outside Earth's range
# switches that feature off for that body (rule 2).
OUT_OF_RANGE_TOLERANCES = 1.0

# Dimensions shown in the app (rule 4). Every compared feature is in one.
DIMENSIONS = {
    "relieve": ["slope_deg", "roughness"],
    "temperatura": ["temp_mean_K", "temp_range_K"],
    "superficie": ["albedo", "em_contrast"],
    "aridez": ["precip_mm", "ndvi"],
}
DIMENSION_LABELS = {
    "relieve": {"es": "Relieve", "en": "Relief"},
    "temperatura": {"es": "Temperatura", "en": "Temperature"},
    "superficie": {"es": "Superficie y roca", "en": "Surface and rock"},
    "aridez": {"es": "Aridez", "en": "Aridity"},
}

TOP_GENERAL = 100               # best places per body (overall score)
TOP_PER_DIMENSION = 25          # best places per body and dimension
SPREAD_KM = 300                 # minimum distance between listed places
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
    "elev_m": {"label": "Elevación", "unit": "m", "dimension": "relieve", "range": [-6000, 6000],
               "source_earth": EARTH_DEM,
               "source_target": {"luna": "LRO LOLA", "marte": "HRSC + MOLA, 200 m"}},
    "slope_deg": {"label": "Pendiente", "unit": "°", "dimension": "relieve", "range": [0, 30],
                  "source_earth": EARTH_DEM,
                  "source_target": {"luna": "LRO LOLA, a 200 m", "marte": "HRSC + MOLA, 200 m"}},
    "roughness": {"label": "Rugosidad", "unit": "m", "dimension": "relieve", "range": [0, 40],
                  "source_earth": EARTH_DEM,
                  "source_target": {"luna": "LRO LOLA, a 200 m", "marte": "HRSC + MOLA, 200 m"}},
    "temp_mean_K": {"label": "Temperatura media", "unit": "K", "dimension": "temperatura", "range": [0, 350],
                    "source_earth": "MODIS MOD11C3 (LST)",
                    "source_target": {"luna": "LRO Diviner", "marte": "Mars Climate Database v6.2 (modelo)"}},
    "temp_range_K": {"label": "Amplitud térmica", "unit": "K", "dimension": "temperatura", "range": [0, 160],
                     "source_earth": "MODIS MOD11C3 (LST)",
                     "source_target": {"luna": "LRO Diviner", "marte": "Mars Climate Database v6.2 (modelo)"}},
    "albedo": {"label": "Albedo", "unit": "", "dimension": "superficie", "range": [0, 1],
               "source_earth": "MODIS MCD43C3",
               "source_target": {"luna": "LRO LOLA (albedo normal)", "marte": "MGS TES"}},
    "precip_mm": {"label": "Precipitación anual", "unit": "mm", "dimension": "aridez", "range": [0, 3000],
                  "source_earth": "GPM IMERG",
                  "source_target": {"luna": "0 (no llueve)", "marte": "0 (no llueve)"}},
    "ndvi": {"label": "Vegetación (NDVI)", "unit": "", "dimension": "aridez", "range": [-0.2, 1],
             "source_earth": "MODIS MOD13C2",
             "source_target": {"luna": "0 (sin plantas)", "marte": "0 (sin plantas)"}},
    "em_contrast": {"label": "Tipo de roca (emisividad)", "unit": "", "dimension": "superficie", "range": [-0.1, 0.3],
                    "source_earth": "ASTER GED",
                    "source_target": {"luna": "LRO Diviner (estimación calibrada, ±0,03)",
                                      "marte": "MGS TES (estimación calibrada, ±0,03)"}},
}


# ---------------------------------------------------------------------------
# 2. Small helpers
# ---------------------------------------------------------------------------

def num(value, digits=4):
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


def dimension_scores(sims, weights):
    """
    Score of each dimension for every cell, from the per-feature similarities:
    the same formula as compare.score_cells, s = exp(-|d|) so d = -ln(s),
    restricted to the dimension's features. NaN when the dimension has no
    usable feature (e.g. temperature on the Moon, rule 2).
    Returns {dimension: array}.
    """
    w = compare.build_weights(weights)
    out = {}
    with np.errstate(divide="ignore", invalid="ignore"):
        d2 = np.log(sims) ** 2
    for dim, feats in DIMENSIONS.items():
        cols = [compare.FEATURES.index(f) for f in feats]
        cw = np.where(np.isnan(sims[:, cols]), 0.0, w[cols])
        wsum = cw.sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            dist = np.sqrt((cw * np.nan_to_num(d2[:, cols])).sum(axis=1) / wsum)
        out[dim] = np.where(wsum > 0, np.exp(-dist), np.nan).astype(np.float32)
    return out


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
    inside = np.zeros(len(cells))
    for _ in range(STABILITY_RUNS):
        factors = rng.uniform(1 - STABILITY_SPREAD, 1 + STABILITY_SPREAD, size=len(base))
        score, _ = compare.score_cells(earth_scaled, target_scaled, base * factors)
        rank = global_rank(score)
        inside += rank[cells] <= STABILITY_TOP
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
            info["mineralogy"] = {"status": "pendiente", "emit_granules": int(m["emit_granules"])}
        if region == "La_Guajira":
            info["quality_flags"] = ["ventana costera: puede incluir mar (provisional)"]
        out[site_id] = info
    return out


# ---------------------------------------------------------------------------
# 6. Build everything
# ---------------------------------------------------------------------------

def is_synthetic(path):
    opener = __import__("gzip").open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        return "SYNTHETIC" in f.readline().upper()


def ranked_places(earth, region_col, pool, score, best_target, n, tiebreak=None):
    """
    Best cell of each region in `pool` by `score`, then places at least
    SPREAD_KM apart (rule 3). Returns [(cell index, target position, score)].
    A dimension with only two features often reaches 1.00 in many places:
    those ties are ordered by `tiebreak` (the overall score), so the places on
    top also look alike in everything else.
    """
    ok = pool & np.isfinite(score)
    idx = np.flatnonzero(ok)
    table = pd.DataFrame({"i": idx, "region": region_col[ok], "score": score[ok],
                          "key": np.round(score[ok], 3),
                          "tie": np.nan_to_num(tiebreak[ok], nan=-1.0) if tiebreak is not None else 0.0})
    table = (table.sort_values(["key", "tie"], ascending=False, kind="stable")
             .drop_duplicates("region"))
    table["lat"] = earth["lat"].to_numpy()[table["i"]]
    table["lon"] = earth["lon"].to_numpy()[table["i"]]
    # spread_out compares each row with the kept ones: only the best few
    # hundred regions can ever be picked, so cut the table first.
    picked = spread_out(table.head(max(n * 6, 200)).reset_index(drop=True), n, SPREAD_KM)
    return [(int(i), int(best_target[i]), float(sc)) for i, sc in zip(picked["i"], picked["score"])]


def build(earth_path, targets_path, regions_path, sites_ts, features_dir, seed=0):
    earth, targets = compare.load_inputs(earth_path, targets_path)
    regions = pd.read_csv(regions_path, comment="#") if Path(regions_path).exists() else None
    region_why = dict(zip(regions["name"], regions["why"])) if regions is not None else {}
    known = (earth["known"] == "yes").to_numpy() if "known" in earth.columns else np.zeros(len(earth), bool)
    region_col = earth["region"].to_numpy() if "region" in earth.columns else np.full(len(earth), "")
    n_cells = len(earth)

    earth_scaled, targets_scaled = compare.scale_together(earth, targets)
    rng = np.random.default_rng(seed)
    per_body = body_weights(targets, earth)

    # ---- Pass 1: score every cell for every target (overall + dimensions).
    per_target = []
    heatmaps = {}
    for pos, (_, t) in enumerate(targets.iterrows()):
        weights, excluded = per_body[t["body"]]
        score, sims = score_target(earth_scaled, targets_scaled[pos], weights)
        dims = dimension_scores(sims, weights)
        del sims
        tid = target_id(t["name"])
        top = np.argsort(-np.nan_to_num(score, nan=-1.0), kind="stable")[:HEATMAP_CELLS]
        heatmaps[tid] = [[num(earth["lat"].iat[i], 3), num(earth["lon"].iat[i], 3), num(score[i], 3)]
                         for i in top]
        per_target.append({"pos": pos, "id": tid, "row": t, "body": str(t["body"]), "weights": weights,
                           "excluded": excluded, "score": score.astype(np.float32), "dims": dims,
                           "rank": global_rank(score)})
        print(f"  scored {tid}")

    # ---- Ranked lists per body: overall and per dimension (rules 3 and 4).
    pool = ~known
    lists = {}
    listed = {}          # cell index -> first list that brought it (for the JSON)
    for body in sorted({tg["body"] for tg in per_target}):
        leave_out = set(LEAVE_OUT_OF_OVERALL.get(body, []))
        group = [tg for tg in per_target if tg["body"] == body and str(tg["row"]["name"]) not in leave_out]
        web_body = BODY_IDS.get(body.lower(), body.lower())

        def best_of(arrays):
            stack = np.vstack([np.nan_to_num(a, nan=-1.0) for a in arrays])
            arg = stack.argmax(axis=0)
            best = stack.max(axis=0)
            return np.where(best < 0, np.nan, best), np.array([group[k]["pos"] for k in range(len(group))])[arg]

        body_lists = {}
        score, who = best_of([tg["score"] for tg in group])
        overall = score
        body_lists["general"] = ranked_places(earth, region_col, pool, score, who, TOP_GENERAL)
        for dim in DIMENSIONS:
            arrays = [tg["dims"][dim] for tg in group]
            if all(np.isnan(a).all() for a in arrays):
                continue           # not comparable for this body (rule 2)
            score, who = best_of(arrays)
            body_lists[dim] = ranked_places(earth, region_col, pool, score, who, TOP_PER_DIMENSION, tiebreak=overall)
        lists[web_body] = body_lists
        for items in body_lists.values():
            for i, _, _ in items:
                listed.setdefault(i, True)

    # ---- Exported sites: catalog sites + every listed place.
    catalog = read_catalog_sites(sites_ts)
    site_cells, site_info, unmatched = {}, {}, []
    for s in catalog:
        i = nearest_cell(earth, s["lat"], s["lng"], CATALOG_MAX_DEG)
        if i is None:
            unmatched.append(s["id"])
            continue
        site_cells[s["id"]] = i
        site_info[s["id"]] = {"kind": "catalog", "name": s["name"]}
    cell_to_site = {}
    for i in listed:
        sid = cell_id(earth["lat"].iat[i], earth["lon"].iat[i])
        cell_to_site[i] = sid
        if sid in site_cells:
            continue
        region = str(region_col[i])
        names = region_names(region)
        site_info[sid] = {
            "kind": "discovery",
            "name": names["name"]["es"],
            "name_en": names["name"]["en"],
            "country": names["country"]["es"],
            "country_en": names["country"]["en"],
            "grid": names["grid"],
            "note": None if names["grid"] else region_why.get(region),
        }
        site_cells[sid] = i

    # ---- Pass 2: full results (similarities, dimensions, rank, stability) of the exported sites.
    ids = list(site_cells)
    cells = np.array([site_cells[sid] for sid in ids])
    results = {sid: [] for sid in ids}
    for tg in per_target:
        _, sims = score_target(earth_scaled[cells], targets_scaled[tg["pos"]], tg["weights"])
        stab = stability(earth_scaled, targets_scaled[tg["pos"]], tg["weights"], cells, rng)
        for k, (sid, i) in enumerate(zip(ids, cells)):
            if not np.isfinite(tg["score"][i]):
                continue
            sim = {f: num(sims[k, j]) for j, f in enumerate(compare.FEATURES)}
            used = {f: v for f, v in sim.items() if v is not None}
            results[sid].append({
                "target": tg["id"],
                "score": num(tg["score"][i]),
                "dims": {d: num(tg["dims"][d][i]) for d in DIMENSIONS},
                "sim": sim,
                "best_match": max(used, key=used.get) if used else None,
                "worst_match": min(used, key=used.get) if used else None,
                "rank": int(tg["rank"][i]),
                "stability": num(stab[k], 3),
            })
        print(f"  results {tg['id']}")

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

    pos_to_id = {tg["pos"]: tg["id"] for tg in per_target}
    rankings = {body: {name: [{"site": cell_to_site[i], "target": pos_to_id[p], "score": num(sc)}
                              for i, p, sc in items]
                       for name, items in body_lists.items()}
                for body, body_lists in lists.items()}

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
        "n_cells": int(n_cells),
        "n_regions": int(len(set(region_col))),
        "stability_runs": STABILITY_RUNS,
        "stability_top": STABILITY_TOP,
        "spread_km": SPREAD_KM,
        "features": [
            {"id": f, **FEATURE_META.get(f, {"label": f, "unit": "", "dimension": "relieve"}),
             "default_weight": float(weights.get(f, 0.0))}
            for f in compare.FEATURES
        ],
        "dimensions": [{"id": d, "features": feats, "label": DIMENSION_LABELS[d]} for d, feats in DIMENSIONS.items()],
        "targets": target_list,
        "sites": sites,
        "rankings": rankings,
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
    args = parser.parse_args(argv)

    data, heatmaps, unmatched = build(args.earth, args.targets, args.regions, args.sites_ts, args.features)
    out = Path(args.out_dir)
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
    for body, body_lists in data["rankings"].items():
        print(f"  {body}: " + ", ".join(f"{k} {len(v)}" for k, v in body_lists.items()))


if __name__ == "__main__":
    main()
