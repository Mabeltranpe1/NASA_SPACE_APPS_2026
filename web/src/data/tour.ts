import type { Lang } from '../i18n/strings'
import type { Body, Target } from './types'

export type TourView = 'discover' | 'sites' | 'analysis'

export interface TourStep {
  view: TourView
  /** Catalog site to select; null shows the whole globe. */
  siteId: string | null
  /** Select the best discovery of the global search for this body. */
  discovery?: Target
  /** Body the globe switches to after a few seconds on Earth. */
  body: Body
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
