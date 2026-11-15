"""
make_photos.py - Real images (what the place really looks like) for every map.

For every pair listed in maps/index.csv (made by src/make_maps.py) it saves,
next to the relief maps, an image of the SAME square with the real surface:

    maps/07_mars_jezero_crater_B_mars_photo.png
    maps/07_mars_jezero_crater_A1_earth_north_greenland_photo.png

The images contain only the surface and a small scale bar, so the
textures of the terrain can be compared directly.

Sources (all free, no login):
    Earth: Sentinel-2 L2A true colour, 10 m (ESA Copernicus), from the open
           AWS catalogue (earth-search.aws.element84.com). For every place we
           pick the scenes with the least clouds and snow, and join several
           scenes if one does not cover the whole square.
    Mars:  CTX global mosaic, 5 m, black and white (NASA/JPL/MSSS, Caltech
           Murray Lab), read from the Esri "OnMars" tile service.
    Moon:  LROC WAC south pole mosaic, 100 m, black and white (NASA/LRO/ASU).
           The Moon is almost grey, so this is close to its real colour.
           100 m is the best mosaic that covers all the south pole sites, so
           Moon images are less sharp than Earth and Mars images.

All images are reprojected to a square of N x N km around the place (an
azimuthal equidistant map centred on it), so 1 pixel = the same number of
metres in the Earth image and in its Moon/Mars twin.

Example:
    python src/make_photos.py
"""

import argparse
import io
import math
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import requests
from PIL import Image, ImageDraw, ImageFont
from rasterio.crs import CRS
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject
from pyproj import Transformer
from shapely.geometry import Point, shape

os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")   # Sentinel-2 files on AWS are public
os.environ.setdefault("AWS_REGION", "us-west-2")

OUT_PX = 2000                       # output images are OUT_PX x OUT_PX pixels
STAC = "https://earth-search.aws.element84.com/v1/search"
CTX_TILES = "https://astro.arcgis.com/arcgis/rest/services/OnMars/CTX/MapServer/tile/{z}/{y}/{x}"
CTX_RES = [0.3515625 / 2**z for z in range(18)]          # degrees per pixel at each zoom level
LROC_SOUTH = ("/vsicurl/https://pds.lroc.asu.edu/data/LRO-L-LROC-5-RDR-V1.0/LROLRC_2001/"
              "DATA/BDR/WAC_GLOBAL/WAC_GLOBAL_P900S0000_100M.IMG")
RADIUS = {"earth": None, "mars": 3396190.0, "moon": 1737400.0}


# ---------------------------------------------------------------------------
# 1. The output square: a small flat map centred on the place
# ---------------------------------------------------------------------------

def square_crs(body, lat, lon):
    """Azimuthal equidistant map centred on the place (distances in metres are true)."""
    if body == "earth":
        return CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m +no_defs")
    return CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +R={RADIUS[body]} +units=m +no_defs")


def square_grid(size_km):
    half = size_km * 1000 / 2
    pixel = size_km * 1000 / OUT_PX
    return from_origin(-half, half, pixel, pixel), pixel


def lonlat_crs(body):
    if body == "earth":
        return CRS.from_epsg(4326)
    return CRS.from_proj4(f"+proj=longlat +R={RADIUS[body]} +no_defs")


# ---------------------------------------------------------------------------
# 2. Earth: Sentinel-2 true colour
# ---------------------------------------------------------------------------

def search_scenes(bbox, query, months=None):
    """Sentinel-2 scenes over the box (only open Cloud-Optimized GeoTIFFs), best first."""
    body = {"collections": ["sentinel-2-l2a"], "bbox": bbox, "limit": 200,   # 300+ gives a server error
            "datetime": "2019-01-01T00:00:00Z/2025-10-31T00:00:00Z", "query": query,
            "sortby": [{"field": "properties.eo:cloud_cover", "direction": "asc"}]}
    response = requests.post(STAC, json=body, timeout=120)
    response.raise_for_status()                    # stop loudly instead of making a black image
    items = response.json().get("features", [])
    items = [f for f in items if f["assets"].get("visual", {}).get("href", "").endswith(".tif")]
    if months:
        items = [f for f in items if int(f["properties"]["datetime"][5:7]) in months]
    return sorted(items, key=lambda f: f["properties"].get("eo:cloud_cover", 50)
                  + f["properties"].get("s2:snow_ice_percentage", 0))


def earth_photo(lat, lon, size_km):
    """
    Fill the square with the best Sentinel-2 scenes. We try strict rules first
    (few clouds, little snow, summer near the poles) and only relax them for
    the parts that are still empty.
    """
    dst_crs = square_crs("earth", lat, lon)
    dst_transform, pixel_m = square_grid(size_km)
    half_lat = size_km / 2 / 111.32 * 1.1
    half_lon = half_lat / max(math.cos(math.radians(lat)), 0.05)
    bbox = [lon - half_lon, lat - half_lat, lon + half_lon, lat + half_lat]
    summer = ((6, 7, 8) if lat > 0 else (12, 1, 2)) if abs(lat) > 60 else None
    rules = [({"eo:cloud_cover": {"lt": 10}, "s2:snow_ice_percentage": {"lt": 40}}, summer),
             ({"eo:cloud_cover": {"lt": 20}}, summer),
             ({"eo:cloud_cover": {"lt": 40}}, None)]

    # A coarse grid of the square in lon/lat, to know which scenes touch the empty part.
    step = 50
    gy, gx = np.mgrid[step // 2:OUT_PX:step, step // 2:OUT_PX:step]
    xs, ys = rasterio.transform.xy(dst_transform, gy.ravel(), gx.ravel())
    lons, lats = Transformer.from_crs(dst_crs, "EPSG:4326", always_xy=True).transform(xs, ys)
    points = [Point(a, b) for a, b in zip(lons, lats)]

    # 20 m overviews are enough when one output pixel is 20 m or more (much faster).
    overview = {"OVERVIEW_LEVEL": 0} if pixel_m >= 19 else {}
    rgb = np.zeros((3, OUT_PX, OUT_PX), dtype=np.uint8)
    reads = 0
    for query, months in rules:
        for f in search_scenes(bbox, query, months):
            empty = rgb.max(axis=0) == 0
            if empty.mean() < 0.002 or reads >= 30:
                return np.moveaxis(rgb, 0, -1)
            footprint = shape(f["geometry"])
            still_empty = empty[gy.ravel(), gx.ravel()]
            if not any(footprint.contains(p) for p, e in zip(points, still_empty) if e):
                continue                                   # this scene adds nothing new
            with rasterio.open(f["assets"]["visual"]["href"], **overview) as src:
                scene = np.zeros_like(rgb)
                for band in range(3):
                    reproject(rasterio.band(src, band + 1), scene[band], dst_transform=dst_transform,
                              dst_crs=dst_crs, resampling=Resampling.average, src_nodata=0, dst_nodata=0)
            reads += 1
            rgb[:, empty] = scene[:, empty]               # fill only what is still empty
    return np.moveaxis(rgb, 0, -1)


# ---------------------------------------------------------------------------
# 3. Mars: CTX mosaic tiles
# ---------------------------------------------------------------------------

def ctx_mosaic(lat, lon, size_km, zoom, session):
    """Join the CTX tiles of one zoom level that cover the square (0 = missing)."""
    res = CTX_RES[zoom]
    tile_deg = res * 512
    half_lat = size_km * 1000 / 2 / (math.radians(1) * RADIUS["mars"]) * 1.1
    half_lon = half_lat / max(math.cos(math.radians(lat)), 0.05)
    c0, c1 = int((lon - half_lon + 180) // tile_deg), int((lon + half_lon + 180) // tile_deg)
    r0, r1 = int((90 - (lat + half_lat)) // tile_deg), int((90 - (lat - half_lat)) // tile_deg)
    mosaic = np.zeros(((r1 - r0 + 1) * 512, (c1 - c0 + 1) * 512), dtype=np.uint8)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            for attempt in range(4):              # the server sometimes cuts a tile short
                if attempt:
                    time.sleep(2 * attempt)
                try:
                    resp = session.get(CTX_TILES.format(z=zoom, y=r, x=c), timeout=60)
                    if resp.status_code != 200 or not resp.content:
                        break
                    tile = Image.open(io.BytesIO(resp.content)).convert("LA")
                    gray, alpha = np.array(tile)[..., 0], np.array(tile)[..., 1]
                    gray = np.where(alpha > 0, np.maximum(gray, 1), 0)   # transparent = missing
                    mosaic[(r - r0) * 512:(r - r0 + 1) * 512,
                           (c - c0) * 512:(c - c0 + 1) * 512] = gray
                    break
                except (OSError, requests.RequestException):
                    continue
    return mosaic, from_origin(-180 + c0 * tile_deg, 90 - r0 * tile_deg, res, res)


def mars_photo(lat, lon, size_km):
    """
    CTX tiles at the best zoom level. Some tiles of the service are empty at a
    given zoom, so the holes are filled from the next coarser zoom levels.
    """
    pixel_m = size_km * 1000 / OUT_PX
    deg_needed = pixel_m / (math.radians(1) * RADIUS["mars"])
    best = max(z for z in range(len(CTX_RES)) if CTX_RES[z] >= deg_needed / 2)
    dst_transform, _ = square_grid(size_km)
    out = np.zeros((OUT_PX, OUT_PX), dtype=np.uint8)
    session = requests.Session()
    for zoom in range(best, max(best - 4, 0), -1):
        mosaic, src_transform = ctx_mosaic(lat, lon, size_km, zoom, session)
        layer = np.zeros_like(out)
        reproject(mosaic, layer, src_transform=src_transform, src_crs=lonlat_crs("mars"),
                  dst_transform=dst_transform, dst_crs=square_crs("mars", lat, lon),
                  resampling=Resampling.average, src_nodata=0, dst_nodata=0)
        empty = out == 0
        out[empty] = layer[empty]
        if (out == 0).mean() < 0.001:
            break
    return out


# ---------------------------------------------------------------------------
# 4. Moon: LROC WAC south pole mosaic (read only the small window we need)
# ---------------------------------------------------------------------------

def moon_photo(lat, lon, size_km):
    dst_transform, _ = square_grid(size_km)
    out = np.zeros((OUT_PX, OUT_PX), dtype=np.float32)
    with rasterio.Env(GDAL_HTTP_TIMEOUT="120"), rasterio.open(LROC_SOUTH) as src:
        reproject(rasterio.band(src, 1), out, dst_transform=dst_transform,
                  dst_crs=square_crs("moon", lat, lon), resampling=Resampling.bilinear,
                  dst_nodata=np.nan)
    out[out < -1] = np.nan
    low, high = np.nanpercentile(out, [1, 99.5])          # stretch the contrast
    return (np.clip((out - low) / (high - low), 0, 1) * 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# 5. Scale bar and saving
# ---------------------------------------------------------------------------

def nice_length(km):
    """A round length near a quarter of the image width (1, 2, 5, 10, 20 km...)."""
    target = km / 4
    for step in (0.5, 1, 2, 5, 10, 20, 50, 100):
        if step >= target * 0.7:
            return step
    return 100


def save_with_scale(array, size_km, path):
    image = Image.fromarray(array).convert("RGB")
    draw = ImageDraw.Draw(image)
    bar_km = nice_length(size_km)
    bar_px = int(bar_km / size_km * OUT_PX)
    x0, y0, h = 60, OUT_PX - 90, 22
    font = ImageFont.load_default(size=44)
    label = f"{bar_km:g} km"
    tw = draw.textlength(label, font=font)
    draw.rectangle([x0 - 16, y0 - 70, x0 + max(bar_px, tw) + 16, y0 + h + 16], fill=(0, 0, 0))
    draw.rectangle([x0, y0, x0 + bar_px, y0 + h], fill=(255, 255, 255))
    draw.text((x0, y0 - 60), label, fill=(255, 255, 255), font=font)
    image.save(path, optimize=True)


def main():
    parser = argparse.ArgumentParser(description="Real-colour images for the maps in maps/.")
    parser.add_argument("--maps", default="maps")
    parser.add_argument("--targets", default="data/targets.csv")
    parser.add_argument("--only", help="Only images whose number starts with this, e.g. 07")
    args = parser.parse_args()

    maps = Path(args.maps)
    index = pd.read_csv(maps / "index.csv", dtype={"number": str})
    targets = pd.read_csv(args.targets).set_index("name")
    sources = {"earth": "Sentinel-2 L2A true colour 10 m (ESA Copernicus, via AWS earth-search)",
               "mars": "CTX mosaic 5 m (NASA/JPL/MSSS, Caltech Murray Lab, Esri OnMars)",
               "moon": "LROC WAC south pole mosaic 100 m (NASA/LRO/ASU)"}
    done, rows = set(), []
    for _, row in index.iterrows():
        if args.only and not row["number"].startswith(args.only):
            continue
        target = targets.loc[row["target"]]
        shape, size = target["area"].split()[0], float(target["area"].split()[1])
        size_km = max(1.5 * size, 20.0) if shape == "rim" else max(4 * size, 20.0)
        body = row["body"].lower()
        jobs = [(row["image_earth"], "earth", row["earth_lat"], row["earth_lon"])]
        if row["image_twin"] not in done:
            jobs.append((row["image_twin"], body, target["site_lat"], target["site_lon"]))
            done.add(row["image_twin"])
        for relief_name, what, lat, lon in jobs:
            path = maps / relief_name.replace(".png", "_photo.png")
            try:
                if what == "earth":
                    array = earth_photo(lat, lon, size_km)
                elif what == "mars":
                    array = mars_photo(lat, lon, size_km)
                else:
                    array = moon_photo(lat, lon, size_km)
                save_with_scale(array, size_km, path)
                rows.append({"image": path.name, "source": sources[what], "square_km": size_km})
                print(f"  {path.name}")
            except Exception as err:   # keep going if one image fails
                print(f"  FAILED {path.name}: {err}")
    if rows:
        pd.DataFrame(rows).to_csv(maps / "photo_sources.csv", index=False)


if __name__ == "__main__":
    main()
