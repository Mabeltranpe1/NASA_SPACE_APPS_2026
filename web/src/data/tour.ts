import type { Lang } from '../i18n/strings'

export type TourMode = 'tierra-luna' | 'tierra-marte' | 'luna-marte'

export interface TourStep {
  mode: TourMode
  /** Site to select; null shows the whole globes. */
  siteId: string | null
  title: Record<Lang, string>
  text: Record<Lang, string>
  /** Scroll down to the detailed comparison at this step. */
  showComparison?: boolean
}

export const TOUR_STEPS: TourStep[] = [
  {
    mode: 'tierra-luna',
    siteId: null,
    title: {
      es: 'Ensayar en la Tierra antes de volar',
      en: 'Rehearse on Earth before flying',
    },
    text: {
      es: 'Antes de construir una base en la Luna o aterrizar en Marte, los equipos prueban equipos y procedimientos en lugares de la Tierra con condiciones parecidas. Aquí los comparamos lado a lado con datos abiertos de la NASA.',
      en: 'Before building a base on the Moon or landing on Mars, teams test equipment and procedures in places on Earth with similar conditions. Here we compare them side by side using open NASA data.',
    },
  },
  {
    mode: 'tierra-luna',
    siteId: 'haughton-crater',
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
    mode: 'tierra-marte',
    siteId: 'atacama-yungay',
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
    mode: 'tierra-marte',
    siteId: 'tatacoa',
    title: {
      es: 'Un candidato poco estudiado: la Tatacoa',
      en: 'A lesser-studied candidate: Tatacoa',
    },
    text: {
      es: 'El reto pide mirar más allá de los análogos conocidos. Las cárcavas de sedimentos rojizos de la Tatacoa, en Colombia, recuerdan terrenos marcianos tallados por agua y viento. La analogía falla en el clima: aquí hay vegetación y lluvia.',
      en: 'The challenge asks us to look beyond well-known analogs. The reddish sediment gullies of Tatacoa, in Colombia, resemble Martian terrains carved by water and wind. The analogy breaks down in the climate: there is vegetation and rain.',
    },
  },
  {
    mode: 'luna-marte',
    siteId: 'lava-beds',
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
    mode: 'tierra-luna',
    siteId: 'haughton-crater',
    title: {
      es: 'Medir cuánto se parecen',
      en: 'Measuring how similar they are',
    },
    text: {
      es: 'Cada par tiene un puntaje calculado con datos reales: pendiente, rugosidad, temperatura, albedo, lluvia y vegetación, frente a unas 164 000 celdas de la Tierra. La vista muestra en qué se parecen, dónde se rompe la analogía y qué no puede reproducir la Tierra: la gravedad, el vacío y la radiación.',
      en: 'Each pair gets a score computed from real data: slope, roughness, temperature, albedo, rain and vegetation, against about 164,000 Earth cells. The view shows what is similar, where the analogy breaks down, and what Earth cannot reproduce: gravity, vacuum and radiation.',
    },
    showComparison: true,
  },
]
