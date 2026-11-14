import { useEffect, useRef } from 'react'
import {
  Cartesian2,
  Cartesian3,
  Color,
  HorizontalOrigin,
  ImageryLayer,
  LabelStyle,
  NearFarScalar,
  ScreenSpaceEventHandler,
  ScreenSpaceEventType,
  VerticalOrigin,
  Viewer,
  defined,
} from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'
import type { Body } from '../data/types'
import { BODIES, createEarthLayers } from '../planet/bodies'
import type { BaseLayerId, OverlayLayerId } from '../map/gibs'

export interface GlobeMarker {
  id: string
  lat: number
  lng: number
  color: string
  label: string
}

interface Props {
  body: Body
  markers: GlobeMarker[]
  selectedId?: string | null
  /** Point the camera flies to. null returns to the whole-globe view. */
  focus?: { lat: number; lng: number } | null
  variant?: 'globe' | 'closeup'
  onSelect?: (markerId: string) => void
  earthBase?: BaseLayerId
  earthOverlays?: OverlayLayerId[]
  /** Show the altimetry relief instead of the imagery (bodies that have one). */
  relief?: boolean
  /** Overrides the close-up camera height (m). */
  closeupHeight?: number
}

function setLayerShown(layer: ImageryLayer, shown: boolean) {
  layer.show = shown
}

function applyEarthLayers(layers: Map<string, ImageryLayer>, base: BaseLayerId, overlays: OverlayLayerId[]) {
  for (const [id, layer] of layers) {
    if (id === 'world') continue
    layer.show = id === base || overlays.includes(id as OverlayLayerId)
  }
}

export default function PlanetGlobe({
  body,
  markers,
  selectedId = null,
  focus = null,
  variant = 'globe',
  onSelect,
  earthBase = 'bluemarble',
  earthOverlays = [],
  relief = false,
  closeupHeight,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const viewerRef = useRef<Viewer | null>(null)
  const earthLayersRef = useRef<Map<string, ImageryLayer> | null>(null)
  const reliefLayerRef = useRef<ImageryLayer | null>(null)
  const onSelectRef = useRef(onSelect)

  useEffect(() => {
    onSelectRef.current = onSelect
  }, [onSelect])

  // Create one Cesium viewer per body.
  useEffect(() => {
    if (!containerRef.current) return
    const cfg = BODIES[body]
    const viewer = new Viewer(containerRef.current, {
      ellipsoid: cfg.ellipsoid,
      baseLayer: cfg.createBaseLayer ? cfg.createBaseLayer() : false,
      skyAtmosphere: cfg.atmosphere ? undefined : false,
      animation: false,
      baseLayerPicker: false,
      fullscreenButton: false,
      geocoder: false,
      homeButton: false,
      infoBox: false,
      sceneModePicker: false,
      selectionIndicator: false,
      timeline: false,
      navigationHelpButton: false,
      requestRenderMode: true,
      maximumRenderTimeChange: Infinity,
    })
    const scene = viewer.scene
    scene.globe.showGroundAtmosphere = cfg.atmosphere
    scene.globe.baseColor = Color.fromCssColorString('#0b0e17')
    scene.fog.enabled = cfg.atmosphere
    if (scene.moon) scene.moon.show = false
    if (variant === 'closeup' && scene.skyBox) scene.skyBox.show = false

    if (cfg.createReliefLayer) {
      const reliefLayer = cfg.createReliefLayer()
      reliefLayer.show = false
      viewer.imageryLayers.add(reliefLayer)
      reliefLayerRef.current = reliefLayer
    }

    if (body === 'tierra') {
      const layers = createEarthLayers()
      for (const layer of layers.values()) viewer.imageryLayers.add(layer)
      earthLayersRef.current = layers
    }

    viewer.camera.setView({
      destination: Cartesian3.fromDegrees(-20, 15, cfg.globeHeight, cfg.ellipsoid),
    })

    const handler = new ScreenSpaceEventHandler(scene.canvas)
    handler.setInputAction((event: ScreenSpaceEventHandler.PositionedEvent) => {
      const picked = scene.pick(event.position)
      if (defined(picked) && picked.id?.id) onSelectRef.current?.(String(picked.id.id))
    }, ScreenSpaceEventType.LEFT_CLICK)

    viewerRef.current = viewer
    return () => {
      handler.destroy()
      viewer.destroy()
      viewerRef.current = null
      earthLayersRef.current = null
      reliefLayerRef.current = null
    }
  }, [body, variant])

  // Earth layer visibility.
  useEffect(() => {
    const layers = earthLayersRef.current
    const viewer = viewerRef.current
    if (!layers || !viewer) return
    applyEarthLayers(layers, earthBase, earthOverlays)
    viewer.scene.requestRender()
  }, [earthBase, earthOverlays, body, variant])

  // Relief layer visibility.
  useEffect(() => {
    const layer = reliefLayerRef.current
    if (!layer) return
    setLayerShown(layer, relief)
    viewerRef.current?.scene.requestRender()
  }, [relief, body, variant])

  // Markers.
  useEffect(() => {
    const viewer = viewerRef.current
    if (!viewer) return
    const ellipsoid = BODIES[body].ellipsoid
    viewer.entities.removeAll()
    for (const m of markers) {
      const isSelected = m.id === selectedId
      const color = Color.fromCssColorString(m.color)
      viewer.entities.add({
        id: m.id,
        position: Cartesian3.fromDegrees(m.lng, m.lat, 0, ellipsoid),
        point: {
          pixelSize: isSelected ? 16 : 10,
          color,
          outlineColor: Color.WHITE,
          outlineWidth: isSelected ? 3 : 2,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        label:
          variant === 'globe'
            ? {
                text: m.label,
                font: `${isSelected ? 600 : 500} 13px system-ui, sans-serif`,
                fillColor: Color.WHITE,
                outlineColor: Color.BLACK.withAlpha(0.85),
                outlineWidth: 3,
                style: LabelStyle.FILL_AND_OUTLINE,
                horizontalOrigin: HorizontalOrigin.LEFT,
                verticalOrigin: VerticalOrigin.CENTER,
                pixelOffset: new Cartesian2(12, 0),
                show: isSelected || markers.length <= 6,
                translucencyByDistance: new NearFarScalar(1.5e6, 1, 4e7, 0.6),
                disableDepthTestDistance: Number.POSITIVE_INFINITY,
              }
            : undefined,
      })
    }
    viewer.scene.requestRender()
  }, [markers, selectedId, body, variant])

  // Camera.
  useEffect(() => {
    const viewer = viewerRef.current
    if (!viewer) return
    const cfg = BODIES[body]
    if (!focus) {
      if (variant === 'globe') {
        viewer.camera.flyTo({
          destination: Cartesian3.fromDegrees(-20, 15, cfg.globeHeight, cfg.ellipsoid),
          duration: 1.5,
        })
      }
      return
    }
    const height = variant === 'closeup' ? (closeupHeight ?? cfg.closeupHeight) : cfg.globeHeight * 0.55
    viewer.camera.flyTo({
      destination: Cartesian3.fromDegrees(focus.lng, focus.lat, height, cfg.ellipsoid),
      duration: variant === 'closeup' ? 0 : 2,
    })
  }, [focus, body, variant, closeupHeight])

  return <div ref={containerRef} className={`planet-globe ${variant}`} />
}
