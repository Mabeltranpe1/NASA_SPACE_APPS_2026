# API de análogos y apartado "Buscar análogos"

Autor: Marco (rama `feature/analog-finder`), integrado en la app en la versión 0.6.0.

## Qué hace

Tres operaciones de solo lectura, con **el mismo cálculo que `src/compare.py`**:

1. **Buscar análogos.** Recibe un sitio de la Luna o Marte, o valores propios, y devuelve los mejores lugares de la Tierra. Cada lugar trae puntaje, similitud por variable, la variable más parecida (`best_match`) y la que rompe la analogía (`worst_match`).
2. **Consultar un punto.** Recibe una lat/lon de la Tierra y responde a qué sitios de la Luna y Marte se parece y dónde falla la analogía.
3. **Exportar.** Formatos disponibles: GeoJSON (QGIS, geojson.io, ArcGIS, Google Earth Pro), KML (Google Earth) y waypoints `QGC WPL 110` (Mission Planner, QGroundControl).

La configuración oficial es la de `make_results.py`:
- escala por tolerancias;
- pesos de `compare.py`, con `elev_m = 0` y `em_contrast = 0.5`;
- cada celda debe tener todas las variables que el sitio usa;
- se excluyen los análogos famosos (`known = yes`);
- se devuelve un lugar por región, con al menos **300 km** entre lugares (configurable).

## Por qué no hay servidor

La web está en Azure Static Web Apps (plan gratis), así que el comparador corre **en el navegador**:

- `python src/analog_api.py export-web` empaqueta las 691 035 celdas de `data/earth_all.csv.gz` en `web/public/data/comparator/earth.bin` (7 MB, gzip, columnas int16) y escribe `comparator.json` con tolerancias, pesos, sitios y regiones.
- La página solo descarga esos archivos cuando se abre el apartado. Una búsqueda tarda entre 0,1 y 0,4 s.
- El código TypeScript **lee la configuración del JSON**, sin copiar números a mano. Si cambian pesos o tolerancias en Python, basta con volver a exportar.

Una función de Azure en Python (`/api/...`) se puede añadir más adelante reutilizando `analog_api.handle()` sin cambios. No hace falta para el prototipo.

## Un solo puntaje (el mismo de toda la app)

La API, el apartado «Buscar» y el resto de la app usan **la misma regla** (`src/export_web.py`, decisión del equipo del 2026-11-15):

- Los pesos son los de `make_results.py`: sin elevación y el tipo de roca a 0,5.
- Si el valor típico de los sitios de un cuerpo queda fuera de todo lo que tiene la Tierra (los 50–150 K de la Luna), **esa variable se apaga para ese cuerpo**. No decide el puntaje.
- Esas variables se listan en `switched_off` (por cuerpo, también en `settings.json`) y en `out_of_earth_range`, con el valor más cercano que tiene la Tierra. La app las muestra como límite de la analogía.

`analog_api.py` calcula los pesos con `export_web.body_weights()`, así que no hay dos copias de la regla. El navegador lee esos pesos del JSON exportado. Ejemplo: Mons Mouton da 0,645 en el Desierto Occidental de Egipto tanto en la API como en «Descubrir» (64/100).

## Cómo se comprobó

`python tests/test_web_port.py` corre 38 búsquedas (todos los sitios y casos especiales) y 3 puntos en Node con el código del navegador y en Python con `compare.py`:

- **Mismo cálculo:** con los mismos valores guardados, la diferencia es 1e-16.
- **Contra la base completa sin redondear:** la diferencia máxima de puntaje es 3e-5 (comprobado con la versión 0.6.0: 31 sitios, sin cambios de orden).
- **Empates prácticos:** a veces dos lugares quedan prácticamente empatados (por ejemplo, 0,03280 frente a 0,03280) y el redondeo puede cambiar cuál sale primero. Con la regla de 300 km, ese cambio puede mover otros lugares de la lista. El script los lista.

## Para investigadores

### 1. API estática (en la web publicada)

`python src/analog_api.py export-static` escribe en `web/public/data/api/v1/`:

| URL | Contenido |
|---|---|
| `/data/api/v1/sites.json` | Los 31 sitios (22 de la Luna, 9 de Marte) y sus valores. Los `id` son los mismos de la app (`jezero`, `connecting-ridge`…) |
| `/data/api/v1/settings.json` | Variables, tolerancias, pesos, rango de la Tierra y fórmula |
| `/data/api/v1/analogs/<sitio>.json` | Los 20 mejores lugares de la Tierra para ese sitio |
| `/data/api/v1/analogs/<sitio>.geojson` / `.kml` / `.waypoints` | Lo mismo, en formato de mapa |

`/api/` no se usa porque Azure Static Web Apps lo reserva para funciones.

Ejemplos: en QGIS, *Capa → Añadir capa vectorial → Protocolo HTTP*, y pegar `https://icy-flower-03890400f.5.azurestaticapps.net/data/api/v1/analogs/jezero.geojson`. En Python: `requests.get(url).json()`.

### 2. Librería y servidor local (consultas libres)

```bash
python src/analog_api.py sites
python src/analog_api.py find --site jezero --top 10 --format geojson > jezero.geojson
python src/analog_api.py find --body Mars --value temp_mean_K=215 --value albedo=0.15 --value slope_deg=3
python src/analog_api.py point --lat 25.4 --lon 29.4
python src/analog_api.py serve --port 8000
```

Rutas del servidor (solo GET, con CORS abierto):

| Ruta | Parámetros |
|---|---|
| `/api/v1/sites` | |
| `/api/v1/settings` | |
| `/api/v1/analogs` | `site` o `body`; valores con el nombre de la variable (`temp_mean_K=215`); pesos con `w_<variable>`; `top`, `per_region`, `min_km`, `include_known`, `format=json\|geojson\|kml\|waypoints` |
| `/api/v1/point` | `lat`, `lon`, `max_km` (25 por defecto), `format` |

Solo necesita pandas y numpy: `compare.py` importa scikit-learn únicamente para `--scaling robust`, que la API no usa.

## Tipos de misión

Siete perfiles de pesos sobre las mismas variables (`web/src/comparator/missions.ts`): rovers, minería e ISRU, hábitats, pruebas térmicas, astrobiología, drones, y aterrizaje y lanzamiento. Cada misión multiplica los pesos del modelo, así que la fórmula y las variables apagadas no cambian (`web/scripts/check-missions.ts` lo comprueba).

- **«Apto para»**: cada lugar muestra hasta 3 misiones. El valor de cada misión se compara con el mejor lugar de la Tierra para esa misión (100), y solo se sugieren las que llegan a **50 o más**. Si ninguna llega, el panel lo dice.
- **Misiones que no aplican**: si un cuerpo tiene apagadas todas las variables que una misión necesita, esa misión no se ofrece. Es el caso de las pruebas térmicas en la Luna, donde la temperatura no se compara. Los hábitats lunares llevan un aviso por la misma razón.
- `public/data/missions.json` guarda los pesos y el mejor valor de la Tierra por sitio y misión (`web/scripts/export-missions.ts`), así el panel no carga la base de 7 MB.

## Integración en la web

- **Apartado «Buscar»** en la barra lateral (`view=finder`). `AnalogFinder` se carga de forma diferida (`React.lazy`): ni el componente ni la base de 7 MB se descargan hasta abrirlo. Un enlace `#buscar?site=...` abre el apartado directamente («Copiar enlace»).
- **Lógica sin React:** `web/src/comparator/compare.ts` (`loadComparator`, `findAnalogs`, `queryPoint`, `toGeoJSON`, `toKML`, `toWaypoints`).
- **Globo 3D:** cada resultado tiene «Ver en el globo 3D», que abre Descubrir con el globo de la Tierra sobre ese lugar. El mapa plano de GIBS del apartado se mantiene como vista general de los 10 resultados.
- Sus textos viven en el propio componente (`TEXT`, en español e inglés) y no en `i18n/strings.ts`; funcionan igual con el selector ES/EN.
- **Peso del despliegue:** ~9 MB (7 de la base + 2 de la API estática).

## Regenerar

```bash
python src/analog_api.py export-web      # después de cambiar earth_all.csv.gz, targets.csv o pesos
python src/analog_api.py export-static
python tests/test_web_port.py            # necesita node >= 22
```
