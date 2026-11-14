"""
build_moon_targets.py - Measure the features of Moon south pole sites.

It downloads (once) three NASA files from the Planetary Data System (PDS):
    LOLA  ldem_80s_80m   elevation of the south pole, 80 m pixels   (231 MB)
    LOLA  ldam_50s_1000m surface albedo at 1064 nm, 1 km pixels      (26 MB)
    Diviner PRP south    yearly mean and max temperature, ~500 m     (605 MB)

For every site in SITES it takes the area around the site, averages the
features there, and writes one row per site to data/targets_moon.csv.
The columns are the same as in data/earth.csv, so src/compare.py can use it.

How each feature is measured (kept the same as on Earth on purpose):
    elev_m        mean height above the Moon reference sphere (1737.4 km)
    slope_deg     mean slope between 80 m pixels
    roughness     mean standard deviation of height in a 3 x 3 pixel window (m)
    temp_mean_K   Diviner yearly mean temperature
    temp_range_K  Diviner yearly max temperature minus the yearly mean
    albedo        LOLA normal albedo (laser, 1064 nm)
    precip_mm     0 (it never rains on the Moon)

Example:
    python src/build_moon_targets.py
"""

import argparse
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from pyproj import CRS, Transformer
from rasterio.windows import Window

RAW = Path("data/raw/moon")
LOLA = "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/float_img/"
DIVINER = "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_prp/"
FILES = {
    "ldem_80s_80m_float.lbl": LOLA, "ldem_80s_80m_float.img": LOLA,
    "ldam_50s_1000m_float.lbl": LOLA, "ldam_50s_1000m_float.img": LOLA,
    "dlre_prp_south.lbl": DIVINER, "dlre_prp_south.tab": DIVINER,
}
MOON_LONLAT = CRS.from_proj4("+proj=longlat +R=1737400 +no_defs")
# South polar stereographic map of the Moon, in metres (same as the LOLA files).
POLAR = CRS.from_proj4("+proj=stere +lat_0=-90 +lon_0=0 +k=1 +R=1737400 +units=m +no_defs")

# ---------------------------------------------------------------------------
# 1. The sites. Centres and diameters come from the USGS Gazetteer of
#    Planetary Nomenclature. "rim" = a ring around the crater edge (where a
#    base would go: high, sunny ground); "disk" = a circle around the centre.
# ---------------------------------------------------------------------------

SITES = [
    # name,                       lat,     lon,     shape,  size_km (crater diameter or disk radius)
    ("Shackleton rim",           -89.67, 129.78, "rim",  20.92),
    ("de Gerlache rim",          -88.48, -88.34, "rim",  32.71),
    ("Haworth rim",              -87.45,  -5.17, "rim",  51.42),
    ("Faustini rim",             -87.18,  84.31, "rim",  42.48),
    ("Mons Mouton summit",       -84.60,  31.00, "disk",  5.0),
    ("Shackleton floor (shadow)", -89.67, 129.78, "disk",  3.0),
]
RIM_INNER, RIM_OUTER = 0.9, 1.3   # ring from 0.9 to 1.3 times the crater radius


# ---------------------------------------------------------------------------
# 2. Download
# ---------------------------------------------------------------------------

def download_missing():
    """Download each file only if we do not have it yet."""
    RAW.mkdir(parents=True, exist_ok=True)
    for name, base in FILES.items():
        path = RAW / name
        if path.exists() and path.stat().st_size > 0:
            continue
        print(f"  downloading {name} ...")
        tmp = path.with_suffix(path.suffix + ".part")
        urllib.request.urlretrieve(base + name, tmp)
        tmp.rename(path)  # only keep complete files


# ---------------------------------------------------------------------------
# 3. Geometry helpers
# ---------------------------------------------------------------------------

def site_mask(x, y, cx, cy, shape, size_km):
    """True for points (x, y in metres) that belong to the site."""
    dist_km = np.hypot(x - cx, y - cy) / 1000
    if shape == "rim":
        radius = size_km / 2
        return (dist_km >= RIM_INNER * radius) & (dist_km <= RIM_OUTER * radius)
    return dist_km <= size_km


def outer_radius_km(shape, size_km):
    return RIM_OUTER * size_km / 2 if shape == "rim" else size_km


def to_map(crs, lon, lat):
    """Longitude/latitude on the Moon -> x, y in metres in a map projection."""
    return Transformer.from_crs(MOON_LONLAT, crs, always_xy=True).transform(lon, lat)


# ---------------------------------------------------------------------------
# 4. Features from the rasters (LOLA)
# ---------------------------------------------------------------------------

def read_around(src, cx, cy, radius_km, pad=2):
    """Read the square of a raster around (cx, cy); returns values and pixel x, y."""
    row, col = src.index(cx, cy)
    half = int(np.ceil(radius_km * 1000 / abs(src.res[0]))) + pad
    window = Window(col - half, row - half, 2 * half + 1, 2 * half + 1)
    values = src.read(1, window=window, boundless=True, fill_value=np.nan).astype(float)
    values[(values < -1e30) | (values > 1e30)] = np.nan   # PDS "no data" value
    rows, cols = np.mgrid[row - half:row + half + 1, col - half:col + half + 1]
    xs, ys = rasterio.transform.xy(src.transform, rows.ravel(), cols.ravel())
    return values, np.reshape(xs, rows.shape), np.reshape(ys, rows.shape)


def terrain_features(dem, site):
    name, lat, lon, shape, size = site
    cx, cy = to_map(dem.crs, lon, lat)
    height_km, xs, ys = read_around(dem, cx, cy, outer_radius_km(shape, size))
    z = height_km * 1000                     # km -> m
    px = abs(dem.res[0])                     # 80 m

    dz_dy, dz_dx = np.gradient(z, px, px)
    slope = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))

    # Standard deviation of height in each 3 x 3 window (same as on Earth).
    pad = np.pad(z, 1, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(pad, (3, 3))
    rough = windows.std(axis=(2, 3))

    inside = site_mask(xs, ys, cx, cy, shape, size)
    return {"elev_m": np.nanmean(z[inside]), "slope_deg": np.nanmean(slope[inside]),
            "roughness": np.nanmean(rough[inside]), "n_dem_pixels": int(inside.sum())}


def albedo_feature(alb, site):
    name, lat, lon, shape, size = site
    cx, cy = to_map(alb.crs, lon, lat)
    values, xs, ys = read_around(alb, cx, cy, outer_radius_km(shape, size))
    inside = site_mask(xs, ys, cx, cy, shape, size)
    if not inside.any():   # very small site: use the nearest 1 km pixel
        inside = np.hypot(xs - cx, ys - cy) == np.hypot(xs - cx, ys - cy).min()
    return {"albedo": np.nanmean(values[inside])}


# ---------------------------------------------------------------------------
# 5. Temperature (Diviner polar resource product)
# ---------------------------------------------------------------------------

def load_diviner():
    """Read the Diviner table (2.9 million triangles); keep only what we need."""
    print("  reading Diviner temperatures (this takes a minute) ...")
    table = pd.read_csv(RAW / "dlre_prp_south.tab", skipinitialspace=True,
                        usecols=["tri_clon", "tri_clat", "temp_avg", "temp_max"])
    table = table[(table["temp_avg"] > 0) & (table["temp_max"] > 0)]   # -999 = no data
    return table


def temperature_features(div, x, y, site):
    name, lat, lon, shape, size = site
    cx, cy = to_map(POLAR, lon, lat)
    inside = site_mask(x, y, cx, cy, shape, size)
    part = div[inside]
    return {"temp_mean_K": part["temp_avg"].mean(),
            "temp_range_K": (part["temp_max"] - part["temp_avg"]).mean(),
            "n_temp_points": int(inside.sum())}



# ---------------------------------------------------------------------------
# 6. Putting it together
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build Moon target rows from LOLA and Diviner.")
    parser.add_argument("--out", default="data/targets_moon.csv")
    args = parser.parse_args()

    download_missing()
    div = load_diviner()
    div_x, div_y = to_map(POLAR, div["tri_clon"].to_numpy(), div["tri_clat"].to_numpy())

    rows = []
    with rasterio.open(RAW / "ldem_80s_80m_float.lbl") as dem, \
         rasterio.open(RAW / "ldam_50s_1000m_float.lbl") as alb:
        for site in SITES:
            row = {"name": site[0], "body": "Moon", "site_lat": site[1], "site_lon": site[2],
                   "area": f"{site[3]} {site[4]} km"}
            row.update(terrain_features(dem, site))
            row.update(temperature_features(div, div_x, div_y, site))
            row.update(albedo_feature(alb, site))
            row["precip_mm"] = 0.0
            rows.append(row)
            print(f"  {site[0]}: done")

    table = pd.DataFrame(rows)
    if table[["temp_mean_K", "slope_deg", "albedo"]].isna().any().any():
        print("WARNING: some sites have no data for a feature; check the coordinates.", file=sys.stderr)
    order = ["name", "body", "site_lat", "site_lon", "area", "elev_m", "slope_deg", "roughness",
             "temp_mean_K", "temp_range_K", "albedo", "precip_mm", "n_dem_pixels", "n_temp_points"]
    table = table[order].round({"elev_m": 1, "slope_deg": 2, "roughness": 2, "temp_mean_K": 2,
                                "temp_range_K": 2, "albedo": 4})
    table.to_csv(args.out, index=False)
    print(f"\nSaved {len(table)} Moon sites to {args.out}\n")
    print(table.drop(columns=["site_lat", "site_lon"]).to_string(index=False))


if __name__ == "__main__":
    main()
