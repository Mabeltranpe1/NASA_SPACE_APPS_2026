"""
build_mars_targets.py - Measure the features of Mars sites.

Sources (all free, no login):
    HRSC + MOLA blended elevation, 200 m pixels (USGS). The file is 11 GB,
        so we do NOT download it: we read only the small square around
        each site directly from the internet.
    TES albedo map, 7.4 km pixels (USGS)                          (17 MB)
    Mars Climate Database v6.2 (LMD, France): surface temperature for every
        season and every hour of the day at each site. Saved in
        data/raw/mars/mcd/ so we can also study seasons later.

Output: data/targets_mars.csv, with the same columns as data/earth.csv.
    elev_m        mean height above the Mars reference (areoid)
    slope_deg     mean slope between 200 m pixels
    roughness     mean standard deviation of height in a 3 x 3 pixel window (m)
    (slope and roughness use 200 m pixels on every body, see terrain_common.py)
    temp_mean_K   mean surface temperature over all seasons and hours
    temp_range_K  hottest moment of the year minus the yearly mean
    albedo        TES albedo
    precip_mm     0 (it does not rain on Mars today)
    ndvi          0 (no plants)
    em_contrast   empty for now: needs a calibration with TES spectra, so it
                  is not compared yet


Example:
    python src/build_mars_targets.py
"""

import argparse
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window


sys.path.insert(0, str(Path(__file__).parent))
import terrain_common  # noqa: E402  (same 200 m terrain for every body)
RAW = Path("data/raw/mars")
DEM_URL = ("/vsicurl/https://planetarymaps.usgs.gov/mosaic/Mars/HRSC_MOLA_Blend/"
           "Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif")
ALBEDO_URL = "https://planetarymaps.usgs.gov/mosaic/Mars_MGS_TES_Albedo_mosaic_global_7410m.tif"
MCD_URL = "https://www-mars.lmd.jussieu.fr/mcd_python/cgi-bin/mcdcgi.py"
MARS_RADIUS_M = 3396190.0
RADIUS_KM = 10.0   # each site is a circle with this radius

# name, latitude, longitude (east, -180..180). Real landing sites, plus
# Arcadia Planitia, a region studied for future human missions (approximate).
SITES = [
    ("Jezero crater (Perseverance)",   18.44,   77.45),
    ("Gale crater (Curiosity)",        -4.59,  137.44),
    ("Elysium Planitia (InSight)",      4.50,  135.62),
    ("Meridiani Planum (Opportunity)", -1.95,   -5.53),
    ("Gusev crater (Spirit)",         -14.57,  175.47),
    ("Chryse Planitia (Viking 1)",     22.27,  -47.95),
    ("Utopia Planitia (Viking 2)",     47.64,  134.29),
    ("Vastitas Borealis (Phoenix)",    68.22, -125.75),
    ("Arcadia Planitia (human candidate)", 40.0, -160.0),
]


# ---------------------------------------------------------------------------
# 1. Terrain (read a small square of the big elevation map over the internet)
# ---------------------------------------------------------------------------

def terrain_features(dem, lat, lon):
    deg_per_px = abs(dem.res[1])
    px_y = np.radians(deg_per_px) * MARS_RADIUS_M          # ~200 m
    px_x = px_y * np.cos(np.radians(lat))                  # narrower away from the equator
    half_r = int(np.ceil(RADIUS_KM * 1000 / px_y)) + 2
    half_c = int(np.ceil(RADIUS_KM * 1000 / px_x)) + 2
    row, col = dem.index(lon, lat)
    z = dem.read(1, window=Window(col - half_c, row - half_r, 2 * half_c + 1, 2 * half_r + 1)).astype(float)
    z[z == dem.nodata] = np.nan

    # Map pixels are 200 m north-south but narrower east-west away from the
    # equator; bring them to square 200 m pixels, like Earth and the Moon.
    z, _ = terrain_common.resample_to_200m(z, px_x, px_y)
    slope, rough = terrain_common.slope_and_roughness(z)

    dy_km, dx_km = terrain_common.pixel_offsets_km(z.shape)
    inside = np.hypot(dy_km, dx_km) <= RADIUS_KM
    return {"elev_m": np.nanmean(z[inside]), "slope_deg": np.nanmean(slope[inside]),
            "roughness": np.nanmean(rough[inside])}


# ---------------------------------------------------------------------------
# 2. Albedo
# ---------------------------------------------------------------------------

def albedo_feature(alb, values, lat, lon):
    """Mean of the 3 x 3 albedo pixels around the site (pixels are 7.4 km)."""
    deg = 360 / alb.width
    row, col = int((90 - lat) / deg), int((lon + 180) / deg) % alb.width
    part = values[max(row - 1, 0):row + 2, max(col - 1, 0):col + 2]
    return {"albedo": float(np.nanmean(np.where(part < 0, np.nan, part)))}


# ---------------------------------------------------------------------------
# 3. Temperature from the Mars Climate Database (season x hour table)
# ---------------------------------------------------------------------------

def mcd_table(name, lat, lon):
    """
    Surface temperature (K) for every season (rows: solar longitude Ls, 0-360)
    and every Martian hour (columns: 0-24). Asked once, then kept on disk.
    """
    folder = RAW / "mcd"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") + ".csv")
    if path.exists():
        return pd.read_csv(path, index_col=0)

    query = {"var1": "tsurf", "var2": "none", "var3": "none", "var4": "none", "datekeyhtml": 1,
             "ls": "all", "localtime": "all", "year": 2024, "month": 1, "day": 1, "hours": 0,
             "minutes": 0, "seconds": 0, "julian": 2460000, "martianyear": 37, "martianmonth": 1,
             "sol": 1, "latitude": lat, "longitude": lon, "altitude": 10, "zkey": 3,
             "isfixedlt": "off", "dust": 1, "hrkey": 1, "zonmean": "off", "averaging": "off",
             "dpi": 80, "islog": "off", "colorm": "jet", "minval": "", "maxval": "", "proj": "cyl",
             "plat": "", "plon": "", "trans": "", "iswind": "off", "latpoint": "", "lonpoint": ""}
    html = urllib.request.urlopen(MCD_URL + "?" + urllib.parse.urlencode(query), timeout=300).read().decode()
    link = re.search(r"href='(\.\./txt/[0-9a-f]+\.txt)'", html)
    if not link:
        raise RuntimeError(f"The Mars Climate Database gave no data for {name}.")
    text = urllib.request.urlopen(urllib.parse.urljoin(MCD_URL, link[1]), timeout=120).read().decode()

    hours, rows = None, {}
    for line in text.splitlines():
        if line.startswith("#") or "||" not in line:
            continue
        label, numbers = line.split("||")
        numbers = [float(v) for v in numbers.split()]
        if label.strip().startswith("-"):
            hours = [int(round(v)) for v in numbers]
        else:
            rows[int(label)] = numbers
    table = pd.DataFrame.from_dict(rows, orient="index", columns=[f"h{h:02d}" for h in hours])
    table.index.name = "Ls"
    table.to_csv(path)
    time.sleep(2)   # be polite with the free server
    return table


def temperature_features(table):
    values = table.iloc[:-1, :-1].to_numpy()   # drop Ls=360 and hour 24 (copies of 0)
    return {"temp_mean_K": values.mean(), "temp_range_K": values.max() - values.mean()}


# ---------------------------------------------------------------------------
# 4. Putting it together
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build Mars target rows.")
    parser.add_argument("--out", default="data/targets_mars.csv")
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    albedo_path = RAW / "tes_albedo_7410m.tif"
    if not albedo_path.exists():
        print("  downloading TES albedo map (17 MB) ...")
        urllib.request.urlretrieve(ALBEDO_URL, albedo_path)

    rows = []
    with rasterio.open(DEM_URL) as dem, rasterio.open(albedo_path) as alb:
        albedo_values = alb.read(1)
        for name, lat, lon in SITES:
            row = {"name": name, "body": "Mars", "site_lat": lat, "site_lon": lon,
                   "area": f"disk {RADIUS_KM:g} km"}
            row.update(terrain_features(dem, lat, lon))
            row.update(temperature_features(mcd_table(name, lat, lon)))
            row.update(albedo_feature(alb, albedo_values, lat, lon))
            row["precip_mm"] = 0.0
            row["ndvi"] = 0.0            # no plants
            row["em_contrast"] = np.nan  # rock type: not yet measured in the same way (left empty = not used)
            rows.append(row)
            print(f"  {name}: done")

    order = ["name", "body", "site_lat", "site_lon", "area", "elev_m", "slope_deg", "roughness",
             "temp_mean_K", "temp_range_K", "albedo", "precip_mm", "ndvi", "em_contrast"]
    table = pd.DataFrame(rows)[order].round({"elev_m": 1, "slope_deg": 2, "roughness": 2,
                                             "temp_mean_K": 2, "temp_range_K": 2, "albedo": 4})
    table.to_csv(args.out, index=False)
    print(f"\nSaved {len(table)} Mars sites to {args.out}\n")
    print(table.drop(columns=["site_lat", "site_lon", "area"]).to_string(index=False))


if __name__ == "__main__":
    main()
