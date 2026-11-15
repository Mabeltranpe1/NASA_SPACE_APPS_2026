"""GeoAnalog — CRISM pilot native-pixel spectral parameter statistics.
Run: python src/extract_crism.py
Requires existing download_crism.py manifest and processed Mars DEMs.
No downloads, no concentration estimates, no PAI changes.
References: NASA PDS CRISM SIS v1.3.7.7, Appendix D3; ODE MRDR4/MTRDR primers.
"""
from pathlib import Path
import csv
import json
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
OUT = BASE / 'data' / 'features'
RAW = BASE / 'data' / 'raw' / 'spectral' / 'mars' / 'crism'
DEM = BASE / 'data' / 'processed' / 'mars'
LOC = {'Jezero': (18.4447,77.4508), 'Gale':(-4.59,137.44), 'Phoenix':(68.22,234.25),
       'Pathfinder':(19.095,326.747), 'Viking_1':(22.269,312.049), 'Viking_2':(47.668,134.28)}
PARAMS = {'OLINDEX3':'olivine spectral indicator','LCPINDEX2':'low-Ca pyroxene indicator',
          'HCPINDEX2':'high-Ca pyroxene indicator','BD530_2':'ferric/hematite-related absorption',
          'D2300':'Fe/Mg-OH spectral indicator','BD2210_2':'Al-OH-related absorption',
          'BD1900_2':'hydration-related absorption','SINDEX2':'hydrated sulfate spectral indicator',
          'CINDEX2':'carbonate-related spectral indicator'}
MIN_COVERAGE = 80.


def local(tag):
    return tag.rsplit('}',1)[-1].lower()


def txt(p):
    return p.read_text(encoding='utf-8',errors='replace')


def num(v):
    try:
        x=float(str(v).strip().strip('"').split('<')[0]); return x if math.isfinite(x) else None
    except (ValueError,TypeError): return None


def parse_list(s):
    return [x.strip().strip('"\'') for x in next(csv.reader([s.replace('\n',' ').replace('\r',' ')],skipinitialspace=True))]


def label_info(p):
    names=[]; missing=[]; scale={}; offset={}; direction=[]; lat_type=[]
    if p.suffix.lower()=='.lbl':
        text=re.sub(r'/\*[\s\S]*?\*/','',txt(p))
        m=re.search(r'\bBAND_NAME\s*=\s*\((.*?)\)',text,re.S|re.I)
        if m: names=parse_list(m[1])
        for k,v in re.findall(r'^\s*([A-Z_]+)\s*=\s*([^\r\n]+)',text,re.M):
            if k in ('MISSING_CONSTANT','NULL_CONSTANT','INVALID_CONSTANT','NULL') and num(v) is not None: missing.append(num(v))
            if k=='POSITIVE_LONGITUDE_DIRECTION': direction.append(v.strip().strip('"').upper())
            if k=='COORDINATE_SYSTEM_NAME': lat_type.append(v.strip().strip('"').upper())
            if k=='SCALING_FACTOR' and num(v) is not None: scale[0]=num(v)
            if k in ('OFFSET','VALUE_OFFSET') and num(v) is not None: offset[0]=num(v)
    elif p.suffix.lower()=='.xml':
        root=ET.parse(p).getroot(); pairs={}
        for e in root.iter():
            k=local(e.tag); v=(e.text or '').strip()
            if k=='crism_band':
                f={local(c.tag):(c.text or '').strip() for c in e}
                i=num(f.get('band_sequence_number')); n=f.get('band_name')
                if i is not None and i.is_integer() and n:
                    i=int(i)
                    if i in pairs and pairs[i]!=n: raise ValueError('Conflicting XML band names')
                    pairs[i]=n
                    if num(f.get('scaling_factor')) is not None: scale[i]=num(f['scaling_factor'])
                    if num(f.get('value_offset')) is not None: offset[i]=num(f['value_offset'])
            if k=='special_constants':
                for c in e:
                    if local(c.tag).endswith('_constant') and num(c.text) is not None: missing.append(num(c.text))
            if k=='element_array':
                for c in e:
                    if local(c.tag)=='scaling_factor' and num(c.text) is not None: scale[0]=num(c.text)
                    if local(c.tag)=='value_offset' and num(c.text) is not None: offset[0]=num(c.text)
            if k=='longitude_direction': direction.append(v.upper())
            if k=='latitude_type': lat_type.append(v.upper())
        if pairs and sorted(pairs)==list(range(1,len(pairs)+1)): names=[pairs[i] for i in sorted(pairs)]
    elif p.suffix.lower()=='.hdr':
        m=re.search(r'band names\s*=\s*\{(.*?)\}',txt(p),re.S|re.I)
        if m: names=parse_list(m[1])
    return dict(names=[x.strip().upper() for x in names],missing=missing,scale=scale,offset=offset,
                longitude=direction,latitude=lat_type)


def get_paths(s):
    if not isinstance(s,str) or not s.strip(): return []
    try: return [BASE / p for p in json.loads(s)]
    except (ValueError,TypeError): return []


def open_product(row):
    image=BASE / row['image_path']
    if not image.is_file(): raise FileNotFoundError(image)
    labels=get_paths(row.get('label_paths'))+get_paths(row.get('header_paths'))
    labels += [p for p in image.parent.iterdir() if p.suffix.lower() in ('.lbl','.xml','.hdr') and p.stem.lower() in (image.stem.lower(),image.name.lower())]
    labels=list(dict.fromkeys(p for p in labels if p.is_file()))
    metadata=[(p,label_info(p)) for p in labels]
    errors=[]
    for p in sorted([p for p in labels if p.suffix.lower() in ('.lbl','.xml')],key=lambda p:p.suffix.lower()!='.lbl'):
        try:
            ds=rasterio.open(p)
            try:
                if ds.driver not in ('PDS','PDS4') or ds.crs is None or ds.transform.is_identity: raise ValueError('Missing verified PDS projection')
                if image.resolve() not in {Path(f).resolve() for f in ds.files}: raise ValueError('Label does not reference manifest image')
                if not ds.count>1: raise ValueError('Expected multiband science image')
                labeled=[(f.name,d['names']) for f,d in metadata if d['names']]
                if any(len(n)!=ds.count for _,n in labeled): raise ValueError('Band count inconsistent with metadata')
                if not labeled:
                    desc=[str(v or '').strip().upper() for v in ds.descriptions]
                    if all(desc) and set(desc)&set(PARAMS): labeled=[('GDAL band descriptions',desc)]
                if not labeled: raise ValueError('No explicit band names found; never assume order')
                names=labeled[0][1]
                if any(n!=names for _,n in labeled[1:]): raise ValueError('Conflicting band names across metadata')
                if len(set(names))!=len(names): raise ValueError('Duplicate band names')
                if not set(names)&set(PARAMS): raise ValueError('No requested spectral parameters')
                active=label_info(p)
                active['missing']=list({v for _,d in metadata for v in d['missing']})
                active['longitude']=[v for _,d in metadata for v in d['longitude']]
                active['latitude']=[v for _,d in metadata for v in d['latitude']]
                # CRISM MRRSU is a float science product, documented missing constant 65535.
                if row['subtype']=='MRRSU': active['missing'].append(65535.)
                if not active['missing'] and all(v is None for v in ds.nodatavals): raise ValueError('No explicit missing-data convention')
                return ds,p,names,active,image
            except Exception: ds.close(); raise
        except Exception as exc: errors.append(f'{p.name}: {exc}')
    raise ValueError(' | '.join(errors) or 'No usable PDS label')


def roi_in_source(region,ds,meta):
    with rasterio.open(DEM/f'{region}_DEM_200m.tif') as d:
        c=CRS.from_user_input(d.crs); b=d.bounds
        if not c.is_projected or not 3.3e6<c.ellipsoid.semi_major_metre<3.5e6 or (d.width,d.height)!=(50,50) or not np.allclose(d.res,(200,200)):
            raise ValueError('Expected 50x50 Mars DEM at 200m')
        inv=Transformer.from_crs(c,c.geodetic_crs,always_xy=True)
        lon0,lat0=inv.transform((b.left+b.right)/2,(b.bottom+b.top)/2)
        lat,lon=LOC[region]
        if abs(lat0-lat)>.02 or abs((lon0-lon+180)%360-180)>.02: raise ValueError('DEM center mismatch')
        t=np.linspace(0,1,41)
        x=np.concatenate([b.left+(b.right-b.left)*t,np.full(t.size,b.right),b.right-(b.right-b.left)*t,np.full(t.size,b.left)])
        y=np.concatenate([np.full(t.size,b.bottom),b.bottom+(b.top-b.bottom)*t,np.full(t.size,b.top),b.top-(b.top-b.bottom)*t])
        lon,lat=inv.transform(x,y)
    c=CRS.from_user_input(ds.crs); a=c.ellipsoid.semi_major_metre; b=c.ellipsoid.semi_minor_metre
    if not c.is_projected or not(3.3e6<a<3.5e6 and 3.3e6<b<3.5e6): raise ValueError('Expected projected Mars CRS')
    if not all(abs(ax.unit_conversion_factor-1)<1e-8 for ax in c.axis_info[:2]): raise ValueError('Not metres')
    if any('WEST' in v for v in meta['longitude']): raise ValueError('West-positive label requires validation')
    # This pilot accepts spherical CRISM maps only to avoid latitude-type ambiguity.
    if abs(a-b)>1 or any('GRAPHIC' in v or 'DETIC' in v for v in meta['latitude']): raise ValueError('Non-spherical/planetographic source requires validation')
    x,y=Transformer.from_crs(c.geodetic_crs,c,always_xy=True).transform(lon,lat,errcheck=True)
    p=Polygon(np.column_stack([x,y]))
    if not p.is_valid or p.area<=0: raise ValueError('Invalid projected DEM footprint')
    return p


def cell_weights(ds,p):
    a=ds.transform
    if abs(a.b)>1e-8 or abs(a.d)>1e-8 or a.a<=0 or a.e>=0: raise ValueError('Rotated/inverted raster grid')
    l,b,r,t=p.bounds; c0,r0=(~a)*(l,t); c1,r1=(~a)*(r,b)
    c0=max(0,math.floor(c0)); r0=max(0,math.floor(r0)); c1=min(ds.width,math.ceil(c1)); r1=min(ds.height,math.ceil(r1))
    if c1<=c0 or r1<=r0: return None,None
    if (c1-c0)*(r1-r0)>5_000_000: raise ValueError('Unexpected ROI size')
    rr,cc=np.mgrid[r0:r1,c0:c1]; x=a.c+cc.ravel()*a.a; y=a.f+rr.ravel()*a.e
    w=shapely.area(shapely.intersection(shapely.box(x,y+a.e,x+a.a,y),p)).reshape(rr.shape)
    if w.sum()>p.area*1.00001: raise ValueError('Area mismatch')
    return Window(c0,r0,c1-c0,r1-r0),w


def analyze(row):
    ds,label,names,meta,image=open_product(row)
    try:
        roi=roi_in_source(row['region'],ds,meta); window,w=cell_weights(ds,roi)
        quality=dict(region=row['region'],product_type=row['product_type'],science_name=row['science_name'],label=label.name,
                     source_band_count=ds.count,band_names=';'.join(names),image_overlap_pct=0 if w is None else min(100.,100*w.sum()/roi.area),
                     native_pixel_x_m=ds.transform.a,native_pixel_y_m=-ds.transform.e, file_bytes=image.stat().st_size,status='processed')
        data=[]
        for name,meaning in PARAMS.items():
            rec=dict(region=row['region'],planet='mars',product_type=row['product_type'],subtype=row['subtype'],science_name=row['science_name'],
                     parameter=name,interpretation=meaning,valid_area_pct=0.,valid_pixel_count=0,quality_status='parameter_missing')
            if name not in names: data.append(rec); continue
            i=names.index(name)+1; rec['band_number']=i
            if window is None: rec['quality_status']='no_overlap'; data.append(rec); continue
            arr=ds.read(i,window=window,masked=True); raw=arr.data
            good=(~np.ma.getmaskarray(arr))&np.isfinite(raw)&(w>0)
            for m in meta['missing']: good &= raw!=m
            scale=meta['scale'].get(i,meta['scale'].get(0,ds.scales[i-1]))
            offset=meta['offset'].get(i,meta['offset'].get(0,ds.offsets[i-1]))
            if not math.isfinite(scale) or scale==0 or not math.isfinite(offset): raise ValueError('Bad scale/offset')
            v=raw.astype('float64')*scale+offset; good &= np.isfinite(v)
            coverage=min(100.,float(100*w[good].sum()/roi.area))
            rec.update(valid_area_pct=coverage,valid_pixel_count=int(good.sum()),scale=scale,offset=offset,quality_status='no_valid_pixels')
            if good.any():
                vv,ww=v[good],w[good]; mean=np.average(vv,weights=ww)
                rec.update(parameter_mean=mean,parameter_std=np.sqrt(np.average((vv-mean)**2,weights=ww)),parameter_min=vv.min(),parameter_max=vv.max(),
                           quality_status='ok' if coverage>=MIN_COVERAGE-1e-8 else 'low_coverage')
            data.append(rec)
        quality['status']='processed' if any(r['valid_pixel_count']>0 for r in data) else 'no_valid_data'
        print(f"  {image.name}: {quality['image_overlap_pct']:.2f}% image overlap; {sum(r['quality_status']=='ok' for r in data)}/{len(PARAMS)} parameters >=80%",flush=True)
        return quality,data
    finally: ds.close()


def catalogue_audit():
    """Local catalogue diagnostics; no automatic retry/download."""
    path=OUT/'crism_scene_catalogue.csv'
    if not path.is_file(): return
    df=pd.read_csv(path).fillna(''); rows=[]
    for r in df.to_dict('records'):
        if r['region'] not in ('Phoenix','Viking_2'): continue
        name=str(r.get('science_name') or r.get('pdsid') or '')
        m=re.search(r'T\d{4}_MRR[A-Z0-9]{2}_(\d{2})([NS])(\d{3})_',name,re.I)
        delta=None
        if m:
            a,lon=LOC[r['region']]; lat=int(m[1])*(1 if m[2].upper()=='N' else -1)
            dlon=(int(m[3])-lon+180)%360-180
            delta=math.degrees(math.acos(max(-1,min(1,math.sin(math.radians(a))*math.sin(math.radians(lat))+math.cos(math.radians(a))*math.cos(math.radians(lat))*math.cos(math.radians(dlon))))))
        rows.append(dict(r,tile_center_distance_deg=delta))
    audit=pd.DataFrame(rows)
    if not audit.empty:
        audit.sort_values(['region','product_type','tile_center_distance_deg'],na_position='last').to_csv(OUT/'crism_catalogue_audit.csv',index=False)
        for region in ('Phoenix','Viking_2'):
            part=audit[audit.region==region]
            print('\nCatalogue diagnosis:',region)
            if part.empty: print('  No catalogue rows'); continue
            print(part.groupby(['product_type','reason']).size().to_string())
            if region=='Viking_2':
                near=part[part.tile_center_distance_deg.notna()].sort_values('tile_center_distance_deg')
                print(near[['pdsid','science_name','tile_center_distance_deg','footprint_overlap_bbox_pct','reason']].head(8).to_string(index=False))
    # Also inspect exact file URLs returned for targeted Phoenix products, including related non-selected files.
    raw_rows=[]
    for p in sorted((RAW/'catalogue').glob('Phoenix_MTRDR_details_*.xml')):
        try:
            root=ET.parse(p).getroot()
            for product in root.iter():
                if local(product.tag)!='product': continue
                fields={local(ch.tag):(ch.text or '').strip() for ch in product}
                pid=fields.get('pdsid') or fields.get('product_lid') or ''
                for f in product.iter():
                    if local(f.tag)=='product_file':
                        m={local(ch.tag):(ch.text or '').strip() for ch in f}
                        raw_rows.append(dict(pdsid=pid,filename=m.get('filename',''),url=m.get('url',''),xml=p.name))
                for k in ('producturl','labelurl'):
                    if fields.get(k): raw_rows.append(dict(pdsid=pid,filename='',url=fields[k],xml=p.name))
        except Exception as exc: print(f'  XML audit error: {p.name}: {exc}')
    pd.DataFrame(raw_rows,columns=['pdsid','filename','url','xml']).to_csv(OUT/'crism_phoenix_catalogue_files.csv',index=False)


def main():
    manifest=pd.read_csv(OUT/'crism_downloads.csv').fillna('')
    quality=[]; results=[]
    for region in LOC:
        print('\n==========',region,'==========',flush=True)
        subset=manifest[(manifest.region==region)&(manifest.status=='files_ready')]
        if subset.empty:
            print('  No downloaded science product'); quality.append(dict(region=region,status='not_downloaded')); continue
        for r in subset.to_dict('records'):
            try:
                q,d=analyze(r); quality.append(q); results.extend(d)
            except Exception as exc:
                print('  ERROR:',exc,flush=True); quality.append(dict(region=region,science_name=r.get('science_name'),status='error',error=str(exc)))
    cols=['region','planet','product_type','subtype','science_name','parameter','interpretation','band_number','valid_area_pct','valid_pixel_count','scale','offset','parameter_mean','parameter_std','parameter_min','parameter_max','quality_status']
    df=pd.DataFrame(results).reindex(columns=cols)
    df.to_csv(OUT/'crism_parameter_features.csv',index=False)
    # Only coverage-qualified values enter the primary feature dataset. Explicit unavailable rows for regions/parameters.
    primary=[]
    for region in LOC:
        for name,meaning in PARAMS.items():
            v=df[(df.region==region)&(df.parameter==name)&(df.quality_status=='ok')]
            if v.empty: primary.append(dict(region=region,planet='mars',parameter=name,interpretation=meaning,quality_status='no_qualified_observation'))
            else: primary.extend(v.to_dict('records'))
    pd.DataFrame(primary).reindex(columns=cols).to_csv(OUT/'mineralogical_mars_features.csv',index=False)
    pd.DataFrame(quality).to_csv(OUT/'crism_scene_quality.csv',index=False)
    catalogue_audit()
    print('\nOutputs in',OUT)
    print('Qualified parameter rows:',int((df.quality_status=='ok').sum()))
    print('Qualified regions:',df.loc[df.quality_status=='ok','region'].nunique(),'/ 6')
    print('Spectral indicators only; no mineral concentration, no PAI changes.')

if __name__=='__main__': main()
