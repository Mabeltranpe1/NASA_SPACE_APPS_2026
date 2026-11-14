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
