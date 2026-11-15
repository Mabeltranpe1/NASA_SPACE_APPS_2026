# GeoAnalog — contexto técnico, resultados y plan de continuidad

**Documento de transferencia para un agente de IA y el equipo de desarrollo**  
**Fecha de corte:** 14 de noviembre de 2026  
**Estado:** prototipo científico funcional en topografía; caracterización terrestre ampliada; mineralogía y validación pendientes.  
**Idioma de trabajo:** español. Mantener los identificadores de código y los nombres de archivos en inglés tal como se indican.

> Este documento resume el trabajo efectuado en la conversación del proyecto. No sustituye los archivos originales, no contiene los scripts locales completos ni certifica una validación científica independiente. Los datos numéricos incluidos proceden de las salidas y CSV compartidos por el responsable; las propuestas futuras se identifican como tales. Antes de cambiar el código, inspeccionar la versión existente del repositorio y sus resultados.

## 0. Instrucciones de continuidad para otra IA

- El usuario es responsable de los datasets y de la metodología científica. Sus compañeros desarrollan la aplicación web y un globo terrestre interactivo que muestra ubicaciones y fichas al hacer clic. No asumir que hay que rehacer la interfaz o cambiar su stack.
- Continuar desde el estado real: **ya se realizó la búsqueda de escenas EMIT; la descarga y el procesamiento mineralógico no están confirmados**. El script de descarga se proporcionó, pero aún no se recibió evidencia de su ejecución.
- No pedir que se vuelvan a descargar los DEM, reconstruir los CSV ya producidos ni repetir tareas finalizadas sin una razón concreta (control de calidad, cambio de geometría o fallo reproducible).
- El proyecto se ejecuta en Windows con PowerShell, VS Code y Python dentro de `.venv`. Entregar pasos concretos, comandos de PowerShell y, cuando se solicite código, preferiblemente un script completo copiable con nombre y ruta exactos.
- Conservar los IDs, unidades, coordenadas, metadatos, procedencia, intervalos temporales, criterios de calidad y versión del algoritmo. Separar resultados observados, hipótesis, decisiones provisionales y propuestas.
- No inventar resultados de una API, disponibilidad, detecciones minerales ni climatología que no se hayan inspeccionado. No equiparar ausencia de datos con valor cero.
- No confundir semejanza topográfica con equivalencia física, habitabilidad, seguridad, capacidad de construcción o aprobación de un lugar por una agencia espacial.
- Prioridad práctica: producir un conjunto de datos utilizable por el equipo web cuanto antes, en paralelo con completar y validar la ciencia. Un producto complementario no debe impedir entregar la versión topográfica inicial.

## 1. Objetivo y alcance

GeoAnalog es un proyecto del contexto de NASA Space Apps, en el reto de identificar ubicaciones terrestres análogas a regiones candidatas para bases lunares y lugares marcianos (título trabajado: *Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars*). El enfoque del equipo es Colombia.

**Pregunta actual:** ¿qué regiones colombianas, de un conjunto inicial seleccionado, se parecen cuantitativamente a determinadas zonas de Marte y del polo sur lunar en términos topográficos, y qué propiedades ambientales, espectrales y geológicas permiten caracterizarlas como lugares de ensayo?

**Diferencial:** comparar variables físicas obtenidas de observación remota, en vez de depender de la similitud visual de fotografías.

Alcance actual:

- Seis candidatos terrestres escogidos previamente; seis regiones marcianas de aterrizaje y seis zonas lunares de interés.
- Comparaciones topográficas cuantitativas entre los candidatos y objetivos extraterrestres.
- Caracterización ambiental, climática y espectral terrestre como capas adicionales de información.
- En una fase posterior, evaluación mineralógica y características térmicas extraterrestres con datos compatibles.
- Integración de resultados en el globo terrestre interactivo y fichas científicas.

**No se ha desarrollado todavía una búsqueda automática de todos los lugares de Colombia ni del mundo.** El ranking solo identifica los mejores candidatos *dentro de las seis ventanas seleccionadas*. Tampoco se ha demostrado que las ventanas lunares correspondan a ubicaciones aprobadas para una base permanente; verificar denominación y georreferenciación con sus fuentes oficiales.

## 2. Inventario de regiones e identificadores canónicos

Formato de ID para uniones: `planet + '_' + region`. Mantener mayúsculas, guiones bajos y nombres exactos. Coordenadas terrestres en grados decimales WGS84; latitud norte positiva, longitud este positiva; GeoJSON utiliza `[longitude, latitude]`.

### 2.1 Tierra (`earth`)

| region | Nombre de presentación | Latitud | Longitud | CRS UTM utilizado |
|---|---|---:|---:|---|
| Tatacoa | Desierto de la Tatacoa, Huila | 3.2300 | -75.1700 | EPSG:32618 |
| La_Guajira | La Guajira, sector de dunas de Taroa | 12.43653 | -71.60899 | EPSG:32619 |
| Nevado_del_Ruiz | Nevado del Ruiz | 4.8950 | -75.3220 | EPSG:32618 |
| Volcan_Purace | Volcán Puracé | 2.3095 | -76.3948 | EPSG:32618 |
| La_Candelaria | Desierto de la Candelaria, Boyacá | 5.5368 | -73.6163 | EPSG:32618 |
| Nevado_Santa_Isabel | Nevado Santa Isabel | 4.8180 | -75.3650 | EPSG:32618 |

Estos son los puntos usados por los scripts, no límites administrativos ni coordenadas certificadas de las cumbres. La Guajira es costera: posible inclusión considerable de océano. Validar también que las demás ventanas correspondan exactamente al lugar anunciado en la web.

### 2.2 Marte (`mars`)

| region | Contexto | Latitud usada | Longitud este usada (0–360°) |
|---|---|---:|---:|
| Jezero | Perseverance | 18.4447 | 77.4508 |
| Gale | Curiosity | -4.59 | 137.44 |
| Phoenix | Phoenix | 68.22 | 234.25 |
| Pathfinder | Mars Pathfinder / Sojourner, Ares Vallis | 19.095 | 326.747 |
| Viking_1 | Viking 1 | 22.269 | 312.049 |
| Viking_2 | Viking 2 | 47.668 | 134.28 |

Coordenadas de trabajo de los scripts iniciales. Revisar `process_planetary.py` y las fuentes de aterrizaje para confirmar si corresponde a latitud planetocéntrica o planetográfica, longitud positiva al este, datum y centro real de salida. No usar EPSG:4326 terrestre para los datos marcianos.

### 2.3 Luna (`moon`)

| region | Archivo LOLA asociado según la selección inicial (por verificar) |
|---|---|
| Connecting_Ridge | Site01_final_adj_5mpp_surf.tif |
| Shackleton_Rim | Site04_final_adj_5mpp_surf.tif |
| Peak_Near_Shackleton | Site07_final_adj_5mpp_surf.tif |
| De_Gerlache_Rim | Site11_final_adj_5mpp_surf.tif |
| Leibnitz_Beta_Plateau | Site20_final_adj_5mpp_surf.tif |
| Malapert_Massif | Site23_final_adj_5mpp_surf.tif |

Las coordenadas centrales lunares exactas no se han incorporado al documento porque no se compartieron. Derivarlas de cada DEM y confirmar con la documentación de NASA, sin inventarlas. Se usó el centro de los archivos lunares en el procesamiento propuesto. El CRS observado es estereográfico polar sur (origen -90°, meridiano central 0°, esfera de radio 1 737 400 m).

## 3. Entorno, dependencias y estructura del repositorio

Ruta observada: `C:\Users\santi\Desktop\SpaceApps`.

Python reportado originalmente: 3.14.6. Verificar la versión efectiva y compatibilidad de las dependencias antes de instalar o cambiar el entorno. No crear otro entorno sin necesidad.

```powershell
cd C:\Users\santi\Desktop\SpaceApps
.\.venv\Scripts\Activate.ps1
python --version
python -m pip --version
```

Paquetes que se indicaron/emplearon: `numpy`, `pandas`, `rasterio`, `matplotlib`, `scipy`, `scikit-learn`, `pyproj`, `requests`, `earthaccess`, `xarray`, `netCDF4`. Si falta alguno usar `python -m pip install <paquete>`. Capturar versiones reales con `python -m pip freeze` antes de congelar dependencias. Una captura muestra `requirements.txt.txt`: comprobar si la extensión doble es accidental.

Incidencia ya resuelta: PowerShell mostró `AmpersandNotAllowed` porque el comando manual se concatenó con el comando `& '...python.exe'` de VS Code. Ejecutar solo un comando a la vez, guardar el archivo (`Ctrl+S`) antes de correrlo, y no pulsar simultáneamente Run Python. La invocación directa también funciona: `.\.venv\Scripts\python.exe src/process_planetary.py`.

```text
SpaceApps/
├── .venv/                           # local, no compartir
├── data/
│   ├── raw/
│   │   ├── earth/                   # DEM originales de Google Earth Engine
│   │   ├── mars/                    # DEM global MOLA/HRSC
│   │   ├── moon/                    # DEM LOLA polares
│   │   ├── climate/                 # series NASA POWER, según script
│   │   └── emit/                    # previsto: NetCDF por región
│   ├── processed/
│   │   ├── earth/                   # *_DEM_200m.tif
│   │   ├── mars/
│   │   └── moon/
│   ├── features/
│   │   ├── planetary_features.csv
│   │   ├── environmental_features.csv
│   │   ├── climate_features.csv
│   │   ├── spectral_features.csv
│   │   ├── emit_availability.csv
│   │   ├── emit_downloads.csv       # pendiente de confirmar
│   │   └── mineralogical_features.csv # pendiente
│   ├── figures/                     # *_analysis.png por planeta y región
│   └── results/
│       ├── analog_ranking.csv
│       ├── similarity_matrix.csv
│       ├── similarity_matrix.png
│       ├── normalized_features.csv
│       └── normalization_parameters.csv
├── src/
│   ├── resample.py
│   ├── visualize.py
│   ├── process_planetary.py
│   ├── extract_features.py
│   ├── similarity.py
│   ├── extract_climate.py
│   ├── search_emit.py
│   ├── download_emit.py            # entregado como código, ejecución no confirmada
│   ├── inspect_emit.py             # propuesto
│   ├── process_emit.py             # propuesto
│   └── build_web_dataset.py       # propuesto
└── requirements.txt                # nombre objetivo, verificar local
```

Los scripts de GEE se trabajaron en el editor web: `GeoAnalog_Environmental`, `GeoAnalog_Spectral` y script anterior de exportación de topografía. Conviene guardar copias `.js` versionadas en el repositorio, por ejemplo `gee/` (propuesta). No almacenar credenciales Earthdata, `.netrc`, `.env`, `.venv`, archivos temporales ni DEM globales grandes en Git.

## 4. Estado y fuentes de adquisición

| Producto | Información | Resolución nominal / escala | Estado real |
|---|---|---|---|
| NASADEM HGT | DEM terrestre | ~30 m | Procesado, CSV compartido |
| HRSC/MOLA Blend v2 (USGS) | DEM de Marte | ~200 m nominal, variable efectiva | Procesado, CSV compartido |
| LOLA polar south DEM | DEM lunar | 5 m nominal | Procesado, CSV compartido |
| MODIS MOD11A1 v061 | LST día/noche | ~1 km | Exportado; CSV visto parcialmente |
| MODIS MOD13Q1 v061 | NDVI | ~250 m | Exportado; valores completos no vistos |
| ESA WorldCover v200 | Clases del terreno | 10 m, 2021 | Exportado; CSV visto parcialmente |
| CHIRPS Daily | Precipitación | 0.05° (~5.5 km) | Exportado; CSV visto parcialmente |
| NASA POWER | Clima y energía solar | Cuadrícula gruesa, depende de variable | Usuario dijo que terminó; CSV no inspeccionado |
| Sentinel-2 L2A harmonized | Reflectancia e índices | 10–20 m bandas empleadas, análisis 20 m | CSV completo compartido |
| EMITL2BMIN v001 | Identificación mineralógica | ~60 m | Disponibilidad confirmada, descarga no confirmada |
| SGC | Geología de Colombia | Variable según mapa | Pendiente |
| THEMIS / Diviner | Variables térmicas de Marte / Luna | Depende del producto | Pendiente |
| CRISM / M³ | Espectros y/o mapas mineralógicos extraterrestres | Depende del producto | Pendiente |

Fuentes de referencia y acceso (rutas usadas o propuestas durante el proyecto; volver a verificar disponibilidad, versión, licencia y documentación antes de una nueva descarga):

- NASADEM GEE: https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001 — ID `NASA/NASADEM_HGT/001`.
- Marte USGS: https://astrogeology.usgs.gov/search/map/mars_mgs_mola_mex_hrsc_blended_dem_global_200m — archivo propuesto `Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif`, URL usada: https://planetarymaps.usgs.gov/mosaic/Mars/HRSC_MOLA_Blend/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif .
- Luna LOLA: https://pgda.gsfc.nasa.gov/products/78 y https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/ .
- GEE Code Editor: https://code.earthengine.google.com/ .
- MOD11A1: https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD11A1 .
- MOD13Q1: https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1 .
- WorldCover: https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v200 .
- CHIRPS: https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY .
- NASA POWER: https://power.larc.nasa.gov/ ; API: https://power.larc.nasa.gov/api/temporal/daily/point .
- Sentinel-2: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED .
- EMIT: https://earth.jpl.nasa.gov/emit/ ; DOI L2B mineralogía: https://doi.org/10.5067/EMIT/EMITL2BMIN.001 ; búsqueda: https://search.earthdata.nasa.gov/ ; login: https://urs.earthdata.nasa.gov/ ; tutorial: https://nasa.github.io/LPDAAC-Data-Resources/external/Working_with_EMIT_L2B_Mineralogy.html .
- SGC: https://www2.sgc.gov.co/ .
- Repositorio planetario de NASA (para investigación futura): https://pds.nasa.gov/ .

## 5. Topografía: metodología implementada

### 5.1 Adquisición y homogeneización

1. En Google Earth Engine se exportó la banda `elevation` de NASADEM, a 30 m, para las seis ubicaciones. Se definió el área mediante un buffer de 5000 m y su rectángulo envolvente; para la mayoría se usó `punto.buffer(5000).bounds(ee.ErrorMargin(1), ee.Projection(crs))`. Exportación GeoTIFF, float32, NoData -9999, carpeta de Drive `GeoAnalog`.
2. `resample.py`: lee los DEM terrestres desde `data/raw/earth/`, reproyecta/remuestrea por promedio (`rasterio.warp.reproject`, `Resampling.average`) a un rectángulo nominal de 10 000 m × 10 000 m centrado en las extensiones originales, 200 m de tamaño de píxel, 50 × 50, float32; guarda en `data/processed/earth/`.
3. `process_planetary.py`: aplica una estrategia semejante para Marte y Luna; en Marte se propuso CRS local azimutal equidistante, elipsoide del DEM fuente y ajuste de longitud; en la Luna se mantiene la proyección métrica polar. Usa lectura por banda para no cargar el DEM marciano global completo (~11 GB referido). Validar el código real para comprobar las transformaciones, factores de escala y georreferenciación.
4. `visualize.py` permite comprobar la comparación gráfica y el remuestreo.

Resultados confirmados por terminal: seis DEM lunares (fuente 5 m; NoData NaN; escala 1, offset 0) y seis marcianos (fuente `ESRI:104971`, resolución angular `0.003374120830641°`, NoData -32768, escala 1, offset 0) procesados a 50×50, 200 m y 100 % de cobertura válida. Los seis terrestres también figuran con 100 % en el CSV. Se obtuvieron 18 × 2500 = 45 000 celdas de elevación en total; esto no significa 45 000 mediciones independientes.

El área objetivo es nominalmente 100 km² en coordenadas proyectadas; las regiones GEE usadas para otros indicadores tienen áreas de ~99.4–99.5 km², por lo que no se garantiza coincidencia exacta de los polígonos. El CRS de origen marciano está en grados y su paso angular no debe interpretarse como metros. Reproyectar a 200 m no aumenta la resolución instrumental. Los niveles de referencia vertical difieren entre cuerpos; elevaciones negativas extraterrestres no implican agua ni error.

### 5.2 Extracción de propiedades

`extract_features.py` recorre `data/processed/{earth,mars,moon}/*.tif`. Lee máscaras de NoData, representa ausencias con NaN, comprueba CRS métrico, resolución y cobertura mínima del 90 % según diseño. Calcula derivadas y vecindad 3×3; excluye bordes o vecindades incompletas para indicadores que lo requieren. El CSV observado contiene 18 filas y 25 columnas.

Fórmulas y significado (revisar implementación exacta antes de modificar):

- Elevación relativa: `z_rel = z - mean(z)`.
- Relieve local de la ventana: `max(z) - min(z)`; sensible a valores extremos.
- Relieve robusto: `P90(z) - P10(z)`; menos sensible a extremos.
- Pendiente en grados: `atan(sqrt(gx² + gy²)) * 180/pi`, derivadas horizontales sobre la malla métrica.
- TRI de Riley: `sqrt(sum((z_vecino - z_centro)²))`, ocho vecinos. No es intercambiable con otras variantes de TRI sin recalcular.
- TPI: `z_centro - mean(z_8_vecinos)`; positivo respecto a su entorno y negativo en depresiones locales.
- Orientación (aspect): se propuso `(degrees(arctan2(-gx, gy)) + 360) % 360` con eje y de las filas; comprobar signos, norte de cuadrícula y tratamiento de superficies planas antes de utilizarla científicamente.
- Clasificación de pendientes prevista: plana <5°, moderada 5–15°, escarpada ≥15° (verificar umbrales exactos/inclusión de extremos en el script).

Cada figura presenta seis paneles: elevación, elevación relativa, pendiente, TRI, TPI y aspecto. Los indicadores de pendiente, TRI y TPI dependen de escala, vecindad y resolución efectiva; no deben compararse con estadísticas de otra escala sin armonización.

### 5.3 Diccionario de `planetary_features.csv`

| Columna | Unidad / descripción |
|---|---|
| region | ID local exacto |
| planet | earth, mars o moon |
| resolution_m | tamaño de celda en m (200) |
| valid_coverage_pct | porcentaje de píxeles de elevación válidos; no equivale a porcentaje de tierra firme |
| elevation_min_m | m, mínimo |
| elevation_max_m | m, máximo |
| elevation_mean_m | m, media |
| elevation_median_m | m, mediana |
| elevation_std_m | m, desviación estándar |
| local_relief_m | m, máximo menos mínimo |
| relief_p90_p10_m | m, P90 menos P10 |
| slope_mean_deg | grados, pendiente media |
| slope_median_deg | grados, mediana |
| slope_std_deg | grados, desviación estándar |
| slope_max_deg | grados, máxima |
| slope_p90_deg | grados, P90 |
| flat_terrain_pct | % de terreno plano entre celdas consideradas |
| moderate_terrain_pct | % de terreno moderado |
| steep_terrain_pct | % de terreno escarpado |
| tri_mean_m | m, TRI promedio |
| tri_std_m | m, desviación estándar TRI |
| tri_p90_m | m, P90 TRI |
| tpi_mean_m | m, TPI promedio |
| tpi_std_m | m, desviación estándar TPI |
| tpi_abs_mean_m | m, media de valor absoluto TPI |

### 5.4 Resultados físicos principales observados

Todos provienen del CSV pegado por el usuario; redondeados. El archivo original conserva mayor precisión.

| Planeta | Región | Elevación media (m) | Relieve local (m) | Pendiente media (°) | TRI medio (m) | Plano (%) |
|---|---|---:|---:|---:|---:|---:|
| earth | La_Candelaria | 2366.85 | 759.94 | 9.58 | 92.99 | 12.72 |
| earth | La_Guajira | 10.64 | 63.54 | 0.66 | 7.38 | 99.74 |
| earth | Nevado_del_Ruiz | 4466.84 | 1762.20 | 16.75 | 163.49 | 3.04 |
| earth | Nevado_Santa_Isabel | 4327.70 | 1387.82 | 13.70 | 136.66 | 7.86 |
| earth | Tatacoa | 433.04 | 137.48 | 2.18 | 22.56 | 95.31 |
| earth | Volcan_Purace | 3937.52 | 1467.14 | 12.99 | 125.66 | 7.12 |
| mars | Gale | -4464.11 | 431.99 | 2.17 | 19.95 | 90.15 |
| mars | Jezero | -2547.16 | 279.44 | 2.15 | 20.22 | 96.96 |
| mars | Pathfinder | -3680.34 | 282.84 | 1.87 | 18.21 | 94.44 |
| mars | Phoenix | -4120.57 | 93.21 | 0.61 | 5.45 | 100.00 |
| mars | Viking_1 | -3632.80 | 39.08 | 0.34 | 3.01 | 100.00 |
| mars | Viking_2 | -4512.22 | 133.12 | 2.09 | 19.29 | 98.44 |
| moon | Connecting_Ridge | 1404.19 | 1428.36 | 10.57 | 94.68 | 14.41 |
| moon | De_Gerlache_Rim | 1033.29 | 2014.03 | 15.07 | 134.89 | 3.65 |
| moon | Leibnitz_Beta_Plateau | 5963.67 | 2130.93 | 11.69 | 104.54 | 9.68 |
| moon | Malapert_Massif | 4388.16 | 2013.40 | 15.91 | 142.68 | 4.82 |
| moon | Peak_Near_Shackleton | 1124.82 | 1255.68 | 10.49 | 92.74 | 12.85 |
| moon | Shackleton_Rim | 448.49 | 3929.85 | 23.97 | 225.83 | 2.04 |

Aplicaciones potenciales: evaluación de pendientes, selección preliminar de ventanas para movilidad de rovers, planificación de ensayos de navegación y caracterización geomorfológica a escala regional. Una cuadrícula de 200 m **no** resuelve rocas, obstáculos, taludes pequeños, capacidad portante ni condiciones de aterrizaje a escala de rover.

## 6. Planetary Analog Index (PAI): modelo experimental

`similarity.py` utiliza únicamente seis características topográficas. No incorpora todavía clima, reflectancia, minerales ni temperatura. El nombre PAI es interno de GeoAnalog, no una métrica oficial de NASA.

### 6.1 Variables y pesos iniciales

| Variable | Peso |
|---|---:|
| relief_p90_p10_m | 0.15 |
| elevation_std_m | 0.15 |
| slope_mean_deg | 0.15 |
| slope_p90_deg | 0.15 |
| tri_mean_m | 0.15 |
| tpi_std_m | 0.25 |

Normalización por variable usando las seis regiones de Tierra como referencia común:

```text
z_j(x) = (x_j - mu_earth,j) / sigma_earth,j
D(T,P) = sqrt(sum_j(w_j * (z_j(T)-z_j(P))^2) / sum_j(w_j))
PAI(T,P) = 100 / (1 + D(T,P))
```

Para variables constantes, excluirlas y volver a normalizar pesos, según el diseño inicial. Aquí `sigma` poblacional (`ddof=0`) reproduce el par de comprobación Tatacoa–Pathfinder con los datos publicados: D=0.0867062173 y PAI=92.02119065. Verificación aritmética realizada al elaborar este documento: las 72 puntuaciones de la matriz de la sección 6.2 se reproducen a dos decimales a partir del anexo 16. No se reejecutó el script local ni el procesamiento de los DEM. Confirmar los parámetros reales en `normalization_parameters.csv`.

El índice tiene máximo 100 cuando los vectores considerados son idénticos; tiende a cero al crecer la distancia. Es un puntaje transformado, no una probabilidad ni un porcentaje calibrado de similitud. No etiquetar valores absolutos como alto/bajo con umbrales arbitrarios sin validar. Se excluyó elevación absoluta porque los datums planetarios son diferentes. Los pesos son exploratorios y varias variables están correlacionadas.

### 6.2 Matriz real de 72 comparaciones PAI (redondeo a dos decimales)

Cada fila corresponde a un objetivo extraterrestre; columnas son candidatos de Colombia. El ranking original guarda `target,candidate,distance,PAI`, ordenado por objetivo y mejor puntuación. No confundir el archivo de ranking (72 filas) con la matriz global (prevista de 18×18; comprobar archivo local).

| Objetivo | Tatacoa | La Guajira | La Candelaria | Puracé | Santa Isabel | Nevado del Ruiz |
|---|---:|---:|---:|---:|---:|---:|
| mars_Gale | 84.16 | 80.28 | 45.39 | 35.15 | 33.44 | 28.96 |
| mars_Jezero | 83.88 | 79.33 | 45.73 | 35.44 | 33.66 | 29.16 |
| mars_Pathfinder | 92.02 | 85.95 | 44.64 | 34.41 | 32.97 | 28.43 |
| mars_Phoenix | 74.49 | 87.62 | 40.59 | 32.20 | 30.75 | 26.93 |
| mars_Viking_1 | 72.32 | 86.50 | 39.62 | 31.51 | 30.17 | 26.44 |
| mars_Viking_2 | 85.69 | 87.14 | 43.80 | 34.00 | 32.50 | 28.17 |
| moon_Connecting_Ridge | 40.78 | 38.06 | 55.96 | 54.69 | 48.13 | 43.65 |
| moon_De_Gerlache_Rim | 31.31 | 29.76 | 41.43 | 48.64 | 43.86 | 46.62 |
| moon_Leibnitz_Beta_Plateau | 37.67 | 35.40 | 51.08 | 53.55 | 47.35 | 44.64 |
| moon_Malapert_Massif | 30.27 | 28.84 | 39.60 | 46.53 | 42.29 | 45.68 |
| moon_Peak_Near_Shackleton | 41.43 | 38.80 | 53.82 | 51.24 | 45.45 | 41.48 |
| moon_Shackleton_Rim | 16.91 | 16.51 | 19.57 | 22.04 | 21.48 | 24.01 |

### 6.3 Mejores candidatos terrestres por objetivo

| Objetivo | Candidato | D | PAI |
|---|---|---:|---:|
| Gale | Tatacoa | 0.18825 | 84.15752 |
| Jezero | Tatacoa | 0.19219 | 83.87904 |
| Pathfinder | Tatacoa | 0.08671 | 92.02119 |
| Phoenix | La_Guajira | 0.14125 | 87.62343 |
| Viking_1 | La_Guajira | 0.15603 | 86.50315 |
| Viking_2 | La_Guajira | 0.14762 | 87.13699 |
| Connecting_Ridge | La_Candelaria | 0.78699 | 55.95991 |
| De_Gerlache_Rim | Volcan_Purace | 1.05591 | 48.64029 |
| Leibnitz_Beta_Plateau | Volcan_Purace | 0.86753 | 53.54678 |
| Malapert_Massif | Volcan_Purace | 1.14904 | 46.53239 |
| Peak_Near_Shackleton | La_Candelaria | 0.85819 | 53.81568 |
| Shackleton_Rim | Nevado_del_Ruiz | 3.16554 | 24.00652 |

Interpretación: las seis ventanas marcianas seleccionadas se asemejan, bajo el algoritmo, a los candidatos relativamente planos Tatacoa y La Guajira; las lunares seleccionadas, a candidatos relativamente montañosos. Los máximos lunares son menores en este conjunto. No generalizar el resultado a los planetas completos: existe sesgo de selección de sitios (aterrizajes marcianos y regiones polares lunares).

Ejemplo Tatacoa–Pathfinder y contraste con Jezero:

| Variable | Tatacoa | Pathfinder | Jezero |
|---|---:|---:|---:|
| relief_p90_p10_m | 77.88781 | 38.39763 | 169.39932 |
| elevation_std_m | 29.21469 | 19.55624 | 61.59744 |
| slope_mean_deg | 2.17971 | 1.86976 | 2.14797 |
| slope_p90_deg | 3.95262 | 3.58945 | 3.82876 |
| tri_mean_m | 22.56462 | 18.20781 | 20.22453 |
| tpi_std_m | 4.75026 | 3.87670 | 2.77464 |

La coincidencia Tatacoa–Pathfinder de 92.02/100 es el máximo del estudio, pero es provisional. En particular, modificar La Guajira cambia los parámetros de normalización y potencialmente todos los scores, no solo los que incluyan La Guajira.

## 7. Caracterización ambiental terrestre (GEE)

Archivo: `data/features/environmental_features.csv`. Script: `GeoAnalog_Environmental` en Google Earth Engine. Exportación `Export.table.toDrive`, carpeta `GeoAnalog`, descarga del CSV y copia a carpeta local. El usuario mostró el archivo con seis filas en VS Code; no compartió todas las columnas y valores numéricos.

### 7.1 Configuración y metodología

- Periodo para MODIS y CHIRPS: inicio inclusivo `2021-01-01`, fin exclusivo `2026-01-01` (cinco años completos, 1826 días nominales).
- Geometría: centros de la sección 2; radio 5000 m y envolvente UTM del buffer; regiones aproximadas de 100 km². No se descargan todos los rasters ni se fuerza una cuadrícula artificial de 200 m en estas variables.
- `MODIS/061/MOD11A1`: `LST_Day_1km`, `LST_Night_1km`; máscaras `QC_Day.bitwiseAnd(3).eq(0)` y similar nocturna; escala 0.02 K por unidad y conversión `T_C = DN*0.02 - 273.15`. La diferencia día-noche se calcula por par válido en el mismo día y píxel; no restar las medias de día y noche como si tuvieran el mismo soporte temporal. Se calculan medias temporales por píxel y después medias regionales, además de recuentos medios de observaciones válidas. La LST es temperatura radiométrica de superficie en condiciones de cielo despejado y horas de paso del satélite, no máximas/mínimas diarias ni temperatura del aire. El filtro QA inicial solo comprueba bits obligatorios; ampliar análisis de calidad de error LST/emisividad si se requiere.
- `MODIS/061/MOD13Q1`: NDVI en compuestos de 16 días, `SummaryQA == 0`, escala 0.0001; media temporal y espacial. Resolución ~250 m. NDVI adimensional, `(NIR-RED)/(NIR+RED)`.
- `ESA/WorldCover/v200`: mapa de 2021, imagen inicial de colección, banda `Map`. Para cada clase se convierte `Map == clase` a 0/1, se calcula su media regional a 10 m y se multiplica por 100. Clases: 10 árboles, 20 arbustos, 30 pastizal, 40 cultivo, 50 zona construida, 60 suelo desnudo/vegetación escasa, 70 nieve/hielo, 80 agua permanente, 90 humedal herbáceo, 95 manglar, 100 musgo/líquenes. No es una serie 2021–2025. Revisar si hay píxeles sin clase y cuál es el denominador de cada porcentaje.
- `UCSB-CHG/CHIRPS/DAILY`: banda `precipitation`, suma diaria de 2021–2025 dividida por cinco para precipitación anual media, reducción regional a ~5566 m. Unidad mm/año. Verificar completitud de fechas y cobertura. No es resolución de una estación meteorológica ni mide precipitación de Marte o Luna.

### 7.2 Campos previstos en el CSV

`region`, `planet`, `latitude`, `longitude`, `area_km2`, `period_start`, `period_end_exclusive`, `lst_day_mean_c`, `lst_night_mean_c`, `thermal_range_mean_c`, `lst_day_observations_mean`, `lst_night_observations_mean`, `paired_observations_mean`, `ndvi_mean`, `annual_precipitation_mm`, `landcover_year`, `tree_cover_pct`, `shrubland_pct`, `grassland_pct`, `cropland_pct`, `built_up_pct`, `bare_ground_pct`, `snow_ice_pct`, `water_pct`, `wetland_pct`, `mangrove_pct`, `moss_lichen_pct`. GEE agrega `system:index` y `.geo`, que no son variables físicas.

### 7.3 Valores ambientales disponibles en la captura

| Región | Precipitación (mm/año) | Suelo desnudo / vegetación escasa (%) | Pastizal (%) | Área (km²) |
|---|---:|---:|---:|---:|
| Tatacoa | 1449.65 | 17.00 | 63.49 | 99.45 |
| La_Guajira | 301.96 | 28.47 | 4.51 | 99.54 |
| Nevado_del_Ruiz | 2083.35 | 52.59 | 32.12 | 99.45 |
| Volcan_Purace | 1861.20 | 14.05 | 75.30 | 99.46 |
| La_Candelaria | 1125.66 | 9.97 | 66.18 | 99.43 |
| Nevado_Santa_Isabel | 2078.44 | 13.56 | 82.38 | 99.45 |

Son datos regionales, no valores exclusivos del desierto o la cumbre. La Guajira tiene menor precipitación en esta muestra pero se requiere verificar su máscara marina. Precipitación, cobertura, NDVI y LST sirven para describir aridez relativa, vegetación, emplazamientos con suelo visible y entorno térmico. No usar directamente como distancias interplanetarias sin una definición física comparable. Solicitar o leer el CSV local para las temperaturas, NDVI MODIS, agua y demás variables no visibles. No inferir su valor desde las columnas Sentinel-2.

## 8. Climatología y energía solar (NASA POWER)

Script: `src/extract_climate.py`. El usuario indicó que terminó; no se ha inspeccionado su CSV ni confirmado que las seis consultas fueron exitosas. Revisar primero `data/features/climate_features.csv` y las series originales en `data/raw/climate/<region>_NASA_POWER.csv`.

### 8.1 Consulta

API `https://power.larc.nasa.gov/api/temporal/daily/point`, biblioteca `requests`, `community=RE`, latitud y longitud del centro, `start=20210101`, `end=20251231`, `format=JSON`, timeout de 180 segundos, espera de dos segundos entre solicitudes (diseño inicial). No requiere descargar archivos globales. El JSON contiene `properties.parameter`; leer unidades desde los metadatos reales, reemplazar `fill_value`/`-999` por NaN y guardar series diarias indexadas por fecha.

| Parámetro | Significado | Unidad prevista (verificar metadatos) |
|---|---|---|
| T2M | temperatura del aire a 2 m | °C |
| T2M_MAX | máxima diaria del aire a 2 m | °C |
| T2M_MIN | mínima diaria del aire a 2 m | °C |
| RH2M | humedad relativa a 2 m | % |
| PS | presión superficial | kPa |
| WS10M | velocidad del viento a 10 m | m/s |
| ALLSKY_SFC_SW_DWN | irradiación solar superficial diaria en todo tipo de cielo | unidad reportada por la API (usualmente kWh/m²/día en RE; verificar) |
| GWETTOP | wetness relativa del suelo superficial | adimensional; no asumir contenido volumétrico |

Campos agregados previstos:

```text
region,planet,latitude,longitude,climate_period_start,climate_period_end,
air_temperature_mean_c,air_temperature_daily_max_mean_c,
air_temperature_daily_min_mean_c,air_temperature_max_c,air_temperature_min_c,
air_thermal_range_mean_c,relative_humidity_mean_pct,surface_pressure_mean_kpa,
wind_speed_mean_ms,wind_speed_p95_ms,solar_radiation_daily_mean,solar_radiation_unit,
surface_soil_wetness_mean,valid_observations_pct,climate_source
```

- Media de amplitud térmica diaria: `mean(T2M_MAX - T2M_MIN)` sobre fechas válidas en las dos variables.
- `valid_observations_pct` inicial agrega valores válidos de todas las variables frente a `1826 * 8`. Mejorar con cobertura desglosada por parámetro y reindexación explícita de todas las fechas esperadas, evitando que una media aparentemente completa oculte una variable ausente.
- `solar_radiation_unit` debe conservarse literalmente o convertirse con método y unidad claros. No confundir irradiación (energía/área/intervalo) con irradiancia instantánea (potencia/área).
- NASA POWER devuelve datos de cuadrícula gruesa asociados al punto, no mediciones de la ventana de 10 km ni observaciones de una estación in situ. Las zonas cercanas pueden compartir celda y valores; contrastar con la gran variación de elevación local en las montañas.
- La LST de MODIS y la temperatura del aire de POWER no son la misma magnitud. Presión, humedad y viento terrestres no tienen equivalentes directos en la Luna; viento marciano, si se usa después, exige considerar densidad atmosférica y variable física de interés.

Aplicaciones: estimación preliminar de recurso solar, planificación de campañas terrestres, exposición térmica y riesgo de confundir variables de superficie/atmósfera. No calcular producción fotovoltaica efectiva sin modelo de equipo, orientación, pérdidas y condiciones de operación.

## 9. Caracterización óptica y espectral (Sentinel-2)

Script GEE `GeoAnalog_Spectral`. Archivo completo `spectral_features.csv` compartido por el usuario para las seis regiones; los resultados siguientes proceden de ese CSV. No son espectros extraterrestres.

### 9.1 Método

- Colección `COPERNICUS/S2_SR_HARMONIZED`, reflectancia de superficie L2A, periodo `2025-01-01` a `2026-01-01` exclusivo.
- Filtrar intersección con región, porcentaje de nubes de escena `<80`, y máscara por píxel `SCL == 4 OR SCL == 5` (vegetación y suelo no vegetado; descarta otras clases, incluyendo agua, nubes, nieve y sombras clasificadas). La clasificación automática no es perfecta.
- Multiplicar bandas por 0.0001 para convertir a reflectancia adimensional (no porcentaje). Seleccionar `B2,B3,B4,B5,B6,B7,B8,B8A,B11,B12`.
- Mediana temporal de cada banda; exigir al menos cinco observaciones válidas en B4 por píxel. Un espectro derivado de medianas por banda no necesariamente fue observado simultáneamente en una única fecha.
- Calcular índices sobre el compuesto, no promediar índices diarios. Estadísticas espaciales a 20 m en UTM. Revisar remuestreo y alineación de bandas 10/20 m si se requiere comparación de alta precisión.
- Calcular NDVI y BSI promedio sobre superficie válida general. Para reflectancias e índices de suelo, aplicar además `NDVI < 0.2`. El umbral es exploratorio y no demuestra que el suelo esté completamente desnudo; puede incluir mezclas de vegetación, sombras no clasificadas o materiales diversos. Los cocientes en el script se enmascaran cuando el denominador no supera 0.001.
- Media y desviación estándar espacial para las diez bandas y cuatro índices en el subconjunto de baja vegetación. Reportar también cobertura válida respecto a la ventana total y cobertura de baja vegetación respecto a la ventana total; no confundir con porcentaje respecto a solo los píxeles válidos.
- Capas GEE: RGB `B4/B3/B2`, SWIR falso color `B12/B11/B4`, cocientes hierro e hidroxilo, polígono de estudio. Visualizaciones no exportadas como archivos cartográficos finales según el estado conocido.

Fórmulas (rho es reflectancia):

```text
NDVI = (rho_B8 - rho_B4) / (rho_B8 + rho_B4)
BSI  = ((rho_B11 + rho_B4) - (rho_B8 + rho_B2)) /
       ((rho_B11 + rho_B4) + (rho_B8 + rho_B2))
IOR  = rho_B4 / rho_B2
HMR  = rho_B11 / rho_B12
```

IOR y HMR son indicadores de **contrastes espectrales compatibles** con ciertos materiales; no identifican minerales de forma inequívoca ni miden concentración de hierro/arcillas. El cociente promedio es la media de cocientes por píxel, no necesariamente cociente de medias.

### 9.2 Bandas

| Banda | Longitud de onda central aprox. (nm) | Resolución nominal (m) |
|---|---:|---:|
| B2 | 490 | 10 |
| B3 | 560 | 10 |
| B4 | 665 | 10 |
| B5 | 705 | 20 |
| B6 | 740 | 20 |
| B7 | 783 | 20 |
| B8 | 842 | 10 |
| B8A | 865 | 20 |
| B11 | 1610 | 20 |
| B12 | 2190 | 20 |

Las longitudes son aproximadas y dependen de plataforma/respuesta espectral. Las diez bandas no constituyen un espectro continuo; las líneas entre puntos en las gráficas se usan solo como guía visual.

### 9.3 Resultados de índices y control de cobertura

| Región | NDVI general | BSI general | IOR medio (NDVI bajo) | HMR medio (NDVI bajo) | Cobertura válida (%) | NDVI bajo válido / ventana (%) | Escenas de colección |
|---|---:|---:|---:|---:|---:|---:|---:|
| Tatacoa | 0.40104 | 0.07650 | 1.42145 | 1.22346 | 100.00 | 26.74 | 45 |
| La_Guajira | 0.12736 | 0.20474 | 1.96724 | 1.31212 | 53.41 | 44.57 | 333 |
| Nevado_del_Ruiz | 0.20573 | 0.06042 | 1.28820 | 1.10445 | 79.58 | 42.64 | 53 |
| Volcan_Purace | 0.49769 | -0.02144 | 1.20737 | 1.27647 | 72.37 | 2.16 | 73 |
| La_Candelaria | 0.50381 | 0.00756 | 1.63443 | 1.28966 | 100.00 | 10.84 | 70 |
| Nevado_Santa_Isabel | 0.37560 | 0.12303 | 1.32603 | 1.13720 | 98.01 | 14.18 | 52 |

`image_count` es cantidad de imágenes/gránulos filtrados, no número de fechas únicas ni observaciones por píxel. La Guajira presenta baja cobertura debido a las máscaras (posible agua y otros factores); esto no prueba que el resto de la ventana sea exclusivamente océano. Puracé tiene muy poco soporte espacial de baja vegetación; no presentar su firma como representativa de toda la ventana. Todos los porcentajes y medias deben acompañarse de su universo de cálculo.

### 9.4 Reflectancia media de superficies de NDVI bajo

| Banda (nm aprox.) | Tatacoa | La_Guajira | Nevado_del_Ruiz | Volcan_Purace | La_Candelaria | Nevado_Santa_Isabel |
|---|---:|---:|---:|---:|---:|---:|
| B2 (490) | 0.130386 | 0.146812 | 0.137719 | 0.126664 | 0.092665 | 0.086946 |
| B3 (560) | 0.163771 | 0.229503 | 0.157135 | 0.134387 | 0.125181 | 0.100259 |
| B4 (665) | 0.183110 | 0.287468 | 0.175069 | 0.150017 | 0.150385 | 0.115138 |
| B5 (705) | 0.213037 | 0.332033 | 0.181702 | 0.163636 | 0.173171 | 0.124035 |
| B6 (740) | 0.233254 | 0.346247 | 0.184312 | 0.176789 | 0.194808 | 0.130806 |
| B7 (783) | 0.244621 | 0.362810 | 0.184621 | 0.184575 | 0.203132 | 0.135501 |
| B8 (842) | 0.238478 | 0.351202 | 0.180907 | 0.186051 | 0.197284 | 0.137847 |
| B8A (865) | 0.259425 | 0.372055 | 0.178560 | 0.194063 | 0.206984 | 0.140941 |
| B11 (1610) | 0.314131 | 0.483763 | 0.185370 | 0.222350 | 0.302023 | 0.206624 |
| B12 (2190) | 0.257508 | 0.375965 | 0.167047 | 0.173999 | 0.234751 | 0.181663 |

La Guajira tiene la mayor reflectancia media en estas diez bandas dentro de los subconjuntos analizados. No atribuirlo de manera exclusiva a un mineral: influyen textura, albedo, humedad, granulometría, vegetación residual, geometría de iluminación y mezclas de materiales.

### 9.5 Esquema de archivo y uso

- `B2_mean`, `B2_stdDev`, ..., `B12_mean`, `B12_stdDev` (diez bandas; no B1/B9/B10 en la selección). Valores de reflectancia media y dispersión espacial en el subconjunto NDVI bajo.
- `ndvi_s2` y `bare_soil_index`: estadísticas generales. `ndvi_s2_mean`, `ndvi_s2_stdDev`, `bare_soil_index_mean`, `bare_soil_index_stdDev`: estadísticas en el subconjunto de baja vegetación. **No intercambiar estos nombres**.
- `iron_oxide_ratio_mean`, `iron_oxide_ratio_stdDev`, `hydroxyl_ratio_mean`, `hydroxyl_ratio_stdDev`: cocientes y dispersión espacial, subconjunto de NDVI bajo.
- `spectral_coverage_pct`, `low_vegetation_valid_pct`, `image_count`, `analysis_scale_m`, `spectral_period_start`, `spectral_period_end_exclusive`, `source`, `region`, `planet`, `latitude`, `longitude`, `system:index`, `.geo`.
- Las desviaciones estándar representan variabilidad espacial, **no incertidumbre instrumental** ni error estándar de la media.

Aplicaciones web: gráfica de reflectancia vs longitud de onda con puntos por banda, comparación entre lugares y, opcionalmente, bandas de dispersión etiquetadas claramente. Presentar la cobertura válida. Reservar comparación mineralógica extraterrestre directa para una metodología que considere respuesta espectral, fotometría y calibración instrumental.

## 10. EMIT: etapa actual (mineralogía hiperespectral)

EMIT (*Earth Surface Mineral Dust Source Investigation*) es un espectrómetro de imagen de NASA/JPL instalado en la Estación Espacial Internacional. Se indicó cobertura nominal de ~60 m y espectroscopía de centenares de canales; se eligió el producto L2B Mineral Identification porque ya contiene resultados de identificación de características de absorción mineral y productos complementarios de incertidumbre. No es necesario iniciar identificación desde cero con reflectancia L2A.

Posibles minerales de interés (no detecciones confirmadas): hematita, goethita, caolinita, illita, calcita, dolomita, yeso, montmorillonita y clorita, entre otros. **Usar exclusivamente los nombres, agrupaciones y códigos de la versión realmente descargada**; no afirmar que todos esos minerales estén presentes o que el producto los distinga individualmente en todas las condiciones.

### 10.1 Búsqueda completada

Script `src/search_emit.py`, `earthaccess.search_data(short_name='EMITL2BMIN', version='001', temporal=('2022-08-09','2026-11-14'), bounding_box=(lon-.05, lat-.05, lon+.05, lat+.05))`. Esta caja es aproximada y no idéntica a la ventana DEM; se usa para encontrar escenas. El procesamiento definitivo debe intersectar el polígono real de análisis.

| Región | Escenas/gránulos encontrados |
|---|---:|
| Tatacoa | 18 |
| La_Guajira | 33 |
| Nevado_del_Ruiz | 13 |
| Volcan_Purace | 5 |
| La_Candelaria | 16 |
| Nevado_Santa_Isabel | 11 |
| Total de coincidencias región–gránulo | 96 |

Resultado confirmado por terminal. Un gránulo puede aparecer en varias regiones; 96 no equivale a 96 escenas únicas. No implica cobertura válida ni identificación mineral dentro de la región. CSV `emit_availability.csv`: `region,planet,latitude,longitude,emit_granules,emit_available,source`, todos los `emit_available=True` en la salida reportada.

### 10.2 Siguiente paso concreto: descargar y comprobar

**Ya se entregó `download_emit.py`. No asumir que los datos están descargados.** Procedimiento original:

1. Crear cuenta gratuita en https://urs.earthdata.nasa.gov/ si todavía no se tiene. Activar cuenta y permisos que NASA solicite para el producto.
2. Guardar `src/download_emit.py` con el código antes proporcionado. Mantener `MAX_SCENES=3` como piloto; ordena granules por `umm.TemporalExtent.RangeDateTime.BeginningDateTime` descendente. El criterio de fecha es provisional, no garantiza calidad o cobertura.
3. Ejecutar desde PowerShell con `.venv` activa:

```powershell
python src/download_emit.py
```

4. Iniciar sesión mediante `earthaccess.login(strategy='interactive')`. La contraseña puede no mostrarse al teclear. Nunca pegar credenciales en el chat ni dejarlas escritas en el script.
5. Las descargas son automáticas, mediante `earthaccess.download(selected, str(region_dir))`. Se esperan pares `EMIT_L2B_MIN_*.nc` y `EMIT_L2B_MINUNCERT_*.nc` según versión y enlaces realmente retornados. Se guardan en `data/raw/emit/<region>/`. El registro previsto `data/features/emit_downloads.csv` contiene región, gránulos disponibles/seleccionados y archivos NetCDF locales (verificar). Hasta 18 selecciones región–gránulo y aproximadamente 36 archivos de datos si cada selección trae dos NetCDF y no existen archivos previos; es una expectativa, no cantidad observada.
6. Verificar terminal, tamaño real, manifest, éxito de descarga, producto/versión, integridad de archivos y correspondencia de MIN con MINUNCERT por ID temporal/escena. No tratar `len(glob('*.nc'))` como prueba de éxito individual; puede incluir archivos antiguos, incompletos o duplicados.

Si se quiere reducir volumen, una mejora opcional es probar **una escena de Tatacoa primero**, verificar el producto y después descargar el resto. Esto no sustituye la selección previa sin que el usuario conozca el cambio. Si hay fallos de autenticación, consultar el mensaje real antes de reinstalar librerías. Si varios lugares comparten escenas, considerar caché única por granule ID (propuesta).

### 10.3 Inspección antes de escribir el algoritmo final

No se inspeccionó aún un NetCDF real. El siguiente agente debe **evitar inventar dimensiones, nombres de variables, códigos de minerales, coordenadas o estructura de grupos**. Consultar guía oficial L2B y un archivo descargado. Un `inspect_emit.py` mínimo (propuesta, no ejecutado) puede listar metadatos sin leer matrices grandes:

```python
from pathlib import Path
from netCDF4 import Dataset

root = Path(__file__).resolve().parent.parent / 'data' / 'raw' / 'emit'

def inspect_group(group, indent=''):
    print(indent + 'GROUP:', group.path)
    print(indent + 'DIMS:', {k: len(v) for k, v in group.dimensions.items()})
    for k, v in group.variables.items():
        print(indent + f'{k}: dims={v.dimensions}, shape={v.shape}, dtype={v.dtype}')
        for a in ('long_name', 'units', '_FillValue', 'missing_value',
                  'flag_values', 'flag_meanings', 'valid_range', 'scale_factor', 'add_offset'):
            if a in v.ncattrs():
                print(indent + '  ', a, v.getncattr(a))
    for child in group.groups.values():
        inspect_group(child, indent + '  ')

files = sorted(root.rglob('*.nc'))
if not files:
    raise SystemExit('No hay NetCDF descargados; revisar download_emit.py')
for prefix in ('EMIT_L2B_MIN_', 'EMIT_L2B_MINUNCERT_'):
    p = next((x for x in files if x.name.startswith(prefix)), None)
    if p is None:
        print('No se encontró archivo para', prefix)
        continue
    print('\nFILE:', p)
    with Dataset(p) as ds:
        print('GLOBAL ATTRIBUTES:', ds.ncattrs())
        inspect_group(ds)
```

Dependencias previamente propuestas: `earthaccess`, `xarray`, `netCDF4`; `rasterio` y `pyproj` ya previstos para geoprocesamiento. Inspeccionar también grupos de minerales y atributos de georreferenciación específicos del producto, usando el tutorial enlazado en sección 4.

### 10.4 Procesamiento científico propuesto

1. Identificar estructura y código de cada grupo mineral, valores de relleno y ausencia de detección, profundidad de absorción, incertidumbres y métricas de calidad. Confirmar si se trata de detección dominante por grupo o de otras representaciones; no asumir independencia entre capas.
2. Usar GLT (geographic lookup table) y sus reglas oficiales de indexado para ortorrectificar si el producto aún está en geometría de adquisición. No aplicar GLT dos veces ni ignorar valores inválidos. Como alternativa para estadística, evaluar recorte de píxeles geolocalizados si está bien fundamentado.
3. Definir polígono DEM/terrestre exacto y recortar escenas por región. Usar vecino más próximo para etiquetas categóricas; no promedio de IDs de mineral. Si se necesitan comparaciones de área, usar malla métrica o pesos de área apropiados.
4. Máscaras: calidad de producto, cobertura, agua, nieve, nubes, vegetación y restricciones que se indiquen en documentación; no asumir que la máscara Sentinel-2 de 2025 aplica automáticamente a escenas de otros años.
5. Calcular cobertura válida por escena y área con detecciones, frecuencia espacial de mineral por grupo, profundidad de absorción e incertidumbre solo donde su interpretación sea válida. Diferenciar: `valid_area / region_area`, `detected_area / valid_area` y `mineral_area / denominator_defined`. Las distintas capas pueden solaparse; no sumar porcentajes entre grupos si se superponen. Cero detecciones válidas significa no detectado en ese soporte, no prueba ausencia física del mineral.
6. Para combinar múltiples fechas, reportar por escena o generar consenso sobre una malla común con método explícito; no sumar píxeles de escenas solapadas como si fueran áreas nuevas. Evitar escoger solo escenas que confirmen hipótesis; definir regla de selección por cobertura/calidad. Conservar fecha e ID de adquisición.
7. Generar `mineralogical_features.csv` (propuesto: formato largo por región, escena, grupo mineral y mineral) y mapas de mineralogía como PNG/GeoTIFF opcional, únicamente si los datos lo permiten. Si no hay detecciones suficientes, publicar `insufficient_valid_coverage` u otro estado explícito en lugar de completar con suposiciones.

Esquema propuesto, sujeto a inspección del producto:

```text
region,planet,granule_id,acquisition_date,product_version,mineral_group,mineral_id,
mineral_name,region_area_km2,valid_area_km2,valid_coverage_pct,detected_area_km2,
mineral_area_km2,denominator_type,mineral_detection_pct,absorption_depth_stat,
uncertainty_stat,quality_rule,status,source
```

Las columnas de profundidad/incertidumbre se deben nombrar con métrica y unidad reales una vez examinadas. Los porcentajes son fracciones de área/píxeles detectados, **no abundancia química ni porcentaje en masa**.

## 11. Control de calidad prioritario y limitaciones

### 11.1 La Guajira: corregir la posible contaminación marina antes de publicar el ranking definitivo

Evidencia observada: elevación media 10.64 m, mediana 1.04 m, 99.74 % de terreno plano a 200 m, cobertura DEM 100 %, pero cobertura espectral válida 53.41 %. La ventana incluye un sector costero; los números son compatibles con inclusión de agua, pero no permiten determinar por sí solos la fracción marina.

Acción recomendada:

1. Abrir la región y los límites de raster exactos sobre una máscara de agua/tierra confiable. Revisar `water_pct` del CSV ambiental, visualización y fuentes de costa (WorldCover 2021, máscara de agua o geometría litoral documentada; confirmar cobertura marina de los productos).
2. Elegir entre mantener el centro y enmascarar agua o definir una ventana nueva tierra adentro (ideal si se desea conservar 100 km² de soporte comparable). No cambiar silenciosamente coordenadas ni nombre de lugar; registrar revisión de versión y decisión con el equipo.
3. Enmascarar **antes** del remuestreo promedio para no mezclar alturas marinas con tierra; comprobar fracción de tierra por celda, umbrales de cobertura, necesidad de excluir celdas mixtas y vecindades con NoData. No convertir el mar a cero como sustituto de máscara.
4. Recalcular features terrestres, `normalization_parameters.csv`, matriz y ranking. Si se modifica el polígono, volver a extraer atributos ambientales, espectrales y mineralógicos que dependan de ese soporte. Conservar resultados v1 para trazabilidad.
5. Hasta entonces, marcar resultados de La Guajira como `provisional_coastal_mask`; el ranking completo también es experimental.

### 11.2 Verificación geográfica y espacial

- Validar DEM centrales y alineación de centros/ventanas, zona UTM, datum vertical, CRS marciano, correspondencia de nombres LOLA y centro de cada archivo. Comprobar que la imagen regional es del sitio descrito.
- El buffer y envolvente usados en GEE no garantizan exactamente 10×10 km, ni coincidencia con el DEM remuestreado. Guardar polígonos exactos de cada análisis y preferir, a futuro, una región canónica derivada de los límites del DEM o un cuadrado UTM explícito centrado en la coordenada objetivo.
- MOLA/HRSC tiene resolución efectiva heterogénea; LOLA puede contener interpolación. Un pixel de 200 m reproyectado no significa detalle real de 200 m. Realizar prueba adicional a 500 m (20×20 para 10 km) o más gruesa según documentación. Rehacer todo el pipeline a esa escala y comparar rankings, no solo cambiar etiquetas.
- Mantener las máscaras en remuestreos y gradientes. Confirmar las unidades y el denominador de cobertura de las variables con vecindad. Inspeccionar posibles picos, artefactos y discontinuidades. La elevación min/max es sensible a outliers.

### 11.3 Validación del índice

- Solo seis candidatos terrestres de referencia; Z-score depende fuertemente de la muestra. Si se agregan otros lugares, congelar o versionar los parámetros para que los resultados sean comparables.
- Evaluar correlaciones entre `relief_p90_p10_m`, `elevation_std_m`, pendientes y TRI/TPI; evitar doble ponderación implícita. Probar pesos iguales, retirar variables redundantes, pesos alternativos y sensibilidad a umbrales/resolución/geometría. Reportar robustez del orden de candidatos.
- Validar frente a regiones conocidas como análogos y controles negativos, con bibliografía o datos independientes. No ajustar pesos para producir el resultado esperado.
- No introducir índices ambientales terrestres en el PAI topográfico simplemente porque están disponibles. Si se crea una similitud multicomponente, definir subíndices por fenómeno y criterios de comparabilidad, unidades, incertidumbre, manejo de datos ausentes y una regla explícita de combinación. Mostrar qué dimensiones se evaluaron.
- Distinguir comparabilidad científica de aptitud logística para hacer ensayos (acceso, restricciones ambientales y permisos, propiedad, seguridad, etc.). Estos aspectos requieren fuentes adicionales, no dependen directamente del PAI.

## 12. Próximos datasets y fases científicas (propuestas, no implementadas)

### 12.1 Geología terrestre: Servicio Geológico Colombiano (SGC)

Objetivo: complementar índices ópticos y EMIT con litología, unidades geológicas, origen y edad. Consultar cartografía geológica oficial y su escala, metadatos, leyenda y licencia; escoger hojas que intersecten las seis regiones. Si existen vectores públicos compatibles, intersectar polígonos y calcular áreas por unidad litológica en un CRS métrico. Si solo hay documentos, documentar texto, mapa y página exacta con referencia. No extrapolar la composición química de la roca a partir de un nombre de unidad.

Salida propuesta: `geology.json` o `geology_features.csv` en formato largo, con `region,unit_code,unit_name,lithology,age,area_pct,map_scale,source,source_url,notes` cuando estén disponibles. Mostrar también diversidad geológica y origen de cada lugar (sedimentario, volcánico, etc.) únicamente con evidencia.

### 12.2 Temperatura de Marte: THEMIS

Investigar productos oficiales de Mars Odyssey THEMIS: temperatura superficial derivada, radiancia térmica o inercia térmica, según archivos disponibles y objetivo. No equiparar una imagen infrarroja radiométrica con temperatura en kelvin sin conversión documentada. Seleccionar productos para las seis ubicaciones, fechas/estación solar Ls, hora local, geometría, resolución, unidades y calidad. Para una primera versión, reportar rangos o temperaturas diurna/nocturna con sus metadatos, no un clima anual terrestre extrapolado.

### 12.3 Temperatura lunar: Diviner (LRO)

Investigar productos térmicos oficiales de Diviner, especialmente datos polares. Considerar hora solar local, incidencia, sombras permanentes, estación lunar y cobertura. Elegir temperatura superficial comparable y documentar escala, estadística, unidades y observaciones. Las zonas lunares polares tienen geometría de iluminación muy distinta; no interpretar diferencia térmica día-noche como el mismo ciclo de 24 h terrestre.

**Salida propuesta conjunta**: `planetary_thermal_features.csv`, con `region,planet,source,product_id,quantity,statistic,value,unit,local_time,season_or_ls,coverage_pct,resolution_m,quality_flag,notes`, adaptado a datos reales. Convertir Kelvin/Celsius solo donde la variable física es temperatura; no inventar comparabilidad entre LST, temperatura del aire, emisión térmica e inercia térmica.

### 12.4 Mineralogía extraterrestre: CRISM (Marte) y M³ (Luna)

- CRISM: buscar productos espectrales o índices de minerales de Mars Reconnaissance Orbiter en PDS. Verificar si hay observaciones útiles de las seis ventanas marcianas y qué producto permite identificación fiable.
- Moon Mineralogy Mapper (M³): investigar datos de Chandrayaan-1 para las zonas polares, sus correcciones y cobertura/limitaciones de iluminación. No suponer disponibilidad en zonas de sombra.
- Si el objetivo es comparación espectral, usar magnitudes compatibles de reflectancia, eliminar bandas inválidas, armonizar geometría fotométrica y considerar respuesta espectral de los sensores. Cuando existan espectros de mayor resolución, integrar contra las funciones de respuesta espectral de las bandas comunes en vez de extrapolar sin fundamento las diez bandas de Sentinel-2.
- Métodos futuros: comparación de profundidad/posición de rasgos de absorción, ángulo espectral (`SAM`) sobre bandas realmente compatibles, biblioteca espectral de laboratorio y coincidencia de familias minerales. Cada método necesita validación y control de mezcla/ruido. Ausencia de una banda o detección no equivale a ausencia del mineral.

No se han descargado ni procesado estos cuatro productos extraterrestres. La siguiente IA debe verificar identificadores, versiones y enlaces en documentación oficial antes de proporcionar un script de descarga. No bloquear la primera entrega web hasta completar todas estas etapas.

### 12.5 Descubrimiento de nuevos análogos

Fase posterior para superar el sesgo de seis candidatos. Definir un dominio de búsqueda (Colombia primero), malla de ventanas de tamaño físicamente comparable, máscara de tierra firme y cobertura, generar features DEM de forma escalable, comparar usando una referencia de normalización versionada, filtrar candidatos y revisar manualmente los resultados. Evaluar muestreo espacial, duplicación/solapamiento, áreas protegidas y restricciones de acceso. No etiquetar como descubrimiento automático el ranking actual.

## 13. Integración de datos con la web (prioridad de entrega)

### 13.1 Contrato de datos propuesto

El equipo web no debería leer NetCDF pesados ni calcular topografía en el navegador. La recomendación es un proceso offline en Python que lea los CSV y produzca JSON/GeoJSON livianos, más imágenes de caracterización. Confirmar con los compañeros qué formato acepta su implementación antes de cambiarlo.

Archivos mínimos para la **primera entrega**:

| Archivo | Contenido y uso |
|---|---|
| `data/features/planetary_features.csv` | Características topográficas de 18 regiones |
| `data/results/analog_ranking.csv` | 72 pares objetivo–candidato y score |
| `data/results/similarity_matrix.csv` y `.png` | Matriz de similitud y mapa de calor |
| `data/results/normalized_features.csv` y `normalization_parameters.csv` | Reproducibilidad y auditoría |
| `data/features/environmental_features.csv` | LST, NDVI MODIS, cobertura y precipitación |
| `data/features/climate_features.csv` | Estadísticas NASA POWER, validar primero |
| `data/features/spectral_features.csv` | Reflectancias e índices Sentinel-2 |
| `data/features/emit_availability.csv` | Disponibilidad de escenas, no mineralogía |
| `data/figures/*_analysis.png` | Visualizaciones regionales |
| `locations.geojson` / `planetary_targets.json` | Salidas propuestas para el frontend |
| Este documento `.md` | Metodología, limitaciones y contexto de continuidad |

No es necesario enviar el DEM global de Marte ni archivos NetCDF brutos a los compañeros que implementan la interfaz. Mantenerlos por separado para reproducibilidad y generar mapas livianos cuando sea necesario. No publicar material sin verificar términos de uso y atribución.

### 13.2 Script de integración propuesto: `src/build_web_dataset.py`

No se ha creado todavía. Debe leer los archivos reales, no transcribir manualmente los números de este documento. Operaciones recomendadas:

1. Cargar `planetary_features.csv` y comprobar unicidad `(planet,region)`, 18 filas esperadas, campos obligatorios y unidades.
2. Filtrar `planet == 'earth'`. Unir ambiental, clima y espectral mediante `(planet,region)` con `validate='one_to_one'` y estrategia de unión izquierda para no perder lugares por datos ausentes. Comprobar claves faltantes, duplicadas o coordenadas inconsistentes; conservar fechas y fuentes por bloque. Eliminar campos `system:index` y `.geo` de GEE una vez extraídos los metadatos útiles. Evitar colisiones en `latitude`, `source`, `period` mediante prefijos o estructura anidada.
3. Construir `id = planet + '_' + region`. En ranking, agrupar por `candidate` y ordenar PAI descendente; conservar las doce coincidencias por ubicación y, si interesa, las mejores por planeta. Usar `target` para buscar ficha extraterrestre. Verificar que 12×6 = 72 pares únicos, PAI en (0,100], distancia no negativa y consistencia con fórmula, dentro de error de redondeo.
4. Convertir tipos NumPy a nativos de JSON; reemplazar NaN/Inf por `null`; usar `json.dump(..., allow_nan=False, ensure_ascii=False)`. No escribir `NaN` literal ni rellenar ausencias con cero. Redondear solo para visualización; conservar precisión original de resultados.
5. Exportar `data/web/locations.geojson` (propuesta) como `FeatureCollection` con seis puntos WGS84 de Tierra, `geometry.coordinates=[longitude,latitude]`. Crear `data/web/planetary_targets.json` con 12 regiones externas, coordenadas/CRS por cuerpo cuando estén confirmadas y sus propiedades. **No superponer coordenadas marcianas/lunares en el globo terrestre WGS84.** Si en el futuro se construyen globos separados, usar convenciones propias de cada cuerpo.
6. Agregar `schema_version`, `algorithm_version`, metadatos por fuente, flags de calidad, `status` y rutas relativas a figuras existentes. Emitir `data/web/manifest.json` con fecha de generación, fuentes, versión de datos y advertencias.
7. Exportar validación: número de sitios, pares, campos nulos, archivos inexistentes y advertencias. Acordar rutas y esquema con el equipo; no sobrescribir producción sin aviso.

### 13.3 Ejemplo real de ficha y formato de integración

Ejemplo parcial ilustrativo basado en resultados reales de Tatacoa; **no es un archivo GeoJSON ya generado**. Los campos `null` indican valores que no se han inspeccionado para este documento, no ausencia real de la propiedad. En el archivo de producción extraerlos del CSV original.

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "earth_Tatacoa",
      "geometry": {"type": "Point", "coordinates": [-75.17, 3.23]},
      "properties": {
        "region": "Tatacoa",
        "planet": "earth",
        "display_name": "Desierto de la Tatacoa",
        "country": "Colombia",
        "department": "Huila",
        "topography": {
          "resolution_m": 200,
          "valid_coverage_pct": 100,
          "elevation_mean_m": 433.03681,
          "local_relief_m": 137.47690,
          "slope_mean_deg": 2.17971,
          "tri_mean_m": 22.56462,
          "flat_terrain_pct": 95.31250,
          "source": "NASADEM"
        },
        "environment": {
          "annual_precipitation_mm": 1449.6457006783073,
          "bare_ground_pct": 17.001135459826543,
          "lst_day_mean_c": null,
          "period_start": "2021-01-01",
          "period_end_exclusive": "2026-01-01",
          "landcover_year": 2021
        },
        "spectral": {
          "ndvi_s2": 0.4010368807236874,
          "iron_oxide_ratio_mean": 1.4214499809718577,
          "hydroxyl_ratio_mean": 1.2234563617962928,
          "spectral_coverage_pct": 100,
          "low_vegetation_valid_pct": 26.741167907529558,
          "source": "Sentinel-2 L2A",
          "year": 2025
        },
        "mineralogy": {"status": "pending_processing", "emit_granules": 18},
        "best_analog": {
          "target": "mars_Pathfinder",
          "distance": 0.08671,
          "pai": 92.02119,
          "scope": "topography_only",
          "status": "experimental"
        },
        "quality_flags": ["experimental_pai", "resolution_effective_not_harmonized"]
      }
    }
  ]
}
```

En una implementación completa, `analog_matches` incluiría los doce resultados de cada lugar, `climate` incluiría sus valores reales, una lista `spectral_bands` tendría banda, longitud de onda aproximada, media y desviación estándar, y `images` referenciaría archivos existentes. El diseño es una propuesta, no un requisito de interfaz impuesto al equipo web.

### 13.4 Qué presentar al usuario del globo

- Nombre, coordenadas, contexto geográfico y fotografía con procedencia/licencia verificada. Distinguir imágenes ilustrativas de mapas calculados a partir de datos.
- Ficha de relieve: elevación media, relieve, pendiente, TRI, porcentaje plano, resolución nominal y área de estudio.
- Ficha de ambiente: LST día/noche y variación por pares, vegetación, precipitación y cobertura (con años distintos claramente visibles).
- Ficha energética y climática (una vez validado el CSV POWER): irradiación, temperatura del aire, humedad y viento, con unidades y advertencias de resolución.
- Espectro Sentinel-2: gráfica de diez puntos, índices y cobertura de datos, distinción de subconjunto NDVI bajo.
- Comparación extraterrestre: objetivo, PAI sobre 100, gráfico de variables topográficas normalizadas o físicas (con unidades), y acceso a los demás resultados. Texto recomendado: «Índice experimental de similitud topográfica dentro de los candidatos analizados». Evitar «92 % idéntico a Marte» o «zona apta para colonización».
- Mineralogía: mostrar `pendiente de procesamiento` hasta disponer de detecciones válidas. No convertir la cobertura de escenas EMIT en lista de minerales encontrados.
- Bloque de fuentes, metodología y limitaciones. Aplicaciones de ensayo presentadas como potenciales, no como certificación de viabilidad.

## 14. Plan priorizado de continuidad y criterios de terminado

| Prioridad | Actividad | Estado a la fecha | Evidencia de terminado |
|---|---|---|---|
| P0 | Adquirir y remuestrear 18 DEM | Completada | 18 rasters 50×50, cobertura reportada |
| P0 | Extraer variables topográficas | Completada | CSV 18×25 y figuras generadas según reporte |
| P0 | Ranking PAI 72 pares | Completada, experimental | CSV completo compartido |
| P0 | Caracterización ambiental con GEE | Exportada | CSV de seis filas; validar campos y máscaras |
| P0 | NASA POWER | Ejecución reportada | Inspeccionar CSV, cobertura y seis regiones pendientes de verificación |
| P0 | Sentinel-2 | Completada | CSV completo de seis filas; resultados preliminares |
| P0 | Disponibilidad EMIT | Completada | CSV + terminal, 96 coincidencias |
| P1 | Primera entrega JSON/GeoJSON al equipo | Pendiente | Seis puntos válidos, 18 fichas/objetivos enlazables, 72 pares, flags |
| P1 | Corregir La Guajira y georreferenciación | Pendiente | Máscaras/ventanas revisadas, ranking regenerado versionado |
| P1 | Descargar piloto EMIT | Pendiente de confirmar | NetCDF válidos por escena, manifest |
| P1 | Inspeccionar y procesar mineralogía EMIT | Pendiente | Cobertura/calidad y resultados con denominadores correctos |
| P2 | Cartografía SGC | Pendiente | Unidades geológicas documentadas por ventana |
| P2 | THEMIS y Diviner | Pendiente | Variables térmicas con unidad, hora, geometría y calidad |
| P2 | CRISM y M³ | Pendiente | Cobertura y metodologías espectrales verificadas |
| P2 | Sensibilidad/validación PAI | Pendiente | Comparación de escalas, pesos, muestras y estabilidad |
| P3 | Descubrimiento automático de nuevos candidatos | Pendiente | Búsqueda regional reproducible y controles |

El avance no debe expresarse como un porcentaje de desarrollo absoluto: las actividades no tienen igual costo ni importancia. El MVP topográfico está operativo; la disponibilidad de los otros atributos y la validez científica deben evaluarse por separado.

### Prueba de reejecución de las etapas existentes (si se requiere)

```powershell
# Solo si faltan outputs o se cambian entradas/código:
python src/resample.py
python src/process_planetary.py
python src/extract_features.py
python src/similarity.py

# Solo si falta el archivo climático o se necesita actualizarlo:
python src/extract_climate.py

# La búsqueda se completó; solo repetir si se desea actualizar inventario:
python src/search_emit.py

# Paso inmediato pendiente:
python src/download_emit.py
```

Las exportaciones GEE ambiental y espectral se realizan desde `Run` → `Tasks` → ejecutar tarea → descargar CSV de Drive → `data/features/`. No ejecutar los comandos de scripts propuestos hasta que estén creados.

## 15. Resumen para explicar al equipo

Se construyó un flujo de procesamiento de datos abiertos para comparar regiones de Colombia con ubicaciones de Marte y del polo sur de la Luna. Se seleccionaron 18 regiones y se homogeneizaron sus DEM en ventanas nominales de 10 × 10 km, con cuadrículas de 200 m. A partir de ellos se calcularon variables como pendiente, rugosidad, relieve y posición topográfica. Se implementó un índice experimental de similitud llamado PAI y se realizaron 72 comparaciones. La Tatacoa obtuvo 92.02/100 frente a Pathfinder, el mejor resultado observado dentro de los candidatos analizados. Para la Luna las mejores coincidencias fueron menores y se concentraron en sitios como La Candelaria y Puracé.

Además, se extrajo información ambiental, climatológica, energética y de reflectancia de las seis regiones colombianas. Los datos permiten construir fichas científicas, gráficas de espectros, comparaciones físicas y descripciones de potenciales ensayos tecnológicos. EMIT ya fue consultado: hay 96 coincidencias región–gránulo, pero la descarga y la caracterización mineralógica todavía están pendientes de confirmar/realizar. El siguiente objetivo de producto consiste en consolidar archivos livianos y documentados para que el globo interactivo consuma datos reales, mientras se completa el control de calidad científico.

## 16. Anexo reproducible: seis variables de entrada PAI

CSV compacto transcrito de `planetary_features.csv` compartido en el chat (no reemplaza el archivo original de 25 columnas). Permite comprobar la fórmula y ranking a partir de los números disponibles sin consultar archivos binarios. Los campos `resolution_m` y `valid_coverage_pct` fueron 200 y 100 para todas las filas.

```csv
region,planet,relief_p90_p10_m,elevation_std_m,slope_mean_deg,slope_p90_deg,tri_mean_m,tpi_std_m
La_Candelaria,earth,418.97878,153.97920,9.58461,15.59400,92.98506,14.14110
La_Guajira,earth,34.10956,14.25317,0.65947,1.76664,7.38358,2.38737
Nevado_del_Ruiz,earth,980.04106,358.34105,16.75431,26.86595,163.48794,21.95268
Nevado_Santa_Isabel,earth,670.39976,257.27771,13.70199,22.59207,136.65770,21.29379
Tatacoa,earth,77.88781,29.21469,2.17971,3.95262,22.56462,4.75026
Volcan_Purace,earth,750.43618,276.88899,12.99448,21.00037,125.66453,17.98132
Gale,mars,101.60166,61.70453,2.17262,4.96686,19.94937,2.42588
Jezero,mars,169.39932,61.59744,2.14797,3.82876,20.22453,2.77464
Pathfinder,mars,38.39763,19.55624,1.86976,3.58945,18.20781,3.87670
Phoenix,mars,68.30786,24.69694,0.61425,1.14340,5.44554,0.40909
Viking_1,mars,18.37642,7.51026,0.33989,0.60812,3.00862,0.21637
Viking_2,mars,53.57075,21.08336,2.09191,3.63387,19.29468,2.28624
Connecting_Ridge,moon,782.06886,286.06118,10.57361,18.33993,94.68433,6.05821
De_Gerlache_Rim,moon,1138.53159,436.22650,15.07354,23.23370,134.88927,5.49213
Leibnitz_Beta_Plateau,moon,768.74463,354.65063,11.69008,20.94967,104.53965,5.43931
Malapert_Massif,moon,1189.86758,455.93863,15.91135,23.71401,142.67541,4.93530
Peak_Near_Shackleton,moon,785.95433,281.44051,10.48747,16.79983,92.74286,4.28118
Shackleton_Rim,moon,2771.84203,1065.35664,23.97213,32.57964,225.82725,6.71176
```

## 17. Qué archivos solicitar para una continuación exacta

El documento es suficiente para entender la estrategia, no para garantizar que se reconstruye byte a byte el repositorio. Si la otra IA puede acceder a los archivos locales, darle preferentemente:

- `src/` completo y exportaciones de los scripts GEE.
- `data/features/`, `data/results/` y `data/figures/`.
- Un NetCDF `MIN` y su `MINUNCERT` correspondientes cuando se complete la descarga EMIT (o solo su inventario de metadatos al principio).
- Los DEM **procesados** para auditar resultados; DEM originales o ventanas crudas para revisar remuestreo y máscaras, sin necesidad de subir el global de Marte si una ruta local es accesible.
- Esquema/stack o ejemplos de datos del equipo web, si se necesita implementar integración real.

No compartir `.venv`, tokens, contraseñas, `.netrc`, credenciales Earthdata ni secretos de APIs. Conservar procedencia, nombres y versiones. El alcance de esta transferencia es el trabajo conocido hasta la fecha de corte; nuevas acciones requieren verificar el estado actual del proyecto.
