"""
export_images.py - Close-up satellite images of the Earth places shown in the app.

For every catalog site (web/src/data/sites.ts) and every discovery of the
global search (web/public/data/comparisons.json) it:
    1. searches the Microsoft Planetary Computer STAC catalog for the least
       cloudy Sentinel-2 L2A scene (10 m) that covers the WHOLE crop;
    2. renders a square crop of about 22 km around the place with the
       Planetary Computer data API (true color, same crop as the app used
       with NASA GIBS);
    3. when the crop falls on the border between two Sentinel-2 tiles, joins
       the tiles of the same satellite pass (same date, seamless); rejects
       crops that still have empty (black) borders and tries the next pass;
    4. saves a light JPEG in web/public/images/earth/<id>.jpg and writes
       web/public/images/earth/index.json with the scene id, date and cloud
       cover of every image, so the app can cite its source.

The app loads these files directly (fast and reliable during a demo). If an
image is missing it falls back to the NASA GIBS snapshot (Landsat WELD).

Free service, no key or account needed. Imagery license: Copernicus
Sentinel data (ESA), open with attribution. (Landsat was tried as a second
source, but the Planetary Computer returned HTTP 500 when rendering its crops.)
Details: docs/DATOS_WEB.md.

Examples:
    python src/export_images.py                  # only missing images (~10 min the first time)
    python src/export_images.py --only tatacoa   # one place
    python src/export_images.py --force          # redo everything
    python src/export_images.py --redo-saturated # redo burnt-out crops (bright sand)
"""

import argparse
import io
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

import numpy as np
import requests
from PIL import Image
from shapely.geometry import box, shape
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_web import read_catalog_sites  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
API = "https://planetarycomputer.microsoft.com/api"

# Half side of the crop in degrees of latitude (0.1 deg = about 11 km), the
# same crop the app used with NASA GIBS. Longitude is widened by 1/cos(lat)
# so the ground area stays square.
HALF_LAT_DEG = 0.1
DATE_RANGE = "2021-01-01/2025-12-31"

COLLECTION = "sentinel-2-l2a"
SOURCE = "Sentinel-2 L2A"
GSD_M = 10
CREDIT = "Copernicus Sentinel-2 (ESA) · Microsoft Planetary Computer"
MAX_PASSES = 5  # satellite passes tried per place, least cloudy first

session = requests.Session()
session.headers["User-Agent"] = "earth-analogs-app/1.0 (NASA Space Apps 2026)"


def request(method, url, retries=4, **kwargs):
    """HTTP request with retries and backoff (the render API is sometimes slow)."""
    for attempt in range(retries):
        try:
            r = session.request(method, url, timeout=120, **kwargs)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return r
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as err:
            if attempt == retries - 1:
                raise
            wait = 3 * 2**attempt
            print(f"      retry in {wait}s ({err})")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def crop_box(lat, lng):
    half_lng = HALF_LAT_DEG / max(math.cos(math.radians(lat)), 0.05)
    return (lng - half_lng, lat - HALF_LAT_DEG, lng + half_lng, lat + HALF_LAT_DEG)


# Above 60 degrees only summer scenes, so the ground is not under snow.
SUMMER_MONTHS = {"north": {7, 8}, "south": {12, 1, 2}}


def in_season(item, lat):
    if abs(lat) < 60:
        return True
    month = int(item["properties"]["datetime"][5:7])
    return month in SUMMER_MONTHS["north" if lat > 0 else "south"]


def passes(bbox, max_cloud, lat, limit=200):
    """
    Scenes that touch the crop, grouped by satellite pass (datatake), least
    cloudy pass first. Only passes whose tiles together cover the crop.
    """
    area = box(*bbox)
    body = {
        "collections": [COLLECTION],
        "intersects": area.__geo_interface__,
        "datetime": DATE_RANGE,
        "query": {"eo:cloud_cover": {"lt": max_cloud}},
        "sortby": [{"field": "eo:cloud_cover", "direction": "asc"}],
        "limit": limit,
    }
    items = request("POST", f"{API}/stac/v1/search", json=body).json()["features"]
    groups = {}
    for it in (x for x in items if in_season(x, lat)):
        key = it["properties"].get("s2:datatake_id") or it["properties"]["datetime"][:10]
        groups.setdefault(key, []).append(it)
    out = []
    for group in groups.values():
        covered = unary_union([shape(it["geometry"]) for it in group]).intersection(area).area / area.area
        if covered < 0.99:
            continue
        # Tile that covers most of the crop first.
        group.sort(key=lambda it: -shape(it["geometry"]).intersection(area).area)
        out.append(group)
    return out


# Very bright surfaces (sand seas, salt) saturate the 8-bit true-color product
# ("visual"). Those crops are rendered again from the red, green and blue bands
# with a wider stretch. L2A values carry a +1000 offset (processing baseline 04.00).
BRIGHT_PARAMS = [("assets", "B04"), ("assets", "B03"), ("assets", "B02"),
                 ("rescale", "1000,9000"), ("color_formula", "Gamma RGB 1.3"), ("nodata", "0")]
SATURATED_LIMIT = 0.25


def render(item, bbox, size, bright=False):
    """True-color crop rendered by the Planetary Computer data API."""
    if bright:
        params = [("collection", COLLECTION), ("item", item["id"]), *BRIGHT_PARAMS]
    else:  # default style of the item
        params = list(parse_qsl(urlsplit(item["assets"]["rendered_preview"]["href"]).query))
        params = [(k, v) for k, v in params if k != "format"]
    params.append(("format", "png"))
    path = ",".join(f"{v:.5f}" for v in bbox)
    url = f"{API}/data/v1/item/bbox/{path}/{size}x{size}.png?{urlencode(params)}"
    return Image.open(io.BytesIO(request("GET", url).content)).convert("RGB")


def saturated_share(pixels):
    """Share of burnt-out pixels (some channel at the top of the scale)."""
    return float((pixels.max(axis=2) >= 250).mean())


def compose(group, bbox, size, bright):
    """Crop from the tiles of one pass, filling each tile's empty part with the next one."""
    pixels, used = None, []
    for item in group:
        img = np.asarray(render(item, bbox, size, bright)).copy()
        if pixels is None:
            pixels = img
        else:
            hole = pixels.max(axis=2) < 6
            pixels[hole] = img[hole]
        used.append(item)
        if empty_share(Image.fromarray(pixels)) <= 0.02:
            break
    return pixels, used


def empty_share(img):
    """Share of pure black pixels (no data outside the scene or masked)."""
    small = np.asarray(img.resize((128, 128)))
    return float((small.max(axis=2) < 6).mean())


def best_image(lat, lng, size, max_cloud):
    bbox = crop_box(lat, lng)
    try:
        groups = passes(bbox, max_cloud, lat)
    except requests.RequestException as err:
        print(f"      search failed: {err}")
        return None, None
    for group in groups[:MAX_PASSES]:
        try:
            pixels, used = compose(group, bbox, size, bright=False)
            stretch = "visual"
            if saturated_share(pixels) > SATURATED_LIMIT:
                print(f"      {saturated_share(pixels):.0%} burnt out: rendering the bands with a wider stretch")
                pixels, used = compose(group, bbox, size, bright=True)
                stretch = "B04-B03-B02 1000-9000"
        except requests.RequestException as err:
            print(f"      render failed for {group[0]['id']}: {err}")
            continue
        empty = empty_share(Image.fromarray(pixels))
        if empty > 0.02:
            print(f"      pass {group[0]['id'][:27]}: {empty:.0%} empty, next pass")
            continue
        props = used[0]["properties"]
        meta = {
            "collection": COLLECTION,
            "source": SOURCE,
            "credit": CREDIT,
            "item": " + ".join(it["id"] for it in used),
            "date": props["datetime"][:10],
            "cloud_cover": round(max(float(it["properties"]["eo:cloud_cover"]) for it in used), 2),
            "gsd_m": GSD_M,
            "stretch": stretch,
            "width_km": round(2 * HALF_LAT_DEG * 111),
            "bbox": [round(v, 5) for v in bbox],
        }
        return Image.fromarray(pixels), meta
    return None, None


def places(sites_ts, comparisons):
    """Catalog sites (all of them) + every discovery of the global search."""
    out = [{"id": s["id"], "name": s["name"], "lat": s["lat"], "lng": s["lng"]} for s in read_catalog_sites(sites_ts)]
    data = json.loads(Path(comparisons).read_text(encoding="utf-8"))
    seen = {p["id"] for p in out}
    for s in data["sites"]:
        if s.get("kind") == "discovery" and s["id"] not in seen:
            out.append({"id": s["id"], "name": s["name"], "lat": s["lat"], "lng": s["lng"]})
            seen.add(s["id"])
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sites-ts", default=str(ROOT / "web/src/data/sites.ts"))
    parser.add_argument("--comparisons", default=str(ROOT / "web/public/data/comparisons.json"))
    parser.add_argument("--out", default=str(ROOT / "web/public/images/earth"))
    parser.add_argument("--size", type=int, default=1024, help="Image side in pixels (default 1024)")
    parser.add_argument("--quality", type=int, default=80, help="JPEG quality (default 80)")
    parser.add_argument("--max-cloud", type=float, default=20, help="Max scene cloud cover in %% (default 20)")
    parser.add_argument("--only", nargs="*", help="Only these place ids")
    parser.add_argument("--force", action="store_true", help="Redo images that already exist")
    parser.add_argument("--prune", action="store_true",
                        help="Delete the images of places that are no longer in the app data")
    parser.add_argument("--redo-saturated", action="store_true",
                        help="Redo the existing images that are burnt out (bright sand or salt)")
    args = parser.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    index_path = out / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {"images": {}}
    images = index.get("images", {})

    todo = places(args.sites_ts, args.comparisons)
    if args.prune:
        wanted = {p["id"] for p in todo}
        stale = sorted(pid for pid in images if pid not in wanted)
        for pid in stale:
            (out / images.pop(pid)["file"]).unlink(missing_ok=True)
        print(f"Pruned {len(stale)} images of places no longer in the data")
    if args.only:
        todo = [p for p in todo if p["id"] in set(args.only)]
    if args.redo_saturated:
        burnt = {pid for pid, m in images.items()
                 if (out / m["file"]).exists()
                 and saturated_share(np.asarray(Image.open(out / m["file"]).convert("RGB"))) > SATURATED_LIMIT}
        print("Burnt-out images to redo:", ", ".join(sorted(burnt)) or "none")
        todo = [p for p in todo if p["id"] in burnt]
        args.force = True
    failed = []
    for i, p in enumerate(todo, 1):
        file = out / f"{p['id']}.jpg"
        if not args.force and file.exists() and p["id"] in images:
            continue
        print(f"[{i}/{len(todo)}] {p['name']} ({p['lat']:.2f}, {p['lng']:.2f})")
        img, meta = best_image(p["lat"], p["lng"], args.size, args.max_cloud)
        if img is None:
            print("      no usable scene: the app keeps the NASA GIBS image")
            failed.append(p["id"])
            images.pop(p["id"], None)
            continue
        img.save(file, "JPEG", quality=args.quality, optimize=True, progressive=True)
        images[p["id"]] = {"file": file.name, **meta}
        print(f"      {meta['source']} {meta['date']} · {meta['cloud_cover']}% clouds · {file.stat().st_size // 1024} KB")
        # Save after every image so an interrupted run keeps its progress.
        index_path.write_text(json.dumps(
            {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "images": dict(sorted(images.items()))},
            ensure_ascii=False, indent=1), encoding="utf-8")

    index_path.write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "images": dict(sorted(images.items()))},
        ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(f.stat().st_size for f in out.glob("*.jpg")) / 1e6
    print(f"\n{len(images)} images in {out} ({total:.1f} MB).")
    if failed:
        print("Without image (GIBS fallback):", ", ".join(failed))


if __name__ == "__main__":
    main()
