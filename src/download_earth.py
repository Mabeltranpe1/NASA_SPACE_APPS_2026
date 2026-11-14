"""
download_earth.py - Download the NASA Earth datasets for the similarity index.

Datasets (all from NASA Earthdata, all free):
    NASADEM_HGT  -> elevation, later slope and roughness  (30 m tiles, region only)
    MOD11C3      -> land surface temperature, monthly     (0.05 deg, global)
    MCD43C3      -> surface albedo, one day per month     (0.05 deg, global)
    GPM_3IMERGM  -> precipitation, monthly                (0.1 deg, global)

Step 1 - see what would be downloaded and how big it is (no login needed):
    python src/download_earth.py --region -80 -5 -66 13

Step 2 - really download (asks for your Earthdata username and password
the first time, or reads them from ~/.netrc):
    python src/download_earth.py --region -80 -5 -66 13 --download

Files go to data/raw/<dataset>/ (git ignores data/raw/).
Files that already exist are skipped, so you can stop and run it again.
"""

import argparse
import shutil
from datetime import date
from pathlib import Path

import earthaccess

RAW_DIR = Path("data/raw")


# ---------------------------------------------------------------------------
# 1. Searching (this part never needs a login)
# ---------------------------------------------------------------------------

def granule_name(granule):
    """The file name of a granule, taken from its download link."""
    return granule.data_links()[0].rsplit("/", 1)[-1]


def granule_mb(granule):
    """Size of one granule in MB (0 if NASA does not say)."""
    size = granule.size() if callable(granule.size) else granule.size
    return float(size or 0)


def find_dem(region):
    """NASADEM tiles (1 x 1 degree each) that touch the region."""
    return earthaccess.search_data(short_name="NASADEM_HGT", version="001",
                                   bounding_box=tuple(region))


def find_monthly(short_name, version, year):
    """One granule per month for a monthly product (MOD11C3, GPM_3IMERGM)."""
    return earthaccess.search_data(short_name=short_name, version=version,
                                   temporal=(f"{year}-01-01", f"{year}-12-31"))


def find_albedo(year):
    """
    MCD43C3 is a DAILY product (about 180 MB per day), so a whole year would
    be about 65 GB. We take only the 15th of each month: 12 files.
    """
    granules = []
    for month in range(1, 13):
        day = date(year, month, 15)
        doy = day.timetuple().tm_yday            # day of the year, 1..366
        tag = f".A{year}{doy:03d}."               # e.g. ".A2023015." in the file name
        found = earthaccess.search_data(short_name="MCD43C3", version="061",
                                        temporal=(day.isoformat(), day.isoformat()))
        granules += [g for g in found if tag in granule_name(g)][:1]
    return granules


def plan(region, year):
    """Return {folder name: list of granules} for everything we need."""
    return {
        "NASADEM_HGT": find_dem(region),
        "MOD11C3": find_monthly("MOD11C3", "061", year),
        "MCD43C3": find_albedo(year),
        "GPM_3IMERGM": find_monthly("GPM_3IMERGM", "07", year),
    }


# ---------------------------------------------------------------------------
# 2. Downloading (needs an Earthdata login)
# ---------------------------------------------------------------------------

def download(datasets):
    """Download every granule into data/raw/<dataset>/, skipping files we already have."""
    earthaccess.login()  # uses ~/.netrc or asks for username/password
    for folder, granules in datasets.items():
        target = RAW_DIR / folder
        target.mkdir(parents=True, exist_ok=True)
        todo = [g for g in granules if not (target / granule_name(g)).exists()]
        print(f"{folder}: {len(granules) - len(todo)} already here, downloading {len(todo)}")
        if not todo:
            continue
        try:
            earthaccess.download(todo, local_path=str(target))
        except earthaccess.exceptions.EulaNotAccepted:
            # Some data centers (like GES DISC for GPM) need a one-time
            # approval in your Earthdata profile before the first download.
            print(f"  SKIPPED {folder}: NASA needs your one-time approval first.\n"
                  "  Go to https://urs.earthdata.nasa.gov/profile -> 'Authorized Apps'\n"
                  "  -> 'Approve More Applications', approve 'NASA GESDISC DATA ARCHIVE',\n"
                  "  then run this script again (files you already have are skipped).")
        except Exception as err:
            # Do not lose the other datasets because one failed.
            print(f"  FAILED {folder}: {err}\n  Run the script again later to retry.")


# ---------------------------------------------------------------------------
# 3. Command line
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Download NASA Earth data for the analog index.")
    parser.add_argument("--region", nargs=4, type=float, required=True,
                        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
                        help="Area for the elevation tiles, in degrees, e.g. -80 -5 -66 13")
    parser.add_argument("--year", type=int, default=2023, help="Year for the monthly data (default 2023)")
    parser.add_argument("--download", action="store_true",
                        help="Really download. Without this flag we only show the plan.")
    args = parser.parse_args()

    west, south, east, north = args.region
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        parser.error("region must be WEST SOUTH EAST NORTH, with west < east and south < north")
    if not 2001 <= args.year < date.today().year:
        parser.error(f"year must be between 2001 and {date.today().year - 1}")

    print(f"Searching NASA Earthdata (year {args.year}, region {args.region}) ...")
    datasets = plan(args.region, args.year)

    total = 0.0
    for folder, granules in datasets.items():
        size = sum(granule_mb(g) for g in granules)
        total += size
        print(f"  {folder:<12} {len(granules):>5} files  {size / 1024:6.2f} GB")
    print(f"  {'TOTAL':<12} {'':>5}        {total / 1024:6.2f} GB")

    free_gb = shutil.disk_usage(".").free / 1024**3
    print(f"Free disk space here: {free_gb:.1f} GB")

    if args.download:
        download(datasets)
        print("Done.")
    else:
        print("\nNothing downloaded. Add --download to download these files.")


if __name__ == "__main__":
    main()
