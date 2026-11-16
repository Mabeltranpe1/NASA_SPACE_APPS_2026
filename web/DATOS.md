# Datos para el aplicativo web (`analogos.json`, contrato histórico)

> **Estado (v0.6.0):** la app **ya no usa** este archivo. Sus datos vienen de `src/export_web.py` → `comparisons.json` y mapas de calor, y el apartado «Buscar» y la API usan `src/analog_api.py` → `public/data/comparator/` y `public/data/api/v1/`. Ver [docs/DATOS_WEB.md](../docs/DATOS_WEB.md) y [docs/API.md](../docs/API.md). `analogos.json` se conserva como fotografía del contrato anterior (15 sitios: 6 de la Luna y 9 de Marte, antes de los 22 sitios de Artemis III).

Este archivo describía el formato de **`web/public/data/analogos.json`**.
Sus tipos de TypeScript están en **`web/src/data/analogos.ts`** (`AnalogData`).

```ts
import type { AnalogData } from './data/analogos'
const data: AnalogData = await fetch('/data/analogos.json').then((r) => r.json())
```

## Cómo se genera

```bash
python src/make_results.py   # comparación (necesita el entorno analogos)
python src/export_analogos.py  # escribe web/public/data/analogos.json
```

Las imágenes **no** se duplican en git. Para usarlas en local, `npm run copy-images` ejecuta
`scripts/copy-data-images.mjs`, que copia cada imagen listada en el JSON desde `maps/` y
`experiments/fotos_analogos/` hacia `public/data/img/` (ignorado por git). En el HTML se usa
siempre `image.url` (por ejemplo `/data/img/maps/07_mars_jezero_crater_B_mars.png`).
Si falta alguna imagen, el script falla y dice cuál.

> **Nota (integración):** el copiado ya no corre solo antes de `dev`/`build`, porque metía unos 100 MB de PNG en el despliegue. La app todavía no usa `analogos.json`; sus datos se integran por `src/export_web.py` → `comparisons.json` (ver `docs/DATOS_WEB.md`).

## Qué hay en el JSON

| Campo | Qué es |
|---|---|
| `sites[]` | Los 15 sitios de la Luna (6) y Marte (9) |
| `sites[].values` | Variables medidas en el sitio (`features` da nombre y unidad) |
| `sites[].composition` | Tipo de roca: litología, Christiansen feature, `em_contrast` ± incertidumbre, evidencia |
| `sites[].images[]` | Mapa de relieve, vista orbital y fotos de superficie del sitio (con crédito y fuente) |
| `sites[].analogs[]` | Los 5 mejores lugares de la Tierra, uno por región, `rank` 1 = mejor |
| `analogs[].score` | Similitud total 0..1 |
| `analogs[].similarity` | Similitud por variable 0..1 (para un gráfico de radar o de barras) |
| `analogs[].earth_values` | Valores de la Tierra para comparar con `sites[].values` |
| `analogs[].composition` | Tipo de roca de la Tierra según ASTER (`ambiguous: true` = revisar) |
| `analogs[].images[]` | Mapa de relieve y foto satelital del lugar (puede estar vacío) |
| `rock_types` | Composición **típica** en óxidos (% en peso) de cada tipo de roca |
| `overall.Moon / overall.Mars` | Ranking de regiones para todos los sitios de cada cuerpo |
| `regions[]` | Rectángulo y descripción de cada región de la Tierra |
| `reference_photos[]` | Fotos de Apolo y Pathfinder que no corresponden a un sitio de la lista |

### Gráfica de composición (óxidos)

Para un sitio `s` y su análogo `a`:

```ts
const lunaOMarte = data.rock_types[s.composition.rock_type].oxides
const tierra = a.composition ? data.rock_types[a.composition.rock_type].oxides : null
// barras agrupadas por data.oxides_order: SiO2, TiO2, Al2O3, FeO, MgO, CaO, Na2O, K2O
```

Mostrar siempre la nota `data.oxides_note`: son valores **típicos del tipo de roca**, no
medidos en el lugar. Si `a.composition.ambiguous` es `true`, mostrar `a.composition.note`.

### Avisos que hay que mostrar

- Imagen de la Tierra con `same_place: false`: es de otro punto de la misma región. Mostrar `note`.
- `analogs[].images` vacío: todavía no hay mapa ni foto de ese lugar (se generan con `src/make_maps.py`
  y `src/make_photos.py`).
- `em_contrast` de la Luna y Marte es una estimación (±0.03). Ver `docs/COMPOSICION.md`.
- Los nombres de los sitios y de las litologías están en inglés; `region_label` es legible.

## Tamaño

Unas 70 imágenes, ~100 MB en `public/data/img/` (y en `dist/`). Las fotos `_photo.png` pesan
hasta 8 MB; si el despliegue se pone lento, conviene convertirlas a JPG o WebP.
