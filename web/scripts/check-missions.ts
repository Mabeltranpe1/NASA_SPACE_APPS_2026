/**
 * Checks the mission filters (src/comparator/missions.ts) against the browser comparator:
 *   1. findAnalogs with a mission's weights gives the same score as scoreFromSimilarity
 *      (so the "suitable for" badge is the real score with that mission's weights);
 *   2. elevation stays at 0 and the variables switched off for a body stay off;
 *   3. public/data/missions.json is up to date (same weights; its best-on-Earth reference is at
 *      least every score the comparator finds), otherwise run export-missions.ts;
 *   4. prints how often each mission is in a place's top 2-3, to spot a profile that never wins.
 *
 *   node --experimental-strip-types web/scripts/check-missions.ts
 *
 * Run by tests/test_missions.py. Exits with code 1 on a failure.
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { findAnalogs, parseComparator, type ComparatorMeta } from '../src/comparator/compare.ts'
import { MISSION_IDS, missionFits, missionReference, missionWeights, scoreFromSimilarity, topMissions } from '../src/comparator/missions.ts'

const dir = fileURLToPath(new URL('../public/data/comparator/', import.meta.url))
const meta = JSON.parse(readFileSync(dir + 'comparator.json', 'utf8')) as ComparatorMeta
const db = await parseComparator(meta, new Uint8Array(readFileSync(dir + 'earth.bin')))

const failures: string[] = []
let checked = 0
let maxErr = 0
const wins: Record<string, number> = Object.fromEntries(MISSION_IDS.map((m) => [m, 0]))

for (const body of ['Moon', 'Mars'] as const) {
  for (const m of MISSION_IDS) {
    const w = missionWeights(meta, body, m)
    if ((w.elev_m ?? 0) !== 0) failures.push(`${body}/${m}: elev_m weight is ${w.elev_m}`)
    for (const f of meta.switched_off?.[body] ?? []) if (w[f] !== 0) failures.push(`${body}/${m}: ${f} should stay off`)
    if (Math.max(...Object.values(w)) > 3 + 1e-12) failures.push(`${body}/${m}: weight above 3`)
  }
}

const file = JSON.parse(readFileSync(fileURLToPath(new URL('../public/data/missions.json', import.meta.url)), 'utf8'))
for (const body of ['Moon', 'Mars'] as const)
  for (const m of MISSION_IDS)
    for (const [f, w] of Object.entries(missionWeights(meta, body, m)))
      if (Math.abs((file.weights[body]?.[m]?.[f] ?? NaN) - w) > 1e-6) failures.push(`missions.json is stale: ${body}/${m}/${f} (run export-missions.ts)`)
for (const s of meta.sites) if (!file.reference[s.id]) failures.push(`missions.json has no reference for ${s.id} (run export-missions.ts)`)

const sites = meta.sites.filter((s, i) => i % 3 === 0)
for (const s of sites) {
  // Model weights: where do the "suitable for" badges land?
  const base = findAnalogs(db, { site: s.id, top: 10 })
  const ref = missionReference(db, base.query.values, s.body)
  for (const r of base.results) for (const f of topMissions(missionFits(meta, s.body, r.similarity, ref))) wins[f.mission]++
  // Mission filter: the badge formula must equal the comparator with the same weights.
  for (const m of MISSION_IDS) {
    const res = findAnalogs(db, { site: s.id, top: 5, weights: missionWeights(meta, s.body, m) })
    for (const r of res.results) {
      const again = scoreFromSimilarity(r.similarity, res.query.weights)
      const err = again == null ? Infinity : Math.abs(again - r.score)
      maxErr = Math.max(maxErr, err)
      checked++
      if (r.rank === 1 && Math.abs(file.reference[s.id]?.[m] - r.score) > 1e-6 && !res.query.include_known && r.score > file.reference[s.id]?.[m])
        failures.push(`${s.id}/${m}: comparator found ${r.score} above missions.json ${file.reference[s.id]?.[m]}`)
      if (err > 1e-9) failures.push(`${s.id}/${m} #${r.rank}: ${r.score} vs ${again}`)
    }
  }
}

console.log(JSON.stringify({ sites: sites.length, checked, max_error: maxErr, top_mission_counts: wins, failures }, null, 1))
if (failures.length) process.exit(1)
