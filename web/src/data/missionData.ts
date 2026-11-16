import { useEffect, useState } from 'react'
import type { MissionId } from '../comparator/missions'

/** public/data/missions.json (web/scripts/export-missions.ts). */
export interface MissionData {
  n_cells: number
  missions: MissionId[]
  /** Weights of each mission per body (model weight x mission factor). */
  weights: Record<'Moon' | 'Mars', Record<MissionId, Record<string, number>>>
  /** Best score Earth has for each mission, per Moon/Mars site id. */
  reference: Record<string, Record<MissionId, number>>
}

let cache: Promise<MissionData> | null = null

function load(): Promise<MissionData> {
  cache ??= fetch('/data/missions.json').then((r) => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    return r.json() as Promise<MissionData>
  })
  cache.catch(() => (cache = null))
  return cache
}

/** Mission weights and references, or null while loading / if missing (the UI then hides missions). */
export function useMissionData(): MissionData | null {
  const [data, setData] = useState<MissionData | null>(null)
  useEffect(() => {
    let alive = true
    load()
      .then((d) => alive && setData(d))
      .catch(() => undefined)
    return () => {
      alive = false
    }
  }, [])
  return data
}
