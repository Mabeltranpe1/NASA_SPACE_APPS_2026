# GeoAnalog

**Análogos terrestres de las bases en la Luna y Marte** · NASA Space Apps Challenge 2026

👉 **App:** https://icy-flower-03890400f.5.azurestaticapps.net (en inglés: `?lang=en`)

GeoAnalog encuentra lugares de la Tierra que se parecen a los sitios donde se planean bases en la Luna y misiones a Marte, y explica con datos **en qué se parecen, cuánto y dónde deja de valer la analogía**. Responde al reto *Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars*.

## Qué hace

- **Búsqueda mundial:** compara **691 035 lugares** de la Tierra (celdas de ~5 km en 727 regiones áridas y frías del mundo) con **31 sitios**: las 16 regiones candidatas de Artemis en el polo sur lunar, 6 sitios a escala de cráter en la Luna y 9 sitios de Marte (Jezero, Gale, Meridiani, Gusev, Elysium, Chryse, Utopia, Vastitas Borealis y Arcadia).
- **Lugares poco estudiados:** para cada cuerpo lista los **100 mejores análogos** que no son ya conocidos, uno por región y separados al menos 300 km. Los análogos famosos (Atacama, los Valles Secos, Islandia…) se usan como control.
- **Similitud por dimensión:** además del puntaje general, cada lugar tiene un puntaje de **relieve, temperatura, superficie y roca, y aridez**. Así se ve, por ejemplo, que un lugar es un buen análogo de relieve aunque su clima no lo sea.
- **Resultados robustos:** cada lugar se prueba con 100 variaciones aleatorias de los pesos; la app marca los que se mantienen entre los mejores.
- **Globo 3D** de la Tierra, la Luna y Marte: al elegir un lugar, el globo vuela a su par en el otro cuerpo.
- **Fotos reales, lado a lado:** imágenes Sentinel-2 del lugar exacto junto a fotos de rovers, módulos de aterrizaje y órbita de la NASA.
- **Análisis detallado:** valores reales de cada variable, ranking mundial, pesos ajustables y lo que la Tierra no puede reproducir (gravedad, vacío, radiación).
- **Estudios regionales:** caracterización detallada de 18 ventanas de 10 × 10 km en Colombia, la Luna y Marte (geología, minerales, temperatura, hielo), como contexto descriptivo.
- **Buscador y API abierta:** busca análogos de cualquier sitio o de valores propios y descarga los resultados en GeoJSON, KML o waypoints para drones. Los mismos datos están en `/data/api/v1/`.
- **Español e inglés**, enlaces que se pueden compartir y un recorrido guiado.

## Cómo medimos el parecido

Cada lugar de la Tierra, la Luna y Marte se describe con las mismas variables: pendiente, rugosidad, temperatura media, amplitud térmica, albedo, tipo de roca, precipitación y vegetación. Cada diferencia se divide por una tolerancia física y se convierte en una similitud de 0 a 1:

```
d = (x_Tierra − x_sitio) / tolerancia        s = e^(−|d|)        S = e^(−√(Σ w·d² / Σ w))
```

Reglas para una comparación honesta:
- **La elevación no se compara:** cada cuerpo mide la altura desde un cero distinto.
- **Lo que la Tierra no alcanza no decide el puntaje:** ningún lugar de la Tierra llega a los 50–150 K de la Luna; esa variable se muestra como límite de la analogía.
- **Un lugar por región y a 300 km o más**, para que una sola zona no llene la lista.
- **Los puntajes sirven para comparar lugares entre sí**, no son un porcentaje de parecido: ningún lugar de la Tierra es la Luna o Marte.

El detalle está en la vista **Método** de la app y en [docs/DATOS_WEB.md](docs/DATOS_WEB.md).

## Datos

| Variable | Tierra | Luna | Marte |
|---|---|---|---|
| Relieve (pendiente, rugosidad) a 200 m | NASADEM, Copernicus DEM | LRO LOLA | HRSC + MOLA |
| Temperatura | MODIS (LST) | LRO Diviner | Mars Climate Database |
| Albedo | MODIS | LRO LOLA | MGS TES |
| Tipo de roca | ASTER GED | Diviner (calibrado) | TES (calibrado) |
| Precipitación y vegetación | GPM IMERG, MODIS NDVI | — | — |

Imágenes: NASA GIBS, Moon Trek y Mars Trek (globo), Sentinel-2 vía Microsoft Planetary Computer (vista de cerca) y la NASA Image and Video Library (fotos). Ubicación de las regiones de Artemis: Wueller et al. (2026). Catálogo completo de fuentes: [RECURSOS.md](RECURSOS.md).

## Cómo correrlo

**App web** (React, Vite y CesiumJS):
```bash
cd web
npm install
npm run dev          # http://localhost:5173
```

**Datos** (Python 3.12, con `environment.yml` o `requirements.txt`):
```bash
uv venv --python 3.12 && uv pip install -r requirements.txt
source .venv/bin/activate
pytest -q tests                                  # pruebas
python src/export_web.py                         # datos de la app (~12 min)
python src/export_images.py --prune --size 768   # imágenes Sentinel-2
python src/export_science.py                     # estudios regionales
python src/analog_api.py export-web              # base del buscador
python src/analog_api.py export-static           # API estática
```

La app se publica en Azure Static Web Apps (plan gratuito) con Terraform y GitHub Actions: [infra/README.md](infra/README.md).

## Estructura

```
├── data/        # Base de datos de la Tierra, sitios de la Luna y Marte, estudios regionales
├── src/         # Descarga, comparador (compare.py), exportación a la web y API
├── tests/       # Pruebas (pytest)
├── web/         # Aplicación web
├── infra/       # Infraestructura en Azure (Terraform)
└── docs/        # Documentación técnica
```

## Documentación

- [docs/DATOS_WEB.md](docs/DATOS_WEB.md): cómo llegan los datos a la app y qué reglas se aplican
- [docs/DATOS_Y_METODO.md](docs/DATOS_Y_METODO.md): la base de datos mundial, los sitios de la Luna y Marte y las variables (en inglés)
- [docs/PIPELINE_COMPARADOR.md](docs/PIPELINE_COMPARADOR.md): el comparador de similitud
- [docs/COMPOSICION.md](docs/COMPOSICION.md): cómo se estima el tipo de roca en la Luna y Marte
- [docs/SCIENTIFIC_DATA_CONTRACT.md](docs/SCIENTIFIC_DATA_CONTRACT.md): estudios científicos regionales
- [docs/API.md](docs/API.md): API de análogos y buscador
- [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md): arquitectura, despliegue y costos
- [docs/OBJETIVO.md](docs/OBJETIVO.md): el reto y los criterios
