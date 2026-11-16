import type { Lang } from '../i18n/strings'
import type { Body, Target } from './types'
import type { RankingId } from './comparisons'

export type TourView = 'discover' | 'sites' | 'analysis' | 'finder' | 'method'

export interface TourStep {
  view: TourView
  /** Catalog site to select; null shows the whole globe. */
  siteId: string | null
  /** Select the best discovery of the global search for this body. */
  discovery?: Target
  /** Body the globe switches to after a few seconds on Earth. */
  body: Body
  /** Delay before switching to `body` (ms, default 4500). */
  bodyDelay?: number
  /** Discover view: body and ranked list to show. */
  discoverBody?: Target
  list?: RankingId
  /** Open the photo gallery of the selected place. */
  gallery?: boolean
  /** "Find" view: Moon/Mars site searched on arrival, and the mission type to filter by. */
  finderSite?: string
  finderMission?: string
  /** Duration of the step in seconds (default 12). */
  seconds?: number
  title: Record<Lang, string>
  text: Record<Lang, string>
}

export const TOUR_STEPS: TourStep[] = [
  {
    view: 'discover',
    siteId: null,
    body: 'tierra',
    title: {
      es: 'Ensayar en la Tierra antes de volar',
      en: 'Rehearse on Earth before flying',
    },
    text: {
      es: 'Antes de construir una base en la Luna o aterrizar en Marte, los equipos prueban equipos y procedimientos en lugares de la Tierra con condiciones parecidas. Aquí los encontramos y los comparamos con datos abiertos de la NASA.',
      en: 'Before building a base on the Moon or landing on Mars, teams test equipment and procedures in places on Earth with similar conditions. Here we find and compare them using open NASA data.',
    },
  },
  {
    view: 'discover',
    siteId: null,
    discovery: 'marte',
    body: 'marte',
    title: {
      es: 'La búsqueda global encuentra lugares nuevos',
      en: 'The global search finds new places',
    },
    text: {
      es: 'Comparamos unas 690 000 celdas de las zonas áridas y frías del mundo con 31 sitios de la Luna y Marte (22 son las regiones candidatas de Artemis III). Listamos los 100 lugares poco estudiados más parecidos para cada cuerpo, separados al menos 300 km, y los mejores por relieve, temperatura, roca y aridez.',
      en: 'We compare about 690,000 cells of the world\'s dry and cold lands with 31 Moon and Mars sites (22 are the Artemis III candidate regions). We list the 100 most similar little-studied places for each body, at least 300 km apart, and the best ones by relief, temperature, rock and aridity.',
    },
  },
  {
    view: 'sites',
    siteId: 'haughton-crater',
    body: 'luna',
    title: {
      es: 'Un cráter polar para practicar Artemis',
      en: 'A polar crater to practice for Artemis',
    },
    text: {
      es: 'El cráter Haughton, en el Ártico canadiense, es un cráter de impacto en un desierto polar. Su homólogo es el cráter Shackleton, en el polo sur lunar, una de las zonas candidatas para una base permanente.',
      en: 'Haughton Crater, in the Canadian Arctic, is an impact crater in a polar desert. Its counterpart is Shackleton Crater at the lunar south pole, one of the candidate regions for a permanent base.',
    },
  },
  {
    view: 'sites',
    siteId: 'atacama-yungay',
    body: 'marte',
    title: {
      es: 'El suelo más seco de la Tierra',
      en: 'The driest soil on Earth',
    },
    text: {
      es: 'Atacama tiene suelos oxidantes con percloratos y casi sin vida microbiana, como los que encontró la misión Phoenix en las llanuras del norte de Marte. Sirve para probar perforadoras y la búsqueda de biofirmas.',
      en: 'Atacama has oxidizing soils with perchlorates and almost no microbial life, like those found by the Phoenix mission on the northern plains of Mars. It is used to test drills and the search for biosignatures.',
    },
  },
  {
    view: 'sites',
    siteId: 'tatacoa',
    body: 'marte',
    title: {
      es: 'Un candidato poco estudiado: la Tatacoa',
      en: 'A lesser-studied candidate: Tatacoa',
    },
    text: {
      es: 'El reto pide mirar más allá de los análogos conocidos. Las cárcavas de sedimentos rojizos de la Tatacoa, en Colombia, recuerdan terrenos marcianos tallados por agua y viento. Las dimensiones lo muestran: se parece en el relieve, pero falla en la aridez, porque aquí hay vegetación y lluvia.',
      en: 'The challenge asks us to look beyond well-known analogs. The reddish sediment gullies of Tatacoa, in Colombia, resemble Martian terrains carved by water and wind. The dimensions show it: it matches in relief but fails in aridity, because there is vegetation and rain.',
    },
  },
  {
    view: 'sites',
    siteId: 'lava-beds',
    body: 'luna',
    title: {
      es: 'Refugios bajo tierra',
      en: 'Shelters underground',
    },
    text: {
      es: 'Los tubos de lava podrían proteger a los astronautas de la radiación. En la Luna se ven tragaluces como el de Marius Hills, y en Marte, en los flancos de Arsia Mons. En la Tierra se ensaya en campos de lava como Lava Beds.',
      en: 'Lava tubes could shield astronauts from radiation. Skylights are seen on the Moon, like the Marius Hills pit, and on Mars, on the flanks of Arsia Mons. On Earth, teams practice in lava fields like Lava Beds.',
    },
  },
  {
    view: 'analysis',
    siteId: null,
    // The best place of the global search: the clearest example of a high, stable score.
    discovery: 'marte',
    body: 'tierra',
    title: {
      es: 'Medir cuánto se parecen',
      en: 'Measuring how similar they are',
    },
    text: {
      es: 'Cada par tiene un puntaje calculado con datos reales: pendiente, rugosidad, temperatura, albedo, tipo de roca, lluvia y vegetación, frente a unas 690 000 celdas de la Tierra, y un puntaje por dimensión. La vista muestra en qué se parecen, dónde se rompe la analogía y qué no puede reproducir la Tierra: la gravedad, el vacío y la radiación.',
      en: 'Each pair gets a score computed from real data: slope, roughness, temperature, albedo, rock type, rain and vegetation, against about 690,000 Earth cells, plus one score per dimension. The view shows what is similar, where the analogy breaks down, and what Earth cannot reproduce: gravity, vacuum and radiation.',
    },
  },
]

/**
 * Video mode (?demo=1): ~30 s that show as many features as possible, with short texts
 * meant to be read on screen. Recorded for the NASA Space Apps presentation.
 */
export const DEMO_STEPS: TourStep[] = [
  {
    view: 'discover',
    siteId: null,
    body: 'tierra',
    discoverBody: 'marte',
    list: 'general',
    seconds: 3.5,
    title: { es: 'GeoAnalog', en: 'GeoAnalog' },
    text: {
      es: '691 000 lugares de la Tierra comparados con 31 sitios de la Luna y Marte, con datos abiertos de la NASA.',
      en: '691,000 places on Earth compared with 31 Moon and Mars sites, using open NASA data.',
    },
  },
  {
    view: 'discover',
    siteId: null,
    body: 'tierra',
    discoverBody: 'luna',
    list: 'relieve',
    seconds: 3.5,
    title: { es: 'Los mejores análogos, por dimensión', en: 'The best analogs, by dimension' },
    text: {
      es: 'Relieve, temperatura, roca y aridez: 100 lugares poco estudiados por cuerpo.',
      en: 'Relief, temperature, rock and aridity: 100 little-studied places per body.',
    },
  },
  {
    view: 'discover',
    siteId: null,
    discovery: 'marte',
    body: 'marte',
    bodyDelay: 2600,
    seconds: 5,
    title: { es: 'Cada lugar, con su par en Marte', en: 'Every place, with its Mars counterpart' },
    text: {
      es: 'Puntaje, dimensiones y mapa de similitud; luego el globo vuela a Marte.',
      en: 'Score, dimensions and similarity map; then the globe flies to Mars.',
    },
  },
  {
    view: 'sites',
    siteId: 'haughton-crater',
    body: 'luna',
    bodyDelay: 1600,
    seconds: 4,
    title: { es: 'Análogos conocidos y la Luna', en: 'Known analogs and the Moon' },
    text: {
      es: 'Haughton ≈ Shackleton, en el polo sur lunar donde Artemis planea su base.',
      en: 'Haughton ≈ Shackleton, at the lunar south pole where Artemis plans its base.',
    },
  },
  {
    view: 'sites',
    siteId: 'haughton-crater',
    body: 'tierra',
    gallery: true,
    seconds: 4,
    title: { es: 'Fotos reales, lado a lado', en: 'Real photos, side by side' },
    text: {
      es: 'Imágenes de la NASA y Sentinel-2 de la Tierra junto a la Luna o Marte.',
      en: 'NASA and Sentinel-2 images of Earth next to the Moon or Mars.',
    },
  },
  {
    view: 'analysis',
    siteId: null,
    discovery: 'marte',
    body: 'tierra',
    seconds: 4,
    title: { es: 'Análisis honesto', en: 'An honest analysis' },
    text: {
      es: 'Valores reales, ranking mundial y dónde deja de valer la analogía.',
      en: 'Real values, world ranking and where the analogy breaks down.',
    },
  },
  {
    view: 'finder',
    siteId: null,
    body: 'tierra',
    finderSite: 'jezero',
    finderMission: 'rover',
    seconds: 4,
    title: { es: 'Análogos para cada misión', en: 'Analogs for each mission' },
    text: {
      es: 'Rovers, minería, hábitats, drones o aterrizaje: el buscador ordena por misión y descarga en GeoJSON o KML.',
      en: 'Rovers, mining, habitats, drones or landing: the finder ranks by mission and downloads GeoJSON or KML.',
    },
  },
  {
    view: 'method',
    siteId: null,
    body: 'tierra',
    seconds: 3,
    title: { es: 'GeoAnalog · método abierto', en: 'GeoAnalog · open method' },
    text: {
      es: 'Fórmula, fuentes y límites a la vista. NASA Space Apps 2026.',
      en: 'Formula, sources and limits in plain sight. NASA Space Apps 2026.',
    },
  },
]
