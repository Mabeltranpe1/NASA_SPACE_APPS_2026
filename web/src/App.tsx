import { useCallback, useMemo, useRef, useState } from 'react'
import { SITES } from './data/sites'
import {
  BODY_LABELS,
  DIMENSION_LABELS,
  ENVIRONMENT_LABELS,
  homologueFor,
  siteTargets,
  type AnalogSite,
  type Body,
  type Dimension,
  type Environment,
  type Target,
} from './data/types'
import PlanetGlobe, { type GlobeMarker } from './components/PlanetGlobe'
import DetailImage from './components/DetailImage'
import ComparisonPanel from './components/ComparisonPanel'
import { BODY_COLORS } from './theme'
import GuidedTour from './components/GuidedTour'
import type { TourStep } from './data/tour'
import { BASE_LAYERS, OVERLAY_LAYERS, type BaseLayerId, type OverlayLayerId } from './map/gibs'
import './App.css'

type Mode = 'tierra-luna' | 'tierra-marte' | 'luna-marte'

const MODES: Record<Mode, { label: string; left: Body; right: Body; requires: Target[] }> = {
  'tierra-luna': { label: 'Tierra ↔ Luna', left: 'tierra', right: 'luna', requires: ['luna'] },
  'tierra-marte': { label: 'Tierra ↔ Marte', left: 'tierra', right: 'marte', requires: ['marte'] },
  'luna-marte': { label: 'Luna ↔ Marte', left: 'luna', right: 'marte', requires: ['luna', 'marte'] },
}


function googleEarthUrl(site: AnalogSite) {
  return `https://earth.google.com/web/@${site.lat},${site.lng},1000a,20000d,35y,0h,45t,0r`
}

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value]
}

/** Location of a site on a given body: the site itself on Earth, its homologue elsewhere. */
function locationOn(site: AnalogSite, body: Body) {
  if (body === 'tierra') return { lat: site.lat, lng: site.lng, name: site.name }
  const h = homologueFor(site, body)
  return h ? { lat: h.lat, lng: h.lng, name: h.name } : null
}

function markersFor(sites: AnalogSite[], body: Body): GlobeMarker[] {
  const seen = new Map<string, GlobeMarker>()
  for (const site of sites) {
    const loc = locationOn(site, body)
    if (!loc) continue
    // Several Earth sites can share a homologue: one marker per place, it selects the first site.
    const key = `${loc.lat},${loc.lng}`
    if (!seen.has(key)) seen.set(key, { id: site.id, lat: loc.lat, lng: loc.lng, color: BODY_COLORS[body], label: loc.name })
  }
  return [...seen.values()]
}

export default function App() {
  const [mode, setMode] = useState<Mode>('tierra-marte')
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [dimensions, setDimensions] = useState<Dimension[]>([])
  const [onlyLesserKnown, setOnlyLesserKnown] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [baseLayer, setBaseLayer] = useState<BaseLayerId>('bluemarble')
  const [overlays, setOverlays] = useState<OverlayLayerId[]>(['labels'])

  const { left, right, requires } = MODES[mode]

  const filtered = useMemo(
    () =>
      SITES.filter((s) => {
        const targets = siteTargets(s)
        if (!requires.every((t) => targets.includes(t))) return false
        if (environments.length && !environments.some((e) => s.environments.includes(e))) return false
        if (dimensions.length && !dimensions.every((d) => s.dimensions[d] === 'alta' || s.dimensions[d] === 'media'))
          return false
        if (onlyLesserKnown && s.wellKnown) return false
        return true
      }),
    [requires, environments, dimensions, onlyLesserKnown],
  )

  const selected = filtered.find((s) => s.id === selectedId) ?? null
  const leftMarkers = useMemo(() => markersFor(filtered, left), [filtered, left])
  const rightMarkers = useMemo(() => markersFor(filtered, right), [filtered, right])
  const leftFocus = useMemo(() => (selected ? locationOn(selected, left) : null), [selected, left])
  const rightFocus = useMemo(() => (selected ? locationOn(selected, right) : null), [selected, right])

  const resetFilters = () => {
    setEnvironments([])
    setDimensions([])
    setOnlyLesserKnown(false)
  }

  const [touring, setTouring] = useState(false)
  const mainRef = useRef<HTMLElement>(null)
  const applyTourStep = useCallback((step: TourStep) => {
    setMode(step.mode)
    setEnvironments([])
    setDimensions([])
    setOnlyLesserKnown(false)
    setSelectedId(step.siteId)
    const main = mainRef.current
    if (!main) return
    if (step.showComparison) {
      window.setTimeout(() => main.querySelector('.comparison')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 2500)
    } else {
      main.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }, [])
  const closeTour = useCallback(() => setTouring(false), [])

  return (
    <div className="app">
      <aside className="sidebar">
        <header className="brand">
          <p className="eyebrow">NASA Space Apps 2026</p>
          <h1>Análogos terrestres</h1>
          <p className="subtitle">Lugares de la Tierra que nos preparan para vivir en la Luna y en Marte</p>
        </header>

        <section className="filter-group">
          <h2>Tipo de ambiente</h2>
          <div className="chips">
            {(Object.keys(ENVIRONMENT_LABELS) as Environment[]).map((e) => (
              <button
                key={e}
                className={`chip ${environments.includes(e) ? 'active' : ''}`}
                onClick={() => setEnvironments((prev) => toggle(prev, e))}
              >
                {ENVIRONMENT_LABELS[e]}
              </button>
            ))}
          </div>
        </section>

        <section className="filter-group">
          <h2>Debe parecerse en…</h2>
          <div className="chips">
            {(Object.keys(DIMENSION_LABELS) as Dimension[]).map((d) => (
              <button
                key={d}
                className={`chip ${dimensions.includes(d) ? 'active' : ''}`}
                onClick={() => setDimensions((prev) => toggle(prev, d))}
              >
                {DIMENSION_LABELS[d]}
              </button>
            ))}
          </div>
        </section>

        <label className="checkbox">
          <input type="checkbox" checked={onlyLesserKnown} onChange={(e) => setOnlyLesserKnown(e.target.checked)} />
          Solo análogos poco estudiados
        </label>

        <div className="results-header">
          <span>
            {filtered.length} sitios en {MODES[mode].label}
          </span>
          <button className="link" onClick={resetFilters}>
            Limpiar filtros
          </button>
        </div>

        {selected ? (
          <SiteDetail site={selected} onClose={() => setSelectedId(null)} />
        ) : (
          <ul className="site-list">
            {filtered.map((s) => (
              <li key={s.id}>
                <button onClick={() => setSelectedId(s.id)}>
                  <span className="dot" style={{ background: BODY_COLORS.tierra }} />
                  <span>
                    <strong>
                      {s.name}
                      {!s.wellKnown && <span className="badge">Poco estudiado</span>}
                    </strong>
                    <small>
                      {s.country} → {s.homologues.map((h) => h.name).join(' · ')}
                    </small>
                  </span>
                </button>
              </li>
            ))}
            {filtered.length === 0 && <li className="empty">Ningún sitio cumple estos filtros.</li>}
          </ul>
        )}

        <footer className="note">
          Similitudes preliminares (cualitativas). Se reemplazarán por puntajes calculados con datos de NASA, ESA,
          JAXA y CSA. Imágenes: NASA GIBS, NASA Moon Trek y Mars Trek.
        </footer>
      </aside>

      <main className="main" ref={mainRef}>
        <div className="topbar">
          <button className="tour-button" onClick={() => setTouring(true)} disabled={touring}>
            ▶ Recorrido guiado
          </button>
          <div className="mode-switch" role="tablist" aria-label="Comparación">
            {(Object.keys(MODES) as Mode[]).map((m) => (
              <button key={m} role="tab" aria-selected={mode === m} className={mode === m ? 'active' : ''} onClick={() => setMode(m)}>
                {MODES[m].label}
              </button>
            ))}
          </div>
          {selected && (
            <p className="pair-title">
              <span>
                <span className="swatch" style={{ background: BODY_COLORS[left] }} /> {leftFocus?.name}
              </span>
              <span className="vs">≈</span>
              <span>
                <span className="swatch" style={{ background: BODY_COLORS[right] }} /> {rightFocus?.name}
              </span>
            </p>
          )}
        </div>

        <section className="globes">
          {[left, right].map((body, i) => (
            <div className="globe-card" key={`${mode}-${body}`}>
              <div className="globe-label">
                <span className="dot" style={{ background: BODY_COLORS[body] }} />
                {BODY_LABELS[body]}
              </div>
              <PlanetGlobe
                body={body}
                markers={i === 0 ? leftMarkers : rightMarkers}
                selectedId={selected?.id ?? null}
                focus={i === 0 ? leftFocus : rightFocus}
                onSelect={setSelectedId}
                earthBase={baseLayer}
                earthOverlays={overlays}
              />
              {body === 'tierra' && (
                <details className="layer-panel">
                  <summary>Capas NASA</summary>
                  {BASE_LAYERS.map((l) => (
                    <label key={l.id} title={l.description}>
                      <input type="radio" name="base-layer" checked={baseLayer === l.id} onChange={() => setBaseLayer(l.id)} />
                      {l.label}
                    </label>
                  ))}
                  {OVERLAY_LAYERS.map((l) => (
                    <label key={l.id} title={l.description}>
                      <input
                        type="checkbox"
                        checked={overlays.includes(l.id)}
                        onChange={() => setOverlays((prev) => toggle(prev, l.id))}
                      />
                      {l.label}
                    </label>
                  ))}
                </details>
              )}
            </div>
          ))}
        </section>

        <section className="details">
          {selected ? (
            [left, right].map((body) => (
              <DetailImage
                key={`${selected.id}-${body}`}
                body={body}
                site={selected}
                homologue={body === 'tierra' ? undefined : homologueFor(selected, body)}
              />
            ))
          ) : (
            <div className="details-empty">
              Selecciona un sitio en la lista o en el globo para comparar sus imágenes de cerca.
            </div>
          )}
        </section>

        {selected &&
          requires.map((body) => <ComparisonPanel key={`${selected.id}-${body}`} site={selected} body={body} />)}
        {touring && <GuidedTour onApply={applyTourStep} onClose={closeTour} />}
      </main>
    </div>
  )
}

function SiteDetail({ site, onClose }: { site: AnalogSite; onClose: () => void }) {
  return (
    <article className="detail">
      <button className="link" onClick={onClose}>
        ← Volver a la lista
      </button>
      <h2>{site.name}</h2>
      <p className="meta">
        {site.country} · {site.lat.toFixed(2)}°, {site.lng.toFixed(2)}°
        {!site.wellKnown && <span className="badge">Poco estudiado</span>}
      </p>

      <h3>Homólogos</h3>
      <ul className="homologues">
        {site.homologues.map((h) => (
          <li key={h.body}>
            <span className="dot" style={{ background: BODY_COLORS[h.body] }} />
            <span>
              <strong>
                {BODY_LABELS[h.body]}: {h.name}
              </strong>
              <small>
                {h.note}
                {h.approximate && ' (ubicación aproximada)'}
              </small>
            </span>
          </li>
        ))}
      </ul>

      <h3>Similitud por dimensión (preliminar)</h3>
      <ul className="dims">
        {(Object.keys(DIMENSION_LABELS) as Dimension[])
          .filter((d) => site.dimensions[d])
          .map((d) => (
            <li key={d}>
              <span>{DIMENSION_LABELS[d]}</span>
              <span className={`level ${site.dimensions[d]}`}>{site.dimensions[d]}</span>
            </li>
          ))}
      </ul>

      <h3>En qué se parece</h3>
      <p>{site.similarities}</p>
      <h3>Dónde deja de valer la analogía</h3>
      <p>{site.limitations}</p>
      <h3>Para qué sirve en una misión</h3>
      <p>{site.missionUse}</p>

      <a className="earth-button" href={googleEarthUrl(site)} target="_blank" rel="noreferrer">
        Ver en Google Earth ↗
      </a>
    </article>
  )
}
