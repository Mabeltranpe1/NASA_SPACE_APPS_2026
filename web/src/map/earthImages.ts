import { useEffect, useState } from 'react'
import type { AnalogSite } from '../data/types'
import { earthSnapshotUrl } from './snapshot'

/** web/public/images/earth/index.json, written by src/export_images.py. */
interface Manifest {
  generated_at: string
  images: Record<
    string,
    {
      file: string
      source: string
      credit: string
      item: string
      date: string
      cloud_cover: number
      gsd_m: number
      width_km: number
    }
  >
}

export interface EarthImage {
  url: string
  /** Sensor, date and resolution, e.g. "Sentinel-2 L2A · 2024-01-23 · 10 m/px". */
  label: string
  widthKm: number
  credit: string
  /** NASA GIBS snapshot used when the local image fails to load. */
  fallback?: EarthImage
}

let manifest: Promise<Manifest | null> | null = null

function loadManifest() {
  manifest ??= fetch('/images/earth/index.json')
    .then((r) => (r.ok ? (r.json() as Promise<Manifest>) : null))
    .catch(() => null)
  return manifest
}

function gibsImage(site: AnalogSite): EarthImage {
  const s = earthSnapshotUrl(site)
  return { url: s.url, label: s.label, widthKm: s.widthKm, credit: 'NASA GIBS' }
}

/**
 * Close-up image of an Earth place: the pre-rendered Sentinel-2 / Landsat crop
 * when there is one, otherwise the NASA GIBS snapshot. null while the index loads.
 */
export function useEarthImage(site: AnalogSite): EarthImage | null {
  const [data, setData] = useState<Manifest | null | undefined>(undefined)
  useEffect(() => {
    let alive = true
    loadManifest().then((m) => alive && setData(m))
    return () => {
      alive = false
    }
  }, [])
  if (data === undefined) return null
  const gibs = gibsImage(site)
  const m = data?.images[site.id]
  if (!m) return gibs
  return {
    url: `/images/earth/${m.file}?v=${m.date}`,
    label: `${m.source} · ${m.date} · ${m.gsd_m} m/px`,
    widthKm: m.width_km,
    credit: m.credit,
    fallback: gibs,
  }
}

/** The image to show: the fallback once the main one failed to load. */
export function shownImage(image: EarthImage | null, failed: boolean): EarthImage | null {
  return image && failed && image.fallback ? image.fallback : image
}
