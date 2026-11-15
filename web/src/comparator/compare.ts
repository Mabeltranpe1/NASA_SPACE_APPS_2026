/**
 * Browser port of src/compare.py (score_cells / best_and_worst) over the compact Earth
 * database made by `python src/analog_api.py export-web`:
 *   public/data/comparator/comparator.json  settings (features, tolerance, weights), sites, regions
 *   public/data/comparator/earth.bin        gzip, int16 columns (see src/analog_api.py export_web)
 *
 * The settings (tolerances, weights, log features) are read from comparator.json, so they always
 * match the Python side. There is ONE score, the same as the rest of the web app (src/export_web.py):
 * the weights of each body already switch off the variables Earth cannot reach (e.g. 125 K on the
 * Moon, listed in `switched_off`), and they are reported apart in `out_of_earth_range`.
 *
 * No React and no DOM here: this file also runs in Node (scripts/check-comparator.ts).
 */

export type Body = 'Moon' | 'Mars'
export type Values = Record<string, number | null | undefined>

export interface ColumnInfo {
  name: string
  dtype: 'int16' | 'uint16'
  scale: number
  /** value = stored / scale + offset */
  offset?: number
  log1p?: boolean
}

export interface SiteInfo {
  id: string
  name: string
  body: Body
  lat: number | null
  lon: number | null
  area?: string
  values: Values
}

export interface RegionInfo {
  name: string
  /** Readable name and country (src/region_names.py); grid tiles are named after their country. */
  label?: { es: string; en: string }
  country?: { es: string; en: string }
  grid?: boolean
  known: boolean
  description?: string
}

export interface ComparatorMeta {
  api_version: string
  features: string[]
  labels: Record<string, { label: string; unit: string }>
  tolerance: Record<string, number>
  log_features: string[]
  weights: Record<Body, Record<string, number>>
  /** Variables switched off per body because Earth cannot reach them (same rule as the web app). */
  switched_off?: Record<Body, string[]>
  min_coverage: number
  earth_range: Record<string, [number, number]>
  n_cells: number
  columns: ColumnInfo[]
  missing: number
  regions: RegionInfo[]
  sites: SiteInfo[]
}

export interface ComparatorDB {
  meta: ComparatorMeta
  n: number
  lat: Float64Array
  lon: Float64Array
  region: Uint16Array
  /** Features present in the web database, in meta.features order (elev_m is not). */
  features: string[]
  /** Earth values already on the compare scale (log1p, divided by tolerance); NaN = missing. */
  scaled: Float64Array[]
}

export interface AnalogResult {
  rank: number
  region: string
  known: boolean
  lat: number
  lon: number
  score: number
  similarity: Record<string, number>
  earth_values: Record<string, number | null>
  best_match: string
  worst_match: string
}

export interface OutOfRange {
  feature: string
  value: number
  earth_min: number
  earth_max: number
  closest_on_earth: number
}

export interface AnalogsResponse {
  kind: 'analogs'
  api_version: string
  query: {
    site: string | null
    site_name: string | null
    body: Body
    site_lat: number | null
    site_lon: number | null
    values: Values
    top: number
    per_region: boolean
    min_km: number
    include_known: boolean
    weights: Record<string, number>
  }
  variables_used: string[]
  out_of_earth_range: OutOfRange[]
  n_candidates: number
  results: AnalogResult[]
}

export interface PointSiteResult {
  rank: number
  site: string
  site_name: string
  body: Body
  site_lat: number | null
  site_lon: number | null
  score: number | null
  similarity: Record<string, number>
  best_match: string | null
  worst_match: string | null
}

export interface PointResponse {
  kind: 'point'
  api_version: string
  query: { lat: number; lon: number }
  cell: {
    lat: number
    lon: number
    distance_km: number
    region: string
    known: boolean
    values: Record<string, number | null>
  }
  results: PointSiteResult[]
}

// ---------------------------------------------------------------------------
// Loading
// ---------------------------------------------------------------------------

async function gunzipIfNeeded(bytes: Uint8Array): Promise<Uint8Array> {
  // Some servers already undo the gzip (Content-Encoding); then the magic number is gone.
  if (bytes[0] !== 0x1f || bytes[1] !== 0x8b) return bytes
  const stream = new Blob([bytes as BlobPart]).stream().pipeThrough(new DecompressionStream('gzip'))
  return new Uint8Array(await new Response(stream).arrayBuffer())
}

/** Build the database from comparator.json (parsed) and the bytes of earth.bin. */
export async function parseComparator(meta: ComparatorMeta, binBytes: Uint8Array): Promise<ComparatorDB> {
  const raw = await gunzipIfNeeded(binBytes)
  const n = meta.n_cells
  const view = new DataView(raw.buffer, raw.byteOffset, raw.byteLength)
  if (raw.byteLength !== n * 2 * meta.columns.length) throw new Error('earth.bin does not match comparator.json')

  const column = (k: number, signed: boolean): Int32Array => {
    const out = new Int32Array(n)
    const base = k * n * 2
    for (let i = 0; i < n; i++) out[i] = signed ? view.getInt16(base + 2 * i, true) : view.getUint16(base + 2 * i, true)
    return out
  }

  const lat = new Float64Array(n)
  const lon = new Float64Array(n)
  const region = new Uint16Array(n)
  const features: string[] = []
  const byName = new Map<string, Float64Array>()
  meta.columns.forEach((c, k) => {
    const ints = column(k, c.dtype === 'int16')
    if (c.name === 'lat' || c.name === 'lon') {
      const out = c.name === 'lat' ? lat : lon
      for (let i = 0; i < n; i++) out[i] = ints[i] / c.scale
    } else if (c.name === 'region') {
      for (let i = 0; i < n; i++) region[i] = ints[i]
    } else {
      // precip is stored as log1p(mm)*scale, i.e. already on the log scale compare.py uses.
      const tol = meta.tolerance[c.name]
      const out = new Float64Array(n)
      const off = c.offset ?? 0
      for (let i = 0; i < n; i++) out[i] = ints[i] === meta.missing ? NaN : (ints[i] / c.scale + off) / tol
      byName.set(c.name, out)
    }
  })
  for (const f of meta.features) if (byName.has(f)) features.push(f)
  return { meta, n, lat, lon, region, features, scaled: features.map((f) => byName.get(f)!) }
}

let cache: Promise<ComparatorDB> | null = null

/** Load once per page (about 6 MB, only when the finder is opened). */
export function loadComparator(base = '/data/comparator'): Promise<ComparatorDB> {
  cache ??= (async () => {
    const [meta, bin] = await Promise.all([
      fetch(`${base}/comparator.json`).then((r) => {
        if (!r.ok) throw new Error(`comparator.json: HTTP ${r.status}`)
        return r.json() as Promise<ComparatorMeta>
      }),
      fetch(`${base}/earth.bin`).then((r) => {
        if (!r.ok) throw new Error(`earth.bin: HTTP ${r.status}`)
        return r.arrayBuffer()
      }),
    ])
    return parseComparator(meta, new Uint8Array(bin))
  })()
  cache.catch(() => (cache = null))
  return cache
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const isNum = (v: number | null | undefined): v is number => typeof v === 'number' && Number.isFinite(v)

/** compare.py to_matrix + tolerance scaling for one target value. */
function scaleValue(meta: ComparatorMeta, f: string, v: number | null | undefined): number {
  if (!isNum(v)) return NaN
  if (meta.log_features.includes(f)) {
    if (v < 0) throw new Error(`'${f}' must be 0 or bigger.`)
    v = Math.log1p(v)
  }
  return v / meta.tolerance[f]
}

/** Weights for this body (comparator.json), with the caller's changes on top. */
export function weightsFor(meta: ComparatorMeta, body: Body, changes: Record<string, number> = {}) {
  const w: Record<string, number> = { ...meta.weights[body] }
  for (const [k, v] of Object.entries(changes)) {
    if (!(k in w)) throw new Error(`Unknown variable '${k}'`)
    if (!(v >= 0)) throw new Error('Weights must be numbers that are 0 or bigger.')
    w[k] = v
  }
  return w
}

export function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number) {
  const r = Math.PI / 180
  const a =
    Math.sin(((lat2 - lat1) * r) / 2) ** 2 +
    Math.cos(lat1 * r) * Math.cos(lat2 * r) * Math.sin(((lon2 - lon1) * r) / 2) ** 2
  return 2 * 6371 * Math.asin(Math.sqrt(Math.min(1, Math.max(0, a))))
}

export function earthValues(db: ComparatorDB, i: number): Record<string, number | null> {
  const out: Record<string, number | null> = {}
  db.features.forEach((f, j) => {
    const s = db.scaled[j][i]
    if (Number.isNaN(s)) out[f] = null
    else {
      const v = s * db.meta.tolerance[f]
      out[f] = db.meta.log_features.includes(f) ? Math.expm1(v) : v
    }
  })
  return out
}

/** Compared variables where the target is outside everything Earth has. Does not change the score. */
export function outOfEarthRange(meta: ComparatorMeta, values: Values, used?: string[]): OutOfRange[] {
  const out: OutOfRange[] = []
  for (const [f, [lo, hi]] of Object.entries(meta.earth_range)) {
    if (used && !used.includes(f)) continue
    const v = values[f]
    if (!isNum(v)) continue
    if (v < lo || v > hi) out.push({ feature: f, value: v, earth_min: lo, earth_max: hi, closest_on_earth: v < lo ? lo : hi })
  }
  return out
}

interface Prepared {
  t: Float64Array
  w: Float64Array
  wSum: number
  used: string[]
}

function prepare(db: ComparatorDB, values: Values, weights: Record<string, number>): Prepared {
  const k = db.features.length
  const t = new Float64Array(k)
  const w = new Float64Array(k)
  let wSum = 0
  const used: string[] = []
  db.features.forEach((f, j) => {
    t[j] = scaleValue(db.meta, f, values[f])
    // A variable the target does not have (e.g. rain on the Moon) is off.
    w[j] = Number.isNaN(t[j]) ? 0 : weights[f] ?? 0
    wSum += w[j]
    if (w[j] > 0) used.push(f)
  })
  // compare.py also has elev_m; in the web database it is absent, so its weight must be 0.
  for (const f of db.meta.features) {
    if (!db.features.includes(f) && isNum(values[f]) && (weights[f] ?? 0) > 0)
      throw new Error(`'${f}' is not in the web database; set its weight to 0.`)
  }
  if (wSum === 0) throw new Error('All weights are 0 for this target; nothing to compare.')
  return { t, w, wSum, used }
}

/** compare.py score_cells for ONE Earth cell. Returns NaN when the cell lacks a used variable. */
function scoreCell(db: ComparatorDB, p: Prepared, i: number, minCoverage: number, sims?: Float64Array): number {
  let num = 0
  let den = 0
  for (let j = 0; j < p.t.length; j++) {
    const wj = p.w[j]
    const d = db.scaled[j][i] - p.t[j]
    if (wj === 0 || Number.isNaN(d)) {
      if (sims) sims[j] = NaN
      continue
    }
    num += wj * d * d
    den += wj
    if (sims) sims[j] = Math.exp(-Math.abs(d))
  }
  if (den / p.wSum < minCoverage - 1e-9) return NaN
  return Math.exp(-Math.sqrt(num / den))
}

/** compare.py best_and_worst: first feature with the highest / lowest similarity. */
function bestWorst(features: string[], sims: Float64Array): [string, string] {
  let best = -1
  let worst = -1
  for (let j = 0; j < sims.length; j++) {
    if (Number.isNaN(sims[j])) continue
    if (best < 0 || sims[j] > sims[best]) best = j
    if (worst < 0 || sims[j] < sims[worst]) worst = j
  }
  return [best < 0 ? '' : features[best], worst < 0 ? '' : features[worst]]
}

// ---------------------------------------------------------------------------
// 1. Find analogs
// ---------------------------------------------------------------------------

export interface FindOptions {
  /** Site id from comparator.json; its values are the starting point. */
  site?: string | null
  /** Your own values; they replace the site's values. */
  values?: Values
  body?: Body
  top?: number
  /** Only the best place of each Earth region (default true). */
  perRegion?: boolean
  /** Minimum distance between returned places, km (default 300, like src/analog_api.py). */
  minKm?: number
  /** Include famous analog regions (default false, like make_results.py). */
  includeKnown?: boolean
  weights?: Record<string, number>
}

export function findAnalogs(db: ComparatorDB, opts: FindOptions = {}): AnalogsResponse {
  const { meta } = db
  const site = opts.site ? meta.sites.find((s) => s.id === opts.site) : undefined
  if (opts.site && !site) throw new Error(`Unknown site '${opts.site}'`)
  const values: Values = { ...(site?.values ?? {}), ...(opts.values ?? {}) }
  const body = opts.body ?? site?.body
  if (body !== 'Moon' && body !== 'Mars') throw new Error("Give a site or body = 'Moon' or 'Mars'.")
  const top = opts.top ?? 10
  const perRegion = opts.perRegion ?? true
  const minKm = opts.minKm ?? 300
  const includeKnown = opts.includeKnown ?? false
  const weights = weightsFor(meta, body, opts.weights)
  const p = prepare(db, values, weights)

  const score = new Float64Array(db.n)
  const idx: number[] = []
  for (let i = 0; i < db.n; i++) {
    if (!includeKnown && meta.regions[db.region[i]].known) continue
    score[i] = scoreCell(db, p, i, meta.min_coverage)
    if (!Number.isNaN(score[i])) idx.push(i)
  }

  // Best first. With perRegion we only need each region's best cell before sorting.
  let order: number[]
  if (perRegion && minKm === 0) {
    const bestOf = new Map<number, number>()
    for (const i of idx) {
      const r = db.region[i]
      const b = bestOf.get(r)
      if (b === undefined || score[i] > score[b]) bestOf.set(r, i)
    }
    order = [...bestOf.values()]
  } else order = idx
  order.sort((a, b) => score[b] - score[a] || a - b)

  const picked: number[] = []
  const seen = new Set<number>()
  for (const i of order) {
    if (perRegion && seen.has(db.region[i])) continue
    if (minKm > 0 && picked.some((j) => haversineKm(db.lat[i], db.lon[i], db.lat[j], db.lon[j]) < minKm)) continue
    picked.push(i)
    seen.add(db.region[i])
    if (picked.length === top) break
  }

  const sims = new Float64Array(db.features.length)
  const results: AnalogResult[] = picked.map((i, k) => {
    scoreCell(db, p, i, meta.min_coverage, sims)
    const [best, worst] = bestWorst(db.features, sims)
    const similarity: Record<string, number> = {}
    db.features.forEach((f, j) => {
      if (!Number.isNaN(sims[j])) similarity[f] = sims[j]
    })
    const reg = meta.regions[db.region[i]]
    return {
      rank: k + 1,
      region: reg.name,
      known: reg.known,
      lat: db.lat[i],
      lon: db.lon[i],
      score: score[i],
      similarity,
      earth_values: earthValues(db, i),
      best_match: best,
      worst_match: worst,
    }
  })

  return {
    kind: 'analogs',
    api_version: meta.api_version,
    query: {
      site: site?.id ?? null,
      site_name: site?.name ?? null,
      body,
      site_lat: site?.lat ?? null,
      site_lon: site?.lon ?? null,
      values,
      top,
      per_region: perRegion,
      min_km: minKm,
      include_known: includeKnown,
      weights,
    },
    variables_used: p.used,
    out_of_earth_range: outOfEarthRange(meta, values, [...p.used, ...(meta.switched_off?.[body] ?? [])]),
    n_candidates: idx.length,
    results,
  }
}

// ---------------------------------------------------------------------------
// 2. What does an Earth point resemble?
// ---------------------------------------------------------------------------

export function queryPoint(db: ComparatorDB, lat: number, lon: number, maxKm = 25, weights: Record<string, number> = {}): PointResponse {
  const { meta } = db
  let i = -1
  let dist = Infinity
  // Fast pre-filter on latitude (1 degree ~ 111 km), then exact distance.
  const band = maxKm / 111 + 0.1
  for (let k = 0; k < db.n; k++) {
    if (Math.abs(db.lat[k] - lat) > band) continue
    const d = haversineKm(lat, lon, db.lat[k], db.lon[k])
    if (d < dist) {
      dist = d
      i = k
    }
  }
  if (i < 0 || dist > maxKm) throw new Error(`No Earth cell of the database within ${maxKm} km of (${lat}, ${lon}). The database covers dry regions only.`)

  const sims = new Float64Array(db.features.length)
  const rows = meta.sites.map((s) => {
    const p = prepare(db, s.values, weightsFor(meta, s.body, weights))
    const sc = scoreCell(db, p, i, meta.min_coverage, sims)
    const [best, worst] = bestWorst(db.features, sims)
    const similarity: Record<string, number> = {}
    db.features.forEach((f, j) => {
      if (!Number.isNaN(sims[j])) similarity[f] = sims[j]
    })
    return {
      rank: 0,
      site: s.id,
      site_name: s.name,
      body: s.body,
      site_lat: s.lat,
      site_lon: s.lon,
      score: Number.isNaN(sc) ? null : sc,
      similarity,
      best_match: best || null,
      worst_match: worst || null,
    }
  })
  rows.sort((a, b) => (b.score ?? -1) - (a.score ?? -1))
  rows.forEach((r, k) => (r.rank = k + 1))
  const reg = meta.regions[db.region[i]]
  return {
    kind: 'point',
    api_version: meta.api_version,
    query: { lat, lon },
    cell: { lat: db.lat[i], lon: db.lon[i], distance_km: dist, region: reg.name, known: reg.known, values: earthValues(db, i) },
    results: rows,
  }
}

// ---------------------------------------------------------------------------
// 3. Export (same files as src/analog_api.py)
// ---------------------------------------------------------------------------

type Placemark = [name: string, lat: number, lon: number, props: Record<string, unknown>]

function placemarks(res: AnalogsResponse | PointResponse): Placemark[] {
  if (res.kind === 'analogs') {
    const of = res.query.site_name ?? `custom ${res.query.body} values`
    return res.results.map((r) => {
      const props: Record<string, unknown> = {
        rank: r.rank, region: r.region, known: r.known, score: r.score,
        best_match: r.best_match, worst_match: r.worst_match, analog_of: of, body: res.query.body,
      }
      for (const [k, v] of Object.entries(r.similarity)) props[`sim_${k}`] = v
      for (const [k, v] of Object.entries(r.earth_values)) props[`earth_${k}`] = v
      return [`#${r.rank} ${r.region} (score ${r.score.toFixed(3)})`, r.lat, r.lon, props]
    })
  }
  const best = res.results[0]
  const props: Record<string, unknown> = {
    region: res.cell.region, known: res.cell.known, distance_km: res.cell.distance_km,
    most_similar_site: best.site_name, score: best.score,
  }
  for (const r of res.results) props[`score_${r.site}`] = r.score
  return [[`${res.cell.region} ~ ${best.site_name} (${(best.score ?? 0).toFixed(3)})`, res.cell.lat, res.cell.lon, props]]
}

export function toGeoJSON(res: AnalogsResponse | PointResponse): string {
  const metadata =
    res.kind === 'analogs'
      ? {
          kind: res.kind, api_version: res.api_version, query: res.query, variables_used: res.variables_used,
          out_of_earth_range: res.out_of_earth_range, n_candidates: res.n_candidates,
        }
      : { kind: res.kind, api_version: res.api_version, query: res.query }
  const features = placemarks(res).map(([name, lat, lon, props]) => ({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [lon, lat] },
    properties: { name, ...props },
  }))
  return JSON.stringify({ type: 'FeatureCollection', metadata, features })
}

const xml = (s: unknown) =>
  String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

export function toKML(res: AnalogsResponse | PointResponse): string {
  const title =
    res.kind === 'analogs'
      ? `Earth analogs of ${res.query.site_name ?? 'custom values'}`
      : `Earth point ${res.query.lat}, ${res.query.lon}`
  const marks = placemarks(res)
    .map(([name, lat, lon, props]) => {
      const rows = Object.entries(props).map(([k, v]) => `<tr><td>${xml(k)}</td><td>${xml(v)}</td></tr>`).join('')
      return `<Placemark><name>${xml(name)}</name><description><![CDATA[<table>${rows}</table>]]></description><Point><coordinates>${lon},${lat},0</coordinates></Point></Placemark>`
    })
    .join('')
  return `<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>${xml(title)}</name>${marks}</Document></kml>\n`
}

/** QGC WPL 110 (Mission Planner / QGroundControl). */
export function toWaypoints(res: AnalogsResponse | PointResponse, altitudeM = 100): string {
  const lines = ['QGC WPL 110']
  placemarks(res).forEach(([, lat, lon], k) => {
    lines.push([k, k === 0 ? 1 : 0, 3, 16, 0, 0, 0, 0, lat.toFixed(6), lon.toFixed(6), altitudeM, 1].join('\t'))
  })
  return lines.join('\n') + '\n'
}
