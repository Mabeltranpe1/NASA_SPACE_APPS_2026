"""
build_earth.py - Turn the downloaded NASA Earth files into data/earth.csv.

It reads what src/download_earth.py saved in data/raw/ and makes ONE table
with one row per Earth grid cell of 0.05 x 0.05 degrees (about 5.5 km).
That is the same grid that the MODIS temperature and albedo files use.

Columns (the same features that src/compare.py uses):
    elev_m        mean elevation of the cell (NASADEM, metres above sea level)
    slope_deg     mean terrain slope, measured at ~90 m pixels (NASADEM)
    roughness     mean local roughness: standard deviation of elevation in
                  a 3 x 3 window of ~90 m pixels, in metres (NASADEM)
    temp_mean_K   yearly mean land surface temperature, day and night (MOD11C3)
    temp_range_K  warmest monthly daytime temperature minus the yearly mean
                  (MOD11C3). Same definition as the Moon (Diviner max - mean).
    albedo        mean white-sky shortwave albedo, 15th of each month (MCD43C3)
    precip_mm     total precipitation in the year (GPM IMERG monthly)
    water_frac    share of the cell covered by water (NASADEM water mask)

Cells that are mostly water (sea, big lakes) are left out.

Example:
    python src/build_earth.py --region -80 -5 -66 13
"""

import argparse
import calendar
import re
import sys
import warnings
import zipfile
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from pyhdf.SD import SD, SDC
from scipy.ndimage import uniform_filter

RAW = Path("data/raw")
CELL = 0.05             # grid cell size in degrees (MODIS CMG grid)
DEM_STEP = 3            # average 3 x 3 NASADEM pixels: 1 arc-second (~30 m) -> ~90 m
M_PER_ARCSEC = 30.87    # metres per arc-second of latitude on Earth


# ---------------------------------------------------------------------------
# 1. The grid
# ---------------------------------------------------------------------------

def make_grid(west, south, east, north):
    """
    Row and column numbers of the global 0.05 degree grid inside the region.
    Row 0 is at latitude 90 (north), column 0 at longitude -180 (west).
    """
    r0, r1 = int(round((90 - north) / CELL)), int(round((90 - south) / CELL))
    c0, c1 = int(round((west + 180) / CELL)), int(round((east + 180) / CELL))
    return r0, r1, c0, c1


def cell_centres(r0, r1, c0, c1):
    """Latitude and longitude of the centre of every cell (2D arrays)."""
    lats = 90 - CELL * (np.arange(r0, r1) + 0.5)
    lons = -180 + CELL * (np.arange(c0, c1) + 0.5)
    return np.meshgrid(lats, lons, indexing="ij")


# ---------------------------------------------------------------------------
# 2. Terrain from NASADEM: elevation, slope, roughness, water
# ---------------------------------------------------------------------------

def read_tile(path):
    """Read one NASADEM zip: elevation (m) and water mask, 3601 x 3601 pixels."""
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.endswith(".hgt"))
        height = np.frombuffer(z.read(name), ">i2").reshape(3601, 3601).astype(float)
        water = np.frombuffer(z.read(name[:-4] + ".swb"), "u1").reshape(3601, 3601) > 0
    height[height == -32768] = np.nan  # -32768 means "no data"
    return height, water


def block_mean(a, size):
    """Average non-overlapping size x size blocks of a 2D array (ignores NaN)."""
    rows, cols = a.shape[0] // size, a.shape[1] // size
    blocks = a[:rows * size, :cols * size].reshape(rows, size, cols, size)
    return quiet_nan(np.nanmean, blocks, axis=(1, 3))


def terrain_for_tile(path):
    """
    Terrain features of one 1 x 1 degree tile, already averaged to the
    0.05 degree grid: returns (lat_south, lon_west, dict of 20 x 20 arrays).
    """
    match = re.search(r"([ns])(\d{2})([ew])(\d{3})", path.name.lower())
    lat_s = int(match[2]) * (1 if match[1] == "n" else -1)
    lon_w = int(match[4]) * (1 if match[3] == "e" else -1)

    height, water = read_tile(path)
    height, water = height[:3600, :3600], water[:3600, :3600]  # drop the shared edge

    # ~90 m pixels: smoother and closer to the 80 m Moon map (LOLA).
    z = block_mean(height, DEM_STEP)
    px_y = DEM_STEP * M_PER_ARCSEC
    px_x = px_y * np.cos(np.radians(lat_s + 0.5))   # pixels get narrower away from the equator

    dz_dy, dz_dx = np.gradient(z, px_y, px_x)
    slope = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))

    # Roughness = standard deviation of elevation in a 3 x 3 window.
    zf = np.nan_to_num(z, nan=np.nanmean(z) if np.isfinite(z).any() else 0.0)
    mean = uniform_filter(zf, 3)
    rough = np.sqrt(np.clip(uniform_filter(zf**2, 3) - mean**2, 0, None))
    rough[np.isnan(z)] = np.nan

    per_cell = int(round(CELL * 3600 / DEM_STEP))   # 60 pixels of ~90 m per 0.05 degrees
    land = ~water
    # Use land pixels only for the terrain averages.
    out = {
        "elev_m": block_mean(np.where(land, height, np.nan), int(CELL * 3600)),
        "slope_deg": block_mean(np.where(block_mean(land.astype(float), DEM_STEP) > 0.5, slope, np.nan), per_cell),
        "roughness": block_mean(np.where(block_mean(land.astype(float), DEM_STEP) > 0.5, rough, np.nan), per_cell),
        "water_frac": block_mean(water.astype(float), int(CELL * 3600)),
    }
    return lat_s, lon_w, out


def terrain(grid):
    """Put the terrain of every downloaded tile into the region grid."""
    r0, r1, c0, c1 = grid
    shape = (r1 - r0, c1 - c0)
    result = {k: np.full(shape, np.nan) for k in ("elev_m", "slope_deg", "roughness", "water_frac")}
    tiles = sorted((RAW / "NASADEM_HGT").glob("*.zip"))
    if not tiles:
        sys.exit("No NASADEM tiles in data/raw/NASADEM_HGT. Run src/download_earth.py first.")

    per_deg = int(round(1 / CELL))  # 20 cells per degree
    for i, path in enumerate(tiles, 1):
        lat_s, lon_w, out = terrain_for_tile(path)
        row = int(round((90 - (lat_s + 1)) / CELL)) - r0   # tile's north edge
        col = int(round((lon_w + 180) / CELL)) - c0
        # Part of the tile that falls inside the region.
        rs, re_ = max(row, 0), min(row + per_deg, shape[0])
        cs, ce = max(col, 0), min(col + per_deg, shape[1])
        if rs < re_ and cs < ce:
            for key, values in out.items():
                result[key][rs:re_, cs:ce] = values[rs - row:re_ - row, cs - col:ce - col]
        print(f"\r  NASADEM tiles: {i}/{len(tiles)}", end="", flush=True)
    print()
    return result


# ---------------------------------------------------------------------------
# 3. Temperature (MOD11C3), albedo (MCD43C3), precipitation (GPM IMERG)
# ---------------------------------------------------------------------------

def read_hdf4(path, name, grid):
    """Read one MODIS layer for the region and apply its scale factor."""
    r0, r1, c0, c1 = grid
    layer = SD(str(path), SDC.READ).select(name)
    attrs = layer.attributes()
    raw = layer[r0:r1, c0:c1].astype(float)
    raw[raw == attrs["_FillValue"]] = np.nan
    low, high = attrs["valid_range"]
    raw[(raw < low) | (raw > high)] = np.nan
    return raw * attrs.get("scale_factor", 1.0) + attrs.get("add_offset", 0.0)


def quiet_nan(func, stack, axis=0):
    """nanmean / nanmax without warnings for cells that have no data at all."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return func(stack, axis=axis)


def temperature(grid):
    files = sorted((RAW / "MOD11C3").glob("*.hdf"))
    if not files:
        sys.exit("No MOD11C3 files in data/raw/MOD11C3.")
    day = np.stack([read_hdf4(f, "LST_Day_CMG", grid) for f in files])
    night = np.stack([read_hdf4(f, "LST_Night_CMG", grid) for f in files])
    mean = quiet_nan(np.nanmean, np.concatenate([day, night]))
    return {"temp_mean_K": mean, "temp_range_K": quiet_nan(np.nanmax, day) - mean}


def albedo(grid):
    files = sorted((RAW / "MCD43C3").glob("*.hdf"))
    if not files:
        sys.exit("No MCD43C3 files in data/raw/MCD43C3.")
    stack = np.stack([read_hdf4(f, "Albedo_WSA_shortwave", grid) for f in files])
    return {"albedo": quiet_nan(np.nanmean, stack)}


def precipitation(lat, lon):
    """Yearly total in mm. IMERG gives a mean rate in mm/hour for each month."""
    files = sorted((RAW / "GPM_3IMERGM").glob("*.HDF5"))
    if len(files) != 12:
        print(f"  WARNING: found {len(files)} GPM files instead of 12; precip_mm will be wrong.")
    # IMERG grid is 0.1 degrees, arranged [lon, lat] from -180 and -90.
    i_lon = np.clip(((lon + 180) / 0.1).astype(int), 0, 3599)
    i_lat = np.clip(((lat + 90) / 0.1).astype(int), 0, 1799)
    total = np.zeros(lat.shape)
    for f in files:
        with h5py.File(f) as h:
            rate = h["Grid/precipitation"][0]                 # mm/hour
            month = re.search(r"\.(\d{4})(\d{2})01-", f.name)
            hours = 24 * calendar.monthrange(int(month[1]), int(month[2]))[1]
            values = rate[i_lon, i_lat].astype(float)
            values[values < 0] = np.nan                       # negative = no data
            total += values * hours
    return {"precip_mm": total}


# ---------------------------------------------------------------------------
# 4. Putting it together
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build data/earth.csv from the NASA downloads.")
    parser.add_argument("--region", nargs=4, type=float, required=True,
                        metavar=("WEST", "SOUTH", "EAST", "NORTH"))
    parser.add_argument("--out", default="data/earth.csv")
    parser.add_argument("--max-water", type=float, default=0.5,
                        help="Leave out cells with more water than this share (default 0.5)")
    args = parser.parse_args()

    grid = make_grid(*args.region)
    lat, lon = cell_centres(*grid)
    print(f"Grid: {lat.size:,} cells of {CELL} degrees")

    layers = {}
    layers.update(terrain(grid))
    print("  temperature (MOD11C3) ..."); layers.update(temperature(grid))
    print("  albedo (MCD43C3) ...");      layers.update(albedo(grid))
    print("  precipitation (GPM) ...");   layers.update(precipitation(lat, lon))

    table = pd.DataFrame({"lat": lat.ravel().round(3), "lon": lon.ravel().round(3)})
    for key in ("elev_m", "slope_deg", "roughness", "temp_mean_K", "temp_range_K",
                "albedo", "precip_mm", "water_frac"):
        table[key] = layers[key].ravel()

    # Keep land cells that have terrain data.
    keep = table["elev_m"].notna() & (table["water_frac"].fillna(1) <= args.max_water)
    table = table[keep].round({"elev_m": 1, "slope_deg": 2, "roughness": 2, "temp_mean_K": 2,
                               "temp_range_K": 2, "albedo": 4, "precip_mm": 1, "water_frac": 3})
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)

    print(f"\nSaved {len(table):,} land cells to {args.out}")
    print(table.describe().loc[["min", "50%", "max"]].round(2).to_string())


if __name__ == "__main__":
    main()
