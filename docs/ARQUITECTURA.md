# Arquitectura

## Vista general

```mermaid
flowchart LR
    subgraph Fuentes["Fuentes de datos abiertas"]
        PDS["NASA PDS<br/>LRO: Diviner, LOLA,<br/>Mini-RF, LEND"]
        EARTH["NASA Earthdata<br/>MODIS, SRTM"]
        COP["Copernicus<br/>Sentinel-1/2/3"]
        OTROS["CSA RADARSAT<br/>JAXA G-Portal<br/>ESA"]
    end

    subgraph Pipeline["Pipeline de datos (Python)"]
        DL["src/ — descarga"]
        PROC["notebooks/ — procesamiento<br/>y métricas de similitud"]
        OUT["sites.json / GeoJSON"]
    end

    subgraph Web["Plataforma web (React)"]
        APP["web/ — React + Vite + TS"]
        MAPS["Google Maps<br/>JavaScript API"]
        GE["Google Earth<br/>(enlace)"]
    end

    subgraph Azure["Azure (plan Free)"]
        SWA["Static Web App<br/>swa-nasa-analogs"]
    end

    GH["GitHub<br/>git flow + Actions"]

    PDS --> DL
    EARTH --> DL
    COP --> DL
    OTROS --> DL
    DL --> PROC --> OUT --> APP
    APP --> MAPS
    APP --> GE
    APP --> GH -->|deploy| SWA
```

## Componentes

### 1. Pipeline de datos (`src/`, `notebooks/`) · *en construcción*
- **Lenguaje:** Python (GDAL/rasterio, numpy, pandas, geopandas).
- **Entrada:** datos planetarios (PDS) y terrestres (Earthdata, Copernicus, CSA, JAXA).
- **Salida:** un archivo de sitios con sus puntajes por dimensión, que la web consume como dato estático.
- **Reglas:**
  - Los datos crudos van en `data/raw/` y los procesados en `data/processed/`. **No se suben a git.**
  - Cada dataset debe tener un script de descarga reproducible.
  - Cada fuente nueva se registra en [RECURSOS.md](../RECURSOS.md).

### 2. Plataforma web (`web/`)

| Aspecto | Elección |
|---|---|
| Framework | React 19 + TypeScript |
| Build | Vite |
| Mapa | `@vis.gl/react-google-maps` (Google Maps JavaScript API, vista `hybrid`, `AdvancedMarker`) |
| Lint | oxlint |
| Estado | `useState` y `useMemo` locales (sin librería de estado global) |
| Datos | Por ahora en `web/src/data/sites.ts`; se reemplazará por el archivo generado por el pipeline |

Estructura:
```
web/src/
├── App.tsx          # Layout, filtros, mapa y ficha del sitio
├── App.css          # Estilos de la app
├── index.css        # Variables de color (modo claro/oscuro)
└── data/
    ├── types.ts     # Tipos: AnalogSite, Target, Environment, Dimension
    └── sites.ts     # Catálogo de sitios (preliminar)
```

**Modelo de datos (`AnalogSite`):**

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Identificador único |
| `name`, `country` | string | Nombre y país |
| `lat`, `lng` | number | Coordenadas WGS84 |
| `environments` | Environment[] | Tipos de ambiente |
| `targets` | Target[] | `luna` y/o `marte` |
| `analogOf` | string | Lugar o ambiente planetario del que es análogo |
| `dimensions` | Record<Dimension, Level> | Similitud por dimensión (`alta`, `media`, `baja`); pasará a puntaje 0–100 |
| `similarities` | string | En qué se parece |
| `limitations` | string | Dónde deja de valer la analogía |
| `missionUse` | string | Para qué sirve en una misión |
| `wellKnown` | boolean | Si ya es un análogo muy estudiado |

**Variables de entorno** (se inyectan al compilar, *build time*):

| Variable | Uso |
|---|---|
| `VITE_GOOGLE_MAPS_API_KEY` | API key de Google Maps |
| `VITE_GOOGLE_MAPS_MAP_ID` | (Opcional) Map ID; si no se define se usa `DEMO_MAP_ID` |

En local van en `web/.env.local` (ignorado por git). En CI se toman de los secrets de GitHub.

### 3. Infraestructura (`infra/`)

Gestionada **100 % con Terraform**. Ver [infra/README.md](../infra/README.md).

| Recurso | Nombre | Plan |
|---|---|---|
| Resource Group | `rg-nasa-analogs` (eastus2) | — |
| Static Web App | `swa-nasa-analogs` | **Free** |

- **Proveedor:** `hashicorp/azurerm` ~> 5.14.
- **Estado:** local (`infra/terraform.tfstate`, fuera de git). Solo una persona aplica cambios de infraestructura.

### 4. CI/CD (`.github/workflows/deploy-web.yml`)

```mermaid
flowchart LR
    F["feature/*"] -->|Pull Request| D["develop"]
    D -->|release| M["main"]
    F -. "PR abierto" .-> PREV["Entorno de vista previa<br/>icy-flower-...-N.eastus2..."]
    M -. "push" .-> PROD["Producción<br/>icy-flower-03890400f.5..."]
```

| Evento | Acción |
|---|---|
| Push a `main` (cambios en `web/`) | Build + despliegue a **producción** |
| PR abierto o actualizado hacia `develop` o `main` | Build + despliegue a un **entorno de vista previa** |
| PR cerrado | Se elimina el entorno de vista previa |

Pasos del job: `npm ci` → `npm run lint` → `npm run build` → `Azure/static-web-apps-deploy@v1` (subida de `web/dist`).

**Secrets de GitHub:**

| Secret | Origen |
|---|---|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | `terraform output -raw static_web_app_deployment_token` |
| `VITE_GOOGLE_MAPS_API_KEY` | Google Cloud Console |

### 5. Flujo de trabajo (git flow)

Ver [CONTRIBUTING.md](../CONTRIBUTING.md). Resumen: `feature/*` → PR → `develop` → `release/*` → `main`.

## URLs

| Entorno | URL |
|---|---|
| Producción | https://icy-flower-03890400f.5.azurestaticapps.net |
| Vista previa del PR *N* | `https://icy-flower-03890400f-N.eastus2.5.azurestaticapps.net` |
| Local | http://localhost:5173 |

## Seguridad

- **La API key de Google Maps queda visible en el navegador** (es inevitable en una app web). Está protegida por:
  - restricción por referrer: `localhost:5173`, el dominio de producción y `*.eastus2.5.azurestaticapps.net`;
  - restricción de API: solo *Maps JavaScript API*;
  - límite diario de cuota.
- El token de despliegue de Azure solo existe en el estado de Terraform y en el secret de GitHub. Si se filtra, se regenera en el portal (*Administrar token de implementación → Restablecer*) y se actualiza el secret.
- `terraform.tfvars`, `*.tfstate` y `.env.local` están en `.gitignore`.

## Costos

**Regla del proyecto: solo planes gratuitos.** Cualquier servicio de pago se consulta antes de activarlo.

| Servicio | Plan | Límite gratuito | Protección |
|---|---|---|---|
| Azure Static Web Apps | Free | 100 GB/mes de ancho de banda, 3 vistas previas | — |
| Google Maps JavaScript API | Pago por uso con cuota gratuita | Cuota mensual gratuita de cargas de mapa | Límite diario de cuota + alerta de presupuesto |
| GitHub Actions | Repositorio público | Minutos ilimitados | — |
| Estado remoto de Terraform | *No usado* | — | Requeriría un Storage Account (costo mínimo) |
