"""
region_names.py - Readable names (Spanish and English) for the Earth regions of
data/regions_catalog.csv, used by src/export_web.py.

Two kinds of regions:
    named regions   e.g. "egypt_western_desert": a hand-picked area
    grid regions    e.g. "egypt_22n_032e": a 2 x 2 degree tile of the worldwide
                    drylands search; it gets the country name and the app shows
                    its coordinates next to it.
"""

import re

# Country prefix of the grid regions -> (es, en).
COUNTRIES = {
    "algeria": ("Argelia", "Algeria"),
    "angola": ("Angola", "Angola"),
    "argentina": ("Argentina", "Argentina"),
    "australia": ("Australia", "Australia"),
    "azerbaijan": ("Azerbaiyán", "Azerbaijan"),
    "bolivia": ("Bolivia", "Bolivia"),
    "canada": ("Canadá", "Canada"),
    "chad": ("Chad", "Chad"),
    "chile": ("Chile", "Chile"),
    "egypt": ("Egipto", "Egypt"),
    "eritrea": ("Eritrea", "Eritrea"),
    "greenland": ("Groenlandia", "Greenland"),
    "kazakhstan": ("Kazajistán", "Kazakhstan"),
    "kyrgyzstan": ("Kirguistán", "Kyrgyzstan"),
    "libya": ("Libia", "Libya"),
    "mali": ("Malí", "Mali"),
    "mauritania": ("Mauritania", "Mauritania"),
    "mexico": ("México", "Mexico"),
    "mongolia": ("Mongolia", "Mongolia"),
    "morocco": ("Marruecos", "Morocco"),
    "namibia": ("Namibia", "Namibia"),
    "niger": ("Níger", "Niger"),
    "pakistan": ("Pakistán", "Pakistan"),
    "peru": ("Perú", "Peru"),
    "somalia": ("Somalia", "Somalia"),
    "somaliland": ("Somalilandia", "Somaliland"),
    "south_africa": ("Sudáfrica", "South Africa"),
    "spain": ("España", "Spain"),
    "sudan": ("Sudán", "Sudan"),
    "tajikistan": ("Tayikistán", "Tajikistan"),
    "tunisia": ("Túnez", "Tunisia"),
    "turkmenistan": ("Turkmenistán", "Turkmenistan"),
    "united_states_of_america": ("Estados Unidos", "United States"),
    "uzbekistan": ("Uzbekistán", "Uzbekistan"),
    "western_sahara": ("Sahara Occidental", "Western Sahara"),
}

# Named regions -> (name es, name en, country es, country en).
NAMED = {
    "northern_andes": ("Andes del norte", "Northern Andes", "Colombia, Ecuador y Venezuela", "Colombia, Ecuador and Venezuela"),
    "dry_valleys": ("Valles Secos de McMurdo", "McMurdo Dry Valleys", "Antártida", "Antarctica"),
    "antarctic_plateau": ("Meseta antártica", "Antarctic Plateau", "Antártida", "Antarctica"),
    "devon_island": ("Isla Devon", "Devon Island", "Canadá", "Canada"),
    "axel_heiberg": ("Isla Axel Heiberg", "Axel Heiberg Island", "Canadá", "Canada"),
    "north_greenland": ("Norte de Groenlandia (Peary Land)", "North Greenland (Peary Land)", "Groenlandia", "Greenland"),
    "svalbard": ("Svalbard", "Svalbard", "Noruega", "Norway"),
    "iceland_highlands": ("Tierras altas de Islandia", "Iceland Highlands", "Islandia", "Iceland"),
    "kamchatka": ("Kamchatka", "Kamchatka", "Rusia", "Russia"),
    "atacama": ("Desierto de Atacama", "Atacama Desert", "Chile", "Chile"),
    "puna": ("Puna de Atacama", "Puna de Atacama", "Argentina", "Argentina"),
    "uyuni_altiplano": ("Altiplano de Uyuni", "Uyuni Altiplano", "Bolivia", "Bolivia"),
    "qaidam_tibet": ("Cuenca de Qaidam", "Qaidam Basin", "China", "China"),
    "ladakh": ("Ladakh", "Ladakh", "India", "India"),
    "pamir": ("Pamir", "Pamir", "Tayikistán", "Tajikistan"),
    "taklamakan": ("Desierto de Taklamakán", "Taklamakan Desert", "China", "China"),
    "gobi": ("Desierto de Gobi", "Gobi Desert", "Mongolia y China", "Mongolia and China"),
    "lut_iran": ("Desierto de Lut", "Lut Desert", "Irán", "Iran"),
    "rub_al_khali": ("Rub al-Jali", "Rub' al Khali", "Arabia Saudita", "Saudi Arabia"),
    "danakil": ("Depresión de Danakil", "Danakil Depression", "Etiopía y Eritrea", "Ethiopia and Eritrea"),
    "tibesti": ("Macizo del Tibesti", "Tibesti Mountains", "Chad", "Chad"),
    "namib": ("Desierto de Namib", "Namib Desert", "Namibia", "Namibia"),
    "pilbara": ("Pilbara", "Pilbara", "Australia", "Australia"),
    "mojave_death_valley": ("Mojave y Valle de la Muerte", "Mojave and Death Valley", "Estados Unidos", "United States"),
    "utah_mdrs": ("Desierto de Utah (MDRS)", "Utah desert (MDRS)", "Estados Unidos", "United States"),
    "mauna_kea_hawaii": ("Mauna Kea", "Mauna Kea", "Estados Unidos (Hawái)", "United States (Hawaii)"),
    "teide_tenerife": ("Teide", "Teide", "España (Tenerife)", "Spain (Tenerife)"),
    "rio_tinto": ("Río Tinto", "Río Tinto", "España", "Spain"),
    "fezzan_libya": ("Fezán", "Fezzan", "Libia", "Libya"),
    "egypt_western_desert": ("Desierto Occidental", "Western Desert", "Egipto", "Egypt"),
    "tanezrouft_sahara": ("Tanezrouft", "Tanezrouft", "Argelia y Malí", "Algeria and Mali"),
    "changtang_tibet": ("Changtang (Tíbet)", "Changtang (Tibet)", "China", "China"),
    "transantarctic_mts": ("Montes Transantárticos", "Transantarctic Mountains", "Antártida", "Antarctica"),
    "prince_charles_mts": ("Montes Príncipe Carlos", "Prince Charles Mountains", "Antártida", "Antarctica"),
    "tenere_niger": ("Teneré", "Ténéré", "Níger", "Niger"),
    "nubian_desert_sudan": ("Desierto de Nubia", "Nubian Desert", "Sudán", "Sudan"),
    "djourab_chad": ("Desierto de Djurab", "Djourab Desert", "Chad", "Chad"),
    "adrar_mauritania": ("Adrar", "Adrar", "Mauritania", "Mauritania"),
    "kumtag_lop_nur": ("Kumtag y Lop Nur", "Kumtag and Lop Nur", "China", "China"),
    "badain_jaran": ("Desierto de Badain Jaran", "Badain Jaran Desert", "China", "China"),
    "dasht_margo": ("Dasht-i-Margo", "Dasht-i-Margo", "Afganistán", "Afghanistan"),
    "victoria_island": ("Isla Victoria", "Victoria Island", "Canadá", "Canada"),
    "ellesmere_north": ("Norte de la isla Ellesmere", "Northern Ellesmere Island", "Canadá", "Canada"),
}

GRID = re.compile(r"^(?P<country>.+)_(?P<lat>\d\d)(?P<ns>[ns])_(?P<lon>\d\d\d)(?P<ew>[ew])$")


def is_grid(region):
    return bool(GRID.match(str(region)))


def region_names(region):
    """
    {"name": {es, en}, "country": {es, en}, "grid": bool} for a region id.
    Grid tiles are named after their country (the app adds the coordinates).
    Unknown names fall back to a title-cased version of the id.
    """
    region = str(region)
    if region in NAMED:
        es, en, ces, cen = NAMED[region]
        return {"name": {"es": es, "en": en}, "country": {"es": ces, "en": cen}, "grid": False}
    m = GRID.match(region)
    if m and m["country"] in COUNTRIES:
        ces, cen = COUNTRIES[m["country"]]
        return {"name": {"es": ces, "en": cen}, "country": {"es": ces, "en": cen}, "grid": True}
    label = region.replace("_", " ").title()
    return {"name": {"es": label, "en": label}, "country": {"es": "", "en": ""}, "grid": bool(m)}
