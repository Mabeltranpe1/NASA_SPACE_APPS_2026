# Bitácora del proyecto

Registro cronológico de decisiones, avances y problemas. **Agrega las entradas nuevas arriba**, con fecha y autor.

Formato sugerido:
```
## AAAA-MM-DD · Título corto
**Autor:** usuario de GitHub
- Qué se hizo
- Decisiones tomadas y por qué
- Problemas y cómo se resolvieron
- Pendientes
```

---

## 2026-11-15 · Release v1.1.0 a producción
**Autor:** @Ssalazarp420

- Se fusionó el PR #22 (modo video de 30 s) y se publicó `v1.1.0` en `main`.

## 2026-11-15 · Modo video del recorrido guiado (30 s)
**Autor:** @Ssalazarp420

- **Pedido:** usar el recorrido guiado para un video de 30 segundos que muestre la mayor cantidad de funciones.
- **Qué se hizo:** un **modo video** con 8 pasos cortos (`DEMO_STEPS` en `web/src/data/tour.ts`): Descubrir, pestañas por dimensión, un lugar con su par en Marte, Haughton ≈ Shackleton en la Luna, la ventana de fotos, el análisis, el apartado Buscar y el Método.
  - Se inicia con la tecla **D** (y se reinicia con D, se cierra con Esc) o con `?demo=1`. La tecla evita que el primer paso salga sin las imágenes del globo.
  - Subtítulo compacto, sin botones, que queda encima incluso de la ventana de fotos.
  - Los pasos aceptan nuevas acciones: duración propia, demora para volar a la Luna o Marte, lista y cuerpo de Descubrir, abrir la galería y buscar un sitio en «Buscar».
- **Guía de grabación** con el guion por segundo y un texto para la voz en español e inglés: [VIDEO.md](VIDEO.md).

## 2026-11-15 · Release v1.0.0 (MVP) a producción
**Autor:** @Ssalazarp420

- Se fusionó el PR #21 (nombre GeoAnalog y cierre de pendientes) y se publicó **`v1.0.0`** en `main`: la versión final del MVP para NASA Space Apps 2026. `develop` y `main` quedan iguales.

## 2026-11-15 · GeoAnalog: nombre de la app y cierre del MVP
**Autor:** @Ssalazarp420

- **Nombre:** la app se llama **GeoAnalog** (propuesta de Santiago). Cambia el título de la pestaña, el encabezado, la bienvenida, el README y los títulos de la documentación. Los recursos de Azure no cambian de nombre (renombrarlos con Terraform los recrearía y cambiaría la URL).
- **Pendientes resueltos (solo trabajo nuestro):**
  - **Buscar → globo 3D:** cada resultado del buscador tiene «Ver en el globo 3D», que abre Descubrir con el globo sobre ese lugar y lo marca.
  - Los botones «Buscar análogos» y «Consultar punto» usan el estilo principal de la app (antes usaban una clase de la versión vieja y se veían grises).
  - **Catálogo de regiones:** se queda el de Marco, que es el que generó la base; queda documentado en DATOS_WEB.
  - Se quitó `web/tests/scientific-integration.spec.ts` de Santiago: probaba partes de su rama que no se integraron (ranking global, su contrato de `comparisons.json`) y necesitaba Playwright como dependencia y una configuración que no están en el proyecto. Sus 16 pruebas de Python, que cubren los datos científicos, siguen.
  - Se borraron estilos que ya no se usaban (`.dims`, `.level`, `.tour-button`).
- **Ramas:** todo queda en `main` (v1.0.0). Las ramas de Marco y Santiago (`feature/compare_analysis`, `feature/analog-finder`, `feature/colombia-scientific-integration`, `feature/planetary-analysis`) se dejan en GitHub como referencia; lo que se usó de ellas ya está en `main`.

## 2026-11-15 · Release v0.6.0 a producción
**Autor:** @Ssalazarp420

- Se fusionó el PR #20 (22 sitios lunares de Marco, ciencia regional de Santiago y API de análogos, con un solo puntaje) y se publicó `v0.6.0` en `main`.

## 2026-11-15 · Integración del equipo: 22 sitios lunares, ciencia regional y API de análogos
**Autor:** @Ssalazarp420

- **Pedido:** adaptar lo que propusieron Marco y Santiago para que no haya conflictos y quede optimizado para la v0.5.0.
- **Decisiones aplicadas** (las recomendadas, para tener una sola versión coherente):
  1. **Una sola regla de puntaje en toda la app y en la API**: la de `export_web.py`. Las variables que la Tierra no alcanza (la temperatura de la Luna) se apagan y se muestran como límite.
  2. **El PAI de Santiago** solo aparece dentro de su panel científico, como «modelo experimental de relieve». No es un ranking ni un puntaje en otra parte.
  3. **El catálogo de regiones es el de Marco** (dueño de los datos globales). La rama de Santiago traía una versión distinta, sin algunos cuadros de Patagonia y Tierra del Fuego; queda para revisar con él.
- **Marco · `feature/compare_analysis` (22 sitios de la Luna):**
  - Se une su rama: las 9 regiones candidatas de Artemis III (NASA 2024) y las 7 de la lista de 2022 (Wueller et al. 2026), con carpetas reorganizadas (`outputs/results/`).
  - Su README en inglés pasa a `docs/DATOS_Y_METODO.md`; sus rutas nuevas se aplican en `src/export_analogos.py`.
  - `export_web.py`: ids legibles para los 16 sitios nuevos (`connecting-ridge`, `malapert`…). Si varios sitios empatan en una dimensión (la aridez es igual en todos los de la Luna), gana el de mejor puntaje general: antes todas las filas decían «≈ Shackleton rim». La prueba de robustez usa `np.partition` en vez de ordenar las 691 000 celdas (idea de Santiago).
  - Galería: los sitios nuevos usan, como alias, las fotos de su región del polo sur (visualizaciones del LRO).
  - Resultado: Mons Mouton summit sigue siendo el par más común (85 de 100 lugares), porque es el más llano, pero ahora aparecen Nobile Rim 2, Slater Plain, Peak near Cabeus B y Faustini. Panel derecho: nueva línea «También se parece a…» con los otros sitios del mismo cuerpo.
- **Santiago · `feature/colombia-scientific-integration`:**
  - Su rama salió de v0.4.2, en paralelo a v0.5.0 (11 archivos en conflicto). En lugar de unirla, se trajeron **solo sus archivos**: los scripts de extracción, `src/export_science.py`, los datos (`data/features/`, `figures/`, `processed/`, `raw/climate/`), `ScientificPanel`, sus textos, sus documentos y sus pruebas.
  - `export_science.py` se volvió a correr con los 22 sitios de Marco: sus ventanas quedan enlazadas **por geometría** con Connecting Ridge, Malapert, Mons Mouton Plateau, de Gerlache Rim 1 y 2, Peak near Shackleton, Jezero, Gale, Viking 1 y 2 y Phoenix.
  - La app lee el enlace desde `science/index.json`: el panel aparece en la ficha de los sitios de Colombia y en el análisis detallado de los sitios de la Luna y Marte.
  - **No se trajeron:** su `comparisons.json`, sus mapas de calor y la tabla «Ranking global» (mostraban otros puntajes), ni su versión de `export_web.py`.
  - Pruebas: 16 de las suyas, ajustadas (sin el CSV viejo que Marco borró, enlace por `index.json`, 31 sitios). Se quitó el `import similarity`, porque ese script reescribe una figura al importarse.
- **Marco · `feature/analog-finder` (API y «Buscar»):**
  - Salía de v0.2.0; se trajeron sus archivos y se integró como apartado **«Buscar»** en la barra lateral, con carga diferida (la base de 7 MB solo se descarga al abrirlo).
  - `analog_api.py` usa `export_web.body_weights()` y `target_id()`: **mismo puntaje y mismos ids** que la app (Mons Mouton → Desierto Occidental de Egipto, 0,645, igual que en Descubrir). Las variables apagadas van en `switched_off` y en `out_of_earth_range`.
  - Nombres legibles de las regiones en el buscador.
  - API estática en `/data/api/v1/` (31 sitios en JSON, GeoJSON, KML y waypoints). `tests/test_web_port.py`: Python y navegador coinciden en 38 búsquedas (1e-16).
- **Pendientes:** confirmar con Santiago el catálogo de regiones; pintar los resultados del buscador en el globo 3D; mover sus textos a `strings.ts`.

## 2026-11-15 · Release v0.5.0 a producción
**Autor:** @Ssalazarp420

- Se fusionó el PR #18 (búsqueda mundial de 727 regiones con un solo sistema de puntajes, que incluye la rama de Marco) y se publicó `v0.5.0` en `main`.

## 2026-11-15 · Búsqueda mundial (727 regiones) y un solo sistema de puntajes
**Autor:** @Ssalazarp420

- **Pedido:** implementar en la app los datos nuevos de Marco (búsqueda mundial y composición de la roca) y homogeneizar todo, para que los puntajes se manejen de una sola manera. Los sitios de Colombia salían muy bajos frente a los demás. Además, la sugerencia que recibió Marco: presentar los puntajes por dimensión («mejor análogo de relieve», «mejor análogo térmico») y mostrar el análisis de sensibilidad.
- **Integración de la rama de Marco** (`feature/compare_analysis`, hasta `e75ecdb`):
  - `data/earth_all.csv.gz`: ~691 000 celdas en 727 regiones (la grilla mundial de 2° sobre zonas áridas y frías), y `targets.csv` con el tipo de roca calibrado (`src/composition.py`, `docs/COMPOSICION.md`).
  - Su `src/export_web.py` chocaba con el nuestro: pasó a `src/export_analogos.py` (escribe `analogos.json`, que la app aún no usa).
  - Se quitaron los ganchos `predev`/`prebuild` que copiaban ~100 MB de PNG de `maps/` al despliegue; queda `npm run copy-images`.
- **Export (`src/export_web.py`, versión 3 del contrato):**
  - Mismos pesos que los resultados de Marco (`make_results.WEIGHTS`: sin elevación, tipo de roca a 0,5).
  - **Puntaje por dimensión** con la misma fórmula: relieve (pendiente, rugosidad), temperatura, superficie y roca (albedo, emisividad), aridez (lluvia, vegetación). `null` si no es comparable (la temperatura en la Luna).
  - **Listas (`rankings`)**: 100 lugares por cuerpo y 25 por dimensión, uno por región y separados al menos 300 km (regla de `make_top_analogos.py`). Sin la separación, la grilla llenaba la lista de cuadros vecinos de Egipto. Los empates en 1,00 de una dimensión se ordenan por el puntaje general.
  - Nombres en español e inglés (`src/region_names.py`): los cuadros de la grilla se llaman como su país y la app agrega las coordenadas.
  - Se quitó el índice PAI de Santiago de los datos de la app: un solo sistema de puntajes. Su caracterización sigue como dato descriptivo.
  - Tarda ~12 minutos (casi todo es la prueba de robustez de 100 variaciones por sitio) y genera un `comparisons.json` de 2,1 MB (~350 KB comprimido).
- **App:**
  - **Descubrir**: los 100 lugares por cuerpo con miniatura, coordenadas, filtro por país, pestañas por dimensión y la etiqueta «resultado robusto» (sigue entre los 500 mejores en ≥ 80 % de las variaciones de pesos). Todos los lugares de la lista se ven en el globo.
  - **Análogos**: «Ordenar por» general o por dimensión. Reemplaza el filtro «Debe parecerse en…», que usaba niveles cualitativos de la bibliografía, no cálculos. También se quitó de la ficha la «Similitud por dimensión (preliminar)».
  - **Panel derecho**: barras «Por dimensión». **Análisis detallado**: «Comparar por» usa las mismas dimensiones.
  - Si el homólogo de un sitio no está en la base, se compara con el **objetivo más parecido** de ese cuerpo (antes era el primero de la lista, al azar). Pasaba con la Tatacoa (homólogo Medusae Fossae, del PAI).
  - Método, recorrido guiado e intro con las cifras nuevas, la regla de 300 km, los países que no cubre la búsqueda y la aclaración de que los puntajes sirven para comparar lugares entre sí.
- **Resultados que cambian:**
  - Mejor análogo general de Marte: Egipto (23,8° N, 32,9° E) ≈ Meridiani, 26/100; de la Luna: el Desierto Occidental de Egipto ≈ Mons Mouton, 64/100.
  - North Greenland ≈ Gale ya no está arriba en general, pero Groenlandia y Canadá encabezan la lista de **temperatura** de Marte.
  - **Colombia en las dimensiones**: La Guajira 97 en relieve; la Tatacoa 76 en relieve y 76 en superficie, pero 0 en aridez. El puntaje general sigue bajo por la lluvia y la vegetación, y ahora se ve por qué.
- **Imágenes:** `export_images.py --prune --size 768` genera las de los lugares nuevos y borra las de los que ya no están.
- **Pendientes:** Marco debe decidir si quita las regiones nombradas en países que la grilla excluye (Tíbet, Taklamakán, Gobi, Lut, Rub al-Jali, Kamchatka); Santiago está adaptando su trabajo al de Marco (sitios y homólogos de Colombia).

## 2026-11-15 · Release v0.4.2 a producción
**Autor:** @Ssalazarp420

- Se fusionó el PR #17 (valores reales y lugares parecidos en la vista principal) y se publicó `v0.4.2` en `main`.

## 2026-11-15 · Valores reales y lugares parecidos en la vista principal
**Autor:** @Ssalazarp420

- **Pedido:** (1) indicar en la lista si cada sitio es poco o muy estudiado, solo como texto; (2) llevar el gráfico «Valores reales» del análisis detallado a la vista principal; (3) idea de Marco: ver los otros lugares parecidos con sus coordenadas y una miniatura del mejor, también en la lista de Análogos.
- **Qué se hizo:**
  - **Lista de Análogos:** cada fila tiene la miniatura de Sentinel-2 del sitio, con los puntos de la Luna o Marte encima, y el texto «Muy estudiado» o «Poco estudiado». El orden por similitud no cambia.
  - **Panel derecho:** las barras de similitud por variable se reemplazaron por los **valores reales**. Cada variable muestra el valor de la Tierra y el de la Luna o Marte sobre la misma escala física. Siguen ordenadas de la más parecida a la menos parecida, con las marcas ✓ y ⚠.
  - **Panel derecho, «Mejores lugares de la Tierra para …»:** los 5 mejores lugares (uno por región) con sus coordenadas y su índice. El primero lleva una miniatura. Al tocar uno, el globo vuela a ese lugar y lo marca.
- **Código:** el formato de números, la escala del gráfico y las coordenadas están en `web/src/data/format.ts`, compartidos con el análisis detallado. La miniatura de la Tierra es `components/EarthThumb.tsx`.

## 2026-11-15 · Release v0.4.1 a producción
**Autor:** @Ssalazarp420

- Se fusionó el PR #16 (análogos ordenados de más a menos similar) y se publicó `v0.4.1` en `main`.

## 2026-11-15 · Análogos ordenados de más a menos similar
**Autor:** @Ssalazarp420

- **Pedido:** en la pestaña «Análogos» del panel izquierdo, ordenar los sitios de más a menos similar para ver de un vistazo cuál es más compatible.
- **Qué se hizo:**
  - Las dos listas (análogos de referencia y caso de estudio Colombia) y la cuadrícula de la sección Análisis se ordenan por el **índice de similitud** (0–100). Es el mismo número del panel derecho.
  - Cada fila muestra el índice en una pastilla del color del cuerpo con el que se compara (Luna o Marte). Si un sitio tiene par en ambos, cuenta el más parecido.
  - Al abrir un sitio desde la lista, el panel derecho ya lo compara con ese cuerpo, para que el número de la lista y el del panel coincidan. Ejemplo: Haughton da 12/100 con Gale (Marte) y solo 2/100 con Shackleton (Luna).
  - Los sitios sin resultado en la base de datos (Timanfaya y Lava Beds, cuyas regiones aún faltan) van al final, sin número.
- **Decisión:** la regla para elegir el objetivo comparado (el par si está en la base, si no el primer objetivo del cuerpo con resultado) quedó en una sola función, `comparedTarget()` en `web/src/data/focus.ts`, que usan la lista y el panel derecho.

## 2026-11-15 · Release v0.4.0 a producción
**Autor:** @Ssalazarp420

- Se fusionó el PR #15 (galería de fotos reales con carruseles) y se publicó `v0.4.0` en `main`.
- **Producción:** https://icy-flower-03890400f.5.azurestaticapps.net

## 2026-11-15 · Galería de fotos reales (carruseles)
**Autor:** @Ssalazarp420

- **Pedido:** ver un pequeño catálogo de fotos de cada sitio en lugar del simple acercamiento al globo 3D, con imágenes de buena resolución como las de Perseverance.
- **Qué se hizo:**
  - En la ventana para comparar y en la sección Análisis hay dos **carruseles**: la Tierra a la izquierda y la Luna o Marte a la derecha. Tienen flechas, puntos, teclado (← →) y deslizamiento en móvil.
  - En la Tierra, primero va el recorte de Sentinel-2 del punto exacto y después las fotos.
  - En la Luna y Marte van las fotos, y al final la vista 3D interactiva.
  - El panel derecho tiene un botón **Ver galería · N imágenes**.
- **96 fotos de la NASA para 40 lugares**, elegidas a mano de la NASA Image and Video Library y del Scientific Visualization Studio:
  - **Marte:** fotos de Perseverance, Curiosity, Spirit, Opportunity, Phoenix, Viking 1 y 2 e InSight; HiRISE y MOC para los sitios sin aterrizaje.
  - **Luna:** fotos del Apolo 11, el pozo de Marius Hills del LRO y visualizaciones del LRO de las regiones de Artemis III.
  - **Tierra:** rovers K10 de la NASA en Haughton, prueba de un dron para Marte en Death Valley, el radar RIMFAX en Svalbard, estromatolitos en Pilbara, fotos de astronautas de Uyuni, el Nevado del Ruiz, La Guajira, el Tibesti, el Ténéré, el Gran Mar de Arena y el Taklamakán, e imágenes del satélite Terra.
- **Honestidad:**
  - Cada foto dice si es "Desde el rover", "Desde órbita", una "Visualización con datos del LRO", una "Foto de campo", etc.
  - Las fotos de las regiones de los descubrimientos llevan el aviso "Foto de la región, no del punto exacto".
  - Se leyó la descripción de cada foto antes de incluirla. Así se descartaron una foto del salar de Coipasa titulada como Uyuni, una de la parte peruana de Atacama y las ilustraciones artísticas.
- **Problemas resueltos:**
  - El crédito de cada misión no estaba en la descripción sino en el campo `secondary_creator`. Lo detectó un test. Ahora se cita completo, por ejemplo "NASA/JPL-Caltech/MSSS".
  - Una panorámica original de 195 megapíxeles detuvo el script. Ahora los JPEG enormes se decodifican a escala reducida.
  - El recorte de bordes negros confundía las sombras lunares con borde vacío. Ahora solo quita filas o columnas casi totalmente negras.
- **Tamaño:** ~25 MB de imágenes. Con las de Sentinel-2, la app sirve ~41 MB de imágenes estáticas, dentro del plan Free de Azure Static Web Apps.
- **Tests:** `tests/test_export_gallery.py` comprueba la lista curada, que todo objetivo de la Luna y Marte tenga fotos, el recorte de bordes y la lectura del crédito.

## 2026-11-15 · Release v0.3.2 a producción
**Autor:** @Ssalazarp420

- Se fusionó el PR #14 (imágenes de Sentinel-2 y corrección del panel duplicado) y se publicó `v0.3.2` en `main`.
- **Producción:** https://icy-flower-03890400f.5.azurestaticapps.net

## 2026-11-15 · Imágenes de Sentinel-2 (Microsoft Planetary Computer)
**Autor:** @Ssalazarp420

- Las imágenes de cerca de la Tierra (ficha, miniaturas, ventana para comparar y análisis) pasan de **Landsat WELD (30 m, año 2000)** a **Sentinel-2 L2A (10 m, 2021–2025)**.
  - Las genera el script nuevo `src/export_images.py` con el catálogo gratuito de Microsoft Planetary Computer, sin cuenta ni clave.
  - Se guardan como JPEG en `web/public/images/earth/` (73 imágenes, 16 MB) con un `index.json` que cita la escena, la fecha y la nubosidad.
- **Por qué pregeneradas y no en vivo:** cada recorte en vivo pesa ~1,7 MB y tarda varios segundos. Con los archivos estáticos, la demo no depende de un servidor externo. Si alguna imagen falta o no carga, la app usa la de NASA GIBS como antes.
- **Problemas encontrados y resueltos:**
  - **Bordes de tesela:** si el recorte caía entre dos teselas de Sentinel-2, ninguna lo cubría entero (North Greenland, Fezzan, Mauna Kea). Se unen las teselas de la misma pasada.
  - **Imágenes quemadas:** el producto de color verdadero (`visual`) satura la arena, la sal y el hielo; Tenere Niger salía casi blanco. Esas imágenes (43 de 73) se renderizan desde las bandas B04, B03 y B02 con una escala de 1000 a 9000, porque los valores L2A llevan un desplazamiento de +1000.
  - **Nieve en latitudes altas:** Haughton salía nevado (escena de septiembre). Por encima de 60° solo se aceptan escenas de verano. Ahora se ve el anillo completo del cráter.
  - **Landsat C2 como respaldo:** el Planetary Computer devuelve error 500 al renderizar sus recortes, así que se descartó.
- **Corrección de la interfaz:** al cambiar de lugar se veían dos fichas encimadas en el panel izquierdo. La causa era que los paneles izquierdo y derecho compartían la misma `key` de React. Ahora cada uno tiene la suya.
- **Créditos:** la ficha y la ventana muestran "Copernicus Sentinel-2 (ESA) · Microsoft Planetary Computer". La vista Método y RECURSOS.md agregan la fuente.
- **Tests:** `tests/test_export_images.py` cubre, sin red, el recorte cuadrado, la detección de bordes vacíos y la lista de lugares.

## 2026-11-15 · Release v0.3.1 a producción
**Autor:** @Ssalazarp420

- Se fusionó el PR #13 (ventana para comparar imágenes) y se publicó `v0.3.1` en `main`.
- **Producción:** https://icy-flower-03890400f.5.azurestaticapps.net

## 2026-11-15 · Ventana para comparar imágenes
**Autor:** @Ssalazarp420

- Al hacer clic en la imagen de la ficha (panel izquierdo) se abre una **ventana emergente**:
  - a la izquierda, la imagen de la Tierra: Landsat, o MODIS por encima de 78°;
  - a la derecha, la vista de cerca del homólogo en la Luna o Marte, con el botón Imagen/Relieve en Marte.
  - Si el lugar tiene homólogo en los dos cuerpos, se cambia con los botones Luna · Marte. Empieza en el cuerpo que se esté comparando en el panel derecho.
- Se cierra con Esc, con el botón ✕ o haciendo clic fuera. En móvil las imágenes quedan una encima de la otra.
- La ventana avisa que cada imagen tiene su propia escala. La de la Luna o Marte se puede acercar o arrastrar.
- **Polo sur lunar:** en la ventana grande se notaba la deformación del mosaico global cerca del polo. Ahí la cámara se aleja más (14 veces la altura normal, frente a 6 en las imágenes pequeñas).
- **Detalle técnico:** la ventana usa `createPortal` hacia `body`, porque el panel tiene `backdrop-filter` y eso encerraría un `position: fixed`.

## 2026-11-14 · Release v0.3.0 a producción
**Autor:** @Ssalazarp420

- Se fusionaron en `develop` los PR #11 (datos reales de Marco y Santiago) y #12 (rediseño visual), y se publicó el release `v0.3.0` en `main`.
- **Producción:** https://icy-flower-03890400f.5.azurestaticapps.net (inglés: `?lang=en`).
- **Contenido de la versión:**
  - Datos reales: búsqueda global en 163 998 celdas, 15 objetivos de la Luna y Marte, y el caso de estudio de Colombia.
  - Un solo globo con selector Tierra · Luna · Marte y paneles flotantes.
  - Secciones Descubrir, Análogos, Análisis y Método.
  - Pantalla de bienvenida, buscador, enlaces que se pueden compartir y recorrido guiado de 7 pasos.
- **Pendientes:** los de [DATOS_WEB.md](DATOS_WEB.md#pendientes-conocidos), y cargar Cesium bajo demanda (la app pesa ~1,2 MB comprimida).

## 2026-11-14 · Rediseño visual: un solo globo y paneles flotantes
**Autor:** @Ssalazarp420

- **Objetivo:** mejorar la primera impresión ante el público y el jurado. Se tomaron como referencia dos conceptos de interfaz espacial: un globo central con paneles de vidrio.
- **Un solo globo** en lugar de dos lado a lado. Los botones **Tierra · Luna · Marte** cambian el cuerpo y el globo vuela al homólogo del lugar elegido.
  - Si el lugar no tiene homólogo en un cuerpo, ese botón queda **bloqueado** con un candado. Por ejemplo, Atacama solo se compara con Marte.
  - Desaparecen los modos Tierra ↔ Luna, Tierra ↔ Marte y Luna ↔ Marte: el par lo define el lugar.
  - Ganancia: un visor de Cesium menos en la vista principal.
- **Barra de navegación** con cuatro secciones:
  - **Descubrir** (vista inicial): la búsqueda global es la respuesta principal.
  - **Análogos:** el catálogo y Colombia.
  - **Análisis:** la comparación detallada.
  - **Método:** la fórmula, las reglas, las fuentes, los límites y el equipo.
- **Paneles flotantes:**
  - a la izquierda, la ficha del lugar con su imagen;
  - a la derecha, las miniaturas de la Tierra, la Luna y Marte, y el **índice de similitud** en anillo, con la posición global, la estabilidad y las barras por variable.
- **Pantalla de bienvenida** con la pregunta del proyecto y las cifras reales del JSON (163 998 celdas, 43 regiones, 15 sitios).
- **Otras mejoras:**
  - buscador de lugares;
  - enlaces que se pueden compartir (`?view=sites&site=tatacoa`);
  - giro lento del globo en reposo;
  - tipografía Inter + Space Grotesk;
  - versión móvil con la navegación abajo.
- **Recorrido guiado de 7 pasos:** se agregó uno sobre la búsqueda global, y en cada parada el globo pasa de la Tierra al homólogo.
- **Decisiones para no exagerar los datos:**
  - Las barras de la referencia del tipo "Tierra 92 % · Luna 78 %" no se copiaron: la Tierra no se compara consigo misma. Se muestran barras por variable frente al objetivo.
  - No se usan etiquetas como "similitud alta", que no están validadas (ver el documento de Santiago). Se muestra el número, la posición y la estabilidad.
  - Las imágenes son las de NASA (GIBS, Moon Trek y Mars Trek), no fotos de stock.
- **Hallazgo:** con el puntaje completo, los sitios del catálogo dan 1–12/100 frente a su homólogo, mientras que el mejor descubrimiento (North Greenland ≈ Gale) da 35/100, queda #62 de 163 998 y es estable en el 100 % de las variaciones. Por eso el último paso del recorrido usa ese ejemplo.
- **Correcciones:**
  - Landsat WELD no tiene datos por encima de ~78° (la imagen salía negra en North Greenland y Ellesmere); ahí se usa MODIS Terra de verano.
  - Si el homólogo del catálogo no está en la base (Medusae Fossae, Eberswalde, Tranquillitatis…), el índice usa el primer objetivo con datos de ese cuerpo, igual que la comparación detallada.
- **Verificación:** `tsc`, `oxlint` y `vite build` sin errores. Capturas con Chromium (Playwright) de todas las vistas, del recorrido completo y del móvil (390 px), sin errores en consola.

## 2026-11-14 · Datos reales en la app (Marco + Santiago)
**Autor:** @Ssalazarp420

- **Integración:** la rama `feature/web-real-data` junta el trabajo de los dos.
  - **Marco** (`feature/compare_analysis`): base global de ~164 000 celdas en 43 regiones, 15 objetivos de la Luna y Marte, y el nuevo `compare.py` con tolerancias físicas. Su README técnico pasó a `docs/PIPELINE_COMPARADOR.md`.
  - **Relieve a 200 m:** Marco subió durante la integración la versión con pendiente y rugosidad medidas a 200 m en los tres cuerpos (`terrain_common.py`), como se había acordado. Los datos de la app se regeneraron con esa versión.
  - **Santiago** (`feature/planetary-analysis`): CSV de `data/features/`, ranking PAI, scripts y su documento técnico (`docs/CONTEXTO_TECNICO_SANTIAGO.md`). No se trajeron los GeoTIFF, las series crudas ni las figuras.
- **Decisión de alcance:** búsqueda en **todo el mundo** (base de Marco), con Colombia destacada. Se agregaron al catálogo los 5 sitios colombianos de Santiago: La Guajira, Nevado del Ruiz, Nevado Santa Isabel, Volcán Puracé y La Candelaria.
- **`src/export_web.py` reescrito.** Usa `compare.py` sin cambiar la fórmula y aplica tres reglas (ver [DATOS_WEB.md](DATOS_WEB.md)):
  - La elevación no se compara: cada cuerpo mide la altura desde un cero distinto.
  - Una variable que ningún lugar de la Tierra alcanza se apaga para ese cuerpo y se muestra como límite. En la Luna se apagan la temperatura media y la amplitud térmica; en Marte, la amplitud térmica.
  - Los descubrimientos se eligen por región.
- **Problema encontrado y corregido:** con la configuración por defecto, los 20 mejores lugares de los 15 objetivos salían **todos** del norte de Groenlandia. Mandaban la temperatura (la Luna está a 50–125 K) y la elevación (con ceros distintos). Con las reglas anteriores aparecen el Desierto Occidental de Egipto y Fezzan (Libia) para la Luna, y Groenlandia, el Sahara central y el Tíbet para Marte.
- **Validación:** los análogos conocidos (controles) quedan arriba. Las mejores celdas del planeta para la Luna y Marte están en la Antártida, y McMurdo queda #171 de 164 000 para Jezero.
- **Web:**
  - Mapa de similitud en el globo de la Tierra.
  - Ranking con un lugar por región; al hacer clic, el globo vuela al lugar.
  - Botones "Comparar por: Todo · Relieve · Superficie · Clima y agua".
  - Etiqueta "fuera del rango de la Tierra" en las variables apagadas.
  - Posición del sitio entre todas las celdas de la Tierra.
  - Caracterización de Santiago en la ficha de los sitios colombianos.
- **Corrección:** los marcadores del otro lado del planeta se veían a través del globo; ahora quedan ocultos.
- **Decisión: la búsqueda global de Marco es la respuesta principal (opción A).**
  - La barra lateral muestra primero los lugares poco estudiados encontrados.
  - Los 6 sitios de Santiago pasan a una sección "Caso de estudio: Colombia", comparados solo por relieve.
  - Sus homólogos se eligieron con el mismo criterio: mejor índice PAI entre los objetivos con datos. Se corrigió el del Nevado del Ruiz, que pasa de Shackleton (24) a de Gerlache (47).
  - El motivo es que antes la ficha decía "se parece a Shackleton" mientras el puntaje completo daba 2/100.
- **Precipitación:** la tolerancia estricta es intencional. Marco busca lugares casi sin lluvia, como la Luna y Marte.
- **Calidad de IMERG en latitudes altas** (comparación con ERA5-Land en 2023 hecha con Earth Engine): IMERG da 0 mm en toda la Antártida (ERA5-Land: 23–94 mm) y 20 mm en el norte de Groenlandia frente a 137 mm. Esto infla la posición de Groenlandia como análogo de Marte. Propuesta para Marco: ERA5-Land por encima de 60°.
- **Entorno:** se agregaron a `requirements.txt` y `environment.yml` las librerías que usan los scripts (`scipy`, `pyproj`, `requests`, `h5py`, `pyhdf`, `earthaccess`). Earth Engine (API de Python) quedó configurado en la máquina de @Ssalazarp420.
- **Pendientes** (detalle en [DATOS_WEB.md](DATOS_WEB.md#pendientes-conocidos)):
  - Regiones para Timanfaya y Lava Beds.
  - Revisar la lluvia de IMERG en latitudes altas (menos confiable por encima de 60°). La tolerancia estricta de la precipitación es intencional: Marco buscó lugares casi sin lluvia, como la Luna y Marte.
  - Máscara de mar en La Guajira.
  - Temperatura de Diviner para los sitios de Artemis de Santiago.
  - Procesar EMIT.

## 2026-11-14 · Release v0.2.0 a producción
**Autor:** @Ssalazarp420

- Se fusionaron en `develop` los PR #5 (entorno de Python), #6 (globos 3D), #7 (comparación detallada), #8 (recorrido guiado) y #9 (inglés), y se publicó el release `v0.2.0` en `main`.
- **Producción:** https://icy-flower-03890400f.5.azurestaticapps.net (inglés: `?lang=en`).
- **Contenido de la versión:**
  - Globos 3D lado a lado de la Tierra, la Luna y Marte, con homólogos.
  - Imágenes de detalle.
  - Comparación detallada con datos de muestra.
  - Recorrido guiado.
  - Español e inglés.
- **Documentación actualizada:** ARQUITECTURA (pipeline `compare.py` → `export_web.py` → web, estructura del código, idiomas) y README (enlace y guía de uso).
- **Pendientes:**
  - Datos reales de Santiago y Marco para reemplazar los sintéticos.
  - Mapa de calor global de similitud.
  - Proteger `main` y `develop` (requiere admin).
  - Cargar Cesium bajo demanda (la app pesa 1,2 MB comprimida).

## 2026-11-14 · Versión en inglés (ES | EN)
**Autor:** @Ssalazarp420

- Selector **ES | EN** en la barra lateral. Toda la app está traducida: interfaz, fichas de los 12 sitios, homólogos, capas NASA, comparación detallada, límites físicos y recorrido guiado.
- **Idioma inicial:** el del navegador (inglés salvo que prefiera español), pensado para el jurado internacional. Se recuerda la elección y se puede forzar con `?lang=en` o `?lang=es`, útil para compartir enlaces.
- **Implementación** sin librerías:
  - `web/src/i18n/strings.ts`: diccionario.
  - `LanguageContext.tsx` + `useLang.ts`: contexto y hook.
  - `web/src/data/sites.en.ts`: textos en inglés del catálogo.
- **Para agregar un texto nuevo:** crear la clave en `strings.ts` en los dos idiomas y usar `t('clave')`.
- **Límite del plan Free:** Azure Static Web Apps admite solo **3 entornos de vista previa**. Con 4 PRs abiertos, el despliegue del #9 falló; se borró el entorno del #6 (`az staticwebapp environment delete ... --environment-name 6`), cuyo contenido ya está incluido en #9. **Recomendación:** fusionar los PRs pronto para no acumular más de 3 abiertos con cambios en `web/`.

## 2026-11-14 · Recorrido guiado
**Autor:** @Ssalazarp420

- Botón **▶ Recorrido guiado**: la app recorre sola 6 paradas (introducción, Haughton ≈ Shackleton, Atacama ≈ Phoenix, la Tatacoa, tubos de lava en la Luna y Marte, y la comparación detallada), 12 s por paso.
- Controles: anterior, pausa, siguiente y cerrar; teclado: ← →, espacio y Esc.
- **Uso previsto:** demo en vivo ante el jurado y grabación del video del proyecto.
- Los textos están en `web/src/data/tour.ts` para que el equipo los ajuste.

## 2026-11-14 · Prototipo de la comparación detallada
**Autor:** @Ssalazarp420

- **`src/export_web.py`:** convierte la salida de `compare.py` (de Marco) en `web/public/data/comparisons.json` siguiendo el contrato de datos. No cambia la fórmula: llama a `compare_all` y `weight_sensitivity`.
- **`ComparisonPanel`** (debajo de las imágenes):
  - Puntaje 0–100, posición en el ranking y estabilidad ante cambios de pesos.
  - Barras de similitud por característica, con "✓ más parecido" y "⚠ rompe la analogía" (icono y texto, no solo color).
  - Pesos ajustables con recálculo exacto en el navegador (misma fórmula de `compare.py`).
  - Valores reales Tierra vs. Luna/Marte, cada variable con su escala física fija.
  - Ranking de los mejores lugares de la Tierra, incluidos los que no están en el catálogo.
  - Límites físicos (gravedad, atmósfera, campo magnético, duración del día), fuentes previstas y tabla de datos.
- **Colores de identidad validados** con el verificador de paletas (daltonismo, luminosidad y contraste): Tierra `#3d8ef0`, Luna `#b08f24`, Marte `#cf4a3c`. El gris anterior de la Luna fallaba por leerse como gris de "desactivado".
- **Datos:** todavía son los **sintéticos** de `data/sample_*.csv`; la interfaz lo indica con una etiqueta visible. Con esos datos hay comparación para Haughton, Atacama, McMurdo y Mauna Kea.

## 2026-11-14 · Globos 3D lado a lado (Tierra, Luna y Marte)
**Autor:** @Ssalazarp420

- **Contexto del equipo:**
  - Marco trabaja en el código Python para vectorizar la información.
  - Santiago descarga las bases de datos para comparar a mayor escala y detalle.
  - Mientras tanto se avanza en la visualización.
- **Cambio:** MapLibre se reemplazó por **CesiumJS** (código abierto, sin Cesium ion).
  - **Motivo:** la proyección Mercator de MapLibre no muestra más allá de ±85°, y la base lunar candidata (cráter Shackleton) está a −89,7°.
  - Cesium permite un visor por cuerpo con su elipsoide real.
- **Nuevas funciones:**
  - **Modos de comparación:** Tierra ↔ Luna, Tierra ↔ Marte y Luna ↔ Marte, con dos globos lado a lado.
  - **Homólogos:** cada sitio terrestre tiene su lugar en la Luna y/o Marte, con coordenadas de sitios de misiones (Shackleton, Apolo 11, Marius Hills, Phoenix, Viking 2, Gale, Jezero, Meridiani, Gusev, Arsia Mons, Eberswalde). Medusae Fossae y Terra Sirenum están marcados como ubicaciones aproximadas.
  - **Imágenes de detalle debajo de los globos:**
    - Tierra: Landsat WELD (30 m/px) desde la GIBS Snapshot API. Para McMurdo y Svalbard, que Landsat no cubre, se usa MODIS Terra en una fecha de verano.
    - Luna: LRO WAC (NASA Moon Trek).
    - Marte: Viking MDIM 2.1 (NASA Mars Trek), con botón para cambiar a relieve MOLA.
- **Problemas resueltos:**
  - `vite-plugin-static-copy` v4 copiaba los assets de Cesium con la ruta completa (`node_modules/...`), así que el cielo y los logos fallaban y el render se detenía. Se corrigió con `rename: { stripBase: 4 }`.
  - Suomi NPP ya no publica imágenes recientes en GIBS; se usa NOAA-20.
  - El mosaico WAC se deforma cerca del polo; la vista de detalle se aleja en sitios con latitud mayor a 80°.
  - No se encontró en Trek un relieve LOLA global con el nombre esperado; queda pendiente para la Luna.
- **Verificación:** capturas automáticas con Chromium (Playwright) de los tres modos, sin errores en consola.
- **Plan:** [VISUALIZACION_COMPARACION.md](VISUALIZACION_COMPARACION.md) describe la vista de comparación detallada, el contrato de datos JSON para el pipeline y las mejoras propuestas para el jurado.

## 2026-11-14 · Release v0.1.0 a producción
**Autor:** @Ssalazarp420

- Se fusionaron los PR #1 (estructura y git flow), #2 (plataforma web e infraestructura) y #3 (mapa con NASA GIBS) en `develop`.
- Se creó el release `v0.1.0` con git flow (`develop` → `main`), que despliega en producción: https://icy-flower-03890400f.5.azurestaticapps.net
- Contenido de la versión:
  - mapa (globo 3D) con capas de NASA GIBS;
  - filtros por objetivo, ambiente y dimensión;
  - 12 sitios con valores cualitativos preliminares;
  - enlace a Google Earth.
- Se agregó [GOOGLE_MAPS_API_KEY.md](GOOGLE_MAPS_API_KEY.md) para que Marco (Mabeltranpe1) pruebe una key con su cuenta de Google Cloud.
- **Pendientes:**
  - Resultado de la prueba de la key de Marco.
  - Borrar el secret `VITE_GOOGLE_MAPS_API_KEY` y la key anterior si no se usan.
  - Poner `develop` como rama por defecto y proteger `main` y `develop` (requiere admin).
  - Empezar el pipeline de puntajes de similitud con datos reales.

## 2026-11-14 · Google Maps bloqueado por la facturación: se pasa a NASA GIBS
**Autor:** @Ssalazarp420

**Intento:**
- Se creó una API key de Google Maps en un proyecto nuevo de Google Cloud ("My First Project").
- Se restringió por referrer y por API (solo Maps JavaScript API) y se cargó como secret en GitHub.
- Al intentar crear la alerta de presupuesto, la consola quedó en un bucle de *Enable billing*.

**Hallazgos:**
- La cuenta de facturación es una **"Cuenta de prueba gratuita"** (90 días), pero aparece **"cerrada"**.
- En Colombia, Google Cloud exige un **prepago (100.000 COP)** para activar la cuenta de facturación, incluso en la prueba gratuita. El prepago queda como saldo a favor, pero es dinero adelantado.
- Mientras la cuenta esté cerrada, el proyecto **no puede usar la Maps JavaScript API**: el mapa no carga y no se pueden crear presupuestos ni alertas.
- Costo real a la fecha: **USD 0**.

**Decisión:**
- **No hacer el prepago**, por la regla del proyecto de usar solo servicios gratuitos.
- Reemplazar Google Maps por **MapLibre GL JS** (código abierto) con capas de **NASA GIBS**: Blue Marble, VIIRS color verdadero, relieve ASTER GDEM y temperatura superficial MODIS. No requiere key ni facturación, y el mapa base pasa a ser **datos abiertos de la NASA**, lo que refuerza la propuesta ante el reto.
- Se mantiene el botón **"Ver en Google Earth"**: es un enlace y no requiere API.
- Si más adelante el equipo decide hacer el prepago, se puede volver a Google Maps (el mapa está aislado en un solo componente).

**Evaluado y pospuesto:** Google AI Studio (API de Gemini).
- No reemplaza al mapa, pero podría servir para búsqueda en lenguaje natural o para redactar las fichas.
- Su key no puede ir en el frontend: requeriría un backend (Azure Functions, incluido en Static Web Apps Free).
- Queda como mejora futura.

**Pendientes:**
- Eliminar el secret `VITE_GOOGLE_MAPS_API_KEY` de GitHub.
- Borrar o desactivar la API key en Google Cloud.

## 2026-11-14 · Restricciones de la API key de Google Maps
**Autor:** @Ssalazarp420

- Se restringió la key por referrer:
  - `http://localhost:5173/*`
  - `https://icy-flower-03890400f.5.azurestaticapps.net/*`
  - `https://*.eastus2.5.azurestaticapps.net/*`
- **Problema:** Google rechaza comodines en medio de un dominio (`icy-flower-03890400f-*.eastus2...`). **Solución:** usar `*.eastus2.5.azurestaticapps.net`, que cubre las vistas previas de los PRs.
- Restricción de API: **solo Maps JavaScript API**. Antes había 32 APIs habilitadas en la key; se redujeron a una para que, si alguien copia la key desde el navegador, no pueda usarla en otros servicios con facturación.
- **Pendiente:**
  - quitar el referrer genérico `https://*.azurestaticapps.net/*`, que es demasiado amplio;
  - confirmar el límite diario de cuota y la alerta de presupuesto.

## 2026-11-14 · Primer despliegue en Azure
**Autor:** @Ssalazarp420

- `terraform apply` creó `rg-nasa-analogs` y `swa-nasa-analogs` (plan Free, eastus2).
- Se cargaron los secrets `AZURE_STATIC_WEB_APPS_API_TOKEN` y `VITE_GOOGLE_MAPS_API_KEY` en GitHub.
- La vista previa del PR #2 quedó funcionando: https://icy-flower-03890400f-2.eastus2.5.azurestaticapps.net
- **Problemas:**
  - El primer despliegue falló con `ApiToken is invalid` porque corrió antes de cargar el token. Se resolvió volviendo a ejecutar el workflow.
  - El secret de Google Maps quedó vacío en el primer intento (se pegó la key en el texto del prompt de `read`). Se volvió a cargar y se verificó que el bundle publicado incluye una key válida.
  - El workflow usaba un input inexistente (`skip_api_build`) y acciones con Node 20. Se corrigió y se pasó a `checkout@v5` y `setup-node@v5`.

## 2026-11-14 · Plataforma web e infraestructura
**Autor:** @Ssalazarp420

- Se creó la app en `web/` con React 19 + Vite + TypeScript y Google Maps (`@vis.gl/react-google-maps`).
- Filtros por objetivo, ambiente y dimensión; ficha por sitio con límites de la analogía; enlace a Google Earth.
- Catálogo inicial de 12 sitios con valores **cualitativos preliminares** (por ejemplo, la Tatacoa como candidato poco estudiado).
- Infraestructura en `infra/` con Terraform y despliegue con GitHub Actions.
- **Decisiones:**
  - **Solo planes gratuitos**; cualquier servicio de pago se consulta antes.
  - **Toda la infraestructura con Terraform**, nada creado a mano en el portal.
  - **Azure Static Web Apps (Free)** en lugar de App Service: el frontend es estático y el plan Free incluye vistas previas por PR.
  - **Google Maps**: elegido por el equipo; se usa con restricciones y cuota para no generar costos.
  - **Datos precalculados**: los puntajes se calculan offline en Python y la web solo los lee, sin backend.
- **Entorno:**
  - Terraform 1.17.2 instalado en `~/.local/bin`.
  - Azure CLI 2.92.0.
  - Docker Desktop pendiente de integrarse con WSL.

## 2026-11-14 · Inicio del proyecto
**Autor:** @Ssalazarp420

- Se clonó el repositorio y se inicializó **git flow** (`main` / `develop`, prefijos estándar, tags `v`).
- Se documentaron el contexto del reto (README), las fuentes de datos (RECURSOS.md) y el flujo de trabajo (CONTRIBUTING.md).
- **Problema:** la página del reto (spaceappschallenge.org) y los datasets de la CSA no cargan desde WSL por un certificado raíz faltante ("AAA Certificate Services"). **Solución temporal:** consultar esas páginas desde el navegador de Windows.
- Mabeltranpe1 agregó colaboradores con permiso de escritura.
- **Pendientes:**
  - fusionar los PR #1 y #2;
  - poner `develop` como rama por defecto y proteger `main` y `develop` (requiere admin);
  - empezar el pipeline de datos (Diviner y LOLA frente a MODIS y SRTM).
