/**
 * Runs the browser comparator (src/comparator/compare.ts) in Node on the exported database and
 * prints the answers as JSON. tests/test_web_port.py compares them with src/analog_api.py.
 *
 *   node --experimental-strip-types web/scripts/check-comparator.ts cases.json > js_answers.json
 *
 * cases.json: {"find": [FindOptions, ...], "point": [[lat, lon], ...]}
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { findAnalogs, parseComparator, queryPoint, toGeoJSON, toKML, toWaypoints, type ComparatorMeta } from '../src/comparator/compare.ts'

const dir = fileURLToPath(new URL('../public/data/comparator/', import.meta.url))
const meta = JSON.parse(readFileSync(dir + 'comparator.json', 'utf8')) as ComparatorMeta
const db = await parseComparator(meta, new Uint8Array(readFileSync(dir + 'earth.bin')))
const cases = JSON.parse(readFileSync(process.argv[2], 'utf8'))

const t0 = performance.now()
const find = cases.find.map((c: Parameters<typeof findAnalogs>[1]) => findAnalogs(db, c))
const ms = (performance.now() - t0) / Math.max(1, cases.find.length)
const point = cases.point.map(([lat, lon]: [number, number]) => queryPoint(db, lat, lon))
// The exporters must at least produce valid output.
JSON.parse(toGeoJSON(find[0]))
if (!toKML(find[0]).includes('<Placemark>') || !toWaypoints(point[0]).startsWith('QGC WPL 110')) throw new Error('export failed')
console.log(JSON.stringify({ find, point, ms_per_search: ms }))
