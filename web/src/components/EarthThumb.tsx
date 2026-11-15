import { useState } from 'react'
import type { AnalogSite } from '../data/types'
import { shownImage, useEarthImage } from '../map/earthImages'

/** Earth thumbnail: the Sentinel-2 crop, or NASA GIBS if it fails. */
export default function EarthThumb({ site, alt = '' }: { site: AnalogSite; alt?: string }) {
  const [failed, setFailed] = useState(false)
  const image = shownImage(useEarthImage(site), failed)
  if (!image) return null
  return <img key={image.url} src={image.url} alt={alt} loading="lazy" onError={() => image.fallback && setFailed(true)} />
}
