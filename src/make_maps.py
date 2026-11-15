"""
make_maps.py - Draw relief maps of each Earth place and its twin on the Moon or Mars.

For every Moon/Mars site it takes its best LITTLE-KNOWN Earth places, each
from a different region (3 by default), and saves separate images in maps/:

    maps/07_mars_jezero_crater_B_mars.png                       <- the Mars site
    maps/07_mars_jezero_crater_A1_earth_north_greenland.png     <- best Earth analog
    maps/07_mars_jezero_crater_A2_earth_egypt_western_desert.png
    maps/07_mars_jezero_crater_A3_earth_fezzan_libya.png

Same number = same Moon/Mars site. "B" is the site, "A1, A2, A3" its Earth
analogs from best to third best. maps/index.csv lists every pair. Both images
show a square of the SAME size in km, so the relief can be compared directly.

Each image is a shaded relief (elevation colours + shadows) at 200 m pixels
(the same as the database, see src/terrain_common.py), made from:
    Earth: Copernicus DEM 90 m (data/raw/COP90) or NASADEM (data/raw/NASADEM_HGT)
    Moon:  LOLA 80 m south pole map (data/raw/moon)
    Mars:  HRSC + MOLA 200 m (read over the internet, only the small square)

Example:
    python src/make_maps.py
"""

import argparse
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # draw to files, no window
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import LightSource
from pyproj import CRS, Transformer
from rasterio.merge import merge
from rasterio.windows import Window

sys.path.insert(0, str(Path(__file__).parent))
import terrain_common  # noqa: E402

RAW = Path("data/raw")
MARS_DEM = ("/vsicurl/https://planetarymaps.usgs.gov/mosaic/Mars/HRSC_MOLA_Blend/"
            "Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif")
MOON_DEM = RAW / "moon" / "ldem_80s_80m_float.lbl"
MOON_LONLAT = CRS.from_proj4("+proj=longlat +R=1737400 +no_defs")
MARS_RADIUS_M = 3396190.0
EARTH_M_PER_DEG = 111320.0


def slug(text):
    """'Jezero crater (Perseverance)' -> 'jezero_crater'"""
    text = re.sub(r"\(.*?\)", "", text.lower())
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def box_km(area):
    """Size of the square to draw, from the target's 'area' text (e.g. 'rim 20.92 km')."""
    shape, size = area.split()[0], float(area.split()[1])
    return max(1.5 * size, 20.0) if shape == "rim" else max(4 * size, 20.0)


# ---------------------------------------------------------------------------
# 1. Reading a square of elevation (returns metres, and pixel size in metres)
# ---------------------------------------------------------------------------

def earth_square(lat, lon, size_km, region_dem):
    half_lat = size_km / 2 * 1000 / EARTH_M_PER_DEG
    half_lon = half_lat / np.cos(np.radians(lat))
    west, east, south, north = lon - half_lon, lon + half_lon, lat - half_lat, lat + half_lat
    tiles = []
    for t_lat in range(int(np.floor(south)), int(np.floor(north)) + 1):
        for t_lon in range(int(np.floor(west)), int(np.floor(east)) + 1):
            ns, ew = ("N" if t_lat >= 0 else "S"), ("E" if t_lon >= 0 else "W")
            if region_dem == "nasadem":
                name = f"{ns.lower()}{abs(t_lat):02d}{ew.lower()}{abs(t_lon):03d}"
                path = RAW / "NASADEM_HGT" / f"NASADEM_HGT_{name}.zip"
                if path.exists():
                    tiles.append(f"/vsizip/{path}/{name}.hgt")
            else:
                path = RAW / "COP90" / f"{ns}{abs(t_lat):02d}_00_{ew}{abs(t_lon):03d}_00.tif"
                if path.exists():
                    tiles.append(str(path))
    if not tiles:
        raise FileNotFoundError(f"No elevation tiles for {lat}, {lon}")
    sources = [rasterio.open(t) for t in tiles]
    z, transform = merge(sources, bounds=(west, south, east, north), nodata=-32768)
    for s in sources:
        s.close()
    z = z[0].astype(float)
    z[z <= -32768] = np.nan
    px_y = abs(transform.e) * EARTH_M_PER_DEG
    px_x = transform.a * EARTH_M_PER_DEG * np.cos(np.radians(lat))
    return z, px_x, px_y


def moon_square(lat, lon, size_km):
    with rasterio.open(MOON_DEM) as dem:
        x, y = Transformer.from_crs(MOON_LONLAT, dem.crs, always_xy=True).transform(lon, lat)
        row, col = dem.index(x, y)
        half = int(size_km / 2 * 1000 / abs(dem.res[0]))
        z = dem.read(1, window=Window(col - half, row - half, 2 * half, 2 * half)).astype(float)
        px = abs(dem.res[0])
    z[(z < -1e30) | (z > 1e30)] = np.nan
    return z * 1000, px, px          # km -> m


def mars_square(lat, lon, size_km):
    with rasterio.open(MARS_DEM) as dem:
        px_y = np.radians(abs(dem.res[1])) * MARS_RADIUS_M
        px_x = px_y * np.cos(np.radians(lat))
        half_r = int(size_km / 2 * 1000 / px_y)
        half_c = int(size_km / 2 * 1000 / px_x)
        row, col = dem.index(lon, lat)
        z = dem.read(1, window=Window(col - half_c, row - half_r, 2 * half_c, 2 * half_r)).astype(float)
        z[z == dem.nodata] = np.nan
    return z, px_x, px_y


# ---------------------------------------------------------------------------
# 2. Drawing
# ---------------------------------------------------------------------------

def draw(z, px_x, px_y, title, subtitle, footer, path):
    """Shaded relief with a km grid, a colour bar and a short text."""
    # Same 200 m pixels as the database, so both images of a pair show the
    # terrain with exactly the same level of detail.
    z, _ = terrain_common.resample_to_200m(z, px_x, px_y)
    px_x = px_y = terrain_common.PIXEL_M
    empty = np.isnan(z)
    z = np.where(empty, np.nanmin(z), z)
    rows, cols = z.shape
    extent = [-cols * px_x / 2000, cols * px_x / 2000, -rows * px_y / 2000, rows * px_y / 2000]
    light = LightSource(azdeg=315, altdeg=45)
    rgb = light.shade(z, cmap=plt.cm.terrain, vert_exag=2, blend_mode="soft", dx=px_x, dy=px_y)
    rgb[empty, :3] = 0.85          # light grey = no elevation data (outside downloaded tiles)

    fig, ax = plt.subplots(figsize=(8, 8.6), dpi=150)
    ax.imshow(rgb, extent=extent, origin="upper")
    mappable = plt.cm.ScalarMappable(cmap=plt.cm.terrain,
                                     norm=plt.Normalize(np.nanmin(z), np.nanmax(z)))
    bar = fig.colorbar(mappable, ax=ax, fraction=0.04, pad=0.02)
    bar.set_label("Elevation (m)")
    ax.plot(0, 0, marker="+", color="red", markersize=14, mew=2)   # the exact place
    ax.set_xlabel("km (west - east)")
    ax.set_ylabel("km (south - north)")
    ax.set_title(f"{title}\n{subtitle}", fontsize=11)
    fig.text(0.5, 0.015, footer, ha="center", fontsize=8.5, wrap=True)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path)
    plt.close(fig)


def fmt(value, unit, digits=0):
    return "-" if pd.isna(value) else f"{value:.{digits}f} {unit}".strip()


def best_places(pairs_file, per_target, earth_file, targets_file):
    """
    For every Moon/Mars site, the best little-known place of each of its
    'per_target' best regions (so the maps show DIFFERENT parts of the world,
    not 15 neighbours of the same place).
    """
    import compare   # noqa: E402  (same comparison as make_results.py)
    from make_results import WEIGHTS   # noqa: E402  (same weights, incl. rock composition)
    earth, targets = compare.load_inputs(earth_file, targets_file)
    earth = earth[earth["known"] != "yes"].reset_index(drop=True)
    results = compare.compare_all(earth, targets, weights=WEIGHTS)
    best = (results.sort_values("score", ascending=False)
            .groupby(["target", "region"], sort=False).first().reset_index())
    best = best.sort_values(["target", "score"], ascending=[True, False])
    best["option"] = best.groupby("target").cumcount() + 1
    order = list(dict.fromkeys(targets["name"]))          # keep the order of targets.csv
    best = best[best["option"] <= per_target]
    best["t_order"] = best["target"].map({name: i for i, name in enumerate(order)})
    return best.sort_values(["t_order", "option"]).reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Relief maps of Earth analogs and their Moon/Mars twins.")
    parser.add_argument("--earth", default="data/earth_all.csv")
    parser.add_argument("--targets", default="data/targets.csv")
    parser.add_argument("--catalog", default="data/regions_catalog.csv")
    parser.add_argument("--per-target", type=int, default=3,
                        help="How many Earth places (each from a different region) per Moon/Mars site")
    parser.add_argument("--out", default="maps")
    args = parser.parse_args()

    targets = pd.read_csv(args.targets).set_index("name")
    dem_of = pd.read_csv(args.catalog, comment="#").set_index("name")["dem"]
    out = Path(args.out)
    out.mkdir(exist_ok=True)

    places = best_places(None, args.per_target, args.earth, args.targets)
    index_rows = []
    for number, (name, group) in enumerate(places.groupby("t_order", sort=True), 1):
        n = f"{number:02d}"
        first = group.iloc[0]
        body = first["body"].lower()
        target = targets.loc[first["target"]]
        size = box_km(target["area"])
        base = f"{n}_{body}_{slug(first['target'])}"

        # B: the Moon or Mars site (one image, shared by all its Earth analogs)
        twin_file = out / f"{base}_B_{body}.png"
        if body == "moon":
            z, px_x, px_y = moon_square(target["site_lat"], target["site_lon"], size)
        else:
            z, px_x, px_y = mars_square(target["site_lat"], target["site_lon"], size)
        analogs = ", ".join(r.replace("_", " ") for r in group["region"])
        draw(z, px_x, px_y,
             f"{n} - B: {first['body'].upper()}, {first['target']}",
             f"lat {target['site_lat']:.2f}, lon {target['site_lon']:.2f}  |  square of {size:.0f} km",
             f"Earth analogs (images {n}_..._A1 to A{len(group)}): {analogs}. "
             f"Mean temp {fmt(target['temp_mean_K'], 'K')}, slope {fmt(target['slope_deg'], 'deg', 1)}, "
             f"albedo {fmt(target['albedo'], '', 2)}.",
             twin_file)

        # A1, A2, ...: the Earth places, same size of square
        for _, row in group.iterrows():
            a = f"A{int(row['option'])}"
            earth_file = out / f"{base}_{a}_earth_{row['region']}.png"
            z, px_x, px_y = earth_square(row["lat"], row["lon"], size, dem_of.get(row["region"], "cop90"))
            draw(z, px_x, px_y,
                 f"{n} - {a}: EARTH, {row['region'].replace('_', ' ')}",
                 f"lat {row['lat']:.3f}, lon {row['lon']:.3f}  |  square of {size:.0f} km",
                 f"Analog of {row['target']} ({row['body']}, image {twin_file.name}). Score {row['score']:.3f}. "
                 f"Mean temp {fmt(row['temp_mean_K'], 'K')}, slope {fmt(row['slope_deg'], 'deg', 1)}, "
                 f"albedo {fmt(row['albedo'], '', 2)}, rain {fmt(row['precip_mm'], 'mm/yr')}, "
                 f"NDVI {fmt(row['ndvi'], '', 2)}. Weakest match: {row['worst_match']}.",
                 earth_file)
            index_rows.append({"number": n, "earth_option": a, "body": row["body"], "target": row["target"],
                               "target_lat": target["site_lat"], "target_lon": target["site_lon"],
                               "earth_region": row["region"], "earth_lat": row["lat"],
                               "earth_lon": row["lon"], "score": round(row["score"], 4),
                               "worst_match": row["worst_match"],
                               "image_earth": earth_file.name, "image_twin": twin_file.name})
            print(f"  {earth_file.name}  <->  {twin_file.name}")

    pd.DataFrame(index_rows).to_csv(out / "index.csv", index=False)
    n_twins = places["target"].nunique()
    print(f"\nSaved {len(index_rows)} Earth images + {n_twins} Moon/Mars images, and {out / 'index.csv'}")


if __name__ == "__main__":
    main()
