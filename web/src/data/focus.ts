import type { ComparisonData, ComparisonResult, ComparisonSite, ComparisonTarget, RankingId } from './comparisons'
import { homologueFor, siteTargets, type AnalogSite, type Body, type Target } from './types'
import type { Lang } from '../i18n/strings'

/** A place of the worldwide search with its best Moon/Mars target. */
export interface Discovery {
  site: ComparisonSite
  target: ComparisonTarget
  /** Score of the list it comes from: overall, or one dimension. */
  score: number
}

/**
 * Ranked places for a body, best first: the overall list or the best analogs
 * of one dimension (src/export_web.py, rules 3 and 4).
 */
export function discoveriesFor(data: ComparisonData, body: Target, limit = Infinity, list: RankingId = 'general'): Discovery[] {
  const ranked = data.rankings?.[body]?.[list]
  if (ranked) {
    const sites = new Map(data.sites.map((s) => [s.id, s]))
    const targets = new Map(data.targets.map((tg) => [tg.id, tg]))
    const out: Discovery[] = []
    for (const p of ranked) {
      const site = sites.get(p.site)
      const target = targets.get(p.target)
      if (site && target) out.push({ site, target, score: p.score })
      if (out.length >= limit) break
    }
    return out
  }
  // Older data files without rankings: best place of each region.
  const targets = new Map(data.targets.filter((tg) => tg.body === body).map((tg) => [tg.id, tg]))
  const best = new Map<string, Discovery>()
  for (const site of data.sites) {
    if (site.kind !== 'discovery' || !site.region) continue
    for (const r of site.results) {
      const target = targets.get(r.target)
      if (!target || r.score == null) continue
      const prev = best.get(site.region)
      if (!prev || r.score > prev.score) best.set(site.region, { site, target, score: r.score })
    }
  }
  return [...best.values()].sort((a, b) => b.score - a.score).slice(0, limit)
}

/** Name of a place of the database in the current language. */
export function placeName(site: ComparisonSite, lang: Lang) {
  return (lang === 'en' ? site.name_en : undefined) ?? site.name
}

export function placeCountry(site: ComparisonSite, lang: Lang) {
  return (lang === 'en' ? site.country_en : site.country) ?? ''
}

/**
 * A discovery seen as a site of the app, so the site card, the close-up images
 * and the detailed comparison work the same way for both.
 */
export function discoveryAsSite(d: Discovery, lang: Lang = 'es'): AnalogSite {
  return {
    id: d.site.id,
    name: placeName(d.site, lang),
    country: placeCountry(d.site, lang) || (d.site.note ?? ''),
    lat: d.site.lat,
    lng: d.site.lng,
    environments: [],
    homologues:
      d.target.lat != null && d.target.lng != null
        ? [{ id: d.target.id, body: d.target.body, name: d.target.name, lat: d.target.lat, lng: d.target.lng, note: '' }]
        : [],
    analogOf: d.target.name,
    dimensions: {},
    similarities: '',
    limitations: '',
    missionUse: '',
    wellKnown: Boolean(d.site.known),
    region: d.site.region,
  }
}

/** Bodies where a place can be shown: Earth plus the bodies of its counterparts. */
export function bodiesOf(site: AnalogSite | null): Body[] {
  return site ? ['tierra', ...siteTargets(site)] : ['tierra', 'luna', 'marte']
}

export function googleEarthUrl(lat: number, lng: number) {
  return `https://earth.google.com/web/@${lat},${lng},1000a,20000d,35y,0h,45t,0r`
}

/**
 * Target used to compare a place with one body: its counterpart when it is in
 * the database, otherwise the most similar target of that body.
 * Same rule in the right panel, the detailed analysis and the site list.
 */
export function comparedTarget(data: ComparisonData, site: AnalogSite, body: Target) {
  const entry = data.sites.find((s) => s.id === site.id)
  const results = entry?.results ?? []
  const homologue = homologueFor(site, body)
  const ofBody = new Set(data.targets.filter((tg) => tg.body === body).map((tg) => tg.id))
  const result =
    results.find((r) => r.target === homologue?.id) ??
    results.filter((r) => ofBody.has(r.target)).sort((a, b) => (b.score ?? -1) - (a.score ?? -1))[0]
  const target = result ? data.targets.find((tg) => tg.id === result.target) : undefined
  return { target, result }
}

/** Score of a result for a list: the overall score or one dimension (null = not comparable). */
export function resultScore(result: ComparisonResult | undefined, list: RankingId = 'general') {
  if (!result) return null
  return list === 'general' ? result.score : (result.dims?.[list] ?? null)
}

/** Best similarity (0..1) of a place with any of its counterparts, and with which body. */
export function bestScore(
  data: ComparisonData,
  site: AnalogSite,
  list: RankingId = 'general',
): { score: number; body: Target } | null {
  let best: { score: number; body: Target } | null = null
  for (const body of siteTargets(site)) {
    const score = resultScore(comparedTarget(data, site, body).result, list)
    if (score != null && (!best || score > best.score)) best = { score, body }
  }
  return best
}
