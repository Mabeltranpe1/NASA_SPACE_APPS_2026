"""
Download (or copy) one high-resolution landscape image per Moon/Mars site,
and write a 2000 px wide JPEG preview of each.

Run from the repo root:
    python experiments/fotos_analogos/build_images.py

Sources were chosen by hand (see sites.csv / README notes). LROC images on
lroc.asu.edu (now lroc.im-ldi.com) only show 1100-1300 px web copies; the full
NAC frames are served as Zoomify tile pyramids, so for those we stitch the
tiles back together at a chosen pyramid level.
"""
import io
import json
import math
import os
import shutil
import socket
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# This network sometimes hangs on IPv6: try IPv4 addresses first.
_getaddrinfo = socket.getaddrinfo
socket.getaddrinfo = lambda *a, **k: sorted(_getaddrinfo(*a, **k), key=lambda r: r[0] != socket.AF_INET)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "images")
PREV = os.path.join(OUT, "previews")
UA = {"User-Agent": "Mozilla/5.0 (analog-photo-gallery)"}
MAX_BYTES = 60e6
LROC = "https://lroc.im-ldi.com"


def get(url, timeout=120):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def head_size(url):
    req = urllib.request.Request(url, headers=UA, method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        n = r.headers.get("Content-Length")
        return int(n) if n else None


def download(url, dest):
    size = head_size(url)
    if size and size > MAX_BYTES:
        raise RuntimeError(f"{url} is {size/1e6:.1f} MB > 60 MB")
    data = get(url)
    with open(dest, "wb") as f:
        f.write(data)


def zoomify_stitch(ptif, width, height, level_from_top=0, tile=256):
    """Rebuild a Zoomify pyramid level. level_from_top=0 is full resolution."""
    base = f"{LROC}/ptif/zoomify/{ptif}"
    tiers = []  # (cols, rows, w, h), from full res down
    w, h = width, height
    while w > tile or h > tile:
        tiers.append((math.ceil(w / tile), math.ceil(h / tile), w, h))
        w >>= 1
        h >>= 1
    tiers.append((1, 1, w, h))
    tiers.reverse()  # tier 0 = smallest
    z = len(tiers) - 1 - level_from_top
    cols, rows, W, H = tiers[z]
    offset = sum(c * r for c, r, _, _ in tiers[:z])
    def fetch(xy):
        x, y = xy
        idx = offset + y * cols + x
        url = f"{base}/TileGroup{idx // 256}/{z}-{x}-{y}.jpg"
        for attempt in range(4):
            try:
                return xy, Image.open(io.BytesIO(get(url, timeout=60)))
            except Exception:
                if attempt == 3:
                    raise

    canvas = None
    jobs = [(x, y) for y in range(rows) for x in range(cols)]
    with ThreadPoolExecutor(16) as pool:
        for n, ((x, y), t) in enumerate(pool.map(fetch, jobs), 1):
            if canvas is None:
                canvas = Image.new(t.mode, (W, H))
            canvas.paste(t, (x * tile, y * tile))
            if n % 100 == 0:
                print(f"  {ptif}: {n}/{len(jobs)} tiles", flush=True)
    return canvas


SITES = [
    # id, file stem, how
    ("01", "mars_jezero_perseverance", {"copy": "experiments/panorama_360/pia/PIA24264.tif", "ext": "tif"}),
    ("02", "mars_gale_mount_sharp", {"url": "https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia16/pia16768/PIA16768.jpg", "ext": "jpg"}),
    # The PIA10693 JPEG is only 21 KB, so the TIFF (0.7 MB) is the largest still.
    ("03", "mars_vastitas_phoenix", {"url": "https://assets.science.nasa.gov/content/dam/science/psd/photojournal/pia/pia10/pia10693/PIA10693.tif", "ext": "tif"}),
    # LROC "On the Rim!" (images/993): full NAC mosaic is a 3750x3750 Zoomify pyramid.
    ("04", "moon_shackleton_rim", {"zoomify": ("02_Shack_M1224655261_LRmos.2016aug_20180112_110035", 3750, 3750, 0), "ext": "png"}),
    # LROC images/1247: no zoomify; the original upload is 1100x1100.
    ("05", "moon_de_gerlache_ridge", {"url": f"{LROC}/ckeditor_assets/pictures/1130/original_M1348682369_LRmos.warp.str01.shrunk6x.1100x1100.png", "ext": "png"}),
    # LROC images/1408: 31000x10000 pyramid; level 1 below full = 15500x5000.
    ("06", "moon_mons_mouton_im2", {"zoomify": ("M1495922531_LRmos.warp.str01_str02.4zoom_20250308_134300", 31000, 10000, 1), "ext": "jpg"}),
]


def preview(src, dest, width=2000):
    im = Image.open(src)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dest, "JPEG", quality=88)


def main():
    os.makedirs(PREV, exist_ok=True)
    info = {}
    only = sys.argv[1:]
    for sid, stem, how in SITES:
        if only and sid not in only:
            continue
        dest = os.path.join(OUT, f"{sid}_{stem}.{how['ext']}")
        print(sid, stem)
        if not os.path.exists(dest):
            if "copy" in how:
                shutil.copy(how["copy"], dest)
            elif "url" in how:
                download(how["url"], dest)
            else:
                im = zoomify_stitch(*how["zoomify"])
                if how["ext"] == "jpg":
                    im.save(dest, "JPEG", quality=90)
                else:
                    im.save(dest, optimize=True)
        im = Image.open(dest)
        preview(dest, os.path.join(PREV, f"{sid}_{stem}.jpg"))
        info[sid] = {"file": os.path.relpath(dest, HERE), "width": im.width, "height": im.height,
                     "size_mb": round(os.path.getsize(dest) / 1e6, 2)}
        print("  ", info[sid])
    path = os.path.join(HERE, "images_info.json")
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(info)
    json.dump(old, open(path, "w"), indent=1)


if __name__ == "__main__":
    main()
