# Contrato científico de GeoAnalog

Fecha: 2026-11-15. Rama de integración: `feature/colombia-scientific-integration`.

## Entradas y responsabilidades

- Marco / `Mabeltranpe1`: `data/earth_all.csv.gz`, 691.035 celdas de 727 regiones, objetivos globales y top 200. Fuente `e75ecdb583d26223cc57ceae142672492f5282aa`.
- Sebastián / `Ssalazarp420`: interfaz Cesium/React y contrato de comparación de `main`, base `58313dc`.
- Santiago / `santiago-851`: seis ventanas colombianas, doce ventanas planetarias, CSV, GeoJSON, DEM, figuras y 72 pares PAI. Fuente `aaf4ebb411e2005b159f90e7c078c81f8d93be6e`.

Los archivos científicos de origen no se editan para ajustarlos al esquema. La base global conserva sus celdas. Los valores regionales se publican en otro espacio de nombres; una igualdad de unidad o un nombre parecido no crea una equivalencia física o espacial.

## `comparisons.json`, versión 3

Es el contrato canónico de la aplicación. Conserva `features`, `targets`, `sites[].values`, `sites[].results`, `n_cells`, `n_regions` y los controles existentes. Añade:

| Campo | Contrato |
|---|---|
| `version` | `"3"`; el frontend acepta 2/3 y rechaza muestras `synthetic=true`. |
| `provenance` | Commits de las tres contribuciones. |
| `method` | Identificador del puntaje web, ecuación, escalado y política de exclusión. |
| `sites[].science_ref` | En seis sitios colombianos: `{id,url,name:{es,en}}`. No sustituye `values` ni `results`. |
| `targets[].science_refs` | Ventanas del mismo cuerpo con intersección geométrica positiva; porcentaje de ventana/objetivo y método de asociación. |
| `science_index_url` | `/data/science/index.json`. |
| `global_rankings_url` | `/data/global-rankings.json`. |

El puntaje web conserva la ecuación exponencial del comparador y la política de dimensiones comparables de la interfaz. La elevación tiene peso cero y el contraste de emisividad equivalente peso 0,5. Las exclusiones calculadas por cuerpo se publican en cada objetivo. La sensibilidad usa 100 variaciones ±50 %, semilla fija y top 500. No es validación instrumental.

Se incorporan los sitios necesarios para abrir todos los lugares del top 200 en los mismos controles y mapas. Los descubrimientos adicionales no eliminan sitios de catálogo ni otras celdas de Colombia. El navegador recibe un subconjunto de sitios y hasta 2.500 puntos por objetivo; no recibe las 691.035 filas.

## Documentos regionales, versión `1.0.0`

Rutas: `/data/science/{earth|moon|mars}/{region_original}.json`.

| Campo | Contenido |
|---|---|
| `id` | `{planet}_{region_original}`; conserva mayúsculas y guiones bajos de Santiago. |
| `site_id` | Solo Tierra; ID del catálogo de Sebastián. |
| `name` | Nombre ES/EN. |
| `source_commit`, `author` | Procedencia de los datos, sin atribuir la integración a su autor original. |
| `geometry` | Centro derivado del DEM, límites proyectados, CRS, resolución y ventana nominal. Puede ser nulo si no está disponible el DEM. |
| `sections[]` | `id`, título bilingüe, fuente, soporte, periodo, método, campos y registros originales. Una sección sin observaciones se marca `unavailable`. |
| `sections[].fields[]` | Columna original, nombre en la app, definición, unidad, fuentes, resolución/soporte, periodo, método, posible contraparte global y razón de compatibilidad. |
| `sections[].records[]` | Valores originales sin redondeo adicional; ausentes como `null`, ceros reales como cero y booleanos como booleanos. |
| `quality_flags[]` | Código estable, nivel y explicación ES/EN; persisten en la interfaz. |
| `pai` | Modelo experimental y todos los resultados originales de esa ventana; seis o doce pares según cuerpo. |
| `sources[]` | Nombre, institución, URL y tipo de evidencia: observación, clasificación, inversión o modelo, etc. |
| `assets[]` | CSV, GeoJSON, GeoTIFF y figuras, con URL y SHA-256 cuando corresponde a un archivo original. |

`index.json` contiene las 18 ventanas, asociaciones, equipo confirmado, modelo PAI y manifiesto de 85 artefactos originales. `variables.json` contiene la correspondencia completa. Las tablas y figuras originales se sirven desde `/data/science/files/data/...`, sin incluir los datasets nativos planetarios de gran tamaño.

Los documentos se cargan al abrir el panel. El panel PAI enlaza las doce ventanas planetarias de Santiago, incluidas las que no coinciden con un objetivo global. Las figuras originales incluyen elevación absoluta y relativa, pendiente, TRI, TPI y orientación.

## Compatibilidad física y prioridad

| Observación regional | Candidato global | Decisión |
|---|---|---|
| Elevación y pendiente del cuadrado de 10 km | Elevación y pendiente de una celda angular global | Mantener ambas; huella y, para elevación entre cuerpos, datum diferentes. |
| TRI de Riley | Desviación local de alturas `roughness` | Definiciones distintas; no convertir ni sustituir. |
| TPI | Sin variable global equivalente | Mantener como descriptor regional. |
| Aire POWER | LST MODIS / MCD / Diviner | Magnitudes distintas; no convertir °C a K para hacerlas parecer equivalentes. |
| LST día/noche MODIS regional | Media global de muestras día+noche | Producto, periodo y estimador diferentes. |
| Diferencia LST emparejada | Máximo menos media global | No equivalentes. |
| CHIRPS medio 2021–2025 | Precipitación GPM/MERRA-2 de la base global | Periodos, producto y soporte diferentes. |
| Cocientes Sentinel-2 o coincidencias EMIT | Contraste ASTER o CF equivalente | Proxies distintos; no traducir a concentración ni fusionar índices. |
| TES | Temperatura | Inercia térmica, con unidad J m⁻² K⁻¹ s⁻¹/². |
| THEMIS IRPBT | Temperatura cinética o amplitud diaria | Piloto; banda sin verificar y fechas no emparejadas. |
| Estabilidad de hielo PRP | Presencia de hielo | Modelo, no detección ni reserva. |

En las seis fichas colombianas la caracterización detallada procede de Santiago. Los valores de la celda global de Marco se mantienen dentro de la comparación global y se explican como otra observación. Los nombres se relacionan mediante una tabla explícita, no mediante coincidencia difusa de cadenas.

Las asociaciones planetarias usan intersecciones de disco/anillo y ventana en el CRS del estudio. Son aproximaciones planas de asociación, no una nueva coalineación ni una demostración de igualdad entre soportes. Solo siete objetivos globales tienen asociaciones positivas en estos datos: dos lunares y cinco marcianos. Los demás estudios siguen accesibles desde el PAI.

## Tres métricas que no se fusionan

1. **Índice global completo de Marco:** resultados originales del top 200, escala 0–1, todas sus variables activas con elevación 0 y emisividad 0,5; media lunar sin el piso sombreado de Shackleton. Orden, separación de 300 km y condiciones se conservan.
2. **Puntaje web de dimensiones comparables:** fórmula exponencial y exclusiones por cuerpo, calculado en la base ampliada y presentado con sus variables activas. Reponderar en el navegador solo reordena los sitios exportados.
3. **PAI topográfico regional:** seis descriptores normalizados sobre seis candidatos colombianos, pesos 0,15×5 y 0,25; `100/(1+distancia)`. Los 72 valores originales permanecen intactos.

`global-rankings.json`, versión `1.0.0`, conserva todas las 39 columnas originales del top 200 y añade solo `site_id` y `target_id` para navegación. Incluye SHA-256 del CSV fuente y los metadatos del modelo. El frontend lo consume en Análisis cuando no hay un sitio seleccionado.

## Contrato histórico `analogos.json`

El JSON de Marco se conserva como fotografía de su contrato anterior y se identifica por su commit de origen. No se renombra ni se entrega a componentes que esperan `comparisons.json`. `src/export_analogos.py` reproduce esa fotografía sin depender de los archivos experimentales externos del exportador histórico. La app unificada consume `comparisons.json` v3, `global-rankings.json` y los documentos regionales; conservar el contrato anterior no implica que todos sus rankings sean la ampliación mundial actual.

## Regeneración y controles

```powershell
.\.venv\Scripts\python.exe -B src/export_web.py
.\.venv\Scripts\python.exe -B src/export_science.py  # solo ciencia regional
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests
cd web
npm ci
npm run lint
npm run build
npm run test:e2e
```

No se requieren consultas a NASA ni nuevas descargas para reexportar los productos incluidos. Los módulos de extracción se ejecutan explícitamente cuando se decide reprocesar datos; la exportación no los invoca. El merge de una reconstrucción regional incompleta falla antes de sobrescribir el gzip publicado. Para reconstruir todos los datos nativos se necesitan entradas adicionales, versiones y dependencias HDF4/NetCDF; ese proceso no se ejecutó como parte de esta integración.
