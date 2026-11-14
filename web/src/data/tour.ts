export type TourMode = 'tierra-luna' | 'tierra-marte' | 'luna-marte'

export interface TourStep {
  mode: TourMode
  /** Site to select; null shows the whole globes. */
  siteId: string | null
  title: string
  text: string
  /** Scroll down to the detailed comparison at this step. */
  showComparison?: boolean
}

export const TOUR_STEPS: TourStep[] = [
  {
    mode: 'tierra-luna',
    siteId: null,
    title: 'Ensayar en la Tierra antes de volar',
    text: 'Antes de construir una base en la Luna o aterrizar en Marte, los equipos prueban equipos y procedimientos en lugares de la Tierra con condiciones parecidas. Aquí los comparamos lado a lado con datos abiertos de la NASA.',
  },
  {
    mode: 'tierra-luna',
    siteId: 'haughton-crater',
    title: 'Un cráter polar para practicar Artemis',
    text: 'El cráter Haughton, en el Ártico canadiense, es un cráter de impacto en un desierto polar. Su homólogo es el cráter Shackleton, en el polo sur lunar, una de las zonas candidatas para una base permanente.',
  },
  {
    mode: 'tierra-marte',
    siteId: 'atacama-yungay',
    title: 'El suelo más seco de la Tierra',
    text: 'Atacama tiene suelos oxidantes con percloratos y casi sin vida microbiana, como los que encontró la misión Phoenix en las llanuras del norte de Marte. Sirve para probar perforadoras y la búsqueda de biofirmas.',
  },
  {
    mode: 'tierra-marte',
    siteId: 'tatacoa',
    title: 'Un candidato poco estudiado: la Tatacoa',
    text: 'El reto pide mirar más allá de los análogos conocidos. Las cárcavas de sedimentos rojizos de la Tatacoa, en Colombia, recuerdan terrenos marcianos tallados por agua y viento. La analogía falla en el clima: aquí hay vegetación y lluvia.',
  },
  {
    mode: 'luna-marte',
    siteId: 'lava-beds',
    title: 'Refugios bajo tierra',
    text: 'Los tubos de lava podrían proteger a los astronautas de la radiación. En la Luna se ven tragaluces como el de Marius Hills, y en Marte, en los flancos de Arsia Mons. En la Tierra se ensaya en campos de lava como Lava Beds.',
  },
  {
    mode: 'tierra-luna',
    siteId: 'haughton-crater',
    title: 'Medir cuánto se parecen',
    text: 'Cada par tiene un puntaje calculado con elevación, pendiente, rugosidad, temperatura y albedo. La vista muestra en qué se parecen, dónde se rompe la analogía y qué no puede reproducir la Tierra: la gravedad, el vacío y la radiación.',
    showComparison: true,
  },
]
