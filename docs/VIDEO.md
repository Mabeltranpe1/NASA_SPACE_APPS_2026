# Grabar el video de 30 segundos

GeoAnalog tiene un **modo video**: un recorrido automático de unos 30 segundos que muestra casi todas las funciones, con un subtítulo corto en cada paso. Los pasos están en `web/src/data/tour.ts` (`DEMO_STEPS`).

## Cómo grabarlo

1. Abre la app en Chrome, en una ventana de **1920 × 1080**, en el idioma del video: https://icy-flower-03890400f.5.azurestaticapps.net/?lang=en (o `?lang=es`).
2. Pon el navegador en pantalla completa (**F11**) y **espera unos segundos** a que el globo cargue sus imágenes. Si es la primera vez, recorre la app una vez antes: así las imágenes ya quedan en caché.
3. Empieza a grabar (OBS, la grabadora de Windows con **Win + Alt + R**, o la de macOS con **Cmd + Shift + 5**).
4. Pulsa **D**. El recorrido empieza solo y termina en el paso de «Método» a los ~31 s.
5. Detén la grabación. **D** lo vuelve a empezar desde el principio (para repetir la toma) y **Esc** lo cierra.

Otra opción es abrir directamente `…/?lang=en&demo=1`: arranca solo al cargar, pero el primer paso puede salir sin las imágenes del globo si todavía no cargaron.

## Qué se ve (guion)

| Segundo | Paso | Qué muestra |
|---|---|---|
| 0–3,5 | GeoAnalog | Globo de la Tierra con los 100 mejores lugares para Marte y la lista con miniaturas |
| 3,5–7 | Los mejores análogos, por dimensión | La lista de la Luna ordenada por **relieve** (pestañas por dimensión) |
| 7–12 | Cada lugar, con su par en Marte | El mejor lugar: ficha, puntaje, barras por dimensión y mapa de similitud; el globo vuela a **Marte** |
| 12–16 | Análogos conocidos y la Luna | Haughton ≈ Shackleton; el globo vuela al **polo sur lunar** |
| 16–20 | Fotos reales, lado a lado | La ventana de fotos: la Tierra a la izquierda, la Luna o Marte a la derecha |
| 20–24 | Análisis honesto | Análisis detallado: fotos, puntaje, valores reales, ranking y límites |
| 24–28 | Busca tus propios análogos | El apartado **Buscar** con Mons Mouton (API, descargas) |
| 28–31 | GeoAnalog · método abierto | La vista **Método**: fórmula, reglas y fuentes |

## Texto para la voz o los subtítulos (opcional)

**English (≈ 30 s):**
> GeoAnalog compares 691,000 places on Earth with 31 candidate sites on the Moon and Mars, using open NASA data. It ranks the best little-studied analogs by relief, temperature, rock and aridity, flies to each counterpart in 3D, and shows real mission photos side by side. Every score explains where the analogy holds and where it breaks — and researchers can run their own searches and download the results.

**Español (≈ 30 s):**
> GeoAnalog compara 691 000 lugares de la Tierra con 31 sitios candidatos de la Luna y Marte, usando datos abiertos de la NASA. Ordena los mejores análogos poco estudiados por relieve, temperatura, roca y aridez, vuela a cada par en 3D y muestra fotos reales de las misiones lado a lado. Cada puntaje explica en qué se parece y dónde deja de valer la analogía, y cualquiera puede hacer sus propias búsquedas y descargar los resultados.

## Ajustes

- **Duración de cada paso:** campo `seconds` de cada paso en `DEMO_STEPS`.
- **Cuándo vuela a la Luna o Marte:** `bodyDelay` (milisegundos).
- **Textos:** `title` y `text`, en español e inglés.
