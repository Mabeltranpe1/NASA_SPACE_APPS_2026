"""
Checks that the browser comparator (web/src/comparator/compare.ts) gives the same answers as
src/compare.py (through src/analog_api.py).

    python tests/test_web_port.py        (needs node >= 22; run export-web first)

Two checks per case:
  1. Exact port: for every place the browser returns, compare.py on the SAME stored values
     (earth.bin decoded) gives the same score and similarities (difference < 1e-9).
  2. Against the full-precision database: same places in the same order, and scores differ
     by less than 0.001 (earth.bin rounds values to int16; two practically tied places
     may swap, which is listed but not counted as an error).
"""

import gzip
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import analog_api as api  # noqa: E402
import compare  # noqa: E402

DIR = ROOT / "web" / "public" / "data" / "comparator"

CASES = {
    "find": [{"site": s["id"], "top": 10} for s in api.sites()] + [
        {"site": "jezero", "top": 10, "perRegion": False, "minKm": 0},
        {"site": "jezero", "top": 10, "minKm": 0},
        {"site": "shackleton", "top": 5, "includeKnown": True},
        {"site": "gale", "top": 5, "minKm": 800},
        {"site": "gale", "top": 5, "weights": {"precip_mm": 0, "temp_mean_K": 3}},
        {"body": "Mars", "top": 5, "values": {"slope_deg": 2, "roughness": 3, "temp_mean_K": 250, "temp_range_K": 40,
                                             "albedo": 0.25, "precip_mm": 0, "ndvi": 0.02, "em_contrast": 0.0}},
        {"body": "Moon", "top": 5, "values": {"slope_deg": 12, "temp_mean_K": 120, "albedo": 0.35}},
    ],
    "point": [[25.425, 29.425], [82.125, -36.625], [-23.5, -68.0]],
}


def py_find(c):
    return api.find_analogs(site=c.get("site"), values=c.get("values"), body=c.get("body"), top=c.get("top", 10),
                            per_region=c.get("perRegion", True), min_km=c.get("minKm", api.DEFAULT_MIN_KM),
                            include_known=c.get("includeKnown", False), weights=c.get("weights"))


def decode_bin():
    meta = json.loads((DIR / "comparator.json").read_text())
    raw = gzip.decompress((DIR / "earth.bin").read_bytes())
    n = meta["n_cells"]
    cols = {}
    for k, c in enumerate(meta["columns"]):
        a = np.frombuffer(raw, dtype="<i2" if c["dtype"] == "int16" else "<u2", count=n, offset=k * n * 2).astype(float)
        if c["name"] not in ("region",):
            a = np.where(a == meta["missing"], np.nan, a / c["scale"] + c.get("offset", 0))
        cols[c["name"]] = a
    return meta, cols


def main():
    with tempfile.TemporaryDirectory() as tmp:
        case_file = Path(tmp) / "cases.json"
        case_file.write_text(json.dumps(CASES))
        out = subprocess.run(["node", "--experimental-strip-types", "--no-warnings",
                              str(ROOT / "web" / "scripts" / "check-comparator.ts"), str(case_file)],
                             capture_output=True, text=True, check=True)
    js = json.loads(out.stdout)
    meta, cols = decode_bin()
    key = {(round(la * 40), round(lo * 40)): i for i, (la, lo) in enumerate(zip(cols["lat"], cols["lon"]))}
    web_feats = [f for f in compare.FEATURES if f in cols]
    tol = np.array([compare.TOLERANCE[f] for f in web_feats])
    # Stored values on the compare scale (precip is already log1p).
    stored = np.column_stack([cols[f] / compare.TOLERANCE[f] for f in web_feats])

    worst_exact, worst_full, failures, swaps = 0.0, 0.0, [], []
    for c, jr in zip(CASES["find"], js["find"]):
        pr = py_find(c)
        name = c.get("site") or f"custom {c['body']}"
        # 1. exact port on the stored values
        vals = jr["query"]["values"]
        t = np.array([np.log1p(vals[f]) if f in compare.LOG_FEATURES and vals.get(f) is not None
                      else (np.nan if vals.get(f) is None else vals[f]) for f in web_feats]) / tol
        w = np.array([jr["query"]["weights"][f] for f in web_feats])
        rows = [key[(round(r["lat"] * 40), round(r["lon"] * 40))] for r in jr["results"]]
        score, sims = compare.score_cells(stored[rows], t, w)
        for k, r in enumerate(jr["results"]):
            worst_exact = max(worst_exact, abs(score[k] - r["score"]))
            for j, f in enumerate(web_feats):
                if f in r["similarity"]:
                    worst_exact = max(worst_exact, abs(sims[k, j] - r["similarity"][f]))
        # 2. same answer as the full-precision Python API
        # Rounding can swap two places whose scores are practically tied; that is reported, not failed.
        for k, (p, q) in enumerate(zip(pr["results"], jr["results"])):
            diff = abs(p["score"] - q["score"])
            worst_full = max(worst_full, diff)
            if (p["region"], p["lat"], p["lon"]) != (q["region"], q["lat"], q["lon"]):
                swaps.append(f"{name} rank {k + 1}: python {p['region']} {p['score']:.5f} / web {q['region']} {q['score']:.5f}")
        if len(pr["results"]) != len(jr["results"]):
            failures.append(f"{name}: different number of results")
        if pr["variables_used"] != jr["variables_used"] or len(pr["out_of_earth_range"]) != len(jr["out_of_earth_range"]):
            failures.append(f"{name}: variables_used / out_of_earth_range differ")

    for (lat, lon), jr in zip(CASES["point"], js["point"]):
        pr = api.query_point(lat, lon)
        if [r["site"] for r in pr["results"]] != [r["site"] for r in jr["results"]]:
            failures.append(f"point {lat},{lon}: site order differs")
        for p, q in zip(pr["results"], jr["results"]):
            if p["score"] is not None:
                worst_full = max(worst_full, abs(p["score"] - q["score"]))

    print(f"{len(CASES['find'])} searches + {len(CASES['point'])} points; browser search takes "
          f"{js['ms_per_search']:.0f} ms in Node")
    print(f"exact port (same stored values): max difference {worst_exact:.1e}")
    print(f"vs full-precision compare.py:    max score difference {worst_full:.1e}")
    print(f"near-ties swapped by rounding: {len(swaps)} of {sum(len(r['results']) for r in js['find'])} places")
    for s in swaps:
        print("   ", s)
    ok = worst_exact < 1e-9 and worst_full < 1e-3 and not failures
    for f in failures:
        print("FAIL", f)
    print("OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
