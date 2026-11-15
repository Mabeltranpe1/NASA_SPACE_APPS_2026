"""GeoAnalog: discovery of CRISM map-projected spectral products.
Only catalogue metadata/counts are requested; no science image is downloaded.
"""
from pathlib import Path
from math import degrees, cos, radians
import time
import xml.etree.ElementTree as ET

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
API = 'https://oderest.rsl.wustl.edu/live2/'
OUT = BASE_DIR / 'data' / 'features' / 'crism_availability.csv'
RAW = BASE_DIR / 'data' / 'raw' / 'spectral' / 'mars' / 'crism' / 'catalogue'
LOCATIONS = {
    'Jezero': (18.4447, 77.4508),
    'Gale': (-4.59, 137.44),
    'Phoenix': (68.22, 234.25),
    'Pathfinder': (19.095, 326.747),
    'Viking_1': (22.269, 312.049),
    'Viking_2': (47.668, 134.28),
}
# MTRDR targeted hyperspectral; MRDR4 multispectral mosaic (PDS4).
PRODUCTS = ('MTRDR', 'MRDR4')


def search_bounds(lat, lon):
    # Approximate enclosing box for a nominal 10 km square, not a precise DEM clip.
    dlat = degrees(5.2 / 3390.0)
    dlon = dlat / cos(radians(abs(lat) + dlat))
    return dict(minlat=lat-dlat, maxlat=lat+dlat,
                westernlon=(lon-dlon) % 360, easternlon=(lon+dlon) % 360)


def read_count(content):
    root = ET.fromstring(content)
    # Permit optional XML namespaces and case variations in error responses.
    tags = {e.tag.split('}')[-1].lower(): (e.text or '').strip() for e in root}
    if tags.get('status', '').lower() != 'success':
        raise ValueError(tags.get('error') or tags.get('status') or 'Unknown ODE status')
    count = int(tags['count'])
    if count < 0:
        raise ValueError('Invalid count')
    return count


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    rows = []
    with requests.Session() as session:
        for region, (lat, lon) in LOCATIONS.items():
            print(f'\n{region}', flush=True)
            for product in PRODUCTS:
                params = dict(query='product', target='mars', ihid='MRO',
                              iid='CRISM', pt=product, results='c', output='XML',
                              loc='f', **search_bounds(lat, lon))
                row = dict(region=region, planet='mars', latitude=lat,
                           longitude_east=lon, product_type=product,
                           **search_bounds(lat, lon), product_count=None,
                           status='error', query_url=requests.Request('GET', API, params=params).prepare().url,
                           error='')
                try:
                    response = session.get(API, params=params, timeout=(15, 120))
                    (RAW / f'{region}_{product}.xml').write_bytes(response.content)
                    response.raise_for_status()
                    count = read_count(response.content)
                    row.update(product_count=count, status='ok' if count else 'no_matches')
                    print(f'  {product}: {count} products', flush=True)
                except (requests.RequestException, ET.ParseError, ValueError, KeyError) as exc:
                    row['error'] = str(exc)
                    print(f'  {product}: ERROR {exc}', flush=True)
                rows.append(row)
                # Persist completed queries even if a later query fails.
                df = pd.DataFrame(rows)
                df['product_count'] = df['product_count'].astype('Int64')
                df.to_csv(OUT, index=False)
                time.sleep(1)
    print(f'\nOutput: {OUT}')
    print('Counts include multiple product subtypes; do not sum as unique observations.')
    print('Catalogue matches do not guarantee valid ROI pixels or mineral detections.')
    print(f'Queries without error: {sum(r["status"] != "error" for r in rows)}/{len(rows)}')


if __name__ == '__main__':
    main()
