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

/** web/public/data/science/index.json, written by src/export_science.py. */
export interface ScienceIndex {
  version: string
  studies: { id: string; region: string; planet: 'earth' | 'moon' | 'mars'; site_id?: string; name: Localized; url: string }[]
  /** Regional windows that overlap each Moon/Mars target, keyed by the target NAME of data/targets.csv. */
  target_associations: Record<string, ScienceReference[]>
}

let indexCache: Promise<ScienceIndex | null> | null = null

/** The scientific index (null while loading or if it is missing). */
export function useScienceIndex(): ScienceIndex | null {
  const [data, setData] = useState<ScienceIndex | null>(null)
  useEffect(() => {
    let alive = true
    indexCache ??= fetch('/data/science/index.json')
      .then((r) => (r.ok ? (r.json() as Promise<ScienceIndex>) : null))
      .catch(() => null)
    indexCache.then((d) => alive && setData(d))
    return () => {
      alive = false
    }
  }, [])
  return data
}

/** Regional study of an Earth catalog site (the Colombian case study), if any. */
export function studyForSite(index: ScienceIndex | null, siteId: string): ScienceReference | null {
  const study = index?.studies.find((s) => s.site_id === siteId)
  return study ? { id: study.id, url: study.url, name: study.name } : null
}

/** Regional windows that overlap a Moon/Mars target (matched by geometry, never by name). */
export function studiesForTarget(index: ScienceIndex | null, targetName: string): ScienceReference[] {
  return index?.target_associations[targetName] ?? []
}
