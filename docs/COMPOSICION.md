# Composición de la roca en la Luna y Marte (`em_contrast`)

## Qué se hizo

En la Tierra, `em_contrast` sale de ASTER GED:

    em_contrast = emisividad media bandas 13-14 (10.6-11.3 µm) − emisividad media bandas 10-12 (8.3-9.1 µm)

Roca rica en sílice (arena de cuarzo, granito) da un valor grande; el basalto da ~0.
En la Luna y Marte no hay ASTER, así que la columna estaba vacía y la composición no influía en el score.
Ahora cada sitio lunar y marciano tiene un valor **equivalente**, calibrado en la misma escala que la Tierra.

Código: `src/composition.py` (`python src/composition.py` muestra la calibración, `--write` escribe los targets).
Tabla con la justificación de cada sitio: `data/composition_targets.csv`.

## Método: el puente es el Christiansen feature (CF)

El CF es un máximo de emisividad justo antes de las bandas de silicatos. Se mueve a longitudes de onda
más cortas cuando la roca tiene más sílice, y a más largas con más olivino o piroxeno. Es justo lo que mide
Diviner en la Luna (canales 7.8 / 8.25 / 8.55 µm) y se puede deducir de los tipos de superficie de TES en Marte.
La misma tendencia de sílice mueve las bandas de ASTER, por eso las dos medidas se pueden relacionar.

Valores típicos de laboratorio (Salisbury & Walter 1989; Cooper et al. 2002; Greenhagen et al. 2010):
cuarzo ~7.3-7.4 µm, granito ~7.8-7.9, andesita ~8.0-8.1, anortosita ~7.9-8.1, basalto ~8.2-8.3, olivino ~8.6+.

1. **Tierra (medido, con nuestra propia base de datos ASTER).** Recta `em_contrast = a + b·CF` con dos anclas:
   - basalto: mediana de `iceland_highlands` = −0.0017 (CF 8.25 µm, n = 1200)
   - arena de cuarzo: mediana de `rub_al_khali` = +0.2083 (CF 7.45 µm, n = 2400)
   - resultado: `em_contrast = 2.1639 − 0.2625·CF` (−0.026 por cada 0.1 µm de CF)
   - **comprobación independiente**: la Puna (volcánicas andesítico-dacíticas, CF ~8.05) predice +0.051 y ASTER mide +0.047.
2. **Luna (Diviner).** Los sitios polares están fuera de los mapas globales de CF de Diviner (el CF necesita superficies
   calientes de día), así que se usa el valor regional de las tierras altas feldespáticas, CF ≈ 8.15 µm (8.18 en Haworth
   y Faustini, más cerca de los eyectos noríticos de la cuenca SPA).
3. **Marte (TES + rovers).** Tipo de superficie TES (Bandfield et al. 2000: Tipo 1 basalto, Tipo 2 andesita o basalto
   alterado; zonas con polvo) más la composición vista por los rovers → litología → CF.

| Sitio | Litología | CF (µm) | em_contrast | ± |
|---|---|---|---|---|
| Shackleton / de Gerlache / Mons Mouton | tierras altas feldespáticas | 8.15 | +0.025 | 0.026 |
| Haworth / Faustini | feldespática + algo de norita SPA | 8.18 | +0.017 | 0.026 |
| Shackleton floor (sombra) | igual que el borde, sin CF medible | 8.15 | +0.025 | 0.039 |
| Jezero | basalto rico en olivino + carbonatos | 8.40 | −0.041 | 0.026 |
| Gale | basalto con olivino | 8.30 | −0.015 | 0.026 |
| Gusev | basalto olivínico (Adirondack) | 8.35 | −0.028 | 0.032 |
| Meridiani | arena basáltica + hematita | 8.25 | −0.002 | 0.026 |
| Elysium / Chryse | basalto bajo polvo | 8.25 | −0.002 | 0.039 |
| Utopia / Vastitas Borealis | TES Tipo 2 | 8.10 | +0.038 | 0.032 |
| Arcadia | Tipo 2 con algo de polvo | 8.15 | +0.025 | 0.039 |

## Límites (hay que decirlos ante los jueces)

- **Es un indicador aproximado de tipo de roca, no una medida de ASTER.** Es el valor que tendría en ASTER una roca
  terrestre de la misma composición.
- **El CF de cada sitio viene de la literatura, no de extraer píxeles.** Los archivos PDS de Diviner y TES no se pueden
  descargar desde este entorno, y en los polos lunares no existe un CF de Diviner. Los valores son regionales.
- **La incertidumbre (±0.026-0.039) es del mismo tamaño que la tolerancia del comparador (0.03).** El término separa bien
  "cuarzo" de "basalto/anortosita", pero no distingue finamente entre sitios del mismo cuerpo.
- **Polvo y regolito fino** (Luna en vacío, polvo marciano) tienen bandas mucho más débiles que la roca de la Tierra.
- **Meteorización espacial y el entorno térmico lunar** desplazan el CF unos 0.1 µm en direcciones opuestas; aquí se supone
  que se compensan.
- **La recta solo tiene 2 anclas.** Los valores menores que el basalto (Jezero, Gusev, Gale) son una extrapolación.
- **En la Tierra, carbonatos, evaporitas y arcillas también dan em_contrast bajo** sin ser basalto. Ejemplo: la nueva mejor
  celda de Egipto para Marte (25.43 N, 30.07 E, em_contrast 0.007) puede ser caliza o lutita, no basalto. Antes de presentarla
  como análogo de roca, hay que mirar el mapa geológico.
- El hielo de la Antártida tiene en ASTER GED un valor fijo (−0.0007), así que allí `em_contrast` no informa de la roca.

## Cómo cambian los rankings (celdas poco conocidas, elevación con peso 0, igual que `make_results.py`)

Archivos en `outputs/composition/` (antes = sin composición, después = con composición, `w05` = peso 0.5 para em_contrast).

**Luna:** cambia poco. En los top 20 de cada sitio se mantienen 16-19 de las 20 celdas. Ellesmere norte y el norte de Groenlandia
siguen arriba (su em_contrast 0.01-0.016 es parecido al de las tierras altas lunares). Por regiones, Kamchatka cae del 1.º al
5.º puesto, Victoria Island sube del 15.º al 7.º y las dunas de cuarzo (Taklamakan, Badain Jaran) quedan penalizadas
(sim_em ≈ 0.05).

**Marte:** cambia bastante. Las arenas de cuarzo del Sahara (Fezzan, Tanezrouft), Kumtag y Taklamakan bajan 4 puestos cada una
(sim_em 0.06-0.2). Suben los terrenos volcánicos o pobres en cuarzo: la Puna pasa del 13.º al 3.º, el norte de Groenlandia del
16.º al 2.º y Tibesti del 10.º al 5.º. El desierto occidental de Egipto sigue siendo el 1.º, pero su mejor celda cambia a una
zona de em_contrast bajo. En 5 de los 9 sitios marcianos (Elysium, Meridiani, Chryse, Vastitas y Arcadia), ninguna de las 20 mejores celdas de antes sigue en el top 20.

Con peso 0.5 los cambios van en la misma dirección, pero son más suaves (por ejemplo, la Puna queda 4.ª).

## Recomendación

Usar `em_contrast` con **peso 0.5** (`WEIGHTS = {"elev_m": 0, "em_contrast": 0.5}` en `make_results.py`), porque su incertidumbre
es de ~1 tolerancia, y presentarlo como "indicador de tipo de roca calibrado". Si se consiguen los mapas de tipos de superficie
TES o un CF de Diviner con menor incertidumbre, basta con cambiar `SITES` en `src/composition.py` y ejecutar `--write`.
