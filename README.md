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
├── src/              # Código reutilizable (descarga, procesamiento, métricas)
├── outputs/          # Mapas, figuras y resultados finales
├── web/              # Plataforma web (React + Vite + Google Maps)
├── infra/            # Infraestructura en Azure con Terraform (solo planes Free)
├── .github/workflows # Despliegue automático a Azure Static Web Apps
├── RECURSOS.md       # Catálogo de fuentes de datos
└── CONTRIBUTING.md   # Flujo de trabajo con git flow
```

## Plataforma web

Mapa interactivo para filtrar análogos terrestres por objetivo (Luna o Marte), tipo de ambiente (desértico, polar, volcánico, cráter, cuevas, salar) y dimensión de similitud. Cada sitio se puede ver en Google Earth.

```bash
cd web
cp .env.example .env.local   # pon tu VITE_GOOGLE_MAPS_API_KEY
npm install
npm run dev                  # http://localhost:5173
```

El despliegue en Azure se explica en [infra/README.md](infra/README.md).

## Documentación

- [docs/OBJETIVO.md](docs/OBJETIVO.md): objetivo detallado de la plataforma y criterios del reto
- [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md): componentes, CI/CD, seguridad y costos
- [docs/BITACORA.md](docs/BITACORA.md): registro de decisiones y avances

## Cómo colaborar

Usamos **git flow**. Lee [CONTRIBUTING.md](CONTRIBUTING.md) antes de empezar a trabajar.
