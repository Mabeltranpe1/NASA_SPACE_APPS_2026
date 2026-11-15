import type { ComparisonData, ComparisonSite, ComparisonTarget } from './comparisons'
import { homologueFor, siteTargets, type AnalogSite, type Body, type Target } from './types'

/** Best Earth cell of one little-known region for one Moon/Mars body (global search). */
export interface Discovery {
  site: ComparisonSite
  target: ComparisonTarget
  score: number
}

/** Best place of each little-known region for a body, best first. */
export function discoveriesFor(data: ComparisonData, body: Target, limit = 8): Discovery[] {
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

/**
 * A discovery seen as a site of the app, so the site card, the close-up images
 * and the detailed comparison work the same way for both.
 */
export function discoveryAsSite(d: Discovery): AnalogSite {
  return {
    id: d.site.id,
    name: d.site.name,
    country: d.site.note ?? '',
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
 * the database, otherwise the first target of that body with a result.
 * Same rule in the right panel, the detailed analysis and the site list.
 */
export function comparedTarget(data: ComparisonData, site: AnalogSite, body: Target) {
  const entry = data.sites.find((s) => s.id === site.id)
  const withResult = new Set(entry?.results.map((r) => r.target) ?? [])
  const homologue = homologueFor(site, body)
  const target =
    data.targets.find((tg) => tg.id === homologue?.id && withResult.has(tg.id)) ??
    data.targets.find((tg) => tg.body === body && withResult.has(tg.id))
  const result = target ? entry?.results.find((r) => r.target === target.id) : undefined
  return { target, result }
}

/** Best similarity (0..1) of a place with any of its counterparts, and with which body. */
export function bestScore(data: ComparisonData, site: AnalogSite): { score: number; body: Target } | null {
  let best: { score: number; body: Target } | null = null
  for (const body of siteTargets(site)) {
    const score = comparedTarget(data, site, body).result?.score
    if (score != null && (!best || score > best.score)) best = { score, body }
  }
  return best
}
