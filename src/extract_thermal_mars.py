"""GeoAnalog: MGS TES TIMAP v1.0 (PDS3, 2007), native-cell area weights.
Run: python src/extract_thermal_mars.py
Dependencies: numpy pandas pyproj shapely
No downloads, no resampling and no use of interpolated pixels in primary statistics.
Reference: https://doi.org/10.17189/1519489
"""
from pathlib import Path
import math
import re
import numpy as np
import pandas as pd
from pyproj import CRS, Transformer
from shapely.geometry import box, Polygon

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / 'data' / 'raw' / 'thermal' / 'mars' / 'tes'
OUT = BASE / 'data' / 'features'
LOCATIONS = {
    'Jezero': (18.4447, 77.4508),
    'Gale': (-4.59, 137.44),
    'Phoenix': (68.22, 234.25),
    'Pathfinder': (19.095, 326.747),
    'Viking_1': (22.269, 312.049),
    'Viking_2': (47.668, 134.28),
}
RADIUS = 3396000.0  # m, PDS label spherical reference
ROWS, COLS = 3600, 7200
STEP = 0.05
HALF = 5000.0
AREA = (2 * HALF)**2
UNIT = 'J m^-2 K^-1 s^-0.5'
GEO = CRS.from_proj4(f'+proj=longlat +R={RADIUS} +no_defs')
SOURCE = 'MGS TES TIMAP V1.0 (Putzig et al., PDS 2009; maps 2007)'

def label_value(text, key):
    match = re.search(r'^\s*' + re.escape(key) + r'\s*=\s*([^\r\n]+)', text, re.M)
    if not match:
        raise ValueError(f'PDS label missing {key}')
    return match.group(1).split('<')[0].strip().strip('"')


def load_product(stem, mask=False):
    lbl, img = RAW / (stem + '.lbl'), RAW / (stem + '.img')
    text = lbl.read_text(encoding='ascii')
    expected = {
        'LINES': ROWS, 'LINE_SAMPLES': COLS,
        'SAMPLE_BITS': 8 if mask else 16,
        'FILE_RECORDS': ROWS, 'RECORD_BYTES': COLS * (1 if mask else 2),
        'MAP_RESOLUTION': 20, 'A_AXIS_RADIUS': 3396,
        'B_AXIS_RADIUS': 3396, 'C_AXIS_RADIUS': 3396,
        'MAXIMUM_LATITUDE': 90, 'MINIMUM_LATITUDE': -90,
        'WESTERNMOST_LONGITUDE': -180, 'EASTERNMOST_LONGITUDE': 180,
        'LINE_PROJECTION_OFFSET': 1800.5, 'SAMPLE_PROJECTION_OFFSET': 3600.5,
        'CENTER_LATITUDE': 0, 'CENTER_LONGITUDE': 0,
        'MAP_PROJECTION_ROTATION': 0,
    }
    for k, v in expected.items():
        if not math.isclose(float(label_value(text, k)), v, rel_tol=0, abs_tol=1e-8):
            raise ValueError(f'{lbl.name}: unexpected {k}')
    for k, v in {'SAMPLE_TYPE': 'MSB_INTEGER', 'POSITIVE_LONGITUDE_DIRECTION': 'EAST',
                 'COORDINATE_SYSTEM_NAME': 'PLANETOCENTRIC',
                 'MAP_PROJECTION_TYPE': 'SIMPLE CYLINDRICAL'}.items():
        if label_value(text, k).upper() != v:
            raise ValueError(f'{lbl.name}: unexpected {k}')
    if label_value(text, '^IMAGE').lower() != img.name.lower():
        raise ValueError(f'{lbl.name}: image pointer mismatch')
    dtype = np.dtype('i1' if mask else '>i2')
    if img.stat().st_size != ROWS * COLS * dtype.itemsize:
        raise ValueError(f'{img.name}: unexpected byte count')
    # PDS detached IMG files have no header; do not use PSI .bin offsets.
    print(f'OK: {img.name} ({img.stat().st_size:,} bytes)')
    return np.memmap(img, mode='r', dtype=dtype, shape=(ROWS, COLS))


def lon180(lon):
    return (lon + 180.0) % 360.0 - 180.0


def footprint_cells(lat, lon):
    """Nominal 10 km square on TES sphere; local Lambert equal-area.
    Intersect native 0.05-degree cells with the square; no interpolation.
    Edges are densified to approximate their projected geometry.
    """
    lon = lon180(lon)
    crs = CRS.from_proj4(f'+proj=laea +lat_0={lat} +lon_0={lon} +R={RADIUS} +units=m +no_defs')
    fwd = Transformer.from_crs(GEO, crs, always_xy=True)
    inv = Transformer.from_crs(crs, GEO, always_xy=True)
    roi = box(-HALF, -HALF, HALF, HALF)
    edge = np.linspace(-HALF, HALF, 41)
    xs = np.concatenate([edge, np.full_like(edge, HALF), edge[::-1], np.full_like(edge, -HALF)])
    ys = np.concatenate([np.full_like(edge, -HALF), edge, np.full_like(edge, HALF), edge[::-1]])
    lons, lats = inv.transform(xs, ys)
    lons = lon + (np.asarray(lons) - lon + 180) % 360 - 180
    # Unwrapped columns allow crossing the longitude seam, if needed.
    c0 = math.floor((min(lons) + 180) / STEP) - 1
    c1 = math.floor((max(lons) + 180) / STEP) + 1
    r0 = max(0, math.floor((90 - max(lats)) / STEP) - 1)
    r1 = min(ROWS - 1, math.floor((90 - min(lats)) / STEP) + 1)
    cells = []
    for r in range(r0, r1 + 1):
        north = 90 - r * STEP
        south = north - STEP
        for cu in range(c0, c1 + 1):
            west = -180 + cu * STEP
            east = west + STEP
            a = np.linspace(west, east, 9)
            b = np.linspace(south, north, 9)
            plon = np.r_[a, np.full(8, east), a[-2::-1], np.full(7, west)]
            plat = np.r_[np.full(9, south), b[1:], np.full(8, north), b[-2:0:-1]]
            xx, yy = fwd.transform(plon, plat)
            poly = Polygon(zip(xx, yy))
            weight = roi.intersection(poly).area
            if weight > 1e-6:
                cells.append((r, cu % COLS, weight))
    if not np.isclose(sum(c[2] for c in cells), AREA, rtol=1e-6):
        raise ValueError('Native pixels do not cover the nominal window')
    return cells


def weighted_stats(vals, weights, keep, prefix):
    vals, w = vals[keep].astype(float), weights[keep]
    result = {prefix + '_valid_cells': int(keep.sum()),
              prefix + '_valid_area_pct': float(100 * w.sum() / AREA)}
    if len(vals):
        mean = np.average(vals, weights=w)
        result.update({prefix + '_mean_tiu': float(mean),
                       prefix + '_std_tiu': float(np.sqrt(np.average((vals - mean)**2, weights=w))),
                       prefix + '_min_tiu': float(vals.min()), prefix + '_max_tiu': float(vals.max())})
    else:
        result.update({prefix + '_' + s + '_tiu': np.nan for s in ('mean', 'std', 'min', 'max')})
    return result


def summarize(region, lat, lon, grids):
    cells = footprint_cells(lat, lon)
    ri, ci = np.array([(r, c) for r,c,w in cells], dtype=int).T
    w = np.array([w for r,c,w in cells])
    row = {'region': region, 'planet': 'mars', 'latitude_planetocentric_deg': lat,
           'longitude_east_360_deg': lon % 360, 'longitude_east_signed_deg': lon180(lon),
           'study_area_km2': AREA / 1e6, 'native_pixel_deg': STEP,
           'native_pixel_ns_km': RADIUS * math.radians(STEP) / 1000,
           'native_pixel_ew_km_approx': RADIUS * math.radians(STEP) * math.cos(math.radians(lat)) / 1000,
           'native_cells_intersecting': len(cells), 'thermal_inertia_unit': UNIT,
           'window_method': 'nominal_10km_square_LAEA_TES_sphere',
           'period': '1999-2004', 'source': SOURCE}
    values, masks, good = {}, {}, {}
    for mode in ('day', 'night'):
        v = np.asarray(grids[mode][ri, ci], dtype=float)
        m = np.asarray(grids[mode + '_mask'][ri, ci])
        if not np.isin(m, [0, 1]).all():
            raise ValueError(f'{region}: unexpected {mode} interpolation mask codes')
        in_range = (v >= 5) & (v <= 5000)
        valid = in_range & (m == 1)
        values[mode], masks[mode], good[mode] = v, m, valid
        row.update(weighted_stats(v, w, valid, f'ti_{mode}'))
        row[f'ti_{mode}_interpolated_area_pct'] = float(100*w[in_range & (m == 0)].sum()/AREA)
        row[f'ti_{mode}_invalid_area_pct'] = float(100*w[~in_range].sum()/AREA)
        row[f'ti_{mode}_coverage_flag'] = 'ok' if row[f'ti_{mode}_valid_area_pct'] >= 80 else ('low_coverage' if valid.any() else 'no_valid_data')
    paired = good['day'] & good['night']
    row.update(weighted_stats(values['day'] - values['night'], w, paired, 'ti_day_minus_night_paired'))
    details = []
    for i, (r, c, area) in enumerate(cells):
        details.append({'region': region, 'planet': 'mars', 'row_0based': r, 'col_0based': c,
                        'latitude_center_deg': 90-(r+.5)*STEP,
                        'longitude_center_east_deg': -180+(c+.5)*STEP,
                        'overlap_area_km2': area/1e6, 'overlap_pct_of_window': 100*area/AREA,
                        'day_raw_tiu': values['day'][i], 'night_raw_tiu': values['night'][i],
                        'day_interpolation_mask': int(masks['day'][i]), 'night_interpolation_mask': int(masks['night'][i]),
                        'day_accepted': bool(good['day'][i]), 'night_accepted': bool(good['night'][i])})
    return row, details


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    grids = {}
    for mode in ('day', 'night'):
        grids[mode] = load_product(f'global_ti_{mode}_2007')
        grids[mode + '_mask'] = load_product(f'global_ti_msk_{mode}_2007', mask=True)
    rows, details = [], []
    for region, (lat, lon) in LOCATIONS.items():
        row, pixels = summarize(region, lat, lon, grids)
        rows.append(row)
        details.extend(pixels)
        print(f'\n{region}: {row["native_cells_intersecting"]} intersecting cells')
        for mode in ('day', 'night'):
            print(f'  {mode}: {row[f"ti_{mode}_mean_tiu"]:.2f} TIU | '
                  f'coverage: {row[f"ti_{mode}_valid_area_pct"]:.2f}% | {row[f"ti_{mode}_coverage_flag"]}')
    for name, data in [('thermal_mars_features.csv', rows), ('thermal_mars_pixels.csv', details)]:
        path = OUT / name
        pd.DataFrame(data).to_csv(path, index=False, float_format='%.6f')
        print(f'Output: {path}')
    print(f'Completed: {len(rows)}/{len(LOCATIONS)} regions. No valid data is left blank in CSV.')
    print('Native cells only; area-weighted statistics; no interpolated pixels in primary results.')

if __name__ == '__main__':
    main()
