"""GeoAnalog: targeted recovery of Viking 2, local diagnostics of Phoenix and Pathfinder.
Save beside download_crism.py; run from project root: python src/recover_crism.py
No new catalogue queries; no downloads except the explicitly selected Viking 2 tile.
"""
from pathlib import Path
import json
import shutil
from datetime import datetime

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import download_crism as dc

TILE = 'T1687_MRRSU_50N137_0327_4.IMG'
BUDGET = 750 * 1024**2
OUT = dc.FEATURES
RAW = dc.RAW
MANIFEST = OUT / 'crism_downloads.csv'


def choose_tile(rows):
    hits = [r for r in rows if r['region'] == 'Viking_2'
            and r['product_type'] == 'MRDR4' and r['eligible']
            and r['science_name'].casefold() == TILE.casefold()]
    if not hits:
        raise RuntimeError('Correct tile not eligible in cached catalogue. Inspect Viking_2 MRDR4 XML.')
    return hits[0]


def find_tile():
    availability = pd.read_csv(OUT / 'crism_availability.csv')
    subset = availability[(availability.region == 'Viking_2') & (availability.product_type == 'MRDR4')]
    if len(subset) != 1:
        raise RuntimeError('Expected one Viking_2 MRDR4 availability row')
    q = next(subset.itertuples(index=False))
    pages = sorted((RAW / 'catalogue').glob('Viking_2_MRDR4_details_*.xml'))
    if not pages:
        raise FileNotFoundError('Viking_2 detailed catalogue XML is missing')
    return choose_tile([r for p in pages for r in dc.parse_products(p.read_bytes(), q)])


def diagnostics():
    print('\n========== Pathfinder: valid data ==========', flush=True)
    p = OUT / 'crism_parameter_features.csv'
    if p.exists():
        d = pd.read_csv(p)
        cols = ['parameter', 'valid_area_pct', 'valid_pixel_count', 'quality_status']
        print(d.loc[d.region == 'Pathfinder', cols].to_string(index=False))
    print('\n========== Phoenix: catalogue names ==========', flush=True)
    p = OUT / 'crism_phoenix_catalogue_files.csv'
    cat = OUT / 'crism_scene_catalogue.csv'
    if cat.exists():
        d = pd.read_csv(cat, dtype=str, keep_default_na=False)
        print(d.loc[d.region == 'Phoenix', ['pdsid','reason']].drop_duplicates().to_string(index=False))
    if p.exists():
        d = pd.read_csv(p, dtype=str, keep_default_na=False)
        d['filename'] = [name or dc.basename(url) for name,url in zip(d.filename,d.url)]
        d = d[['pdsid','filename','url']].drop_duplicates()
        d.to_csv(OUT / 'crism_phoenix_recovery_inventory.csv', index=False)
        print('Phoenix inventory:', len(d), 'file links')
        print(d[['pdsid','filename']].head(40).to_string(index=False))
    else:
        print('No Phoenix file inventory. Run extract_crism.py first.')


def main():
    diagnostics()
    manifest = pd.read_csv(MANIFEST, dtype=str, keep_default_na=False)
    row = find_tile()
    print('\n========== Viking_2: targeted recovery ==========', flush=True)
    print('Selected:', row['science_name'])
    print('Catalogue overlap (not valid coverage):', row['footprint_overlap_bbox_pct'])
    folder = RAW / 'Viking_2' / 'MRDR4' / Path(row['science_name']).stem
    folder.mkdir(parents=True, exist_ok=True)
    rec = {k:v for k,v in row.items() if k != 'files'}
    rec.update(status='error', error='', image_path='', label_paths='[]', header_paths='[]', file_urls='[]', files_ready=0)
    completed = []
    new_bytes = 0
    items = sorted(row['files'], key=lambda f: Path(f['name']).suffix.lower() == '.img')
    try:
        with requests.Session() as session:
            session.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=1,
                status_forcelist=(429,500,502,503,504), allowed_methods=('GET',))))
            for f in items:
                dest = folder / f['name']
                n, status = dc.download(session, f, dest, BUDGET-new_bytes)
                new_bytes += n
                completed.append(dest)
                print(f"  {dest.name}: {status}", flush=True)
        if len(completed) != len(items):
            raise RuntimeError('Incomplete file set')
        rec['status'] = 'files_ready'
    except Exception as exc:
        rec['error'] = str(exc)
    rec['files_ready'] = len(completed)
    rec['image_path'] = next((str(p.relative_to(dc.BASE)) for p in completed if p.suffix.lower()=='.img'), '')
    rec['label_paths'] = json.dumps([str(p.relative_to(dc.BASE)) for p in completed if p.suffix.lower() in ('.xml','.lbl')])
    rec['header_paths'] = json.dumps([str(p.relative_to(dc.BASE)) for p in completed if p.suffix.lower()=='.hdr'])
    rec['file_urls'] = json.dumps([f['url'] for f in items])
    pd.DataFrame([rec]).to_csv(OUT / 'crism_viking2_recovery.csv', index=False)
    print('Status:', rec['status'], rec['error'])
    print('New download:', round(new_bytes/1024**2, 1), 'MiB')
    if rec['status'] != 'files_ready':
        print('Original manifest unchanged; rerun after resolving the error.')
        return
    if not rec['image_path'] or rec['label_paths']=='[]':
        raise RuntimeError('Missing image or label; manifest not changed')
    # Only replace rows for this exact tile, not earlier observations or failed attempts.
    same = (manifest.region == 'Viking_2') & (manifest.science_name.str.casefold() == TILE.casefold())
    result = pd.concat([manifest.loc[~same], pd.DataFrame([rec])], ignore_index=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup = MANIFEST.with_name(f'crism_downloads_backup_{stamp}.csv')
    shutil.copy2(MANIFEST, backup)
    temp = MANIFEST.with_suffix('.csv.tmp')
    result.to_csv(temp, index=False)
    temp.replace(MANIFEST)
    print('Manifest updated:', MANIFEST)
    print('Backup:', backup)
    print('Run python src/extract_crism.py next. Coverage still unverified.')


if __name__ == '__main__':
    main()
