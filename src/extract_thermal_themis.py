"""GeoAnalog — pilot THEMIS IRPBT brightness temperature extraction.
Run: python src/extract_thermal_themis.py
Reads the existing download_themis.py manifest; never downloads or changes PAI.
Sources: https://doi.org/10.17189/1520354 ; https://doi.org/10.17189/fs8c-m768
GDAL PDS/PDS4 georeferencing; label scale/offset and masks; planimetric weights
in each source projection, not resampled temperatures. All aggregates are pilot
scene statistics, not climatology or paired diurnal temperature amplitude.
"""
from pathlib import Path
import math
import re
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from pyproj import CRS, Transformer
import shapely
from shapely.geometry import Polygon

BASE = Path(__file__).resolve().parent.parent
FEATURES = BASE / 'data' / 'features'
DEM = BASE / 'data' / 'processed' / 'mars'
MANIFEST = FEATURES / 'themis_downloads.csv'
LOCATIONS = {'Jezero': (18.4447, 77.4508), 'Gale': (-4.59, 137.44),
             'Phoenix': (68.22, 234.25), 'Pathfinder': (19.095, 326.747),
             'Viking_1': (22.269, 312.049), 'Viking_2': (47.668, 134.28)}
MIN_COVERAGE = 80.0  # exploratory threshold; low coverage reported but excluded
MIN_PLAUSIBLE_K, MAX_PLAUSIBLE_K = 40.0, 450.0  # diagnostic, not official calibration limits
SOURCE = 'Mars Odyssey THEMIS IRPBT (NASA PDS), pilot sample'


def numeric(v):
    try:
        val = float(v)
        return val if math.isfinite(val) else None
    except (TypeError, ValueError):
        return None


def local(tag):
    return tag.rsplit('}', 1)[-1].lower()


def plain(v):
    return str(v).split('<', 1)[0].strip().strip('"\'')


def value_number(v, dtype=None):
    """PDS3 based integers (e.g. 16#8000#) are bit patterns."""
    v = plain(v)
    m = re.fullmatch(r'(\d+)#([0-9A-Fa-f]+)#', v)
    if m:
        n = int(m[2], int(m[1]))
        if dtype is not None and np.dtype(dtype).kind == 'i':
            bits = np.dtype(dtype).itemsize * 8
            if 2**(bits-1) <= n < 2**bits:
                n -= 2**bits
        return n
    return numeric(v)


def one_number(values):
    vals = {v for v in (numeric(plain(x)) for x in values) if v is not None}
    return next(iter(vals)) if len(vals) == 1 else None


def label_metadata(path, dtype):
    """Read the actual label, not an assumed universal scale or band."""
    md = {}
    def put(key, val):
        if val is not None:
            md.setdefault(key.lower(), []).append(str(val).strip())
    if path.suffix.lower() == '.xml':
        root = ET.parse(path).getroot()
        arrays = [e for e in root.iter() if local(e.tag) in ('array_2d_image', 'array_2d', 'array_3d_image')]
        if len(arrays) != 1:
            raise ValueError(f'Expected one science array; found {len(arrays)}')
        arr = arrays[0]
        for e in arr.iter():
            if local(e.tag) in ('element_array', 'special_constants'):
                for ch in e:
                    put(local(ch.tag), ch.text)
        for e in root.iter():
            k = local(e.tag)
            if k in ('latitude_type','longitude_direction','incidence_angle','solar_longitude',
                     'local_true_solar_time','local_mean_solar_time','local_solar_time','band_number',
                     'filter_number','center_filter_wavelength','central_wavelength','center_wavelength'):
                put(k, e.text)
                if 'wavelength' in k and e.attrib.get('unit'):
                    put(k+'_unit', e.attrib['unit'])
        unit_values = md.get('unit', [])
        scale_key, offset_key = 'scaling_factor','value_offset'
        special_keys = [k for k in md if k.endswith('_constant') and k not in ('valid_minimum','valid_maximum')]
    else:
        # Attached PDS3 labels end on an END line; do not decode full binary image.
        with path.open('rb') as f:
            raw = f.read(1024*1024)
        text = raw.decode('ascii', errors='replace')
        m = re.search(r'^\s*END[ \t]*\r?$', text, re.M)
        if m:
            text = text[:m.start()]
        elif path.suffix.lower() != '.lbl':
            raise ValueError('Attached PDS3 label has no END marker')
        if not re.search(r'PDS_VERSION_ID\s*=\s*PDS3', text, re.I):
            raise ValueError('PDS3 label not recognized')
        for key,val in re.findall(r'^\s*([A-Z0-9_^]+)\s*=\s*([^\r\n]+)', text, re.M):
            put(key,val)
        # Seek the IMAGE object for sample conversion, not unrelated offsets.
        img = re.search(r'^\s*OBJECT\s*=\s*IMAGE\s*$([\s\S]*?)^\s*END_OBJECT\s*=\s*IMAGE\s*$', text,re.M|re.I)
        if img:
            im = {}
            for k,v in re.findall(r'^\s*([A-Z0-9_]+)\s*=\s*([^\r\n]+)', img[1],re.M):
                im.setdefault(k.lower(),[]).append(v)
            for k in ('scaling_factor','offset','sample_unit','null_constant','missing_constant',
                      'invalid_constant','valid_minimum','valid_maximum','low_repr_saturation',
                      'high_repr_saturation','low_instr_saturation','high_instr_saturation',
                      'core_null','null','saturation_constant'):
                if k in im: md[k] = im[k]
        unit_values = md.get('sample_unit', [])
        scale_key, offset_key = 'scaling_factor','offset'
        special_keys = [k for k in md if k in ('null','core_null','null_constant','missing_constant',
            'invalid_constant','not_applicable_constant','unknown_constant','low_repr_saturation',
            'high_repr_saturation','low_instr_saturation','high_instr_saturation','saturation_constant')]
    units = {plain(v).lower() for v in unit_values if plain(v)}
    if units and not units <= {'k','kelvin','deg k','kelvins'}:
        raise ValueError(f'Unexpected sample unit: {units}')
    scale = one_number(md.get(scale_key, []))
    offset = one_number(md.get(offset_key, []))
    if md.get(scale_key) and scale is None: raise ValueError('Ambiguous scale in label')
    if md.get(offset_key) and offset is None: raise ValueError('Ambiguous offset in label')
    special = [v for key in special_keys for val in md[key] if (v:=value_number(val,dtype)) is not None]
    lower = one_number(md.get('valid_minimum',[]))
    upper = one_number(md.get('valid_maximum',[]))
    # Record evidence for the spectral band. Never assume band 9 when not explicit.
    band = one_number(md.get('band_number',[]) + md.get('filter_number',[]))
    band = int(band) if band is not None and band.is_integer() and 1<=band<=10 else None
    wave = None
    for key in ('center_filter_wavelength','central_wavelength','center_wavelength'):
        val = one_number(md.get(key,[]))
        if val is not None:
            # Values in nm are converted; typical THEMIS IR wavelengths in um.
            if 1000<=val<=20000: val /= 1000
            if 5<=val<=16: wave = val; break
    if wave is not None:
        if abs(wave-12.57)<=0.15:
            if band is not None and band!=9: raise ValueError('Conflicting spectral band and wavelength')
            band = 9
    band_group = f'band_{band}' if band is not None else (f'wavelength_{wave:.2f}_um' if wave is not None else 'band_unverified')
    lat = ' '.join(md.get('latitude_type',[]) + md.get('coordinate_system_name',[]) + md.get('coordinate_system_type',[])).upper()
    lon = ' '.join(md.get('longitude_direction',[]) + md.get('positive_longitude_direction',[])).upper()
    return dict(scale=scale,offset=offset,special=special,unit_evidence='label' if units else 'IRPBT_product_definition',
                valid_min=lower,valid_max=upper,band_group=band_group,band_number=band,wavelength_um=wave,
                label_incidence_deg=one_number(md.get('incidence_angle',[])),
                label_solar_longitude_deg=one_number(md.get('solar_longitude',[])),
                label_local_solar_time=';'.join(md.get('local_true_solar_time',[]) or md.get('local_mean_solar_time',[]) or md.get('local_solar_time',[])),
                latitude_type=lat,longitude_direction=lon)


def open_scene(row):
    files = [BASE / p for p in str(row.get('local_files','')).split(';') if p]
    images = [p for p in files if p.suffix.lower() in ('.img','.dat','.bin')]
    if len(images)!=1 or not images[0].is_file(): raise ValueError('Exactly one local science image required')
    labels = [p for p in files if p.suffix.lower() in ('.xml','.lbl') and p.is_file()]
    if str(row['product_type'])=='IRPBT4':
        labels.sort(key=lambda p:p.suffix.lower()!='.xml')
    else:
        labels.sort(key=lambda p:p.suffix.lower()!='.lbl')
    # An attached PDS3 label is supported, when no detached label is available.
    errors=[]
    for p in labels + images:
        try:
            ds = rasterio.open(p)
            try:
                if ds.driver not in ('PDS','PDS4') or ds.count!=1 or ds.crs is None:
                    raise ValueError(f'Unexpected driver/bands/CRS: {ds.driver}, {ds.count}, {ds.crs}')
                if ds.transform.is_identity: raise ValueError('Missing geotransform')
                # GDAL must use the science file from this manifest, not a browse image.
                used = {Path(f).resolve() for f in ds.files}
                if images[0].resolve() not in used and p.resolve()!=images[0].resolve():
                    raise ValueError('GDAL label does not reference manifest science image')
                meta = label_metadata(p, ds.dtypes[0])
                return ds,p,meta
            except Exception:
                ds.close(); raise
        except Exception as exc: errors.append(f'{p.name}: {exc}')
    raise ValueError(' | '.join(errors))


def dem_window(region):
    path=DEM / f'{region}_DEM_200m.tif'
    with rasterio.open(path) as ds:
        crs=CRS.from_user_input(ds.crs)
        if not crs.is_projected or not 3.3e6<crs.ellipsoid.semi_major_metre<3.5e6:
            raise ValueError('Expected projected Mars DEM CRS')
        if ds.width!=50 or ds.height!=50 or not np.allclose(ds.res,(200,200),atol=.01):
            raise ValueError('Expected processed 50 x 50 DEM at 200 m')
        if not all(abs(a.unit_conversion_factor-1)<1e-8 for a in crs.axis_info[:2]):
            raise ValueError('DEM coordinates must be metres')
        b=ds.bounds
        x0,y0,x1,y1=b.left,b.bottom,b.right,b.top
    # Densify the ROI outline before conversion to source projection.
    t=np.linspace(0,1,41)
    x=np.concatenate([x0+(x1-x0)*t, np.full(t.size,x1), x1-(x1-x0)*t, np.full(t.size,x0)])
    y=np.concatenate([np.full(t.size,y0), y0+(y1-y0)*t, np.full(t.size,y1), y1-(y1-y0)*t])
    inv=Transformer.from_crs(crs, crs.geodetic_crs, always_xy=True)
    lon,lat=inv.transform(x,y)
    cx,cy=inv.transform((x0+x1)/2,(y0+y1)/2)
    exp_lat,exp_lon=LOCATIONS[region]
    if abs(cy-exp_lat)>.02 or abs((cx-exp_lon+180)%360-180)>.02:
        raise ValueError(f'DEM center {cy}, {cx} differs from registered coordinates')
    return np.asarray(lon),np.asarray(lat),cy,cx


def source_polygon(ds, roi, meta):
    crs=CRS.from_user_input(ds.crs)
    a,b=crs.ellipsoid.semi_major_metre,crs.ellipsoid.semi_minor_metre
    if not crs.is_projected or not (3.3e6<a<3.5e6 and 3.3e6<b<3.5e6):
        raise ValueError('Expected a projected Mars CRS')
    if not all(abs(ax.unit_conversion_factor-1)<1e-8 for ax in crs.axis_info[:2]):
        raise ValueError('Source map units are not metres')
    lon,lat,_,_=roi
    # GDAL converts supported PDS west-positive labels to standard CRS axes.
    # Fail safely on west-positive products pending actual label validation.
    if 'WEST' in meta['longitude_direction']:
        raise ValueError('West-positive label requires manual longitude validation')
    if abs(a-b)>1:
        if 'PLANETOGRAPHIC' not in meta['latitude_type'] and 'PLANETODETIC' not in meta['latitude_type']:
            raise ValueError('Non-spherical source CRS without explicit planetographic latitude; inspect label')
        rad=np.deg2rad(lat)
        lat=np.rad2deg(np.arctan2(a*a*np.sin(rad),b*b*np.cos(rad)))
    elif 'PLANETOGRAPHIC' in meta['latitude_type']:
        # A sphere with a graphic-latitude label may hide an ellipsoidal definition.
        raise ValueError('Spherical source CRS with planetographic label; verify PDS radii')
    fwd=Transformer.from_crs(crs.geodetic_crs,crs,always_xy=True)
    x,y=fwd.transform(lon,lat,errcheck=True)
    poly=Polygon(np.column_stack([x,y]))
    if not poly.is_valid or poly.area<=0 or not np.isfinite(poly.area): raise ValueError('Invalid projected ROI')
    return poly


def candidate_class(angle):
    return 'day_candidate' if angle is not None and 0<=angle<85 else ('night_candidate' if angle is not None and 95<angle<=180 else 'unknown_or_twilight')


def extract_roi(ds, poly, meta):
    """Exact planar intersection weights on native projected pixel rectangles."""
    aff=ds.transform
    if abs(aff.b)>1e-8 or abs(aff.d)>1e-8 or aff.a<=0 or aff.e>=0:
        raise ValueError('Unsupported rotated/inverted grid')
    left,bottom,right,top=poly.bounds
    inv=~aff
    c0,r0=inv*(left,top); c1,r1=inv*(right,bottom)
    c0=max(0,math.floor(c0)); r0=max(0,math.floor(r0))
    c1=min(ds.width,math.ceil(c1)); r1=min(ds.height,math.ceil(r1))
    if c1<=c0 or r1<=r0: return dict(valid_area_pct=0., image_overlap_pct=0., native_valid_pixels=0, quality_status='no_overlap')
    if (r1-r0)*(c1-c0)>5_000_000: raise ValueError('Unexpected ROI pixel count')
    rows,cols=np.mgrid[r0:r1,c0:c1]
    x=aff.c+cols.ravel()*aff.a; y=aff.f+rows.ravel()*aff.e
    cells=shapely.box(x,y+aff.e,x+aff.a,y)
    weights=shapely.area(shapely.intersection(cells,poly)).reshape(rows.shape)
    overlap=100*weights.sum()/poly.area
    if overlap>100.001: raise ValueError('Native pixel overlaps exceed region area')
    arr=ds.read(1,window=Window(c0,r0,c1-c0,r1-r0),masked=True)
    raw=arr.data
    valid=(~np.ma.getmaskarray(arr)) & np.isfinite(raw) & (weights>0)
    for val in meta['special']: valid &= raw!=val
    if meta['valid_min'] is not None: valid &= raw>=meta['valid_min']
    if meta['valid_max'] is not None: valid &= raw<=meta['valid_max']
    scale=meta['scale'] if meta['scale'] is not None else ds.scales[0]
    offset=meta['offset'] if meta['offset'] is not None else ds.offsets[0]
    if not np.isfinite(scale) or scale<=0 or not np.isfinite(offset): raise ValueError('Invalid scale/offset')
    # Rasterio reads raw sample values: convert exactly once.
    temp=raw.astype(np.float64)*scale+offset
    good=valid & np.isfinite(temp)
    coverage=100*weights[good].sum()/poly.area
    invalid_physical=good & ((temp<MIN_PLAUSIBLE_K)|(temp>MAX_PLAUSIBLE_K))
    stats=dict(image_overlap_pct=min(100.,overlap),valid_area_pct=min(100.,coverage),
               native_valid_pixels=int(good.sum()),native_pixel_x_m=aff.a,native_pixel_y_m=-aff.e,
               scale_applied=scale,offset_applied=offset,scale_gdal=ds.scales[0],offset_gdal=ds.offsets[0],
               out_of_plausible_range_pixels=int(invalid_physical.sum()))
    if not good.any(): return dict(stats,quality_status='no_valid_pixels')
    if invalid_physical.any():
        # Do not silently clip unexplained or unmasked values.
        return dict(stats,quality_status='check_temperature_range',diagnostic_min_k=float(temp[good].min()),diagnostic_max_k=float(temp[good].max()))
    v,w=temp[good],weights[good]
    mean=np.average(v,weights=w)
    stats.update(brightness_mean_k=mean,brightness_std_k=np.sqrt(np.average((v-mean)**2,weights=w)),
                 brightness_min_k=v.min(),brightness_max_k=v.max(),
                 quality_status='ok' if coverage>=MIN_COVERAGE-1e-8 else 'low_coverage')
    return stats


def scene_row(row, roi):
    fields=('region','product_type','pdsid','observation_key','utc','solar_longitude_deg','incidence_deg','emission_deg','illumination_candidate','footprint_overlap_bbox_pct','science_url','local_files')
    out={k:row.get(k,'') for k in fields}
    out.update(planet='mars', source=SOURCE,temperature_unit='K',quality_status='error',error='')
    if row.get('status')!='files_ready': return dict(out,error='Manifest not files_ready')
    try:
        ds,p,meta=open_scene(row)
        with ds:
            out.update({k:v for k,v in meta.items() if k!='special'})
            out.update(label_file=str(p.relative_to(BASE)),driver=ds.driver,source_crs=ds.crs.to_wkt())
            cat=candidate_class(numeric(row.get('incidence_deg')))
            label_angle=meta['label_incidence_deg']
            label_cat=candidate_class(label_angle)
            if label_angle is not None:
                out['illumination_used']=label_cat
                out['illumination_evidence']='label_incidence_at_reference_location'
            else:
                out['illumination_used']=cat
                out['illumination_evidence']='catalogue_incidence_at_reference_location'
            out['illumination_disagreement']=bool(label_angle is not None and label_cat!=cat)
            out.update(extract_roi(ds,source_polygon(ds,roi,meta),meta))
            if out['illumination_used'] not in ('day_candidate','night_candidate') or out['illumination_disagreement']:
                if out['quality_status']=='ok': out['quality_status']='check_illumination'
    except Exception as exc: out.update(quality_status='error',error=str(exc))
    return out


def summarize(scenes):
    """Equal weighting of accepted scene means; never pool pixel observations or bands."""
    out=[]
    for region in LOCATIONS:
        for cat in ('day_candidate','night_candidate'):
            subset=scenes[(scenes['region']==region)&(scenes['illumination_candidate']==cat)]
            ok=subset[subset['quality_status']=='ok']
            if ok.empty:
                out.append(dict(region=region,planet='mars',illumination=cat,band_group='',
                    selected_scene_count=len(subset),accepted_scene_count=0,summary_status='no_accepted_scenes',source=SOURCE))
                continue
            for band,g in ok.groupby('band_group',dropna=False):
                vals=g['brightness_mean_k'].astype(float)
                ls=pd.to_numeric(g['label_solar_longitude_deg'],errors='coerce').fillna(pd.to_numeric(g['solar_longitude_deg'],errors='coerce'))
                out.append(dict(region=region,planet='mars',illumination=cat,band_group=band,
                    selected_scene_count=len(subset),accepted_scene_count=len(g),
                    brightness_scene_mean_k=vals.mean(),brightness_between_scene_std_k=vals.std(ddof=0) if len(vals)>1 else np.nan,
                    brightness_observed_min_k=g['brightness_min_k'].min(),brightness_observed_max_k=g['brightness_max_k'].max(),
                    mean_scene_valid_area_pct=g['valid_area_pct'].mean(),minimum_scene_valid_area_pct=g['valid_area_pct'].min(),
                    solar_longitude_deg_list=';'.join(f'{v:.3f}' for v in ls.dropna()),
                    observation_ids=';'.join(g['observation_key'].astype(str)),
                    summary_status='pilot_band_unverified' if band=='band_unverified' else 'pilot',source=SOURCE))
    columns = ['region','planet','illumination','band_group','selected_scene_count','accepted_scene_count',
               'brightness_scene_mean_k','brightness_between_scene_std_k','brightness_observed_min_k',
               'brightness_observed_max_k','mean_scene_valid_area_pct','minimum_scene_valid_area_pct',
               'solar_longitude_deg_list','observation_ids','summary_status','source']
    return pd.DataFrame(out,columns=columns)


def main():
    manifest=pd.read_csv(MANIFEST,keep_default_na=False)
    required={'region','product_type','pdsid','observation_key','status','local_files','illumination_candidate','incidence_deg'}
    missing=required-set(manifest.columns)
    if missing: raise ValueError(f'Missing manifest columns: {missing}')
    if manifest.duplicated(['region','observation_key']).any():
        raise ValueError('Duplicate observation keys within region: check manifest before aggregation')
    rows=[]
    for region in LOCATIONS:
        print(f'\n========== {region} ==========',flush=True)
        try: roi=dem_window(region); err=None
        except Exception as exc: roi=None; err=str(exc)
        for row in manifest[manifest['region']==region].to_dict('records'):
            result=scene_row(row,roi) if roi is not None else dict(row,quality_status='error',error=err)
            rows.append(result)
            val=result.get('brightness_mean_k'); cov=result.get('valid_area_pct')
            print(f"  {result['pdsid']} | {result['quality_status']} | " + (f'{val:.2f} K | ' if val is not None else '')+(f'{cov:.2f}% | ' if cov is not None else '')+str(result.get('band_group',''))+(' | '+result['error'] if result.get('error') else ''),flush=True)
    if not rows: raise ValueError('No manifest observations for known regions')
    scenes=pd.DataFrame(rows)
    # Stable output schema even when all scenes fail; blank means missing.
    for field in ('band_group','brightness_mean_k','brightness_min_k','brightness_max_k','valid_area_pct','label_solar_longitude_deg','solar_longitude_deg'):
        if field not in scenes: scenes[field]=np.nan
    scene_file=FEATURES/'themis_scene_features.csv'; summary_file=FEATURES/'themis_thermal_features.csv'
    scenes.to_csv(scene_file,index=False)
    summary=summarize(scenes); summary.to_csv(summary_file,index=False)
    print('\nQuality counts:\n'+scenes['quality_status'].value_counts().to_string())
    print('\nOutput:',scene_file,'\nOutput:',summary_file)
    print('Accepted scenes:',int((scenes['quality_status']=='ok').sum()),'/',len(scenes))
    print('Pilot observations only; no climatology, no PAI changes; unverified bands kept separate.')


if __name__=='__main__':
    main()
