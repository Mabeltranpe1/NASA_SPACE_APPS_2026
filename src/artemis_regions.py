"""
artemis_regions.py - Centre and radius of each NASA Artemis candidate landing
region, from the candidate landing sites of Wueller et al. (2026).

NASA publishes the region names (and a map) but not a table of coordinates.
Wueller et al. 2026 (JGR Planets, doi:10.1029/2025JE009434) give 130
candidate landing sites inside the regions, as a shapefile (CC-BY-4.0):
    https://zenodo.org/records/17084058  ->  Landing_Sites.zip  (12 MB zip,
    ~890 MB unzipped because of a GeoTIFF we do not use)
Put LandingSites.shp/.shx/.dbf in data/raw/moon/artemis_sites/ and run:
    python src/artemis_regions.py
It prints one line per region (centre lat/lon, radius km, number of sites),
ready to paste into SITES in src/build_moon_targets.py.

Centre = mean of the sites in polar stereographic metres (same map as LOLA).
Radius = farthest site from the centre + 2 km (the exploration area around a
landing site), so the disk covers everywhere the crew would land and walk.
"""
import collections
from pathlib import Path

import numpy as np
import shapefile   # pip install pyshp
from pyproj import CRS, Transformer

SHP = Path("data/raw/moon/artemis_sites/LandingSites")
POLAR = CRS.from_proj4("+proj=stere +lat_0=-90 +lon_0=0 +k=1 +R=1737400 +units=m +no_defs")
LONLAT = CRS.from_proj4("+proj=longlat +R=1737400 +no_defs")
NAMES = {  # region code in the shapefile -> name used in our tables
    "PCB": "Peak near Cabeus B (Artemis III)", "HW": "Haworth (Artemis III)",
    "MMA": "Malapert Massif (Artemis III)", "MMP": "Mons Mouton Plateau (Artemis III)",
    "MMO": "Mons Mouton (Artemis III)", "NR1": "Nobile Rim 1 (Artemis III)",
    "NR2": "Nobile Rim 2 (Artemis III)", "dGR2": "de Gerlache Rim 2 (Artemis III)",
    "SP": "Slater Plain (Artemis III)", "PNS": "Peak near Shackleton (Artemis 2022)",
    "CR": "Connecting Ridge (Artemis 2022)", "CRE": "Connecting Ridge Extension (Artemis 2022)",
    "dGR1": "de Gerlache Rim 1 (Artemis 2022)", "dGKM": "de Gerlache-Kocher Massif (Artemis 2022)",
    "FRA": "Faustini Rim A (Artemis 2022)", "AR": "Amundsen Rim (Artemis 2022)",
}


def main():
    to_xy = Transformer.from_crs(LONLAT, POLAR, always_xy=True)
    to_ll = Transformer.from_crs(POLAR, LONLAT, always_xy=True)
    sites = collections.defaultdict(list)
    for rec in shapefile.Reader(str(SHP)).records():
        sites[rec["Landing_Re"]].append(to_xy.transform(rec["Longitude"], rec["Latitude"]))
    for code, name in NAMES.items():
        xy = np.array(sites[code])
        centre = xy.mean(axis=0)
        radius = np.hypot(*(xy - centre).T).max() / 1000 + 2
        lon, lat = to_ll.transform(*centre)
        print(f'    ("{name}", {lat:.3f}, {lon:.3f}, "disk", {radius:.1f}),   # {len(xy)} sites')


if __name__ == "__main__":
    main()
