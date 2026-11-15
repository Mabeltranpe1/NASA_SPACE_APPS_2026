"""
analog_api.py - Read-only API of the Earth-analog comparator (for researchers and for the web app).

Same maths as src/compare.py (it calls compare.py; nothing is re-implemented here), with the
official settings of the project: tolerance scaling, compare.py weights except elev_m = 0 and
em_contrast = 0.5 (the same as src/make_results.py), and every Earth cell must have all the
variables the site uses (min_coverage = 1).

Three operations:
    find_analogs   a Moon/Mars site (or your own values) -> best Earth places, score,
                   similarity per variable, best/worst match
    query_point    an Earth lat/lon -> which Moon/Mars sites it resembles and where it fails
    to_geojson / to_kml / to_waypoints   export any result (QGIS, Google Earth, Mission Planner)

Use it from Python:
    import sys; sys.path.insert(0, "src")
    import analog_api as api
    res = api.find_analogs(site="Jezero crater", top=10)
    res = api.find_analogs(body="Mars", values={"temp_mean_K": 215, "albedo": 0.15, ...})
    res = api.query_point(24.5, 26.0)
    open("jezero.geojson", "w").write(api.to_geojson(res))

Or from the command line:
    python src/analog_api.py sites
    python src/analog_api.py find --site "Jezero crater" --top 10 --format geojson > jezero.geojson
    python src/analog_api.py find --body Mars --value temp_mean_K=215 --value albedo=0.15
    python src/analog_api.py point --lat 24.5 --lon 26.0
    python src/analog_api.py serve --port 8000          # local HTTP API, see docs/API.md
    python src/analog_api.py export-static              # static API files for the web site
    python src/analog_api.py export-web                 # compact Earth database for the browser

Only pandas and numpy are needed (no scikit-learn).
"""

import argparse
import gzip
import json
import math
import re
import sys
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import compare  # noqa: E402
import export_web as web_rules  # noqa: E402  (same rules and ids as the web app)
from region_names import region_names  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EARTH_PATH = ROOT / "data" / "earth_all.csv.gz"
TARGETS_PATH = ROOT / "data" / "targets.csv"
CATALOG_PATH = ROOT / "data" / "regions_catalog.csv"
API_VERSION = "v1"

# Weights and rules: the same as the web app (src/export_web.py), so the API,
# the "Find analogs" section and every other page give the SAME score:
#   - make_results.py WEIGHTS on top of compare.DEFAULT_WEIGHTS (no elevation, rock type 0.5);
#   - a variable is switched off for a body when Earth cannot reach the typical
#     value of its sites (e.g. the Moon at 125 K). It is reported apart, in
#     out_of_earth_range, instead of deciding the score.
BODIES = ("Moon", "Mars")

LABELS = {
    "elev_m": ("Elevation", "m"), "slope_deg": ("Slope", "deg"), "roughness": ("Roughness", "m"),
    "temp_mean_K": ("Mean temperature", "K"), "temp_range_K": ("Temperature range", "K"),
    "albedo": ("Albedo", ""), "precip_mm": ("Precipitation", "mm/yr"), "ndvi": ("Vegetation (NDVI)", ""),
    "em_contrast": ("Rock type (emissivity contrast)", ""),
}


# ---------------------------------------------------------------------------
# Data (loaded once, cached)
# ---------------------------------------------------------------------------

def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")


@lru_cache(maxsize=1)
def earth():
    """All Earth cells (about 690 thousand) with region, known flag and the variables."""
    table = compare.load_table(EARTH_PATH, ["lat", "lon"])
    if "known" not in table.columns:
        table["known"] = "no"
    if "region" not in table.columns:
        table["region"] = ""
    return table


@lru_cache(maxsize=1)
def earth_scaled():
    """Earth cells on the compare.py scale (tolerance). Rows match earth()."""
    tol = np.array([compare.TOLERANCE[f] for f in compare.FEATURES])
    return compare.to_matrix(earth()) / tol


@lru_cache(maxsize=1)
def earth_ranges():
    """Smallest and largest value of each variable on Earth (to say when a site is out of reach)."""
    e = earth()
    return {f: (float(e[f].min()), float(e[f].max())) for f in compare.FEATURES if e[f].notna().any()}


@lru_cache(maxsize=1)
def sites():
    """The Moon/Mars sites of data/targets.csv, as a list of dicts with an 'id'."""
    t = compare.load_table(TARGETS_PATH, ["name", "body"])
    out = []
    for _, r in t.iterrows():
        out.append(dict(
            id=web_rules.target_id(r["name"]), name=r["name"], body=r["body"],
            lat=_num(r.get("site_lat")), lon=_num(r.get("site_lon")), area=r.get("area"),
            values={f: _num(r[f]) for f in compare.FEATURES},
        ))
    return out


def find_site(key):
    """Find a site by id or name (case does not matter)."""
    k = slug(key)
    for s in sites():
        if k in (slug(s["id"]), slug(s["name"])):
            return s
    starts = [s for s in sites() if slug(s["name"]).startswith(k) or slug(s["id"]).startswith(k)]
    if len(starts) == 1:   # "jezero_crater" -> "jezero_crater_perseverance"
        return starts[0]
    raise ValueError(f"Unknown site '{key}'. Use one of: {[s['id'] for s in sites()]}")


def _num(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


@lru_cache(maxsize=1)
def body_rules():
    """{body: (weights dict, switched-off variables)}, computed exactly like export_web.py."""
    t = compare.load_table(TARGETS_PATH, ["name", "body"])
    return web_rules.body_weights(t, earth())


def weights_for(body, weights=None):
    """The web app's weights for this body, plus the caller's changes."""
    merged = {**body_rules()[body][0], **(weights or {})}
    return compare.build_weights(merged, body)


def settings():
    """Everything a client needs to reproduce the score (also exported for the web app)."""
    return dict(
        api_version=API_VERSION,
        features=compare.FEATURES,
        labels={f: dict(label=LABELS[f][0], unit=LABELS[f][1]) for f in compare.FEATURES},
        tolerance=compare.TOLERANCE,
        log_features=compare.LOG_FEATURES,
        weights={b: dict(zip(compare.FEATURES, weights_for(b).tolist())) for b in BODIES},
        switched_off={b: body_rules()[b][1] for b in BODIES},
        min_coverage=1.0,
        earth_range={f: list(v) for f, v in earth_ranges().items()},
        score="score = exp(-sqrt(sum(w_f * d_f^2) / sum(w_f))), d_f = (target_f - earth_f) / tolerance_f "
              "(log1p first for log_features); similarity_f = exp(-|d_f|). A variable the target does not "
              "have (empty) gets weight 0. Same as src/compare.py score_cells.",
    )


# ---------------------------------------------------------------------------
# 1. Find Earth analogs of a site
# ---------------------------------------------------------------------------

def _target_row(values):
    row = pd.DataFrame([{f: values.get(f) for f in compare.FEATURES}])
    for f in compare.FEATURES:
        row[f] = pd.to_numeric(row[f], errors="raise")
    return row


def _haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def out_of_reach(values, used=None):
    """Compared variables where the site lies outside everything Earth has (e.g. 125 K on the Moon).
    The score is NOT changed by this: it only explains a low similarity that no place can fix."""
    out = []
    for f, (lo, hi) in earth_ranges().items():
        if used is not None and f not in used:
            continue
        v = values.get(f)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            continue
        if v < lo or v > hi:
            out.append(dict(feature=f, value=v, earth_min=lo, earth_max=hi, closest_on_earth=lo if v < lo else hi))
    return out


DEFAULT_MIN_KM = 300   # neighbouring 2x2-degree regions would otherwise fill the list (top200 uses 300 too)


def find_analogs(site=None, values=None, body=None, top=10, per_region=True, min_km=DEFAULT_MIN_KM,
                 include_known=False, weights=None):
    """
    Best Earth places for one Moon/Mars site or for your own values.

    site          id or name from data/targets.csv (its values are used)
    values        dict {variable: value}; with a site, these replace the site's values
    body          "Moon" or "Mars" (needed without a site; picks the weights)
    top           how many places to return
    per_region    True = only the best place of each Earth region (more variety)
    min_km        places at least this far apart (default 300; 0 = no rule; make_results.py uses 800 for its top 5)
    include_known True = also famous analog regions (known = yes); False like make_results.py
    weights       dict to change weights, e.g. {"precip_mm": 0}
    """
    base = find_site(site) if site else None
    vals = dict(base["values"]) if base else {}
    vals.update({k: (None if v is None else float(v)) for k, v in (values or {}).items()})
    unknown = [k for k in vals if k not in compare.FEATURES]
    if unknown:
        raise ValueError(f"Unknown variable(s) {unknown}. Choose from {compare.FEATURES}")
    body = body or (base["body"] if base else None)
    if body not in BODIES:
        raise ValueError("Give a site or body = 'Moon' or 'Mars'.")

    tol = np.array([compare.TOLERANCE[f] for f in compare.FEATURES])
    target_scaled = compare.to_matrix(_target_row(vals))[0] / tol
    w = weights_for(body, weights)
    score, sims = compare.score_cells(earth_scaled(), target_scaled, w)

    e = earth()
    usable = ~np.isnan(score)
    if not include_known:
        usable &= (e["known"] != "yes").to_numpy()
    order = np.flatnonzero(usable)
    order = order[np.argsort(-score[order], kind="stable")]

    picked, seen = [], set()
    lat, lon, region = e["lat"].to_numpy(), e["lon"].to_numpy(), e["region"].to_numpy()
    for i in order:
        if per_region and region[i] in seen:
            continue
        if min_km > 0 and picked and _haversine_km(lat[i], lon[i], lat[picked], lon[picked]).min() < min_km:
            continue
        picked.append(i)
        seen.add(region[i])
        if len(picked) == top:
            break

    picked = np.array(picked, dtype=int)
    best, worst = compare.best_and_worst(sims[picked]) if len(picked) else ([], [])
    used = [f for j, f in enumerate(compare.FEATURES) if w[j] > 0 and not np.isnan(target_scaled[j])]
    results = []
    for k, i in enumerate(picked):
        results.append(dict(
            rank=k + 1, region=region[i], known=e["known"].iat[i] == "yes",
            lat=float(lat[i]), lon=float(lon[i]), score=round(float(score[i]), 6),
            similarity={f: round(float(sims[i, j]), 6) for j, f in enumerate(compare.FEATURES) if f in used},
            earth_values={f: _num(e[f].iat[i]) for f in compare.FEATURES},
            best_match=str(best[k]), worst_match=str(worst[k]),
        ))
    return dict(
        kind="analogs", api_version=API_VERSION,
        query=dict(site=base["id"] if base else None, site_name=base["name"] if base else None, body=body,
                   site_lat=base["lat"] if base else None, site_lon=base["lon"] if base else None,
                   values=vals, top=top, per_region=per_region, min_km=min_km, include_known=include_known,
                   weights=dict(zip(compare.FEATURES, w.tolist()))),
        variables_used=used,
        switched_off=body_rules()[body][1],
        out_of_earth_range=out_of_reach(vals, used + body_rules()[body][1]),
        n_candidates=int(usable.sum()),
        results=results,
    )


# ---------------------------------------------------------------------------
# 2. What does an Earth point resemble?
# ---------------------------------------------------------------------------

def query_point(lat, lon, max_km=25.0, weights=None):
    """
    Nearest Earth cell of the database to (lat, lon), compared with every Moon/Mars site.
    The database covers dry regions only; farther than max_km from any cell -> error.
    """
    e = earth()
    dist = _haversine_km(lat, lon, e["lat"].to_numpy(), e["lon"].to_numpy())
    i = int(np.argmin(dist))
    if dist[i] > max_km:
        raise ValueError(f"No Earth cell within {max_km:g} km of ({lat}, {lon}); nearest is "
                         f"{dist[i]:.0f} km away at ({e['lat'].iat[i]}, {e['lon'].iat[i]}), region {e['region'].iat[i]}.")
    cell = earth_scaled()[i:i + 1]
    tol = np.array([compare.TOLERANCE[f] for f in compare.FEATURES])
    rows = []
    for s in sites():
        w = weights_for(s["body"], weights)
        target_scaled = compare.to_matrix(_target_row(s["values"]))[0] / tol
        score, sims = compare.score_cells(cell, target_scaled, w)
        best, worst = compare.best_and_worst(sims)
        rows.append(dict(
            site=s["id"], site_name=s["name"], body=s["body"], site_lat=s["lat"], site_lon=s["lon"],
            score=None if np.isnan(score[0]) else round(float(score[0]), 6),
            similarity={f: round(float(sims[0, j]), 6) for j, f in enumerate(compare.FEATURES) if not np.isnan(sims[0, j])},
            best_match=str(best[0]) or None, worst_match=str(worst[0]) or None,
        ))
    rows.sort(key=lambda r: -1 if r["score"] is None else -r["score"])
    for k, r in enumerate(rows):
        r["rank"] = k + 1
    return dict(
        kind="point", api_version=API_VERSION,
        query=dict(lat=lat, lon=lon),
        cell=dict(lat=float(e["lat"].iat[i]), lon=float(e["lon"].iat[i]), distance_km=round(float(dist[i]), 2),
                  region=e["region"].iat[i], known=e["known"].iat[i] == "yes",
                  values={f: _num(e[f].iat[i]) for f in compare.FEATURES}),
        results=rows,
    )


# ---------------------------------------------------------------------------
# 3. Export: GeoJSON, KML, Mission Planner waypoints
# ---------------------------------------------------------------------------

def _features_of(result):
    """(name, lat, lon, properties) for every place of a result."""
    out = []
    if result["kind"] == "analogs":
        q = result["query"]
        for r in result["results"]:
            title = f"#{r['rank']} {r['region']} (score {r['score']:.3f})"
            props = dict(rank=r["rank"], region=r["region"], known=r["known"], score=r["score"],
                         best_match=r["best_match"], worst_match=r["worst_match"],
                         analog_of=q["site_name"] or f"custom {q['body']} values", body=q["body"])
            props.update({f"sim_{k}": v for k, v in r["similarity"].items()})
            props.update({f"earth_{k}": v for k, v in r["earth_values"].items()})
            out.append((title, r["lat"], r["lon"], props))
    else:
        c = result["cell"]
        best = result["results"][0]
        props = dict(region=c["region"], known=c["known"], distance_km=c["distance_km"],
                     most_similar_site=best["site_name"], score=best["score"])
        props.update({f"score_{r['site']}": r["score"] for r in result["results"]})
        out.append((f"{c['region']} ~ {best['site_name']} ({best['score']:.3f})", c["lat"], c["lon"], props))
    return out


def to_geojson(result):
    """GeoJSON FeatureCollection (opens directly in QGIS, geojson.io, Google Earth Pro, ArcGIS)."""
    feats = [dict(type="Feature", geometry=dict(type="Point", coordinates=[lon, lat]),
                  properties=dict(name=name, **props))
             for name, lat, lon, props in _features_of(result)]
    meta = {k: v for k, v in result.items() if k not in ("results", "cell")}
    return json.dumps(dict(type="FeatureCollection", metadata=meta, features=feats), ensure_ascii=False)


def to_kml(result):
    """KML placemarks (Google Earth, Mission Planner map, most GIS tools)."""
    q = result["query"]
    title = (f"Earth analogs of {q.get('site_name') or 'custom values'}" if result["kind"] == "analogs"
             else f"Earth point {q['lat']}, {q['lon']}")
    marks = []
    for name, lat, lon, props in _features_of(result):
        rows = "".join(f"<tr><td>{escape(str(k))}</td><td>{escape(str(v))}</td></tr>" for k, v in props.items())
        marks.append(f"<Placemark><name>{escape(name)}</name><description><![CDATA[<table>{rows}</table>]]>"
                     f"</description><Point><coordinates>{lon},{lat},0</coordinates></Point></Placemark>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
            f"<name>{escape(title)}</name>" + "".join(marks) + "</Document></kml>\n")


def to_waypoints(result, altitude_m=100):
    """QGC WPL 110 waypoint file (Mission Planner / QGroundControl): one waypoint per place."""
    lines = ["QGC WPL 110"]
    for k, (_, lat, lon, _) in enumerate(_features_of(result)):
        # index, current, frame (3 = relative alt), command 16 = NAV_WAYPOINT, 4 params, lat, lon, alt, autocontinue
        lines.append(f"{k}\t{1 if k == 0 else 0}\t3\t16\t0\t0\t0\t0\t{lat:.6f}\t{lon:.6f}\t{altitude_m}\t1")
    return "\n".join(lines) + "\n"


FORMATS = {"json": (lambda r: json.dumps(r, ensure_ascii=False), "application/json"),
           "geojson": (to_geojson, "application/geo+json"),
           "kml": (to_kml, "application/vnd.google-earth.kml+xml"),
           "waypoints": (to_waypoints, "text/plain")}


# ---------------------------------------------------------------------------
# Local HTTP server (read-only, GET only)
# ---------------------------------------------------------------------------

def _parse_values(params):
    return {f: float(params[f][0]) for f in compare.FEATURES if f in params and params[f][0] != ""}


def _parse_weights(params):
    return {f[2:]: float(v[0]) for f, v in params.items() if f.startswith("w_") and f[2:] in compare.FEATURES}


def handle(path, params):
    """Route a GET request. Returns (status, body text, content type). Also used by the tests."""
    one = lambda k, d=None: params.get(k, [d])[0]  # noqa: E731
    flag = lambda k, d: one(k, str(d)).lower() in ("1", "true", "yes")  # noqa: E731
    fmt = one("format", "json")
    if fmt not in FORMATS:
        return 400, json.dumps(dict(error=f"format must be one of {list(FORMATS)}")), "application/json"
    path = path.rstrip("/")
    prefix = f"/api/{API_VERSION}"
    try:
        if path in (prefix, f"{prefix}/settings"):
            return 200, json.dumps(settings()), "application/json"
        if path == f"{prefix}/sites":
            return 200, json.dumps(dict(sites=sites())), "application/json"
        if path == f"{prefix}/analogs":
            result = find_analogs(site=one("site"), values=_parse_values(params), body=one("body"),
                                  top=min(int(one("top", 10)), 500), per_region=flag("per_region", True),
                                  min_km=float(one("min_km", DEFAULT_MIN_KM)), include_known=flag("include_known", False),
                                  weights=_parse_weights(params))
        elif path == f"{prefix}/point":
            result = query_point(float(one("lat")), float(one("lon")), max_km=float(one("max_km", 25)),
                                 weights=_parse_weights(params))
        else:
            return 404, json.dumps(dict(error="not found", routes=[f"{prefix}/sites", f"{prefix}/settings",
                                                                     f"{prefix}/analogs", f"{prefix}/point"])), "application/json"
    except (ValueError, TypeError) as err:
        return 400, json.dumps(dict(error=str(err))), "application/json"
    writer, ctype = FORMATS[fmt]
    return 200, writer(result), ctype


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        url = urlparse(self.path)
        status, body, ctype = handle(url.path, parse_qs(url.query))
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve(host="127.0.0.1", port=8000):
    earth_scaled()  # load the data before the first request
    print(f"Analog API on http://{host}:{port}/api/{API_VERSION}/sites  (Ctrl+C to stop)")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


# ---------------------------------------------------------------------------
# Static API for the web site (same answers as the server, for the listed sites)
# ---------------------------------------------------------------------------

def export_static(out_dir=ROOT / "web" / "public" / "data" / "api" / API_VERSION, top=20):
    """
    Write the answers for every site as plain files, so the static web site works as an API:
        sites.json, settings.json
        analogs/<site>.json | .geojson | .kml | .waypoints
    (served at https://<site>/data/api/v1/...; /api/ itself is reserved by Azure Static Web Apps.)
    """
    out = Path(out_dir)
    (out / "analogs").mkdir(parents=True, exist_ok=True)
    (out / "sites.json").write_text(json.dumps(dict(sites=sites()), ensure_ascii=False, indent=1))
    (out / "settings.json").write_text(json.dumps(settings(), indent=1))
    for s in sites():
        result = find_analogs(site=s["id"], top=top)
        for fmt, (writer, _) in FORMATS.items():
            ext = "json" if fmt == "json" else fmt
            (out / "analogs" / f"{s['id']}.{ext}").write_text(writer(result), encoding="utf-8")
    print(f"Static API: {len(sites())} sites x {len(FORMATS)} formats in {out}")


# ---------------------------------------------------------------------------
# Compact Earth database for the browser (web/src/comparator/compare.ts)
# ---------------------------------------------------------------------------

# Stored as int16 (precip_mm is stored as log1p(mm), already on the compare scale).
# (scale, offset): stored = round((value - offset) * scale). Chosen to keep the source precision.
WEB_SCALES = {"slope_deg": (100, 0), "roughness": (100, 0), "temp_mean_K": (100, 200), "temp_range_K": (100, 0),
              "albedo": (10000, 0), "precip_mm": (3000, 0), "ndvi": (10000, 0), "em_contrast": (10000, 0)}
WEB_MISSING = -32768


def export_web(out_dir=ROOT / "web" / "public" / "data" / "comparator"):
    """
    comparator.json : settings, sites, regions, column layout
    earth.bin       : gzip of the columns (little endian): lat*40 int16, lon*40 int16, region uint16,
                      then one int16 column per variable in WEB_SCALES, value = stored / scale + offset (missing = -32768).
    elev_m is left out (official weight 0). Rounding changes scores by less than 0.0005.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    e = earth().sort_values(["region", "lat", "lon"], kind="stable").reset_index(drop=True)
    regions = list(pd.unique(e["region"]))
    known = e.groupby("region")["known"].first().eq("yes")
    catalog = pd.read_csv(CATALOG_PATH, comment="#") if CATALOG_PATH.exists() else None

    cols = [np.round(e["lat"] * 40).astype("<i2"), np.round(e["lon"] * 40).astype("<i2"),
            e["region"].map({r: i for i, r in enumerate(regions)}).astype("<u2")]
    layout = [dict(name="lat", dtype="int16", scale=40), dict(name="lon", dtype="int16", scale=40),
              dict(name="region", dtype="uint16", scale=1)]
    for f, (s, off) in WEB_SCALES.items():
        v = np.log1p(e[f]) if f == "precip_mm" else e[f]
        v = np.round((v - off) * s)
        if v.max() > 32767 or v.min() <= WEB_MISSING:
            raise ValueError(f"{f} does not fit in int16 with scale {s} and offset {off}")
        cols.append(v.fillna(WEB_MISSING).astype("<i2"))
        layout.append(dict(name=f, dtype="int16", scale=s, offset=off, log1p=f == "precip_mm"))
    raw = b"".join(np.ascontiguousarray(c.to_numpy()).tobytes() for c in cols)
    (out / "earth.bin").write_bytes(gzip.compress(raw, 9, mtime=0))

    def region_info(r):
        names = region_names(r)
        info = dict(name=r, known=bool(known[r]), label=names["name"], country=names["country"], grid=names["grid"])
        if catalog is not None and "name" in catalog.columns:
            row = catalog[catalog["name"] == r]
            if len(row) and "why" in catalog.columns and pd.notna(row["why"].iat[0]):
                info["description"] = str(row["why"].iat[0])
        return info

    meta = dict(settings(), n_cells=len(e), columns=layout, missing=WEB_MISSING,
                regions=[region_info(r) for r in regions], sites=sites(),
                source="data/earth_all.csv.gz via src/analog_api.py export-web")
    (out / "comparator.json").write_text(json.dumps(meta, ensure_ascii=False))
    size = (out / "earth.bin").stat().st_size / 1e6
    print(f"Web database: {len(e):,} cells, {len(regions)} regions, earth.bin {size:.1f} MB in {out}")


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description="Read-only API of the Earth-analog comparator.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sites", help="List the Moon/Mars sites")
    f = sub.add_parser("find", help="Best Earth analogs of a site or of your own values")
    f.add_argument("--site")
    f.add_argument("--body", choices=BODIES)
    f.add_argument("--value", action="append", default=[], metavar="VAR=NUMBER")
    f.add_argument("--weight", action="append", default=[], metavar="VAR=NUMBER")
    f.add_argument("--top", type=int, default=10)
    f.add_argument("--all-cells", action="store_true", help="Do not limit to one place per region")
    f.add_argument("--min-km", type=float, default=DEFAULT_MIN_KM)
    f.add_argument("--include-known", action="store_true")
    f.add_argument("--format", choices=list(FORMATS), default="json")
    q = sub.add_parser("point", help="What does an Earth place resemble?")
    q.add_argument("--lat", type=float, required=True)
    q.add_argument("--lon", type=float, required=True)
    q.add_argument("--max-km", type=float, default=25)
    q.add_argument("--format", choices=list(FORMATS), default="json")
    s = sub.add_parser("serve", help="Local HTTP API")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8000)
    sub.add_parser("export-static", help="Static API files in web/public/data/api/v1")
    sub.add_parser("export-web", help="Compact Earth database in web/public/data/comparator")
    a = p.parse_args(argv)

    try:
        if a.cmd == "sites":
            for site in sites():
                print(f"{site['id']:32s} {site['body']:5s} {site['name']}")
        elif a.cmd == "find":
            res = find_analogs(site=a.site, body=a.body, values=compare.parse_weights(a.value),
                               weights=compare.parse_weights(a.weight), top=a.top, per_region=not a.all_cells,
                               min_km=a.min_km, include_known=a.include_known)
            print(FORMATS[a.format][0](res))
        elif a.cmd == "point":
            print(FORMATS[a.format][0](query_point(a.lat, a.lon, a.max_km)))
        elif a.cmd == "serve":
            serve(a.host, a.port)
        elif a.cmd == "export-static":
            export_static()
        elif a.cmd == "export-web":
            export_web()
    except (ValueError, OSError) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
