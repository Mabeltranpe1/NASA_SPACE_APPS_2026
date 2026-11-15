/**
 * Types of public/data/analogos.json, made by `python src/export_web.py`
 * (repo root). Load it with: fetch('/data/analogos.json').then((r) => r.json() as Promise<AnalogData>)
 * Images: use `image.url` (served from public/data/img/, copied by scripts/copy-data-images.mjs).
 * See web/DATOS.md.
 */

export type Body = 'Moon' | 'Mars'

/** Variable keys, same names in values / earth_values / similarity. */
export type FeatureKey =
  | 'elev_m' | 'slope_deg' | 'roughness' | 'temp_mean_K' | 'temp_range_K'
  | 'albedo' | 'precip_mm' | 'ndvi' | 'em_contrast'

export type Oxide = 'SiO2' | 'TiO2' | 'Al2O3' | 'FeO' | 'MgO' | 'CaO' | 'Na2O' | 'K2O'

export type RockTypeKey =
  | 'luna_feldespatica' | 'luna_feldespatica_noritica'
  | 'marte_basalto_olivinico' | 'marte_suelo_basaltico' | 'marte_tipo2'
  | 'tierra_basalto' | 'tierra_andesita' | 'tierra_granito' | 'tierra_arena_cuarzo'

export type ImageKind =
  | 'mapa_relieve'      // shaded relief map made by src/make_maps.py
  | 'foto_orbital'      // photo from orbit (LROC, CTX, ...)
  | 'foto_satelite'     // Earth satellite photo (Sentinel-2)
  | 'foto_superficie'   // photo taken on the surface (rover, Apollo)

export interface ImageRef {
  kind: ImageKind
  /** Path in the repo (maps/..., experiments/...). */
  src: string
  /** URL to use in <img src>. */
  url: string
  title: string
  credit: string | null
  source: string | null
  lat: number | null
  lon: number | null
  /** Earth images only: true if the image shows this exact analog place (< 10 km). */
  same_place?: boolean
  distance_km?: number
  /** Surface photos: distance from the photo to the Moon/Mars site centre. */
  distance_to_site_km?: number
  mission?: string
  instrument?: string
  date?: string | null
  product_id?: string
  licence?: string
  coord_precision?: string
  width?: number
  height?: number
  /** Warning to show next to the image, if any. */
  note?: string
  /** Only in reference_photos. */
  body?: Body
}

export interface SiteComposition {
  lithology: string
  /** Christiansen feature position (micrometres) and its uncertainty. */
  cf_um: number
  cf_sigma_um: number
  /** Rock-type value on the same scale as Earth ASTER (approximate, ± sigma). */
  em_contrast: number
  em_contrast_sigma: number
  evidence: string
  /** Key into AnalogData.rock_types (typical oxide composition for the chart). */
  rock_type: RockTypeKey
}

export interface EarthComposition {
  em_contrast: number
  cf_equivalent_um: number
  rock_type: RockTypeKey
  /** true when a low value can also mean carbonate, clay, evaporite or ice. */
  ambiguous: boolean
  note: string
}

export interface Analog {
  /** 1 = best region for this site. */
  rank: number
  region: string
  region_label: string
  region_description: string | null
  lat: number
  lon: number
  /** Overall similarity 0..1. */
  score: number
  earth_values: Record<FeatureKey, number | null>
  /** Similarity per variable 0..1 (elev_m is not compared). */
  similarity: Partial<Record<FeatureKey, number | null>>
  best_match: FeatureKey
  worst_match: FeatureKey
  composition: EarthComposition | null
  /** May be empty: no map/photo made yet for this place. */
  images: ImageRef[]
}

export interface PlanetarySite {
  id: string
  number: number
  name: string
  body: Body
  lat: number
  lon: number
  area: string
  values: Record<FeatureKey, number | null>
  composition: SiteComposition
  images: ImageRef[]
  /** 5 best Earth analogs, one per region, best first. */
  analogs: Analog[]
}

export interface OverallRow {
  rank: number
  region: string
  lat: number
  lon: number
  mean_score: number
  /** e.g. "5 of 8": variables with mean similarity >= 0.5 */
  conditions_met: string
  weakest: FeatureKey
  similarity: Partial<Record<FeatureKey, number>>
}

export interface RegionInfo {
  name: string
  west: number
  south: number
  east: number
  north: number
  /** Famous analog region (left out of the rankings). */
  known: boolean
  description: string
}

export interface RockType {
  label: string
  /** Typical composition, wt % (literature, NOT measured at the place). */
  oxides: Record<Oxide, number>
  source: string
}

export interface AnalogData {
  generated: string
  about: string
  features: Record<FeatureKey, { label: string; unit: string }>
  composition_method: string
  oxides_order: Oxide[]
  oxides_note: string
  rock_types: Record<RockTypeKey, RockType>
  sites: PlanetarySite[]
  /** Best place of each Earth region for all sites of one body together. */
  overall: Record<Body, OverallRow[]>
  regions: RegionInfo[]
  /** Moon/Mars surface photos not linked to a site (Apollo, Pathfinder). */
  reference_photos: ImageRef[]
}
