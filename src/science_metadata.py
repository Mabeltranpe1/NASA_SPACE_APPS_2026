"""Physical definitions for regional products; these are not global cell features."""

SCHEMA_VERSION = "1.0.0"
SCIENCE_COMMIT = "aaf4ebb411e2005b159f90e7c078c81f8d93be6e"
GLOBAL_COMMIT = "e75ecdb583d26223cc57ceae142672492f5282aa"
WEB_COMMIT = "58313dc"


def bilingual(es, en):
    return {"es": es, "en": en}


SITES = {
    "Tatacoa": ("tatacoa", "Tatacoa", "Tatacoa", 3.2300, -75.1700),
    "La_Guajira": ("la-guajira", "La Guajira", "La Guajira", 12.43653, -71.60899),
    "La_Candelaria": ("la-candelaria", "La Candelaria", "La Candelaria", 5.5368, -73.6163),
    "Nevado_del_Ruiz": ("nevado-del-ruiz", "Nevado del Ruiz", "Nevado del Ruiz", 4.895, -75.322),
    "Nevado_Santa_Isabel": ("nevado-santa-isabel", "Nevado Santa Isabel", "Nevado Santa Isabel", 4.818, -75.365),
    "Volcan_Purace": ("volcan-purace", "Volcán Puracé", "Puracé Volcano", 2.3095, -76.3948),
}

SOURCES = {
    "nasadem": ("NASADEM HGT 001", "NASA / LP DAAC", "https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001", "derived_observation"),
    "lola": ("LRO LOLA polar site DEMs", "NASA GSFC / PGDA", "https://pgda.gsfc.nasa.gov/products/78", "derived_observation"),
    "mola_hrsc": ("MOLA / HRSC blended DEM v2", "NASA / ESA / USGS", "https://astrogeology.usgs.gov/search/map/mars_mgs_mola_mex_hrsc_blended_dem_global_200m", "derived_observation"),
    "power": ("NASA POWER", "NASA LaRC", "https://power.larc.nasa.gov/", "gridded_estimate"),
    "modis_lst": ("MODIS MOD11A1.061", "NASA / LP DAAC", "https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD11A1", "observation"),
    "modis_ndvi": ("MODIS MOD13Q1.061", "NASA / LP DAAC", "https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1", "derived_observation"),
    "chirps": ("CHIRPS v2 daily", "UCSB Climate Hazards Center", "https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY", "gridded_estimate"),
    "worldcover": ("ESA WorldCover v200 (2021)", "ESA / Copernicus", "https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v200", "classification"),
    "sentinel2": ("Sentinel-2 MSI L2A harmonized", "ESA / Copernicus", "https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED", "derived_observation"),
    "sgc": ("Atlas Geológico de Colombia 2023", "Servicio Geológico Colombiano", "https://srvags.sgc.gov.co/arcgis/rest/services/Mapa_Geologico_Colombia/Mapa_Geologico_Colombia_V2023/MapServer/733", "geological_map"),
    "emit": ("EMITL2BMIN.001", "NASA JPL / LP DAAC", "https://doi.org/10.5067/EMIT/EMITL2BMIN.001", "provisional_spectral_match"),
    "crism": ("MRO CRISM MTRDR / MRDR4", "NASA / APL / PDS", "https://pds-geosciences.wustl.edu/missions/mro/crism.htm", "spectral_indicator"),
    "tes": ("MGS TES TIMAP v1.0", "NASA / PDS", "https://doi.org/10.17189/1519489", "thermophysical_inversion"),
    "themis": ("Mars Odyssey THEMIS IRPBT", "NASA / ASU / PDS", "https://pds-geosciences.wustl.edu/missions/odyssey/themis.html", "pilot_brightness_temperature"),
    "diviner": ("LRO Diviner PRP v2.0", "NASA / UCLA / PDS", "https://pds-geosciences.wustl.edu/missions/lro/diviner.htm", "thermophysical_model"),
}

# section id: file, title, source ids, spatial support, period, method, compatibility.
# Field-level entries below refine mixed-source sections such as environment.
SECTION_SPECS = {
    "topography": ("planetary_features.csv", bilingual("Topografía a 200 m", "Topography at 200 m"), [], "200 m grid; nominal 10 × 10 km DEM window", "source acquisition epochs; see DEM provenance", "Metric DEM gradients; complete 3×3 neighborhoods; Riley TRI and eight-neighbor TPI", "regional_support; TRI is not global local-height standard deviation"),
    "climate": ("climate_features.csv", bilingual("Clima del aire y energía solar", "Air climate and solar energy"), ["power"], "POWER point-associated coarse grid; not a summit station or a 10 km spatial average", "2021-01-01 / 2025-12-31", "Daily series aggregated by the original extract_climate.py", "air_temperature_is_not_surface_temperature"),
    "environment": ("environmental_features.csv", bilingual("Ambiente y cobertura terrestre", "Environment and land cover"), ["modis_lst", "modis_ndvi", "chirps", "worldcover"], "Original GEE regional footprint; approximately 100 km², distinct from DEM bounds", "2021–2025; WorldCover 2021", "Original GEE QA, regional aggregation; paired LST differences; CHIRPS five-year annual mean", "different_period_support_and_estimators_from_global_cell"),
    "spectral": ("spectral_features.csv", bilingual("Reflectancia e índices Sentinel-2", "Sentinel-2 reflectance and indices"), ["sentinel2"], "20 m analysis; regional low-vegetation subset where specified", "2025-01-01 / 2026-01-01 exclusive", "Temporal band medians; NDVI<0.2 subset; BSI, B4/B2 and B11/B12 ratios", "spectral_proxy_not_mineral_concentration"),
    "geology_coverage": ("geological_coverage.csv", bilingual("Cobertura del mapa geológico", "Geological map coverage"), ["sgc"], "1:500,000 map intersected with the processed DEM window", "Atlas 2023", "Polygon intersections and union areas; unmapped area retained", "regional_map_not_200m_lithology_measurement"),
    "geology": ("geological_features.csv", bilingual("Unidades geológicas", "Geological units"), ["sgc"], "1:500,000 map; clipped regional polygons", "Atlas 2023", "Area by unit; percentages use study area or mapped area as named", "regional_geological_map"),
    "emit_availability": ("emit_availability.csv", bilingual("Disponibilidad EMIT", "EMIT availability"), ["emit"], "Catalogue intersection; not valid surface coverage", "catalogue query snapshot", "Earthaccess catalogue search", "availability_is_not_a_mineral_detection"),
    "emit_coverage": ("mineralogical_coverage.csv", bilingual("EMIT: cobertura y aceptación", "EMIT: coverage and acceptance"), ["emit"], "Native pixel centers in DEM window; 200 m bins touched are diagnostic, not area coverage", "selected acquisitions; see scene quality", "Two spectral groups; fit stored ≥0.20, depth≥0.02 and depth≥2×uncertainty", "provisional_observation_counts_not_concentration"),
    "emit_minerals": ("mineralogical_features.csv", bilingual("EMIT: coincidencias de biblioteca", "EMIT: spectral library matches"), ["emit"], "Approximately 60 m native observations pooled across selected scenes", "selected acquisitions; see scene quality", "Counts and weighted sums of accepted matches; fit corrected by ×2", "provisional_spectral_match_not_confirmed_mineral_or_resource"),
    "emit_quality": ("mineralogical_scene_quality.csv", bilingual("EMIT: calidad por escena", "EMIT: scene quality"), ["emit"], "Native observations and center-bin diagnostics", "acquisition_utc per scene", "Missing, rejected and accepted observations retained; no L2A cloud or marine mask", "quality_and_coverage_not_detection_probability"),
    "emit_scene_matches": ("mineralogical_scene_features.csv", bilingual("EMIT: resultados por adquisición", "EMIT: results by acquisition"), ["emit"], "Native observations within the original regional footprint", "acquisition_utc per scene", "Accepted library matches per scene and spectral group", "provisional_spectral_match"),
    "tes": ("thermal_mars_features.csv", bilingual("TES: inercia térmica", "TES: thermal inertia"), ["tes"], "Native 0.05° cells; nominal 100 km² LAEA square on TES sphere (R=3,396 km)", "1999–2004; map 2007", "Native-cell intersection area weighting; interpolation-mask exclusion; ≥80% quality threshold", "thermal_inertia_is_not_temperature"),
    "themis": ("themis_thermal_features.csv", bilingual("THEMIS: temperatura de brillo piloto", "THEMIS: pilot brightness temperature"), ["themis"], "Native projected pixels intersecting DEM window; equal weight for accepted scene means", "unpaired acquisitions and seasons; see scene metadata", "Separate illumination candidates and band groups; minimum 80% valid area", "band_unverified_not_a_climatology_or_paired_thermal_range"),
    "themis_scenes": ("themis_scene_features.csv", bilingual("THEMIS: calidad y escenas", "THEMIS: quality and scenes"), ["themis"], "Native projected pixels; scene valid area retained", "utc and solar_longitude_deg per scene", "PDS label scales/offset once; valid constants, range and illumination checks", "brightness_not_kinetic_temperature"),
    "crism": ("mineralogical_mars_features.csv", bilingual("CRISM: indicadores espectrales", "CRISM: spectral indicators"), ["crism"], "Native mapped CRISM cells intersecting DEM footprint; product-dependent resolution", "per product acquisition; see manifests", "Area-weighted parameters; ≥80% coverage for primary records; unavailable rows retained", "spectral_indicator_not_mineral_concentration"),
    "crism_quality": ("crism_scene_quality.csv", bilingual("CRISM: calidad geométrica", "CRISM: geometric quality"), ["crism"], "Native projected product; non-spherical or planetographic products conservatively rejected", "per product", "Label and CRS validation; explicit errors are retained", "unavailable_is_not_zero"),
    "crism_all": ("crism_parameter_features.csv", bilingual("CRISM: parámetros y cobertura completa", "CRISM: all parameters and coverage"), ["crism"], "Native product cells; includes low-coverage or invalid observations", "per product", "Same parameters as primary table, including unqualified observations", "do_not_treat_unqualified_observations_as_primary"),
    "diviner": ("thermal_moon_features.csv", bilingual("Diviner: temperatura y estabilidad modelada", "Diviner: temperature and modeled ice stability"), ["diviner"], "Native triangular facets; horizontal equal-area intersection with LOLA study window", "annual model statistics, PRP v2.0", "Native-facet area weighting; 2 cm annual mean separated from surface maximum; −32768 depth means beyond 2.8738 m", "modeled_ice_stability_is_not_ice_detection"),
}

EARTH_SECTIONS = ["topography", "climate", "environment", "spectral", "geology_coverage", "geology", "emit_availability", "emit_coverage", "emit_minerals", "emit_quality", "emit_scene_matches"]
MARS_SECTIONS = ["topography", "tes", "themis", "themis_scenes", "crism", "crism_quality", "crism_all"]
MOON_SECTIONS = ["topography", "diviner"]

PAI_FEATURES = ["relief_p90_p10_m", "elevation_std_m", "slope_mean_deg", "slope_p90_deg", "tri_mean_m", "tpi_std_m"]
PAI_WEIGHTS = [0.15, 0.15, 0.15, 0.15, 0.15, 0.25]

# A possible global counterpart is documented, never assigned to a global cell.
GLOBAL_COUNTERPARTS = {
    "elevation_mean_m": ("elev_m", "different_spatial_support_and_vertical_datum"),
    "slope_mean_deg": ("slope_deg", "different_footprint_and_derivative_implementation"),
    "tri_mean_m": ("roughness", "incompatible_definition_Riley_TRI_vs_local_height_std"),
    "tpi_std_m": (None, "no_global_TPI_variable"),
    "lst_day_mean_c": ("temp_mean_K", "day_only_vs_day_night_mean_and_different_period"),
    "lst_night_mean_c": ("temp_mean_K", "night_only_vs_day_night_mean_and_different_period"),
    "thermal_range_mean_c": ("temp_range_K", "paired_day_night_difference_vs_global_max_minus_mean"),
    "air_temperature_mean_c": ("temp_mean_K", "incompatible_air_vs_surface_temperature"),
    "annual_precipitation_mm": ("precip_mm", "multi_year_CHIRPS_mean_vs_global_year_GPM_or_MERRA2"),
    "ndvi_mean": ("ndvi", "different_product_footprint_and_period"),
    "iron_oxide_ratio_mean": ("em_contrast", "incompatible_optical_ratio_vs_thermal_emissivity"),
    "hydroxyl_ratio_mean": ("em_contrast", "incompatible_optical_ratio_vs_thermal_emissivity"),
}

LABELS = {
    "elevation_mean_m": bilingual("Elevación media", "Mean elevation"),
    "elevation_min_m": bilingual("Elevación mínima", "Minimum elevation"),
    "elevation_max_m": bilingual("Elevación máxima", "Maximum elevation"),
    "relief_p90_p10_m": bilingual("Relieve robusto P90−P10", "Robust relief P90−P10"),
    "local_relief_m": bilingual("Relieve máximo−mínimo", "Maximum−minimum relief"),
    "slope_mean_deg": bilingual("Pendiente media", "Mean slope"),
    "tri_mean_m": bilingual("TRI de Riley medio", "Mean Riley TRI"),
    "tpi_std_m": bilingual("Desviación estándar del TPI", "TPI standard deviation"),
    "flat_terrain_pct": bilingual("Terreno con pendiente <5°", "Terrain with slope <5°"),
    "lst_day_mean_c": bilingual("LST diurna", "Daytime LST"),
    "lst_night_mean_c": bilingual("LST nocturna", "Nighttime LST"),
    "thermal_range_mean_c": bilingual("Diferencia LST día−noche emparejada", "Paired daytime−nighttime LST difference"),
    "annual_precipitation_mm": bilingual("Precipitación anual media CHIRPS", "CHIRPS mean annual precipitation"),
    "air_temperature_mean_c": bilingual("Temperatura media del aire a 2 m", "Mean air temperature at 2 m"),
    "surface_pressure_mean_kpa": bilingual("Presión superficial", "Surface pressure"),
    "wind_speed_mean_ms": bilingual("Viento medio a 10 m", "Mean wind at 10 m"),
    "relative_humidity_mean_pct": bilingual("Humedad relativa", "Relative humidity"),
    "solar_radiation_daily_mean": bilingual("Irradiación solar diaria", "Daily solar irradiation"),
    "surface_soil_wetness_mean": bilingual("Humedad relativa del suelo superficial", "Relative surface soil wetness"),
    "water_pct": bilingual("Agua en la ventana WorldCover", "WorldCover water in the window"),
    "mineral_name": bilingual("Entrada de biblioteca espectral", "Spectral library entry"),
    "detection_pct_of_valid_observations": bilingual("Coincidencias / observaciones válidas", "Matches / valid observations"),
    "detection_pct_of_accepted_observations": bilingual("Coincidencias / observaciones aceptadas", "Matches / accepted observations"),
    "band_depth_mean": bilingual("Profundidad media de banda", "Mean band depth"),
    "band_depth_uncertainty_mean": bilingual("Incertidumbre media de profundidad", "Mean band-depth uncertainty"),
    "fit_corrected_mean": bilingual("Ajuste espectral corregido ×2", "Spectral fit corrected ×2"),
    "pct_study_area": bilingual("Porcentaje de la ventana", "Share of study window"),
    "pct_mapped_area": bilingual("Porcentaje del área cartografiada", "Share of mapped area"),
    "unit_symbol": bilingual("Unidad geológica", "Geological unit"),
    "description": bilingual("Litología del mapa", "Map lithology"),
    "geological_age": bilingual("Edad geológica del mapa", "Map geological age"),
    "annual_avg_2cm_mean_k": bilingual("Temperatura anual media a 2 cm", "Mean annual temperature at 2 cm"),
    "annual_max_surface_mean_k": bilingual("Media regional de máximas superficiales anuales", "Regional mean of annual surface maxima"),
    "ice_surface_stable_model_area_pct": bilingual("Área de estabilidad superficial modelada de hielo", "Modeled surface ice stability area"),
    "brightness_scene_mean_k": bilingual("Temperatura de brillo media de escenas", "Mean scene brightness temperature"),
    "ti_day_mean_tiu": bilingual("Inercia térmica TES diurna", "TES daytime thermal inertia"),
    "ti_night_mean_tiu": bilingual("Inercia térmica TES nocturna", "TES nighttime thermal inertia"),
    "parameter_mean": bilingual("Media del indicador espectral", "Mean spectral indicator"),
    "quality_status": bilingual("Estado de calidad", "Quality status"),
    "status": bilingual("Estado", "Status"),
    "summary_status": bilingual("Estado del resumen", "Summary status"),
}

SPANISH_WORDS = dict(zip(
    "mean std median min max slope elevation relief terrain flat moderate steep valid coverage observations accepted rejected matched no raw scene scenes count region planet latitude longitude period source quality status depth fit uncertainty band pixel native annual surface temperature ice area thermal day night inertia illumination mapped unmapped overlap excess unit geological age acquisition solar wind humidity pressure wetness soil radiation start end number group parameter interpretation water snow bare ground vegetation image scale resolution range paired topography spectral mineral name detected beyond limit classified finite reported record".split(),
    "media desviación mediana mínima máxima pendiente elevación relieve terreno plano moderado escarpado válidas cobertura observaciones aceptadas rechazadas coincidencias sin originales escena escenas cantidad región cuerpo latitud longitud período fuente calidad estado profundidad ajuste incertidumbre banda píxel nativo anual superficie temperatura hielo área térmica día noche inercia iluminación cartografiada no_cartografiada superposición exceso unidad geológica edad adquisición solar viento humedad presión humedad suelo irradiación inicio fin número grupo parámetro interpretación agua nieve desnudo suelo vegetación imagen escala resolución rango emparejadas topografía espectral material nombre detectado más_allá límite clasificado finito reportado registro".split(),
))

METHOD_ES = {
    "topography": "Gradientes del DEM en metros; vecindarios completos 3×3; TRI de Riley y TPI con ocho vecinos.",
    "climate": "Agregación de series diarias NASA POWER; temperatura del aire, viento, presión, humedad e irradiación, conservando unidades originales.",
    "environment": "Agregaciones regionales GEE con QA; LST emparejada día/noche, NDVI, precipitación anual media CHIRPS y cobertura WorldCover 2021.",
    "spectral": "Mediana temporal por banda; subconjunto NDVI<0,2 cuando corresponde; índices BSI, B4/B2 y B11/B12.",
    "geology_coverage": "Intersección y unión de polígonos; se conserva el área sin cartografiar y el denominador de los porcentajes.",
    "geology": "Área por unidad geológica y porcentajes sobre la ventana o el área cartografiada, según la columna.",
    "emit_availability": "Búsqueda de gránulos en el catálogo Earthdata; disponibilidad no significa cobertura válida ni detección.",
    "emit_coverage": "Dos grupos espectrales; ajuste almacenado ≥0,20, profundidad ≥0,02 y profundidad ≥2×incertidumbre. Los bins tocados no son cobertura de área.",
    "emit_minerals": "Conteos y sumas de coincidencias aceptadas de biblioteca; ajuste corregido por ×2; no equivale a abundancia química.",
    "emit_quality": "Observaciones ausentes, rechazadas y aceptadas conservadas; no se aplicó máscara L2A de nubes ni máscara marina.",
    "emit_scene_matches": "Coincidencias aceptadas de biblioteca por adquisición y grupo espectral, sin fusionar su significado con concentración.",
    "tes": "Media y dispersión ponderadas por intersección de celdas nativas; se excluyen píxeles interpolados; umbral exploratorio de cobertura ≥80 %.",
    "themis": "Se promedian escenas aceptadas con igual peso, separando iluminación y banda; no son pares de un ciclo diario.",
    "themis_scenes": "Escala y offset de etiqueta PDS aplicados una vez; validación de constantes, rango, geometría e iluminación.",
    "crism": "Indicadores ponderados por área; se exige ≥80 % de cobertura para observaciones primarias y se conservan ausencias explícitas.",
    "crism_quality": "Validación de etiqueta y referencia geométrica; los productos no esféricos o planetográficos incompatibles conservan su error.",
    "crism_all": "Se conservan también parámetros con cobertura insuficiente o píxeles inválidos; no se consideran observaciones primarias calificadas.",
    "diviner": "Ponderación por área de facetas nativas; temperatura anual a 2 cm separada de máxima superficial. Profundidad −32768 indica más allá de 2,8738 m del modelo.",
}

SUPPORT_ES = {
    "topography": "Malla de 200 m en la ventana propia del DEM, nominalmente 10×10 km.",
    "climate": "Cuadrícula gruesa asociada al punto NASA POWER; no es una estación de cumbre ni una media espacial de 10 km.",
    "environment": "Huella regional original GEE de aproximadamente 100 km², distinta de los límites del DEM. MODIS LST ~1 km, NDVI ~250 m, CHIRPS 0,05° y WorldCover 10 m.",
    "spectral": "Análisis a 20 m; el subconjunto de baja vegetación conserva su propia cobertura y denominador.",
    "geology_coverage": "Mapa a escala 1:500.000 intersectado con la ventana del DEM.",
    "geology": "Polígonos de cartografía 1:500.000 recortados; no son mediciones litológicas independientes a 200 m.",
    "emit_availability": "Intersección de catálogo; no representa cobertura válida de superficie.",
    "emit_coverage": "Centros de píxeles nativos en la ventana; bins de 200 m usados solo como diagnóstico.",
    "emit_minerals": "Observaciones nativas de ~60 m agrupadas entre adquisiciones seleccionadas; pueden repetirse ubicaciones.",
    "emit_quality": "Observaciones nativas y diagnóstico de bins tocados por sus centros.",
    "emit_scene_matches": "Observaciones nativas dentro de la huella regional original.",
    "tes": "Celdas nativas de 0,05°; cuadrado LAEA nominal de 100 km² sobre la esfera TES de radio 3.396 km.",
    "themis": "Píxeles nativos y medias de escenas con igual peso; adquisiciones no emparejadas.",
    "themis_scenes": "Píxeles proyectados nativos y cobertura de área válida por escena.",
    "crism": "Celdas CRISM nativas intersectadas con la huella del DEM; resolución dependiente del producto.",
    "crism_quality": "Referencia proyectada nativa; los productos incompatibles se rechazan de forma conservadora.",
    "crism_all": "Celdas nativas del producto; se incluyen observaciones sin calificación primaria.",
    "diviner": "Facetas triangulares nativas; intersección de área horizontal equivalente con la ventana LOLA.",
}

DEFINITIONS = {
    "elevation_mean_m": bilingual("Media de elevaciones válidas respecto al datum vertical del DEM de ese cuerpo.", "Mean valid elevation relative to that body's DEM vertical datum."),
    "elevation_std_m": bilingual("Desviación estándar poblacional de elevaciones válidas (ddof=0).", "Population standard deviation of valid elevations (ddof=0)."),
    "relief_p90_p10_m": bilingual("Percentil 90 menos percentil 10 de las elevaciones válidas.", "90th minus 10th percentile of valid elevations."),
    "local_relief_m": bilingual("Elevación máxima menos mínima; sensible a valores extremos.", "Maximum minus minimum elevation; sensitive to extremes."),
    "slope_mean_deg": bilingual("Media de atan(sqrt(gx²+gy²)) en grados, con derivadas sobre malla métrica y vecindarios completos.", "Mean atan(sqrt(gx²+gy²)) in degrees, using metric-grid derivatives and complete neighborhoods."),
    "tri_mean_m": bilingual("Media de sqrt(sum((z_vecino−z_centro)²)) con ocho vecinos. No es la desviación local de alturas del comparador global.", "Mean sqrt(sum((z_neighbor−z_center)²)) over eight neighbors. Not the global comparator's local height standard deviation."),
    "tpi_std_m": bilingual("Desviación estándar de z_centro−media(z_ocho_vecinos).", "Standard deviation of z_center−mean(z_eight_neighbors)."),
    "lst_day_mean_c": bilingual("Temperatura radiométrica superficial diurna MODIS con cielo despejado; no es temperatura del aire ni máxima diaria.", "Clear-sky MODIS daytime radiometric surface temperature; neither air temperature nor the daily maximum."),
    "lst_night_mean_c": bilingual("Temperatura radiométrica superficial nocturna MODIS; no es temperatura del aire ni mínima diaria.", "MODIS nighttime radiometric surface temperature; neither air temperature nor the daily minimum."),
    "thermal_range_mean_c": bilingual("Media de diferencias LST día−noche de pares válidos; no es resta de medias marginales ni máximo−mínimo global.", "Mean daytime−nighttime LST differences for valid pairs; not the difference of marginal means or the global maximum−minimum."),
    "air_temperature_mean_c": bilingual("Temperatura media del aire a 2 m en la cuadrícula NASA POWER; diferente de LST.", "Mean air temperature at 2 m in the NASA POWER grid; distinct from LST."),
    "annual_precipitation_mm": bilingual("Suma de lluvia diaria CHIRPS 2021–2025 dividida por cinco; media anual de la huella regional.", "Sum of daily CHIRPS precipitation for 2021–2025 divided by five; regional-footprint annual mean."),
    "solar_radiation_daily_mean": bilingual("Energía solar por área y día, promediada sobre días. No es irradiancia instantánea ni producción fotovoltaica.", "Solar energy per area per day, averaged over days. Neither instantaneous irradiance nor photovoltaic production."),
    "detection_pct_of_valid_observations": bilingual("100×conteo de coincidencias aceptadas de esta entrada / observaciones válidas. No es concentración ni porcentaje de área exclusiva.", "100×accepted matches for this library entry / valid observations. Neither concentration nor an exclusive area fraction."),
    "ti_day_mean_tiu": bilingual("Media diurna ponderada del producto de inercia térmica TES; I=sqrt(kρc), no temperatura.", "Weighted mean of daytime TES thermal inertia; I=sqrt(kρc), not temperature."),
    "ti_night_mean_tiu": bilingual("Media nocturna ponderada del producto de inercia térmica TES; no es temperatura nocturna.", "Weighted mean of nighttime TES thermal inertia; not nighttime temperature."),
    "annual_avg_2cm_mean_k": bilingual("Media regional ponderada de la temperatura anual media modelada a 2 cm.", "Area-weighted regional mean of modeled annual mean temperature at 2 cm."),
    "annual_max_surface_mean_k": bilingual("Media regional de máximas superficiales anuales modeladas; no es el máximo absoluto regional ni la media a 2 cm.", "Regional mean of modeled annual surface maxima; neither the absolute regional maximum nor the mean at 2 cm."),
    "ice_surface_stable_model_area_pct": bilingual("Fracción de ventana donde el modelo permite estabilidad de hielo en superficie; no demuestra presencia de hielo.", "Window fraction where the model allows stable surface ice; not evidence of ice presence."),
    "brightness_scene_mean_k": bilingual("Media de temperaturas de brillo de escenas aceptadas, con igual peso; banda sin verificar y fechas no emparejadas.", "Equally weighted mean brightness temperatures from accepted scenes; unverified band and unpaired dates."),
    "parameter_mean": bilingual("Media ponderada por área de un parámetro espectral CRISM; interpretación específica del parámetro, no concentración química.", "Area-weighted mean of a CRISM spectral parameter; parameter-specific interpretation, not chemical concentration."),
}

QUALITY_REFERENCES = {
    "topography": "valid_coverage_pct (minimum 90%); complete 3×3 neighborhoods; unmasked marine cells remain valid elevations",
    "climate": "valid_observations_pct; original daily series (1,826 days); coarse-grid representativeness",
    "environment": "LST observation/paired counts; water_pct; original GEE QA; class-specific denominators",
    "spectral": "spectral_coverage_pct; low_vegetation_valid_pct; image_count; original SCL and minimum-observation rules",
    "geology_coverage": "mapped_pct; unmapped_pct; overlap_excess_km2; map scale 1:500,000",
    "geology": "geological_coverage.csv; pct_study_area versus pct_mapped_area; map-scale limitation",
    "emit_availability": "catalogue availability only; mineralogical_scene_quality.csv controls actual observation validity",
    "emit_coverage": "status; scenes_with_valid_observations; accepted_pct_of_valid_observations; bin counts are not area coverage",
    "emit_minerals": "status provisional/partial_provisional; depth/fit/uncertainty filters; no cloud/marine masks",
    "emit_quality": "status; accepted/rejected counts; l2a_cloud_mask_applied; marine_mask_applied",
    "emit_scene_matches": "mineralogical_scene_quality.csv for the same region, scene and spectral group",
    "tes": "ti_day/night_valid_area_pct; coverage_flag; interpolation masks excluded; threshold 80%",
    "themis": "summary_status=pilot_band_unverified; accepted_scene_count; minimum_scene_valid_area_pct",
    "themis_scenes": "quality_status; band_group; illumination_disagreement; valid_area_pct",
    "crism": "quality_status; valid_area_pct; >=80% primary threshold; unavailable rows retained",
    "crism_quality": "status and error; conservative CRS rejection for Phoenix",
    "crism_all": "quality_status; low_coverage and no_valid_pixels are not primary qualified results",
    "diviner": "thermal_quality_status; mesh/temperature/depth coverage; co-registration assumption; model not ice detection",
}


def field_metadata(section, column, source_ids):
    """Explicit namespaces and physical metadata: no implicit global aliasing."""
    _, _, _, support, period, method, compatibility = SECTION_SPECS[section]
    unit = ""
    if "_pct" in column or column.startswith("pct_"):
        unit = "%"
    elif column.endswith("_tiu"):
        unit = "J m⁻² K⁻¹ s⁻¹/²"
    elif column.endswith("_kpa"):
        unit = "kPa"
    elif column.endswith("_ms"):
        unit = "m/s"
    elif column.endswith("_deg"):
        unit = "°"
    elif column.endswith("_km2"):
        unit = "km²"
    elif column.endswith("_m"):
        unit = "m"
    elif column.endswith("_k"):
        unit = "K"
    elif column.endswith("_c"):
        unit = "°C"
    elif column.endswith("_um"):
        unit = "µm"
    if column in {"latitude", "longitude", "longitude_east"}:
        unit = "°"
    if column == "annual_precipitation_mm":
        unit = "mm/año"  # original physical definition, not a unit conversion
    if column == "solar_radiation_daily_mean":
        unit = "kWh/m²/day"
    sources = source_ids
    if section == "environment":
        if column.startswith(("lst_", "thermal_range", "paired_")):
            sources, support = ["modis_lst"], "MOD11A1 ~1 km; original GEE regional footprint"
        elif column == "ndvi_mean":
            sources, support = ["modis_ndvi"], "MOD13Q1 ~250 m; original GEE regional footprint"
        elif column == "annual_precipitation_mm":
            sources, support = ["chirps"], "CHIRPS 0.05°; original GEE regional footprint"
        elif column.endswith("_pct") or column == "landcover_year":
            sources, support, period = ["worldcover"], "WorldCover 10 m; original GEE regional footprint", "2021"
    suffixes = {"m", "c", "k", "deg", "pct", "tiu", "kpa", "ms", "km2"}
    words = [w for w in column.split("_") if w not in suffixes]
    label = LABELS.get(column, bilingual(" ".join(SPANISH_WORDS.get(w, w) for w in words).capitalize(), " ".join(words).capitalize()))
    counterpart, reason = GLOBAL_COUNTERPARTS.get(column, (None, compatibility))
    if section != "topography" and column in {"latitude", "longitude"}:
        reason = "source_geometry_metadata_not_a_score_variable"
    return {
        "id": column, "app_field": f"{section}.{column}", "original_column": column,
        "label": label, "unit": unit, "source_ids": sources,
        "spatial_support": support, "period": period, "method": method,
        "definition": DEFINITIONS.get(column, label), "global_candidate": counterpart, "compatibility": reason,
        "method_text": bilingual(METHOD_ES[section], method),
        "support_text": bilingual(SUPPORT_ES[section], support),
        "compatibility_text": bilingual("Se conserva como observación regional independiente; no reemplaza automáticamente ninguna variable de una celda global.", "Retained as a separate regional observation; does not automatically replace any global cell feature."),
        "conversion": "none; original value retained",
        "quality_reference": QUALITY_REFERENCES[section],
    }
