"""GeoAnalog: targeted MTRDR recovery (Phoenix and Pathfinder).
Save in src/ next to download_crism.py. Run from project root.
Uses cached ODE XML; matches IF catalogue IDs to SR/SU siblings by exact identity.
Does not redownload MRDR mosaics or change PAI. Keeps successful manifest rows.
"""
from pathlib import Path
from datetime import datetime
import json
import math
import re
import shutil
import xml.etree.ElementTree as ET

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from shapely.geometry import box
import download_crism as dc

OUT, RAW = dc.FEATURES, dc.RAW
MANIFEST = OUT / 'crism_downloads.csv'
REGIONS = ('Phoenix', 'Pathfinder')
MAX_PER_REGION = 3
BUDGET = 1500 * 1024**2  # new completed bytes; failed transfers may add traffic
ID = re.compile(r'(?P<prefix>(?:FRT|HRL|HRS)[0-9a-f]{8}_[0-9a-f]{2}_)'
                r'(?P<kind>IF|SR|SU)(?P<suffix>\d{3}J_MTR[0-9a-z])', re.I)


def choose_siblings(pid, files):
    match = ID.fullmatch(pid)
    if not match:
        return []
    choices = []
    for kind in ('SR', 'SU'):
        stem = (match['prefix'] + kind + match['suffix']).upper()
        by_ext = {}
        for f in files:
            name = f['name']
            suffix = Path(name).suffix.lower()
            if Path(name).stem.upper() in (stem, stem + '.IMG') and suffix in ('.img', '.lbl', '.xml', '.hdr'):
                if suffix == '.img' and Path(name).stem.upper() != stem:
                    continue
                by_ext.setdefault(suffix, f)
        if '.img' not in by_ext or not ({'.lbl', '.xml'} & by_ext.keys()):
            continue
        items = list(by_ext.values())
        if any(f['kbytes'] is not None and f['kbytes'] * 1024 > dc.MAX_FILE_BYTES for f in items):
            continue
        choices.append((kind, stem, items, by_ext['.img']))
    return choices


def get_candidates(q, pages):
    roi = box(float(q.westernlon), float(q.minlat), float(q.easternlon), float(q.maxlat))
    rows = []
    for p in pages:
        root = ET.parse(p).getroot()
        if dc.fields(root).get('status', '').lower() != 'success':
            raise ValueError(f'Unsuccessful ODE response: {p.name}')
        for product in root.iter():
            if dc.local(product.tag) != 'product':
                continue
            meta = dc.fields(product)
            pid = meta.get('pdsid') or meta.get('product_lid') or ''
            files = dc.product_files(product, meta)
            options = choose_siblings(pid, files)
            if not options:
                continue
            kind, stem, items, image = options[0]  # SR before SU for same catalogue entry
            rows.append(dict(region=q.region, product_type='MTRDR', pdsid=pid,
                             ode_id=meta.get('ode_id', ''), dataset_id=meta.get('data_set_id', ''),
                             utc=meta.get('utc_start_time') or meta.get('observation_time', ''),
                             footprint_overlap_bbox_pct=dc.footprint_pct(meta, roi),
                             subtype=kind, observation_key=stem.split('_')[0],
                             science_name=image['name'], science_url=image['url'],
                             eligible=True, reason='eligible_exact_sibling', files=items))
    def rank(r):
        cov = r['footprint_overlap_bbox_pct']
        return (cov if cov is not None else -1, r['subtype']=='SR', r['utc'])
    unique = {}
    for r in sorted(rows, key=rank, reverse=True):
        unique.setdefault(r['observation_key'], r)
    return list(unique.values())


def download_one(session, row, remaining):
    folder = RAW / row['region'] / 'MTRDR' / Path(row['science_name']).stem
    folder.mkdir(parents=True, exist_ok=True)
    rec = {k:v for k,v in row.items() if k != 'files'}
    rec.update(status='error', error='', image_path='', label_paths='[]', header_paths='[]', file_urls='[]', files_ready=0)
    completed=[]; new_bytes=0
    items=sorted(row['files'], key=lambda f: Path(f['name']).suffix.lower()=='.img')
    rec['file_urls']=json.dumps([f['url'] for f in items])
    try:
        for f in items:
            dest=folder/f['name']
            # The shared downloader verifies transfer sizes and rejects HTML.
            n,status=dc.download(session,f,dest,remaining-new_bytes)
            new_bytes+=n; completed.append(dest)
            print(f'    {dest.name}: {status}',flush=True)
        images=[p for p in completed if p.suffix.lower()=='.img']
        labels=[p for p in completed if p.suffix.lower() in ('.lbl','.xml')]
        headers=[p for p in completed if p.suffix.lower()=='.hdr']
        if len(images)!=1 or not labels:
            raise RuntimeError('Missing unique image or detached label')
        rec.update(status='files_ready',image_path=str(images[0].relative_to(dc.BASE)),
                   label_paths=json.dumps([str(p.relative_to(dc.BASE)) for p in labels]),
                   header_paths=json.dumps([str(p.relative_to(dc.BASE)) for p in headers]))
    except Exception as exc:
        rec['error']=str(exc)
    rec['files_ready']=len(completed)
    return rec,new_bytes


def update_manifest(rec):
    manifest=pd.read_csv(MANIFEST,dtype=str,keep_default_na=False)
    same=(manifest.region==rec['region']) & (manifest.science_name.str.casefold()==rec['science_name'].casefold())
    merged=pd.concat([manifest.loc[~same],pd.DataFrame([rec])],ignore_index=True)
    temp=MANIFEST.with_suffix('.csv.tmp')
    merged.to_csv(temp,index=False)
    temp.replace(MANIFEST)


def main():
    availability=pd.read_csv(OUT/'crism_availability.csv')
    manifest=pd.read_csv(MANIFEST,dtype=str,keep_default_na=False)
    ready={(r.region,r.science_name.casefold()) for r in manifest.itertuples() if r.status=='files_ready'}
    all_candidates=[]; selected=[]
    for region in REGIONS:
        print(f'\n========== {region} ==========',flush=True)
        qs=availability[(availability.region==region)&(availability.product_type=='MTRDR')]
        pages=sorted((RAW/'catalogue').glob(f'{region}_MTRDR_details_*.xml'))
        if len(qs)!=1 or not pages:
            print('  Missing cached catalogue; not attempting a guessed download.'); continue
        rows=get_candidates(next(qs.itertuples(index=False)),pages)
        print(f'  Candidate observations: {len(rows)}')
        all_candidates.extend(rows)
        for row in rows[:MAX_PER_REGION]:
            print(f"  {row['science_name']} | catalogue overlap {row['footprint_overlap_bbox_pct']}")
            selected.append(row)
    pd.DataFrame([{k:v for k,v in r.items() if k!='files'} for r in all_candidates]).to_csv(OUT/'crism_targeted_candidates.csv',index=False)
    if not selected:
        print('No candidates; original manifest unchanged.'); return
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup=MANIFEST.with_name(f'crism_downloads_backup_{stamp}.csv')
    shutil.copy2(MANIFEST,backup)
    log=[]; total=0
    with requests.Session() as session:
        session.mount('https://',HTTPAdapter(max_retries=Retry(total=2,backoff_factor=1,status_forcelist=(429,500,502,503,504),allowed_methods=('GET',))))
        # Alternate regions so one does not consume the entire budget first.
        selected.sort(key=lambda r: [x['observation_key'] for x in all_candidates if x['region']==r['region']].index(r['observation_key']))
        for row in selected:
            key=(row['region'],row['science_name'].casefold())
            if key in ready:
                print(f'  {key}: already registered; skipped'); continue
            if total>=BUDGET:
                print('Budget exhausted; remaining products not attempted.'); break
            print(f"\n{row['region']} | {row['science_name']}",flush=True)
            rec,n=download_one(session,row,BUDGET-total)
            total+=n; log.append(rec)
            print('  Status:',rec['status'],rec['error'],flush=True)
            if rec['status']=='files_ready':
                update_manifest(rec); ready.add(key)
            pd.DataFrame(log).to_csv(OUT/'crism_targeted_recovery.csv',index=False)
    print(f'\nNew completed downloads: {total/1024**2:.1f} MiB')
    print('New ready products:',sum(r['status']=='files_ready' for r in log))
    print('Manifest backup:',backup)
    print('Run python src/extract_crism.py next. Valid ROI coverage is still unverified.')

if __name__=='__main__':
    main()
