import { useState } from 'react'
import type { ComparisonData } from '../data/comparisons'
import type { Discovery } from '../data/focus'
import { useGlobalRankings } from '../data/science'
import { useLang } from '../i18n/useLang'
import { SCIENCE_STRINGS } from '../i18n/science'

export default function GlobalRankings({ data, onSelect }: { data: ComparisonData; onSelect: (d: Discovery) => void }) {
  const state = useGlobalRankings()
  const { lang } = useLang()
  const copy = SCIENCE_STRINGS[lang]
  const [body, setBody] = useState<'Moon' | 'Mars'>('Mars')
  const [all, setAll] = useState(false)
  if (state.status === 'error') return <p role="alert">{copy.error}</p>
  if (state.status !== 'ready') return <p role="status">{copy.loading}</p>
  const rows = state.data.rows.filter((r) => r.body === body)
  return <section className="science-global card" aria-label={copy.globalTitle}>
    <h2>{copy.globalTitle}</h2>
    <p className="science-note">{copy.globalNote}</p>
    <p>{state.data.n_cells.toLocaleString(lang)} {copy.globalCells} · {state.data.n_regions.toLocaleString(lang)} {copy.globalRegions}</p>
    <div className="chips" role="group"><button className={`chip ${body === 'Mars' ? 'active' : ''}`} aria-pressed={body === 'Mars'} onClick={() => setBody('Mars')}>{copy.mars}</button><button className={`chip ${body === 'Moon' ? 'active' : ''}`} aria-pressed={body === 'Moon'} onClick={() => setBody('Moon')}>{copy.moon}</button></div>
    <div className="science-table-scroll"><table><thead><tr><th>#</th><th>{copy.region}</th><th>{copy.globalMean}</th><th>{copy.globalBest}</th><th>{copy.target}</th><th /></tr></thead><tbody>
      {(all ? rows : rows.slice(0, 10)).map((row) => {
        const site = data.sites.find((s) => s.id === row.site_id)
        const target = data.targets.find((t) => t.id === row.target_id)
        const score = site?.results.find((r) => r.target === target?.id)?.score
        return <tr key={`${row.body}-${row.rank}`}><td>{row.rank}</td><th scope="row"><strong>{row.earth_region.replaceAll('_', ' ')}</strong><small>{row.earth_lat.toFixed(3)}°, {row.earth_lon.toFixed(3)}°</small></th><td>{row.mean_score_all_sites.toFixed(4)}</td><td>{row.score_best_site.toFixed(4)}</td><td>{row.best_site}</td><td><button className="link" disabled={!site || !target} onClick={() => { if (site && target) onSelect({ site, target, score: score ?? 0 }) }}>{copy.openMap}</button></td></tr>
      })}
    </tbody></table></div>
    <button className="link" aria-expanded={all} onClick={() => setAll(!all)}>{all ? copy.showLess : `${copy.showAll} (${rows.length})`}</button>
  </section>
}
