import type { AnalogSite } from '../data/types'

const SNAPSHOT = 'https://wvs.earthdata.nasa.gov/api/v1/snapshot'

const DEFAULT_EARTH_IMAGE = {
  layer: 'Landsat_WELD_CorrectedReflectance_TrueColor_Global_Annual',
  time: '2000-01-01',
  label: 'Landsat (WELD) · 30 m/px',
  halfLatDeg: 0.1,
}

/** Landsat WELD has no data near the poles: use a summer MODIS Terra scene instead. */
function highLatitudeImage(lat: number) {
  const time = lat > 0 ? '2024-07-15' : '2024-01-10'
  return { layer: 'MODIS_Terra_CorrectedReflectance_TrueColor', time, label: `MODIS Terra · ${time}`, halfLatDeg: 0.4 }
}

/** Snapshot of a square area around (lat, lng). Longitude span is widened by 1/cos(lat) to keep the ground square. */
export function earthSnapshotUrl(site: AnalogSite) {
  const image = site.earthImage
    ? { ...site.earthImage, halfLatDeg: 0.4 }
    : Math.abs(site.lat) > 78
      ? highLatitudeImage(site.lat)
      : DEFAULT_EARTH_IMAGE
  const half = image.halfLatDeg
  const halfLng = half / Math.max(Math.cos((site.lat * Math.PI) / 180), 0.05)
  const bbox = [site.lat - half, site.lng - halfLng, site.lat + half, site.lng + halfLng].map((v) => v.toFixed(4))
  const params = new URLSearchParams({
    REQUEST: 'GetSnapshot',
    CRS: 'EPSG:4326',
    FORMAT: 'image/jpeg',
    WIDTH: '768',
    HEIGHT: '768',
    LAYERS: image.layer,
    TIME: image.time,
    BBOX: bbox.join(','),
  })
  const widthKm = Math.round(2 * half * 111)
  return { url: `${SNAPSHOT}?${params}`, label: image.label, widthKm }
}
