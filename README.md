# NASA Space Apps 2026: Análogos terrestres de bases en la Luna y Marte

Proyecto para el reto **Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars** del NASA Space Apps Challenge 2026.

## El reto

Elegir sitios de aterrizaje o de bases permanentes en la Luna y en Marte depende de la topografía, la geología, el ambiente y los recursos disponibles. En la Tierra hay lugares con características parecidas (el desierto de Atacama, el cráter Haughton, el Valle de la Muerte) donde se prueban equipos y métodos antes de volar. Aun así, muchos de esos **análogos terrestres** no están bien caracterizados.

**Objetivo:** usar datos abiertos de la Tierra, la Luna y Marte (de la NASA y de otras agencias espaciales) para **identificar y caracterizar análogos terrestres nuevos** de sitios candidatos para bases lunares o para aterrizar y explorar en Marte. Los resultados se presentan como un mapa, una visualización u otra herramienta.

### Qué se espera
- **No basta con que se parezca visualmente.** Hay que demostrar con datos *por qué* un lugar es un buen análogo.
- **Una analogía no tiene que ser total.** Hay que explicar en qué se parece, cuánto se parece y **dónde deja de valer**.
- **Buscar más allá de los análogos conocidos** (Antártida, Atacama, Islandia, Hawái) y descubrir lugares poco estudiados.
- **Pensar en procesos además de lugares:** sedimentación, tormentas de polvo, vulcanismo, erosión, dinámica del hielo.
- **Tener en cuenta la escala:** un cráter, un valle o un campo volcánico puede ser mejor análogo que un desierto entero.
- **Conectar con la exploración:** cómo el análogo ayuda a probar instrumentos, preparar operaciones, buscar recursos o reducir riesgos.
- **Reconocer los límites de la Tierra:** gravedad reducida, vacío lunar, atmósfera marciana tenue y radiación no se pueden reproducir.

### Dimensiones de análisis
| Dimensión | Ejemplos de variables |
|---|---|
| Geología y materiales | Mineralogía, tipo de roca, regolito |
| Terreno | Elevación, pendiente, rugosidad, cráteres |
| Ambiente extremo | Temperatura, iluminación, amplitud térmica |
| Agua y recursos | Hielo, permafrost, hidratación |
| Procesos atmosféricos | Polvo, viento, erosión eólica |
| Habitabilidad | Extremófilos, biofirmas |
| Subsuelo | Cuevas, tubos de lava |
| Operaciones | Aterrizaje, movilidad, navegación, construcción |

### Posibles enfoques
Reporte escrito, mapa interactivo, visualización, app, sistema de ranking por similitud, métricas de similitud, machine learning, SIG o cualquier enfoque innovador.

## Recursos

Las fuentes de datos (PDS, LRO/Diviner, Earthdata, Copernicus, RADARSAT, JAXA, etc.) están descritas en [RECURSOS.md](RECURSOS.md).

## Estructura del repositorio

```
├── data/
│   ├── raw/          # Datos descargados sin modificar (no se suben a git)
│   └── processed/    # Datos procesados (no se suben a git)
├── docs/             # Objetivo, arquitectura y bitácora del proyecto
├── notebooks/        # Jupyter notebooks de exploración y análisis
├── src/              # Descarga, procesamiento, comparador (compare.py) y exportación a la web (export_web.py)
├── tests/            # Tests de Python (pytest)
├── outputs/          # Mapas, figuras y resultados finales
├── web/              # Plataforma web (React + Vite + CesiumJS + NASA GIBS/Trek)
├── infra/            # Infraestructura en Azure con Terraform (solo planes Free)
├── .github/workflows # Despliegue automático a Azure Static Web Apps
├── RECURSOS.md       # Catálogo de fuentes de datos
└── CONTRIBUTING.md   # Flujo de trabajo con git flow
```

## Entorno de Python (análisis y comparador)

El comparador de similitud (`src/compare.py`) y los notebooks usan Python 3.12. Hay dos formas de instalar el entorno:

**Con conda** (`environment.yml`):
```bash
conda env create -f environment.yml
conda activate analogos
```

**Con uv o pip** (`requirements.txt`):
```bash
uv venv --python 3.12 && uv pip install -r requirements.txt
source .venv/bin/activate
```

Verificar:
```bash
pytest -q tests
python src/compare.py --earth data/sample_earth.csv --targets data/sample_targets.csv --top 5

# Regenerar los datos reales que muestra la app (~2 min)
python src/export_web.py
```

En VS Code: `Ctrl+Shift+P` → *Python: Select Interpreter* → `.venv` o `analogos`.

## Plataforma web

👉 **Ver la app:** https://icy-flower-03890400f.5.azurestaticapps.net (versión en inglés: agrega `?lang=en`)

**Cómo usarla:**
1. Elige una comparación arriba: **Tierra ↔ Luna**, **Tierra ↔ Marte** o **Luna ↔ Marte**.
2. Filtra por tipo de ambiente o por la dimensión en la que debe parecerse.
3. Haz clic en un sitio (lista o globo): los dos globos vuelan al lugar y debajo aparecen las imágenes de cerca.
4. Baja para ver la **comparación detallada** (puntaje, pesos ajustables, valores reales y límites).
5. O pulsa **▶ Recorrido guiado** para una demo automática.

Comparación lado a lado en **globos 3D de la Tierra, la Luna y Marte** (modos Tierra ↔ Luna, Tierra ↔ Marte y Luna ↔ Marte), con filtros por tipo de ambiente y dimensión de similitud. Al elegir un sitio, ambos globos vuelan al lugar y debajo aparecen sus imágenes de detalle: Landsat de la Tierra y los mosaicos de NASA Moon Trek y Mars Trek. Todo con datos abiertos de la NASA, sin API keys. Disponible en **español e inglés** (`?lang=es` / `?lang=en`). Incluye un **recorrido guiado** y una **comparación detallada** con puntajes, pesos ajustables y límites de la analogía. Cada sitio se puede abrir en Google Earth.

```bash
cd web
npm install
npm run dev                  # http://localhost:5173
```

El despliegue en Azure se explica en [infra/README.md](infra/README.md).

## Documentación

- [docs/OBJETIVO.md](docs/OBJETIVO.md): objetivo detallado de la plataforma y criterios del reto
- [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md): componentes, CI/CD, seguridad y costos
- [docs/BITACORA.md](docs/BITACORA.md): registro de decisiones y avances
- [docs/GOOGLE_MAPS_API_KEY.md](docs/GOOGLE_MAPS_API_KEY.md): guía para crear y probar una API key de Google Maps
- [docs/VISUALIZACION_COMPARACION.md](docs/VISUALIZACION_COMPARACION.md): plan de la vista de comparación detallada, contrato de datos y mejoras para el jurado
- [docs/PIPELINE_COMPARADOR.md](docs/PIPELINE_COMPARADOR.md): cómo funciona el comparador (`compare.py`), fuentes de datos de la Tierra, la Luna y Marte, y cómo correrlo (Marco)
- [docs/CONTEXTO_TECNICO_SANTIAGO.md](docs/CONTEXTO_TECNICO_SANTIAGO.md): caracterización de los sitios de Colombia, índice topográfico PAI, Sentinel-2, EMIT y plan científico (Santiago)
- [docs/DATOS_WEB.md](docs/DATOS_WEB.md): cómo llegan los datos a la app, reglas aplicadas y cómo regenerarlos

## Cómo colaborar

Usamos **git flow**. Lee [CONTRIBUTING.md](CONTRIBUTING.md) antes de empezar a trabajar.
