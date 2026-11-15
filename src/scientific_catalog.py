"""Read-only adapters and small, lazy-loaded exports of Santiago's regional science.

No download, reprocessing, replacement of global cells, or implicit score fusion.
Original values and units are retained. Scientific artifacts remain byte-identical.
"""

from pathlib import Path
import hashlib
import json
import math
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import rasterio
from pyproj import CRS, Transformer
from shapely.geometry import Point, box

from science_metadata import (
    SCHEMA_VERSION, SCIENCE_COMMIT, GLOBAL_COMMIT, WEB_COMMIT,
    SITES, SOURCES, SECTION_SPECS, EARTH_SECTIONS, MARS_SECTIONS, MOON_SECTIONS,
    PAI_FEATURES, PAI_WEIGHTS, bilingual, field_metadata,
)

ROOT = Path(__file__).resolve().parent.parent
URL_ROOT = "/data/science"
IGNORED_COLUMNS = {"system:index", ".geo", "source_crs"}


def json_value(value):
    """Missing observations remain null; genuine zeros, False and strings survive."""
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(value) else None
    if value is None or value is pd.NA:
        return None
    return value


def write_json(path, value):
    path = Path(path)
    data = json.dumps(json_value(value), ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)
    return len(data)


def read_table(path):
    path = Path(path)
    return pd.read_csv(path, keep_default_na=True) if path.exists() else pd.DataFrame()


def region_rows(table, region, planet=None):
    if table.empty or "region" not in table:
        return []
    selection = table[table["region"] == region]
    if planet is not None and "planet" in selection:
        selection = selection[selection["planet"] == planet]
    return json_value(selection.drop(columns=list(IGNORED_COLUMNS), errors="ignore").to_dict("records"))


def flag(code, es, en, level="warning"):
    return {"code": code, "level": level, "message": bilingual(es, en)}


def quality_flags(region, planet, sections):
    by_id = {s["id"]: s["records"] for s in sections}
    flags = []
    if region == "La_Guajira":
        water = next(iter(by_id.get("environment", [])), {}).get("water_pct")
        flags.append(flag("coastal_water", f"Ventana costera: {water:.5f} % de agua WorldCover; el PAI y EMIT no tienen máscara marina." if water is not None else "Ventana costera; máscara marina no aplicada.", f"Coastal window: {water:.5f}% WorldCover water; PAI and EMIT have no marine mask." if water is not None else "Coastal window; no marine mask applied."))
    if planet == "earth":
        flags.extend([
            flag("emit_provisional", "EMIT contiene coincidencias provisionales de biblioteca, sin máscara L2A de nubes ni máscara marina. No son concentraciones ni detecciones confirmadas de recursos.", "EMIT contains provisional library matches, without L2A cloud or marine masks. These are not concentrations or confirmed resource detections."),
            flag("separate_support", "La caracterización regional es la fuente detallada de Santiago; las celdas y puntajes globales de Marco mantienen su propio soporte espacial.", "Santiago supplies the detailed regional characterization; Marco's global cells and scores retain their own spatial support.", "info"),
        ])
        if region == "Volcan_Purace":
            flags.append(flag("emit_partial", "Puracé: solo dos adquisiciones EMIT válidas por grupo; resultado parcialmente provisional.", "Puracé: only two valid EMIT acquisitions per group; partially provisional result."))
    if planet == "mars":
        flags.append(flag("themis_pilot", "THEMIS es piloto, con banda no verificada y adquisiciones día/noche no emparejadas. No restar sus medias como amplitud diaria.", "THEMIS is a pilot with an unverified band and unpaired day/night acquisitions. Do not subtract means as a daily thermal range."))
        if region == "Phoenix":
            flags.extend([
                flag("crism_geometry", "CRISM Phoenix no tiene observación calificada: tres productos rechazados por referencia no esférica/planetográfica pendiente de validar.", "Phoenix CRISM has no qualified observation: three products rejected pending validation of a non-spherical/planetographic reference."),
                flag("tes_low_coverage", "TES diurno Phoenix: 79,60697 % de cobertura válida, inferior al umbral de 80 %.", "Phoenix daytime TES: 79.60697% valid coverage, below the 80% threshold."),
            ])
    if planet == "moon":
        flags.append(flag("ice_model", "La estabilidad térmica modelada del hielo no demuestra presencia, volumen ni accesibilidad del hielo. La media anual a 2 cm difiere de la máxima superficial.", "Modeled thermal ice stability does not establish ice presence, volume or accessibility. The annual mean at 2 cm differs from the surface maximum."))
    return flags


def dem_geometry(path):
    """Use each study's actual raster footprint, never the similarly named global target."""
    path = Path(path)
    if not path.exists():
        return None
    with rasterio.open(path) as dem:
        crs = CRS.from_user_input(dem.crs)
        inverse = Transformer.from_crs(crs, crs.geodetic_crs, always_xy=True)
        x = (dem.bounds.left + dem.bounds.right) / 2
        y = (dem.bounds.bottom + dem.bounds.top) / 2
        lon, lat = inverse.transform(x, y)
        return {
            "latitude": lat, "longitude_east_signed_deg": (lon + 180) % 360 - 180,
            "bounds_projected_m": list(dem.bounds), "crs_wkt": crs.to_wkt(),
            "width": dem.width, "height": dem.height, "resolution_m": list(dem.res),
            "nominal_window_km": 10, "source_dem": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name,
        }


def footprint_association(target, document):
    """Match by same-body geometric overlap, not by name.

    This is a planar approximation in the study CRS, consistent with the global
    ring/disk convention. It documents overlap only; product supports are not fused.
    """
    geometry = document.get("geometry")
    if not geometry:
        return None
    body = {"Moon": "moon", "Mars": "mars"}.get(target.get("body"))
    if body != document["planet"]:
        return None
    lat, lon = target.get("site_lat"), target.get("site_lon")
    if lat is None or lon is None or not np.isfinite([lat, lon]).all():
        return None
    crs = CRS.from_wkt(geometry["crs_wkt"])
    x, y = Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True).transform(lon, lat)
    area = str(target.get("area", "")).split()
    if len(area) < 2 or area[0] not in {"disk", "rim"}:
        return None
    size_m = float(area[1]) * 1000
    center = Point(x, y)
    if area[0] == "rim":
        radius = size_m / 2
        footprint = center.buffer(1.3 * radius, quad_segs=128).difference(center.buffer(.9 * radius, quad_segs=128))
    else:
        footprint = center.buffer(size_m, quad_segs=128)
    study = box(*geometry["bounds_projected_m"])
    overlap = footprint.intersection(study).area
    if overlap <= 1:
        return None
    return {
        "study_id": document["id"], "url": f"{URL_ROOT}/{body}/{document['region']}.json",
        "name": document["name"], "overlap_study_pct": 100 * overlap / study.area,
        "overlap_target_pct": 100 * overlap / footprint.area,
        "center_separation_projected_km": math.hypot(x - (study.bounds[0] + study.bounds[2]) / 2, y - (study.bounds[1] + study.bounds[3]) / 2) / 1000,
        "relation": "overlapping_regional_window_distinct_support",
        "method": "same-body planar ring/disk intersection in study DEM CRS; not exact co-registration",
        "note": bilingual("La ventana científica se superpone parcialmente o totalmente con el objetivo global; los valores conservan su propia geometría y no sustituyen el objetivo.", "The scientific window overlaps the global target partially or fully; values retain their own geometry and do not replace the target."),
    }


def model_pai(results_dir):
    params = read_table(Path(results_dir) / "normalization_parameters.csv")
    if not params.empty:
        params = params.rename(columns={params.columns[0]: "feature"})
    return {
        "id": "pai-topography-v1", "label": bilingual("PAI topográfico regional", "Regional topographic PAI"),
        "equation": "z=(x−μEarth)/σEarth; d=√Σw(zA−zB)²; PAI=100/(1+d)",
        "normalization": "population z-score fitted only to six Colombian regions; constant features removed and weights renormalized",
        "features": [{"id": f, "weight": w} for f, w in zip(PAI_FEATURES, PAI_WEIGHTS)],
        "normalization_parameters": json_value(params.to_dict("records")),
        "scale": [0, 100], "calibration_status": "experimental_not_probability",
        "note": bilingual("Solo seis descriptores topográficos a 200 m. No incorpora clima o mineralogía, no es porcentaje de equivalencia física y no se promedia con el índice global.", "Only six topographic descriptors at 200 m. It includes neither climate nor mineralogy, is not a physical-equivalence percentage and is not averaged with the global index."),
    }


def build_science(features_dir, results_dir, processed_dir, output_dir, targets=None):
    """Export all available regional products and referenced artifacts, without changing inputs."""
    features_dir, results_dir, processed_dir, output_dir = map(Path, (features_dir, results_dir, processed_dir, output_dir))
    tables = {filename: read_table(features_dir / filename) for filename, *_ in SECTION_SPECS.values()}
    topo = tables["planetary_features.csv"]
    ranking = read_table(results_dir / "analog_ranking.csv")
    if topo.empty or ranking.empty:
        raise ValueError("The original planetary features and PAI ranking are required for the science export")
    if topo.duplicated(["planet", "region"]).any():
        raise ValueError("Duplicate regional scientific identifiers")
    if ranking.duplicated(["target", "candidate"]).any():
        raise ValueError("Duplicate PAI comparison pair")
    expected = {f"earth_{r}" for r in SITES}
    if set(ranking.candidate) != expected or len(ranking) != 72:
        raise ValueError("Expected the original six-region, twelve-target, 72-pair PAI dataset")
    all_pai = ranking.sort_values(["target", "PAI"], ascending=[True, False]).copy()
    all_pai["rank_among_six"] = all_pai.groupby("target").cumcount() + 1
    pai_model = model_pai(results_dir)
    documents, variable_catalog = {}, {}
    source_catalog = {key: dict(id=key, name=v[0], institution=v[1], url=v[2], evidence_type=v[3]) for key, v in SOURCES.items()}
    for _, row in topo.iterrows():
        planet, region = row["planet"], row["region"]
        sid = f"{planet}_{region}"
        if planet == "earth" and region not in SITES:
            continue
        selected = EARTH_SECTIONS if planet == "earth" else MARS_SECTIONS if planet == "mars" else MOON_SECTIONS
        sections = []
        for section in selected:
            filename, title, sources, support, period, method, compatibility = SECTION_SPECS[section]
            sources = [{"earth": "nasadem", "moon": "lola", "mars": "mola_hrsc"}[planet]] if section == "topography" else sources
            records = region_rows(tables[filename], region, planet)
            fields = [field_metadata(section, col, sources) for col in tables[filename].columns if col not in IGNORED_COLUMNS]
            for f in fields:
                variable_catalog[f"{planet}.{f['app_field']}"] = {**f, "original_file": f"data/features/{filename}"}
            sections.append({
                "id": section, "title": title, "source_ids": sources,
                "spatial_support": support, "period": period, "method": method,
                "compatibility": compatibility, "fields": fields, "records": records,
                "status": "available" if records else "unavailable",
                "source_file": f"data/features/{filename}",
            })
        document = {
            "version": SCHEMA_VERSION, "id": sid, "planet": planet, "region": region,
            "name": bilingual(SITES[region][1], SITES[region][2]) if planet == "earth" else bilingual(region.replace("_", " "), region.replace("_", " ")),
            "author": {"name": "Santiago", "github": "santiago-851"},
            "source_commit": SCIENCE_COMMIT,
            "geometry": dem_geometry(processed_dir / planet / f"{region}_DEM_200m.tif"),
            "sections": sections, "quality_flags": quality_flags(region, planet, sections),
            "sources": [source_catalog[k] for k in sorted({k for s in sections for k in s["source_ids"]})],
            "assets": [],
        }
        if planet == "earth":
            document["site_id"] = SITES[region][0]
            observations = all_pai[all_pai.candidate == sid].sort_values("PAI", ascending=False).to_dict("records")
            for result in observations:
                body, name = result["target"].split("_", 1)
                result["study_url"] = f"{URL_ROOT}/{body}/{name}.json"
            document["pai"] = {"model": pai_model, "results": json_value(observations)}
            climate = next((s["records"][0] for s in sections if s["id"] == "climate" and s["records"]), None)
            if climate:
                document["representative_point"] = {"latitude": climate["latitude"], "longitude": climate["longitude"], "source": "original regional study coordinates"}
        else:
            observations = all_pai[all_pai.target == sid].to_dict("records")
            for result in observations:
                result["study_url"] = f"{URL_ROOT}/earth/{result['candidate'].split('_', 1)[1]}.json"
            document["pai"] = {"model": pai_model, "results": json_value(observations)}
        documents[sid] = document

    # Copy small derived artifacts only. No native EMIT/CRISM/THEMIS or global raw DEMs.
    artifact_paths = list(features_dir.glob("*.csv")) + list(features_dir.glob("*.geojson"))
    artifact_paths += list(results_dir.glob("*.csv")) + list(results_dir.glob("*.png"))
    artifact_paths += list((features_dir.parent / "figures").glob("*.png"))
    artifact_paths += list(processed_dir.glob("*/*_DEM_200m.tif"))
    artifact_paths += list((features_dir.parent / "raw/climate").glob("*.csv"))
    assets = []
    for src in sorted(set(artifact_paths)):
        if not src.is_relative_to(ROOT):
            relative = Path("data") / src.parent.name / src.name
        else:
            relative = src.relative_to(ROOT)
        data = src.read_bytes()
        dest = output_dir / "files" / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.read_bytes() != data:
            dest.write_bytes(data)
        assets.append({"source_file": relative.as_posix(), "url": f"{URL_ROOT}/files/{relative.as_posix()}", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    asset_by_source = {a["source_file"]: a for a in assets}
    for document in documents.values():
        region, planet = document["region"], document["planet"]
        for s in document["sections"]:
            if s["source_file"] in asset_by_source:
                document["assets"].append(asset_by_source[s["source_file"]])
        for path in [f"data/processed/{planet}/{region}_DEM_200m.tif", f"data/figures/{planet}_{region}_analysis.png", "data/results/analog_ranking.csv", "data/results/similarity_matrix.csv", "data/results/similarity_matrix.png"]:
            if path in asset_by_source:
                document["assets"].append(asset_by_source[path])
        if planet == "earth":
            path = features_dir / "geological_units.geojson"
            if path.exists():
                collection = json.loads(path.read_text(encoding="utf-8"))
                collection["features"] = [f for f in collection["features"] if f["properties"].get("region") == region]
                write_json(output_dir / "earth" / f"{region}.geojson", collection)
                document["assets"].append({"url": f"{URL_ROOT}/earth/{region}.geojson", "source_file": "data/features/geological_units.geojson", "kind": "regional_geology"})
        write_json(output_dir / planet / f"{region}.json", document)

    target_links = {}
    if targets is not None:
        for target in targets.to_dict("records"):
            links = [footprint_association(target, doc) for doc in documents.values() if doc["planet"] != "earth"]
            target_links[target["name"]] = [link for link in links if link]
    index = {
        "version": SCHEMA_VERSION, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provenance": {"science_commit": SCIENCE_COMMIT, "global_commit": GLOBAL_COMMIT, "web_base_commit": WEB_COMMIT},
        "team": [{"name": "Marco", "github": "Mabeltranpe1", "role": "global research and comparator"}, {"name": "Sebastián", "github": "Ssalazarp420", "role": "interface and visualization"}, {"name": "Santiago", "github": "santiago-851", "role": "detailed regional science and PAI"}],
        "studies": [{"id": d["id"], "region": d["region"], "planet": d["planet"], "site_id": d.get("site_id"), "name": d["name"], "url": f"{URL_ROOT}/{d['planet']}/{d['region']}.json"} for d in documents.values()],
        "target_associations": target_links, "pai_model": pai_model,
        "variable_catalog_url": f"{URL_ROOT}/variables.json", "sources": source_catalog,
        "artifacts": assets,
    }
    write_json(output_dir / "variables.json", {"version": SCHEMA_VERSION, "fields": variable_catalog})
    write_json(output_dir / "index.json", index)
    return index


def validate_comparison_contract(data):
    """Fail before publishing duplicate identifiers, nonfinite numbers or broken refs."""
    json.dumps(data, allow_nan=False)
    if data.get("synthetic"):
        raise ValueError("Synthetic comparison input cannot be exported as integrated science")
    targets = [t["id"] for t in data["targets"]]
    sites = [s["id"] for s in data["sites"]]
    if len(targets) != len(set(targets)) or len(sites) != len(set(sites)):
        raise ValueError("Duplicate comparison identifiers")
    for site in data["sites"]:
        ids = [r["target"] for r in site["results"]]
        if len(ids) != len(set(ids)) or not set(ids) <= set(targets):
            raise ValueError(f"Broken or duplicate target reference in {site['id']}")
        for result in site["results"]:
            if result["score"] is not None and not 0 <= result["score"] <= 1:
                raise ValueError("Global score outside [0,1]")

