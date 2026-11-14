import {
  Credit,
  Ellipsoid,
  GeographicTilingScheme,
  ImageryLayer,
  Rectangle,
  SingleTileImageryProvider,
  UrlTemplateImageryProvider,
  WebMercatorTilingScheme,
} from 'cesium'
import type { Body } from '../data/types'
import { BASE_LAYERS, OVERLAY_LAYERS, gibsTileUrl, type GibsLayer } from '../map/gibs'

const TREK = 'https://trek.nasa.gov/tiles'

export interface BodyConfig {
  id: Body
  label: string
  ellipsoid: Ellipsoid
  atmosphere: boolean
  /** Camera height (m) for the whole-globe view. */
  globeHeight: number
  /** Camera height (m) for the site close-up view. */
  closeupHeight: number
  imageryCredit: string
  /** Base imagery for the Moon and Mars. The Earth uses createEarthLayers instead. */
  createBaseLayer?: () => ImageryLayer
  /** Optional shaded-relief (altimetry) layer that can replace the base imagery. */
  createReliefLayer?: () => ImageryLayer
  reliefCredit?: string
}

function trekLayer(body: 'Moon' | 'Mars', product: string, ellipsoid: Ellipsoid, maximumLevel: number, credit: string) {
  return new ImageryLayer(
    new UrlTemplateImageryProvider({
      url: `${TREK}/${body}/EQ/${product}/1.0.0/default/default028mm/{z}/{y}/{x}.jpg`,
      tilingScheme: new GeographicTilingScheme({ ellipsoid }),
      ellipsoid,
      maximumLevel,
      credit: new Credit(credit),
    }),
  )
}

export const BODIES: Record<Body, BodyConfig> = {
  tierra: {
    id: 'tierra',
    label: 'Tierra',
    ellipsoid: Ellipsoid.WGS84,
    atmosphere: true,
    globeHeight: 22_000_000,
    closeupHeight: 60_000,
    imageryCredit: 'NASA GIBS / EOSDIS',
  },
  luna: {
    id: 'luna',
    label: 'Luna',
    ellipsoid: Ellipsoid.MOON,
    atmosphere: false,
    globeHeight: 6_500_000,
    closeupHeight: 60_000,
    imageryCredit: 'NASA Moon Trek · LRO WAC',
    createBaseLayer: () =>
      trekLayer('Moon', 'LRO_WAC_Mosaic_Global_303ppd_v02', Ellipsoid.MOON, 8, 'NASA Moon Trek · LRO WAC (100 m/px)'),
  },
  marte: {
    id: 'marte',
    label: 'Marte',
    ellipsoid: Ellipsoid.MARS,
    atmosphere: false,
    globeHeight: 12_000_000,
    closeupHeight: 120_000,
    imageryCredit: 'NASA Mars Trek · Viking MDIM 2.1',
    createBaseLayer: () =>
      trekLayer('Mars', 'Mars_Viking_MDIM21_ClrMosaic_global_232m', Ellipsoid.MARS, 7, 'NASA Mars Trek · Viking MDIM 2.1 (232 m/px)'),
    createReliefLayer: () =>
      trekLayer('Mars', 'Mars_MGS_MOLA_ClrShade_merge_global_463m', Ellipsoid.MARS, 6, 'NASA Mars Trek · MGS MOLA (463 m/px)'),
    reliefCredit: 'NASA Mars Trek · MOLA relieve coloreado por altura',
  },
}

/**
 * Earth imagery: a whole-world Blue Marble snapshot in geographic projection
 * (covers the poles) under NASA GIBS Web Mercator tiles (more detail, up to ±85°).
 */
export function createEarthLayers(): Map<string, ImageryLayer> {
  const layers = new Map<string, ImageryLayer>()
  layers.set(
    'world',
    new ImageryLayer(
      new SingleTileImageryProvider({
        url: 'https://wvs.earthdata.nasa.gov/api/v1/snapshot?REQUEST=GetSnapshot&CRS=EPSG:4326&FORMAT=image/jpeg&WIDTH=4096&HEIGHT=2048&LAYERS=BlueMarble_ShadedRelief_Bathymetry&BBOX=-90,-180,90,180',
        rectangle: Rectangle.MAX_VALUE,
        tileWidth: 4096,
        tileHeight: 2048,
        credit: new Credit('NASA GIBS / EOSDIS'),
      }),
    ),
  )
  for (const layer of [...BASE_LAYERS, ...OVERLAY_LAYERS] as readonly GibsLayer[]) {
    const imagery = new ImageryLayer(
      new UrlTemplateImageryProvider({
        url: gibsTileUrl(layer),
        tilingScheme: new WebMercatorTilingScheme(),
        maximumLevel: layer.maxZoom,
        hasAlphaChannel: layer.format === 'png',
        credit: new Credit(layer.id === 'labels' ? 'NASA GIBS · © OpenStreetMap' : 'NASA GIBS / EOSDIS'),
      }),
    )
    if (layer.opacity) imagery.alpha = layer.opacity
    imagery.show = false
    layers.set(layer.id, imagery)
  }
  return layers
}
