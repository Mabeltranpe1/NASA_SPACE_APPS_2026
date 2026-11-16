import type { MissionId } from '../comparator/missions'
import type { Lang } from './strings'

/** Names and short explanations of the mission types (src/comparator/missions.ts). */
export interface MissionText {
  /** Full name (filter chips). */
  name: string
  /** Short name (badges). */
  short: string
  /** What the mission puts first, in one sentence. */
  why: string
  /** What the app does NOT measure for this mission (optional). */
  note?: string
}

export const MISSION_TEXT: Record<Lang, Record<MissionId, MissionText>> = {
  es: {
    rover: {
      name: 'Movilidad de rovers', short: 'Rovers',
      why: 'Pendiente y rugosidad parecidas para probar ruedas, suspensión y navegación; el tipo de roca acerca el suelo.',
    },
    isru: {
      name: 'Minería e ISRU', short: 'Minería / ISRU',
      why: 'El tipo de roca y el albedo pesan más, para ensayar la extracción y el uso de recursos del lugar.',
      note: 'El tipo de roca (contraste de emisividad) es solo un indicador aproximado de la composición.',
    },
    habitat: {
      name: 'Hábitats análogos', short: 'Hábitats',
      why: 'Frío, amplitud térmica, sequedad y nada de vegetación, para estancias de tripulaciones aisladas.',
    },
    thermal: {
      name: 'Pruebas térmicas de equipos', short: 'Pruebas térmicas',
      why: 'Temperatura media, amplitud térmica y albedo, para probar equipos con ciclos de calor y frío parecidos.',
    },
    science: {
      name: 'Ciencia y astrobiología', short: 'Astrobiología',
      why: 'Sequedad extrema, sin vegetación y el mismo tipo de roca, para estudiar la vida al límite y probar instrumentos.',
    },
    drone: {
      name: 'Drones y vuelo', short: 'Drones',
      why: 'Brillo y relieve parecidos para la navegación visual; la temperatura cuenta por las baterías.',
      note: 'No medimos la densidad del aire: en Marte la atmósfera es unas 100 veces más delgada y en la Luna no hay.',
    },
    landing: {
      name: 'Aterrizaje y lanzamiento de cohetes y cápsulas', short: 'Aterrizaje y lanzamiento',
      why: 'Terreno plano y liso por encima de todo, para plataformas de aterrizaje y despegue.',
      note: 'Las pruebas reales también necesitan espacio aéreo restringido y distancia de zonas pobladas, y eso no lo medimos.',
    },
  },
  en: {
    rover: {
      name: 'Rover mobility', short: 'Rovers',
      why: 'Similar slope and roughness to test wheels, suspension and navigation; rock type brings the ground closer.',
    },
    isru: {
      name: 'Mining and ISRU', short: 'Mining / ISRU',
      why: 'Rock type and albedo weigh more, to rehearse extracting and using local resources.',
      note: 'Rock type (emissivity contrast) is only a rough proxy for composition.',
    },
    habitat: {
      name: 'Analog habitats', short: 'Habitats',
      why: 'Cold, large temperature swings, dryness and no vegetation, for isolated crew stays.',
    },
    thermal: {
      name: 'Thermal equipment tests', short: 'Thermal tests',
      why: 'Mean temperature, temperature range and albedo, to test equipment under similar hot/cold cycles.',
    },
    science: {
      name: 'Science and astrobiology', short: 'Astrobiology',
      why: 'Extreme dryness, no vegetation and the same rock type, to study life at the limit and test instruments.',
    },
    drone: {
      name: 'Drones and flight', short: 'Drones',
      why: 'Similar brightness and relief for visual navigation; temperature matters for batteries.',
      note: 'We do not measure air density: the Martian atmosphere is about 100 times thinner and the Moon has none.',
    },
    landing: {
      name: 'Landing and launch of rockets and capsules', short: 'Landing & launch',
      why: 'Flat, smooth ground above everything else, for landing and launch pads.',
      note: 'Real tests also need restricted airspace and distance from populated areas, which we do not measure.',
    },
  },
}

export const MISSION_UI = {
  es: {
    title: 'Tipo de misión',
    all: 'Todas (pesos del modelo)',
    hint: 'Cada misión solo cambia los pesos de las mismas variables: no agrega datos. No hay capas de polvo, hielo, cuevas ni iluminación.',
    priorities: 'Pesa más: {list}',
    moonTemp: 'En la Luna la temperatura no cuenta: ningún lugar de la Tierra llega a esos valores.',
    suitable: 'Apto para',
    fitTip: '{mission}: {score}/100 con los pesos de esta misión · {rel} % de lo mejor de la Tierra para esta misión. Clic para filtrar.',
    custom: 'Pesos propios',
    panelTitle: 'Misiones que se pueden probar aquí',
    panelAll: 'Ver las 7 misiones',
    panelFewer: 'Ver menos',
    panelHint: '100 = el mejor lugar de la Tierra para esa misión, con el mismo puntaje de la app y los pesos de cada misión. Solo cambian los pesos: no hay datos de polvo, hielo, cuevas ni iluminación.',
  },
  en: {
    title: 'Mission type',
    all: 'All (model weights)',
    hint: 'Each mission only changes the weights of the same variables: it adds no data. There are no layers for dust, ice, caves or lighting.',
    priorities: 'Weighs more: {list}',
    moonTemp: 'On the Moon temperature does not count: no place on Earth reaches those values.',
    suitable: 'Suitable for',
    fitTip: '{mission}: {score}/100 with this mission\'s weights · {rel}% of the best on Earth for this mission. Click to filter.',
    custom: 'Custom weights',
    panelTitle: 'Missions that could be tested here',
    panelAll: 'Show all 7 missions',
    panelFewer: 'Show fewer',
    panelHint: '100 = the best place on Earth for that mission, with the app\'s same score and each mission\'s weights. Only the weights change: there is no data on dust, ice, caves or lighting.',
  },
} as const
