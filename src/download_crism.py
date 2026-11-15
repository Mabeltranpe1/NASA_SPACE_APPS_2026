"""GeoAnalog: bounded pilot download of CRISM spectral parameter products.
Run: python src/download_crism.py
Input: data/features/crism_availability.csv (search_crism.py).
Output: raw PDS science images, labels, catalogue XML and CSV manifests.
No mineral detections or PAI changes are inferred from catalogue metadata.
Sources: NASA PDS ODE MTRDR / MRDR4 product primers; ODE REST API.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import math
import re
import json
import time
import xml.etree.ElementTree as ET

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from shapely import wkt
from shapely.geometry import box
from shapely.affinity import translate
from shapely.validation import make_valid

BASE = Path(__file__).resolve().parent.parent
FEATURES = BASE / 'data' / 'features'
RAW = BASE / 'data' / 'raw' / 'spectral' / 'mars' / 'crism'
API = 'https://oderest.rsl.wustl.edu/live2/'
PAGE = 100
MTR_PER_REGION = 2
MRDR_PER_REGION = 1
MAX_FILE_BYTES = 750 * 1024**2
MAX_TOTAL_BYTES = 2500 * 1024**2  # new downloads per execution
REGIONS = ['Jezero', 'Gale', 'Phoenix', 'Pathfinder', 'Viking_1', 'Viking_2']
MTR = re.compile(r'^(?P<obs>(?:FRT|HRL|HRS)[0-9a-f]{8})_[0-9a-f]{2}_(?P<sub>SU|SR)\d{3}J_MTR[0-9a-z]$', re.I)
MRR = re.compile(r'^T\d{4}_MRRSU_\d{2}[NS]\d{3}_\d{4}_[0-9a-z]$', re.I)


def local(tag):
    return tag.rsplit('}', 1)[-1].lower()


def fields(node):
    return {local(child.tag): (child.text or '').strip() for child in node}


def number(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def basename(url):
    return unquote(urlsplit(url).path.rsplit('/', 1)[-1])


def safe_name(name):
    return bool(re.fullmatch(r'[A-Za-z0-9_.-]+', name or '')) and name not in ('.', '..')


def subtype(stem, product_type):
    m = MTR.fullmatch(stem) if product_type == 'MTRDR' else MRR.fullmatch(stem)
    if not m:
        return None, None
    if product_type == 'MTRDR':
        return m.group('sub').upper(), m.group('obs').upper()
    return 'MRRSU', stem.rsplit('_', 1)[0].upper()


def product_files(product, meta):
    found = {}
    def add(url, name='', kb=None):
        if urlsplit(url).scheme not in ('http', 'https'):
            return
        name = name or basename(url)
        if safe_name(name):
            found.setdefault(name.lower(), dict(name=name, url=url, kbytes=kb))
    for node in product.iter():
        if local(node.tag) == 'product_file':
            f = fields(node)
            add(f.get('url', ''), f.get('filename', ''), number(f.get('kbytes')))
    for key in ('producturl', 'labelurl'):
        add(meta.get(key, ''))
    return list(found.values())


def footprint_pct(meta, roi):
    try:
        g = make_valid(wkt.loads(meta['footprint_geometry']))
        # Allow both longitude conventions; no reprojection or pixel-validity claim.
        return max(0., min(100., max(100 * g.intersection(translate(roi, xoff=d)).area / roi.area
                                      for d in (-360, 0, 360))))
    except Exception:
        return None


def parse_products(content, q):
    root = ET.fromstring(content)
    header = fields(root)
    if header.get('status', '').lower() != 'success':
        raise ValueError(header.get('error') or header.get('status') or 'Unknown ODE status')
    roi = box(float(q.westernlon), float(q.minlat), float(q.easternlon), float(q.maxlat))
    rows = []
    for product in root.iter():
        if local(product.tag) != 'product':
            continue
        meta = fields(product)
        pid = meta.get('pdsid') or meta.get('product_lid') or ''
        files = product_files(product, meta)
        images = [f for f in files if Path(f['name']).suffix.lower() == '.img' and
                  subtype(Path(f['name']).stem, q.product_type)[0]]
        # A product may include related products. Prefer the exact product image.
        exact = [f for f in images if Path(f['name']).stem.lower() == pid.lower()]
        if exact:
            images = exact
        elif len(images) > 1:
            # Never guess among multiple science images with ambiguous identity.
            images = []
        row = dict(region=q.region, product_type=q.product_type, pdsid=pid,
                   ode_id=meta.get('ode_id', ''), dataset_id=meta.get('data_set_id', ''),
                   utc=meta.get('utc_start_time') or meta.get('observation_time', ''),
                   footprint_overlap_bbox_pct=footprint_pct(meta, roi),
                   subtype='', observation_key='', science_name='', science_url='',
                   eligible=False, reason='no_matching_parameter_image', files=[])
        if len(images) == 1:
            image = images[0]
            stem = Path(image['name']).stem
            sub, obs = subtype(stem, q.product_type)
            related = [f for f in files if Path(f['name']).suffix.lower() in ('.lbl', '.xml', '.hdr')
                       and Path(f['name']).stem.lower() in (stem.lower(), image['name'].lower())]
            labels = [f for f in related if Path(f['name']).suffix.lower() in ('.lbl', '.xml')]
            if not labels:
                labelurl = meta.get('labelurl', '')
                labels = [f for f in files if f['url'] == labelurl and
                          Path(f['name']).suffix.lower() in ('.lbl', '.xml') and
                          Path(f['name']).stem.lower() in (stem.lower(), image['name'].lower())]
                related += labels
            chosen = [image, *related]
            too_big = any(f['kbytes'] is not None and f['kbytes'] * 1024 > MAX_FILE_BYTES for f in chosen)
            row.update(subtype=sub, observation_key=obs, science_name=image['name'], science_url=image['url'],
                       files=chosen, eligible=bool(labels) and not too_big,
                       reason='missing_label' if not labels else 'file_over_limit' if too_big else 'eligible')
        rows.append(row)
    return rows


def collect(session, q):
    rows = []
    count = int(q.product_count)
    for offset in range(0, count, PAGE):
        params = dict(query='product', target='mars', ihid='MRO', iid='CRISM', pt=q.product_type,
                      results='opmf', output='XML', loc='f', minlat=q.minlat, maxlat=q.maxlat,
                      westernlon=q.westernlon, easternlon=q.easternlon, limit=PAGE, offset=offset)
        resp = session.get(API, params=params, timeout=(20, 180))
        resp.raise_for_status()
        (RAW / 'catalogue' / f'{q.region}_{q.product_type}_details_{offset}.xml').write_bytes(resp.content)
        page = parse_products(resp.content, q)
        if not page:
            raise ValueError(f'No Product entries at offset {offset}')
        rows.extend(page)
        time.sleep(.5)
    return list({(r['pdsid'], r['ode_id'], r['science_name']): r for r in rows}.values())


def select(rows, kind, count):
    # One targeted observation or map tile; prefer refined SR over SU for same observation.
    unique = {}
    def ranking(r):
        cov = r['footprint_overlap_bbox_pct']
        return (r['subtype'] == 'SR', cov if cov is not None else -1, r['utc'])
    for r in sorted((x for x in rows if x['eligible'] and x['product_type'] == kind), key=ranking, reverse=True):
        unique.setdefault(r['observation_key'], r)
    # Across different observations, favor catalogue intersection, then subtype.
    def coverage_rank(r):
        cov = r['footprint_overlap_bbox_pct']
        return (cov if cov is not None else -1, r['subtype'] == 'SR', r['utc'])
    return sorted(unique.values(), key=coverage_rank, reverse=True)[:count]


def download(session, item, dest, remaining):
    if dest.is_file() and dest.stat().st_size > 0:
        return 0, 'existing_not_reverified'
    limit = min(MAX_FILE_BYTES, remaining)
    if limit <= 0:
        raise ValueError('Download budget exhausted')
    tmp = dest.with_suffix(dest.suffix + '.part')
    size = 0
    try:
        with session.get(item['url'], stream=True, timeout=(20, 180), headers={'Accept-Encoding':'identity'}) as response:
            response.raise_for_status()
            if 'text/html' in response.headers.get('Content-Type', '').lower():
                raise ValueError('HTML returned instead of PDS file')
            length = number(response.headers.get('Content-Length'))
            if length is not None and length > limit:
                raise ValueError(f'File exceeds allowed bytes ({int(length):,})')
            with tmp.open('wb') as out:
                for block in response.iter_content(1024**2):
                    size += len(block)
                    if size > limit:
                        raise ValueError('File exceeds download budget')
                    out.write(block)
            if not size or (length is not None and size != int(length)):
                raise ValueError(f'Incomplete download: {size} bytes; expected {length}')
        tmp.replace(dest)
    finally:
        if tmp.exists():
            tmp.unlink()
    return size, 'downloaded'


def save(rows, name, columns=None):
    pd.DataFrame([{k:v for k,v in r.items() if k != 'files'} for r in rows], columns=columns).to_csv(FEATURES / name, index=False)


def main():
    availability = pd.read_csv(FEATURES / 'crism_availability.csv')
    (RAW / 'catalogue').mkdir(parents=True, exist_ok=True)
    all_rows, queries, manifest = [], [], []
    selected = {r: {} for r in REGIONS}
    total_bytes = 0
    with requests.Session() as session:
        session.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=1,
                      status_forcelist=(429,500,502,503,504), allowed_methods=('GET',))))
        for region in REGIONS:
            rows = []
            print(f'\n========== {region} ==========', flush=True)
            for q in availability[availability.region == region].itertuples(index=False):
                detail = dict(region=region, product_type=q.product_type, expected_count=q.product_count,
                              actual_count=0, status=q.status, error='')
                if q.status == 'ok' and pd.notna(q.product_count) and int(q.product_count) > 0:
                    try:
                        part = collect(session, q)
                        rows.extend(part)
                        detail.update(actual_count=len(part), status='ok' if len(part)==int(q.product_count) else 'count_mismatch')
                        print(f'  {q.product_type}: {len(part)} entries; {sum(p["eligible"] for p in part)} eligible', flush=True)
                    except Exception as exc:
                        detail.update(status='error', error=str(exc))
                        print(f'  {q.product_type}: ERROR {exc}', flush=True)
                queries.append(detail)
            all_rows.extend(rows)
            selected[region]['MTRDR'] = select(rows, 'MTRDR', MTR_PER_REGION)
            selected[region]['MRDR4'] = select(rows, 'MRDR4', MRDR_PER_REGION)
            print('  Pilot selected:', {k:len(v) for k,v in selected[region].items()}, flush=True)
            if not any(selected[region].values()):
                print('  No eligible parameter product (see catalogue CSV/XML).', flush=True)
        save(all_rows, 'crism_scene_catalogue.csv', columns=['region','product_type','pdsid','ode_id','dataset_id','utc','footprint_overlap_bbox_pct','subtype','observation_key','science_name','science_url','eligible','reason'])
        save(queries, 'crism_catalogue_queries.csv')
        # Round-robin first targeted observations, then mosaics, then extra targeted ones.
        plan = []
        for kind, index in [('MTRDR',0), ('MRDR4',0), ('MTRDR',1)]:
            for region in REGIONS:
                group = selected[region][kind]
                if index < len(group):
                    plan.append(group[index])
        for row in plan:
            dest = RAW / row['region'] / row['product_type'] / Path(row['science_name']).stem
            dest.mkdir(parents=True, exist_ok=True)
            record = {k:v for k,v in row.items() if k != 'files'}
            record.update(status='error', error='', image_path='', label_paths='', header_paths='', file_urls='', files_ready=0)
            completed = []
            # Small metadata first; keep image last. Partial successes persist for retries.
            items = sorted(row['files'], key=lambda f: Path(f['name']).suffix.lower()=='.img')
            try:
                for f in items:
                    n, _ = download(session, f, dest / f['name'], MAX_TOTAL_BYTES-total_bytes)
                    total_bytes += n
                    completed.append(dest / f['name'])
                record['status'] = 'files_ready'
            except Exception as exc:
                record['error'] = str(exc)
                if 'budget' in str(exc).lower() or 'allowed bytes' in str(exc).lower():
                    record['status'] = 'size_or_budget_limit'
            record['files_ready'] = len(completed)
            record['image_path'] = next((str(p.relative_to(BASE)) for p in completed if p.suffix.lower()=='.img'), '')
            record['label_paths'] = json.dumps([str(p.relative_to(BASE)) for p in completed if p.suffix.lower() in ('.xml','.lbl')])
            record['header_paths'] = json.dumps([str(p.relative_to(BASE)) for p in completed if p.suffix.lower()=='.hdr'])
            record['file_urls'] = json.dumps([f['url'] for f in row['files']])
            manifest.append(record)
            save(manifest, 'crism_downloads.csv')
            print(f"{row['region']} | {row['subtype']} | {row['science_name']} | {record['status']} {record['error']}", flush=True)
        if not manifest:
            save([], 'crism_downloads.csv', columns=['region','product_type','pdsid','subtype','status','error','image_path','label_paths','header_paths'])
    print(f'\nDownloaded this run: {total_bytes/1024**2:.1f} MiB')
    print(f'Files ready: {sum(r["status"]=="files_ready" for r in manifest)}/{len(manifest)} selected products')
    print('Output:', FEATURES / 'crism_downloads.csv')
    print('Catalogue eligibility is not valid-pixel coverage or mineral identification. No PAI changes.')


if __name__ == '__main__':
    main()
