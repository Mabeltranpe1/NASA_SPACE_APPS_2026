"""
screen_global.py - Look at the WHOLE Earth to discover new analog areas.

Why: if we choose regions by hand we only find places we already know.
This script scores every land cell of the planet (0.05 degrees, ~5.5 km),
using only the files that are already global:
    temperature (MOD11C3), albedo (MCD43C3), precipitation (GPM IMERG)
    and vegetation (MOD13C2).
Terrain (slope, roughness) is NOT used here, because the elevation data is
too big for the whole planet. So this is a first filter by CLIMATE and
SURFACE. The best areas it finds are then studied in detail with
src/build_database.py (which adds the terrain).

For each body (Moon, Mars) it:
    1. scores every land cell against every target site (same maths and
       tolerances as src/compare.py) and keeps the mean score,
    2. groups the best cells into areas of 2 x 2 degrees,
    3. marks the areas that are already famous analogs (so you can skip them),
    4. writes the best areas to data/discovery_<body>.csv, with a ready
       "west south east north" box to add to data/regions_catalog.csv.

Example:
    python src/screen_global.py --targets data/targets.csv
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import build_earth   # we reuse its readers  # noqa: E402
import compare       # and the tolerances and weights  # noqa: E402

USED = ["temp_mean_K", "temp_range_K", "albedo", "precip_mm", "ndvi"]   # global features
AREA_DEG = 2.0           # size of the areas we group cells into
BAND = 30                # degrees of latitude processed at a time (saves memory)

# Famous analog sites (lat, lon, name). An area within ~3 degrees of one of
# these is marked as "known", so the list of NEW candidates is easy to read.
KNOWN = [
    (-77.5, 162.0, "McMurdo Dry Valleys"), (75.4, -89.7, "Devon Island / Haughton"),
    (-24.0, -69.0, "Atacama"), (38.4, -110.8, "Utah MDRS"), (19.8, -155.5, "Mauna Kea / HI-SEAS"),
    (64.8, -17.5, "Iceland highlands"), (78.5, 15.5, "Svalbard"), (36.2, -116.8, "Death Valley / Mojave"),
    (37.7, -6.6, "Rio Tinto"), (28.3, -16.6, "Teide"), (29.0, -13.7, "Lanzarote"),
    (35.2, -111.6, "Arizona craters / Flagstaff"), (43.4, -113.5, "Craters of the Moon, Idaho"),
    (-23.8, 133.0, "Central Australia"), (79.4, -90.8, "Axel Heiberg"), (31.0, -4.0, "Morocco Erfoud / Ibn Battuta"),
    (38.0, 92.0, "Qaidam basin"), (14.2, 40.3, "Danakil / Dallol"), (-75.1, 123.3, "Concordia, Dome C"),
    (-72.0, 2.5, "Antarctic stations, Dronning Maud Land"), (30.6, 34.8, "Negev / Ramon crater"),
    (-24.5, 15.2, "Namib"), (34.2, 77.8, "Ladakh"), (-21.5, 118.5, "Pilbara"), (13.5, 41.0, "Afar"),
    (64.0, -16.0, "Vatnajokull"), (37.0, -112.0, "Colorado Plateau"),
    (20.0, 57.0, "Oman Dhofar"), (-20.2, -67.6, "Uyuni"), (37.75, 14.99, "Etna"),
]


def load_band(north, south):
    """Global features for one band of latitude: dict of 2D arrays + lat/lon."""
    grid = build_earth.make_grid(-180, south, 180, north)
    lat, lon = build_earth.cell_centres(*grid)
    layers = {}
    layers.update(build_earth.temperature(grid))
    layers.update(build_earth.albedo(grid))
    layers.update(build_earth.precipitation(lat, lon))
    layers.update(build_earth.vegetation(grid))
    return lat, lon, layers


def score_band(layers, targets, weights):
    """Mean score of every cell over all the targets of one body."""
    land = np.isfinite(layers["temp_mean_K"]) & np.isfinite(layers["albedo"])
    total = np.zeros(land.sum())
    cells = {}
    for name in USED:
        values = layers[name][land]
        if name in compare.LOG_FEATURES:
            values = np.log1p(values)
        cells[name] = values / compare.TOLERANCE[name]
    w_sum = sum(weights[n] for n in USED)
    for _, target in targets.iterrows():
        squares = 0.0
        for name in USED:
            t = np.log1p(target[name]) if name in compare.LOG_FEATURES else target[name]
            squares = squares + weights[name] * (cells[name] - t / compare.TOLERANCE[name]) ** 2
        total += np.exp(-np.sqrt(squares / w_sum))
    return land, total / len(targets)


# Whole zones the challenge explicitly asks to avoid (south, west, north, east).
AVOID_ZONES = [
    (-90, -180, -60, 180, "Antarctica (challenge: avoid)"),
    (-30, -72, -17, -66, "Atacama (challenge: avoid)"),
    (63, -25, 67, -13, "Iceland (challenge: avoid)"),
    (18, -161, 23, -154, "Hawaii (challenge: avoid)"),
]


def nearest_known(lat, lon):
    """Name of a famous analog or avoided zone near this place, or '' if none."""
    for south, west, north, east, name in AVOID_ZONES:
        if south <= lat <= north and west <= lon <= east:
            return name
    for k_lat, k_lon, name in KNOWN:
        d_lon = (lon - k_lon + 180) % 360 - 180
        if abs(lat - k_lat) <= 3 and abs(d_lon) * np.cos(np.radians(lat)) <= 3:
            return name
    return ""


def screen(targets, body, top_areas):
    weights = compare.DEFAULT_WEIGHTS
    parts = []
    for north in range(90, -90, -BAND):
        lat, lon, layers = load_band(north, north - BAND)
        land, score = score_band(layers, targets, weights)
        part = pd.DataFrame({"lat": lat[land], "lon": lon[land], "score": score})
        for name in USED:
            part[name] = layers[name][land]
        parts.append(part.astype("float32"))
        print(f"  {body}: latitudes {north} to {north - BAND} done ({land.sum():,} land cells)")
    cells = pd.concat(parts, ignore_index=True)

    # Group the cells into areas of AREA_DEG x AREA_DEG degrees.
    cells["a_lat"] = np.floor(cells["lat"] / AREA_DEG) * AREA_DEG
    cells["a_lon"] = np.floor(cells["lon"] / AREA_DEG) * AREA_DEG
    areas = cells.groupby(["a_lat", "a_lon"]).agg(
        best_score=("score", "max"), mean_score=("score", "mean"), land_cells=("score", "size"),
        temp_mean_K=("temp_mean_K", "median"), temp_range_K=("temp_range_K", "median"),
        albedo=("albedo", "median"), precip_mm=("precip_mm", "median")).reset_index()
    areas = areas[areas["land_cells"] >= 50]                      # skip tiny islands and coasts
    # Rank by the score of the best 10% of the area, not by one lucky cell.
    top10 = cells.groupby(["a_lat", "a_lon"])["score"].quantile(0.9).rename("score_top10pct")
    areas = areas.merge(top10, on=["a_lat", "a_lon"]).sort_values("score_top10pct", ascending=False)

    areas.insert(0, "body", body)
    areas["known_analog"] = [nearest_known(a + AREA_DEG / 2, o + AREA_DEG / 2)
                             for a, o in zip(areas["a_lat"], areas["a_lon"])]
    areas["box_west_south_east_north"] = [f"{o:g} {a:g} {o + AREA_DEG:g} {a + AREA_DEG:g}"
                                          for a, o in zip(areas["a_lat"], areas["a_lon"])]
    areas = areas.rename(columns={"a_lat": "south", "a_lon": "west"})
    areas.insert(1, "rank", range(1, len(areas) + 1))
    return areas.head(top_areas), len(cells)


def new_candidates(areas, block_deg=10, n=25):
    """
    Little-known areas only, and at most one per block of block_deg x block_deg
    degrees, so the list shows DIFFERENT parts of the world instead of 15
    neighbours of the same place.
    """
    new = areas[areas["known_analog"] == ""].copy()
    new["block"] = (np.floor(new["south"] / block_deg).astype(int).astype(str) + "_"
                    + np.floor(new["west"] / block_deg).astype(int).astype(str))
    return new.drop_duplicates("block").drop(columns="block").head(n)


def main():
    parser = argparse.ArgumentParser(description="Screen the whole Earth for new analog areas.")
    parser.add_argument("--targets", default="data/targets.csv")
    parser.add_argument("--top", type=int, default=2000, help="How many areas to save per body")
    args = parser.parse_args()

    targets = pd.read_csv(args.targets, comment="#")
    for body, group in targets.groupby("body", sort=False):
        areas, n_cells = screen(group, body, args.top)
        out = f"data/discovery_{body.lower()}.csv"
        areas.round(4).to_csv(out, index=False)
        new = new_candidates(areas)
        new.round(4).to_csv(f"data/discovery_{body.lower()}_new.csv", index=False)
        print(f"\n{body}: scored {n_cells:,} land cells. Saved the best {len(areas)} areas to {out}")
        print(f"Best NEW areas (famous analogs and avoided zones left out, one per 10 x 10 degrees),")
        print(f"also saved to data/discovery_{body.lower()}_new.csv:")
        show = ["rank", "south", "west", "score_top10pct", "temp_mean_K", "temp_range_K",
                "albedo", "precip_mm", "box_west_south_east_north"]
        with pd.option_context("display.width", 200, "display.float_format", "{:.3f}".format):
            print(new[show].head(25).to_string(index=False))
        print()


if __name__ == "__main__":
    main()
