"""
export_gallery.py - Download the curated image gallery shown in the app's carousels.

Input:  data/gallery_sources.json  hand-picked images per place (NASA Image and
                                   Video Library ids or NASA SVS stills), with
                                   a short caption in Spanish and English.
Output: web/public/images/gallery/<place>/<n>.jpg   resized JPEGs (max 1600 px)
        web/public/data/gallery.json                captions, credit, date, kind
                                                    and link to the source

Every image is public NASA material (NASA media guidelines: not copyrighted
unless noted). The script stops on any image whose description mentions a
copyright, and keeps the credit line written in the NASA description
("Credit: NASA/JPL-Caltech/..."). Details: docs/DATOS_WEB.md.

Examples:
    python src/export_gallery.py            # only missing images
    python src/export_gallery.py --force    # download everything again
"""

import argparse
import html
import io
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
NASA_API = "https://images-api.nasa.gov"
SVS_API = "https://svs.gsfc.nasa.gov/api"

MAX_SIDE = 1600
MAX_ASPECT = 2.4  # wider panoramas are center-cropped to this width / height
MIN_ASPECT = 0.75  # taller strips are center-cropped to this

session = requests.Session()
session.headers["User-Agent"] = "earth-analogs-app/1.0 (NASA Space Apps 2026)"


def get(url, **kwargs):
    for attempt in range(4):
        try:
            r = session.get(url, timeout=120, **kwargs)
            r.raise_for_status()
            return r
        except requests.RequestException as err:
            if attempt == 3:
                raise
            print(f"      retry ({err})")
            time.sleep(3 * 2**attempt)
    raise RuntimeError("unreachable")


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text or ""))).strip()


def nasa_credit(desc, center, secondary_creator=None):
    """Mission credit: the item's secondary_creator (e.g. NASA/JPL-Caltech/MSSS), else a credit line in the text."""
    if secondary_creator and "nasa" in secondary_creator.lower():
        return secondary_creator.strip()
    m = re.search(r"(?:image )?credits?:\s*([^\n]+?)(?:\.\s|\.?$)", desc, re.I)
    if m:
        return m.group(1).strip().rstrip(".")
    return f"NASA/{center}" if center else "NASA"


def nasa_image(nasa_id):
    """Best JPEG of a NASA Image Library item (large or original) + its metadata."""
    data = get(f"{NASA_API}/search", params={"nasa_id": nasa_id}).json()["collection"]["items"]
    if not data:
        raise ValueError(f"{nasa_id}: not found in the NASA Image Library")
    meta = data[0]["data"][0]
    desc = clean(meta.get("description", ""))
    if re.search(r"©|copyright", desc, re.I):
        raise ValueError(f"{nasa_id}: the description mentions a copyright, choose another image")
    assets = [a["href"] for a in get(f"{NASA_API}/asset/{nasa_id}").json()["collection"]["items"]]
    jpgs = [a for a in assets if a.lower().endswith((".jpg", ".jpeg"))]
    large = next((a for a in jpgs if "~large" in a), None)
    orig = next((a for a in jpgs if "~orig" in a), None)
    img = open_image(large or orig or jpgs[0])
    # A small "large" rendition (or a thin panorama, cropped later): use the original.
    if orig and large and min(img.size) < 900:
        img = open_image(orig)
    return img, {
        "title": clean(meta.get("title", "")),
        "date": (meta.get("date_created") or "")[:10],
        "credit": nasa_credit(desc, meta.get("center"), meta.get("secondary_creator")),
        "source_url": f"https://images.nasa.gov/details/{nasa_id}",
    }


def open_image(url):
    """Decode a JPEG at reduced scale when it is huge (some panoramas are ~200 megapixels)."""
    Image.MAX_IMAGE_PIXELS = None  # trusted NASA sources; draft() keeps memory low
    img = Image.open(io.BytesIO(get(url.replace("http://", "https://")).content))
    if img.format == "JPEG":
        img.draft("RGB", (MAX_SIDE * 2, MAX_SIDE * 2))
    img.load()
    return img


def svs_image(svs_id, file):
    page = get(f"{SVS_API}/{svs_id}").json()
    url = None
    for group in page.get("media_groups", []):
        for item in group.get("items", []):
            inst = item.get("instance") or {}
            if (inst.get("url") or "").endswith(file):
                url = inst["url"]
    if not url:
        raise ValueError(f"SVS {svs_id}: {file} not found")
    img = open_image(url)
    return img, {
        "title": clean(page.get("title", "")),
        "date": (page.get("release_date") or "")[:10],
        "credit": "NASA's Scientific Visualization Studio (LRO data)",
        "source_url": f"https://svs.gsfc.nasa.gov/{svs_id}",
    }


def trim_and_fit(img):
    """Remove black borders (rotated orbital strips), tame extreme aspect ratios and resize."""
    img = img.convert("RGB")
    a = np.asarray(img)
    # Only rows/columns that are almost entirely black: lunar shadows are dark
    # too, so anything stricter eats real terrain.
    lit = a.max(axis=2) > 12
    rows = np.where(lit.mean(axis=1) > 0.03)[0]
    cols = np.where(lit.mean(axis=0) > 0.03)[0]
    if len(rows) > 10 and len(cols) > 10:
        img = img.crop((cols[0], rows[0], cols[-1] + 1, rows[-1] + 1))
    w, h = img.size
    if w / h > MAX_ASPECT:
        nw = int(h * MAX_ASPECT)
        img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    elif w / h < MIN_ASPECT:
        nh = int(w / MIN_ASPECT)
        img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    return img


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sources", default=str(ROOT / "data/gallery_sources.json"))
    parser.add_argument("--images", default=str(ROOT / "web/public/images/gallery"))
    parser.add_argument("--out", default=str(ROOT / "web/public/data/gallery.json"))
    parser.add_argument("--quality", type=int, default=80)
    parser.add_argument("--force", action="store_true", help="Download images that already exist")
    parser.add_argument("--only", nargs="*", help="Only these places (with --force, redo just them)")
    args = parser.parse_args(argv)

    sources = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    images_dir = Path(args.images)
    out_path = Path(args.out)
    previous = json.loads(out_path.read_text(encoding="utf-8"))["places"] if out_path.exists() else {}
    cache = {}  # the same image can be used by several places
    places, problems = {}, []

    for place, entries in sources["places"].items():
        folder = images_dir / place.replace(":", "_")
        redo = args.force and (not args.only or place in args.only)
        folder.mkdir(parents=True, exist_ok=True)
        print(place)
        items = []
        for n, e in enumerate(entries, 1):
            key = e.get("nasa_id") or f"svs-{e['svs']}-{e['file']}"
            file = folder / f"{n}.jpg"
            rel = f"{folder.name}/{file.name}"
            old = next((x for x in previous.get(place, []) if x.get("key") == key and x["file"] == rel), None)
            try:
                if old and file.exists() and not redo:
                    meta = {k: old[k] for k in ("title", "date", "credit", "source_url", "width", "height")}
                else:
                    if key not in cache:
                        cache[key] = nasa_image(e["nasa_id"]) if "nasa_id" in e else svs_image(e["svs"], e["file"])
                    img, meta = cache[key]
                    fitted = trim_and_fit(img)
                    fitted.save(file, "JPEG", quality=args.quality, optimize=True, progressive=True)
                    meta = {**meta, "width": fitted.width, "height": fitted.height}
                    print(f"   {n}. {key}: {fitted.width}x{fitted.height}, {file.stat().st_size // 1024} KB · {meta['credit']}")
            except (requests.RequestException, ValueError, OSError) as err:
                print(f"   {n}. {key}: SKIPPED ({err})")
                problems.append(f"{place}/{key}: {err}")
                continue
            items.append({
                "key": key,
                "file": rel,
                "kind": e["kind"],
                "caption": {"es": e["es"], "en": e["en"]},
                **meta,
            })
        places[place] = items
        keep = {Path(it["file"]).name for it in items}
        for stale in folder.glob("*.jpg"):
            if stale.name not in keep:
                stale.unlink()

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "aliases": sources.get("aliases", {}),
        "places": places,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(f.stat().st_size for f in images_dir.rglob("*.jpg")) / 1e6
    count = sum(len(v) for v in places.values())
    print(f"\n{count} images for {len(places)} places ({total:.1f} MB) -> {out_path}")
    if problems:
        print("Problems:\n  " + "\n  ".join(problems))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
