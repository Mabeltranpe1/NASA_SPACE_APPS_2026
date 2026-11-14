import { useEffect, useRef } from 'react'
import {
  GlobeControl,
  Map as MapLibreMap,
  Marker,
  NavigationControl,
  Popup,
  ScaleControl,
  type StyleSpecification,
} from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { AnalogSite } from '../data/types'
import {
  BASE_LAYERS,
  OVERLAY_LAYERS,
  gibsTileUrl,
  type BaseLayerId,
  type GibsLayer,
  type OverlayLayerId,
} from '../map/gibs'

interface Props {
  sites: AnalogSite[]
  selectedId: string | null
  onSelect: (id: string | null) => void
  baseLayer: BaseLayerId
  overlays: OverlayLayerId[]
  colorFor: (site: AnalogSite) => string
  earthUrlFor: (site: AnalogSite) => string
}

const ATTRIBUTION =
  'Imágenes: <a href="https://earthdata.nasa.gov/gibs" target="_blank" rel="noreferrer">NASA GIBS / EOSDIS</a> · Etiquetas © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a>'

function buildStyle(): StyleSpecification {
  const sources: StyleSpecification['sources'] = {}
  const layers: StyleSpecification['layers'] = [
    { id: 'background', type: 'background', paint: { 'background-color': '#05070d' } },
  ]

  for (const layer of [...BASE_LAYERS, ...OVERLAY_LAYERS] as readonly GibsLayer[]) {
    sources[layer.id] = {
      type: 'raster',
      tiles: [gibsTileUrl(layer)],
      tileSize: 256,
      maxzoom: layer.maxZoom,
      attribution: ATTRIBUTION,
    }
    layers.push({
      id: layer.id,
      type: 'raster',
      source: layer.id,
      layout: { visibility: 'none' },
      paint: layer.opacity ? { 'raster-opacity': layer.opacity } : {},
    })
  }

  return {
    version: 8,
    projection: { type: 'globe' },
    sources,
    layers,
  }
}

function popupContent(site: AnalogSite, earthUrl: string): HTMLElement {
  const root = document.createElement('div')
  root.className = 'popup'
  const title = document.createElement('strong')
  title.textContent = site.name
  const desc = document.createElement('p')
  desc.textContent = site.analogOf
  const link = document.createElement('a')
  link.href = earthUrl
  link.target = '_blank'
  link.rel = 'noreferrer'
  link.textContent = 'Ver en Google Earth ↗'
  root.append(title, desc, link)
  return root
}

export default function SiteMap({ sites, selectedId, onSelect, baseLayer, overlays, colorFor, earthUrlFor }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const markersRef = useRef<Map<string, Marker>>(new Map())
  const popupRef = useRef<Popup | null>(null)
  const onSelectRef = useRef(onSelect)
  useEffect(() => {
    onSelectRef.current = onSelect
  }, [onSelect])

  // Create the map once.
  useEffect(() => {
    if (!containerRef.current) return
    const map = new MapLibreMap({
      container: containerRef.current,
      style: buildStyle(),
      center: [-20, 15],
      zoom: 1.6,
      attributionControl: { compact: true },
    })
    map.addControl(new NavigationControl({ visualizePitch: true }), 'top-right')
    map.addControl(new GlobeControl(), 'top-right')
    map.addControl(new ScaleControl({ unit: 'metric' }), 'bottom-right')
    mapRef.current = map
    const markers = markersRef.current
    return () => {
      markers.clear()
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Visible layers.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const apply = () => {
      for (const l of BASE_LAYERS) map.setLayoutProperty(l.id, 'visibility', l.id === baseLayer ? 'visible' : 'none')
      for (const l of OVERLAY_LAYERS) map.setLayoutProperty(l.id, 'visibility', overlays.includes(l.id) ? 'visible' : 'none')
    }
    if (map.isStyleLoaded()) apply()
    else map.once('load', apply)
  }, [baseLayer, overlays])

  // Markers for the filtered sites.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const markers = markersRef.current
    const visible = new Set(sites.map((s) => s.id))

    for (const [id, marker] of markers) {
      if (!visible.has(id)) {
        marker.remove()
        markers.delete(id)
      }
    }
    for (const site of sites) {
      if (markers.has(site.id)) continue
      const el = document.createElement('button')
      el.className = 'site-marker'
      el.style.background = colorFor(site)
      el.title = site.name
      el.setAttribute('aria-label', site.name)
      el.addEventListener('click', (e) => {
        e.stopPropagation()
        onSelectRef.current(site.id)
      })
      markers.set(site.id, new Marker({ element: el }).setLngLat([site.lng, site.lat]).addTo(map))
    }
  }, [sites, colorFor])

  // Selected site: highlight, fly to it and show a popup.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    for (const [id, marker] of markersRef.current) {
      marker.getElement().classList.toggle('selected', id === selectedId)
    }
    popupRef.current?.remove()
    popupRef.current = null

    const site = sites.find((s) => s.id === selectedId)
    if (!site) return
    map.flyTo({ center: [site.lng, site.lat], zoom: Math.max(map.getZoom(), 6), duration: 1800 })
    const popup = new Popup({ offset: 16, closeButton: true, maxWidth: '260px' })
      .setLngLat([site.lng, site.lat])
      .setDOMContent(popupContent(site, earthUrlFor(site)))
      .addTo(map)
    popup.on('close', () => {
      if (popupRef.current === popup) onSelectRef.current(null)
    })
    popupRef.current = popup
  }, [selectedId, sites, earthUrlFor])

  return <div ref={containerRef} className="site-map" />
}
