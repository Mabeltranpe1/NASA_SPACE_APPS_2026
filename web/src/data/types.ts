export type Body = 'tierra' | 'luna' | 'marte'
export type Target = Exclude<Body, 'tierra'>

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

/** A place on the Moon or Mars that an Earth site is an analog of. */
export interface Homologue {
  /** Stable id; matches the target ids in public/data/comparisons.json. */
  id: string
  body: Target
  name: string
  /** Planetocentric latitude, degrees. */
  lat: number
  /** East-positive longitude in [-180, 180], degrees. */
  lng: number
  note: string
  /** True when the coordinates point to a representative area, not an exact landmark. */
  approximate?: boolean
}

/** NASA GIBS snapshot used for the Earth detail image. Defaults to Landsat WELD (30 m). */
export interface EarthImageOverride {
  layer: string
  time: string
  label: string
}

export interface AnalogSite {
  id: string
  name: string
  country: string
  lat: number
  lng: number
  environments: Environment[]
  /** Planetary places this site is an analog of (one per body at most). */
  homologues: Homologue[]
  /** Planetary location or environment this site is an analog of. */
  analogOf: string
  /** Similarity per dimension. Preliminary qualitative values until the data pipeline computes scores. */
  dimensions: Partial<Record<Dimension, Level>>
  similarities: string
  limitations: string
  missionUse: string
  /** Already widely studied analog (the challenge asks to look beyond these). */
  wellKnown: boolean
  earthImage?: EarthImageOverride
}

export const BODY_LABELS: Record<Body, string> = {
  tierra: 'Tierra',
  luna: 'Luna',
  marte: 'Marte',
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

export function siteTargets(site: AnalogSite): Target[] {
  return [...new Set(site.homologues.map((h) => h.body))]
}

export function homologueFor(site: AnalogSite, body: Target): Homologue | undefined {
  return site.homologues.find((h) => h.body === body)
}
