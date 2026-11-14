# Objetivo de la plataforma web de análogos terrestres

Este documento describe **qué busca la plataforma web**, cómo responde al reto de NASA Space Apps 2026 y qué falta para considerarla terminada.

## 1. El reto en una frase

> Usar datos abiertos de la Tierra, la Luna y Marte para **identificar y caracterizar lugares de la Tierra** que sirvan como análogos de futuras bases lunares o sitios de exploración en Marte, y presentar los hallazgos en un mapa, visualización o herramienta.

Reto oficial: *Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars*.

## 2. Qué problema resuelve la plataforma

Hoy los análogos terrestres (Atacama, Haughton, Valle de la Muerte, etc.) están **dispersos en artículos científicos** y casi nunca se comparan entre sí con criterios cuantitativos. Un equipo de misión o un estudiante no tiene una forma sencilla de responder preguntas como:

- *"¿Qué lugares de la Tierra se parecen al polo sur lunar en temperatura **y** en topografía?"*
- *"¿Qué análogos de Marte hay con tubos de lava?"*
- *"¿Dónde deja de valer la analogía de este sitio?"*

La plataforma reúne los sitios en un **mapa interactivo filtrable** y muestra **por qué** cada lugar es (o no es) un buen análogo.

## 3. Qué debe hacer

### 3.1 Funcionalidades actuales (versión 0.1)

| Funcionalidad | Descripción |
|---|---|
| Filtro por objetivo | Luna, Marte o ambos |
| Filtro por tipo de ambiente | Desértico, polar/ártico, volcánico, cráter de impacto, cuevas/tubos de lava, salar |
| Filtro por dimensión | Muestra solo los sitios con similitud **alta o media** en todas las dimensiones elegidas (geología, terreno, temperatura, agua/hielo, polvo/viento, habitabilidad, subsuelo, operaciones) |
| Solo poco estudiados | Oculta los análogos ya muy conocidos, como pide el reto |
| Mapa satelital | Google Maps con marcadores por color: gris = Luna, naranja = Marte, morado = ambos |
| Ficha del sitio | Similitud por dimensión, en qué se parece, **dónde deja de valer la analogía** y para qué sirve en una misión |
| Ver en Google Earth | Enlace directo a la vista 3D del sitio |

### 3.2 Funcionalidades previstas

| Prioridad | Funcionalidad | Por qué |
|---|---|---|
| Alta | **Puntaje de similitud (0–100) calculado con datos reales** | El reto pide demostrar con datos *por qué* un sitio es análogo, no solo que se parezca |
| Alta | Selección del **sitio objetivo concreto** (por ejemplo, cráter Shackleton o cráter Jezero) | La similitud depende de con qué lugar se compara |
| Alta | **Búsqueda sistemática** de análogos nuevos (cuadrícula global, no solo una lista curada) | El reto premia descubrir lugares poco estudiados |
| Media | Comparación lado a lado: sitio terrestre frente a sitio lunar o marciano | Comunicación visual de la analogía |
| Media | Capas de datos sobre el mapa (temperatura, pendiente, radar) | Explorar más allá de los puntos |
| Baja | Versión en inglés | Público internacional del hackathon |

## 4. Criterios del reto y cómo los cubrimos

| Lo que pide el reto | Cómo lo cubre la plataforma |
|---|---|
| "Think beyond visual similarity" | Similitud por **8 dimensiones** con datos, no por apariencia |
| "An analog does not have to match everything" | Cada sitio muestra niveles distintos por dimensión y una sección **"Dónde deja de valer la analogía"** |
| "Look beyond well-known analog sites" | Filtro *Solo poco estudiados* y, más adelante, búsqueda sistemática global |
| "Consider scale" | Los sitios son lugares concretos (un cráter, un valle, un salar), no continentes |
| "Connect your analog to exploration" | Sección **"Para qué sirve en una misión"** en cada ficha |
| "Remember Earth's limits" | Las limitaciones (gravedad, atmósfera, radiación) se documentan por sitio |
| "Use multiple datasets" | Pipeline previsto con Diviner, LOLA, Mini-RF, LEND (Luna); THEMIS, MOLA (Marte); MODIS, SRTM, Sentinel-1, RADARSAT (Tierra) |

## 5. Métrica de similitud (propuesta)

Para cada dimensión *d* se comparan variables medibles del sitio terrestre *T* y del sitio objetivo *P*:

| Dimensión | Variable Luna/Marte | Variable Tierra |
|---|---|---|
| Temperatura | Amplitud y mínimos térmicos (Diviner / THEMIS) | Temperatura superficial (MODIS LST) |
| Terreno | Pendiente y rugosidad (LOLA / MOLA) | DEM (SRTM / Copernicus DEM) |
| Radar / superficie | Retrodispersión (Mini-RF) | Retrodispersión (Sentinel-1 / RADARSAT) |
| Agua / hielo | Hidrógeno (LEND) | Permafrost, nieve y hielo (productos de Earthdata) |

1. Se normaliza cada variable a una escala común (0–1).
2. Se calcula la similitud por dimensión: `s_d = 1 − |T_d − P_d|`.
3. El puntaje total es un promedio ponderado: `S = Σ w_d · s_d`, con pesos elegidos por el usuario en la plataforma.

Las diferencias físicas que la Tierra **no puede reproducir** (gravedad, vacío, radiación) no entran en el puntaje: se muestran siempre como limitaciones explícitas.

## 6. Alcance y fuera de alcance

**Dentro del alcance:**
- Mapa web público, gratuito y sin inicio de sesión.
- Catálogo de sitios con datos trazables a su fuente.
- Puntajes reproducibles con los scripts y notebooks del repositorio.

**Fuera del alcance (por ahora):**
- Cuentas de usuario o edición colaborativa en la web.
- Procesamiento de datos en el servidor en tiempo real (los datos se preprocesan y se publican como archivos estáticos).
- Cualquier servicio de pago (ver [ARQUITECTURA.md](ARQUITECTURA.md#costos)).

## 7. Criterios de "terminado" para el hackathon

- [ ] Los puntajes de al menos 3 dimensiones se calculan con datos reales.
- [ ] Al menos 2 sitios objetivo (uno lunar y uno marciano).
- [ ] Al menos 3 análogos **poco estudiados** propuestos con justificación basada en datos.
- [ ] Cada sitio tiene fuentes citadas.
- [ ] La plataforma está desplegada en producción (rama `main`).
- [ ] Hay un video o presentación de demostración.
