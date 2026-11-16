import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { SITES } from './data/sites'
import {
  ENVIRONMENT_LABELS,
  homologueFor,
  siteTargets,
  type AnalogSite,
  type Body,
  type Environment,
  type Target,
} from './data/types'
import PlanetGlobe, { type GlobeMarker } from './components/PlanetGlobe'
import { EarthCarousel, TargetCarousel } from './components/PlaceCarousels'
import ComparisonPanel, { type Place } from './components/ComparisonPanel'
import InsightPanel from './components/InsightPanel'
import SiteCard from './components/SiteCard'
import EarthThumb from './components/EarthThumb'
import MethodView from './components/MethodView'
import IntroOverlay from './components/IntroOverlay'
import GuidedTour from './components/GuidedTour'
import {
  IconBook,
  IconChart,
  IconCompass,
  IconFilter,
  IconLayers,
  IconLock,
  IconPin,
  IconPlay,
  IconSearch,
  LogoMark,
} from './components/Icons'
import { loadHeatmap, useComparisons, type ComparisonData, type Heatmap, type RankingId } from './data/comparisons'
import { bestScore, bodiesOf, discoveriesFor, discoveryAsSite, placeCountry, placeName, type Discovery } from './data/focus'
import DiscoverList, { type DiscoverItem } from './components/DiscoverList'
import { formatCoords } from './data/format'
import { DEMO_STEPS, type TourStep } from './data/tour'
import { BODY_COLORS, SIMILARITY_COLOR } from './theme'
import { BASE_LAYERS, OVERLAY_LAYERS, type BaseLayerId, type OverlayLayerId } from './map/gibs'
import { localizeSite } from './data/sites.en'
import { useLang } from './i18n/useLang'
import { BODY_NAMES, ENVIRONMENT_NAMES } from './i18n/strings'
import './App.css'

type View = 'discover' | 'sites' | 'analysis' | 'finder' | 'method'

// "Find analogs": loaded only when opened (it brings its own ~7 MB Earth database).
const AnalogFinder = lazy(() => import('./components/AnalogFinder'))
type GlobeView = 'discover' | 'sites'

const BODY_ORDER: Body[] = ['tierra', 'luna', 'marte']
const INTRO_KEY = 'analogs.introSeen'

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value]
}

function readStorage(key: string) {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

function writeStorage(key: string, value: string) {
  try {
    window.localStorage.setItem(key, value)
  } catch {
    /* storage can be blocked */
  }
}

function readParams() {
  try {
    return new URLSearchParams(window.location.search)
  } catch {
    return new URLSearchParams()
  }
}

/** Location of a place on a given body: the place itself on Earth, its counterpart elsewhere. */
function locationOn(site: AnalogSite, body: Body) {
  if (body === 'tierra') return { lat: site.lat, lng: site.lng, name: site.name }
  const h = homologueFor(site, body)
  return h ? { lat: h.lat, lng: h.lng, name: h.name } : null
}

function normalize(text: string) {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
}

/** Best Earth cell found by the global search for one Moon/Mars target. */
function bestDiscoveryForTarget(data: ComparisonData, targetId: string): Discovery | null {
  const target = data.targets.find((tg) => tg.id === targetId)
  if (!target) return null
  let best: Discovery | null = null
  for (const site of data.sites) {
    if (site.kind !== 'discovery') continue
    const r = site.results.find((x) => x.target === targetId)
    if (r?.score != null && (!best || r.score > best.score)) best = { site, target, score: r.score }
  }
  return best
}

export default function App() {
  const { lang, setLang, t } = useLang()
  const sites = useMemo(() => SITES.map((s) => localizeSite(s, lang)), [lang])
  const comparisons = useComparisons()
  const data = comparisons.status === 'ready' ? comparisons.data : null

  // ---------- Navigation and selection ----------
  const [initial] = useState(readParams)
  const initialSite = initial.get('site')
  const startsOnSite = !!initialSite && SITES.some((s) => s.id === initialSite)
  const [view, setView] = useState<View>(() => {
    const v = initial.get('view')
    if (window.location.hash.startsWith('#buscar')) return 'finder'
    if (v === 'analysis' || v === 'finder' || v === 'method' || v === 'sites' || v === 'discover') return v
    return startsOnSite ? 'sites' : 'discover'
  })
  const [globeView, setGlobeView] = useState<GlobeView>(startsOnSite ? 'sites' : 'discover')
  const [activeBody, setActiveBody] = useState<Body>('tierra')
  const [lastTarget, setLastTarget] = useState<Target | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(startsOnSite ? initialSite : null)
  const [discoveryKey, setDiscoveryKey] = useState<{ siteId: string; targetId: string } | null>(null)
  const [discoverBody, setDiscoverBody] = useState<Target>('marte')
  const [discoverList, setDiscoverList] = useState<RankingId>('general')
  const [discoverCountry, setDiscoverCountry] = useState('')
  const [sortList, setSortList] = useState<RankingId>('general')
  const [place, setPlace] = useState<Place | null>(null)
  // Video mode (?demo=1): the ~30 s tour starts by itself, without the welcome screen.
  const [demo, setDemo] = useState(() => initial.get('demo') === '1')
  const [showIntro, setShowIntro] = useState(() => readStorage(INTRO_KEY) !== '1' && !startsOnSite && initial.get('demo') !== '1')
  const [touring, setTouring] = useState(() => initial.get('demo') === '1')
  const [galleryOpen, setGalleryOpen] = useState(false)
  const [demoRun, setDemoRun] = useState(0)

  // "D" starts (or restarts) the ~30 s video mode: open the app, let the globe load,
  // start recording and press D.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null
      if (e.key.toLowerCase() !== 'd' || e.ctrlKey || e.metaKey || e.altKey) return
      if (target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) return
      setShowIntro(false)
      setDemo(true)
      setTouring(true)
      setDemoRun((n) => n + 1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
  const [mapTarget, setMapTarget] = useState<{ id: string; name: string; body: Target } | null>(null)
  const [heat, setHeat] = useState<Heatmap | null>(null)

  // ---------- Filters (reference analogs) ----------
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [onlyLesserKnown, setOnlyLesserKnown] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const filterCount = environments.length + (onlyLesserKnown ? 1 : 0)
  const resetFilters = () => {
    setEnvironments([])
    setOnlyLesserKnown(false)
  }
  const filtered = useMemo(
    () =>
      sites.filter((s) => {
        if (environments.length && !environments.some((e) => s.environments.includes(e))) return false
        if (onlyLesserKnown && s.wellKnown) return false
        return true
      }),
    [sites, environments, onlyLesserKnown],
  )

  // ---------- Earth layers ----------
  const [baseLayer, setBaseLayer] = useState<BaseLayerId>('bluemarble')
  const [overlays, setOverlays] = useState<OverlayLayerId[]>([])
  const [showLayers, setShowLayers] = useState(false)

  // ---------- Focus: the selected place of the current globe view ----------
  // Ranked places of the worldwide search: the chosen list, then the country filter.
  const fullList = useMemo(
    () => (data ? discoveriesFor(data, discoverBody, Infinity, discoverList) : []),
    [data, discoverBody, discoverList],
  )
  const countries = useMemo(() => {
    const count = new Map<string, number>()
    for (const d of fullList) {
      const c = placeCountry(d.site, lang)
      if (c) count.set(c, (count.get(c) ?? 0) + 1)
    }
    return [...count].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], lang))
  }, [fullList, lang])
  const discoverItems = useMemo<DiscoverItem[]>(
    () =>
      fullList
        .map((d, i) => ({ d, rank: i + 1 }))
        .filter(({ d }) => !discoverCountry || placeCountry(d.site, lang) === discoverCountry),
    [fullList, discoverCountry, lang],
  )
  const discoveries = useMemo(() => discoverItems.map((x) => x.d), [discoverItems])
  const discovery = useMemo<Discovery | null>(() => {
    if (!data || !discoveryKey) return null
    const site = data.sites.find((s) => s.id === discoveryKey.siteId)
    const target = data.targets.find((tg) => tg.id === discoveryKey.targetId)
    const score = site?.results.find((r) => r.target === discoveryKey.targetId)?.score
    return site && target ? { site, target, score: score ?? 0 } : null
  }, [data, discoveryKey])
  const discoverySite = useMemo(() => (discovery ? discoveryAsSite(discovery, lang) : null), [discovery, lang])
  const selectedSite = useMemo(() => sites.find((s) => s.id === selectedId) ?? null, [sites, selectedId])

  const focusKind: GlobeView = view === 'discover' || view === 'sites' ? view : globeView
  const focus = focusKind === 'discover' ? discoverySite : selectedSite
  const allowed = bodiesOf(focus)
  const shownBody: Body = allowed.includes(activeBody) ? activeBody : 'tierra'
  const focusTargets = focus ? siteTargets(focus) : []
  const compareBody: Target | null =
    shownBody !== 'tierra'
      ? shownBody
      : lastTarget && focusTargets.includes(lastTarget)
        ? lastTarget
        : (focusTargets[0] ?? null)

  const chooseBody = useCallback((body: Body) => {
    setActiveBody(body)
    if (body !== 'tierra') setLastTarget(body)
  }, [])

  const keepBodyFor = (site: AnalogSite) => setActiveBody((prev) => (bodiesOf(site).includes(prev) ? prev : 'tierra'))

  const selectSite = (site: AnalogSite, stay = false) => {
    setSelectedId(site.id)
    setPlace(null)
    keepBodyFor(site)
    setGlobeView('sites')
    if (!stay) setView('sites')
  }
  const selectDiscovery = (d: Discovery, stay = false) => {
    setDiscoveryKey({ siteId: d.site.id, targetId: d.target.id })
    if (d.target.body !== discoverBody) {
      setDiscoverBody(d.target.body)
      setDiscoverCountry('')
    }
    setPlace(null)
    keepBodyFor(discoveryAsSite(d, lang))
    setMapTarget({ id: d.target.id, name: d.target.name, body: d.target.body })
    setGlobeView('discover')
    if (!stay) setView('discover')
  }
  const clearFocus = () => {
    if (focusKind === 'discover') setDiscoveryKey(null)
    else setSelectedId(null)
    setPlace(null)
  }
  const goView = (v: View) => {
    setView(v)
    if (v === 'discover' || v === 'sites') setGlobeView(v)
  }

  // Shareable link: ?view=…&site=…
  useEffect(() => {
    try {
      const url = new URL(window.location.href)
      url.searchParams.set('view', view)
      if (selectedSite && focusKind === 'sites') url.searchParams.set('site', selectedSite.id)
      else url.searchParams.delete('site')
      window.history.replaceState(null, '', url)
    } catch {
      /* ignore */
    }
  }, [view, selectedSite, focusKind])

  // ---------- Similarity map on the Earth globe ----------
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
  const heatCells = shownBody === 'tierra' && mapTarget && heat?.target === mapTarget.id ? heat.cells : null

  // ---------- Globe markers and camera ----------
  const { markers, highlightId } = useMemo(() => {
    const list: GlobeMarker[] = []
    if (focusKind === 'discover') {
      if (shownBody === 'tierra') {
        for (const d of discoveries)
          list.push({ id: `disc:${d.site.id}:${d.target.id}`, lat: d.site.lat, lng: d.site.lng, color: SIMILARITY_COLOR, label: placeName(d.site, lang) })
      } else if (data) {
        for (const tg of data.targets)
          if (tg.body === shownBody && tg.lat != null && tg.lng != null)
            list.push({ id: `target:${tg.id}`, lat: tg.lat, lng: tg.lng, color: BODY_COLORS[shownBody], label: tg.name })
      }
    } else {
      const seen = new Set<string>()
      for (const s of filtered) {
        const loc = locationOn(s, shownBody)
        if (!loc) continue
        const key = `${loc.lat},${loc.lng}`
        if (seen.has(key)) continue // several Earth sites can share a counterpart
        seen.add(key)
        list.push({ id: s.id, lat: loc.lat, lng: loc.lng, color: BODY_COLORS[shownBody], label: loc.name })
      }
    }
    let highlight: string | null = null
    const loc = focus ? locationOn(focus, shownBody) : null
    if (loc) {
      highlight = list.find((m) => m.lat === loc.lat && m.lng === loc.lng)?.id ?? null
      if (!highlight) {
        list.push({ id: 'focus', lat: loc.lat, lng: loc.lng, color: '#ffffff', label: loc.name })
        highlight = 'focus'
      }
    }
    if (place && shownBody === 'tierra') list.push({ id: 'place', lat: place.lat, lng: place.lng, color: '#ffffff', label: place.name })
    return { markers: list, highlightId: highlight }
  }, [focusKind, shownBody, discoveries, data, filtered, focus, place, lang])

  const cameraFocus = useMemo(() => {
    if (shownBody === 'tierra' && place) return place
    return focus ? locationOn(focus, shownBody) : null
  }, [shownBody, place, focus])

  const onMarker = (id: string) => {
    if (id === 'focus' || id === 'place') return
    if (id.startsWith('disc:')) {
      const d = discoveries.find((x) => `disc:${x.site.id}:${x.target.id}` === id)
      if (d) selectDiscovery(d)
      return
    }
    if (id.startsWith('target:')) {
      const d = data ? bestDiscoveryForTarget(data, id.slice(7)) : null
      if (d) selectDiscovery(d)
      return
    }
    const s = sites.find((x) => x.id === id)
    if (s) selectSite(s)
  }

  // ---------- Guided tour ----------
  const tourTimer = useRef<number | undefined>(undefined)
  const pageRef = useRef<HTMLDivElement>(null)
  const applyTourStep = (step: TourStep) => {
    window.clearTimeout(tourTimer.current)
    setShowIntro(false)
    resetFilters()
    setGalleryOpen(false)
    if (step.discoverBody) setDiscoverBody(step.discoverBody)
    if (step.list) setDiscoverList(step.list)
    if (step.finderSite)
      window.location.hash = `#buscar?site=${step.finderSite}${step.finderMission ? `&mission=${step.finderMission}` : ''}`
    if (step.discovery && data) {
      const d = discoveriesFor(data, step.discovery, 1)[0]
      setDiscoverList('general')
      setDiscoverCountry('')
      if (d) selectDiscovery(d, true)
    } else if (step.siteId) {
      const s = sites.find((x) => x.id === step.siteId)
      if (s) selectSite(s, true)
    } else {
      setSelectedId(null)
      setDiscoveryKey(null)
      setMapTarget(null)
    }
    setActiveBody('tierra')
    setView(step.view)
    if (step.view === 'discover' || step.view === 'sites') setGlobeView(step.view)
    pageRef.current?.scrollTo({ top: 0 })
    if (step.body !== 'tierra') {
      const body = step.body
      tourTimer.current = window.setTimeout(() => chooseBody(body), step.bodyDelay ?? 4500)
    } else if (step.gallery) {
      tourTimer.current = window.setTimeout(() => setGalleryOpen(true), 600)
    }
  }
  const closeTour = useCallback(() => {
    window.clearTimeout(tourTimer.current)
    setTouring(false)
    setDemo(false)
    setGalleryOpen(false)
  }, [])
  const closeIntro = useCallback(() => {
    setShowIntro(false)
    writeStorage(INTRO_KEY, '1')
  }, [])
  const startTour = () => {
    closeIntro()
    setTouring(true)
  }

  // ---------- Search ----------
  const searchItems = (() => {
    const items: { key: string; label: string; sub: string; color: string; pick: () => void }[] = []
    for (const s of sites)
      items.push({
        key: s.id,
        label: s.name,
        sub: `${s.country} · ${s.caseStudy ? t('search.case') : t('search.catalog')}`,
        color: BODY_COLORS.tierra,
        pick: () => selectSite(s),
      })
    if (data)
      for (const body of ['marte', 'luna'] as Target[])
        for (const d of discoveriesFor(data, body))
          items.push({
            key: `${body}-${d.site.id}`,
            label: placeName(d.site, lang),
            sub: `${[placeCountry(d.site, lang), d.site.grid ? formatCoords(d.site.lat, d.site.lng, lang) : ''].filter(Boolean).join(' · ')} · ${t('search.discovery', { body: BODY_NAMES[lang][body] })} · ${d.target.name}`,
            color: SIMILARITY_COLOR,
            pick: () => selectDiscovery(d),
          })
    return items
  })()

  // Most similar first, so the most compatible place is on top (no score yet: last).
  const scores = useMemo(
    () => new Map(data ? sites.map((s) => [s.id, bestScore(data, s, sortList)] as const) : []),
    [data, sites, sortList],
  )
  const byScore = (list: AnalogSite[]) =>
    [...list].sort((a, b) => (scores.get(b.id)?.score ?? -1) - (scores.get(a.id)?.score ?? -1))
  // Open a site from the lists already compared with the body of its score.
  const pickSite = (site: AnalogSite, stay = false) => {
    const best = scores.get(site.id)
    if (best) setLastTarget(best.body)
    selectSite(site, stay)
  }
  const mainSites = byScore(filtered.filter((s) => !s.caseStudy))
  const caseStudies = byScore(filtered.filter((s) => s.caseStudy))
  const onGlobe = view === 'discover' || view === 'sites'

  return (
    <div className="app">
      <nav className="rail" aria-label={t('nav.aria')}>
        <button className="rail-logo" onClick={() => setShowIntro(true)} title={t('nav.intro')} aria-label={t('nav.intro')}>
          <LogoMark />
        </button>
        {(
          [
            ['discover', IconCompass],
            ['sites', IconPin],
            ['analysis', IconChart],
            ['finder', IconSearch],
            ['method', IconBook],
          ] as const
        ).map(([v, Icon]) => (
          <button key={v} className={`rail-item ${view === v ? 'active' : ''}`} aria-current={view === v ? 'page' : undefined} onClick={() => goView(v)}>
            <Icon size={21} />
            <span>{t(`nav.${v}`)}</span>
          </button>
        ))}
      </nav>

      <div className="workspace">
        <header className="topbar">
          <div className="title-block">
            <p className="eyebrow">{t('brand.eyebrow')}</p>
            <h1>{t('brand.title')}</h1>
            <p className="subtitle">{t('brand.subtitle')}</p>
          </div>
          <div className="top-actions">
            <SearchBox items={searchItems} />
            <button className="btn primary tour-button" onClick={startTour} disabled={touring}>
              <IconPlay size={13} /> {t('tour.button').replace('▶ ', '')}
            </button>
            <div className="lang-switch" role="group" aria-label={t('lang.label')}>
              {(['es', 'en'] as const).map((l) => (
                <button key={l} className={lang === l ? 'active' : ''} aria-pressed={lang === l} onClick={() => setLang(l)}>
                  {l.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </header>

        {onGlobe && (
          <section className="stage">
            <PlanetGlobe
              body={shownBody}
              markers={markers}
              selectedId={highlightId}
              focus={cameraFocus}
              onSelect={onMarker}
              earthBase={baseLayer}
              earthOverlays={overlays}
              heat={heatCells}
              heatColor={SIMILARITY_COLOR}
              spin={!focus && !place}
            />
            <div className="vignette" aria-hidden="true" />

            <div className="body-switch-wrap">
              <div className="body-switch" role="group" aria-label={t('body.aria')}>
                {BODY_ORDER.map((b) => {
                  const locked = !allowed.includes(b)
                  const name = BODY_NAMES[lang][b]
                  return (
                    <button
                      key={b}
                      className={shownBody === b ? 'active' : ''}
                      style={{ ['--body' as string]: BODY_COLORS[b] }}
                      aria-pressed={shownBody === b}
                      disabled={locked}
                      title={locked ? t('body.locked', { body: name }) : undefined}
                      onClick={() => chooseBody(b)}
                    >
                      {locked ? <IconLock size={13} /> : <span className="dot" style={{ background: BODY_COLORS[b] }} />}
                      {name}
                    </button>
                  )
                })}
              </div>
              {focus && compareBody && (
                <p className="pair-title">
                  <span>{focus.name}</span>
                  <span className="vs">≈</span>
                  <span>{homologueFor(focus, compareBody)?.name}</span>
                </p>
              )}
            </div>

            <aside className="panel panel-left glass" key={focus ? `left-${focus.id}` : `left-list-${focusKind}`}>
              {focus ? (
                <SiteCard
                  site={focus}
                  discovery={focusKind === 'discover'}
                  onBack={clearFocus}
                  onBody={chooseBody}
                  compareBody={compareBody}
                />
              ) : focusKind === 'discover' ? (
                <>
                  <p className="eyebrow">{t('nav.discover')}</p>
                  <h2 className="panel-heading">{t('side.discoveries')}</h2>
                  {data ? (
                    <DiscoverList
                      data={data}
                      body={discoverBody}
                      onBody={(b) => {
                        setDiscoverBody(b)
                        setDiscoverCountry('')
                      }}
                      list={discoverList}
                      onList={setDiscoverList}
                      country={discoverCountry}
                      onCountry={setDiscoverCountry}
                      items={discoverItems}
                      countries={countries}
                      onPick={(d) => selectDiscovery(d)}
                    />
                  ) : (
                    <p className="hint">{t('cmp.loading')}</p>
                  )}
                  {data && (
                    <p className="muted small">
                      {t('disc.stats', {
                        cells: data.n_cells.toLocaleString(lang),
                        regions: data.n_regions ?? '—',
                        targets: data.targets.length,
                      })}
                    </p>
                  )}
                  <p className="muted small">{t('disc.control')}</p>
                </>
              ) : (
                <>
                  <div className="panel-head-row">
                    <div>
                      <p className="eyebrow">{t('nav.sites')}</p>
                      <h2 className="panel-heading">{t('side.catalog')}</h2>
                    </div>
                    <button
                      className={`icon-btn ${showFilters || filterCount ? 'on' : ''}`}
                      onClick={() => setShowFilters((v) => !v)}
                      aria-expanded={showFilters}
                      title={t('filters.environment')}
                    >
                      <IconFilter size={17} />
                      {filterCount > 0 && <span className="count">{filterCount}</span>}
                    </button>
                  </div>
                  {showFilters && (
                    <div className="filters">
                      <h3 className="panel-sub">{t('filters.environment')}</h3>
                      <div className="chips">
                        {(Object.keys(ENVIRONMENT_LABELS) as Environment[]).map((e) => (
                          <button key={e} className={`chip ${environments.includes(e) ? 'active' : ''}`} onClick={() => setEnvironments((p) => toggle(p, e))}>
                            {ENVIRONMENT_NAMES[lang][e]}
                          </button>
                        ))}
                      </div>
                      <label className="checkbox">
                        <input type="checkbox" checked={onlyLesserKnown} onChange={(e) => setOnlyLesserKnown(e.target.checked)} />
                        {t('filters.lesserKnown')}
                      </label>
                      {filterCount > 0 && (
                        <button className="link small" onClick={resetFilters}>
                          {t('filters.reset')}
                        </button>
                      )}
                    </div>
                  )}
                  {data && (
                    <>
                      <div className="chips list-chips" role="group" aria-label={t('side.sortBy')}>
                        <span className="muted small">{t('side.sortBy')}</span>
                        {(['general', ...(data.dimensions ?? []).map((d) => d.id)] as RankingId[]).map((id) => (
                          <button
                            key={id}
                            className={`chip ${sortList === id ? 'active' : ''}`}
                            aria-pressed={sortList === id}
                            onClick={() => setSortList(id)}
                          >
                            {id === 'general' ? t('disc.list.general') : data.dimensions?.find((d) => d.id === id)?.label[lang]}
                          </button>
                        ))}
                      </div>
                      <p className="hint">
                        {sortList === 'general'
                          ? t('side.sortedHint')
                          : t('side.sortedHintDim', { dim: data.dimensions?.find((d) => d.id === sortList)?.label[lang].toLowerCase() ?? '' })}
                      </p>
                    </>
                  )}
                  <SiteList items={mainSites} scores={scores} onPick={pickSite} />
                  {filtered.length === 0 && <p className="hint">{t('results.empty')}</p>}
                  {caseStudies.length > 0 && (
                    <>
                      <h2 className="panel-heading sm">{t('side.caseStudy')}</h2>
                      <p className="hint">{t('side.caseStudyHint')}</p>
                      <SiteList items={caseStudies} scores={scores} onPick={pickSite} />
                    </>
                  )}
                  <p className="muted small">{t('footer.note')}</p>
                </>
              )}
            </aside>

            {focus && (
              <InsightPanel
                key={`right-${focus.id}`}
                site={focus}
                activeBody={shownBody}
                compareBody={compareBody}
                onBody={chooseBody}
                onOpenAnalysis={() => goView('analysis')}
                mapTargetId={mapTarget?.id ?? null}
                onToggleMap={(target) => {
                  setMapTarget(target)
                  if (target) setActiveBody('tierra')
                }}
                onGoTo={(p) => {
                  setPlace(p)
                  setActiveBody('tierra')
                }}
                galleryOpen={galleryOpen}
                onGalleryClose={() => setGalleryOpen(false)}
              />
            )}

            {!focus && !touring && !heatCells && <p className="stage-hint">{t('stage.hint')}</p>}

            {heatCells && mapTarget && (
              <div className="heat-legend glass" role="note">
                <strong>{t('heat.legend', { target: mapTarget.name })}</strong>
                <span className="heat-scale">
                  <span>{t('heat.low')}</span>
                  <span className="heat-bar" style={{ background: `linear-gradient(90deg, ${SIMILARITY_COLOR}33, ${SIMILARITY_COLOR})` }} />
                  <span>{t('heat.high')}</span>
                </span>
                <small>{t('heat.cells', { n: heatCells.length.toLocaleString(lang) })}</small>
                <button className="link small" onClick={() => setMapTarget(null)}>
                  {t('cmp.hideMap')}
                </button>
              </div>
            )}

            {shownBody === 'tierra' && (
              <div className="layer-control">
                <button className={`icon-btn glass ${showLayers ? 'on' : ''}`} onClick={() => setShowLayers((v) => !v)} aria-expanded={showLayers} title={t('layers.title')}>
                  <IconLayers size={18} />
                </button>
                {showLayers && (
                  <div className="layer-panel glass">
                    <strong>{t('layers.title')}</strong>
                    {BASE_LAYERS.map((l) => (
                      <label key={l.id} title={lang === 'en' ? l.descriptionEn : l.description}>
                        <input type="radio" name="base-layer" checked={baseLayer === l.id} onChange={() => setBaseLayer(l.id)} />
                        {lang === 'en' ? l.labelEn : l.label}
                      </label>
                    ))}
                    {OVERLAY_LAYERS.map((l) => (
                      <label key={l.id} title={lang === 'en' ? l.descriptionEn : l.description}>
                        <input type="checkbox" checked={overlays.includes(l.id)} onChange={() => setOverlays((p) => toggle(p, l.id))} />
                        {lang === 'en' ? l.labelEn : l.label}
                      </label>
                    ))}
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {view === 'analysis' && (
          <div className="page analysis" ref={pageRef}>
            {focus ? (
              <>
                <header className="page-hero compact">
                  <button className="link" onClick={() => goView(globeView)}>
                    {t('analysis.back')}
                  </button>
                  <p className="eyebrow">{t('nav.analysis')}</p>
                  <h1 className="pair-heading">
                    <span>
                      <span className="dot" style={{ background: BODY_COLORS.tierra }} /> {focus.name}
                    </span>
                    {focus.homologues.map((h) => (
                      <span key={h.body}>
                        <span className="vs">≈</span>
                        <span className="dot" style={{ background: BODY_COLORS[h.body] }} /> {h.name}
                      </span>
                    ))}
                  </h1>
                </header>
                <h2 className="section-title">{t('analysis.images')}</h2>
                <section className="details" style={{ ['--cols' as string]: 1 + focus.homologues.length }}>
                  <EarthCarousel site={focus} />
                  {siteTargets(focus).map((body) => (
                    <TargetCarousel key={`${focus.id}-${body}`} site={focus} body={body} />
                  ))}
                </section>
                {siteTargets(focus).map((body) => (
                  <ComparisonPanel
                    key={`${focus.id}-${body}`}
                    site={focus}
                    body={body}
                    mapTargetId={mapTarget?.id ?? null}
                    onShowMap={(target) => {
                      setMapTarget(target ? { ...target, body } : null)
                      if (target) {
                        setActiveBody('tierra')
                        goView(globeView)
                      }
                    }}
                    onGoTo={(p) => {
                      setPlace(p)
                      setActiveBody('tierra')
                      goView(globeView)
                    }}
                  />
                ))}
              </>
            ) : (
              <>
                <header className="page-hero">
                  <p className="eyebrow">{t('nav.analysis')}</p>
                  <h1>{t('analysis.pick')}</h1>
                  <p className="page-lead">{t('analysis.pickHint')}</p>
                </header>
                {data && (
                  <>
                    <h2 className="section-title">{t('side.discoveries')}</h2>
                    <div className="pick-grid">
                      {(['marte', 'luna'] as Target[]).flatMap((b) =>
                        discoveriesFor(data, b, 4).map((d) => (
                          <button key={`${b}-${d.site.id}`} className="pick glass" onClick={() => selectDiscovery(d, true)}>
                            <span className="pick-score" style={{ color: SIMILARITY_COLOR }}>
                              {Math.round(d.score * 100)}
                            </span>
                            <span>
                              <strong>{placeName(d.site, lang)}</strong>
                              <small>
                                <span className="dot" style={{ background: BODY_COLORS[b] }} /> {d.target.name}
                              </small>
                            </span>
                          </button>
                        )),
                      )}
                    </div>
                  </>
                )}
                <h2 className="section-title">{t('side.catalog')}</h2>
                <div className="pick-grid">
                  {byScore(sites).map((s) => (
                    <button key={s.id} className="pick glass" onClick={() => pickSite(s, true)}>
                      <span className="pick-dots">
                        {s.homologues.map((h) => (
                          <span key={h.body} className="dot" style={{ background: BODY_COLORS[h.body] }} />
                        ))}
                      </span>
                      <span>
                        <strong>{s.name}</strong>
                        <small>{s.homologues.map((h) => h.name).join(' · ')}</small>
                      </span>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {view === 'finder' && (
          <div className="page finder-page">
            <Suspense fallback={<p className="hint">{t('cmp.loading')}</p>}>
              <AnalogFinder
                onShowOnGlobe={(p) => {
                  // Fly the Earth globe of the Discover view to the place and mark it.
                  setDiscoveryKey(null)
                  setActiveBody('tierra')
                  goView('discover')
                  setPlace(p)
                }}
              />
            </Suspense>
          </div>
        )}

        {view === 'method' && <MethodView />}
      </div>

      {showIntro && <IntroOverlay onTour={startTour} onClose={closeIntro} />}
      {touring && (
        <GuidedTour key={demoRun} onApply={applyTourStep} onClose={closeTour} steps={demo ? DEMO_STEPS : undefined} demo={demo} />
      )}
    </div>
  )
}

function SiteList({
  items,
  scores,
  onPick,
}: {
  items: AnalogSite[]
  scores: Map<string, { score: number; body: Target } | null>
  onPick: (s: AnalogSite) => void
}) {
  const { lang, t } = useLang()
  return (
    <ul className="site-list">
      {items.map((s) => {
        const best = scores.get(s.id)
        return (
          <li key={s.id}>
            <button onClick={() => onPick(s)}>
              <span className="site-thumb">
                <EarthThumb site={s} />
                <span className="site-dots">
                  {s.homologues.map((h) => (
                    <span key={h.body} className="dot" style={{ background: BODY_COLORS[h.body] }} />
                  ))}
                </span>
              </span>
              <span>
                <strong>{s.name}</strong>
                <small>
                  {s.country} → {s.homologues.map((h) => h.name).join(' · ')}
                </small>
                <small className={`studied ${s.wellKnown ? 'well' : 'little'}`}>
                  {s.wellKnown ? t('badge.wellKnown') : t('badge.lesserKnown')}
                </small>
              </span>
              {best && (
                <span
                  className="site-score"
                  style={{ ['--body' as string]: BODY_COLORS[best.body] }}
                  title={t('side.scoreTitle', { body: BODY_NAMES[lang][best.body] })}
                >
                  <b>{Math.round(best.score * 100)}</b>
                  <small>/100</small>
                </span>
              )}
            </button>
          </li>
        )
      })}
    </ul>
  )
}

function SearchBox({ items }: { items: { key: string; label: string; sub: string; color: string; pick: () => void }[] }) {
  const { t } = useLang()
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const q = normalize(query.trim())
  const results = q ? items.filter((i) => normalize(`${i.label} ${i.sub}`).includes(q)).slice(0, 8) : []
  const pick = (i: (typeof items)[number]) => {
    i.pick()
    setQuery('')
    setOpen(false)
  }
  return (
    <div className="search" onBlur={(e) => !e.currentTarget.contains(e.relatedTarget) && setOpen(false)}>
      <IconSearch size={16} />
      <input
        type="search"
        value={query}
        placeholder={t('search.placeholder')}
        aria-label={t('search.placeholder')}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && results[0]) pick(results[0])
          if (e.key === 'Escape') setOpen(false)
        }}
      />
      {open && q && (
        <ul className="search-results glass" role="listbox">
          {results.map((i) => (
            <li key={i.key}>
              <button role="option" aria-selected="false" onClick={() => pick(i)}>
                <span className="dot" style={{ background: i.color }} />
                <span>
                  <strong>{i.label}</strong>
                  <small>{i.sub}</small>
                </span>
              </button>
            </li>
          ))}
          {results.length === 0 && <li className="hint">{t('search.empty')}</li>}
        </ul>
      )}
    </div>
  )
}
