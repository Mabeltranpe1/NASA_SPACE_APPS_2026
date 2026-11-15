"""
build_database.py - Build the whole Earth database from the region catalog.

It reads data/regions_catalog.csv (one row per region) and, for each region:
    1. downloads the elevation tiles it needs (only the missing ones),
    2. builds data/regions/<name>.csv with src/build_earth.py (skipped if the
       file already exists; use --rebuild to force it),
then joins every region into ONE table: data/earth_all.csv.

The temperature, albedo and rain files in data/raw/ are global, so new
regions only need new elevation tiles.

Examples:
    python src/build_database.py                 # build what is missing, then merge
    python src/build_database.py --only gobi     # just one region
    python src/build_database.py --rebuild       # rebuild everything
    python src/build_database.py --refresh-surface   # only redo climate, vegetation
                                                    # and rock columns (fast, keeps terrain)
"""

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd

CATALOG = Path("data/regions_catalog.csv")
REGIONS_DIR = Path("data/regions")
OUT = Path("data/earth_all.csv")
SRC = Path(__file__).parent


def run(script, *args):
    """Run another script of this project with the same Python."""
    command = [sys.executable, str(SRC / script), *[str(a) for a in args]]
    return subprocess.run(command).returncode == 0


def build_region(row, rebuild):
    out = REGIONS_DIR / f"{row['name']}.csv"
    if out.exists() and not rebuild:
        return True
    print(f"\n=== {row['name']} ({row['why']}) ===")
    box = [row["west"], row["south"], row["east"], row["north"]]
    if row["dem"] == "cop90":
        run("download_earth.py", "--dem", "cop90", "--region", *box, "--download")
    return run("build_earth.py", "--dem", row["dem"], "--name", row["name"],
               "--region", *box, "--out", out)


def merge(catalog):
    """Join all region files into one table (a place that is in two regions is kept once)."""
    parts = [pd.read_csv(REGIONS_DIR / f"{name}.csv") for name in catalog["name"]
             if (REGIONS_DIR / f"{name}.csv").exists()]
    table = pd.concat(parts, ignore_index=True).drop_duplicates(["lat", "lon"])
    # known = yes / no, from the catalog (famous analogs are controls only).
    table["known"] = table["region"].map(dict(zip(catalog["name"], catalog["known"]))).fillna("no")
    table.to_csv(OUT, index=False)
    print(f"\nSaved {len(table):,} places from {table['region'].nunique()} regions to {OUT}\n")
    summary = table.groupby("region").agg(
        places=("lat", "size"), elev_m=("elev_m", "median"), slope_deg=("slope_deg", "median"),
        temp_mean_K=("temp_mean_K", "median"), albedo=("albedo", "median"),
        precip_mm=("precip_mm", "median"), ndvi=("ndvi", "median"),
        em_contrast=("em_contrast", "median"), missing_ndvi=("ndvi", lambda s: s.isna().sum()),
        missing_rock=("em_contrast", lambda s: s.isna().sum()), missing_albedo=("albedo", lambda s: s.isna().sum()),
        missing_temp=("temp_mean_K", lambda s: s.isna().sum()))
    print(summary.round(2).to_string())


def main():
    parser = argparse.ArgumentParser(description="Build the Earth database from the region catalog.")
    parser.add_argument("--only", action="append", help="Build only this region (can repeat)")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild region files that already exist")
    parser.add_argument("--refresh-surface", action="store_true",
                        help="Recompute only the non-terrain columns of existing region files")
    args = parser.parse_args()

    catalog = pd.read_csv(CATALOG, comment="#")
    REGIONS_DIR.mkdir(parents=True, exist_ok=True)
    unknown = set(args.only or []) - set(catalog["name"])
    if unknown:
        sys.exit(f"Not in the catalog: {sorted(unknown)}")

    failed = []
    for _, row in catalog.iterrows():
        if args.only and row["name"] not in args.only:
            continue
        path = REGIONS_DIR / f"{row['name']}.csv"
        if args.refresh_surface and path.exists() and not args.rebuild:
            print(f"\n=== {row['name']}: refreshing climate, vegetation and rock columns ===")
            sys.path.insert(0, str(SRC))
            import build_earth
            build_earth.refresh_surface(path)
            continue
        if not build_region(row, args.rebuild):
            failed.append(row["name"])
    merge(catalog)
    if failed:
        print(f"\nWARNING: these regions failed and are not in the table: {failed}")


if __name__ == "__main__":
    main()
