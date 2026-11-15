"""
build_earth.py - Turn the downloaded NASA Earth files into data/earth.csv.

It reads what src/download_earth.py saved in data/raw/ and makes ONE table
with one row per Earth grid cell of 0.05 x 0.05 degrees (about 5.5 km).
That is the same grid that the MODIS temperature and albedo files use.

Columns (the same features that src/compare.py uses):
    elev_m        mean elevation of the cell (NASADEM, metres above sea level)
    slope_deg     mean terrain slope, measured between 200 m pixels
    roughness     mean local roughness: standard deviation of elevation in
                  a 3 x 3 window of 200 m pixels, in metres
                  (all bodies use 200 m pixels, see src/terrain_common.py)
    temp_mean_K   yearly mean land surface temperature, day and night (MOD11C3)
    temp_range_K  warmest monthly daytime temperature minus the yearly mean
                  (MOD11C3). Same definition as the Moon (Diviner max - mean).
    albedo        mean white-sky shortwave albedo, 15th of each month (MCD43C3)
    precip_mm     total precipitation in the year (GPM IMERG monthly)
    ndvi          vegetation index, mean of 4 months, one per season (MOD13C2).
                  About 0 or below = no plants (rock, sand, ice); 0.2 = sparse
                  shrubs; above 0.5 = dense vegetation. MODIS does not cover
                  Antarctica, so there it is set to 0 (almost no plants).
    em_contrast   rock type from thermal emissivity (ASTER GED): emissivity at
                  10.6-11.3 um minus emissivity at 8.3-9.1 um. Silica-rich rock
                  (quartz sand, granite) gives a big contrast (~0.1 or more);
                  basalt and other dark volcanic rock give a small one (~0.02).
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
import rasterio
from pyhdf.SD import SD, SDC

sys.path.insert(0, str(Path(__file__).parent))
import terrain_common  # noqa: E402  (same 200 m terrain for every body)

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


def tile_corner(path):
    """South-west corner of a tile from its file name (n00w080 or N75_00_W090_00)."""
    m = re.search(r"([ns])(\d{2})(?:_00)?_?([ew])(\d{3})", path.name.lower())
    lat_s = int(m[2]) * (1 if m[1] == "n" else -1)
    lon_w = int(m[4]) * (1 if m[3] == "e" else -1)
    return lat_s, lon_w


def read_nasadem_90m(path):
    """NASADEM tile averaged to ~90 m (1200 x 1200) + water share per pixel."""
    height, water = read_tile(path)
    height, water = height[:3600, :3600], water[:3600, :3600]  # drop the shared edge
    return block_mean(height, DEM_STEP), block_mean(water.astype(float), DEM_STEP)


def read_cop90(path):
    """
    Copernicus GLO-90 tile: 1200 rows of 3 arc-seconds. Far from the equator
    it has fewer columns (e.g. 400 at 70-80 degrees), so each pixel stays ~90 m
    wide. The sea is stored as exactly 0 m, which we use as the water mask.
    """
    with rasterio.open(path) as src:
        z = src.read(1).astype(float)
    if src.nodata is not None:
        z[z == src.nodata] = np.nan
    return z, (z == 0).astype(float)


def terrain_for_tile(path, source):
    """
    Terrain features of one 1 x 1 degree tile, averaged to the 0.05 degree
    grid: returns (lat_south, lon_west, dict of 20 x 20 arrays).
    The tile is first brought to 200 m pixels (src/terrain_common.py), the
    same pixel size used for the Moon and Mars.
    """
    lat_s, lon_w = tile_corner(path)
    z, water = read_nasadem_90m(path) if source == "nasadem" else read_cop90(path)
    rows, cols = z.shape

    # Native pixel size in metres (pixels get narrower away from the equator).
    px_y = (3600 / rows) * M_PER_ARCSEC
    px_x = (3600 / cols) * M_PER_ARCSEC * np.cos(np.radians(lat_s + 0.5))

    z200, _ = terrain_common.resample_to_200m(z, px_x, px_y)
    water200, _ = terrain_common.resample_to_200m(water, px_x, px_y)
    slope, rough = terrain_common.slope_and_roughness(z200)

    # Terrain averages use land pixels only.
    land = water200 <= 0.5
    layers = {"elev_m": np.where(land, z200, np.nan), "slope_deg": np.where(land, slope, np.nan),
              "roughness": np.where(land, rough, np.nan), "water_frac": water200}

    # Every 200 m pixel belongs to one of the 20 x 20 cells of 0.05 degrees.
    r200, c200 = z200.shape
    cell_r = np.minimum((np.arange(r200) * 20) // r200, 19)
    cell_c = np.minimum((np.arange(c200) * 20) // c200, 19)
    cell_id = (cell_r[:, None] * 20 + cell_c[None, :]).ravel()
    out = {}
    for key, values in layers.items():
        v = values.ravel()
        ok = np.isfinite(v)
        total = np.bincount(cell_id[ok], weights=v[ok], minlength=400)
        count = np.bincount(cell_id[ok], minlength=400)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[key] = (total / count).reshape(20, 20)
    return lat_s, lon_w, out


def terrain(grid, source="nasadem"):
    """Put the terrain of every downloaded tile that touches the region into the grid."""
    r0, r1, c0, c1 = grid
    shape = (r1 - r0, c1 - c0)
    result = {k: np.full(shape, np.nan) for k in ("elev_m", "slope_deg", "roughness", "water_frac")}
    folder, pattern = ("NASADEM_HGT", "*.zip") if source == "nasadem" else ("COP90", "*.tif")
    north, west = 90 - r0 * CELL, -180 + c0 * CELL
    south, east = 90 - r1 * CELL, -180 + c1 * CELL
    tiles = [t for t in sorted((RAW / folder).glob(pattern))
             if south < tile_corner(t)[0] + 1 and tile_corner(t)[0] < north
             and west < tile_corner(t)[1] + 1 and tile_corner(t)[1] < east]
    if not tiles:
        sys.exit(f"No {folder} tiles for this region in data/raw/{folder}. "
                 "Run src/download_earth.py first.")

    per_deg = int(round(1 / CELL))  # 20 cells per degree
    for i, path in enumerate(tiles, 1):
        lat_s, lon_w, out = terrain_for_tile(path, source)
        row = int(round((90 - (lat_s + 1)) / CELL)) - r0   # tile's north edge
        col = int(round((lon_w + 180) / CELL)) - c0
        # Part of the tile that falls inside the region.
        rs, re_ = max(row, 0), min(row + per_deg, shape[0])
        cs, ce = max(col, 0), min(col + per_deg, shape[1])
        if rs < re_ and cs < ce:
            for key, values in out.items():
                result[key][rs:re_, cs:ce] = values[rs - row:re_ - row, cs - col:ce - col]
        print(f"\r  {folder} tiles: {i}/{len(tiles)}", end="", flush=True)
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


def vegetation(grid):
    """
    Mean NDVI of the downloaded months (MOD13C2). Note: this product stores
    NDVI as raw / 10000 (it DIVIDES by its scale factor), unlike the
    temperature and albedo files, so we do not use read_hdf4 here.
    """
    r0, r1, c0, c1 = grid
    files = sorted((RAW / "MOD13C2").glob("*.hdf"))
    if not files:
        sys.exit("No MOD13C2 files in data/raw/MOD13C2.")
    stack = []
    for f in files:
        layer = SD(str(f), SDC.READ).select("CMG 0.05 Deg Monthly NDVI")
        raw = layer[r0:r1, c0:c1].astype(float)
        raw[(raw < -2000) | (raw > 10000)] = np.nan   # -3000 = no data
        stack.append(raw / 10000)
    ndvi = quiet_nan(np.nanmean, np.stack(stack))
    # MOD13C2 has no data south of about 60 S. Antarctica has almost no
    # plants (a few mosses and lichens), so there we use 0 instead of empty.
    lats = 90 - CELL * (np.arange(r0, r1) + 0.5)
    ndvi[(lats < -60)[:, None] & np.isnan(ndvi)] = 0.0
    return {"ndvi": ndvi}


def rock(grid):
    """
    Emissivity contrast from ASTER GED (5 thermal bands: 10, 11, 12, 13, 14).
    Mean of the downloaded files (January and July 2015).
    """
    r0, r1, c0, c1 = grid
    files = sorted((RAW / "AG5KMMOH").glob("*.h5"))
    if not files:
        sys.exit("No ASTER GED files in data/raw/AG5KMMOH.")
    values = []
    for f in files:
        with h5py.File(f) as h:
            raw = h["SDS/Emissivity"][:, r0:r1, c0:c1].astype(float)
        raw[raw == 0] = np.nan                         # 0 = no data
        em = raw * 0.002 + 0.49
        values.append(np.nanmean(em[3:5], axis=0) - np.nanmean(em[0:3], axis=0))
    return {"em_contrast": quiet_nan(np.nanmean, np.stack(values))}


def surface_layers(grid, lat, lon):
    """Every layer that is NOT terrain: all of them come from global files."""
    layers = {}
    print("  temperature (MOD11C3) ..."); layers.update(temperature(grid))
    print("  albedo (MCD43C3) ...");      layers.update(albedo(grid))
    print("  precipitation (GPM) ...");   layers.update(precipitation(lat, lon))
    print("  vegetation (MOD13C2) ...");  layers.update(vegetation(grid))
    print("  rock type (ASTER GED) ..."); layers.update(rock(grid))
    return layers


SURFACE = ["temp_mean_K", "temp_range_K", "albedo", "precip_mm", "ndvi", "em_contrast"]
ROUNDING = {"elev_m": 1, "slope_deg": 2, "roughness": 2, "temp_mean_K": 2, "temp_range_K": 2,
            "albedo": 4, "precip_mm": 1, "water_frac": 3, "ndvi": 3, "em_contrast": 4}


def refresh_surface(path):
    """
    Recompute the non-terrain columns of an existing region file, without
    redoing the (slow) terrain. Used when a new global variable is added.
    """
    table = pd.read_csv(path)
    lat_min, lat_max = table["lat"].min(), table["lat"].max()
    lon_min, lon_max = table["lon"].min(), table["lon"].max()
    grid = make_grid(lon_min - CELL / 2, lat_min - CELL / 2, lon_max + CELL / 2, lat_max + CELL / 2)
    lat, lon = cell_centres(*grid)
    layers = surface_layers(grid, lat, lon)
    r0, _, c0, _ = grid
    rows = np.round((90 - table["lat"]) / CELL - 0.5).astype(int) - r0
    cols = np.round((table["lon"] + 180) / CELL - 0.5).astype(int) - c0
    for key in SURFACE:
        table[key] = layers[key][rows, cols]
    order = [c for c in table.columns if c != "water_frac"] + ["water_frac"]
    table[order].round(ROUNDING).to_csv(path, index=False)
    return table


# ---------------------------------------------------------------------------
# 4. Putting it together
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build data/earth.csv from the NASA downloads.")
    parser.add_argument("--region", nargs=4, type=float, required=True,
                        metavar=("WEST", "SOUTH", "EAST", "NORTH"))
    parser.add_argument("--out", default="data/earth.csv")
    parser.add_argument("--dem", choices=["nasadem", "cop90"], default="nasadem",
                        help="Elevation source: nasadem (60N-56S) or cop90 (Copernicus, whole Earth)")
    parser.add_argument("--name", help="Region name to write in a 'region' column, e.g. atacama")
    parser.add_argument("--max-water", type=float, default=0.5,
                        help="Leave out cells with more water than this share (default 0.5)")
    args = parser.parse_args()

    grid = make_grid(*args.region)
    lat, lon = cell_centres(*grid)
    print(f"Grid: {lat.size:,} cells of {CELL} degrees")

    layers = {}
    layers.update(terrain(grid, args.dem))
    layers.update(surface_layers(grid, lat, lon))

    table = pd.DataFrame({"lat": lat.ravel().round(3), "lon": lon.ravel().round(3)})
    if args.name:
        table.insert(0, "region", args.name)
    for key in ["elev_m", "slope_deg", "roughness"] + SURFACE + ["water_frac"]:
        table[key] = layers[key].ravel()

    # Keep land cells that have terrain data.
    keep = table["elev_m"].notna() & (table["water_frac"].fillna(1) <= args.max_water)
    table = table[keep].round(ROUNDING)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)

    print(f"\nSaved {len(table):,} land cells to {args.out}")
    print(table.describe().loc[["min", "50%", "max"]].round(2).to_string())


if __name__ == "__main__":
    main()
