# Plan: visualizar en detalle por qué dos lugares son homólogos

Estado: **funcionando con datos reales** (`src/export_web.py` → `web/public/data/` → `ComparisonPanel` y mapa de similitud). Usa la base global y el comparador de Marco y la caracterización de Santiago. Reglas y regeneración: [DATOS_WEB.md](DATOS_WEB.md).

Objetivo: que cualquier persona, y en especial el jurado, entienda **con datos** por qué un lugar de la Tierra es análogo a uno de la Luna o de Marte, **cuánto** se parece y **dónde deja de valer** la analogía.

---

## 1. Qué preguntas debe responder la vista

| Pregunta del usuario | Respuesta visual |
|---|---|
| ¿Qué tan parecidos son en total? | **Puntaje grande** (0–100) + estabilidad del ranking |
| ¿En qué se parecen y en qué no? | **Lista de barras por característica** (similitud 0–1), con la mejor y la peor marcadas |
| ¿Cuáles son los valores reales? | **Comparación por variable** (valor Tierra vs. valor Luna/Marte), cada una en su propia escala y unidad |
| ¿De dónde salen los datos? | **Fuente por variable** (dataset, instrumento, resolución) |
| ¿Hay lugares mejores? | **Ranking** de los mejores candidatos de la Tierra para ese objetivo |
| ¿Dónde más en la Tierra se da esto? | **Mapa de calor** de similitud sobre el globo terrestre |
| ¿Qué no puede reproducir la Tierra? | **Bloque de límites físicos** fijo (gravedad, vacío, radiación, atmósfera) |

## 2. Diseño de la vista "Comparación detallada"

Se abre debajo de las imágenes de detalle (o como panel a pantalla completa) al elegir un par.

```
┌──────────────────────────────────────────────────────────────────────┐
│ Desierto de la Tatacoa  ≈  Formación Medusae Fossae                    │
│                                                                      │
│   72 / 100        Estable en 94 % de 200 variaciones de pesos          │
│   similitud       Mejor: rugosidad · Rompe la analogía: temperatura    │
├───────────────────────────────┬──────────────────────────────────────┤
│ SIMILITUD POR CARACTERÍSTICA   │ VALORES REALES                        │
│ Rugosidad      ████████▉ 0.91  │ Temperatura media (K)                 │
│ Pendiente      ███████▋  0.78  │   Tierra ●──────────────● Marte        │
│ Albedo         ██████▏   0.63  │         300            210            │
│ Elevación      ████▌     0.47  │ Amplitud térmica (K)                  │
│ Temp. media    █▊        0.18 ⚠│   Tierra ●────● Marte                  │
│ (pesos ajustables ▸)           │ ...                                   │
├───────────────────────────────┴──────────────────────────────────────┤
│ FUENTES  Temperatura: MODIS LST (1 km) vs THEMIS · Relieve: SRTM vs MOLA│
│ LÍMITES  Gravedad 1 g vs 0,38 g · Atmósfera 1013 hPa vs 6 hPa · ...    │
└──────────────────────────────────────────────────────────────────────┘
```

### Componentes y forma de cada gráfico

| Componente | Forma | Por qué |
|---|---|---|
| Puntaje total | **Número grande** (≥ 48 px) + texto de estabilidad | Un solo valor no necesita gráfico |
| Similitud por característica | **Lista de barras** (nombre + barra + cifra por fila), un solo tono; la peor fila lleva icono ⚠ y la etiqueta "rompe la analogía" | Compara varias razones 0–1, cada una contra el máximo; es más legible que un gráfico de radar |
| Valores reales | **Mancuernas (dumbbell) en múltiplos pequeños**: una fila por variable, cada una con su propio eje físico fijo (`range` en el JSON) y unidad | Las variables tienen escalas distintas (K, m, grados, albedo): **nunca** un solo eje compartido ni dos ejes en un mismo gráfico |
| Ranking de candidatos | **Barras horizontales ordenadas**, un tono, el sitio actual resaltado | Comparar magnitudes entre candidatos |
| Mapa de similitud | **Mapa de calor secuencial** (un tono, claro → oscuro) superpuesto al globo de la Tierra | Magnitud en el espacio; nada de arcoíris |
| Tabla | Tabla con todos los valores, siempre disponible | Accesibilidad y verificación |

Reglas de color (guía de visualización):
- Colores de identidad fijos: **Tierra azul, Luna gris, Marte naranja**, igual que en los globos.
- La similitud (magnitud) usa **un solo tono**; la peor característica se marca con **icono + texto**, no solo con color.
- Todos los gráficos tienen tooltip al pasar el cursor y una vista de tabla.
- La paleta se valida con el script de daltonismo antes de publicarla.

### Interacción
- **Pesos ajustables:** un control por característica. El puntaje se recalcula **exactamente** en el navegador con la misma fórmula de `compare.py`: como `s_f = exp(−|d_f|)`, se recupera `|d_f| = −ln s_f` y `S = exp(−√(Σ w·d² / Σ w))`.
- **Al cambiar de par**, todas las vistas se actualizan juntas: globos, imágenes y comparación.
- **Clic en una celda del mapa de calor:** abre la comparación de esa celda aunque no esté en el catálogo, para descubrir análogos nuevos.

## 3. Contrato de datos (lo que debe generar el pipeline)

La web leerá archivos JSON estáticos de `web/public/data/`. Los nombres de las características coinciden con las columnas de `compare.py`.

### `web/public/data/comparisons.json`

```jsonc
{
  "version": "1",
  "generated_at": "2026-11-20T00:00:00Z",
  "synthetic": false,                         // true mientras se use data de muestra
  "features": [
    {
      "id": "temp_range_K",                   // = columna de compare.py
      "label": "Amplitud térmica",
      "unit": "K",
      "dimension": "temperatura",             // = Dimension de la web
      "source_earth": "MODIS Terra LST (1 km)",
      "source_target": { "luna": "LRO Diviner", "marte": "MO THEMIS" }
    }
  ],
  "targets": [
    {
      "id": "shackleton", "body": "luna", "name": "Cráter Shackleton",
      "lat": -89.67, "lng": 129.78,
      "values": { "temp_range_K": 250, "elev_m": -2000 }
    }
  ],
  "sites": [
    {
      "id": "haughton-crater",                // = id en web/src/data/sites.ts, o "cell_<lat>_<lng>"
      "lat": 75.38, "lng": -89.67,
      "values": { "temp_range_K": 60, "elev_m": 200 },
      "results": [
        {
          "target": "shackleton",
          "score": 0.26,                      // 0–1
          "sim": { "temp_range_K": 0.05, "elev_m": 0.87 },
          "best_match": "elev_m",
          "worst_match": "temp_range_K",
          "rank": 2,
          "stability": 0.94                   // fracción de corridas de --sensitivity con el mismo top
        }
      ]
    }
  ]
}
```

### Campos agregados en la versión 2 (datos reales)

| Dónde | Campo | Significado |
|---|---|---|
| `targets[]` | `lat`, `lng`, `area` | Ubicación del sitio y tamaño del área promediada (por ejemplo, `disk 10 km`) |
| `targets[]` | `excluded` | Variables apagadas para ese cuerpo porque ningún lugar de la Tierra las alcanza |
| `targets[]` | `best_score` | Mejor puntaje de toda la Tierra para ese objetivo |
| `sites[]` | `kind` | `catalog` (sitio de `sites.ts`) o `discovery` (mejor celda de una región poco conocida) |
| `sites[]` | `region`, `known`, `note` | Región de la base de Marco, si es un análogo conocido (control) y por qué está en la base |
| `sites[]` | `characterization` | Solo sitios colombianos: relieve a 200 m, ambiente, Sentinel-2, EMIT e índice PAI (Santiago). Descriptivo |
| `results[]` | `rank` | Posición entre **todas** las celdas de la Tierra |
| `results[]` | `stability` | Fracción de 100 variaciones de pesos en que sigue entre las 500 mejores celdas |

### `web/public/data/heatmap/<target>.json` (mapa de calor)

Las 2500 mejores celdas de 0,05° para ese objetivo, de mayor a menor puntaje (~55 KB por archivo):

```jsonc
{ "target": "shackleton", "cells": [[lat, lng, score], ...] }
```

### Qué necesita cada persona del equipo

| Persona | Entrega |
|---|---|
| Santiago | Datasets descargados, recortados y documentados en [RECURSOS.md](../RECURSOS.md) (fuente, resolución, fecha) |
| Marco | Datos reales en los CSV de entrada de `compare.py`. El JSON lo genera `python src/export_web.py --earth <csv> --targets <csv>`, que usa las funciones de `compare.py` sin cambiarlas. Para enlazar celdas con el catálogo, `place_hint` debe contener el nombre del sitio (ver `SITE_KEYWORDS`) |
| Web | Componentes de la sección 2, que leen el JSON; mientras tanto, prototipo con los datos sintéticos de `data/sample_*.csv`, marcados como **"datos de muestra"** |

## 4. Fases

1. ✅ **Prototipo con datos sintéticos:** `src/export_web.py` y `ComparisonPanel` con la etiqueta "datos de muestra".
2. ✅ **Datos reales:** 15 objetivos (6 de la Luna, 9 de Marte) y 15 de los 17 sitios del catálogo.
3. ✅ **Mapa de calor** en el globo y descubrimiento de análogos nuevos por región.
4. ✅ **Pesos ajustables** (con opciones predefinidas por tipo de variable) y análisis de estabilidad.

---

## 5. Mejoras para impactar al jurado

Ordenadas por impacto/esfuerzo:

| # | Mejora | Impacto | Esfuerzo |
|---|---|---|---|
| 1 | **Puntajes con datos reales + mapa de calor de "descubrimientos"** (lugares con alta similitud que no están entre los análogos conocidos) | ⭐⭐⭐ Es lo que el reto pide explícitamente | Alto (depende del pipeline) |
| 2 | **Recorrido guiado** de 60–90 s: la app vuela sola por 4–5 pares con un texto corto en cada uno. Sirve como demo en vivo y para grabar el video | ⭐⭐⭐ | Medio |
| 3 | **Versión en inglés** (selector ES/EN): el jurado es internacional | ⭐⭐⭐ | Bajo–medio |
| 4 | **Panel "Cómo lo calculamos"**: método, fórmulas, fuentes por variable y límites (gravedad, vacío, radiación) | ⭐⭐ Credibilidad científica | Bajo |
| 5 | **Enlaces compartibles**: la URL guarda el modo y el par (`?modo=tierra-marte&sitio=tatacoa`) | ⭐⭐ Útil para la presentación | Bajo |
| 6 | **Cámaras sincronizadas**: girar un globo gira el otro; o vista "lado a lado a la misma escala" | ⭐⭐ Efecto visual | Medio |
| 7 | **Pantalla de inicio** con la pregunta del proyecto y un botón "Explorar" | ⭐⭐ Primera impresión | Bajo |
| 8 | **Rendimiento**: cargar Cesium bajo demanda y mostrar una pantalla de carga | ⭐ Evita la "pantalla negra" | Bajo |
| 9 | **Móvil y accesibilidad**: navegación con teclado, contraste, tabla alternativa | ⭐ | Medio |
