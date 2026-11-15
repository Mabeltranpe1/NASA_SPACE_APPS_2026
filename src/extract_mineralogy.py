"""GeoAnalog: exploratory EMIT L2B V001 mineral detection statistics.
Run from the repository with: python src/extract_mineralogy.py
No network calls. One pixel in one acquisition = one observation.
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd
import xarray as xr
import rasterio
from pyproj import CRS, Transformer

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / 'data' / 'raw' / 'emit'
DEMS = BASE / 'data' / 'processed' / 'earth'
OUT = BASE / 'data' / 'features'
SOURCE = 'NASA EMITL2BMIN.001'
LOCATIONS = {
    'Tatacoa': (3.2300, -75.1700),
    'La_Guajira': (12.43653, -71.60899),
    'Nevado_del_Ruiz': (4.8950, -75.3220),
    'Volcan_Purace': (2.3095, -76.3948),
    'La_Candelaria': (5.5368, -73.6163),
    'Nevado_Santa_Isabel': (4.8180, -75.3650),
}
# Exploratory thresholds: adjust only with a documented sensitivity analysis.
MIN_DEPTH = 0.02
MIN_FIT_STORED = 0.20  # EMIT V001 half-scale: equivalent to fit >= 0.40
MIN_SNR_DEPTH = 2.0   # additional GeoAnalog rule: depth >= 2 * uncertainty
DIMS = ('downtrack', 'crosstrack')


def study_window(region, lat, lon):
    """Prefer the actual processed DEM extent; otherwise nominal UTM square."""
    dem = DEMS / f'{region}_DEM_200m.tif'
    if dem.exists():
        with rasterio.open(dem) as src:
            bounds = tuple(src.bounds)
            crs = CRS.from_user_input(src.crs)
            if not crs.is_projected or any(
                abs(a.unit_conversion_factor - 1) > 1e-8 for a in crs.axis_info[:2]
            ):
                raise ValueError('DEM CRS is not projected in metres')
            if not np.allclose([bounds[2]-bounds[0], bounds[3]-bounds[1]], 10000, atol=2):
                raise ValueError(f'Unexpected DEM extent: {bounds}')
        return crs, bounds, 'processed_dem_bounds'
    zone = int((lon + 180) // 6) + 1
    crs = CRS.from_epsg(32600 + zone)
    x, y = Transformer.from_crs(4326, crs, always_xy=True).transform(lon, lat)
    return crs, (x-5000, y-5000, x+5000, y+5000), 'nominal_utm_square'


def numeric(ds, key):
    da = ds[key]
    if set(da.dims) != set(DIMS) or da.ndim != 2:
        raise ValueError(f'Unexpected dimensions for {key}: {da.dims}')
    return np.asarray(da.transpose(*DIMS).values, dtype=float)


def names_lookup(meta):
    ids = np.asarray(meta['index'].values).ravel()
    names = np.asarray(meta['name'].values).ravel()
    if len(ids) != len(names):
        raise ValueError('Mineral metadata index/name length mismatch')
    lookup = {}
    for i, name in zip(ids, names):
        if not np.isfinite(i) or i <= 0 or i > 100000 or i != int(i):
            continue
        if isinstance(name, bytes):
            name = name.decode('utf-8', errors='replace')
        label = str(name).strip().strip('\x00')
        if label and label.lower() != 'nan':
            lookup[int(i)] = label
    if not lookup:
        raise ValueError('No spectral library entries found')
    return lookup


def roi_pixels(location, crs, bounds):
    lat, lon = numeric(location, 'lat'), numeric(location, 'lon')
    if lat.shape != lon.shape:
        raise ValueError('Latitude and longitude arrays differ')
    ok = np.isfinite(lat) & np.isfinite(lon) & (abs(lat) <= 90) & (abs(lon) <= 180)
    flat = np.flatnonzero(ok)
    x, y = Transformer.from_crs(4326, crs, always_xy=True).transform(
        lon.ravel()[flat], lat.ravel()[flat]
    )
    left, bottom, right, top = bounds
    inside = (x >= left) & (x < right) & (y >= bottom) & (y < top)
    flat = flat[inside]
    # Diagnostic only: bins touched by pixel centres (not percent area covered).
    nx = int(round((right-left)/200))
    ny = int(round((top-bottom)/200))
    cols = np.floor((x[inside]-left)/(right-left)*nx).astype(int)
    rows = np.floor((y[inside]-bottom)/(top-bottom)*ny).astype(int)
    cells = rows*nx + cols
    return flat, cells, nx*ny, lat.shape


def stats_for_group(ids, depth, fit, unc, lookup):
    known = np.isin(ids, list(lookup))
    valid = np.isfinite(depth) & (depth >= 0) & (depth <= 1) & ((ids == 0) | known)
    matches = valid & known
    passed = (matches & np.isfinite(fit) & (fit >= MIN_FIT_STORED) & (fit <= 0.50001)
              & np.isfinite(unc) & (unc >= 0) & (unc <= 1)
              & (depth >= MIN_DEPTH) & (depth >= MIN_SNR_DEPTH * unc))
    return valid, matches, passed


def pct(n, d):
    return 100*n/d if d else np.nan


def scene_date(stem):
    m = re.search(r'_(\d{8}T\d{6})_', stem)
    return pd.to_datetime(m.group(1), format='%Y%m%dT%H%M%S').isoformat() if m else ''


def process_scene(region, path, crs, bounds, window_source):
    companion = path.with_name(path.name.replace('EMIT_L2B_MIN_', 'EMIT_L2B_MINUNCERT_', 1))
    if not companion.is_file():
        raise FileNotFoundError(f'Missing uncertainty file: {companion.name}')
    scene = path.stem
    with xr.open_dataset(path, engine='netcdf4', group='location') as loc, \
         xr.open_dataset(path, engine='netcdf4', group='mineral_metadata') as meta, \
         xr.open_dataset(path, engine='netcdf4') as mineral, \
         xr.open_dataset(companion, engine='netcdf4') as quality:
        flat, cells, n_cells, shape = roi_pixels(loc, crs, bounds)
        lookup = names_lookup(meta)
        # Companion filename identifies the same acquisition. Check dimensions as well.
        def subset(ds, key):
            a = numeric(ds, key)
            if a.shape != shape:
                raise ValueError(f'{key} shape {a.shape} != geolocation {shape}')
            return a.ravel()[flat]
        scene_rows, mineral_rows = [], []
        for g in (1, 2):
            prefix = f'group_{g}_'
            ids = subset(mineral, prefix+'mineral_id')
            depth = subset(mineral, prefix+'band_depth')
            fit = subset(quality, prefix+'fit')
            unc = subset(quality, prefix+'band_depth_unc')
            # Avoid silently discarding unexpected scale conventions in newer files.
            plausible = fit[np.isfinite(fit) & (fit >= 0)]
            if plausible.size and np.max(plausible) > .50001:
                raise ValueError('Unexpected fit scale (>0.5); check product/version before proceeding')
            valid, matches, passed = stats_for_group(ids, depth, fit, unc, lookup)
            common = dict(region=region, planet='earth', scene=scene,
                          acquisition_utc=scene_date(scene), spectral_group=g,
                          source=SOURCE, window_source=window_source)
            n, v, m, a = map(int, (len(flat), valid.sum(), matches.sum(), passed.sum()))
            scene_rows.append(dict(common, roi_pixel_observations=n, valid_observations=v,
                                   no_match_observations=v-m, raw_matched_observations=m,
                                   accepted_observations=a, rejected_matched_observations=m-a,
                                   valid_pct_of_roi_observations=pct(v,n),
                                   accepted_pct_of_valid_observations=pct(a,v),
                                   roi_bins_touched_pct_200m=pct(len(np.unique(cells)), n_cells),
                                   valid_bins_touched_pct_200m=pct(len(np.unique(cells[valid])), n_cells),
                                   fit_min_stored=MIN_FIT_STORED, band_depth_min=MIN_DEPTH,
                                   depth_to_uncertainty_min=MIN_SNR_DEPTH,
                                   l2a_cloud_mask_applied=False, marine_mask_applied=False,
                                   status='ok' if v else 'no_valid_observations', error=''))
            for i in np.unique(ids[passed]).astype(int):
                mask = passed & (ids == i)
                count = int(mask.sum())
                mineral_rows.append(dict(common, mineral_id=i, mineral_name=lookup[i],
                    detection_count=count, band_depth_sum=float(depth[mask].sum()),
                    fit_corrected_sum=float((2*fit[mask]).sum()),
                    band_depth_uncertainty_sum=float(unc[mask].sum()),
                    detection_pct_of_valid_observations=pct(count,v)))
    return scene_rows, mineral_rows


MINERAL_COLS = ['region','planet','spectral_group','mineral_id','mineral_name',
                'scene_count_with_detection','detection_count','valid_observations',
                'accepted_observations','detection_pct_of_valid_observations',
                'detection_pct_of_accepted_observations','band_depth_mean',
                'fit_corrected_mean','band_depth_uncertainty_mean','source','status']


def summarize(quality_rows, mineral_rows):
    q = pd.DataFrame(quality_rows)
    d = pd.DataFrame(mineral_rows)
    regional, detail = [], []
    for region in LOCATIONS:
        qr = q[q.region == region] if not q.empty else q
        for g in (1,2):
            group = qr[qr.spectral_group == g] if not qr.empty else qr
            good = group[group.status == 'ok'] if not group.empty else group
            totals = {key: int(good[key].sum()) if not good.empty else 0 for key in (
                'valid_observations','accepted_observations','raw_matched_observations','no_match_observations')}
            v, a = totals['valid_observations'], totals['accepted_observations']
            status = ('no_valid_observations' if not v else
                      'partial_provisional' if len(good) < 3 or len(good) < len(group) else 'provisional')
            regional.append(dict(region=region, planet='earth', spectral_group=g,
                scenes_seen=len(group), scenes_with_valid_observations=len(good), **totals,
                accepted_pct_of_valid_observations=pct(a,v),
                mean_valid_bins_touched_pct_200m=good['valid_bins_touched_pct_200m'].mean() if not good.empty else np.nan,
                source=SOURCE, status=status))
            if d.empty or not a:
                continue
            ds = d[(d.region == region) & (d.spectral_group == g)]
            for (i, name), sub in ds.groupby(['mineral_id','mineral_name']):
                n = int(sub.detection_count.sum())
                detail.append(dict(region=region, planet='earth', spectral_group=g,
                    mineral_id=i, mineral_name=name, scene_count_with_detection=sub.scene.nunique(),
                    detection_count=n, valid_observations=v, accepted_observations=a,
                    detection_pct_of_valid_observations=pct(n,v),
                    detection_pct_of_accepted_observations=pct(n,a),
                    band_depth_mean=sub.band_depth_sum.sum()/n,
                    fit_corrected_mean=sub.fit_corrected_sum.sum()/n,
                    band_depth_uncertainty_mean=sub.band_depth_uncertainty_sum.sum()/n,
                    source=SOURCE, status=status))
    out = pd.DataFrame(detail, columns=MINERAL_COLS).sort_values(
        ['region','spectral_group','detection_count'], ascending=[True,True,False])
    return pd.DataFrame(regional), out


def main():
    if not RAW.is_dir():
        raise FileNotFoundError(f'EMIT folder not found: {RAW}')
    OUT.mkdir(parents=True, exist_ok=True)
    quality, detections = [], []
    errors = 0
    for region, (lat,lon) in LOCATIONS.items():
        print(f'\n========== {region} ==========')
        crs, bounds, window_source = study_window(region,lat,lon)
        print('Window:', window_source)
        files = sorted((RAW/region).glob('EMIT_L2B_MIN_*.nc'))
        print('Mineral files:', len(files))
        for path in files:
            print(' ', path.name)
            try:
                q, d = process_scene(region,path,crs,bounds,window_source)
                quality.extend(q)
                detections.extend(d)
                for row in q:
                    print(f"   G{row['spectral_group']}: ROI={row['roi_pixel_observations']}, "
                          f"valid={row['valid_observations']}, accepted={row['accepted_observations']}, "
                          f"sampled bins={row['roi_bins_touched_pct_200m']:.1f}%")
            except Exception as exc:
                errors += 1
                print('   ERROR:', exc)
                for g in (1,2):
                    quality.append(dict(region=region,planet='earth',scene=path.stem,
                        acquisition_utc=scene_date(path.stem),spectral_group=g,source=SOURCE,
                        window_source=window_source,status='error',error=str(exc)))
        if not files:
            errors += 1
            print('   WARNING: no mineral files found')
    regional, detail = summarize(quality,detections)
    pd.DataFrame(quality, columns=list(dict.fromkeys([
        'region','planet','scene','acquisition_utc','spectral_group','source','window_source',
        'roi_pixel_observations','valid_observations','no_match_observations','raw_matched_observations',
        'accepted_observations','rejected_matched_observations','valid_pct_of_roi_observations',
        'accepted_pct_of_valid_observations','roi_bins_touched_pct_200m','valid_bins_touched_pct_200m',
        'fit_min_stored','band_depth_min','depth_to_uncertainty_min','l2a_cloud_mask_applied',
        'marine_mask_applied','status','error']))).to_csv(OUT/'mineralogical_scene_quality.csv',index=False)
    regional.to_csv(OUT/'mineralogical_coverage.csv',index=False,float_format='%.6f')
    detail.to_csv(OUT/'mineralogical_features.csv',index=False,float_format='%.6f')
    pd.DataFrame(detections,columns=['region','planet','scene','acquisition_utc','spectral_group',
        'source','window_source','mineral_id','mineral_name','detection_count','band_depth_sum',
        'fit_corrected_sum','band_depth_uncertainty_sum','detection_pct_of_valid_observations']).to_csv(
        OUT/'mineralogical_scene_features.csv',index=False,float_format='%.6f')
    print('\n========== REGIONAL SUMMARY ==========')
    print(regional[['region','spectral_group','scenes_with_valid_observations','valid_observations',
        'accepted_observations','status']].to_string(index=False))
    print('\nTop three spectral-library entries per region/group:')
    if not detail.empty:
        print(detail.groupby(['region','spectral_group']).head(3)[['region','spectral_group','mineral_name',
              'detection_count','detection_pct_of_valid_observations']].to_string(index=False))
    else:
        print('No detections passed thresholds. Inspect scene quality before interpreting.')
    print(f'\nOutput: {OUT}\nScene/folder errors: {errors}\nAll results are exploratory; L2A cloud and marine masks not applied.')
    return 1 if errors or not quality else 0


if __name__ == '__main__':
    raise SystemExit(main())
