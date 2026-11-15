"""
seasons.py - In which months is an Earth place most like the Moon or Mars?

The main comparison (src/compare.py) uses yearly averages. But an analog
mission happens in a certain month, so here we look month by month.

For the best Earth place of every region (taken from the "overall" results
file) it reads, for each month of the year:
    day_K, night_K  land surface temperature by day and by night (MOD11C3)
    precip_mm       precipitation in that month (GPM IMERG)
and gives every month a score between 0 and 1:
    sim_temp  how close the month's temperature is to the target bodies' mean
              (same 30 K tolerance as compare.py; we use the colder of day
              and night because every Moon/Mars site is colder than Earth)
    sim_dry   how dry the month is (Moon and Mars have no rain)
    month_score = the mean of the two (geometric mean)
The best months are the ones with the highest month_score.

Honest limits: temperature and rain are not everything. In polar places the
coldest months are dark all day and very hard to work in; the table shows
daylight hours so you can see that trade-off.

Example:
    python src/seasons.py --overall data/results_mars_overall.csv --targets data/targets_mars.csv
"""

import argparse
import calendar
import re
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from pyhdf.SD import SD, SDC

sys.path.insert(0, str(Path(__file__).parent))
import build_earth  # noqa: E402  (same precipitation rules as the database)

RAW = Path("data/raw")
CELL = 0.05
TEMP_TOLERANCE_K = 30.0
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def monthly_temperature(lat, lon):
    """12 day values and 12 night values (K) for the grid cell of this place."""
    row, col = int((90 - lat) / CELL), int((lon + 180) / CELL)
    files = sorted((RAW / "MOD11C3").glob("*.hdf"))
    out = {"day_K": [], "night_K": []}
    for f in files:
        sd = SD(str(f), SDC.READ)
        for key, layer in (("day_K", "LST_Day_CMG"), ("night_K", "LST_Night_CMG")):
            raw = float(sd.select(layer)[row:row + 1, col:col + 1][0, 0])
            out[key].append(raw * 0.02 if raw > 0 else np.nan)   # 0 = no data (e.g. polar night)
    return out


def monthly_precipitation(lat, lon):
    """12 monthly totals in mm (IMERG, or MERRA-2 above 60 degrees; see build_earth.py)."""
    return list(build_earth.monthly_precipitation(np.array([lat]), np.array([lon]))[:, 0])


def daylight_hours(lat, month):
    """Approximate hours of daylight on the 15th of the month."""
    day_of_year = pd.Timestamp(2023, month, 15).day_of_year
    decl = np.radians(-23.44) * np.cos(2 * np.pi * (day_of_year + 10) / 365)
    x = -np.tan(np.radians(lat)) * np.tan(decl)
    return float(24 * np.degrees(np.arccos(np.clip(x, -1, 1))) / 180)


def month_table(place, target_temp):
    lat, lon = place["lat"], place["lon"]
    table = pd.DataFrame({"month": MONTHS, **monthly_temperature(lat, lon),
                          "precip_mm": monthly_precipitation(lat, lon)})
    table["daylight_h"] = [daylight_hours(lat, m) for m in range(1, 13)]
    coldest = table[["day_K", "night_K"]].min(axis=1)
    table["sim_temp"] = np.exp(-(coldest - target_temp).abs() / TEMP_TOLERANCE_K)
    table["sim_dry"] = np.exp(-np.log1p(12 * table["precip_mm"]))   # 12x = as if the whole year were like this month
    table["month_score"] = np.sqrt(table["sim_temp"] * table["sim_dry"])
    for key in ("region", "lat", "lon"):
        table.insert(0, key, place[key])
    return table


def main():
    parser = argparse.ArgumentParser(description="Best months for an analog mission at each top place.")
    parser.add_argument("--overall", required=True, help="Overall results file from compare.py")
    parser.add_argument("--targets", required=True, help="Targets file (to know how cold the body is)")
    parser.add_argument("--out", help="Save the month-by-month table to this CSV file")
    args = parser.parse_args()

    overall = pd.read_csv(args.overall)
    targets = pd.read_csv(args.targets)
    target_temp = targets["temp_mean_K"].mean()
    body = targets["body"].iloc[0]
    places = overall.groupby("region", sort=False).first().reset_index()   # best place per region

    print(f"Target: {body}, mean temperature of the sites {target_temp:.0f} K\n")
    tables, summary = [], []
    for _, place in places.iterrows():
        table = month_table(place, target_temp)
        tables.append(table)
        best = table.sort_values("month_score", ascending=False).head(3)
        summary.append({"region": place["region"], "lat": place["lat"], "lon": place["lon"],
                        "best_months": ", ".join(best["month"]),
                        "best_score": best["month_score"].iloc[0],
                        "worst_score": table["month_score"].min(),
                        "coldest_K": table[["day_K", "night_K"]].min().min(),
                        "daylight_h_in_best": best["daylight_h"].iloc[0]})

    with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
        print(pd.DataFrame(summary).to_string(index=False))
    if args.out:
        pd.concat(tables).round(3).to_csv(args.out, index=False)
        print(f"\nMonth-by-month table saved to {args.out}")


if __name__ == "__main__":
    main()
