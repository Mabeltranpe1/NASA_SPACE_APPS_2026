import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { SITES } from './data/sites'
import {
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
import ComparisonPanel, { type Place } from './components/ComparisonPanel'
import { loadHeatmap, useComparisons, type Characterization, type Heatmap } from './data/comparisons'
import { BODY_COLORS, SIMILARITY_COLOR } from './theme'
import GuidedTour from './components/GuidedTour'
import type { TourStep } from './data/tour'
import { BASE_LAYERS, OVERLAY_LAYERS, type BaseLayerId, type OverlayLayerId } from './map/gibs'
import { localizeSite } from './data/sites.en'
import { useLang } from './i18n/useLang'
import { BODY_NAMES, DIMENSION_NAMES, ENVIRONMENT_NAMES, MODE_NAMES } from './i18n/strings'
import './App.css'

type Mode = 'tierra-luna' | 'tierra-marte' | 'luna-marte'

const MODES: Record<Mode, { left: Body; right: Body; requires: Target[] }> = {
  'tierra-luna': { left: 'tierra', right: 'luna', requires: ['luna'] },
  'tierra-marte': { left: 'tierra', right: 'marte', requires: ['marte'] },
  'luna-marte': { left: 'luna', right: 'marte', requires: ['luna', 'marte'] },
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
  const { lang, setLang, t } = useLang()
  const sites = useMemo(() => SITES.map((s) => localizeSite(s, lang)), [lang])
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
      sites.filter((s) => {
        const targets = siteTargets(s)
        if (!requires.every((t) => targets.includes(t))) return false
        if (environments.length && !environments.some((e) => s.environments.includes(e))) return false
        if (dimensions.length && !dimensions.every((d) => s.dimensions[d] === 'alta' || s.dimensions[d] === 'media'))
          return false
        if (onlyLesserKnown && s.wellKnown) return false
        return true
      }),
    [sites, requires, environments, dimensions, onlyLesserKnown],
  )

  const selected = filtered.find((s) => s.id === selectedId) ?? null

  // Similarity map on the Earth globe for one Moon/Mars target.
  const [mapTarget, setMapTarget] = useState<{ id: string; name: string; body: Target } | null>(null)
  const [heat, setHeat] = useState<Heatmap | null>(null)
  useEffect(() => {
    if (!mapTarget) return
    let alive = true
    loadHeatmap(mapTarget.id)
      .then((h) => alive && setHeat(h))
      .catch(() => alive && setHeat(null))
    return () => {
      alive = false
    }
  }, [mapTarget])
  const visibleMap = mapTarget && requires.includes(mapTarget.body) ? mapTarget : null
  const heatCells = visibleMap && heat?.target === visibleMap.id ? heat.cells : null

  // A place the Earth globe flies to: from a site's ranking (siteId = that site,
  // valid while it stays selected) or from the discoveries list (siteId = null).
  // `other` = the Moon/Mars site of a discovery, so the second globe flies there too.
  const [place, setPlace] = useState<(Place & { siteId: string | null; other?: Place & { body: Target } }) | null>(null)
  const earthPlace = place && place.siteId === (selected?.id ?? null) ? place : null

  // Discoveries of the global search for the body shown next to the Earth.
  const comparisons = useComparisons()
  const discoveryBody: Target | null = left === 'tierra' && right !== 'tierra' ? right : null
  const discoveries = useMemo(() => {
    if (comparisons.status !== 'ready' || !discoveryBody) return []
    const { data } = comparisons
    const targets = new Map(data.targets.filter((tg) => tg.body === discoveryBody).map((tg) => [tg.id, tg]))
    const best = new Map<string, { site: (typeof data.sites)[number]; target: (typeof data.targets)[number]; score: number }>()
    for (const site of data.sites) {
      if (site.kind !== 'discovery' || !site.region) continue
      for (const r of site.results) {
        const target = targets.get(r.target)
        if (!target || r.score == null) continue
        const prev = best.get(site.region)
        if (!prev || r.score > prev.score) best.set(site.region, { site, target, score: r.score })
      }
    }
    return [...best.values()].sort((a, b) => b.score - a.score).slice(0, 8)
  }, [comparisons, discoveryBody])
  const showDiscovery = (d: (typeof discoveries)[number]) => {
    setSelectedId(null)
    const other =
      d.target.lat != null && d.target.lng != null
        ? { lat: d.target.lat, lng: d.target.lng, name: d.target.name, body: d.target.body }
        : undefined
    setPlace({ lat: d.site.lat, lng: d.site.lng, name: d.site.name, siteId: null, other })
    setMapTarget({ id: d.target.id, name: d.target.name, body: d.target.body })
  }
  const mainSites = filtered.filter((s) => !s.caseStudy)
  const caseStudies = filtered.filter((s) => s.caseStudy)
  const renderSite = (s: AnalogSite) => (
    <li key={s.id}>
      <button onClick={() => setSelectedId(s.id)}>
        <span className="dot" style={{ background: BODY_COLORS.tierra }} />
        <span>
          <strong>
            {s.name}
            {s.caseStudy ? (
              <span className="badge case">{t('badge.caseStudy')}</span>
            ) : (
              !s.wellKnown && <span className="badge">{t('badge.lesserKnown')}</span>
            )}
          </strong>
          <small>
            {s.country} → {s.homologues.map((h) => h.name).join(' · ')}
          </small>
        </span>
      </button>
    </li>
  )

  const markersOn = useCallback(
    (body: Body) => {
      const list = markersFor(filtered, body)
      if (body === 'tierra' && earthPlace)
        list.push({ id: `place-${earthPlace.lat}-${earthPlace.lng}`, lat: earthPlace.lat, lng: earthPlace.lng, color: '#ffffff', label: earthPlace.name })
      const other = earthPlace?.other
      if (other && other.body === body)
        list.push({ id: `place-${other.lat}-${other.lng}`, lat: other.lat, lng: other.lng, color: '#ffffff', label: other.name })
      return list
    },
    [filtered, earthPlace],
  )
  const focusOn = useCallback(
    (body: Body) => {
      if (body === 'tierra' && earthPlace) return earthPlace
      if (earthPlace?.other && earthPlace.other.body === body) return earthPlace.other
      return selected ? locationOn(selected, body) : null
    },
    [selected, earthPlace],
  )
  const leftMarkers = useMemo(() => markersOn(left), [markersOn, left])
  const rightMarkers = useMemo(() => markersOn(right), [markersOn, right])
  const leftFocus = useMemo(() => focusOn(left), [focusOn, left])
  const rightFocus = useMemo(() => focusOn(right), [focusOn, right])

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
  const closeTour = useCallback(() => setTouring(false), [setTouring])

  return (
    <div className="app">
      <aside className="sidebar">
        <header className="brand">
          <div className="brand-top">
            <p className="eyebrow">{t('brand.eyebrow')}</p>
            <div className="lang-switch" role="group" aria-label={t('lang.label')}>
              {(['es', 'en'] as const).map((l) => (
                <button key={l} className={lang === l ? 'active' : ''} aria-pressed={lang === l} onClick={() => setLang(l)}>
                  {l.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          <h1>{t('brand.title')}</h1>
          <p className="subtitle">{t('brand.subtitle')}</p>
        </header>

        <section className="filter-group">
          <h2>{t('filters.environment')}</h2>
          <div className="chips">
            {(Object.keys(ENVIRONMENT_LABELS) as Environment[]).map((e) => (
              <button
                key={e}
                className={`chip ${environments.includes(e) ? 'active' : ''}`}
                onClick={() => setEnvironments((prev) => toggle(prev, e))}
              >
                {ENVIRONMENT_NAMES[lang][e]}
              </button>
            ))}
          </div>
        </section>

        <section className="filter-group">
          <h2>{t('filters.dimension')}</h2>
          <div className="chips">
            {(Object.keys(DIMENSION_LABELS) as Dimension[]).map((d) => (
              <button
                key={d}
                className={`chip ${dimensions.includes(d) ? 'active' : ''}`}
                onClick={() => setDimensions((prev) => toggle(prev, d))}
              >
                {DIMENSION_NAMES[lang][d]}
              </button>
            ))}
          </div>
        </section>

        <label className="checkbox">
          <input type="checkbox" checked={onlyLesserKnown} onChange={(e) => setOnlyLesserKnown(e.target.checked)} />
          {t('filters.lesserKnown')}
        </label>

        <div className="results-header">
          <span>{t('results.count', { n: filtered.length, mode: MODE_NAMES[lang][mode] })}</span>
          <button className="link" onClick={resetFilters}>
            {t('filters.reset')}
          </button>
        </div>

        {selected ? (
          <SiteDetail site={selected} onClose={() => setSelectedId(null)} />
        ) : (
          <>
            {discoveries.length > 0 && discoveryBody && (
              <section className="side-section">
                <h2>{t('side.discoveries')}</h2>
                <p className="hint">{t('side.discoveriesHint', { body: BODY_NAMES[lang][discoveryBody] })}</p>
                <ul className="site-list">
                  {discoveries.map((d) => {
                    const active = earthPlace?.lat === d.site.lat && earthPlace?.lng === d.site.lng
                    return (
                      <li key={d.site.region}>
                        <button
                          className={active ? 'active' : ''}
                          aria-pressed={active}
                          title={d.site.note ?? undefined}
                          onClick={() => showDiscovery(d)}
                        >
                          <span className="dot" style={{ background: SIMILARITY_COLOR }} />
                          <span>
                            <strong>{d.site.name}</strong>
                            <small>
                              {t('side.discoveryFor', { score: Math.round(d.score * 100), target: d.target.name })}
                            </small>
                          </span>
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </section>
            )}
            <section className="side-section">
              <h2>{t('side.catalog')}</h2>
              <ul className="site-list">
                {mainSites.map(renderSite)}
                {filtered.length === 0 && <li className="empty">{t('results.empty')}</li>}
              </ul>
            </section>
            {caseStudies.length > 0 && (
              <section className="side-section">
                <h2>{t('side.caseStudy')}</h2>
                <p className="hint">{t('side.caseStudyHint')}</p>
                <ul className="site-list">{caseStudies.map(renderSite)}</ul>
              </section>
            )}
          </>
        )}

        <footer className="note">{t('footer.note')}</footer>
      </aside>

      <main className="main" ref={mainRef}>
        <div className="topbar">
          <button className="tour-button" onClick={() => setTouring(true)} disabled={touring}>
            {t('tour.button')}
          </button>
          <div className="mode-switch" role="tablist" aria-label={t('mode.aria')}>
            {(Object.keys(MODES) as Mode[]).map((m) => (
              <button key={m} role="tab" aria-selected={mode === m} className={mode === m ? 'active' : ''} onClick={() => setMode(m)}>
                {MODE_NAMES[lang][m]}
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
                {BODY_NAMES[lang][body]}
              </div>
              <PlanetGlobe
                body={body}
                markers={i === 0 ? leftMarkers : rightMarkers}
                selectedId={selected?.id ?? null}
                focus={i === 0 ? leftFocus : rightFocus}
                onSelect={(id) => (id.startsWith('place-') ? undefined : setSelectedId(id))}
                earthBase={baseLayer}
                earthOverlays={overlays}
                heat={body === 'tierra' ? heatCells : null}
                heatColor={SIMILARITY_COLOR}
              />
              {body === 'tierra' && visibleMap && heatCells && (
                <div className="heat-legend" role="note">
                  <strong>{t('heat.legend', { target: visibleMap.name })}</strong>
                  <span className="heat-scale">
                    <span>{t('heat.low')}</span>
                    <span className="heat-bar" style={{ background: `linear-gradient(90deg, ${SIMILARITY_COLOR}33, ${SIMILARITY_COLOR})` }} />
                    <span>{t('heat.high')}</span>
                  </span>
                  <small>{t('heat.cells', { n: heatCells.length.toLocaleString(lang) })}</small>
                  <button className="link" onClick={() => setMapTarget(null)}>
                    {t('cmp.hideMap')}
                  </button>
                </div>
              )}
              {body === 'tierra' && (
                <details className="layer-panel">
                  <summary>{t('layers.title')}</summary>
                  {BASE_LAYERS.map((l) => (
                    <label key={l.id} title={lang === 'en' ? l.descriptionEn : l.description}>
                      <input type="radio" name="base-layer" checked={baseLayer === l.id} onChange={() => setBaseLayer(l.id)} />
                      {lang === 'en' ? l.labelEn : l.label}
                    </label>
                  ))}
                  {OVERLAY_LAYERS.map((l) => (
                    <label key={l.id} title={lang === 'en' ? l.descriptionEn : l.description}>
                      <input
                        type="checkbox"
                        checked={overlays.includes(l.id)}
                        onChange={() => setOverlays((prev) => toggle(prev, l.id))}
                      />
                      {lang === 'en' ? l.labelEn : l.label}
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
            <div className="details-empty">{t('details.empty')}</div>
          )}
        </section>

        {selected &&
          requires.map((body) => (
            <ComparisonPanel
              key={`${selected.id}-${body}`}
              site={selected}
              body={body}
              mapTargetId={visibleMap?.id ?? null}
              onShowMap={(target) => setMapTarget(target ? { ...target, body } : null)}
              onGoTo={(p) => {
                setPlace({ ...p, siteId: selected.id })
                mainRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
              }}
            />
          ))}
        {touring && <GuidedTour onApply={applyTourStep} onClose={closeTour} />}
      </main>
    </div>
  )
}

function SiteDetail({ site, onClose }: { site: AnalogSite; onClose: () => void }) {
  const { lang, t } = useLang()
  return (
    <article className="detail">
      <button className="link" onClick={onClose}>
        {t('detail.back')}
      </button>
      <h2>{site.name}</h2>
      <p className="meta">
        {site.country} · {site.lat.toFixed(2)}°, {site.lng.toFixed(2)}°
        {!site.wellKnown && <span className="badge">{t('badge.lesserKnown')}</span>}
      </p>

      <h3>{t('detail.homologues')}</h3>
      <ul className="homologues">
        {site.homologues.map((h) => (
          <li key={h.body}>
            <span className="dot" style={{ background: BODY_COLORS[h.body] }} />
            <span>
              <strong>
                {BODY_NAMES[lang][h.body]}: {h.name}
              </strong>
              <small>
                {h.note}
                {h.approximate && t('detail.approximate')}
              </small>
            </span>
          </li>
        ))}
      </ul>

      <SiteCharacterization siteId={site.id} />

      <h3>{t('detail.dimensions')}</h3>
      <ul className="dims">
        {(Object.keys(DIMENSION_LABELS) as Dimension[])
          .filter((d) => site.dimensions[d])
          .map((d) => (
            <li key={d}>
              <span>{DIMENSION_NAMES[lang][d]}</span>
              <span className={`level ${site.dimensions[d]}`}>{t(`level.${site.dimensions[d]}` as 'level.alta')}</span>
            </li>
          ))}
      </ul>

      <h3>{t('detail.similarities')}</h3>
      <p>{site.similarities}</p>
      <h3>{t('detail.limitations')}</h3>
      <p>{site.limitations}</p>
      <h3>{t('detail.missionUse')}</h3>
      <p>{site.missionUse}</p>

      <a className="earth-button" href={googleEarthUrl(site)} target="_blank" rel="noreferrer">
        {t('detail.googleEarth')}
      </a>
    </article>
  )
}

/** Santiago's detailed 10 x 10 km characterization, when the site has one. */
function SiteCharacterization({ siteId }: { siteId: string }) {
  const state = useComparisons()
  const { lang, t } = useLang()
  if (state.status !== 'ready') return null
  const c: Characterization | undefined = state.data.sites.find((s) => s.id === siteId)?.characterization
  if (!c) return null
  const n = (v: number | string | null | undefined, unit = '', digits = 1) =>
    typeof v === 'number' ? `${v.toLocaleString(lang, { maximumFractionDigits: digits })}${unit}` : '—'
  const rows: [string, string][] = []
  if (c.topography) {
    rows.push([t('char.slope'), n(c.topography.slope_mean_deg, '°')])
    rows.push([t('char.relief'), n(c.topography.relief_p90_p10_m, ' m', 0)])
    rows.push([t('char.flat'), n(c.topography.flat_terrain_pct, ' %', 0)])
  }
  const env: [string, string][] = c.environment
    ? [
        [t('char.lstDay'), n(c.environment.lst_day_mean_K, ' K', 0)],
        [t('char.lstNight'), n(c.environment.lst_night_mean_K, ' K', 0)],
        [t('char.rain'), n(c.environment.annual_precipitation_mm, ' mm', 0)],
        [t('char.ndvi'), n(c.environment.ndvi_mean, '', 2)],
        [t('char.bare'), n(c.environment.bare_ground_pct, ' %', 0)],
      ]
    : []
  const spec: [string, string][] = c.spectral
    ? [
        [t('char.iron'), n(c.spectral.iron_oxide_ratio, '', 2)],
        [t('char.hydroxyl'), n(c.spectral.hydroxyl_ratio, '', 2)],
      ]
    : []
  const block = (title: string, list: [string, string][]) =>
    list.length > 0 && (
      <>
        <h4>{title}</h4>
        <dl className="char-list">
          {list.map(([k, v]) => (
            <div key={k}>
              <dt>{k}</dt>
              <dd>{v}</dd>
            </div>
          ))}
        </dl>
      </>
    )
  return (
    <section className="characterization">
      <h3>{t('char.title')}</h3>
      <p className="hint">{t('char.note')}</p>
      {c.quality_flags?.map((f) => (
        <p key={f} className="tag bad">
          ⚠ {f}
        </p>
      ))}
      {block(t('char.topography'), rows)}
      {block(t('char.environment'), env)}
      {block(t('char.spectral'), spec)}
      {c.topographic_index && c.topographic_index.length > 0 && (
        <>
          <h4>{t('char.pai')}</h4>
          <dl className="char-list">
            {c.topographic_index.map((p) => (
              <div key={p.target}>
                <dt>
                  {BODY_NAMES[lang][p.body]}: {p.target}
                </dt>
                <dd>{n(p.pai, ' / 100', 0)}</dd>
              </div>
            ))}
          </dl>
        </>
      )}
      {c.mineralogy && <p className="hint">{t('char.mineralogy', { n: c.mineralogy.emit_granules })}</p>}
    </section>
  )
}
