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

## 2026-11-14 · Versión en inglés (ES | EN)
**Autor:** @Ssalazarp420

- Selector **ES | EN** en la barra lateral. Toda la app está traducida: interfaz, fichas de los 12 sitios, homólogos, capas NASA, comparación detallada, límites físicos y recorrido guiado.
- **Idioma inicial:** el del navegador (inglés salvo que prefiera español), pensado para el jurado internacional. Se recuerda la elección y se puede forzar con `?lang=en` o `?lang=es`, útil para compartir enlaces.
- **Implementación** sin librerías:
  - `web/src/i18n/strings.ts`: diccionario.
  - `LanguageContext.tsx` + `useLang.ts`: contexto y hook.
  - `web/src/data/sites.en.ts`: textos en inglés del catálogo.
- **Para agregar un texto nuevo:** crear la clave en `strings.ts` en los dos idiomas y usar `t('clave')`.

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
