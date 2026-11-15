"""
export_analogos.py - Put ALL the results in one JSON file for the web app.

It joins, for every Moon/Mars site:
    - its measured features (data/targets.csv)
    - its rock composition (data/composition_targets.csv, src/composition.py)
      plus a TYPICAL oxide composition for that rock type (literature values)
    - its 5 best Earth analogs, one per region (data/results_per_target_top_regions.csv),
      with the Earth values, the similarity of every feature and the Earth
      rock class read from ASTER em_contrast
    - every image that belongs to it (relief maps and photos in maps/,
      surface photos in experiments/fotos_analogos/), with credit and source

Output: web/public/data/analogos.json
Images are NOT copied here: web/scripts/copy-data-images.mjs copies them into
web/public/data/img/ before `npm run dev` / `npm run build` (see web/DATOS.md).

Example (from the repo root, after src/make_results.py):
    python src/export_analogos.py
"""

import json
import math
import re
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "public" / "data" / "analogos.json"
IMG_URL = "/data/img/"          # where copy-data-images.mjs puts the images
N_ANALOGS = 5                   # analogs per site in the JSON (the app can show fewer)
SAME_PLACE_KM = 10              # an Earth image is "of this place" if closer than this

FEATURES = {  # key: (label, unit)
    "elev_m": ("Elevación", "m"),
    "slope_deg": ("Pendiente", "°"),
    "roughness": ("Rugosidad", "m"),
    "temp_mean_K": ("Temperatura media", "K"),
    "temp_range_K": ("Variación de temperatura", "K"),
    "albedo": ("Albedo", ""),
    "precip_mm": ("Precipitación anual", "mm"),
    "ndvi": ("Vegetación (NDVI)", ""),
    "em_contrast": ("Composición de la roca (contraste de emisividad)", ""),
}
RADIUS_KM = {"Moon": 1737.4, "Mars": 3389.5, "Earth": 6371.0}

# ---------------------------------------------------------------------------
# Typical oxide composition (wt %) of each rock type. APPROXIMATE literature
# values for the rock TYPE, not measurements of the exact place.
# ---------------------------------------------------------------------------
OXIDES = ["SiO2", "TiO2", "Al2O3", "FeO", "MgO", "CaO", "Na2O", "K2O"]
ROCK_TYPES = {
    "luna_feldespatica": dict(
        label="Tierras altas feldespáticas (anortosita)",
        oxides=[45.0, 0.6, 27.0, 5.5, 6.0, 15.5, 0.45, 0.11],
        source="Promedio del regolito de Apolo 16 (Lunar Sourcebook; Korotev 1981)"),
    "luna_feldespatica_noritica": dict(
        label="Tierras altas feldespáticas con norita (borde de la cuenca SPA)",
        oxides=[45.5, 0.7, 22.0, 8.0, 9.0, 13.0, 0.5, 0.15],
        source="Valor aproximado intermedio entre Apolo 16 y norita de SPA (Lunar Prospector)"),
    "marte_basalto_olivinico": dict(
        label="Basalto rico en olivino",
        oxides=[45.7, 0.5, 10.9, 18.8, 10.8, 7.8, 2.4, 0.07],
        source="Basalto Adirondack, cráter Gusev (Spirit APXS; McSween et al. 2006)"),
    "marte_suelo_basaltico": dict(
        label="Suelo y arena basáltica marciana",
        oxides=[45.4, 0.9, 9.6, 17.6, 8.3, 7.0, 2.6, 0.45],
        source="Suelo marciano promedio (Spirit, Opportunity, Curiosity APXS; Yen et al. 2005, "
               "O'Connell-Cooper et al. 2017). Además ~6 % SO3 y ~0.7 % Cl"),
    "marte_tipo2": dict(
        label="Tipo de superficie 2 de TES (andesita basáltica o basalto alterado)",
        oxides=[55.0, 1.0, 16.0, 9.0, 4.5, 7.5, 3.3, 1.2],
        source="Andesita basáltica típica de la Tierra. Si es basalto alterado, se parece más a "
               "'marte_suelo_basaltico' (Bandfield et al. 2000; Wyatt & McSween 2002)"),
    "tierra_basalto": dict(
        label="Basalto",
        oxides=[49.2, 1.8, 15.7, 10.4, 6.7, 9.5, 2.9, 1.1],
        source="Basalto promedio (Le Maitre 1976)"),
    "tierra_andesita": dict(
        label="Andesita / roca intermedia",
        oxides=[57.9, 0.9, 17.0, 6.9, 3.3, 6.8, 3.5, 1.6],
        source="Andesita promedio (Le Maitre 1976)"),
    "tierra_granito": dict(
        label="Granito / roca félsica",
        oxides=[71.3, 0.3, 14.3, 2.6, 0.7, 1.8, 3.7, 4.1],
        source="Granito promedio (Le Maitre 1976)"),
    "tierra_arena_cuarzo": dict(
        label="Arena o arenisca de cuarzo",
        oxides=[92.0, 0.2, 3.5, 0.8, 0.3, 1.0, 0.4, 1.2],
        source="Arena de duna cuarzosa típica (valor aproximado; sin contar carbonatos)"),
}
SITE_ROCK = {
    "Shackleton rim": "luna_feldespatica", "de Gerlache rim": "luna_feldespatica",
    "Mons Mouton summit": "luna_feldespatica", "Shackleton floor (shadow)": "luna_feldespatica",
    "Haworth rim": "luna_feldespatica_noritica", "Faustini rim": "luna_feldespatica_noritica",
    "Jezero crater (Perseverance)": "marte_basalto_olivinico", "Gusev crater (Spirit)": "marte_basalto_olivinico",
    "Gale crater (Curiosity)": "marte_suelo_basaltico", "Meridiani Planum (Opportunity)": "marte_suelo_basaltico",
    "Elysium Planitia (InSight)": "marte_suelo_basaltico", "Chryse Planitia (Viking 1)": "marte_suelo_basaltico",
    "Utopia Planitia (Viking 2)": "marte_tipo2", "Vastitas Borealis (Phoenix)": "marte_tipo2",
    "Arcadia Planitia (human candidate)": "marte_tipo2",
}

# Same line as src/composition.py (kept in sync by reading the site table when possible)
CAL_A, CAL_B = 2.1639, -0.2625


def earth_rock(em):
    """Rock class of an Earth cell from its ASTER em_contrast."""
    if em is None or (isinstance(em, float) and math.isnan(em)):
        return None
    cf = (em - CAL_A) / CAL_B
    if em < 0.01:
        key, note = "tierra_basalto", ("Contraste bajo: basalto u otra roca máfica, pero también carbonatos, "
                                       "arcillas, evaporitas o hielo dan valores así. Confirmar con mapa geológico.")
    elif em < 0.07:
        key, note = "tierra_andesita", "Contraste intermedio: roca intermedia o mezcla de materiales."
    elif em < 0.14:
        key, note = "tierra_granito", "Contraste alto: roca félsica o arena con bastante cuarzo."
    else:
        key, note = "tierra_arena_cuarzo", "Contraste muy alto: arena o arenisca rica en cuarzo."
    return dict(em_contrast=round(em, 4), cf_equivalent_um=round(cf, 2), rock_type=key,
                ambiguous=em < 0.01, note=note)


def region_label(region):
    return region.replace("_", " ").title()


def slug(text):
    text = re.sub(r"\(.*?\)", "", text).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def distance_km(lat1, lon1, lat2, lon2, radius):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    c = math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dl)
    return radius * math.acos(max(-1.0, min(1.0, c)))


def num(x, nd=4):
    return None if pd.isna(x) else round(float(x), nd)


def image(src, kind, title, credit=None, source=None, lat=None, lon=None, **extra):
    return dict(kind=kind, src=src, url=IMG_URL + src, title=title, credit=credit, source=source,
                lat=lat, lon=lon, **extra)


def main():
    targets = pd.read_csv(ROOT / "data/targets.csv")
    comp = pd.read_csv(ROOT / "data/composition_targets.csv").set_index("name")
    top = pd.read_csv(ROOT / "data/results_per_target_top_regions.csv")
    catalog = pd.read_csv(ROOT / "data/regions_catalog.csv", comment="#").set_index("name")
    maps = pd.read_csv(ROOT / "maps/index.csv")
    photo_src = pd.read_csv(ROOT / "maps/photo_sources.csv").set_index("image")["source"].to_dict()
    fotos = pd.read_csv(ROOT / "experiments/fotos_analogos/imagenes/fotos.csv")
    old_set = pd.read_csv(ROOT / "experiments/fotos_analogos/sites.csv", dtype={"id": str})

    def map_photo(png):
        """The satellite/orbital photo next to a relief map, if it exists."""
        photo = png.replace(".png", "_photo.png")
        return photo if (ROOT / "maps" / photo).exists() else None

    def default_credit(name):
        if name in photo_src:
            return photo_src[name]
        if "_earth_" in name:                      # same sources as src/make_photos.py
            return "Sentinel-2 L2A true colour 10 m (ESA Copernicus, via AWS earth-search)"
        if "_mars_" in name:
            return "CTX mosaic 5 m (NASA/JPL/MSSS, Caltech Murray Lab, Esri OnMars)"
        return "LROC WAC south pole mosaic 100 m (NASA/LRO/ASU)"

    # Surface photos: link to the nearest target of the same body (if close enough)
    used_photo_ids = set()
    surface = {}
    reference = []
    body_es = {"Marte": "Mars", "Luna": "Moon"}
    for _, f in fotos.iterrows():
        body = body_es.get(f["cuerpo"], f["cuerpo"])
        cands = targets[targets["body"] == body]
        d = cands.apply(lambda t: distance_km(t.site_lat, t.site_lon, f.lat, f.lon, RADIUS_KM[body]), axis=1)
        img = image("experiments/fotos_analogos/imagenes/" + f["archivo"], "foto_superficie" if f["tipo"] == "superficie"
                    else "foto_orbital", f["sitio"], f["credito"], f["url_fuente"], float(f["lat"]), float(f["lon"]),
                    mission=f["mision"], instrument=f["instrumento"], date=f["sol_o_fecha"],
                    product_id=f["id_original"], licence=f["licencia"], coord_precision=f["precision_coord"],
                    width=int(f["ancho"]), height=int(f["alto"]))
        used_photo_ids.add(str(f["id_original"]))
        if len(d) and d.min() <= 60:
            name = cands.loc[d.idxmin(), "name"]
            img["distance_to_site_km"] = round(float(d.min()), 1)
            surface.setdefault(name, []).append(img)
        else:
            img["body"] = body
            reference.append(img)
    for _, s in old_set.iterrows():
        if str(s["pia_or_product_id"]) in used_photo_ids or pd.isna(s.get("preview")):
            continue
        surface.setdefault(s["target_name"], []).append(image(
            "experiments/fotos_analogos/" + s["preview"], "foto_orbital" if s["body"] == "Moon" else "foto_superficie",
            s["image_title"], s["credit"], s["source_page"], float(s["site_lat"]), float(s["site_lon"]),
            mission=s["mission_instrument"], date=None if pd.isna(s["sol_or_date"]) else s["sol_or_date"],
            product_id=s["pia_or_product_id"], licence=s["licence"], note=s["note"]))

    sites = []
    for number, (_, t) in enumerate(targets.iterrows(), start=1):
        name, body = t["name"], t["body"]
        c = comp.loc[name]
        rock_key = SITE_ROCK[name]
        site_maps = maps[maps["target"] == name]

        images = []
        if len(site_maps):
            twin = site_maps["image_twin"].iloc[0]
            images.append(image("maps/" + twin, "mapa_relieve", f"Relieve de {name}",
                                credit="LOLA (Luna) / HRSC-MOLA (Marte), NASA", lat=t.site_lat, lon=t.site_lon))
            if map_photo(twin):
                p = map_photo(twin)
                images.append(image("maps/" + p, "foto_orbital", f"Vista orbital de {name}",
                                    credit=default_credit(p), lat=t.site_lat, lon=t.site_lon))
        images += surface.get(name, [])

        analogs = []
        for _, a in top[top["target"] == name].sort_values("region_rank").head(N_ANALOGS).iterrows():
            region = a["region"]
            a_images = []
            for _, m in site_maps[site_maps["earth_region"] == region].iterrows():
                d = distance_km(a.lat, a.lon, m.earth_lat, m.earth_lon, RADIUS_KM["Earth"])
                same = d <= SAME_PLACE_KM
                extra = dict(same_place=bool(same), distance_km=round(d, 1))
                if not same:
                    extra["note"] = ("Imagen de otro punto de la misma región (el mejor lugar antes de "
                                     "añadir la composición). Regenerar con src/make_maps.py.")
                a_images.append(image("maps/" + m["image_earth"], "mapa_relieve", f"Relieve en {region}",
                                      credit="Copernicus DEM 90 m / NASADEM", lat=m.earth_lat, lon=m.earth_lon, **extra))
                if map_photo(m["image_earth"]):
                    p = map_photo(m["image_earth"])
                    a_images.append(image("maps/" + p, "foto_satelite", f"Foto satelital en {region}",
                                          credit=default_credit(p), lat=m.earth_lat, lon=m.earth_lon, **extra))
            cat = catalog.loc[region] if region in catalog.index else None
            analogs.append(dict(
                rank=int(a["region_rank"]), region=region, region_label=region_label(region),
                region_description=None if cat is None else cat["why"],
                lat=num(a["lat"], 3), lon=num(a["lon"], 3), score=num(a["score"]),
                earth_values={k: num(a[k]) for k in FEATURES if k in a and k != "elev_m"} | {"elev_m": num(a["elev_m"], 1)},
                similarity={k: num(a.get(f"sim_{k}")) for k in FEATURES if f"sim_{k}" in a},
                best_match=a["best_match"], worst_match=a["worst_match"],
                composition=earth_rock(a["em_contrast"]),
                images=a_images,
            ))

        sites.append(dict(
            id=slug(name), number=number, name=name, body=body,
            lat=t.site_lat, lon=t.site_lon, area=t.get("area"),
            values={k: num(t[k]) for k in FEATURES},
            composition=dict(
                lithology=c["lithology"], cf_um=num(c["cf_um"], 2), cf_sigma_um=num(c["cf_sigma_um"], 2),
                em_contrast=num(c["em_contrast"]), em_contrast_sigma=num(c["em_contrast_sigma"]),
                evidence=c["evidence"], rock_type=rock_key),
            images=images,
            analogs=analogs,
        ))

    overall = {}
    for body in ("Moon", "Mars"):
        per_region = pd.read_csv(ROOT / f"data/results_{body.lower()}_new_per_region.csv")
        rows = []
        for _, r in per_region.iterrows():
            rows.append(dict(rank=int(r["rank"]), region=r["region"], lat=num(r["lat"], 3), lon=num(r["lon"], 3),
                             mean_score=num(r["mean_score"]), conditions_met=r["conditions_met"],
                             weakest=r["weakest"],
                             similarity={c[4:]: num(r[c]) for c in per_region.columns if c.startswith("sim_")}))
        overall[body] = rows

    regions = [dict(name=n, west=r.west, south=r.south, east=r.east, north=r.north,
                    known=r.known == "yes", description=r.why) for n, r in catalog.iterrows()]

    data = dict(
        generated=str(date.today()),
        about=("Lugares poco conocidos de la Tierra análogos a sitios de bases en la Luna y Marte. "
               "score: similitud total 0..1; similarity: similitud por variable 0..1."),
        features={k: dict(label=l, unit=u) for k, (l, u) in FEATURES.items()},
        composition_method=("em_contrast = emisividad ASTER (10.6-11.3 um) - (8.3-9.1 um). En la Luna y Marte "
                            "es un valor EQUIVALENTE calculado con el Christiansen feature (Diviner / TES): "
                            "indicador aproximado del tipo de roca, ±0.03. Ver docs/COMPOSICION.md."),
        oxides_order=OXIDES,
        oxides_note=("Composición TÍPICA del tipo de roca (% en peso, valores de literatura), "
                     "no medida en el lugar exacto. FeO = hierro total."),
        rock_types={k: dict(label=v["label"], oxides=dict(zip(OXIDES, v["oxides"])), source=v["source"])
                    for k, v in ROCK_TYPES.items()},
        sites=sites,
        overall=overall,
        regions=regions,
        reference_photos=reference,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1, allow_nan=False, default=lambda o: None
                              if isinstance(o, float) and math.isnan(o) else str(o)))
    n_img = sum(len(s["images"]) + sum(len(a["images"]) for a in s["analogs"]) for s in sites) + len(reference)
    print(f"Saved {OUT.relative_to(ROOT)}: {len(sites)} sites, {n_img} image links, "
          f"{len(reference)} reference photos")


if __name__ == "__main__":
    main()
