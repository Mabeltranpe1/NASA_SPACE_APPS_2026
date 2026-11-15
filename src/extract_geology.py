"""GeoAnalog: geological units from SGC Atlas 2023, layer 733.
Run from SpaceApps: python src/extract_geology.py
"""
from pathlib import Path
from collections import defaultdict
import json
import time

import pandas as pd
import requests
import rasterio
from pyproj import CRS, Transformer
from shapely.geometry import box, shape, mapping
from shapely.ops import transform, unary_union
from shapely import make_valid

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / 'data/raw/geology'
OUT = BASE / 'data/features'
DEM = BASE / 'data/processed/earth'
LAYER = ('https://srvags.sgc.gov.co/arcgis/rest/services/'
         'Mapa_Geologico_Colombia/Mapa_Geologico_Colombia_V2023/MapServer/733')
SOURCE = 'SGC - Atlas Geologico de Colombia 2023, 1:500000'
LOCATIONS = {
    'Tatacoa': (3.2300, -75.1700),
    'La_Guajira': (12.43653, -71.60899),
    'Nevado_del_Ruiz': (4.8950, -75.3220),
    'Volcan_Purace': (2.3095, -76.3948),
    'La_Candelaria': (5.5368, -73.6163),
    'Nevado_Santa_Isabel': (4.8180, -75.3650),
}
FIELDS = ['SimboloUC', 'Descripcion', 'Edad', 'CodigoUC', 'Comentarios']
UNIT_COLS = ['region','planet','unit_symbol','description','geological_age',
             'unit_code','comments','area_km2','pct_study_area','pct_mapped_area',
             'window_source','source','source_url']


def study_window(region, lat, lon):
    path = DEM / f'{region}_DEM_200m.tif'
    if path.exists():
        with rasterio.open(path) as src:
            if src.crs is None:
                raise ValueError(f'DEM sin CRS: {path}')
            crs = CRS.from_user_input(src.crs)
            if not crs.is_projected or any(abs(a.unit_conversion_factor - 1) > 1e-9 for a in crs.axis_info):
                raise ValueError('Se esperaba un DEM proyectado en metros')
            if src.width != 50 or src.height != 50 or any(abs(abs(r)-200)>1e-6 for r in src.res):
                raise ValueError('DEM distinto de la cuadricula esperada de 50 x 50 a 200 m')
            if src.transform.b != 0 or src.transform.d != 0:
                raise ValueError('DEM rotado: revisar limites')
            return box(*src.bounds), crs, 'processed_dem_bounds'
    zone = int((lon + 180) // 6) + 1
    crs = CRS.from_epsg(32600 + zone)
    x, y = Transformer.from_crs(4326, crs, always_xy=True).transform(lon, lat)
    print('  AVISO: DEM no encontrado; usando ventana nominal de 10 x 10 km')
    return box(x-5000,y-5000,x+5000,y+5000), crs, 'nominal_utm_square'


def query_units(window, crs):
    to_wgs = Transformer.from_crs(crs, 4326, always_xy=True)
    bounds = to_wgs.transform_bounds(*window.bounds, densify_pts=21)
    response = requests.get(LAYER + '/query', params={
        'where':'1=1', 'geometry':','.join(map(str,bounds)),
        'geometryType':'esriGeometryEnvelope', 'inSR':4326,
        'spatialRel':'esriSpatialRelIntersects',
        'outFields':','.join(FIELDS), 'returnGeometry':'true',
        'outSR':4326, 'f':'geojson',
    }, timeout=180)
    response.raise_for_status()
    data = response.json()
    if 'error' in data:
        raise RuntimeError(str(data['error']))
    if data.get('type') != 'FeatureCollection' or 'features' not in data:
        raise ValueError('Respuesta no es una FeatureCollection GeoJSON')
    if data.get('exceededTransferLimit') or data.get('properties',{}).get('exceededTransferLimit') or len(data['features']) >= 10000:
        raise ValueError('Limite de transferencia: resultado posiblemente incompleto')
    return data


def summarize(region, data, window, crs, window_source):
    to_local = Transformer.from_crs(4326, crs, always_xy=True).transform
    to_wgs = Transformer.from_crs(crs, 4326, always_xy=True).transform
    units = defaultdict(list)
    for feature in data['features']:
        if not feature.get('geometry'):
            raise ValueError('Unidad recibida sin geometria')
        p = feature['properties']
        if not p.get('SimboloUC'):
            raise ValueError('Unidad recibida sin SimboloUC')
        geom = make_valid(transform(to_local, shape(feature['geometry'])))
        clipped = geom.intersection(window)
        if clipped.area > 0:
            key = tuple(p.get(f) for f in FIELDS)
            units[key].append(clipped)
    merged = {key: unary_union(geoms) for key, geoms in units.items()}
    mapped = unary_union(list(merged.values())).area if merged else 0.0
    total = window.area
    summed = sum(g.area for g in merged.values())
    coverage = dict(region=region,planet='earth',window_source=window_source,
                    study_area_km2=total/1e6,mapped_area_km2=mapped/1e6,
                    mapped_pct=100*mapped/total,unmapped_pct=100*(total-mapped)/total,
                    overlap_excess_km2=max(0,summed-mapped)/1e6,
                    unit_count=len(merged),status='ok' if merged else 'no_mapped_units',
                    source=SOURCE,source_url=LAYER)
    rows, features = [], []
    for key,g in sorted(merged.items(),key=lambda item:item[1].area,reverse=True):
        symbol,desc,age,code,comments = key
        row = dict(region=region,planet='earth',unit_symbol=symbol,description=desc,
                   geological_age=age,unit_code=code,comments=comments,
                   area_km2=g.area/1e6,pct_study_area=100*g.area/total,
                   pct_mapped_area=100*g.area/mapped,window_source=window_source,
                   source=SOURCE,source_url=LAYER)
        rows.append(row)
        features.append({'type':'Feature','geometry':mapping(transform(to_wgs,g)), 'properties':row})
    return rows,coverage,features


def main():
    RAW.mkdir(parents=True,exist_ok=True)
    OUT.mkdir(parents=True,exist_ok=True)
    all_rows,all_coverage,all_features=[],[],[]
    for region,(lat,lon) in LOCATIONS.items():
        print(f'\nProcesando SGC: {region}')
        window_source = 'unknown'
        try:
            window,crs,window_source = study_window(region,lat,lon)
            data = query_units(window,crs)
            (RAW/f'{region}_SGC.geojson').write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
            rows,cov,features = summarize(region,data,window,crs,window_source)
            all_rows.extend(rows)
            all_coverage.append(cov)
            all_features.extend(features)
            print(f"Unidades: {cov['unit_count']} | Cobertura cartografiada: {cov['mapped_pct']:.2f}%")
            if rows:
                print(f"Principal: {rows[0]['unit_symbol']} ({rows[0]['pct_study_area']:.2f}% de ventana)")
            if cov['overlap_excess_km2'] > 0.01:
                print('AVISO: unidades superpuestas; porcentajes no son aditivos')
        except Exception as exc:
            print(f'ERROR: {exc}')
            all_coverage.append(dict(region=region,planet='earth',status='error',window_source=window_source,error=str(exc),source=SOURCE,source_url=LAYER))
        time.sleep(1)
    pd.DataFrame(all_rows,columns=UNIT_COLS).to_csv(OUT/'geological_features.csv',index=False,encoding='utf-8',float_format='%.6f')
    pd.DataFrame(all_coverage).to_csv(OUT/'geological_coverage.csv',index=False,encoding='utf-8',float_format='%.6f')
    (OUT/'geological_units.geojson').write_text(json.dumps({'type':'FeatureCollection','features':all_features},ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print('\nResultados:',OUT)
    print('Regiones con unidades:',sum(c['status']=='ok' for c in all_coverage),'/',len(LOCATIONS))
    print('Errores:',sum(c['status']=='error' for c in all_coverage))
    print('Unidades regionales:',len(all_rows))

if __name__ == '__main__':
    main()
