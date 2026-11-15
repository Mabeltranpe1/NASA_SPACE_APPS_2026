"""GeoAnalog: select and download a bounded pilot sample of THEMIS IRPBT.
Run from project root: python src/download_themis.py
Requires successful data/features/themis_availability.csv from search_themis.py.
Does not extract brightness temperatures; labels must be validated first.
ODE REST 2.1.6: https://oderest.rsl.wustl.edu/ODE_REST_V2.1.6.pdf
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import math
import re
import time
import xml.etree.ElementTree as ET

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from shapely import wkt
from shapely.geometry import box
from shapely.validation import make_valid

BASE = Path(__file__).resolve().parent.parent
FEATURES = BASE / 'data' / 'features'
RAW = BASE / 'data' / 'raw' / 'thermal' / 'mars' / 'themis'
API = 'https://oderest.rsl.wustl.edu/live2/'
PAGE = 100
PER_CLASS = 3
MAX_UNKNOWN = 1   # diagnostic only when no day/night candidates were usable
MAX_FILE_BYTES = 100 * 1024**2
MAX_TOTAL_BYTES = 1500 * 1024**2
MIN_FOOTPRINT_PCT = 80.0  # ranking proxy, not valid-pixel coverage


def local(tag):
    return tag.rsplit('}', 1)[-1].lower()


def fields(node):
    return {local(child.tag): (child.text or '').strip() for child in node}


def numeric(value):
    try:
        val = float(value)
        return val if math.isfinite(val) else None
    except (TypeError, ValueError):
        return None


def illumination(angle):
    # Incidence at image metadata reference location, not at every ROI pixel.
    if angle is None or not 0 <= angle <= 180:
        return 'unknown'
    if angle < 85:
        return 'day_candidate'
    if angle > 95:
        return 'night_candidate'
    return 'twilight_candidate'


def url_basename(url):
    return unquote(urlsplit(url).path.rsplit('/', 1)[-1])


def safe_name(name):
    return bool(re.fullmatch(r'[A-Za-z0-9_.-]+', name or '')) and name not in ('.', '..')


def urls_for(product, meta):
    found = {}
    def add(url, name='', kb=None):
        if urlsplit(url).scheme not in ('http', 'https'):
            return
        name = name or url_basename(url)
        if safe_name(name):
            found.setdefault(name.lower(), dict(name=name, url=url, kbytes=kb))
    for e in product.iter():
        if local(e.tag) == 'product_file':
            f = fields(e)
            add(f.get('url', ''), f.get('filename', ''), numeric(f.get('kbytes')))
    for key in ('producturl', 'labelurl'):
        add(meta.get(key, ''))
    files = list(found.values())
    images = [f for f in files if re.search(r'pbt[^/]*\.(img|dat|bin)$', f['name'], re.I)]
    if not images:
        images = [f for f in files if f['name'].lower().endswith('.img')]
    if len(images) != 1:
        return []
    image = images[0]
    stem = Path(image['name']).stem.lower()
    labels = [f for f in files if f['name'].lower().endswith(('.lbl', '.xml'))
              and (Path(f['name']).stem.lower() == stem or
                   Path(f['name']).stem.lower() == image['name'].lower())]
    # Some ODE results identify a detached label separately with a different stem.
    if not labels:
        labelurl = meta.get('labelurl', '')
        labels = [f for f in files if f['url'] == labelurl and f['name'].lower().endswith(('.lbl', '.xml'))]
    return [image, *labels]


def footprint_pct(meta, roi):
    try:
        geom = make_valid(wkt.loads(meta['footprint_geometry']))
        return min(100.0, max(0.0, 100.0 * geom.intersection(roi).area / roi.area))
    except Exception:
        return None


def parse_products(content, query):
    root = ET.fromstring(content)
    header = fields(root)
    if header.get('status', '').lower() != 'success':
        raise ValueError(header.get('error') or header.get('status') or 'Unknown ODE status')
    roi = box(float(query.westernlon), float(query.minlat),
              float(query.easternlon), float(query.maxlat))
    rows = []
    for product in root.iter():
        if local(product.tag) != 'product':
            continue
        meta = fields(product)
        pid = meta.get('pdsid') or meta.get('product_lid') or ''
        if not pid:
            continue
        files = urls_for(product, meta)
        # THEMIS image ID shared across archive representations, if present.
        match = re.search(r'I\d{8}', pid, re.I)
        if not match and files:
            match = re.search(r'I\d{8}', files[0]['name'], re.I)
        obs_id = match.group().upper() if match else pid.lower()
        incidence = numeric(meta.get('incidence_angle'))
        rows.append(dict(region=query.region, product_type=query.product_type,
                         pdsid=pid, observation_key=obs_id,
                         ode_id=meta.get('ode_id', ''),
                         dataset_id=meta.get('data_set_id', ''),
                         utc=meta.get('utc_start_time') or meta.get('observation_time', ''),
                         solar_longitude_deg=numeric(meta.get('solar_longitude')),
                         incidence_deg=incidence, emission_deg=numeric(meta.get('emission_angle')),
                         illumination_candidate=illumination(incidence),
                         footprint_overlap_bbox_pct=footprint_pct(meta, roi),
                         science_url=files[0]['url'] if files else '',
                         science_name=files[0]['name'] if files else '',
                         files=files))
    return rows


def collect(session, query):
    out = []
    count = int(query.product_count)
    for offset in range(0, count, PAGE):
        params = dict(query='product', target='mars', ihid='ODY', iid='THEMIS',
                      pt=query.product_type, results='opmf', output='XML', loc='f',
                      minlat=query.minlat, maxlat=query.maxlat,
                      westernlon=query.westernlon, easternlon=query.easternlon,
                      limit=PAGE, offset=offset)
        resp = session.get(API, params=params, timeout=(20, 180))
        resp.raise_for_status()
        path = RAW / 'catalogue' / f'{query.region}_{query.product_type}_details_{offset}.xml'
        path.write_bytes(resp.content)
        rows = parse_products(resp.content, query)
        if not rows:
            raise ValueError(f'No Product elements at offset {offset} (expected count {count})')
        out.extend(rows)
        time.sleep(.7)
    unique = {(r['product_type'], r['pdsid'], r['ode_id']): r for r in out}
    if len(unique) < count:
        print(f'  WARNING: {len(unique)} unique catalogue rows versus earlier count {count}; review XML')
    return list(unique.values())


def file_eligible(row):
    return bool(row['files']) and all(
        f['kbytes'] is None or f['kbytes'] * 1024 <= MAX_FILE_BYTES for f in row['files'])


def rank(row):
    cov = row['footprint_overlap_bbox_pct']
    return (cov is not None and cov >= MIN_FOOTPRINT_PCT,
            cov if cov is not None else -1,
            row['product_type'] == 'IRPBT4',
            row['utc'])


def selection(rows):
    # Choose one product per observation, favoring downloadable high-overlap IRPBT4.
    unique = {}
    for row in sorted([r for r in rows if file_eligible(r)], key=rank, reverse=True):
        existing = unique.get(row['observation_key'])
        if existing is None or (existing['illumination_candidate'] == 'unknown'
                                and row['illumination_candidate'] != 'unknown'):
            unique[row['observation_key']] = row
    ordered = sorted(unique.values(), key=rank, reverse=True)
    selected = []
    for category in ('day_candidate', 'night_candidate'):
        selected.extend([r for r in ordered if r['illumination_candidate'] == category][:PER_CLASS])
    if not selected:
        selected.extend([r for r in ordered if r['illumination_candidate'] == 'unknown'][:MAX_UNKNOWN])
    return selected


def download(session, spec, destination, budget):
    expected = spec['kbytes']
    # ODE KBytes values can be rounded: do not use them as exact byte checks.
    if destination.is_file() and destination.stat().st_size > 0:
        return 0, 'existing_not_reverified'
    limit = min(MAX_FILE_BYTES, budget)
    if limit <= 0:
        raise ValueError('Run download budget exhausted')
    tmp = destination.with_suffix(destination.suffix + '.part')
    size = 0
    try:
        with session.get(spec['url'], stream=True, timeout=(20, 180),
                         headers={'Accept-Encoding': 'identity'}) as response:
            response.raise_for_status()
            if 'text/html' in response.headers.get('Content-Type', '').lower():
                raise ValueError('HTML response instead of PDS file')
            length = numeric(response.headers.get('Content-Length'))
            if length is not None and length > limit:
                raise ValueError(f'File exceeds allowed bytes ({int(length)})')
            with tmp.open('wb') as handle:
                for chunk in response.iter_content(1024 * 1024):
                    size += len(chunk)
                    if size > limit:
                        raise ValueError('File exceeds download limit')
                    handle.write(chunk)
            if size == 0 or (length is not None and size != int(length)):
                raise ValueError(f'Incomplete download: {size} bytes; expected {length}')
        tmp.replace(destination)
    finally:
        if tmp.exists():
            tmp.unlink()
    return size, 'downloaded'


def save(rows, path):
    pd.DataFrame([{k:v for k,v in r.items() if k != 'files'} for r in rows]).to_csv(path, index=False)


def session_factory():
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504), allowed_methods=('GET',))))
    return session


def main():
    availability = pd.read_csv(FEATURES / 'themis_availability.csv')
    (RAW / 'catalogue').mkdir(parents=True, exist_ok=True)
    all_rows, manifests, queries = [], [], []
    byte_count = 0
    with session_factory() as session:
        for region, group in availability.groupby('region', sort=False):
            print(f'\n========== {region} ==========', flush=True)
            rows = []
            for query in group.itertuples(index=False):
                if query.status != 'ok' or not query.product_count:
                    continue
                try:
                    part = collect(session, query)
                    rows.extend(part)
                    queries.append(dict(region=region, product_type=query.product_type,
                                        catalogue_rows=len(part), status='ok', error=''))
                    print(f'  {query.product_type}: {len(part)} detailed entries', flush=True)
                except Exception as exc:
                    queries.append(dict(region=region, product_type=query.product_type,
                                        catalogue_rows=0, status='error', error=str(exc)))
                    print(f'  {query.product_type}: ERROR {exc}', flush=True)
            all_rows.extend(rows)
            selected = selection(rows)
            print(f'  Selected {len(selected)} pilot scenes', flush=True)
            for row in selected:
                key = re.sub(r'[^A-Za-z0-9_.-]', '_', row['observation_key'])
                folder = RAW / region / row['product_type'] / key
                folder.mkdir(parents=True, exist_ok=True)
                manifest = {k:v for k,v in row.items() if k != 'files'}
                paths = []
                statuses = []
                try:
                    for spec in row['files']:
                        path = folder / spec['name']
                        size, state = download(session, spec, path, MAX_TOTAL_BYTES-byte_count)
                        byte_count += size
                        paths.append(str(path.relative_to(BASE)))
                        statuses.append(state)
                    manifest.update(status='files_ready', error='')
                except Exception as exc:
                    manifest.update(status='download_error', error=str(exc))
                manifest.update(local_files=';'.join(paths), file_status=';'.join(statuses))
                manifests.append(manifest)
                print(f'  {row["observation_key"]} | {row["illumination_candidate"]} | {manifest["status"]}', flush=True)
                save(manifests, FEATURES / 'themis_downloads.csv')
            save(all_rows, FEATURES / 'themis_scene_catalogue.csv')
            save(queries, FEATURES / 'themis_catalogue_queries.csv')
    # Explicit schemas even when no downloads were possible.
    if not manifests:
        pd.DataFrame(columns=['region','product_type','pdsid','status','error','local_files']).to_csv(FEATURES / 'themis_downloads.csv', index=False)
    print(f'\nDownloaded this run: {byte_count / 1024**2:.1f} MiB')
    print(f'Files ready: {sum(r["status"] == "files_ready" for r in manifests)}/{len(manifests)} scenes')
    print('Output:', FEATURES / 'themis_downloads.csv')
    print('Illumination and footprint overlap are catalogue proxies, not verified pixel-level quality.')
    print('No temperature retrieval or PAI changes have been made.')


if __name__ == '__main__':
    main()
