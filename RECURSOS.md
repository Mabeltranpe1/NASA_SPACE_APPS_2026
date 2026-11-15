# Recursos y bases de datos del reto

Reto: **Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars** (NASA Space Apps 2026).

Idea general: caracterizar los sitios candidatos para bases en la Luna (polo sur lunar) y en Marte con datos orbitales (temperatura, topografía, radar, hielo, iluminación) y luego buscar en la Tierra lugares con condiciones parecidas usando datos de observación terrestre.

Estado de acceso verificado el 2026-11-14: ✅ carga bien · ⚠️ requiere revisión manual.

---

## 1. Luna y Marte (datos planetarios)

### NASA Planetary Data System (PDS) ✅
- URL: https://pds.nasa.gov/
- Archivo oficial de la NASA con todos los datos de misiones planetarias.
- Buscador general: https://pds.nasa.gov/tools/data-search/

### PDS Geosciences Node: Lunar Reconnaissance Orbiter (LRO) ✅
- URL: https://pds-geosciences.wustl.edu/missions/lro/
- La página reúne los instrumentos de LRO. Estos son los útiles para este reto:

| Instrumento | Qué mide | Por qué sirve para una base | Archivo |
|---|---|---|---|
| **Diviner** | Temperatura superficial (radiómetro IR, ~500 m) | Extremos térmicos y trampas frías en el polo sur | [Diviner](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm) |
| **LOLA** | Altimetría láser (topografía, pendientes, rugosidad) | Terreno plano y seguro, iluminación y sombras | [LOLA](https://pds-geosciences.wustl.edu/missions/lro/lola.htm) |
| **LEND** | Neutrones (hidrógeno, posible hielo de agua) | Recursos in situ (ISRU) | [LEND](https://pds-geosciences.wustl.edu/missions/lro/lend.htm) |
| **Mini-RF** | Radar SAR | Hielo en cráteres sombreados; comparable con SAR terrestre | [Mini-RF](https://pds-geosciences.wustl.edu/missions/lro/mrf.htm) |
| **CRaTER** | Radiación cósmica | Riesgo para la tripulación | [PPI Node](https://pds-ppi.igpp.ucla.edu/) |
| **LROC** | Imágenes de alta resolución | Inspección visual de los sitios | http://lroc.sese.asu.edu/ |

- **Lunar Orbital Data Explorer (ODE)** permite buscar, visualizar y descargar todos los datos de LRO: https://ode.rsl.wustl.edu/moon/
- El mismo nodo tiene datos de Marte (MRO/SHARAD, Odyssey/THEMIS, MGS/MOLA, etc.). Explorador para Marte: https://ode.rsl.wustl.edu/mars/
- También hay un **DEM del polo sur lunar** (radar terrestre): https://pds-geosciences.wustl.edu/missions/lram/index.htm

### Diviner: productos principales ✅
- URL: https://pds-geosciences.wustl.edu/missions/lro/diviner.htm
- Cobertura desde julio de 2009 hasta junio de 2026 (Release 67).
- Productos derivados (los más útiles para empezar, sin procesar datos crudos):
  - **PCP – Polar Cumulative Products**: estadísticas de temperatura en los polos.
  - **PRP – Polar Resource Products**: productos para recursos polares.
  - **GDR L2/L3**: mapas globales de temperatura.
  - **GHRM**: mosaicos globales de alta resolución.
  - Raíz de los productos derivados: https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/
- ⚠️ Desde abril de 2019, casi todos los RDR traen vacíos los canales solares 1 y 2. Los datos faltantes tienen el valor `-9999` en la columna 24 (`tb`).

---

## 2. Tierra (para buscar los análogos)

### NASA Earthdata Search ✅
- URL: https://search.earthdata.nasa.gov/
- Buscador de todos los datos de observación terrestre de la NASA (MODIS, Landsat, SRTM/ASTER DEM, temperatura superficial, etc.). Necesita una cuenta gratuita de Earthdata Login para descargar.

### NASA Worldview ✅
- URL: https://worldview.earthdata.nasa.gov/
- Visor interactivo de capas satelitales casi en tiempo real. Sirve para explorar rápido sitios candidatos (desiertos, Antártida, zonas volcánicas, permafrost).

### Copernicus Data Space Ecosystem (ESA/UE) ✅
- URL: https://dataspace.copernicus.eu/
- Sentinel-1 (radar SAR), Sentinel-2 (óptico), Sentinel-3 (temperatura) y DEM de Copernicus. Gratuito con registro.

### ESA Open Science Data ✅
- URL: https://opensciencedata.esa.int/
- Catálogo abierto de datos científicos de la ESA.

### JAXA G-Portal ✅
- URL: https://www.gportal.jaxa.jp/?lang=en
- Datos de satélites japoneses (ALOS/PALSAR radar, GCOM, etc.).

### Agencia Espacial Canadiense (CSA): RADARSAT ⚠️
- RADARSAT Constellation Mission (RCM): https://donnees-data.asc-csa.gc.ca/en/dataset/rcm
- RADARSAT-1: https://donnees-data.asc-csa.gc.ca/en/dataset/radarsat1
- Datos de radar SAR terrestre, comparables con Mini-RF lunar y SHARAD de Marte.
- ⚠️ Desde WSL falla la verificación del certificado SSL. En el navegador debería abrir sin problema.

### Microsoft Planetary Computer ✅
- Catálogo: https://planetarycomputer.microsoft.com/catalog · API STAC: https://planetarycomputer.microsoft.com/api/stac/v1
- Unas 140 colecciones de la Tierra: Sentinel-2 L2A, Landsat Collection 2, Copernicus DEM, NASADEM, MODIS, ALOS, ESA WorldCover…
- **Gratis, sin cuenta ni clave** para buscar y renderizar. Tiene CORS abierto.
- La app lo usa para las **imágenes de cerca de la Tierra** (Sentinel-2, 10 m), generadas con `src/export_images.py`. Ver [docs/DATOS_WEB.md](docs/DATOS_WEB.md#imágenes-de-cerca-de-la-tierra).
- Cita obligatoria: "Contiene datos modificados de Copernicus Sentinel" (ESA).
- ⚠️ Comprobado el 2026-11-15: el renderizado de recortes de Landsat C2 devuelve error 500, así que solo se usa Sentinel-2.

### Tutorial SAR de la CSA ✅
- URL: https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial
- Guía para principiantes sobre cómo cargar y graficar rasters SAR (RADARSAT/RCM) y shapefiles.
  - Opción 1: QGIS (guía en PDF).
  - Opción 2: Python, con un notebook Jupyter que usa `osgeo` (GDAL), `cartopy` y `matplotlib`.
- Datos de ejemplo: incendios de Columbia Británica captados por RCM3.

---

## 3. Variables candidatas para comparar Luna/Marte ↔ Tierra

| Variable | Luna / Marte | Tierra |
|---|---|---|
| Temperatura superficial | Diviner (Luna), THEMIS/TES (Marte) | MODIS LST, Sentinel-3 |
| Topografía / pendiente | LOLA, MOLA | SRTM, Copernicus DEM, ASTER |
| Rugosidad / radar | Mini-RF, SHARAD | Sentinel-1, RADARSAT, ALOS-PALSAR |
| Hielo / agua | LEND, Mini-RF | Permafrost, glaciares (Earthdata) |
| Iluminación | LOLA (sombras permanentes) | Latitudes polares |

---

## 4. Fuentes que ya usa el proyecto (actualizado el 2026-11-14)

Las descargas se hacen con los scripts de `src/`. Detalle de versiones, resoluciones y periodos en [docs/PIPELINE_COMPARADOR.md](docs/PIPELINE_COMPARADOR.md) (Marco) y [docs/CONTEXTO_TECNICO_SANTIAGO.md](docs/CONTEXTO_TECNICO_SANTIAGO.md) (Santiago).

| Cuerpo | Fuente | Variable | Usada por |
|---|---|---|---|
| Tierra | NASADEM (30 m) y Copernicus GLO-90 | Elevación, pendiente, rugosidad | Marco, Santiago |
| Tierra | MODIS MOD11C3 / MOD11A1 | Temperatura superficial | Marco, Santiago |
| Tierra | MODIS MCD43C3 | Albedo | Marco |
| Tierra | GPM IMERG / CHIRPS | Precipitación | Marco / Santiago |
| Tierra | MODIS MOD13C2 / MOD13Q1 | Vegetación (NDVI) | Marco / Santiago |
| Tierra | ASTER GED | Emisividad (tipo de roca) | Marco |
| Tierra | ESA WorldCover 2021 | Cobertura del suelo | Santiago |
| Tierra | Sentinel-2 L2A | Reflectancia, índices de óxidos de hierro e hidroxilos | Santiago |
| Tierra | NASA POWER | Clima del aire y radiación solar | Santiago |
| Tierra | EMIT L2B (EMITL2BMIN) | Mineralogía (pendiente de procesar) | Santiago |
| Tierra | Sentinel-2 L2A (Microsoft Planetary Computer) | Imágenes de cerca en la app (no entran en el puntaje) | Web |
| Luna | LRO LOLA (LDEM 80 m polar, 5 m en sitios de Artemis) | Elevación, pendiente, rugosidad, albedo | Marco, Santiago |
| Luna | LRO Diviner PRP | Temperatura media y máxima | Marco |
| Marte | HRSC + MOLA blend (200 m, USGS) | Elevación, pendiente, rugosidad | Marco, Santiago |
| Marte | MGS TES | Albedo | Marco |
| Marte | Mars Climate Database v6.2 (LMD) | Temperatura superficial (modelo) | Marco |
