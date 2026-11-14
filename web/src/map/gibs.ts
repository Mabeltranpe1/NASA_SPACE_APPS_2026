/**
 * Layers from NASA GIBS (Global Imagery Browse Services).
 * Free, no API key, CORS open. Docs: https://nasa-gibs.github.io/gibs-api-docs/
 */

const GIBS_WMTS = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best'

export interface GibsLayer {
  id: string
  label: string
  description: string
  /** GIBS layer identifier. */
  gibsId: string
  /** 'default' for static layers, or how many days back to request for daily layers. */
  time: 'default' | { daysAgo: number }
  tileMatrixSet: string
  maxZoom: number
  format: 'jpg' | 'jpeg' | 'png'
  opacity?: number
}

function isoDaysAgo(days: number): string {
  const d = new Date()
  d.setUTCDate(d.getUTCDate() - days)
  return d.toISOString().slice(0, 10)
}

export function gibsTileUrl(layer: GibsLayer): string {
  const time = layer.time === 'default' ? 'default' : isoDaysAgo(layer.time.daysAgo)
  return `${GIBS_WMTS}/${layer.gibsId}/default/${time}/${layer.tileMatrixSet}/{z}/{y}/{x}.${layer.format}`
}

export const BASE_LAYERS = [
  {
    id: 'bluemarble',
    label: 'Blue Marble',
    description: 'Mosaico global sin nubes con relieve y batimetría (NASA).',
    gibsId: 'BlueMarble_ShadedRelief_Bathymetry',
    time: 'default',
    tileMatrixSet: 'GoogleMapsCompatible_Level8',
    maxZoom: 8,
    format: 'jpeg',
  },
  {
    id: 'viirs',
    label: 'Satélite reciente',
    description: 'Color verdadero VIIRS (NOAA-20) de hace 2 días.',
    gibsId: 'VIIRS_NOAA20_CorrectedReflectance_TrueColor',
    time: { daysAgo: 2 },
    tileMatrixSet: 'GoogleMapsCompatible_Level9',
    maxZoom: 9,
    format: 'jpg',
  },
  {
    id: 'relief',
    label: 'Relieve (ASTER)',
    description: 'Relieve sombreado del modelo de elevación global ASTER GDEM.',
    gibsId: 'ASTER_GDEM_Greyscale_Shaded_Relief',
    time: 'default',
    tileMatrixSet: 'GoogleMapsCompatible_Level12',
    maxZoom: 12,
    format: 'jpg',
  },
] as const satisfies readonly GibsLayer[]

export const OVERLAY_LAYERS = [
  {
    id: 'lst',
    label: 'Temperatura superficial (MODIS)',
    description: 'Temperatura de la superficie terrestre de día, MODIS Terra, hace 3 días. Hay huecos donde había nubes.',
    gibsId: 'MODIS_Terra_Land_Surface_Temp_Day',
    time: { daysAgo: 3 },
    tileMatrixSet: 'GoogleMapsCompatible_Level7',
    maxZoom: 7,
    format: 'png',
    opacity: 0.75,
  },
  {
    id: 'labels',
    label: 'Fronteras y nombres',
    description: 'Etiquetas de referencia (OpenStreetMap, vía GIBS).',
    gibsId: 'Reference_Labels_15m',
    time: 'default',
    tileMatrixSet: 'GoogleMapsCompatible_Level13',
    maxZoom: 13,
    format: 'png',
  },
] as const satisfies readonly GibsLayer[]

export type BaseLayerId = (typeof BASE_LAYERS)[number]['id']
export type OverlayLayerId = (typeof OVERLAY_LAYERS)[number]['id']
