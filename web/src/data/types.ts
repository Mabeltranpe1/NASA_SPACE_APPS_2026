export type Target = 'luna' | 'marte'

export type Environment =
  | 'desertico'
  | 'polar'
  | 'volcanico'
  | 'crater'
  | 'subsuelo'
  | 'salar'

export type Dimension =
  | 'geologia'
  | 'terreno'
  | 'temperatura'
  | 'agua_hielo'
  | 'polvo'
  | 'habitabilidad'
  | 'subsuelo'
  | 'operaciones'

export type Level = 'alta' | 'media' | 'baja'

export interface AnalogSite {
  id: string
  name: string
  country: string
  lat: number
  lng: number
  environments: Environment[]
  targets: Target[]
  /** Planetary location or environment this site is an analog of. */
  analogOf: string
  /** Similarity per dimension. Preliminary qualitative values until the data pipeline computes scores. */
  dimensions: Partial<Record<Dimension, Level>>
  similarities: string
  limitations: string
  missionUse: string
  /** Already widely studied analog (the challenge asks to look beyond these). */
  wellKnown: boolean
}

export const TARGET_LABELS: Record<Target, string> = {
  luna: 'Luna',
  marte: 'Marte',
}

export const ENVIRONMENT_LABELS: Record<Environment, string> = {
  desertico: 'Desértico',
  polar: 'Polar / ártico',
  volcanico: 'Volcánico',
  crater: 'Cráter de impacto',
  subsuelo: 'Cuevas / tubos de lava',
  salar: 'Salar',
}

export const DIMENSION_LABELS: Record<Dimension, string> = {
  geologia: 'Geología',
  terreno: 'Terreno',
  temperatura: 'Temperatura',
  agua_hielo: 'Agua / hielo',
  polvo: 'Polvo / viento',
  habitabilidad: 'Habitabilidad',
  subsuelo: 'Subsuelo',
  operaciones: 'Operaciones',
}
