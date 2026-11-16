import { useEffect, useMemo, useState, type MouseEvent } from 'react'
import {
  findAnalogs,
  loadComparator,
  queryPoint,
  toGeoJSON,
  toKML,
  toWaypoints,
  type AnalogsResponse,
  type Body,
  type ComparatorDB,
  type PointResponse,
  type Values,
} from '../comparator/compare'
import {
  MISSION_IDS,
  missionAvailable,
  missionFits,
  missionReference,
  missionWeights,
  topMissions,
  type MissionFit,
  type MissionId,
} from '../comparator/missions'
import { useLang } from '../i18n/useLang'
import { MISSION_TEXT, MISSION_UI } from '../i18n/missions'
import { MissionIcon } from './MissionIcons'
import { useMissionData } from '../data/missionData'
import { BODY_NAMES, type Lang } from '../i18n/strings'
import { BODY_COLORS, SIMILARITY_COLOR } from '../theme'
import './AnalogFinder.css'

/**
 * "Find analogs": the user picks a Moon/Mars site or types the values of a place on another
 * planet, and gets the most similar places on Earth (same score as the rest of the app). Second tab:
 * an Earth point -> which Moon/Mars sites it resembles. Results download as GeoJSON/KML/waypoints.
 * Self-contained: it loads its own data (public/data/comparator, ~7 MB) only when opened.
 * Visual language = ComparisonPanel (.comparison, .card, .hero, .meter-list, .ranking, .chips).
 * Mission types (comparator/missions.ts) are weight presets: picking one re-ranks the places for that
 * kind of test, and every result shows the 2-3 missions it suits best ("suitable for").
 */

/** Readable region name ("Egipto · 24,1° N, 32,1° E"), like the rest of the app. */
function regionLabel(db: ComparatorDB, region: string, lang: Lang, lat?: number, lon?: number) {
  const info = db.meta.regions.find((r) => r.name === region)
  const name = info?.label?.[lang] ?? region.replaceAll('_', ' ')
  if (!info?.grid || lat == null || lon == null) return name
  const f = (v: number) => Math.abs(v).toLocaleString(lang, { maximumFractionDigits: 1 })
  return `${name} · ${f(lat)}° ${lat >= 0 ? 'N' : 'S'}, ${f(lon)}° ${lon >= 0 ? 'E' : lang === 'en' ? 'W' : 'O'}`
}

const TEXT = {
  es: {
    title: 'Buscar análogos en la Tierra',
    intro:
      'Elige un sitio de la Luna o de Marte, o escribe tus propios valores: el comparador busca los lugares más parecidos entre 691 mil lugares de 727 regiones de la Tierra. Es el mismo puntaje que el resto de la app.',
    tabSite: 'Lugar en otro planeta',
    tabPoint: 'Punto en la Tierra',
    loading: 'Cargando la base de datos de la Tierra (unos 7 MB, solo la primera vez)…',
    loadError: 'No se pudo cargar la base de datos del comparador.',
    start: 'Sitio de partida',
    custom: 'Valores propios',
    body: 'Cuerpo',
    values: 'Datos del lugar',
    emptyHint: 'vacío = no se compara',
    range: 'Tierra: {min} a {max}',
    options: 'Opciones y pesos (qué importa más)',
    top: 'Resultados',
    perRegion: 'Uno por región',
    includeKnown: 'Incluir análogos famosos',
    minKm: 'Separación mínima (km)',
    resetWeights: 'Restaurar pesos del modelo',
    search: 'Buscar análogos',
    reset: 'Restablecer',
    outOfRange: 'La Tierra no llega a estos valores',
    outOfRangeHint: 'Ningún lugar de la Tierra llega a estos valores: se muestran como límite y no cuentan en el puntaje, igual que en el resto de la app.',
    closest: 'lo más cercano en la Tierra: {v}',
    ranking: 'Mejores lugares de la Tierra',
    forWhat: 'para {what}',
    customWhat: 'tus valores de {body}',
    candidates: '{n} lugares comparados en {ms} ms',
    similarity: 'Similitud por característica',
    simTip: '{feature}: Tierra {earth} / {body} {other}',
    best: '✓ más parecido',
    worst: '⚠ rompe la analogía',
    map: 'Dónde están',
    globe: 'Ver en el globo 3D',
    googleEarth: 'Ver en Google Earth ↗',
    checkPoint: 'A qué se parece este lugar',
    download: 'Descargar',
    copyLink: 'Copiar enlace',
    copied: '¡Copiado!',
    point: 'Punto de la Tierra',
    lat: 'Latitud',
    lon: 'Longitud',
    pointHint: 'Escribe las coordenadas o haz clic en el mapa. La base cubre regiones secas o frías.',
    pointSearch: 'Consultar punto',
    nearest: 'Lugar más cercano: {region}, a {km} km',
    known: 'Famoso',
    pointResults: 'A qué sitios se parece',
    bestSite: 'Más parecido a {site}',
    api: 'Para investigadores: los mismos resultados en /data/api/v1/ y en src/analog_api.py (docs/API.md).',
  },
  en: {
    title: 'Find analogs on Earth',
    intro:
      'Pick a site on the Moon or Mars, or type your own values: the comparator finds the most similar places among 691 thousand places in 727 regions of Earth. It is the same score as the rest of the app.',
    tabSite: 'Place on another world',
    tabPoint: 'Point on Earth',
    loading: 'Loading the Earth database (about 7 MB, only the first time)…',
    loadError: 'Could not load the comparator database.',
    start: 'Starting site',
    custom: 'Custom values',
    body: 'Body',
    values: 'Place data',
    emptyHint: 'empty = not compared',
    range: 'Earth: {min} to {max}',
    options: 'Options and weights (what matters more)',
    top: 'Results',
    perRegion: 'One per region',
    includeKnown: 'Include famous analogs',
    minKm: 'Minimum separation (km)',
    resetWeights: 'Reset model weights',
    search: 'Find analogs',
    reset: 'Reset',
    outOfRange: 'Earth does not reach these values',
    outOfRangeHint: 'No place on Earth reaches these values: they are shown as a limit and do not count in the score, as everywhere else in the app.',
    closest: 'closest on Earth: {v}',
    ranking: 'Best places on Earth',
    forWhat: 'for {what}',
    customWhat: 'your {body} values',
    candidates: '{n} places compared in {ms} ms',
    similarity: 'Similarity per feature',
    simTip: '{feature}: Earth {earth} / {body} {other}',
    best: '✓ most similar',
    worst: '⚠ breaks the analogy',
    map: 'Where they are',
    globe: 'Show on the 3D globe',
    googleEarth: 'View in Google Earth ↗',
    checkPoint: 'What does this place resemble',
    download: 'Download',
    copyLink: 'Copy link',
    copied: 'Copied!',
    point: 'Point on Earth',
    lat: 'Latitude',
    lon: 'Longitude',
    pointHint: 'Type the coordinates or click the map. The database covers dry or cold regions.',
    pointSearch: 'Check point',
    nearest: 'Nearest place: {region}, {km} km away',
    known: 'Famous',
    pointResults: 'Which sites it resembles',
    bestSite: 'Most similar to {site}',
    api: 'For researchers: the same results in /data/api/v1/ and in src/analog_api.py (docs/API.md).',
  },
} as const

type Key = keyof (typeof TEXT)['es']

const FEATURE_NAMES: Record<Lang, Record<string, string>> = {
  es: {
    slope_deg: 'Pendiente', roughness: 'Rugosidad', temp_mean_K: 'Temperatura media', temp_range_K: 'Amplitud térmica',
    albedo: 'Albedo', precip_mm: 'Precipitación', ndvi: 'Vegetación (NDVI)', em_contrast: 'Tipo de roca',
  },
  en: {
    slope_deg: 'Slope', roughness: 'Roughness', temp_mean_K: 'Mean temperature', temp_range_K: 'Temperature range',
    albedo: 'Albedo', precip_mm: 'Precipitation', ndvi: 'Vegetation (NDVI)', em_contrast: 'Rock type',
  },
}
const UNITS: Record<Lang, Record<string, string>> = {
  es: { slope_deg: '°', roughness: 'm', temp_mean_K: 'K', temp_range_K: 'K', precip_mm: 'mm/año' },
  en: { slope_deg: '°', roughness: 'm', temp_mean_K: 'K', temp_range_K: 'K', precip_mm: 'mm/yr' },
}
const BODY_KEY: Record<Body, 'luna' | 'marte'> = { Moon: 'luna', Mars: 'marte' }

const GIBS_WORLD =
  'https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0' +
  '&LAYERS=BlueMarble_ShadedRelief_Bathymetry&STYLES=&CRS=EPSG:4326&BBOX=-90,-180,90,180&WIDTH=1024&HEIGHT=512&FORMAT=image/jpeg'
const DEFAULT_MIN_KM = 300

function fill(text: string, vars: Record<string, string | number> = {}) {
  return text.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? ''))
}

function fmt(v: number | null | undefined, lang: Lang, digits?: number) {
  if (v == null || !Number.isFinite(v)) return '—'
  const abs = Math.abs(v)
  const d = digits ?? (abs >= 100 ? 0 : abs >= 10 ? 1 : abs >= 1 ? 2 : 3)
  return v.toLocaleString(lang, { maximumFractionDigits: d })
}

function download(name: string, text: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function earthUrl(lat: number, lon: number) {
  return `https://earth.google.com/web/@${lat},${lon},1000a,30000d,35y,0h,45t,0r`
}

type Form = {
  site: string // site id or '' for custom values
  body: Body
  values: Record<string, string>
  top: number
  perRegion: boolean
  includeKnown: boolean
  minKm: number
  weights: Record<string, number>
  /** Mission type whose weights are in use, or '' for the model weights / custom weights. */
  mission: MissionId | ''
}

/** The mission, if it makes sense for this body (no thermal tests on the Moon, whose temperature is not compared). */
function missionFor(db: ComparatorDB, body: Body, mission: MissionId | ''): MissionId | '' {
  return mission && missionAvailable(missionWeights(db.meta, body, mission), mission) ? mission : ''
}

/** Weights to start from: the mission's, or the model's for this body. */
function startWeights(db: ComparatorDB, body: Body, mission: MissionId | '') {
  const m = missionFor(db, body, mission)
  return m ? missionWeights(db.meta, body, m) : { ...db.meta.weights[body] }
}

function siteStrings(db: ComparatorDB, id: string): Record<string, string> {
  const s = db.meta.sites.find((x) => x.id === id)
  const out: Record<string, string> = {}
  for (const f of db.features) {
    const v = s?.values[f]
    out[f] = v == null ? '' : String(v)
  }
  return out
}

/** Reads a shared query from the URL hash: #buscar?site=...&body=...&v.temp_mean_K=...&w.albedo=... */
function formFromHash(db: ComparatorDB): Partial<Form> | null {
  const h = window.location.hash
  if (!h.startsWith('#buscar')) return null
  const p = new URLSearchParams(h.split('?')[1] ?? '')
  const values: Record<string, string> = {}
  const weights: Record<string, number> = {}
  p.forEach((v, k) => {
    if (k.startsWith('v.') && db.features.includes(k.slice(2))) values[k.slice(2)] = v
    if (k.startsWith('w.') && db.features.includes(k.slice(2)) && Number(v) >= 0) weights[k.slice(2)] = Number(v)
  })
  const s = db.meta.sites.find((x) => x.id === p.get('site'))
  const body: Body = (p.get('body') ?? s?.body) === 'Moon' ? 'Moon' : 'Mars'
  const mission = (MISSION_IDS as string[]).includes(p.get('mission') ?? '') ? (p.get('mission') as MissionId) : ''
  return {
    mission: missionFor(db, body, mission),
    site: s && !Object.keys(values).length ? s.id : '',
    body,
    values: { ...(s ? siteStrings(db, s.id) : {}), ...values },
    top: Number(p.get('top')) || 10,
    perRegion: p.get('per_region') !== '0',
    includeKnown: p.get('include_known') === '1',
    minKm: p.has('min_km') ? Math.max(0, Number(p.get('min_km')) || 0) : DEFAULT_MIN_KM,
    weights: { ...startWeights(db, body, mission), ...weights },
  }
}

export default function AnalogFinder({ onShowOnGlobe }: { onShowOnGlobe?: (place: { lat: number; lng: number; name: string }) => void } = {}) {
  const { lang } = useLang()
  const t = (k: Key, vars?: Record<string, string | number>) => fill(TEXT[lang][k], vars)
  const [db, setDb] = useState<ComparatorDB | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<'site' | 'point'>('site')
  const [form, setForm] = useState<Form | null>(null)
  const [result, setResult] = useState<AnalogsResponse | null>(null)
  const [selected, setSelected] = useState(0)
  const [point, setPoint] = useState({ lat: '25.425', lon: '29.425' })
  const [pointResult, setPointResult] = useState<PointResponse | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [copied, setCopied] = useState(false)

  function run(d: ComparatorDB, f: Form) {
    const values: Values = {}
    for (const k of d.features) {
      const s = (f.values[k] ?? '').trim().replace(',', '.')
      values[k] = s === '' ? null : Number(s)
    }
    try {
      const t0 = performance.now()
      const res = findAnalogs(d, {
        site: f.site || null, body: f.body, values, top: f.top, perRegion: f.perRegion,
        includeKnown: f.includeKnown, minKm: f.minKm, weights: f.weights,
      })
      setElapsed(Math.round(performance.now() - t0))
      setResult(res)
      setSelected(0)
      setError(null)
    } catch (e) {
      setError((e as Error).message)
      setResult(null)
    }
  }

  function runPoint(d: ComparatorDB, lat: number, lon: number) {
    try {
      setPointResult(queryPoint(d, lat, lon))
      setError(null)
    } catch (e) {
      setError((e as Error).message)
      setPointResult(null)
    }
  }

  useEffect(() => {
    let alive = true
    loadComparator()
      .then((d) => {
        if (!alive) return
        setDb(d)
        const first = d.meta.sites.find((s) => s.body === 'Mars') ?? d.meta.sites[0]
        const initial: Form = {
          site: first.id, body: first.body, values: siteStrings(d, first.id), top: 10,
          perRegion: true, includeKnown: false, minKm: DEFAULT_MIN_KM, weights: { ...d.meta.weights[first.body] }, mission: '',
        }
        const f = { ...initial, ...formFromHash(d) }
        setForm(f)
        run(d, f)
      })
      .catch((e: Error) => alive && setError(e.message))
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const shareUrl = useMemo(() => {
    if (!db || !form) return ''
    const p = new URLSearchParams()
    if (form.site) p.set('site', form.site)
    p.set('body', form.body)
    if (form.mission) p.set('mission', form.mission)
    if (!form.site) for (const f of db.features) if (form.values[f]) p.set(`v.${f}`, form.values[f])
    const start = startWeights(db, form.body, form.mission)
    for (const f of db.features) if (form.weights[f] !== start[f]) p.set(`w.${f}`, String(form.weights[f]))
    if (form.top !== 10) p.set('top', String(form.top))
    if (!form.perRegion) p.set('per_region', '0')
    if (form.includeKnown) p.set('include_known', '1')
    if (form.minKm !== DEFAULT_MIN_KM) p.set('min_km', String(form.minKm))
    return `${window.location.origin}${window.location.pathname}#buscar?${p.toString()}`
  }, [db, form])

  // Yardstick for "suitable for": best score Earth has for each mission, for the searched target.
  // Known sites read it from public/data/missions.json (full scan, same as the site panel); custom
  // values get it from a sample of Earth. It depends only on the target, not on the weights.
  const missionData = useMissionData()
  const refKey = result ? `${result.query.site ?? ''}|${result.query.body}|${JSON.stringify(result.query.values)}` : ''
  const missionRef = useMemo(() => {
    if (!db || !result) return null
    const known = result.query.site ? missionData?.reference[result.query.site] : undefined
    return known ?? missionReference(db, result.query.values, result.query.body)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [db, refKey, missionData])
  const pointSiteId = pointResult?.results[0]?.site
  const pointRef = useMemo(() => {
    const s = pointSiteId ? db?.meta.sites.find((x) => x.id === pointSiteId) : undefined
    if (!db || !s) return null
    return missionData?.reference[s.id] ?? missionReference(db, s.values, s.body)
  }, [db, pointSiteId, missionData])

  if (error && !db) return <section className="comparison muted-box">{t('loadError')} ({error})</section>
  if (!db || !form) return <section className="comparison muted-box">{t('loading')}</section>

  const set = (patch: Partial<Form>) => setForm({ ...form, ...patch })
  const pickSite = (id: string) => {
    if (!id) return set({ site: '' })
    const s = db.meta.sites.find((x) => x.id === id)!
    const f = { ...form, site: id, body: s.body, values: siteStrings(db, id), mission: missionFor(db, s.body, form.mission), weights: startWeights(db, s.body, form.mission) }
    setForm(f)
    run(db, f)
  }
  const pickMission = (mission: MissionId | '') => {
    const f = { ...form, mission, weights: startWeights(db, form.body, mission) }
    setForm(f)
    run(db, f)
  }
  const usingDefaults = !form.mission && db.features.every((f) => form.weights[f] === db.meta.weights[form.body][f])
  const mt = (m: MissionId) => MISSION_TEXT[lang][m]
  const mu = (k: keyof (typeof MISSION_UI)['es'], vars?: Record<string, string | number>) => fill(MISSION_UI[lang][k], vars)
  /** Variables a mission weighs most for this body (switched-off ones excluded). */
  const priorities = (m: MissionId) => {
    const w = missionWeights(db.meta, form.body, m)
    return db.features.filter((f) => w[f] > 0).sort((a, b) => w[b] - w[a]).slice(0, 3).map((f) => FEATURE_NAMES[lang][f]).join(', ')
  }
  const fitsOf = (body: Body, similarity: Record<string, number>, ref: Record<MissionId, number> | null) =>
    topMissions(missionFits(db.meta, body, similarity, ref ?? undefined))
  /** "Suitable for" badge: the 2-3 missions a place suits best; a click filters by that mission. */
  const suitable = (fits: MissionFit[], compact = false, onPick: (m: MissionId) => void = pickMission) => (
    <span className={`mission-fits ${compact ? 'compact' : ''}`}>
      {!compact && <span className="mission-fits-label">{mu('suitable')}</span>}
      {fits.map((x) => {
        const tip = mu('fitTip', {
          mission: mt(x.mission).name, score: Math.round(x.score * 100), rel: Math.min(100, Math.round(x.relative * 100)),
        })
        return compact ? (
          <span key={x.mission} className="mission-dot" title={tip} aria-label={tip}>
            <MissionIcon id={x.mission} size={14} />
          </span>
        ) : (
          <button key={x.mission} className={`pill mission ${form.mission === x.mission ? 'active' : ''}`} title={tip}
            onClick={(e) => {
              e.stopPropagation()
              onPick(x.mission)
            }}>
            <MissionIcon id={x.mission} size={14} /> {mt(x.mission).short}
          </button>
        )
      })}
    </span>
  )
  const range = db.meta.earth_range
  const unit = (f: string) => UNITS[lang][f] ?? ''
  const bodyName = (b: Body) => BODY_NAMES[lang][BODY_KEY[b]]
  const fname = (result?.query.site ?? `custom_${form.body.toLowerCase()}`) + '_analogs'
  const sel = result?.results[selected] ?? null

  const onMapClick = (e: MouseEvent<HTMLDivElement>) => {
    if (tab !== 'point') return
    const box = e.currentTarget.getBoundingClientRect()
    const lon = ((e.clientX - box.left) / box.width) * 360 - 180
    const lat = 90 - ((e.clientY - box.top) / box.height) * 180
    setPoint({ lat: lat.toFixed(3), lon: lon.toFixed(3) })
    runPoint(db, lat, lon)
  }

  const worldMap = (dots: { key: string; lat: number; lon: number; label: string; active?: boolean; onClick?: () => void }[]) => (
    <div className={`finder-world ${tab === 'point' ? 'clickable' : ''}`} onClick={onMapClick}>
      <img src={GIBS_WORLD} alt="" loading="lazy" onError={(e) => (e.currentTarget.style.visibility = 'hidden')} />
      {dots.map((d) => (
        <button
          key={d.key}
          className={`finder-dot ${d.active ? 'active' : ''}`}
          title={d.label}
          aria-label={d.label}
          style={{ left: `${((d.lon + 180) / 360) * 100}%`, top: `${((90 - d.lat) / 180) * 100}%`, background: BODY_COLORS.tierra }}
          onClick={(e) => {
            e.stopPropagation()
            d.onClick?.()
          }}
        />
      ))}
    </div>
  )

  return (
    <section className="comparison finder" aria-label={t('title')}>
      <header className="comparison-header">
        <div>
          <h2>{t('title')}</h2>
          <p className="pair muted">{t('intro')}</p>
        </div>
        <div className="seg" role="tablist">
          {(['site', 'point'] as const).map((k) => (
            <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? 'active' : ''} onClick={() => setTab(k)}>
              {k === 'site' ? t('tabSite') : t('tabPoint')}
            </button>
          ))}
        </div>
      </header>

      {error && <p className="finder-error">{error}</p>}

      {tab === 'site' ? (
        <>
          <h3>{t('start')}</h3>
          <div className="finder-sites">
            {(['Moon', 'Mars'] as Body[]).map((b) => (
              <div className="chips target-chips" key={b} role="group" aria-label={bodyName(b)}>
                <span className="finder-body">
                  <span className="swatch" style={{ background: BODY_COLORS[BODY_KEY[b]] }} /> {bodyName(b)}
                </span>
                {db.meta.sites.filter((s) => s.body === b).map((s) => (
                  <button key={s.id} className={`chip ${form.site === s.id ? 'active' : ''}`} onClick={() => pickSite(s.id)}>
                    {s.name}
                  </button>
                ))}
              </div>
            ))}
            <div className="chips target-chips">
              <span className="finder-body">{t('custom')}</span>
              {(['Moon', 'Mars'] as Body[]).map((b) => (
                <button key={b} className={`chip ${!form.site && form.body === b ? 'active' : ''}`}
                  onClick={() => set({ site: '', body: b, mission: missionFor(db, b, form.mission), weights: startWeights(db, b, form.mission) })}>
                  {bodyName(b)}
                </button>
              ))}
            </div>
          </div>

          {/* ---------- Mission type (weight presets) ---------- */}
          <h3>{mu('title')}</h3>
          <div className="chips mission-chips" role="group" aria-label={mu('title')}>
            <button className={`chip ${!form.mission && usingDefaults ? 'active' : ''}`} onClick={() => pickMission('')}>
              {mu('all')}
            </button>
            {MISSION_IDS.filter((m) => missionFor(db, form.body, m)).map((m) => (
              <button key={m} className={`chip mission-chip ${form.mission === m ? 'active' : ''}`} onClick={() => pickMission(m)}
                aria-pressed={form.mission === m}>
                <MissionIcon id={m} /> {mt(m).name}
              </button>
            ))}
            {!form.mission && !usingDefaults && <span className="chip mission-custom" aria-disabled="true">{mu('custom')}</span>}
          </div>
          <div className="mission-info">
            {form.mission ? (
              <>
                <span className="mission-info-icon"><MissionIcon id={form.mission} size={30} /></span>
                <div>
                  <p><strong>{mt(form.mission).name}.</strong> {mt(form.mission).why}</p>
                  <p className="muted small">
                    {mu('priorities', { list: priorities(form.mission) })}
                    {form.body === 'Moon' && form.mission === 'habitat' && <> · {mu('moonTemp')}</>}
                  </p>
                  {mt(form.mission).note && <p className="mission-note small">⚠ {mt(form.mission).note}</p>}
                </div>
              </>
            ) : (
              <p className="muted small">{mu('hint')}</p>
            )}
          </div>

          <div className="comparison-grid">
            {/* ---------- Input values ---------- */}
            <div className="card">
              <h3>{t('values')}</h3>
              <div className="finder-values">
                {db.features.map((f) => (
                  <label className="finder-field" key={f}>
                    <span>
                      {FEATURE_NAMES[lang][f]} {unit(f) && <small className="muted">({unit(f)})</small>}
                    </span>
                    <input
                      inputMode="decimal"
                      value={form.values[f] ?? ''}
                      placeholder={t('emptyHint')}
                      onChange={(e) => set({ site: '', values: { ...form.values, [f]: e.target.value } })}
                    />
                    {range[f] && <small className="muted">{t('range', { min: fmt(range[f][0], lang), max: fmt(range[f][1], lang) })}</small>}
                  </label>
                ))}
              </div>

              <details className="weights">
                <summary>{t('options')}</summary>
                <label>
                  <span>{t('top')}</span>
                  <select value={form.top} onChange={(e) => set({ top: Number(e.target.value) })}>
                    {[5, 10, 20, 50].map((n) => <option key={n} value={n}>{n}</option>)}
                  </select>
                  <span />
                </label>
                <label>
                  <span>{t('minKm')}</span>
                  <input inputMode="numeric" value={form.minKm} onChange={(e) => set({ minKm: Math.max(0, Number(e.target.value) || 0) })} />
                  <span />
                </label>
                <label className="checkbox">
                  <input type="checkbox" checked={form.perRegion} onChange={(e) => set({ perRegion: e.target.checked })} />
                  {t('perRegion')}
                </label>
                <label className="checkbox">
                  <input type="checkbox" checked={form.includeKnown} onChange={(e) => set({ includeKnown: e.target.checked })} />
                  {t('includeKnown')}
                </label>
                {db.features.map((f) => (
                  <label key={f}>
                    <span>{FEATURE_NAMES[lang][f]}</span>
                    <input type="range" min={0} max={3} step={0.25} value={form.weights[f] ?? 0}
                      onChange={(e) => set({ mission: '', weights: { ...form.weights, [f]: Number(e.target.value) } })} />
                    <span className="weight-value">{(form.weights[f] ?? 0).toFixed(2)}</span>
                  </label>
                ))}
                <button className="link" disabled={usingDefaults} onClick={() => pickMission('')}>
                  {t('resetWeights')}
                </button>
              </details>

              <div className="finder-actions">
                <button className="btn primary" onClick={() => run(db, form)}>{t('search')}</button>
                <button className="link" onClick={() => pickSite(form.site || db.meta.sites[0].id)}>{t('reset')}</button>
              </div>
            </div>

            {/* ---------- Ranking ---------- */}
            <div className="card">
              <h3>{t('ranking')}</h3>
              {result && result.results.length > 0 && sel ? (
                <>
                  <div className="hero">
                    <div>
                      <span className="hero-number">{Math.round(sel.score * 100)}</span>
                      <span className="hero-unit">/ 100</span>
                    </div>
                    <div className="hero-meta">
                      <p>
                        <strong>#{sel.rank} {regionLabel(db, sel.region, lang, sel.lat, sel.lon)}</strong>
                        {sel.known && <span className="badge">{t('known')}</span>}
                      </p>
                      <p className="muted">
                        {t('forWhat', { what: result.query.site_name ?? t('customWhat', { body: bodyName(result.query.body) }) })}
                      </p>
                      <p className="muted">{t('candidates', { n: result.n_candidates.toLocaleString(lang), ms: elapsed })}</p>
                      {suitable(fitsOf(result.query.body, sel.similarity, missionRef))}
                    </div>
                  </div>
                  <ol className="ranking">
                    {result.results.map((r, i) => (
                      <li key={`${r.region}-${r.lat}-${r.lon}`} className={`finder-rank ${i === selected ? 'current' : ''}`}
                        onClick={() => setSelected(i)} title={`${regionLabel(db, r.region, lang, r.lat, r.lon)}: ${Math.round(r.score * 100)} / 100`}>
                        <span className="rank-pos">{r.rank}</span>
                        <span className="rank-name">
                          {regionLabel(db, r.region, lang, r.lat, r.lon)}
                          {r.known && <small> · {t('known')}</small>}
                          {suitable(fitsOf(result.query.body, r.similarity, missionRef), true)}
                        </span>
                        <span className="rank-track">
                          <span className="rank-fill" style={{ width: `${r.score * 100}%`, background: i === selected ? SIMILARITY_COLOR : '#3a4560' }} />
                        </span>
                        <span className="rank-value">{Math.round(r.score * 100)}</span>
                      </li>
                    ))}
                  </ol>
                  <p className="finder-downloads">
                    <span className="muted">{t('download')}:</span>
                    <button className="link" onClick={() => download(`${fname}.geojson`, toGeoJSON(result), 'application/geo+json')}>GeoJSON</button>
                    <button className="link" onClick={() => download(`${fname}.kml`, toKML(result), 'application/vnd.google-earth.kml+xml')}>KML</button>
                    <button className="link" onClick={() => download(`${fname}.waypoints`, toWaypoints(result), 'text/plain')}>Waypoints</button>
                    <button className="link" onClick={() => {
                      void navigator.clipboard?.writeText(shareUrl)
                      setCopied(true)
                      window.setTimeout(() => setCopied(false), 1500)
                    }}>{copied ? t('copied') : t('copyLink')}</button>
                  </p>
                </>
              ) : (
                <p className="muted">—</p>
              )}
            </div>

            {/* ---------- Per-feature similarity of the selected place ---------- */}
            {result && sel && (
              <div className="card">
                <h3>{t('similarity')} · {regionLabel(db, sel.region, lang, sel.lat, sel.lon)}</h3>
                <ul className="meter-list">
                  {Object.entries(sel.similarity).map(([f, s]) => (
                    <li key={f} title={t('simTip', {
                      feature: FEATURE_NAMES[lang][f], earth: `${fmt(sel.earth_values[f], lang)} ${unit(f)}`,
                      body: bodyName(result.query.body), other: `${fmt(result.query.values[f] ?? null, lang)} ${unit(f)}`,
                    })}>
                      <span className="meter-name">{FEATURE_NAMES[lang][f] ?? f}</span>
                      <span className="meter-track">
                        <span className="meter-fill" style={{ width: `${s * 100}%`, background: SIMILARITY_COLOR }} />
                      </span>
                      <span className="meter-value">{fmt(s, lang, 2)}</span>
                      <span className="meter-tag">
                        <span className="tag muted">
                          {fmt(sel.earth_values[f], lang)} / {fmt(result.query.values[f] ?? null, lang)} {unit(f)}
                        </span>{' '}
                        {f === sel.best_match && <span className="tag good">{t('best')}</span>}
                        {f === sel.worst_match && <span className="tag bad">{t('worst')}</span>}
                      </span>
                    </li>
                  ))}
                </ul>
                <p className="finder-downloads">
                  {onShowOnGlobe && (
                    <button className="link" onClick={() => onShowOnGlobe({ lat: sel.lat, lng: sel.lon, name: regionLabel(db, sel.region, lang, sel.lat, sel.lon) })}>
                      {t('globe')}
                    </button>
                  )}
                  <a className="link" href={earthUrl(sel.lat, sel.lon)} target="_blank" rel="noreferrer">{t('googleEarth')}</a>
                  <button className="link" onClick={() => {
                    setTab('point')
                    setPoint({ lat: String(sel.lat), lon: String(sel.lon) })
                    runPoint(db, sel.lat, sel.lon)
                  }}>{t('checkPoint')}</button>
                </p>
              </div>
            )}

            {/* ---------- Map + limits ---------- */}
            {result && (
              <div className="card">
                <h3>{t('map')}</h3>
                {worldMap(result.results.map((r, i) => ({
                  key: `${r.region}-${i}`, lat: r.lat, lon: r.lon, label: `#${r.rank} ${regionLabel(db, r.region, lang, r.lat, r.lon)}`,
                  active: i === selected, onClick: () => setSelected(i),
                })))}
                {result.out_of_earth_range.length > 0 && (
                  <>
                    <h3>{t('outOfRange')}</h3>
                    <p className="muted small">{t('outOfRangeHint')}</p>
                    <table className="limits">
                      <tbody>
                        {result.out_of_earth_range.map((o) => (
                          <tr key={o.feature}>
                            <th scope="row">{FEATURE_NAMES[lang][o.feature] ?? o.feature}</th>
                            <td>{bodyName(result.query.body)}: {fmt(o.value, lang)} {unit(o.feature)}</td>
                            <td>{t('closest', { v: `${fmt(o.closest_on_earth, lang)} ${unit(o.feature)}` })}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                )}
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="comparison-grid">
          <div className="card">
            <h3>{t('point')}</h3>
            <p className="muted small">{t('pointHint')}</p>
            <div className="finder-values">
              {(['lat', 'lon'] as const).map((k) => (
                <label className="finder-field" key={k}>
                  <span>{t(k)}</span>
                  <input inputMode="decimal" value={point[k]} onChange={(e) => setPoint({ ...point, [k]: e.target.value })} />
                </label>
              ))}
            </div>
            <div className="finder-actions">
              <button className="btn primary"
                onClick={() => runPoint(db, Number(point.lat.replace(',', '.')), Number(point.lon.replace(',', '.')))}>
                {t('pointSearch')}
              </button>
            </div>
            <div className="finder-map-gap">
              {worldMap(pointResult ? [{ key: 'cell', lat: pointResult.cell.lat, lon: pointResult.cell.lon, label: regionLabel(db, pointResult.cell.region, lang), active: true }] : [])}
            </div>
          </div>

          <div className="card">
            <h3>{t('pointResults')}</h3>
            {pointResult ? (
              <>
                <div className="hero">
                  <div>
                    <span className="hero-number">{Math.round((pointResult.results[0].score ?? 0) * 100)}</span>
                    <span className="hero-unit">/ 100</span>
                  </div>
                  <div className="hero-meta">
                    <p><strong>{t('bestSite', { site: pointResult.results[0].site_name })}</strong></p>
                    <p className="muted">
                      {t('nearest', { region: regionLabel(db, pointResult.cell.region, lang, pointResult.cell.lat, pointResult.cell.lon), km: fmt(pointResult.cell.distance_km, lang, 1) })}
                      {pointResult.cell.known && <span className="badge">{t('known')}</span>}
                    </p>
                    {pointResult.results[0].score != null &&
                      suitable(fitsOf(pointResult.results[0].body, pointResult.results[0].similarity, pointRef), false, (m) => {
                        // Search analogs of that site for this mission.
                        const s = pointResult.results[0]
                        const f = { ...form, site: s.site, body: s.body, values: siteStrings(db, s.site), mission: m, weights: missionWeights(db.meta, s.body, m) }
                        setForm(f)
                        setTab('site')
                        run(db, f)
                      })}
                  </div>
                </div>
                <ol className="ranking">
                  {pointResult.results.map((r, i) => (
                    <li key={r.site} className={i === 0 ? 'current' : ''}
                      title={`${r.site_name}: ${r.worst_match ? `${t('worst')} ${FEATURE_NAMES[lang][r.worst_match] ?? r.worst_match}` : ''}`}>
                      <span className="rank-pos">{r.rank}</span>
                      <span className="rank-name">
                        <span className="swatch" style={{ background: BODY_COLORS[BODY_KEY[r.body]] }} /> {r.site_name}
                      </span>
                      <span className="rank-track">
                        <span className="rank-fill" style={{ width: `${(r.score ?? 0) * 100}%`, background: i === 0 ? SIMILARITY_COLOR : '#3a4560' }} />
                      </span>
                      <span className="rank-value">{r.score == null ? '—' : Math.round(r.score * 100)}</span>
                    </li>
                  ))}
                </ol>
                <p className="finder-downloads">
                  {pointResult.results[0].best_match && (
                    <span className="tag good">{t('best')}: {FEATURE_NAMES[lang][pointResult.results[0].best_match!]}</span>
                  )}
                  {pointResult.results[0].worst_match && (
                    <span className="tag bad">{t('worst')}: {FEATURE_NAMES[lang][pointResult.results[0].worst_match!]}</span>
                  )}
                </p>
                <p className="finder-downloads">
                  <span className="muted">{t('download')}:</span>
                  <button className="link" onClick={() => download('earth_point.geojson', toGeoJSON(pointResult), 'application/geo+json')}>GeoJSON</button>
                  <button className="link" onClick={() => download('earth_point.kml', toKML(pointResult), 'application/vnd.google-earth.kml+xml')}>KML</button>
                </p>
              </>
            ) : (
              <p className="muted">—</p>
            )}
          </div>
        </div>
      )}

      <p className="muted small finder-api">{t('api')}</p>
    </section>
  )
}
