import { useEffect, useState } from 'react'
import type { Lang } from '../i18n/strings'
import type { AnalogSite } from './types'

/** web/public/data/gallery.json, written by src/export_gallery.py from data/gallery_sources.json. */
export type GalleryKind =
  | 'rover'
  | 'lander'
  | 'apollo'
  | 'orbital'
  | 'visualization'
  | 'field'
  | 'astronaut'
  | 'satellite'
  | 'radar'

export interface GalleryImage {
  key: string
  /** Path inside /images/gallery/. */
  file: string
  kind: GalleryKind
  caption: Record<Lang, string>
  title: string
  date: string
  credit: string
  source_url: string
  width: number
  height: number
}

interface GalleryData {
  generated_at: string
  aliases: Record<string, string>
  places: Record<string, GalleryImage[]>
}

let cache: Promise<GalleryData | null> | null = null

function load() {
  cache ??= fetch('/data/gallery.json')
    .then((r) => (r.ok ? (r.json() as Promise<GalleryData>) : null))
    .catch(() => null)
  return cache
}

/** The whole gallery (null while loading or if it is missing). */
export function useGallery(): GalleryData | null {
  const [data, setData] = useState<GalleryData | null>(null)
  useEffect(() => {
    let alive = true
    load().then((d) => alive && setData(d))
    return () => {
      alive = false
    }
  }, [])
  return data
}

/**
 * Images of one place. Keys: Moon/Mars target ids (homologue ids), Earth catalog
 * site ids, and `region:<region>` for the discoveries of the global search.
 */
export function imagesFor(data: GalleryData | null, key: string | undefined): GalleryImage[] {
  if (!data || !key) return []
  return data.places[data.aliases[key] ?? key] ?? []
}

export function galleryUrl(image: GalleryImage) {
  return `/images/gallery/${image.file}`
}

/** Gallery key of an Earth place: its catalog id, or its region for a discovery. */
export function earthGalleryKey(site: AnalogSite) {
  return site.region ? `region:${site.region}` : site.id
}

/** Number of gallery images of a place and its counterparts (for the "view gallery" button). */
export function useGalleryCount(site: AnalogSite) {
  const gallery = useGallery()
  return (
    imagesFor(gallery, earthGalleryKey(site)).length +
    site.homologues.reduce((n, h) => n + imagesFor(gallery, h.id).length, 0)
  )
}
