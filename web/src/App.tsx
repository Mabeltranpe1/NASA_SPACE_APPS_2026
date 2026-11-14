import { useMemo, useState } from 'react'
import {
  APIProvider,
  AdvancedMarker,
  InfoWindow,
  Map,
  Pin,
} from '@vis.gl/react-google-maps'
import { SITES } from './data/sites'
import {
  DIMENSION_LABELS,
  ENVIRONMENT_LABELS,
  TARGET_LABELS,
  type AnalogSite,
  type Dimension,
  type Environment,
  type Target,
} from './data/types'
import './App.css'

const API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY as string | undefined
const MAP_ID = (import.meta.env.VITE_GOOGLE_MAPS_MAP_ID as string | undefined) ?? 'DEMO_MAP_ID'

const TARGET_COLORS: Record<Target | 'ambos', string> = {
  luna: '#9aa4b2',
  marte: '#d0603b',
  ambos: '#8e6bd6',
}

function siteColor(site: AnalogSite) {
  if (site.targets.length > 1) return TARGET_COLORS.ambos
  return TARGET_COLORS[site.targets[0]]
}

function googleEarthUrl(site: AnalogSite) {
  return `https://earth.google.com/web/@${site.lat},${site.lng},1000a,20000d,35y,0h,45t,0r`
}

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value]
}

export default function App() {
  const [target, setTarget] = useState<Target | 'todos'>('todos')
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [dimensions, setDimensions] = useState<Dimension[]>([])
  const [onlyLesserKnown, setOnlyLesserKnown] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const filtered = useMemo(
    () =>
      SITES.filter((s) => {
        if (target !== 'todos' && !s.targets.includes(target)) return false
        if (environments.length && !environments.some((e) => s.environments.includes(e))) return false
        if (
          dimensions.length &&
          !dimensions.every((d) => s.dimensions[d] === 'alta' || s.dimensions[d] === 'media')
        )
          return false
        if (onlyLesserKnown && s.wellKnown) return false
        return true
      }),
    [target, environments, dimensions, onlyLesserKnown],
  )

  const selected = filtered.find((s) => s.id === selectedId) ?? null

  const resetFilters = () => {
    setTarget('todos')
    setEnvironments([])
    setDimensions([])
    setOnlyLesserKnown(false)
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <header>
          <h1>Análogos terrestres</h1>
          <p className="subtitle">Lugares de la Tierra que se parecen a la Luna y a Marte</p>
        </header>

        <section className="filter-group">
          <h2>Objetivo</h2>
          <div className="chips">
            {(['todos', 'luna', 'marte'] as const).map((t) => (
              <button
                key={t}
                className={`chip ${target === t ? 'active' : ''}`}
                onClick={() => setTarget(t)}
              >
                {t === 'todos' ? 'Todos' : TARGET_LABELS[t]}
              </button>
            ))}
          </div>
        </section>

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
          <input
            type="checkbox"
            checked={onlyLesserKnown}
            onChange={(e) => setOnlyLesserKnown(e.target.checked)}
          />
          Solo análogos poco estudiados
        </label>

        <div className="results-header">
          <span>
            {filtered.length} de {SITES.length} sitios
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
                  <span className="dot" style={{ background: siteColor(s) }} />
                  <span>
                    <strong>{s.name}</strong>
                    <small>
                      {s.country} · {s.analogOf}
                    </small>
                  </span>
                </button>
              </li>
            ))}
            {filtered.length === 0 && <li className="empty">Ningún sitio cumple estos filtros.</li>}
          </ul>
        )}

        <footer className="note">
          Similitudes preliminares (cualitativas). Se reemplazarán por puntajes calculados con datos de NASA,
          ESA, JAXA y CSA.
        </footer>
      </aside>

      <main className="map-area">
        {API_KEY ? (
          <APIProvider apiKey={API_KEY} language="es">
            <Map
              mapId={MAP_ID}
              defaultCenter={{ lat: 15, lng: -20 }}
              defaultZoom={2}
              mapTypeId="hybrid"
              gestureHandling="greedy"
              disableDefaultUI={false}
            >
              {filtered.map((s) => (
                <AdvancedMarker
                  key={s.id}
                  position={{ lat: s.lat, lng: s.lng }}
                  title={s.name}
                  onClick={() => setSelectedId(s.id)}
                >
                  <Pin
                    background={siteColor(s)}
                    borderColor="#1b1b1f"
                    glyphColor="#ffffff"
                    scale={s.id === selectedId ? 1.4 : 1}
                  />
                </AdvancedMarker>
              ))}
              {selected && (
                <InfoWindow
                  position={{ lat: selected.lat, lng: selected.lng }}
                  pixelOffset={[0, -40]}
                  onCloseClick={() => setSelectedId(null)}
                  headerContent={<strong>{selected.name}</strong>}
                >
                  <div className="info">
                    <p>{selected.analogOf}</p>
                    <a href={googleEarthUrl(selected)} target="_blank" rel="noreferrer">
                      Ver en Google Earth ↗
                    </a>
                  </div>
                </InfoWindow>
              )}
            </Map>
          </APIProvider>
        ) : (
          <div className="missing-key">
            <h2>Falta la API key de Google Maps</h2>
            <p>
              Crea <code>web/.env.local</code> con:
            </p>
            <pre>VITE_GOOGLE_MAPS_API_KEY=tu_api_key</pre>
            <p>y reinicia <code>npm run dev</code>.</p>
          </div>
        )}
        <div className="legend">
          <span>
            <i style={{ background: TARGET_COLORS.luna }} /> Luna
          </span>
          <span>
            <i style={{ background: TARGET_COLORS.marte }} /> Marte
          </span>
          <span>
            <i style={{ background: TARGET_COLORS.ambos }} /> Ambos
          </span>
        </div>
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
        {site.country} · {site.lat.toFixed(2)}, {site.lng.toFixed(2)}
        {!site.wellKnown && <span className="badge">Poco estudiado</span>}
      </p>
      <p>
        <strong>Análogo de:</strong> {site.analogOf} ({site.targets.map((t) => TARGET_LABELS[t]).join(' y ')})
      </p>

      <h3>Similitud por dimensión</h3>
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
