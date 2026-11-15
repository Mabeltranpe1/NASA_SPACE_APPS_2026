"""GeoAnalog | LRO Diviner PRP V2.0, south pole.
Run from the repository: python src/extract_thermal_moon.py
Source: https://doi.org/10.17189/1520650 ; Diviner RDR SIS v1.21, sec. 7.
Native triangular facets; horizontal equal-area weighting (not sloped 3-D area).
"""
from pathlib import Path
import io
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import rasterio
from pyproj import CRS, Transformer
import shapely
from shapely.geometry import Polygon

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / 'data/raw/thermal/moon/diviner'
DEMS = BASE / 'data/processed/moon'
OUT = BASE / 'data/features'
TAB = RAW / 'dlre_prp_south.tab'
XML = RAW / 'dlre_prp_south.xml'
LBL = RAW / 'dlre_prp_south.lbl'
REGIONS = ['Connecting_Ridge', 'Shackleton_Rim', 'Peak_Near_Shackleton',
           'De_Gerlache_Rim', 'Leibnitz_Beta_Plateau', 'Malapert_Massif']
R = 1737400.0
RECORD_BYTES = 210
N_ROWS = 2_880_000
CHUNK = 100_000
MIN_COVERAGE = 80.0  # exploratory GeoAnalog flag
GEO = CRS.from_proj4(f'+proj=longlat +R={R} +no_defs')
EA = CRS.from_proj4(f'+proj=laea +lat_0=-90 +lon_0=0 +R={R} +units=m +no_defs')
TO_EA = Transformer.from_crs(GEO, EA, always_xy=True)
SOURCE = 'LRO Diviner PRP V2.0 (LRO-L-DLRE-5-PRP-V2.0)'


def xml_slices(path):
    """PDS4 character table field offsets, if present; optional fallback."""
    root = ET.parse(path).getroot()
    for table in root.iter():
        if table.tag.split('}')[-1] != 'Record_Character':
            continue
        fields = []
        for node in table:
            if node.tag.split('}')[-1] != 'Field_Character':
                continue
            d = {c.tag.split('}')[-1]: c.text for c in node}
            if 'field_location' not in d or 'field_length' not in d:
                continue
            start = int(d['field_location']) - 1
            fields.append((start, start + int(d['field_length'])))
        if len(fields) == 15:
            return sorted(fields)
    return None


def parse_records(raw, sep, slices=None):
    if len(raw) % RECORD_BYTES:
        raise ValueError('Incomplete fixed-length record.')
    n = len(raw) // RECORD_BYTES
    if slices is not None:
        dt = np.dtype({'names': [f'f{i}' for i in range(15)],
                       'formats': [f'S{b-a}' for a,b in slices],
                       'offsets': [a for a,b in slices], 'itemsize': RECORD_BYTES})
        rec = np.frombuffer(raw, dtype=dt)
        a = np.column_stack([rec[f'f{i}'].astype(float) for i in range(15)])
    else:
        # PDS ASCII includes CRLF. Whitespace or comma separation is detected.
        a = np.loadtxt(io.BytesIO(raw), delimiter=sep, dtype=np.float64, ndmin=2)
    if a.shape != (n, 15):
        raise ValueError(f'Expected {n} rows x 15 columns; got {a.shape}.')
    return a


def read_batches(tab, xml, n_rows=N_ROWS, chunk=CHUNK):
    with tab.open('rb') as f:
        header = f.read(RECORD_BYTES)
        print('PRP header:', header.decode('ascii', errors='replace').strip())
        probe = f.read(RECORD_BYTES * min(n_rows, 4))
        if not probe:
            raise ValueError('Empty PRP table.')
        sep = ',' if b',' in probe[:RECORD_BYTES] else None
        slices = None
        try:
            parse_records(probe, sep)
        except ValueError:
            slices = xml_slices(xml)
            if slices is None:
                raise ValueError('Cannot parse PRP records. Inspect XML and first data row.')
            parse_records(probe, sep, slices)
        print('Parser:', 'XML fixed fields' if slices else ('comma' if sep else 'whitespace'))
        f.seek(RECORD_BYTES)
        total = 0
        while total < n_rows:
            count = min(chunk, n_rows - total)
            raw = f.read(RECORD_BYTES * count)
            if len(raw) != RECORD_BYTES * count:
                raise ValueError(f'Unexpected EOF at row {total+1}.')
            a = parse_records(raw, sep, slices)
            yield total, a
            total += count
        if f.read(1):
            raise ValueError('Unexpected data after last declared PRP record.')


def footprint(name, dem_dir=DEMS):
    path = dem_dir / f'{name}_DEM_200m.tif'
    if not path.is_file():
        raise FileNotFoundError(f'Missing processed DEM: {path}')
    with rasterio.open(path) as src:
        crs = CRS.from_wkt(src.crs.to_wkt()) if src.crs else None
        if not crs or not crs.is_projected or not crs.geodetic_crs:
            raise ValueError(f'{name}: invalid lunar projected CRS.')
        if abs(crs.ellipsoid.semi_major_metre - R) > 1 or abs(crs.ellipsoid.semi_minor_metre - R) > 1:
            raise ValueError(f'{name}: unexpected lunar radius.')
        if src.width != 50 or src.height != 50 or not np.allclose(src.res, [200, 200], atol=.01):
            raise ValueError(f'{name}: expected processed 50x50 DEM at 200 m.')
        # Densify the true raster perimeter before converting to equal-area.
        corners = [(0,0), (src.width,0), (src.width,src.height), (0,src.height)]
        pix = []
        for i,(c0,r0) in enumerate(corners):
            c1,r1 = corners[(i+1)%4]
            pix.extend((c0+t*(c1-c0), r0+t*(r1-r0)) for t in np.linspace(0,1,33,endpoint=False))
        xy = np.array([src.transform * p for p in pix])
        to_geo = Transformer.from_crs(crs, crs.geodetic_crs, always_xy=True)
        lon,lat = to_geo.transform(xy[:,0],xy[:,1])
        cx,cy = src.transform * (src.width/2,src.height/2)
        clon,clat = to_geo.transform(cx,cy)
        if not np.all(np.isfinite(lat)) or np.min(lat) < -90.000001 or np.max(lat) > -75:
            raise ValueError(f'{name}: DEM is not in lunar south polar region.')
        x,y = TO_EA.transform(lon,lat)
        poly = Polygon(np.column_stack([x,y]))
        if not poly.is_valid or not 90e6 < poly.area < 110e6:
            raise ValueError(f'{name}: invalid footprint or unexpected area {poly.area}.')
    return {'name': name, 'path': path.name, 'poly': poly, 'lat': clat,
            'lon': clon % 360, 'parts': []}


def vertices_equal_area(a):
    # PDS vertex XYZ are Moon-centered Cartesian coordinates in kilometres.
    v = a[:,:9].reshape(-1,3,3)
    x,y,z = v[:,:,0],v[:,:,1],v[:,:,2]
    radius = np.sqrt(x*x+y*y+z*z)
    good = (np.isfinite(v).all(axis=(1,2)) & (radius > 1600).all(axis=1)
            & (radius < 1900).all(axis=1) & (z < 0).all(axis=1))
    lon = np.degrees(np.arctan2(y,x))
    lat = np.degrees(np.arctan2(z,np.hypot(x,y)))
    px,py = TO_EA.transform(lon,lat)
    coords = np.stack([px,py], axis=-1)
    good &= np.isfinite(coords).all(axis=(1,2))
    return coords, good


def check_centers(a, good):
    # Independent consistency check on the first valid records.
    sub = a[good][:1000]
    if not len(sub):
        return False
    v = sub[:,:9].reshape(-1,3,3).mean(axis=1)
    lo = np.degrees(np.arctan2(v[:,1],v[:,0]))
    la = np.degrees(np.arctan2(v[:,2],np.hypot(v[:,0],v[:,1])))
    x,y = TO_EA.transform(lo,la)
    cx,cy = TO_EA.transform(sub[:,9],sub[:,10])
    err = np.hypot(x-cx,y-cy)
    if not np.isfinite(err).all() or np.max(err) > 1000:
        raise ValueError('Vertex/center consistency check failed (over 1 km). Check PRP field order.')
    print(f'Vertex/center check: max {np.max(err):.1f} m ({len(sub)} records).')
    return True


def collect(regions, batches):
    checked = False
    invalid_vertices = 0
    for offset, a in batches:
        xy,good = vertices_equal_area(a)
        invalid_vertices += int((~good).sum())
        if not checked:
            checked = check_centers(a,good)
        xmin,xmax = xy[:,:,0].min(axis=1),xy[:,:,0].max(axis=1)
        ymin,ymax = xy[:,:,1].min(axis=1),xy[:,:,1].max(axis=1)
        for region in regions:
            poly = region['poly']
            l,b,r,t = poly.bounds
            ix = np.flatnonzero(good & (xmax>=l)&(xmin<=r)&(ymax>=b)&(ymin<=t))
            if not len(ix):
                continue
            tris = shapely.polygons(xy[ix])
            if not np.all(shapely.is_valid(tris)):
                tris = shapely.make_valid(tris)
            area = shapely.area(shapely.intersection(tris,poly))
            keep = np.isfinite(area) & (area > 0.01)
            ix,area = ix[keep],area[keep]
            subset = a[ix]
            if len(ix):
                region['parts'].append(pd.DataFrame({
                    'region':region['name'], 'planet':'moon', 'prp_record':offset+ix+1,
                    'center_lon_east_deg':subset[:,9]%360, 'center_lat_deg':subset[:,10],
                    'center_alt_km':subset[:,11], 'intersection_area_m2':area,
                    'annual_avg_2cm_k_raw':subset[:,12], 'annual_max_surface_k_raw':subset[:,13],
                    'ice_depth_m_raw':subset[:,14]}))
        if (offset+len(a)) % 500000 == 0 or offset+len(a)==N_ROWS:
            print(f'PRP records read: {offset+len(a):,}')
    if not checked:
        raise ValueError('No valid vertices in PRP.')
    print('Invalid vertex records skipped:',invalid_vertices)


def weighted(values, weights, valid):
    use = valid & np.isfinite(values) & np.isfinite(weights) & (weights>0)
    if not use.any():
        return dict(mean=np.nan,std=np.nan,min=np.nan,max=np.nan)
    x,w = values[use],weights[use]
    mean = np.average(x,weights=w)
    return dict(mean=mean,std=np.sqrt(np.average((x-mean)**2,weights=w)),min=x.min(),max=x.max())


def summarize(region):
    area = region['poly'].area
    d = pd.concat(region['parts'], ignore_index=True) if region['parts'] else pd.DataFrame(columns=[
        'region','planet','prp_record','center_lon_east_deg','center_lat_deg','center_alt_km',
        'intersection_area_m2','annual_avg_2cm_k_raw','annual_max_surface_k_raw','ice_depth_m_raw'])
    w = d['intersection_area_m2'].to_numpy(dtype=float)
    avg = d['annual_avg_2cm_k_raw'].to_numpy(dtype=float)
    mx = d['annual_max_surface_k_raw'].to_numpy(dtype=float)
    ice = d['ice_depth_m_raw'].to_numpy(dtype=float)
    # Sentinel -32768 is documented for ice depths exceeding 2.8738 m.
    va = np.isfinite(avg)&(avg>0)&(avg<500)
    vm = np.isfinite(mx)&(mx>0)&(mx<500)
    vi = np.isfinite(ice)&(ice>=0)&(ice<=2.8738+1e-8)
    deep = ice == -32768
    surface = vi & (ice==0)
    d['annual_avg_2cm_valid'] = va
    d['annual_max_surface_valid'] = vm
    d['ice_depth_status'] = np.select([surface,vi,deep],['surface_stable_model','finite_depth_model','beyond_2.8738m_code'], default='invalid_or_missing')
    pct = lambda mask: float(w[mask].sum()/area*100)
    covered = float(w.sum()/area*100)
    if covered > 100.5:
        raise ValueError(f'{region["name"]}: mesh overlap {covered:.3f}% exceeds expected coverage.')
    row = dict(region=region['name'], planet='moon', latitude=region['lat'], longitude_east_deg=region['lon'],
               footprint_dem=region['path'], study_area_km2=area/1e6, native_facets_intersecting=len(d),
               mesh_coverage_pct=covered, annual_avg_2cm_valid_area_pct=pct(va),
               annual_max_surface_valid_area_pct=pct(vm), ice_depth_reported_area_pct=pct(vi),
               ice_depth_beyond_limit_area_pct=pct(deep), ice_surface_stable_model_area_pct=pct(surface),
               ice_depth_classified_area_pct=pct(vi|deep), ice_depth_invalid_in_mesh_area_pct=pct(~(vi|deep)),
               thermal_quality_status=('ok' if min(pct(va),pct(vm))>=MIN_COVERAGE else ('low_coverage' if va.any() or vm.any() else 'no_valid_temperature')),
               ice_depth_coverage_status=('ok' if pct(vi|deep)>=MIN_COVERAGE else ('low_coverage' if (vi|deep).any() else 'no_classified_depth')),
               source=SOURCE, coordinate_frame='Moon ME (assumed co-registration to LOLA DE421)',
               area_weighting='horizontal spherical equal-area; native facets',
               ice_depth_note='conditional finite depths; code -32768 is beyond model reporting limit, not zero')
    for tag,values,valid,unit in [('annual_avg_2cm',avg,va,'k'),('annual_max_surface',mx,vm,'k'),('ice_depth_finite',ice,vi,'m')]:
        for key,val in weighted(values,w,valid).items():
            row[f'{tag}_{key}_{unit}'] = val
    return row,d


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for p in (TAB,XML,LBL):
        if not p.is_file():
            raise FileNotFoundError(p)
    if TAB.stat().st_size != RECORD_BYTES*(N_ROWS+1):
        raise ValueError(f'Unexpected TAB size: {TAB.stat().st_size:,} bytes.')
    label = LBL.read_text(encoding='ascii')
    if 'LRO-L-DLRE-5-PRP-V2.0' not in label:
        raise ValueError('Expected PRP V2.0 label.')
    regions = [footprint(n) for n in REGIONS]
    for r in regions:
        print(f'{r["name"]}: {r["lat"]:.6f} deg, {r["lon"]:.6f} E | area {r["poly"].area/1e6:.3f} km2')
    collect(regions,read_batches(TAB,XML))
    rows,facets = [],[]
    for r in regions:
        info,d = summarize(r)
        rows.append(info); facets.append(d)
        print(f'\n{r["name"]}: {len(d)} facets | mesh {info["mesh_coverage_pct"]:.2f}%')
        print(f'  Annual avg at 2 cm: {info["annual_avg_2cm_mean_k"]:.2f} K | coverage {info["annual_avg_2cm_valid_area_pct"]:.2f}%')
        print(f'  Annual surface max (mean): {info["annual_max_surface_mean_k"]:.2f} K | coverage {info["annual_max_surface_valid_area_pct"]:.2f}%')
        print(f'  Model surface ice stability: {info["ice_surface_stable_model_area_pct"]:.2f}% of window | classified {info["ice_depth_classified_area_pct"]:.2f}% | {info["thermal_quality_status"]}')
    summary = pd.DataFrame(rows)
    detail = pd.concat(facets,ignore_index=True)
    for df, filename in [(summary,'thermal_moon_features.csv'),(detail,'thermal_moon_facets.csv')]:
        p = OUT / filename
        df.to_csv(p,index=False,float_format='%.8f',na_rep='')
        print('Output:',p)
    print(f'Completed: {len(rows)}/{len(REGIONS)} regions. Missing statistics left blank.')
    print('Model ice stability does NOT establish ice presence. No interpolation, no PAI changes.')


if __name__ == '__main__':
    main()
