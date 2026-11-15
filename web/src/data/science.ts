import { useEffect, useState } from 'react'

export type Localized = { es: string; en: string }
export type ScienceValue = number | string | boolean | null

export interface ScienceReference {
  id?: string
  study_id?: string
  url: string
  name: Localized
  overlap_study_pct?: number
  overlap_target_pct?: number
  center_separation_projected_km?: number
  relation?: string
  note?: Localized
}

export interface ScienceField {
  id: string
  app_field: string
  original_column: string
  label: Localized
  definition: Localized
  unit: string
  source_ids: string[]
  spatial_support: string
  period: string
  method: string
  compatibility: string
  global_candidate: string | null
  conversion: string
  method_text: Localized
  support_text: Localized
  compatibility_text: Localized
  quality_reference: string
}

export interface ScienceSection {
  id: string
  title: Localized
  fields: ScienceField[]
  records: Record<string, ScienceValue>[]
  source_ids: string[]
  spatial_support: string
  period: string
  method: string
  compatibility: string
  status: string
  source_file: string
}

export interface PaiResult {
  target: string
  candidate: string
  distance: number
  PAI: number
  rank_among_six: number
  study_url: string
}

export interface ScienceStudy {
  version: '1.0.0'
  id: string
  region: string
  planet: 'earth' | 'moon' | 'mars'
  site_id?: string
  name: Localized
  author: { name: string; github: string }
  source_commit: string
  geometry: {
    latitude: number
    longitude_east_signed_deg: number
    resolution_m: [number, number]
    nominal_window_km: number
    crs_wkt: string
    bounds_projected_m: [number, number, number, number]
  } | null
  sections: ScienceSection[]
  quality_flags: { code: string; level: 'warning' | 'info'; message: Localized }[]
  sources: { id: string; name: string; institution: string; url: string; evidence_type: string }[]
  assets: { url: string; source_file: string; sha256?: string; bytes?: number; kind?: string }[]
  pai: {
    model: { id: string; label: Localized; equation: string; note: Localized; features: { id: string; weight: number }[] }
    results: PaiResult[]
  }
}

type State<T> = { status: 'idle' | 'loading' } | { status: 'error'; message: string } | { status: 'ready'; data: T }

const studyCache = new Map<string, Promise<ScienceStudy>>()

export function validateStudy(value: unknown): ScienceStudy {
  if (!value || typeof value !== 'object') throw new Error('Invalid scientific document')
  const d = value as Partial<ScienceStudy>
  if (d.version !== '1.0.0' || typeof d.id !== 'string' || !d.name || !Array.isArray(d.sections) || !Array.isArray(d.quality_flags) || !d.pai || !Array.isArray(d.pai.results)) {
    throw new Error('Unsupported scientific data contract')
  }
  if (new Set(d.sections.map((s) => s.id)).size !== d.sections.length) throw new Error('Duplicate scientific section')
  if (d.pai.results.some((r) => !Number.isFinite(r.PAI) || r.PAI < 0 || r.PAI > 100)) throw new Error('Invalid topographic PAI')
  return d as ScienceStudy
}

export function useScientificStudy(reference: ScienceReference | null | undefined): State<ScienceStudy> {
  const url = reference?.url ?? null
  const [state, setState] = useState<State<ScienceStudy> & { url?: string }>({ status: 'idle' })
  useEffect(() => {
    if (!url) return
    let alive = true
    let request = studyCache.get(url)
    if (!request) {
      request = fetch(url).then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<unknown>
      }).then(validateStudy)
      studyCache.set(url, request)
      request.catch(() => studyCache.delete(url))
    }
    request.then(
      (data) => { if (alive) setState({ status: 'ready', data, url }) },
      (error: unknown) => { if (alive) setState({ status: 'error', message: String(error), url }) },
    )
    return () => { alive = false }
  }, [url])
  if (!url) return { status: 'idle' }
  return state.url === url ? state : { status: 'loading' }
}

export interface GlobalRankingRow {
  body: 'Moon' | 'Mars'
  rank: number
  earth_region: string
  region_description: string
  earth_lat: number
  earth_lon: number
  mean_score_all_sites: number
  conditions_met: string
  weakest: string
  best_site: string
  score_best_site: number
  site_id: string
  target_id: string
}

export interface GlobalRankings {
  version: '1.0.0'
  n_cells: number
  n_regions: number
  source_commit: string
  source_sha256: string
  model: { id: string; note: string; separation_km: number }
  rows: GlobalRankingRow[]
}

let globalCache: Promise<GlobalRankings> | null = null

export function useGlobalRankings(): State<GlobalRankings> {
  const [state, setState] = useState<State<GlobalRankings>>({ status: 'loading' })
  useEffect(() => {
    let alive = true
    globalCache ??= fetch('/data/global-rankings.json').then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      return r.json() as Promise<GlobalRankings>
    }).then((data) => {
      if (data.version !== '1.0.0' || !Array.isArray(data.rows) || data.rows.length !== 200) throw new Error('Invalid global ranking contract')
      return data
    })
    globalCache.then(
      (data) => { if (alive) setState({ status: 'ready', data }) },
      (error: unknown) => { globalCache = null; if (alive) setState({ status: 'error', message: String(error) }) },
    )
    return () => { alive = false }
  }, [])
  return state
}
