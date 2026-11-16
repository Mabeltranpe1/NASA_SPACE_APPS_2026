/**
 * Mission types: what a place on Earth would be good for as an analog.
 *
 * Each mission is a weight PROFILE over the same variables the comparator already uses. It does
 * not add data and does not change the score formula: the weights of a mission are the model
 * weights of the body (comparator.json, so elevation stays 0 and the variables Earth cannot reach
 * stay switched off) multiplied by the mission's factors below.
 *
 *   - As a filter, the mission's weights go into findAnalogs, so the ranking is "most similar for
 *     this kind of test".
 *   - "Suitable for" is the same score recomputed with every mission's weights from the per-variable
 *     similarity of a result (similarity_f = exp(-|d_f|), so |d_f| = -ln(similarity_f)). It equals
 *     findAnalogs with those weights (checked in web/scripts/check-missions.ts). Missions are ranked
 *     by how close that score is to the best Earth has for the mission (missionReference).
 *
 * Rock type (em_contrast) is only a proxy for composition. There are no layers for dust, ice, caves
 * or lighting, so no mission pretends to measure them.
 *
 * No React and no DOM here: this file also runs in Node.
 */
import { sampleScores, type Body, type ComparatorDB, type ComparatorMeta, type Values } from './compare.ts'

export type MissionId = 'rover' | 'isru' | 'habitat' | 'thermal' | 'science' | 'drone' | 'landing'

/** Factor per variable (multiplies the model weight). Never 0, so every variable still counts a bit. */
export type MissionProfile = Record<string, number>

export const MISSION_IDS: MissionId[] = ['rover', 'isru', 'habitat', 'thermal', 'science', 'drone', 'landing']

export const MISSION_PROFILES: Record<MissionId, MissionProfile> = {
  // Wheels care about slopes and rocks first, then the kind of ground they drive on.
  rover: { slope_deg: 2, roughness: 3, temp_mean_K: 0.5, temp_range_K: 1, albedo: 0.5, precip_mm: 1, ndvi: 1, em_contrast: 1.5 },
  // Mining / in-situ resources: the rock and the surface it makes; terrain matters less.
  isru: { slope_deg: 1, roughness: 0.5, temp_mean_K: 0.5, temp_range_K: 0.5, albedo: 2, precip_mm: 1, ndvi: 1, em_contrast: 3 },
  // People living in a habitat: cold, big day/night swings, dryness and isolation (no vegetation).
  habitat: { slope_deg: 1.5, roughness: 1, temp_mean_K: 2.5, temp_range_K: 2.5, albedo: 0.5, precip_mm: 2, ndvi: 1.5, em_contrast: 0.5 },
  // Equipment that must survive the thermal environment: temperature and how much sun the ground reflects.
  thermal: { slope_deg: 0.25, roughness: 0.25, temp_mean_K: 3, temp_range_K: 3, albedo: 2, precip_mm: 1, ndvi: 0.5, em_contrast: 0.25 },
  // Science / astrobiology: same kind of rock, as dry and lifeless as possible.
  science: { slope_deg: 0.5, roughness: 0.5, temp_mean_K: 1, temp_range_K: 1, albedo: 1, precip_mm: 3, ndvi: 3, em_contrast: 2.5 },
  // Drones / flight: optical navigation needs similar brightness and relief; temperature for batteries.
  drone: { slope_deg: 1, roughness: 2, temp_mean_K: 1, temp_range_K: 1.5, albedo: 2.5, precip_mm: 1, ndvi: 1, em_contrast: 0.5 },
  // Landing and launch pads for rockets / capsules: flat and smooth above everything else.
  landing: { slope_deg: 3, roughness: 3, temp_mean_K: 0.25, temp_range_K: 0.5, albedo: 0.5, precip_mm: 0.5, ndvi: 1, em_contrast: 0.25 },
}

/**
 * Variables a mission cannot do without. If all of them are switched off for a body (the Moon's
 * temperature: no place on Earth reaches it), the mission is not offered for that body, because its
 * score would be decided by other variables than the ones it is about.
 */
export const MISSION_REQUIRES: Partial<Record<MissionId, string[]>> = {
  thermal: ['temp_mean_K', 'temp_range_K'],
}

/** A mission's weights (missionWeights) still contain the variables it cannot do without. */
export function missionAvailable(weights: Record<string, number>, mission: MissionId) {
  const need = MISSION_REQUIRES[mission]
  return !need || need.some((f) => (weights[f] ?? 0) > 0)
}

/**
 * Variables a mission weighs a lot (factor >= 2) but that are switched off for this body, e.g. the
 * temperature of "habitats" on the Moon. The app warns about them.
 */
export function switchedOffFor(weights: Record<string, number>, mission: MissionId) {
  return Object.entries(MISSION_PROFILES[mission])
    .filter(([f, factor]) => factor >= 2 && !((weights[f] ?? 0) > 0))
    .map(([f]) => f)
}

/** Highest weight a slider shows (AnalogFinder's range input goes 0..3). */
const MAX_WEIGHT = 3

/**
 * Weights of a mission for a body: model weight x mission factor, scaled so the biggest is 3.
 * Scaling all weights by the same number does not change the score (it is a weighted mean).
 */
export function missionWeights(meta: ComparatorMeta, body: Body, mission: MissionId): Record<string, number> {
  const base = meta.weights[body]
  const profile = MISSION_PROFILES[mission]
  const w: Record<string, number> = {}
  let max = 0
  for (const f of Object.keys(base)) {
    w[f] = base[f] * (profile[f] ?? 1)
    max = Math.max(max, w[f])
  }
  if (max > MAX_WEIGHT) for (const f of Object.keys(w)) w[f] = (w[f] * MAX_WEIGHT) / max
  return w
}

/**
 * Score of a place with other weights, from its per-variable similarity (same formula as
 * compare.ts scoreCell: exp(-sqrt(sum w d^2 / sum w))). Variables without similarity do not count.
 */
export function scoreFromSimilarity(similarity: Record<string, number>, weights: Record<string, number>): number | null {
  let num = 0
  let den = 0
  for (const [f, s] of Object.entries(similarity)) {
    const w = weights[f] ?? 0
    if (!(w > 0) || !(s > 0)) continue
    const d = -Math.log(s)
    num += w * d * d
    den += w
  }
  return den > 0 ? Math.exp(-Math.sqrt(num / den)) : null
}

/**
 * Best score of each mission over an even sample of Earth (every `step`-th cell) for one target.
 * It is the yardstick for "suitable for": a place is suited to a mission when it comes close to the
 * best Earth has for that mission, not just when its mission score is high (flat, dry places score
 * high on terrain for almost every target, so raw scores would always say "rovers" and "landing").
 * For the known sites it is precomputed with step = 1 in public/data/missions.json (export-missions.ts).
 */
export function missionReference(db: ComparatorDB, values: Values, body: Body, step = 10): Record<MissionId, number> {
  const ref = {} as Record<MissionId, number>
  for (const m of MISSION_IDS) {
    let best = 0
    for (const s of sampleScores(db, values, missionWeights(db.meta, body, m), step)) if (s > best) best = s
    ref[m] = best
  }
  return ref
}

export interface MissionFit {
  mission: MissionId
  /** Score of the place with the mission's weights (0..1, same formula as the ranking). */
  score: number
  /** score / best score Earth has for this mission (missionReference); can pass 1 a little. */
  relative: number
}

/** Every mission's fit for one place, best first (by `relative` when a reference is given). */
export function missionFits(
  meta: ComparatorMeta, body: Body, similarity: Record<string, number>, ref?: Record<MissionId, number>,
): MissionFit[] {
  const weights = {} as Record<MissionId, Record<string, number>>
  for (const m of MISSION_IDS) weights[m] = missionWeights(meta, body, m)
  return fitsWithWeights(weights, similarity, ref)
}

/** Same as missionFits with the weights already computed (public/data/missions.json). */
export function fitsWithWeights(
  weights: Record<MissionId, Record<string, number>>, similarity: Record<string, number | null>, ref?: Record<MissionId, number>,
): MissionFit[] {
  const sim: Record<string, number> = {}
  for (const [f, v] of Object.entries(similarity)) if (v != null) sim[f] = v
  const out: MissionFit[] = []
  for (const m of MISSION_IDS) {
    if (!weights[m] || !missionAvailable(weights[m], m)) continue
    const s = scoreFromSimilarity(sim, weights[m])
    if (s != null) out.push({ mission: m, score: s, relative: ref?.[m] ? s / ref[m] : s })
  }
  return out.sort((a, b) => b.relative - a.relative || MISSION_IDS.indexOf(a.mission) - MISSION_IDS.indexOf(b.mission))
}

/** A place is "suitable for" a mission only if it reaches this share of the best place on Earth for it. */
export const SUITABLE_MIN = 0.5

/**
 * The 2-3 missions a place is best suited for ("suitable for" badge): the best two, and the third
 * only when it is close to the second (within 0.03). Missions below SUITABLE_MIN of the best place
 * on Earth are never suggested, so a poor match gets no badge instead of a misleading one.
 */
export function topMissions(fits: MissionFit[], closeTo = 0.03, minRelative = SUITABLE_MIN): MissionFit[] {
  const good = fits.filter((f) => f.relative >= minRelative)
  const top = good.slice(0, 2)
  if (good.length > 2 && good[1].relative - good[2].relative <= closeTo) top.push(good[2])
  return top
}
