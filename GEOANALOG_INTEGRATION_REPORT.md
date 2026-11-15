# GeoAnalog — Informe de integración científica, computacional y funcional

**Fecha del corte:** 15 de noviembre de 2026, America/Bogota.  
**Rama local:** `feature/colombia-scientific-integration`.  
**Estado:** implementación y datos generados completos; pruebas completadas. Santiago autorizó posteriormente crear el commit y publicar `feature/colombia-scientific-integration` en `origin` para revisión del equipo. El commit de publicación puede consultarse en el historial de esa rama. No se integra esta entrega en `main` ni se realiza un despliegue en Azure.

**Revisión previa a la publicación:** la rama remota de integración todavía no existía. `main` remoto había avanzado a `875187a4210227e08b215e18927ee8eba1e13d9a`; esta publicación conserva la base auditada `58313dc` y no incorpora ni sobrescribe ese avance. Antes de un futuro merge se deberá revisar la diferencia con el `main` vigente.

Este documento describe la versión unificada que conecta la investigación global de Marco, la interfaz de Sebastián y los productos regionales de Santiago. Sirve como registro de revisión y contexto para preparar la presentación del equipo. Las cifras de similitud son resultados de modelos exploratorios; no constituyen certificaciones de emplazamientos para una base espacial.

La identidad de los integrantes fue confirmada expresamente por Santiago:

| Integrante | GitHub confirmado | Contribución utilizada |
|---|---|---|
| Marco | [Mabeltranpe1](https://github.com/Mabeltranpe1) | Investigación global, adquisición, comparador y ampliación de la base terrestre. |
| Sebastián | [Ssalazarp420](https://github.com/Ssalazarp420) | Interfaz React/Cesium, mapas, navegación, comparación y visualización. |
| Santiago | [santiago-851](https://github.com/santiago-851) | Investigación detallada de Colombia, topografía comparada, PAI y productos científicos complementarios. |

La identificación de cuentas no acredita por sí misma nacionalidad, afiliación o autoría exclusiva de cada línea histórica. La cooperación internacional demostrable en los productos procede de NASA, ESA, USGS, universidades y SGC; no se infieren nacionalidades de los integrantes. El informe técnico anterior se conserva como evidencia histórica y debe leerse con esta corrección de identidades.

## 1. Estado inicial del repositorio

El directorio de trabajo es `C:\Users\santi\Desktop\SpaceApps`. Inicialmente estaba en `recovery/original-project`, commit `aaf4ebb411e2005b159f90e7c078c81f8d93be6e`, con la ciencia regional de Santiago. El único cambio inicial identificado era el documento sin seguimiento [GEOANALOG_TECHNICAL_REPORT.md](GEOANALOG_TECHNICAL_REPORT.md), producido por la auditoría anterior. Se preservó sin modificar sus 434.123 bytes.

Existía además un clon independiente dentro de `NASA_SPACE_APPS_2026/`, en `513ada5593274b71549984ac9c3ab13aeb6b73d2`. No se utilizó como fuente vigente ni se modificó. Se excluye del seguimiento de la integración para evitar incorporar accidentalmente un repositorio anidado.

El diagnóstico confirmó la diferencia de bases detectada en la auditoría: la aplicación de `main` utilizaba 163.998 celdas de 43 regiones, mientras que Marco tenía un gzip con 691.035 celdas de 727 regiones. También coexistían dos contratos JSON incompatibles, `comparisons.json` y `analogos.json`, y una caracterización web resumida que no publicaba toda la ciencia regional.

Tras actualizar las referencias remotas, se encontró un cambio adicional de Marco: `e75ecdb` ya había corregido las rutas de sus pipelines para utilizar `earth_all.csv.gz`. Esa corrección pertenece a Marco. La integración conecta esa base ampliada con el exportador y los consumidores de la interfaz de Sebastián.

El procedimiento seguido fue: inspección de ramas y entradas; conservación de datos de origen; creación de una rama desde `origin/main`; incorporación selectiva; contrato científico separado de las celdas globales; exportación completa; pruebas de preservación, cálculo y navegador. No se ejecutaron descargadores masivos ni se reconstruyeron los productos nativos planetarios.

## 2. Ramas y commits utilizados

Repositorio de procedencia: [Mabeltranpe1/NASA_SPACE_APPS_2026](https://github.com/Mabeltranpe1/NASA_SPACE_APPS_2026).

| Referencia | Commit del corte | Uso |
|---|---|---|
| `origin/main` | `58313dc9db0c9a7a58f9d12ace0bd9a0ce30e6ba` | Base funcional, release 0.4.2 de la interfaz. |
| `origin/develop` | `b58172530bcc7af595dc0f5c3e983b076e059513` | Inspección del estado de desarrollo; no fue la base de trabajo. |
| `origin/feature/compare_analysis` | `e75ecdb583d26223cc57ceae142672492f5282aa` | Comparador, entradas globales ampliadas, rankings y composición de Marco. |
| `origin/feature/planetary-analysis` | `aaf4ebb411e2005b159f90e7c078c81f8d93be6e` | Ciencia regional de Santiago. Coincide con `recovery/original-project`. |
| `feature/planetary-analysis`, local | `15805610f8b61049a46dbd62e8537f9e57da17dd` | Referencia local anterior conservada; no confundida con la remota actual. |
| `recovery/github-src` | `a8cdd153a000f4ac3c5c30da118a12214d806f21` | Recuperación previa conservada. |
| `feature/colombia-scientific-integration` | Creada sobre `58313dc9db0c9a7a58f9d12ace0bd9a0ce30e6ba` | Rama de esta implementación; commit de publicación en su historial, revisión del equipo pendiente. |

`git fetch origin` se ejecutó antes de seleccionar las fuentes; la rama de Marco avanzó desde `cc8f849` hasta `e75ecdb`. No se alteraron los punteros de las ramas originales. La rama nueva no tiene upstream configurado hacia `main`, para evitar un destino de publicación accidental.

Los commits fuente están registrados en [src/science_metadata.py](src/science_metadata.py), en los JSON generados y en los manifiestos de referencia. La selección por archivo preserva la interfaz de `main`; no es un merge completo de las historias de las ramas científicas.

## 3. Archivos incorporados de cada integrante

La procedencia se distingue de las adaptaciones de integración. Un archivo compartido puede tener historia de varios integrantes; la atribución siguiente identifica la rama fuente utilizada.

| Fuente | Archivos y productos principales |
|---|---|
| Marco, `e75ecdb` | `data/earth_all.csv.gz`, catálogo ampliado, objetivos terrestres/planetarios, `data/top200_analogos.{csv,json}`, resultados globales, descubrimientos, temporadas y composición. Módulos `compare.py`, `build_database.py`, `build_earth.py`, `build_mars_targets.py`, `build_moon_targets.py`, `make_results.py`, `make_top_analogos.py`, `composition.py` y auxiliares. `docs/COMPOSICION.md`. |
| Sebastián, `58313dc` | Aplicación `web/`, Cesium, navegación, catálogo `sites.ts`, controles, exportador de comparación, imágenes, galerías y pruebas existentes. La interfaz se amplía sobre esos componentes. |
| Santiago, `aaf4ebb` | Todo `data/features/`, resultados PAI, matriz y parámetros de normalización, 18 DEM pequeños, 18 figuras de análisis, seis series NASA POWER, GeoJSON geológico y módulos de extracción/adquisición regional. `docs/GeoAnalog_CONTEXTO_TECNICO.md` y `data/raw/moon/README`. |

Se incorporaron inicialmente 107 archivos de la rama de ciencia regional y 78 de la rama global. Dos módulos regionales incorporados, `extract_features.py` y `similarity.py`, se adaptaron después para ejecución explícita y pruebas sin efectos de importación. El manifiesto [santiago_source_manifest.json](data/reference/santiago_source_manifest.json) enumera **105 archivos presentes byte a byte** respecto al commit de Santiago; [marco_source_manifest.json](data/reference/marco_source_manifest.json) enumera **78** respecto al de Marco. Son fotografías de equivalencia de contenido, no listas de autoría exclusiva ni sumas de archivos únicos entre ambas ramas.

La implementación conserva además:

- La base anterior `data/earth_all.csv`, como referencia histórica; no es la entrada activa.
- **42 archivos** de referencia en `data/archive/integration-main/`: 26 entradas/tablas originales de `main`, su `comparisons.json` y 15 mapas de similitud anteriores.
- El contrato histórico de Marco, intacto, en `data/reference/marco_analogos.json` y `web/public/data/analogos.json`.
- Las fuentes originales en Git, con sus commits y ramas sin sobrescribir.

Las pruebas verifican por contenido los CSV, resultados, figuras, DEM y series regionales, la base gzip y el top 200 de Marco. Ningún CSV científico original se editó para ajustarlo al esquema de la interfaz.

## 4. Correspondencia entre variables y modelos matemáticos

La correspondencia completa de **445 campos/cuerpos** se entrega en [SCIENTIFIC_VARIABLE_MAPPING.md](docs/SCIENTIFIC_VARIABLE_MAPPING.md) y [variables.json](web/public/data/science/variables.json). Para cada campo se registra archivo y columna original, nombre en la aplicación, definición, unidad, fuentes, soporte, periodo, método, calidad/cobertura y posible contraparte global. La conversión registrada es `none; original value retained`.

El adaptador no introduce equivalencias a partir de nombres parecidos:

| Producto regional | Variable global relacionada | Decisión científica |
|---|---|---|
| Media y dispersión de elevación del DEM de 10 km | `elev_m` de una celda de 0,05° | Soporte diferente; los datums verticales tampoco son equivalentes entre cuerpos. Se conservan ambas. |
| Pendiente media y percentiles a 200 m | `slope_deg` | Misma dimensión física, distinta huella y agregación; no reemplazar automáticamente. |
| TRI de Riley, m | `roughness`, desviación local de alturas, m | Definiciones distintas. Compartir unidad no permite sustituir una por otra. |
| TPI y su dispersión, m | Sin contraparte directa | Descriptor regional independiente. |
| Temperatura del aire POWER, °C | LST/modelos superficiales, K | Diferentes magnitudes; convertir unidades no resuelve la incompatibilidad. |
| LST MODIS regional día/noche | Media superficial global | Distintos producto, periodo, soporte y estimador. |
| Diferencias LST día/noche emparejadas | Amplitud global basada en máximo menos media | No equivalentes ni intercambiables con una resta de medias marginales. |
| CHIRPS anual medio 2021–2025 | GPM/MERRA-2 global | Productos, periodos y soportes separados. |
| Reflectancia e índices Sentinel-2 | ASTER GED / CF equivalente | Proxies diferentes; no estiman la misma composición. |
| Coincidencias EMIT / parámetros CRISM | Contraste de emisividad global | No convertir coincidencia espectral a abundancia, roca confirmada ni recurso. |
| TES, J m⁻² K⁻¹ s⁻¹/² | Temperatura | Inercia térmica `I=√(kρc)`; no es temperatura. |
| THEMIS IRPBT piloto | Temperatura cinética / amplitud diaria | Temperatura de brillo, banda no verificada y adquisiciones sin emparejar. |
| Estabilidad modelada de hielo Diviner PRP | Presencia o reserva de hielo | Modelo termofísico; no detección de hielo. |

Las definiciones regionales proceden de los extractores originales. A 200 m, la pendiente usa `atan(√(gx²+gy²))`; TRI es `√Σ(z_vecino−z_centro)²` sobre ocho vecinos; TPI es `z_centro−media(z_ocho_vecinos)`. Se exigen vecindarios completos para los derivados. Las pruebas reproducen los 25 estadísticos escalares de cada uno de los 18 DEM con tolerancia absoluta `5,01×10⁻⁶`, correspondiente al redondeo del CSV.

### 4.1 Comparador global y puntaje web

Para cada variable `f`, `d_f=[g_f(x_T)−g_f(x_P)]/τ_f`; `g=log(1+x)` para precipitación y es identidad para las demás. La similitud individual es `exp(−|d_f|)` y el puntaje compuesto:

```text
S = exp(−sqrt(Σ w_f d_f² / Σ w_f))
```

Referencia: [src/compare.py](src/compare.py), funciones `scale_together`, `score_cells` y `build_weights`. La configuración base del módulo es distinta de la configuración usada para publicar estos resultados: se especifica elevación 0 y emisividad equivalente 0,5.

| Variable global | Tolerancia `τ` | Peso publicado antes de exclusiones web |
|---|---:|---:|
| Elevación, m | 1.000 | 0 |
| Pendiente, grados | 5 | 1 |
| Rugosidad local, m | 5 | 1 |
| Temperatura superficial media, K | 30 | 1,5 |
| Amplitud térmica global, K | 30 | 1 |
| Albedo | 0,10 | 1 |
| Precipitación, `log1p(mm)` | 1 | 1 |
| NDVI | 0,10 | 1 |
| Contraste de emisividad | 0,03 | 0,5 |

El **índice global completo de Marco**, escala 0–1, conserva las ocho dimensiones activas, el top 100 por cuerpo y la separación original de 300 km. La media lunar excluye el piso sombreado de Shackleton. Sus resultados originales no se recalculan para adaptarlos a la web.

El **puntaje web de dimensiones comparables**, también 0–1, utiliza esa ecuación y la política previa de Sebastián: excluye una variable por cuerpo si la mediana de sus objetivos está fuera del rango terrestre por más de una tolerancia. En esta exportación ampliada quedan excluidas `temp_mean_K` y `temp_range_K` para la Luna; **no queda ninguna exclusión adicional para Marte**. Esto difiere de la base pequeña anterior y está registrado en cada objetivo. El modo web «Relieve» es una restricción del comparador global; no es el PAI regional.

La sensibilidad web usa 100 variaciones de pesos uniformes entre 0,5 y 1,5 veces su valor, semilla 0 y permanencia en el top 500 de celdas. Los empates respetan el orden estable original. Es sensibilidad a decisiones de ponderación; no es incertidumbre instrumental ni probabilidad de equivalencia física. Reponderar en el navegador solo reordena sitios exportados, sin explorar de nuevo las 691.035 celdas ni recalcular esa sensibilidad.

### 4.2 PAI topográfico regional

El PAI conserva el modelo de Santiago, sin añadir clima o mineralogía:

```text
z_f = (x_f − μ_f,Tierra) / σ_f,Tierra       σ poblacional, ddof=0
d(A,B) = sqrt(Σ w_f (z_A,f − z_B,f)²)
PAI(A,B) = 100 / (1 + d(A,B))
```

| Descriptor a 200 m | Peso | Media Tierra | Desviación Tierra |
|---|---:|---:|---:|
| Relieve P90−P10, m | 0,15 | 488,6421916667 | 347,1831457138 |
| Desviación de elevación, m | 0,15 | 181,659135 | 127,8238618744 |
| Pendiente media, grados | 0,15 | 9,3124283333 | 5,9725873852 |
| Pendiente P90, grados | 0,15 | 15,295275 | 9,4113483822 |
| TRI medio, m | 0,15 | 91,4572383333 | 58,0496190715 |
| Desviación del TPI, m | 0,25 | 13,7510866667 | 7,6632720209 |

Los parámetros exactos están en [normalization_parameters.csv](data/results/normalization_parameters.csv). La normalización depende de seis candidatos colombianos; no representa una población mundial. Las seis variables tienen correlaciones topográficas y no son seis observaciones independientes. Un valor PAI de 92 no significa «92 % de equivalencia física». Los 72 pares, su precisión original, distancias y matriz de 18×18 se mantienen separados de los dos puntajes exponenciales.

## 5. Criterios de prioridad de fuentes

1. **Conservación:** una entrada original identificada por commit prevalece sobre una transcripción, un valor de demostración o un resumen redondeado. Los ausentes permanecen `null`; cero y `false` se preservan.
2. **Caracterización de las seis ventanas colombianas:** el panel detallado utiliza las observaciones regionales de Santiago y muestra sus fuentes, fechas y cobertura. Sus valores no se escriben sobre `sites[].values` del comparador global.
3. **Búsqueda mundial:** se conserva la celda de Marco y su metodología. No se sustituye una celda angular por una media regional, ni se eliminan las demás celdas de Colombia. Hay 79.791 celdas de la región global `northern_andes` preservadas; esa etiqueta regional no es un límite administrativo de Colombia.
4. **Objetivos planetarios:** se exige coincidencia de cuerpo e intersección geométrica positiva. Las ventanas regionales y los anillos/discos globales siguen siendo soportes distintos, incluso si se solapan.
5. **Naturaleza de la evidencia:** medición, clasificación, estimación de cuadrícula, inversión termofísica, modelo y proxy bibliográfico se identifican por separado. El origen NASA no convierte automáticamente una variable modelada en una observación directa.
6. **Calidad antes que completitud aparente:** cobertura insuficiente, error geométrico y bandas no verificadas siguen visibles. No se rellenan para obtener una ficha completa.

La atribución confirmada se publica tanto en los metadatos como en la página Método. No se asignan a los integrantes los cambios de adaptación realizados durante esta integración como si fueran resultados científicos originales suyos.

## 6. Datos científicos integrados y resultados verificables

### 6.1 Alcance efectivo

| Producto | Cantidad verificada |
|---|---:|
| Base terrestre activa | 691.035 celdas únicas por latitud/longitud; 727 regiones |
| Objetivos globales | 15: seis lunares y nueve marcianos |
| Sitios enviados al comparador web | 274: 16 de catálogo y 258 de descubrimiento |
| Ranking internacional original | 200 filas, 100 por cuerpo, 39 columnas originales conservadas |
| Estudios regionales | 18: seis terrestres, seis lunares y seis marcianos |
| Comparaciones regionales Tierra–objetivo | 72 |
| Matriz PAI original | 18×18, 324 valores reproducidos |
| Correspondencias de campo/cuerpo | 445 |
| Tipos de sección regional | 18; cada ficha terrestre tiene 11 |
| Artefactos originales publicados para consulta/descarga | 85, con SHA-256 |
| Mapas de similitud global | 15 JSON de 2.500 puntos cada uno |

### 6.2 Colombia

Las seis regiones son Tatacoa, La Guajira, La Candelaria, Nevado del Ruiz, Nevado Santa Isabel y Volcán Puracé. Cada una expone topografía, POWER, ambiente, Sentinel-2, cobertura y unidades SGC, disponibilidad EMIT, aceptación/cobertura EMIT, coincidencias por biblioteca y resultados/calidad por adquisición. Las figuras incluyen elevación absoluta y relativa, pendiente, TRI, TPI y orientación.

Ejemplos numéricos, redondeados solo en esta tabla; los archivos y JSON mantienen los valores de origen:

| Región | Relieve P90−P10, m | Pendiente media, ° | TRI medio, m | Aire POWER, °C | LST diurna, °C | CHIRPS anual medio, mm/año | Agua WorldCover, % |
|---|---:|---:|---:|---:|---:|---:|---:|
| Tatacoa | 77,88781 | 2,17971 | 22,56462 | 20,33373 | 35,91822 | 1.449,64570 | 0,00040 |
| La Guajira | 34,10956 | 0,65947 | 7,38358 | 27,75910 | 33,41788 | 301,96109 | 47,92280 |
| La Candelaria | 418,97878 | 9,58461 | 92,98506 | 15,75817 | 24,85390 | 1.125,66225 | 0,00152 |
| Nevado del Ruiz | 980,04106 | 16,75431 | 163,48794 | 16,43417 | 15,75828 | 2.083,35242 | 0,04225 |
| Nevado Santa Isabel | 670,39976 | 13,70199 | 136,65770 | 16,43417 | 17,32188 | 2.078,43559 | 0,54254 |
| Volcán Puracé | 750,43618 | 12,99448 | 125,66453 | 14,83502 | 16,72251 | 1.861,19680 | 0,00192 |

Fuentes directas: [planetary_features.csv](data/features/planetary_features.csv), [climate_features.csv](data/features/climate_features.csv) y [environmental_features.csv](data/features/environmental_features.csv). La temperatura POWER corresponde a una cuadrícula gruesa asociada al punto; los valores idénticos de los dos nevados no son dos estaciones independientes de cumbre. La lluvia de Tatacoa no debe descartarse por una expectativa sobre el nombre «desierto»: es el resultado del producto, periodo y huella incluidos y exige interpretar su representatividad.

Se conservan seis series diarias POWER de 1.826 días, periodo 2021–2025; ambiente 2021–2025; WorldCover 2021; Sentinel-2 2025; y cartografía SGC 2023 a 1:500.000. Hay 16 registros de unidades geológicas y sus polígonos originales. Las huellas de GEE, del DEM y de la cuadrícula POWER no se presentan como una única geometría.

EMIT conserva 222 registros agregados, 12 registros de cobertura por región/grupo, 305 resultados por escena y 36 registros de calidad por escena/grupo. Las coincidencias aceptadas usan profundidad ≥0,02, profundidad ≥2×incertidumbre y ajuste almacenado ≥0,20; el ajuste corregido se obtiene por ×2. Son coincidencias provisionales; Puracé conserva un muestreo parcial de dos adquisiciones. Las fracciones son de observaciones y pueden acumular ubicaciones repetidas entre fechas; no son porcentajes exclusivos de superficie ni concentración mineral.

### 6.3 Productos planetarios

Marte conserva Jezero, Gale, Pathfinder, Viking 1, Viking 2 y Phoenix: topografía, TES, THEMIS resumido y por escena, CRISM primario, calidad geométrica y parámetros de todas las coberturas. Se publican seis resúmenes TES, 148 registros de celdas TES, 12 resúmenes THEMIS y 36 registros THEMIS por escena. CRISM mantiene 72 registros de parámetros y 63 registros primarios/resumidos, incluidos nueve ausentes explícitos de Phoenix.

La Luna conserva Shackleton Rim, Connecting Ridge, De Gerlache Rim, Leibnitz Beta Plateau, Malapert Massif y Peak Near Shackleton. Se publican topografía y Diviner PRP, seis resúmenes y 5.079 facetas originales, con coberturas y estados de profundidad. La estabilidad superficial modelada en Shackleton Rim es 1,22878 % de su ventana: no demuestra presencia de hielo.

### 6.4 Los mejores PAI originales entre seis candidatos

| Objetivo regional | Candidato con mayor PAI | PAI |
|---|---|---:|
| Marte · Pathfinder | Tatacoa | 92,02119 |
| Marte · Phoenix | La Guajira | 87,62343 |
| Marte · Viking 2 | La Guajira | 87,13699 |
| Marte · Viking 1 | La Guajira | 86,50315 |
| Marte · Gale | Tatacoa | 84,15752 |
| Marte · Jezero | Tatacoa | 83,87904 |
| Luna · Connecting Ridge | La Candelaria | 55,95991 |
| Luna · Peak Near Shackleton | La Candelaria | 53,81568 |
| Luna · Leibnitz Beta Plateau | Volcán Puracé | 53,54678 |
| Luna · De Gerlache Rim | Volcán Puracé | 48,64029 |
| Luna · Malapert Massif | Volcán Puracé | 46,53239 |
| Luna · Shackleton Rim | Nevado del Ruiz | 24,00652 |

Fuente: [analog_ranking.csv](data/results/analog_ranking.csv). Rango de los 72 pares: 16,51150–92,02119. El primer puesto es relativo a estos seis candidatos y estos descriptores; La Guajira incluye agua sin máscara marina en el análisis original.

### 6.5 Ranking global original

El primer lugar lunar de Marco es `greenland_82n_038w`, celda 82,075° N / 36,225° O, media completa 0,0485 y mejor objetivo de Gerlache rim con 0,0619. El primer lugar marciano es `egypt_western_desert`, 25,325° N / 29,625° E, media 0,1959 y mejor objetivo Chryse Planitia/Viking 1 con 0,2235. Estos valores bajos incluyen límites ambientales que el puntaje web puede excluir; no se transformaron para hacerlos coincidir con el PAI.

Fuente: [top200_analogos.csv](data/top200_analogos.csv). Las pruebas recalculan sus medias con las variables publicadas y tolerancia `5,001×10⁻⁵`, acorde con los cuatro decimales del CSV original. El JSON conserva el orden y las 39 columnas y añade únicamente referencias de navegación.

### 6.6 Fuentes e instituciones

Las URL siguientes se conservan desde la procedencia de los productos y los módulos científicos. La integración utilizó archivos locales y no revalidó en línea cada catálogo ni descargó nuevas escenas. Los scripts y manifiestos originales contienen identificadores de producto más específicos; el informe técnico previo conserva el análisis bibliográfico extenso.

| Fuente | Institución y enlace | Naturaleza y producto integrado |
|---|---|---|
| NASADEM | NASA/LP DAAC, [NASADEM HGT 001](https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001) | DEM terrestre observado y derivado. |
| LOLA | NASA GSFC, [DEM de sitios polares](https://pgda.gsfc.nasa.gov/products/78) | DEM lunar y derivados. |
| MOLA/HRSC | NASA/ESA/USGS, [DEM combinado de Marte](https://astrogeology.usgs.gov/search/map/mars_mgs_mola_mex_hrsc_blended_dem_global_200m) | DEM combinado a 200 m. |
| POWER | NASA LaRC, [NASA POWER](https://power.larc.nasa.gov/) | Estimaciones de cuadrícula de aire, humedad, viento, presión y energía solar. |
| MODIS LST regional | NASA/LP DAAC, [MOD11A1.061](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD11A1) | Temperatura radiométrica superficial. |
| MODIS NDVI regional | NASA/LP DAAC, [MOD13Q1.061](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1) | Índice de vegetación derivado. |
| CHIRPS | UCSB, [CHIRPS diario](https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY) | Precipitación de cuadrícula. |
| WorldCover | ESA, [v200, 2021](https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v200) | Clasificación de cobertura terrestre. |
| Sentinel-2 | ESA/Copernicus, [MSI L2A armonizado](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED) | Reflectancia e índices; no mineralogía confirmada. |
| Geología | SGC, [Atlas 2023, capa 733](https://srvags.sgc.gov.co/arcgis/rest/services/Mapa_Geologico_Colombia/Mapa_Geologico_Colombia_V2023/MapServer/733) | Cartografía colombiana a 1:500.000. |
| EMIT | NASA/JPL/LP DAAC, [EMITL2BMIN.001](https://doi.org/10.5067/EMIT/EMITL2BMIN.001) | Coincidencias de biblioteca espectral provisionales. |
| CRISM | NASA/APL/PDS, [archivo CRISM](https://pds-geosciences.wustl.edu/missions/mro/crism.htm) | Parámetros espectrales MTRDR/MRDR4. |
| TES | NASA/PDS, [TIMAP](https://doi.org/10.17189/1519489) | Inversión de inercia térmica; interpolados excluidos. |
| THEMIS | NASA/ASU/PDS, [archivo THEMIS](https://pds-geosciences.wustl.edu/missions/odyssey/themis.html) | IRPBT piloto de temperatura de brillo. |
| Diviner | NASA/UCLA/PDS, [archivo Diviner](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm) | PRP v2, modelo termofísico polar. |

La base global conserva además MOD11C3, MCD43C3, MOD13C2, GPM/MERRA-2, ASTER GED, el modelo Mars Climate Database 6.2 y equivalentes CF bibliográficos. Sus referencias y calibraciones se documentan en [COMPOSICION.md](docs/COMPOSICION.md), [RECURSOS.md](RECURSOS.md), [build_earth.py](src/build_earth.py), [composition.py](src/composition.py) y el informe técnico. No se confunden MOD11C3 global y MOD11A1 regional, ni MCD con una medición de temperatura marciana.

## 7. Modificaciones en exportadores y pipelines

### 7.1 Contrato canónico de comparación

[src/export_web.py](src/export_web.py) mantiene el comparador de Marco y el contrato base de Sebastián. Su entrada por defecto es `data/earth_all.csv.gz`. `comparisons.json` pasa a versión **3**, conservando las estructuras consumidas por las comparaciones existentes y añadiendo procedencia, método, referencias regionales y URL del ranking internacional.

El exportador incorpora las celdas necesarias para abrir todos los lugares del top 200; falla si sus coordenadas no existen en la base. No limita la integración a un JSON guardado que ningún componente consume. Se publican 274 sitios con resultados contra los 15 objetivos y mapas de 2.500 puntos por objetivo. Las puntuaciones web se exportan a ocho decimales, sin alterar los resultados originales del ranking global ni del PAI.

La lectura de la marca de datos sintéticos reconoce gzip. La validación rechaza identificadores duplicados, referencias de objetivos rotas, JSON con números no finitos y una publicación científica marcada como sintética.

La sensibilidad reutiliza diferencias cuadráticas y calcula el umbral top 500 mediante partición, respetando empates estables. Mantiene todos los sorteos de las nueve dimensiones para conservar la secuencia aleatoria original. También evita conservar simultáneamente las matrices completas de similitudes de los 15 objetivos. Una prueba compara el procedimiento optimizado con el algoritmo estable de referencia, incluyendo empates y ausencias. No se realizó un benchmark controlado de tiempo/memoria ni se afirma una aceleración numérica específica.

### 7.2 Catálogo científico regional

Nuevos [src/scientific_catalog.py](src/scientific_catalog.py), [src/science_metadata.py](src/science_metadata.py) y [src/export_science.py](src/export_science.py):

- Leen los resultados existentes sin ejecutar adquisición, extracción nativa ni cambiar entradas.
- Construyen 18 documentos regionales versión `1.0.0`, índice, catálogo de variables y GeoJSON regionales derivados.
- Comprueban las identidades regionales y los 72 pares PAI; mantienen resultados, distancia, precisión y rango entre seis candidatos.
- Copian 85 artefactos originales bajo `science/files/data/`, con tamaño y SHA-256. Los DEM pequeños están incluidos; los insumos nativos de gran volumen no.
- Publican flags bilingües de calidad, tipo de evidencia, método, fechas, resolución y soporte.
- Enlazan las ventanas planetarias desde los pares PAI, aunque no exista un objetivo global coincidente.

`src/export_science.py` permite reexportar solo la ciencia regional. `src/export_web.py` ejecuta también ese adaptador para producir el conjunto coherente completo.

### 7.3 Asociaciones geográficas

`footprint_association` intersecta el disco/anillo global y la ventana del DEM regional, en el CRS del estudio y dentro del mismo cuerpo. No asocia por nombre ni interpola valores. Las fracciones de esta aproximación plana son:

| Objetivo global → estudio | Ventana regional cubierta, % | Objetivo global cubierto, % |
|---|---:|---:|
| Shackleton rim → Shackleton Rim | 43,428159 | 14,357751 |
| de Gerlache rim → De Gerlache Rim | 68,576216 | 9,273652 |
| Jezero → Jezero | 100 | 31,831788 |
| Gale → Gale | 100 | 31,831788 |
| Chryse/Viking 1 → Viking 1 | 100 | 31,831788 |
| Utopia/Viking 2 → Viking 2 | 100 | 31,831788 |
| Vastitas Borealis/Phoenix → Phoenix | 100 | 31,831788 |

Son siete asociaciones positivas, no siete soportes idénticos. Haworth, Faustini, Mons Mouton, Shackleton floor, Elysium, Meridiani, Gusev y Arcadia no reciben productos regionales por una coincidencia nominal. Los demás estudios se consultan por el PAI. La intersección sirve para navegación y contexto; no es una nueva validación de coregistro instrumental.

### 7.4 Compatibilidad histórica y seguridad de reconstrucción

[src/export_analogos.py](src/export_analogos.py) reproduce byte a byte el contrato histórico de Marco desde `data/reference/marco_analogos.json`. Su antiguo exportador dependía de archivos experimentales que no están incluidos. La implementación original sigue en Git, `e75ecdb:src/export_web.py`; no se presenta la restauración de su fotografía como una nueva corrida global.

`comparisons.json` v3 es el contrato canónico de la app unificada; `global-rankings.json` y la ciencia regional son complementos versionados. El frontend no entrega `analogos.json` a componentes con otro esquema. Véase [SCIENTIFIC_DATA_CONTRACT.md](docs/SCIENTIFIC_DATA_CONTRACT.md).

Se añadieron guardas `main` a `similarity.py`, `extract_features.py` y `extract_climate.py`, evitando procesamiento o consultas por importarlos. La extracción topográfica permite `save_figure=False` y el PAI recibe pesos explícitos al usar dimensiones activas. Los algoritmos se conservan y se verifican contra sus resultados publicados. Otros descargadores originales pueden mantener efectos al ejecutarse; no se importan ni invocan desde la exportación científica.

`build_database.merge` ahora rechaza una reconstrucción incompleta antes de sustituir el gzip y escribe el resultado completo mediante archivo temporal y reemplazo. El repositorio no contiene los CSV intermedios de todas las 727 regiones; reconstruir únicamente los presentes habría reducido accidentalmente la base publicada. La prueba correspondiente demuestra que una entrada incompleta deja intacto el archivo existente.

## 8. Modificaciones en la interfaz

La aplicación conserva su estructura React/Cesium y diseño. No se reconstruyó desde cero.

| Componente | Cambio y finalidad |
|---|---|
| `web/src/data/comparisons.ts` | Acepta versiones 2/3 y las referencias científicas; rechaza muestras sintéticas y duplicados. |
| `web/src/data/science.ts` | Tipos del contrato regional y ranking; validación básica y carga diferida con caché por documento. |
| `ScientificPanel.tsx` | Panel desplegable, pestañas de productos, valores originales, calidad persistente, metadatos por variable, fuentes, descargas, figuras y PAI. |
| `GlobalRankings.tsx` | Consume el top 100 lunar y marciano original; muestra escala y método y abre cada celda en los controles existentes. |
| `SiteCard.tsx` y `App.tsx` | Integran el panel regional en las seis fichas y en Análisis; añaden el ranking internacional cuando no hay una selección activa. |
| `ComparisonPanel.tsx` | Añade estudios planetarios solo mediante referencias de solapamiento, explicando la diferencia de huella. |
| `MethodView.tsx` | Distingue los tres resultados, corrige atribuciones y afirmaciones demasiado amplias de cobertura/validación, y mantiene límites físicos. |
| `IntroOverlay.tsx` | Presenta las cifras efectivas de la base y evita afirmar que se ha observado toda la Tierra. |
| `App.css`, `i18n/science.ts`, `i18n/strings.ts` | Adaptaciones de diseño, tablas desplazables, pestañas y textos ES/EN. |

Cada ficha terrestre dispone de 11 secciones científicas y una pestaña PAI con sus 12 comparaciones. Los datos extensos tienen controles para desplegar todas las observaciones. Los detalles de procedencia acompañan cada variable. Los flags de calidad no dependen de que el usuario abra una tabla técnica.

Las figuras PNG originales se cargan bajo demanda. Sentinel-2 añade una gráfica de bandas discretas; sus barras no representan un espectro continuo ni una identificación mineral inequívoca. Las imágenes y carruseles existentes mantienen su función ilustrativa.

La interfaz ofrece nombres y textos de método ES/EN; identificadores de columnas, códigos de calidad y etiquetas originales de catálogo pueden conservar el idioma del archivo fuente para preservar trazabilidad. El frontend recibe subconjuntos y documentos regionales, nunca la tabla global completa de 691.035 filas.

## 9. Productos disponibles en la aplicación

| URL pública local | Consumidor / contenido | Tamaño del corte |
|---|---|---:|
| `/data/comparisons.json` | Comparador y navegación: versión 3, 274 sitios, 15 objetivos, `synthetic=false`. | 1.435.751 bytes |
| `/data/global-rankings.json` | Ranking internacional original y referencias de navegación. | 199.942 bytes |
| `/data/heatmap/*.json` | 15 capas existentes de similitud. | 817.883 bytes en total |
| `/data/science/index.json` | 18 estudios, modelo, equipo, asociaciones y manifiesto. | Incluido en el conjunto científico |
| `/data/science/variables.json` | 445 correspondencias de campos/cuerpos. | Incluido en el conjunto científico |
| `/data/science/{earth,moon,mars}/*.json` | Documentos de estudio cargados al abrir sus paneles. | 18 documentos |
| `/data/science/earth/*.geojson` | Seis recortes geológicos derivados. | Seis archivos |
| `/data/science/files/data/...` | Tablas, figuras, series y DEM originales. | 85 artefactos |
| `/data/analogos.json` | Contrato histórico conservado; no es la fuente canónica del comparador unificado. | 164.627 bytes |

El directorio científico contiene 111 archivos y 14.012.385 bytes. Esa cifra describe activos estáticos, no una carga inicial: documentos, imágenes y descargas se solicitan según la navegación. Los 18 documentos de estudio suman 4.429.514 bytes; parte del tamaño procede de repetir metadatos para que cada documento sea autocontenido.

Rutas de demostración:

- `http://127.0.0.1:5173/?site=tatacoa&view=analysis&lang=es`
- `http://127.0.0.1:5173/?site=la-guajira&view=analysis&lang=es`
- `http://127.0.0.1:5173/?site=volcan-purace&view=analysis&lang=en`
- `http://127.0.0.1:5173/?view=analysis&lang=en` para consultar el ranking internacional sin selección.

### 9.1 Huellas de preservación

| Archivo | SHA-256 |
|---|---|
| `data/earth_all.csv.gz` | `d7c61ad14fdf6b2ead58295bbb0bc093968478896e93504e91431298b9f1ef1a` |
| `data/top200_analogos.csv` | `9f8dff15bb2a9343c913782b5d786e168a6242e54fea7f5d227fce529dd092c7` |
| `data/results/analog_ranking.csv` | `de0d7415ebdc702b33ee01dc3a11a5498a38f15ecad57faf86b5d7c6a36ed417` |
| `data/features/planetary_features.csv` | `f3756a1bd3a7b4f396bda34aae9bcd4c0def5a8a7780f7b2b589c157ffa8ac0c` |
| `GEOANALOG_TECHNICAL_REPORT.md` | `7c0b65bd84e2edf3e764989658f3f08e018e00c49af050ec818119544b501f94` |

El manifiesto de `science/index.json` entrega además el hash de cada uno de los 85 artefactos publicados. Las fechas de generación pueden variar al reexportar; la preservación científica se comprueba en entradas y valores, no en la igualdad binaria de un JSON con fecha nueva.

## 10. Pruebas ejecutadas y resultados

Entorno efectivo: Windows/PowerShell; Python **3.14.6** en `.venv`, pytest **9.2.0**; Node **24.22.1**; Vite **8.3.8**; Playwright **1.65.1**, con Edge ya instalado. Los archivos de entorno siguen recomendando Python 3.12 para una instalación nueva. No se afirma haber validado todas las combinaciones de versiones.

| Comprobación ejecutada | Resultado final | Alcance |
|---|---|---|
| `python -B -m pytest -q -p no:cacheprovider tests` | **50 pruebas superadas**, 8,31 s en la última ejecución | 26 existentes y 24 casos de integración, incluidos parámetros. |
| `npm run lint` | Código de salida 0, sin incidencias | Lint del frontend. |
| `npm run build` | Código de salida 0 | `tsc -b` y producción Vite; 1.673 módulos, 342 elementos estáticos copiados. |
| `npm run test:e2e` | **4 pruebas superadas**, 30,4 s | Navegador real con interfaz y archivos científicos locales. |
| Exportación completa, 100 variaciones de sensibilidad | Completada | Base real 691.035/727, 15 objetivos, 274 sitios y 15 mapas. |
| Exportación científica independiente | Completada | 18 estudios, 72 pares y 85 artefactos. |
| Restauración del contrato histórico | Prueba superada | Coincidencia byte a byte con la fotografía fuente de Marco. |

Las pruebas Python adicionales, [test_scientific_integration.py](tests/test_scientific_integration.py), comprueban:

- Igualdad de insumos regionales respecto a `aaf4ebb` y del gzip/top 200 respecto a `e75ecdb`; conservación de la base anterior y de las 79.791 celdas `northern_andes`.
- Unicidad de coordenadas y conteos reales de regiones; seis fichas autoritativas con 11 secciones; 18 estudios en total.
- Los 72 PAI y distancias originales; reproducción exacta de los 324 valores de la matriz; extracción de todos los DEM sin escribir nuevas figuras.
- Ausente frente a cero/booleano; rechazo de valores JSON no finitos, duplicados, datos sintéticos y referencias rotas.
- Agua de Guajira y ausencia de máscaras EMIT; Puracé parcial; CRISM Phoenix ausente; TES Phoenix con cobertura diurna inferior al 80 %; hielo lunar etiquetado como modelo.
- Asociaciones geométricas válidas y rechazo de coincidencias nominales lejanas o de otro cuerpo.
- Metadatos de compatibilidad, unidades, calidad, métodos y fuentes; existencia de referencias y verificación SHA-256 de artefactos.
- Conexión de los 200 lugares originales con el comparador, preservación/reproducción de sus medias y equivalencia de la sensibilidad optimizada.
- Rechazo de una reconstrucción parcial que pudiera sobrescribir la base ampliada.

Las pruebas [scientific-integration.spec.ts](web/tests/scientific-integration.spec.ts), con [playwright.config.ts](web/playwright.config.ts), verifican:

1. Las seis fichas colombianas en español, los 12 pares PAI de cada una, clima, EMIT, advertencia de agua, comparador existente y ausencia de errores JavaScript durante ese recorrido.
2. La ficha en inglés, carga efectiva de la figura original y navegación PAI hacia Phoenix con CRISM no calificado.
3. El ranking 691.035/727, expansión a 100 filas por cuerpo, selección de un lugar nuevo, comparación, retorno al globo, leyenda de 2.500 celdas y canvas visible.
4. Los endpoints JSON reales, identificadores, `synthetic=false`, seis referencias científicas y valores de Tatacoa/PAI.

Las pruebas de navegador bloquean las solicitudes externas para aislar capas remotas: no simulan los JSON científicos ni las figuras locales. Validan la conectividad local del globo y sus controles, pero **no validan disponibilidad o contenido actual de tiles NASA, fotografías externas, geocodificación remota ni comportamiento visual en todos los dispositivos**. La aplicación se ejecutó localmente; no se probó un despliegue Azure.

El bundle principal de producción mide 4.551,96 kB, 1.235,27 kB gzip; CSS 63,67 kB. Es una limitación de carga relevante, en gran parte asociada a la aplicación Cesium existente. Una compilación correcta no equivale a una prueba de rendimiento de red o de GPU.

## 11. Limitaciones y trabajo científico pendiente

1. **Guajira costera:** 47,9228003989 % de agua WorldCover. El DEM/PAI y EMIT originales no aplican máscara marina. El resultado topográfico puede estar favorecido por superficies acuáticas planas. Se requiere una variante terrestre explícita antes de atribuir la analogía exclusivamente al terreno seco.
2. **EMIT provisional:** sin máscara L2A de nubes ni máscara marina; conteos de observaciones con repetición temporal, categorías no necesariamente exclusivas, Puracé parcial. No hay identificación mineral validada en campo ni estimación de recursos. No se transformó la cobertura de bins tocados en porcentaje de área válida.
3. **Sentinel-2 y geología:** índices espectrales son proxies; las unidades geológicas a 1:500.000 no son una cartografía litológica nueva a 200 m. Periodos y denominadores se mantienen separados.
4. **POWER y ambiente:** la cuadrícula gruesa puede representar mal cumbres o gradientes fuertes. Aire, LST de cielo despejado y modelo superficial planetario son magnitudes diferentes. No se incorporó una corrección altitudinal nueva ni se validó con estaciones.
5. **THEMIS:** banda sin verificar, escenas y estaciones no emparejadas, medias de escenas con igual peso. El resultado sigue siendo piloto; no se presenta como ciclo diurno, temperatura cinética o climatología comparable directamente con MODIS/MCD.
6. **CRISM Phoenix:** rechazo geométrico conservador de productos recuperados; nueve filas `no_qualified_observation`, con parámetros ausentes. Los inventarios y errores de recuperación se preservan. No se forzó una reproyección para producir valores aparentemente válidos.
7. **TES Phoenix:** cobertura diurna válida 79,60697 %, inferior al umbral exploratorio de 80 %. La inercia térmica de celdas nativas gruesas no se convierte en medición a 200 m.
8. **Diviner PRP:** modelo de temperaturas y estabilidad de hielo, con suposiciones de coregistro y censura de profundidad. El código `−32768` indica más allá del límite modelado de 2,8738 m; no es una profundidad física negativa ni evidencia de hielo presente.
9. **Modelos de similitud:** pesos y tolerancias son decisiones de diseño; falta validación externa para afirmar poder predictivo. El PAI depende de seis candidatos y descriptores correlacionados. No hay fusión metodológica nueva, propagación completa de incertidumbres ni validación de campo.
10. **Soportes y asociación:** celdas de 0,05° varían en anchura con latitud; los DEM regionales, huellas GEE, facetas y anillos planetarios no son equivalentes. El solapamiento plano es una asociación de navegación, no una homologación de resoluciones o geometrías nativas.
11. **Cobertura mundial y catálogo:** 727 regiones no cubren cada lugar de la Tierra. `lava-beds` permanece en el catálogo original pero no tiene celda cercana dentro del umbral de exportación; no se fabricó una puntuación. La búsqueda en el navegador está limitada a los sitios/puntos exportados.
12. **Reconstrucción nativa:** no se ejecutaron nuevas adquisiciones EMIT/CRISM/THEMIS ni procesamiento global desde HDF4/NetCDF. `h5py` y `pyhdf` no estaban disponibles en la `.venv` usada; su declaración se conserva y `netCDF4` se añade explícitamente. Los CSV intermedios de todas las regiones globales no están presentes. Reexportar los productos incluidos sí está verificado.
13. **Reproducibilidad de entorno:** dependencias Python sin bloqueo completo; validación ejecutada en 3.14.6, entorno recomendado 3.12 no reconstruido desde cero en esta sesión. Las ventanas/catálogos remotos y los modelos pueden actualizarse; deben fijarse versiones para una reproducción independiente de adquisiciones.
14. **Frontend y operación:** bundle Cesium grande; no se realizó una campaña de rendimiento, accesibilidad o navegadores/dispositivos. No se verificaron servicios remotos en las pruebas aisladas ni un despliegue cloud. La compilación local no garantiza capacidad de producción.
15. **Seguridad física de una base:** gravedad, radiación, vacío, presión, toxicidad, mecánica del regolito y viabilidad de construcción no se validan mediante estas similitudes. No se afirma que un lugar sea apto para una base permanente ni que reproduzca todo el ambiente lunar o marciano.

Estas limitaciones se incluyen en metadatos y paneles cuando corresponden al producto. No se ocultaron para mejorar las puntuaciones ni se atribuyó a los autores una nueva validación que no realizaron.

## 12. Inventario de archivos modificados e incorporados

El inventario siguiente se registró antes del commit de publicación: compara el árbol de trabajo con la base de esta rama, `58313dc`, y añade archivos nuevos no ignorados. Distingue modificaciones de archivos ya versionados y nuevas incorporaciones. No incluye cachés, `node_modules`, `.venv`, `dist`, trazas de navegador ni el clon anidado. Los archivos originales con diferencias únicamente de conversión CRLF/LF y sin diff lógico no se cuentan como cambios científicos.

`.gitattributes` conserva CSV/JSON/GeoJSON con LF y trata TIFF/PNG/gzip como binarios. `.gitignore` permite versionar los pequeños DEM y series necesarios, sin incorporar insumos nativos grandes ni credenciales. `requirements.txt` y `environment.yml` declaran `netCDF4`. Los cambios de `package.json`/lock añaden únicamente la herramienta y comando de pruebas de navegador.

`GEOANALOG_TECHNICAL_REPORT.md` figura como archivo nuevo porque ya estaba sin seguimiento al comenzar; **es preexistente y no fue modificado por esta integración**. Los dos manifiestos de referencia registran los archivos byte a byte de cada rama fuente. Los 85 artefactos copiados al área pública pueden enumerarse también en `web/public/data/science/index.json`.

**70 archivos versionados con cambios y 276 archivos nuevos no ignorados** en el corte de revisión. `M`: modificado respecto a la base; `A`: incorporado al árbol de trabajo, todavía sin seguimiento.

<details>
<summary>Inventario completo por ruta</summary>

```text
A .gitattributes
M .gitignore
A GEOANALOG_INTEGRATION_REPORT.md
A GEOANALOG_TECHNICAL_REPORT.md
M README.md
M data/README.md
A data/archive/integration-main/discovery_mars.csv
A data/archive/integration-main/discovery_mars_new.csv
A data/archive/integration-main/discovery_moon.csv
A data/archive/integration-main/discovery_moon_new.csv
A data/archive/integration-main/regions/antarctic_plateau.csv
A data/archive/integration-main/regions/axel_heiberg.csv
A data/archive/integration-main/regions/devon_island.csv
A data/archive/integration-main/regions/dry_valleys.csv
A data/archive/integration-main/regions/ellesmere_north.csv
A data/archive/integration-main/regions/iceland_highlands.csv
A data/archive/integration-main/regions/north_greenland.csv
A data/archive/integration-main/regions/prince_charles_mts.csv
A data/archive/integration-main/regions/svalbard.csv
A data/archive/integration-main/regions/transantarctic_mts.csv
A data/archive/integration-main/regions/victoria_island.csv
A data/archive/integration-main/regions_catalog.csv
A data/archive/integration-main/results_mars_new_per_region.csv
A data/archive/integration-main/results_mars_overall.csv
A data/archive/integration-main/results_moon_new_per_region.csv
A data/archive/integration-main/results_moon_overall.csv
A data/archive/integration-main/results_pairs_top20.csv
A data/archive/integration-main/seasons_mars.csv
A data/archive/integration-main/seasons_moon.csv
A data/archive/integration-main/targets.csv
A data/archive/integration-main/targets_mars.csv
A data/archive/integration-main/targets_moon.csv
A data/archive/integration-main/web/public/data/comparisons.json
A data/archive/integration-main/web/public/data/heatmap/arcadia.json
A data/archive/integration-main/web/public/data/heatmap/chryse.json
A data/archive/integration-main/web/public/data/heatmap/de-gerlache.json
A data/archive/integration-main/web/public/data/heatmap/elysium.json
A data/archive/integration-main/web/public/data/heatmap/faustini.json
A data/archive/integration-main/web/public/data/heatmap/gale.json
A data/archive/integration-main/web/public/data/heatmap/gusev.json
A data/archive/integration-main/web/public/data/heatmap/haworth.json
A data/archive/integration-main/web/public/data/heatmap/jezero.json
A data/archive/integration-main/web/public/data/heatmap/meridiani.json
A data/archive/integration-main/web/public/data/heatmap/mons-mouton.json
A data/archive/integration-main/web/public/data/heatmap/phoenix.json
A data/archive/integration-main/web/public/data/heatmap/shackleton-floor.json
A data/archive/integration-main/web/public/data/heatmap/shackleton.json
A data/archive/integration-main/web/public/data/heatmap/utopia.json
A data/composition_targets.csv
M data/discovery_mars.csv
M data/discovery_mars_new.csv
M data/discovery_moon.csv
M data/discovery_moon_new.csv
A data/earth_all.csv.gz
A data/features/crism_availability.csv
A data/features/crism_catalogue_audit.csv
A data/features/crism_catalogue_queries.csv
A data/features/crism_downloads.csv
A data/features/crism_downloads_backup_20261115_102453_743623.csv
A data/features/crism_downloads_backup_20261115_102812_935796.csv
A data/features/crism_parameter_features.csv
A data/features/crism_phoenix_catalogue_files.csv
A data/features/crism_phoenix_recovery_inventory.csv
A data/features/crism_scene_catalogue.csv
A data/features/crism_scene_quality.csv
A data/features/crism_targeted_candidates.csv
A data/features/crism_targeted_recovery.csv
A data/features/crism_viking2_recovery.csv
A data/features/emit_downloads.csv
A data/features/geological_coverage.csv
A data/features/geological_features.csv
A data/features/geological_units.geojson
A data/features/mineralogical_coverage.csv
A data/features/mineralogical_features.csv
A data/features/mineralogical_mars_features.csv
A data/features/mineralogical_scene_features.csv
A data/features/mineralogical_scene_quality.csv
A data/features/themis_availability.csv
A data/features/themis_catalogue_queries.csv
A data/features/themis_downloads.csv
A data/features/themis_scene_catalogue.csv
A data/features/themis_scene_features.csv
A data/features/themis_thermal_features.csv
A data/features/thermal_mars_features.csv
A data/features/thermal_mars_pixels.csv
A data/features/thermal_moon_facets.csv
A data/features/thermal_moon_features.csv
A data/figures/earth_La_Candelaria_analysis.png
A data/figures/earth_La_Guajira_analysis.png
A data/figures/earth_Nevado_Santa_Isabel_analysis.png
A data/figures/earth_Nevado_del_Ruiz_analysis.png
A data/figures/earth_Tatacoa_analysis.png
A data/figures/earth_Volcan_Purace_analysis.png
A data/figures/mars_Gale_analysis.png
A data/figures/mars_Jezero_analysis.png
A data/figures/mars_Pathfinder_analysis.png
A data/figures/mars_Phoenix_analysis.png
A data/figures/mars_Viking_1_analysis.png
A data/figures/mars_Viking_2_analysis.png
A data/figures/moon_Connecting_Ridge_analysis.png
A data/figures/moon_De_Gerlache_Rim_analysis.png
A data/figures/moon_Leibnitz_Beta_Plateau_analysis.png
A data/figures/moon_Malapert_Massif_analysis.png
A data/figures/moon_Peak_Near_Shackleton_analysis.png
A data/figures/moon_Shackleton_Rim_analysis.png
A data/processed/earth/La_Candelaria_DEM_200m.tif
A data/processed/earth/La_Guajira_DEM_200m.tif
A data/processed/earth/Nevado_Santa_Isabel_DEM_200m.tif
A data/processed/earth/Nevado_del_Ruiz_DEM_200m.tif
A data/processed/earth/Tatacoa_DEM_200m.tif
A data/processed/earth/Volcan_Purace_DEM_200m.tif
A data/processed/mars/Gale_DEM_200m.tif
A data/processed/mars/Jezero_DEM_200m.tif
A data/processed/mars/Pathfinder_DEM_200m.tif
A data/processed/mars/Phoenix_DEM_200m.tif
A data/processed/mars/Viking_1_DEM_200m.tif
A data/processed/mars/Viking_2_DEM_200m.tif
A data/processed/moon/Connecting_Ridge_DEM_200m.tif
A data/processed/moon/De_Gerlache_Rim_DEM_200m.tif
A data/processed/moon/Leibnitz_Beta_Plateau_DEM_200m.tif
A data/processed/moon/Malapert_Massif_DEM_200m.tif
A data/processed/moon/Peak_Near_Shackleton_DEM_200m.tif
A data/processed/moon/Shackleton_Rim_DEM_200m.tif
A data/raw/climate/La_Candelaria_NASA_POWER.csv
A data/raw/climate/La_Guajira_NASA_POWER.csv
A data/raw/climate/Nevado_Santa_Isabel_NASA_POWER.csv
A data/raw/climate/Nevado_del_Ruiz_NASA_POWER.csv
A data/raw/climate/Tatacoa_NASA_POWER.csv
A data/raw/climate/Volcan_Purace_NASA_POWER.csv
A data/raw/moon/README
A data/reference/marco_analogos.json
A data/reference/marco_source_manifest.json
A data/reference/santiago_source_manifest.json
M data/regions/antarctic_plateau.csv
M data/regions/axel_heiberg.csv
M data/regions/devon_island.csv
M data/regions/dry_valleys.csv
M data/regions/ellesmere_north.csv
M data/regions/iceland_highlands.csv
M data/regions/north_greenland.csv
M data/regions/prince_charles_mts.csv
M data/regions/svalbard.csv
M data/regions/transantarctic_mts.csv
M data/regions/victoria_island.csv
M data/regions_catalog.csv
A data/results/normalization_parameters.csv
A data/results/normalized_features.csv
A data/results/similarity_matrix.csv
A data/results/similarity_matrix.png
M data/results_mars_new_per_region.csv
M data/results_mars_overall.csv
M data/results_moon_new_per_region.csv
M data/results_moon_overall.csv
M data/results_pairs_top20.csv
A data/results_per_target_top_regions.csv
M data/seasons_mars.csv
M data/seasons_moon.csv
M data/targets.csv
M data/targets_mars.csv
M data/targets_moon.csv
A data/top200_analogos.csv
A data/top200_analogos.json
A docs/COMPOSICION.md
M docs/DATOS_WEB.md
A docs/GeoAnalog_CONTEXTO_TECNICO.md
A docs/SCIENTIFIC_DATA_CONTRACT.md
A docs/SCIENTIFIC_VARIABLE_MAPPING.md
M environment.yml
M requirements.txt
M src/build_database.py
M src/build_earth.py
M src/build_mars_targets.py
M src/build_moon_targets.py
M src/compare.py
A src/composition.py
A src/download_crism.py
A src/download_themis.py
A src/export_analogos.py
A src/export_science.py
M src/export_web.py
M src/extract_climate.py
A src/extract_crism.py
M src/extract_features.py
A src/extract_geology.py
A src/extract_mineralogy.py
A src/extract_thermal_mars.py
A src/extract_thermal_moon.py
A src/extract_thermal_themis.py
M src/make_maps.py
A src/make_photos.py
M src/make_results.py
A src/make_top_analogos.py
A src/recover_crism.py
A src/recover_crism_targeted.py
A src/science_metadata.py
A src/scientific_catalog.py
A src/search_crism.py
A src/search_themis.py
M src/seasons.py
M src/similarity.py
A tests/test_scientific_integration.py
M web/package-lock.json
M web/package.json
A web/playwright.config.ts
A web/public/data/analogos.json
M web/public/data/comparisons.json
A web/public/data/global-rankings.json
M web/public/data/heatmap/arcadia.json
M web/public/data/heatmap/chryse.json
M web/public/data/heatmap/de-gerlache.json
M web/public/data/heatmap/elysium.json
M web/public/data/heatmap/faustini.json
M web/public/data/heatmap/gale.json
M web/public/data/heatmap/gusev.json
M web/public/data/heatmap/haworth.json
M web/public/data/heatmap/jezero.json
M web/public/data/heatmap/meridiani.json
M web/public/data/heatmap/mons-mouton.json
M web/public/data/heatmap/phoenix.json
M web/public/data/heatmap/shackleton-floor.json
M web/public/data/heatmap/shackleton.json
M web/public/data/heatmap/utopia.json
A web/public/data/science/earth/La_Candelaria.geojson
A web/public/data/science/earth/La_Candelaria.json
A web/public/data/science/earth/La_Guajira.geojson
A web/public/data/science/earth/La_Guajira.json
A web/public/data/science/earth/Nevado_Santa_Isabel.geojson
A web/public/data/science/earth/Nevado_Santa_Isabel.json
A web/public/data/science/earth/Nevado_del_Ruiz.geojson
A web/public/data/science/earth/Nevado_del_Ruiz.json
A web/public/data/science/earth/Tatacoa.geojson
A web/public/data/science/earth/Tatacoa.json
A web/public/data/science/earth/Volcan_Purace.geojson
A web/public/data/science/earth/Volcan_Purace.json
A web/public/data/science/files/data/features/climate_features.csv
A web/public/data/science/files/data/features/crism_availability.csv
A web/public/data/science/files/data/features/crism_catalogue_audit.csv
A web/public/data/science/files/data/features/crism_catalogue_queries.csv
A web/public/data/science/files/data/features/crism_downloads.csv
A web/public/data/science/files/data/features/crism_downloads_backup_20261115_102453_743623.csv
A web/public/data/science/files/data/features/crism_downloads_backup_20261115_102812_935796.csv
A web/public/data/science/files/data/features/crism_parameter_features.csv
A web/public/data/science/files/data/features/crism_phoenix_catalogue_files.csv
A web/public/data/science/files/data/features/crism_phoenix_recovery_inventory.csv
A web/public/data/science/files/data/features/crism_scene_catalogue.csv
A web/public/data/science/files/data/features/crism_scene_quality.csv
A web/public/data/science/files/data/features/crism_targeted_candidates.csv
A web/public/data/science/files/data/features/crism_targeted_recovery.csv
A web/public/data/science/files/data/features/crism_viking2_recovery.csv
A web/public/data/science/files/data/features/emit_availability.csv
A web/public/data/science/files/data/features/emit_downloads.csv
A web/public/data/science/files/data/features/environmental_features.csv
A web/public/data/science/files/data/features/geological_coverage.csv
A web/public/data/science/files/data/features/geological_features.csv
A web/public/data/science/files/data/features/geological_units.geojson
A web/public/data/science/files/data/features/mineralogical_coverage.csv
A web/public/data/science/files/data/features/mineralogical_features.csv
A web/public/data/science/files/data/features/mineralogical_mars_features.csv
A web/public/data/science/files/data/features/mineralogical_scene_features.csv
A web/public/data/science/files/data/features/mineralogical_scene_quality.csv
A web/public/data/science/files/data/features/planetary_features.csv
A web/public/data/science/files/data/features/spectral_features.csv
A web/public/data/science/files/data/features/themis_availability.csv
A web/public/data/science/files/data/features/themis_catalogue_queries.csv
A web/public/data/science/files/data/features/themis_downloads.csv
A web/public/data/science/files/data/features/themis_scene_catalogue.csv
A web/public/data/science/files/data/features/themis_scene_features.csv
A web/public/data/science/files/data/features/themis_thermal_features.csv
A web/public/data/science/files/data/features/thermal_mars_features.csv
A web/public/data/science/files/data/features/thermal_mars_pixels.csv
A web/public/data/science/files/data/features/thermal_moon_facets.csv
A web/public/data/science/files/data/features/thermal_moon_features.csv
A web/public/data/science/files/data/figures/earth_La_Candelaria_analysis.png
A web/public/data/science/files/data/figures/earth_La_Guajira_analysis.png
A web/public/data/science/files/data/figures/earth_Nevado_Santa_Isabel_analysis.png
A web/public/data/science/files/data/figures/earth_Nevado_del_Ruiz_analysis.png
A web/public/data/science/files/data/figures/earth_Tatacoa_analysis.png
A web/public/data/science/files/data/figures/earth_Volcan_Purace_analysis.png
A web/public/data/science/files/data/figures/mars_Gale_analysis.png
A web/public/data/science/files/data/figures/mars_Jezero_analysis.png
A web/public/data/science/files/data/figures/mars_Pathfinder_analysis.png
A web/public/data/science/files/data/figures/mars_Phoenix_analysis.png
A web/public/data/science/files/data/figures/mars_Viking_1_analysis.png
A web/public/data/science/files/data/figures/mars_Viking_2_analysis.png
A web/public/data/science/files/data/figures/moon_Connecting_Ridge_analysis.png
A web/public/data/science/files/data/figures/moon_De_Gerlache_Rim_analysis.png
A web/public/data/science/files/data/figures/moon_Leibnitz_Beta_Plateau_analysis.png
A web/public/data/science/files/data/figures/moon_Malapert_Massif_analysis.png
A web/public/data/science/files/data/figures/moon_Peak_Near_Shackleton_analysis.png
A web/public/data/science/files/data/figures/moon_Shackleton_Rim_analysis.png
A web/public/data/science/files/data/processed/earth/La_Candelaria_DEM_200m.tif
A web/public/data/science/files/data/processed/earth/La_Guajira_DEM_200m.tif
A web/public/data/science/files/data/processed/earth/Nevado_Santa_Isabel_DEM_200m.tif
A web/public/data/science/files/data/processed/earth/Nevado_del_Ruiz_DEM_200m.tif
A web/public/data/science/files/data/processed/earth/Tatacoa_DEM_200m.tif
A web/public/data/science/files/data/processed/earth/Volcan_Purace_DEM_200m.tif
A web/public/data/science/files/data/processed/mars/Gale_DEM_200m.tif
A web/public/data/science/files/data/processed/mars/Jezero_DEM_200m.tif
A web/public/data/science/files/data/processed/mars/Pathfinder_DEM_200m.tif
A web/public/data/science/files/data/processed/mars/Phoenix_DEM_200m.tif
A web/public/data/science/files/data/processed/mars/Viking_1_DEM_200m.tif
A web/public/data/science/files/data/processed/mars/Viking_2_DEM_200m.tif
A web/public/data/science/files/data/processed/moon/Connecting_Ridge_DEM_200m.tif
A web/public/data/science/files/data/processed/moon/De_Gerlache_Rim_DEM_200m.tif
A web/public/data/science/files/data/processed/moon/Leibnitz_Beta_Plateau_DEM_200m.tif
A web/public/data/science/files/data/processed/moon/Malapert_Massif_DEM_200m.tif
A web/public/data/science/files/data/processed/moon/Peak_Near_Shackleton_DEM_200m.tif
A web/public/data/science/files/data/processed/moon/Shackleton_Rim_DEM_200m.tif
A web/public/data/science/files/data/raw/climate/La_Candelaria_NASA_POWER.csv
A web/public/data/science/files/data/raw/climate/La_Guajira_NASA_POWER.csv
A web/public/data/science/files/data/raw/climate/Nevado_Santa_Isabel_NASA_POWER.csv
A web/public/data/science/files/data/raw/climate/Nevado_del_Ruiz_NASA_POWER.csv
A web/public/data/science/files/data/raw/climate/Tatacoa_NASA_POWER.csv
A web/public/data/science/files/data/raw/climate/Volcan_Purace_NASA_POWER.csv
A web/public/data/science/files/data/results/analog_ranking.csv
A web/public/data/science/files/data/results/normalization_parameters.csv
A web/public/data/science/files/data/results/normalized_features.csv
A web/public/data/science/files/data/results/similarity_matrix.csv
A web/public/data/science/files/data/results/similarity_matrix.png
A web/public/data/science/index.json
A web/public/data/science/mars/Gale.json
A web/public/data/science/mars/Jezero.json
A web/public/data/science/mars/Pathfinder.json
A web/public/data/science/mars/Phoenix.json
A web/public/data/science/mars/Viking_1.json
A web/public/data/science/mars/Viking_2.json
A web/public/data/science/moon/Connecting_Ridge.json
A web/public/data/science/moon/De_Gerlache_Rim.json
A web/public/data/science/moon/Leibnitz_Beta_Plateau.json
A web/public/data/science/moon/Malapert_Massif.json
A web/public/data/science/moon/Peak_Near_Shackleton.json
A web/public/data/science/moon/Shackleton_Rim.json
A web/public/data/science/variables.json
M web/src/App.css
M web/src/App.tsx
M web/src/components/ComparisonPanel.tsx
A web/src/components/GlobalRankings.tsx
M web/src/components/IntroOverlay.tsx
M web/src/components/MethodView.tsx
A web/src/components/ScientificPanel.tsx
M web/src/components/SiteCard.tsx
M web/src/data/comparisons.ts
A web/src/data/science.ts
A web/src/i18n/science.ts
M web/src/i18n/strings.ts
A web/tests/scientific-integration.spec.ts
```

</details>

## 13. Instrucciones para ejecutar el proyecto unificado

### 13.1 Consultar la versión existente

Desde la raíz, con Node disponible:

```powershell
cd web
npm ci
npm run dev -- --host 127.0.0.1
```

Abrir `http://127.0.0.1:5173/`. Los JSON y activos científicos ya están generados, por lo que no es necesario ejecutar descargadores ni tener credenciales NASA para consultarlos localmente. Las capas e imágenes externas requieren conectividad a sus proveedores.

### 13.2 Preparar Python y reexportar

Para una instalación nueva se recomienda el entorno conda declarado:

```powershell
conda env create -f environment.yml
conda activate analogos
python -B src/export_web.py
```

Alternativamente, en la `.venv` ya preparada de este directorio:

```powershell
.\.venv\Scripts\python.exe -B src/export_web.py
# Solo si cambia ciencia regional y no es necesario recalcular la comparación global:
.\.venv\Scripts\python.exe -B src/export_science.py
# Restauración opcional del contrato histórico; no recalcula el ranking global:
.\.venv\Scripts\python.exe -B src/export_analogos.py
```

`export_web.py` utiliza por defecto la sensibilidad completa de 100 variaciones. Requiere los datos ampliados y las entradas incluidas, no consultas remotas. No ejecutar `build_database.py` como paso rutinario para ver la web; reconstruir desde fuentes nativas exige completar primero sus insumos. La guarda añadida rechaza reemplazos parciales.

### 13.3 Ejecutar las verificaciones

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests
cd web
npm run lint
npm run build
npm run test:e2e
```

Las pruebas e2e usan Edge (`msedge`) instalado en el sistema. Pueden reutilizar el servidor local del puerto 5173 o iniciar Vite con la configuración incluida. Para usar Chromium de Playwright debe instalarse su navegador y establecer `$env:PLAYWRIGHT_CHANNEL = 'chromium'`; esa descarga no se efectuó en esta integración. Las pruebas de preservación requieren que los commits fuente estén disponibles en el repositorio Git local.

Para revisar la publicación, usar `git log -1` y `git diff 58313dc...HEAD` en `feature/colombia-scientific-integration`; `git status --short` muestra cualquier cambio local posterior. La documentación complementaria está en [README.md](README.md), [DATOS_WEB.md](docs/DATOS_WEB.md), [SCIENTIFIC_DATA_CONTRACT.md](docs/SCIENTIFIC_DATA_CONTRACT.md) y [SCIENTIFIC_VARIABLE_MAPPING.md](docs/SCIENTIFIC_VARIABLE_MAPPING.md).

## 14. Recomendaciones para integrar la nueva rama en main

1. Revisar los cambios locales, este informe, la atribución y los tres modelos con los integrantes. Confirmar especialmente que las advertencias regionales y el ranking internacional se presentan con su alcance correcto.
2. Crear un commit en la rama de integración después de revisar el inventario. No incluir `.venv`, cachés, artefactos de ejecución, credenciales ni el clon anidado. Conservar los pequeños datos derivados y los contratos generados necesarios para reproducir la demostración.
3. Antes de publicar, actualizar las referencias y revisar cualquier avance posterior de `main` o de las ramas científicas. Resolver los cambios sobre la rama de integración, preservando hashes de los insumos y contratos; no sustituir automáticamente el exportador de Sebastián por el contrato histórico de Marco.
4. Repetir las pruebas al resolver conflictos o cambiar entradas; revisar los conteos reales y la conexión de los 200 lugares. No exigir igualdad de fechas de generación JSON como criterio de preservación de ciencia.
5. La publicación de esta rama quedó autorizada por Santiago después de revisar la entrega local. La creación de un PR y el merge hacia `main` siguen pendientes de revisión del equipo; el PR deberá incluir este informe, resultados de pruebas y limitaciones.
6. Mantener después una política de versiones para contratos e insumos; separar adquisición de datos, extracción, puntuación y publicación. No incorporar nuevas variables al PAI o sustituir proxies globales sin una definición y evaluación científica independiente.
7. Para la presentación, mostrar un caso colombiano, sus fuentes y calidad, sus 12 PAI y el índice global con sus límites. Explicar que el top mundial y la caracterización regional contestan preguntas de escala diferente. Evitar afirmar validación de recursos, habitabilidad o base permanente a partir de un puntaje de similitud.
8. Programar como trabajo posterior la máscara terrestre de Guajira, validación EMIT, resolución geométrica CRISM Phoenix, verificación de banda THEMIS, reconstrucción de entorno bloqueado y pruebas de rendimiento/servicios remotos. Esos pendientes no cambian el carácter exploratorio de los resultados ya integrados.

La revisión puede realizarse íntegramente con los archivos y la aplicación locales. Las ramas fuente, los datos científicos originales y el informe técnico histórico permanecen disponibles para contrastar cada resultado.
