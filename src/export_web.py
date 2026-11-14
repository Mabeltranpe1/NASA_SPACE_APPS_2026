"""
export_web.py - Turn the output of compare.py into the JSON the web app reads.

It does NOT change how the similarity is computed: it calls compare.py's own
functions (compare_all, weight_sensitivity) and writes the result following
the data contract in docs/VISUALIZACION_COMPARACION.md.

Example (with the synthetic sample data):
    python src/export_web.py --earth data/sample_earth.csv \
                             --targets data/sample_targets.csv \
                             --out web/public/data/comparisons.json

How Earth cells are linked to the sites of the web catalog
(web/src/data/sites.ts): through SITE_KEYWORDS below. A cell whose
place_hint contains one of the keywords gets that site id; any other cell
gets an id like "cell_-23.90_-69.10" and still appears in the rankings.
"""

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare  # noqa: E402

# Feature metadata shown in the web app. Keys must match compare.FEATURES.
# "range" is the fixed axis used to draw the real values (Earth vs target).
FEATURE_META = {
    "elev_m": {"label": "Elevación", "unit": "m", "dimension": "terreno", "range": [-6000, 6000],
               "source_earth": "SRTM / Copernicus DEM",
               "source_target": {"luna": "LRO LOLA", "marte": "MGS MOLA"}},
    "slope_deg": {"label": "Pendiente", "unit": "°", "dimension": "terreno", "range": [0, 45],
                  "source_earth": "Derivada del DEM",
                  "source_target": {"luna": "LRO LOLA", "marte": "MGS MOLA"}},
    "roughness": {"label": "Rugosidad", "unit": "", "dimension": "terreno", "range": [0, 1],
                  "source_earth": "Derivada del DEM",
                  "source_target": {"luna": "LRO LOLA", "marte": "MGS MOLA"}},
    "temp_mean_K": {"label": "Temperatura media", "unit": "K", "dimension": "temperatura", "range": [0, 400],
                    "source_earth": "MODIS LST",
                    "source_target": {"luna": "LRO Diviner", "marte": "MO THEMIS / MGS TES"}},
    "temp_range_K": {"label": "Amplitud térmica", "unit": "K", "dimension": "temperatura", "range": [0, 350],
                     "source_earth": "MODIS LST (día − noche)",
                     "source_target": {"luna": "LRO Diviner", "marte": "MO THEMIS / MGS TES"}},
    "albedo": {"label": "Albedo", "unit": "", "dimension": "geologia", "range": [0, 1],
               "source_earth": "MODIS MCD43 albedo",
               "source_target": {"luna": "LRO Diviner / LROC", "marte": "MGS TES"}},
    "precip_mm": {"label": "Precipitación anual", "unit": "mm", "dimension": "agua_hielo", "range": [0, 3000],
                  "source_earth": "GPM IMERG",
                  "source_target": {"luna": "No aplica", "marte": "No aplica"}},
}

BODY_IDS = {"moon": "luna", "luna": "luna", "mars": "marte", "marte": "marte"}

# place_hint keyword -> site id in web/src/data/sites.ts
SITE_KEYWORDS = {
    "atacama": "atacama-yungay",
    "mcmurdo": "mcmurdo-dry-valleys",
    "devon": "haughton-crater",
    "haughton": "haughton-crater",
    "mauna kea": "mauna-kea",
    "death valley": "death-valley",
    "rio tinto": "rio-tinto",
    "tatacoa": "tatacoa",
    "timanfaya": "timanfaya",
    "uyuni": "uyuni",
    "lava beds": "lava-beds",
    "pilbara": "pilbara",
    "svalbard": "svalbard-bockfjorden",
}

# target name keyword -> homologue id in web/src/data/sites.ts
TARGET_KEYWORDS = {
    "shackleton": "shackleton",
    "jezero": "jezero",
    "gale": "gale",
    "phoenix": "phoenix",
    "utopia": "utopia",
    "meridiani": "meridiani",
    "gusev": "gusev",
    "arsia": "arsia",
    "marius": "marius",
    "tranquillitatis": "tranquillitatis",
    "eberswalde": "eberswalde",
    "medusae": "medusae",
    "sirenum": "sirenum",
}


def clean_name(name):
    return re.sub(r"\s*\(fake\)\s*", "", str(name)).strip()


def match_keyword(text, table, default):
    low = str(text).lower()
    for key, value in table.items():
        if key in low:
            return value
    return default


def num(value, digits=4):
    """JSON-safe number: NaN/inf become null."""
    if value is None:
        return None
    value = float(value)
    if math.isnan(value) or math.isinf(value):
        return None
    return round(value, digits)


def is_synthetic(path):
    with open(path, encoding="utf-8") as f:
        return "SYNTHETIC" in f.readline().upper()


def build(earth_path, targets_path, sensitivity_runs=200, top=5):
    earth, targets = compare.load_inputs(earth_path, targets_path)
    results = compare.compare_all(earth, targets)
    stability = compare.weight_sensitivity(earth, targets, top=top, runs=sensitivity_runs)

    target_ids = {}
    target_list = []
    for _, t in targets.iterrows():
        tid = match_keyword(t["name"], TARGET_KEYWORDS, re.sub(r"\W+", "-", clean_name(t["name"]).lower()))
        target_ids[t["name"]] = tid
        target_list.append({
            "id": tid,
            "body": BODY_IDS.get(str(t["body"]).lower(), str(t["body"]).lower()),
            "name": clean_name(t["name"]),
            "values": {f: num(t[f]) for f in compare.FEATURES},
        })

    def cell_id(row):
        hint = row.get("place_hint", "")
        return match_keyword(hint, SITE_KEYWORDS, f"cell_{row['lat']:.2f}_{row['lon']:.2f}")

    share = {}
    for _, r in stability.iterrows():
        share[(r["target"], round(r["lat"], 4), round(r["lon"], 4))] = r["top_share"]

    sites = {}
    for _, row in earth.iterrows():
        sid = cell_id(row)
        sites[sid] = {
            "id": sid,
            "name": clean_name(row.get("place_hint", sid)),
            "lat": num(row["lat"]),
            "lng": num(row["lon"]),
            "values": {f: num(row[f]) for f in compare.FEATURES},
            "results": [],
        }

    for _, r in results.iterrows():
        sid = cell_id(r)
        key = (r["target"], round(r["lat"], 4), round(r["lon"], 4))
        sites[sid]["results"].append({
            "target": target_ids[r["target"]],
            "score": num(r["score"]),
            "sim": {f: num(r[f"sim_{f}"]) for f in compare.FEATURES},
            "best_match": r["best_match"] or None,
            "worst_match": r["worst_match"] or None,
            "rank": int(r["rank"]),
            "stability": num(share.get(key, 0.0)),
        })

    weights = compare.build_weights()
    return {
        "version": "1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "synthetic": is_synthetic(earth_path) or is_synthetic(targets_path),
        "n_cells": int(len(earth)),
        "stability_runs": sensitivity_runs,
        "stability_top": top,
        "features": [
            {"id": f, **FEATURE_META.get(f, {"label": f, "unit": "", "dimension": "terreno"}),
             "default_weight": float(w)}
            for f, w in zip(compare.FEATURES, np.asarray(weights))
        ],
        "targets": target_list,
        "sites": list(sites.values()),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--earth", default="data/sample_earth.csv")
    parser.add_argument("--targets", default="data/sample_targets.csv")
    parser.add_argument("--out", default="web/public/data/comparisons.json")
    parser.add_argument("--sensitivity", type=int, default=200, help="Runs of the weight sensitivity check")
    args = parser.parse_args(argv)

    data = build(args.earth, args.targets, args.sensitivity)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {out} ({len(data['sites'])} sites, {len(data['targets'])} targets, synthetic={data['synthetic']})")


if __name__ == "__main__":
    main()
