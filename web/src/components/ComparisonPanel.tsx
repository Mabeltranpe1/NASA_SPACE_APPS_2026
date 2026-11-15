import { useMemo, useState, type MouseEvent } from 'react'
import {
  rankForTarget,
  scoreWithWeights,
  useComparisons,
  type ComparisonData,
  type ComparisonTarget,
  type FeatureMeta,
} from '../data/comparisons'
import { homologueFor, type AnalogSite, type Target } from '../data/types'
import { BODY_COLORS, SIMILARITY_COLOR } from '../theme'
import { useLang } from '../i18n/useLang'
import { BODY_NAMES, SOURCE_PHRASES_EN, type Lang } from '../i18n/strings'
import { dumbbellScale, featureLabel, makeFmt } from '../data/format'
import ScientificPanel from './ScientificPanel'
import { SCIENCE_STRINGS } from '../i18n/science'

/** Physical conditions Earth cannot reproduce. Always shown: the analogy breaks here for every site. */
type Limit = { label: string; earth: string; body: string }

const PHYSICAL_LIMITS_EN: Record<Target, Limit[]> = {
  luna: [
    { label: 'Gravity', earth: '9.81 m/s² (1 g)', body: '1.62 m/s² (0.17 g)' },
    { label: 'Atmosphere', earth: '1013 hPa', body: 'Practically a vacuum (exosphere)' },
    { label: 'Global magnetic field', earth: 'Yes: shields from radiation', body: 'No' },
    { label: 'Length of day', earth: '24 h', body: '≈ 29.5 Earth days' },
  ],
  marte: [
    { label: 'Gravity', earth: '9.81 m/s² (1 g)', body: '3.71 m/s² (0.38 g)' },
    { label: 'Atmosphere', earth: '1013 hPa, with oxygen', body: '≈ 6 hPa, 95% CO₂' },
    { label: 'Global magnetic field', earth: 'Yes: shields from radiation', body: 'No' },
    { label: 'Length of day', earth: '24 h', body: '24 h 40 min (sol)' },
  ],
}

const PHYSICAL_LIMITS: Record<Target, Limit[]> = {
  luna: [
    { label: 'Gravedad', earth: '9,81 m/s² (1 g)', body: '1,62 m/s² (0,17 g)' },
    { label: 'Atmósfera', earth: '1013 hPa', body: 'Prácticamente vacío (exosfera)' },
    { label: 'Campo magnético global', earth: 'Sí: protege de la radiación', body: 'No' },
    { label: 'Duración del día', earth: '24 h', body: '≈ 29,5 días terrestres' },
  ],
  marte: [
    { label: 'Gravedad', earth: '9,81 m/s² (1 g)', body: '3,71 m/s² (0,38 g)' },
    { label: 'Atmósfera', earth: '1013 hPa, con oxígeno', body: '≈ 6 hPa, 95 % CO₂' },
    { label: 'Campo magnético global', earth: 'Sí: protege de la radiación', body: 'No' },
    { label: 'Duración del día', earth: '24 h', body: '24 h 40 min (sol)' },
  ],
}

interface Tooltip {
  x: number
  y: number
  text: string
}

function sourceText(text: string | undefined, lang: Lang) {
  if (!text) return '—'
  return lang === 'en' ? (SOURCE_PHRASES_EN[text] ?? text) : text
}

/** Weight presets: each one keeps only the features of one kind (default weights), the rest go to 0. */
const PRESETS: { id: 'all' | 'terrain' | 'surface' | 'climate'; features: string[] | null }[] = [
  { id: 'all', features: null },
  { id: 'terrain', features: ['elev_m', 'slope_deg', 'roughness'] },
  { id: 'surface', features: ['albedo', 'ndvi', 'em_contrast'] },
  { id: 'climate', features: ['temp_mean_K', 'temp_range_K', 'precip_mm'] },
]

export interface Place {
  lat: number
  lng: number
  name: string
}

interface Props {
  site: AnalogSite
  body: Target
  /** Target whose similarity map is shown on the Earth globe (null = none). */
  mapTargetId?: string | null
  onShowMap?: (target: { id: string; name: string } | null) => void
  /** Fly the Earth globe to a place of the ranking. */
  onGoTo?: (place: Place) => void
}

export default function ComparisonPanel({ site, body, mapTargetId = null, onShowMap, onGoTo }: Props) {
  const state = useComparisons()
  const { t } = useLang()

  if (state.status === 'loading') return <section className="comparison muted-box">{t('cmp.loading')}</section>
  if (state.status === 'error') return <section className="comparison muted-box">{t('cmp.error')}</section>

  return (
    <ComparisonContent
      key={`${site.id}-${body}`}
      data={state.data}
      site={site}
      body={body}
      mapTargetId={mapTargetId}
      onShowMap={onShowMap}
      onGoTo={onGoTo}
    />
  )
}

function ComparisonContent({
  data,
  site,
  body,
  mapTargetId,
  onShowMap,
  onGoTo,
}: { data: ComparisonData } & Required<Pick<Props, 'site' | 'body'>> & Omit<Props, 'site' | 'body'>) {
  const { lang, t } = useLang()
  const fmt = makeFmt(lang)
  const bodyName = BODY_NAMES[lang][body]
  const limits = lang === 'en' ? PHYSICAL_LIMITS_EN : PHYSICAL_LIMITS
  const entry = data.sites.find((s) => s.id === site.id)
  const homologue = homologueFor(site, body)

  // Targets with computed results for this site on this body. The homologue goes first.
  const available = useMemo(() => {
    if (!entry) return []
    const ids = new Set(entry.results.map((r) => r.target))
    const list = data.targets.filter((t) => t.body === body && ids.has(t.id))
    return list.sort((a, b) => Number(b.id === homologue?.id) - Number(a.id === homologue?.id))
  }, [data, entry, body, homologue])

  const defaults = useMemo(() => Object.fromEntries(data.features.map((f) => [f.id, f.default_weight])), [data])
  const [targetId, setTargetId] = useState<string | null>(available[0]?.id ?? null)
  const [weights, setWeights] = useState<Record<string, number>>(defaults)
  const [tooltip, setTooltip] = useState<Tooltip | null>(null)

  const target = data.targets.find((t) => t.id === targetId) ?? null
  const result = entry?.results.find((r) => r.target === targetId) ?? null
  const ranking = useMemo(() => (targetId ? rankForTarget(data, targetId, weights) : []), [data, targetId, weights])

  if (!entry || !target || !result) {
    return (
      <section className="comparison muted-box">
        <h2>{t('cmp.title')}</h2>
        <p>
          {t('cmp.noData', { site: site.name, body: bodyName, homologue: homologue ? ` (${homologue.name})` : '' })}{' '}
          (<code>src/compare.py</code> → <code>src/export_web.py</code>)
        </p>
        <p className="hint">{t('cmp.noDataHint')}</p>
      </section>
    )
  }

  const usingDefaults = data.features.every((f) => weights[f.id] === f.default_weight)
  const score = scoreWithWeights(result.sim, weights)
  const position = ranking.findIndex((r) => r.site.id === site.id) + 1
  const excluded = new Set(target.excluded ?? [])
  const presetWeights = (features: string[] | null) =>
    Object.fromEntries(data.features.map((f) => [f.id, !features || features.includes(f.id) ? f.default_weight : 0]))
  const activePreset = PRESETS.find((p) => {
    const w = presetWeights(p.features)
    return data.features.every((f) => weights[f.id] === w[f.id])
  })?.id
  const mapShown = mapTargetId === target.id
  const features = data.features
  const usable = features.filter((f) => result.sim[f.id] != null && (weights[f.id] ?? 0) > 0)
  const best = usable.length ? usable.reduce((a, b) => ((result.sim[a.id] ?? 0) >= (result.sim[b.id] ?? 0) ? a : b)) : null
  const worst = usable.length ? usable.reduce((a, b) => ((result.sim[a.id] ?? 1) <= (result.sim[b.id] ?? 1) ? a : b)) : null

  const showTip = (e: MouseEvent, text: string) => {
    const box = (e.currentTarget as HTMLElement).closest('.comparison')?.getBoundingClientRect()
    if (!box) return
    setTooltip({ x: e.clientX - box.left + 12, y: e.clientY - box.top + 12, text })
  }
  const hideTip = () => setTooltip(null)

  return (
    <section className="comparison" aria-label={t('cmp.title')}>
      <header className="comparison-header">
        <div>
          <h2>{t('cmp.title')}</h2>
          <p className="pair">
            <span className="swatch" style={{ background: BODY_COLORS.tierra }} /> {site.name}{' '}
            <span className="muted">{t('cmp.versus')}</span> <span className="swatch" style={{ background: BODY_COLORS[body] }} />{' '}
            {target.name} ({bodyName})
          </p>
        </div>
        {data.synthetic && (
          <span className="synthetic-badge" title={t('cmp.syntheticTitle')}>
            {t('cmp.synthetic')}
          </span>
        )}
      </header>

      {site.caseStudy && <p className="case-note">{t('cmp.caseStudy')}</p>}

      {available.length > 1 && (
        <div className="chips target-chips" role="group" aria-label={t('cmp.targetAria')}>
          {available.map((tg: ComparisonTarget) => (
            <button key={tg.id} className={`chip ${tg.id === targetId ? 'active' : ''}`} onClick={() => setTargetId(tg.id)}>
              {tg.name}
              {tg.id === homologue?.id ? t('cmp.homologueTag') : ''}
            </button>
          ))}
        </div>
      )}

      <div className="comparison-grid">
        {/* ---------- Score + per-feature similarity ---------- */}
        <div className="card">
          <div className="hero">
            <div>
              <span className="hero-number">{score == null ? '—' : Math.round(score * 100)}</span>
              <span className="hero-unit">/ 100</span>
            </div>
            <div className="hero-meta">
              <p>
                {usingDefaults ? (
                  <>
                    <strong>{t('cmp.rank', { pos: result.rank.toLocaleString(lang), n: data.n_cells.toLocaleString(lang) })}</strong>{' '}
                    {t('cmp.rankEarth', { target: target.name })}
                  </>
                ) : (
                  <>
                    <strong>{t('cmp.rank', { pos: position, n: ranking.length })}</strong> {t('cmp.rankShown', { target: target.name })}
                  </>
                )}
              </p>
              <p className="muted">
                {usingDefaults && result.stability != null
                  ? t('cmp.stability', {
                      top: data.stability_top,
                      pct: Math.round(result.stability * 100),
                      runs: data.stability_runs,
                    })
                  : t('cmp.reweighted')}
              </p>
            </div>
          </div>

          <div className="chips presets" role="group" aria-label={t('cmp.presets')}>
            <span className="muted">{t('cmp.presets')}</span>
            {PRESETS.map((p) => (
              <button
                key={p.id}
                className={`chip ${activePreset === p.id ? 'active' : ''}`}
                aria-pressed={activePreset === p.id}
                onClick={() => setWeights(presetWeights(p.features))}
              >
                {t(`cmp.preset.${p.id}`)}
              </button>
            ))}
          </div>

          <h3>{t('cmp.similarity')}</h3>
          <ul className="meter-list">
            {features.map((f) => {
              const s = result.sim[f.id]
              const off = s == null || (weights[f.id] ?? 0) === 0
              return (
                <li key={f.id} className={off ? 'off' : ''}>
                  <span className="meter-name">{featureLabel(f, lang)}</span>
                  <span
                    className="meter-track"
                    onMouseMove={(e) =>
                      showTip(
                        e,
                        excluded.has(f.id)
                          ? t('cmp.excludedTip', { feature: featureLabel(f, lang), body: bodyName })
                          : off
                            ? t('cmp.notUsedTip', { feature: featureLabel(f, lang) })
                            : t('cmp.simTip', { feature: featureLabel(f, lang), value: fmt(s) }),
                      )
                    }
                    onMouseLeave={hideTip}
                  >
                    {!off && <span className="meter-fill" style={{ width: `${(s ?? 0) * 100}%`, background: SIMILARITY_COLOR }} />}
                  </span>
                  <span className="meter-value">{s == null ? '—' : fmt(s)}</span>
                  <span className="meter-tag">
                    {s == null && excluded.has(f.id) && <span className="tag bad">{t('cmp.excluded')}</span>}
                    {s == null && f.id === 'elev_m' && <span className="tag muted">{t('cmp.datum')}</span>}
                    {s == null && !excluded.has(f.id) && f.id !== 'elev_m' && (
                      <span className="tag muted">{t('cmp.notApplicable', { body: bodyName })}</span>
                    )}
                    {s != null && off && <span className="tag muted">{t('cmp.noWeight')}</span>}
                    {!off && f.id === best?.id && <span className="tag good">{t('cmp.best')}</span>}
                    {!off && f.id === worst?.id && <span className="tag bad">{t('cmp.worst')}</span>}
                  </span>
                </li>
              )
            })}
          </ul>

          <details className="weights">
            <summary>{t('cmp.weights')}</summary>
            {features.map((f) => (
              <label key={f.id}>
                <span>{featureLabel(f, lang)}</span>
                <input
                  type="range"
                  min={0}
                  max={3}
                  step={0.25}
                  value={weights[f.id] ?? 0}
                  onChange={(e) => setWeights((w) => ({ ...w, [f.id]: Number(e.target.value) }))}
                />
                <span className="weight-value">{(weights[f.id] ?? 0).toFixed(2)}</span>
              </label>
            ))}
            <button className="link" onClick={() => setWeights(defaults)} disabled={usingDefaults}>
              {t('cmp.resetWeights')}
            </button>
          </details>
        </div>

        {/* ---------- Real values, one scale per variable ---------- */}
        <div className="card">
          <h3>{t('cmp.values')}</h3>
          <p className="legend">
            <span>
              <span className="swatch" style={{ background: BODY_COLORS.tierra }} /> {BODY_NAMES[lang].tierra}
            </span>
            <span>
              <span className="swatch" style={{ background: BODY_COLORS[body] }} /> {bodyName}
            </span>
            <span className="muted">{t('cmp.valuesScale')}</span>
          </p>
          <ul className="dumbbells">
            {features.map((f) => (
              <Dumbbell
                key={f.id}
                feature={f}
                earth={entry.values[f.id]}
                other={target.values[f.id]}
                otherColor={BODY_COLORS[body]}
                otherLabel={bodyName}
                lang={lang}
                onTip={showTip}
                onLeave={hideTip}
              />
            ))}
          </ul>
        </div>

        {/* ---------- Ranking ---------- */}
        <div className="card">
          <h3>{t('cmp.ranking', { target: target.name })}</h3>
          <p className="hint">{t('cmp.rankingNote')}</p>
          <ol className="ranking">
            {ranking.slice(0, 10).map((r, i) => {
              const current = r.site.id === site.id
              const tag = r.site.kind === 'discovery' ? t('cmp.discovery') : r.site.known ? t('cmp.known') : null
              return (
                <li
                  key={r.site.id}
                  className={current ? 'current' : ''}
                  onMouseMove={(e) =>
                    showTip(e, `${r.site.name}: ${Math.round((r.score ?? 0) * 100)} / 100${r.site.note ? ` · ${r.site.note}` : ''}`)
                  }
                  onMouseLeave={hideTip}
                >
                  <span className="rank-pos">{i + 1}</span>
                  <span className="rank-name">
                    {onGoTo ? (
                      <button
                        className="link"
                        title={t('cmp.goTo')}
                        onClick={() => onGoTo({ lat: r.site.lat, lng: r.site.lng, name: r.site.name })}
                      >
                        {r.site.name}
                      </button>
                    ) : (
                      r.site.name
                    )}
                    {tag && <small> · {tag}</small>}
                  </span>
                  <span className="rank-track">
                    <span
                      className="rank-fill"
                      style={{ width: `${(r.score ?? 0) * 100}%`, background: current ? SIMILARITY_COLOR : '#3a4560' }}
                    />
                  </span>
                  <span className="rank-value">{Math.round((r.score ?? 0) * 100)}</span>
                </li>
              )
            })}
          </ol>
          {onShowMap && (
            <button
              className={`map-toggle ${mapShown ? 'active' : ''}`}
              aria-pressed={mapShown}
              onClick={() => onShowMap(mapShown ? null : { id: target.id, name: target.name })}
            >
              {mapShown ? t('cmp.hideMap') : t('cmp.showMap')}
            </button>
          )}
        </div>

        {/* ---------- Limits + sources ---------- */}
        <div className="card">
          <h3>{t('cmp.limits')}</h3>
          <table className="limits">
            <thead>
              <tr>
                <th />
                <th>{BODY_NAMES[lang].tierra}</th>
                <th>{bodyName}</th>
              </tr>
            </thead>
            <tbody>
              {limits[body].map((l) => (
                <tr key={l.label}>
                  <th scope="row">{l.label}</th>
                  <td>{l.earth}</td>
                  <td>{l.body}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h3>{t('cmp.sources')}</h3>
          <ul className="sources">
            {features.map((f) => (
              <li key={f.id}>
                <strong>{featureLabel(f, lang)}:</strong> {sourceText(f.source_earth, lang)}{' '}
                <span className="muted">{t('cmp.versus')}</span> {sourceText(f.source_target[body], lang)}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <details className="data-table">
        <summary>{t('cmp.table')}</summary>
        <table>
          <thead>
            <tr>
              <th>{t('cmp.variable')}</th>
              <th>{BODY_NAMES[lang].tierra}</th>
              <th>{bodyName}</th>
              <th>{t('cmp.similarity')}</th>
              <th>{t('cmp.weight')}</th>
            </tr>
          </thead>
          <tbody>
            {features.map((f) => (
              <tr key={f.id}>
                <th scope="row">{featureLabel(f, lang)}</th>
                <td>{fmt(entry.values[f.id], f.unit)}</td>
                <td>{fmt(target.values[f.id], f.unit)}</td>
                <td>{fmt(result.sim[f.id])}</td>
                <td>{(weights[f.id] ?? 0).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted">
          {t('cmp.generated', { date: new Date(data.generated_at).toLocaleString(lang), n: data.n_cells })}
        </p>
      </details>

      {target.science_refs && target.science_refs.length > 0 && (
        <section className="science-related">
          <h3>{SCIENCE_STRINGS[lang].related}</h3>
          <p className="hint">{SCIENCE_STRINGS[lang].reference}</p>
          {target.science_refs.map((reference) => <ScientificPanel key={reference.url} reference={reference} />)}
        </section>
      )}

      {tooltip && (
        <div className="chart-tooltip" style={{ left: tooltip.x, top: tooltip.y }} role="status">
          {tooltip.text}
        </div>
      )}
    </section>
  )
}

function Dumbbell({
  feature,
  earth,
  other,
  otherColor,
  otherLabel,
  lang,
  onTip,
  onLeave,
}: {
  feature: FeatureMeta
  earth: number | null
  other: number | null
  otherColor: string
  otherLabel: string
  lang: Lang
  onTip: (e: MouseEvent, text: string) => void
  onLeave: () => void
}) {
  const fmt = makeFmt(lang)
  const label = featureLabel(feature, lang)
  const earthName = BODY_NAMES[lang].tierra
  if (earth == null || other == null) {
    return (
      <li className="dumbbell off">
        <span className="dumbbell-name">{label}</span>
        <span className="muted">
          {other == null
            ? lang === 'en'
              ? `Not applicable on ${otherLabel}`
              : `No aplica en ${otherLabel}`
            : lang === 'en'
              ? 'No Earth data'
              : 'Sin dato en la Tierra'}
        </span>
      </li>
    )
  }
  // Fixed physical axis so the distance between the two dots means something.
  const { lo, hi, earth: pe, other: po } = dumbbellScale(feature, earth, other)
  const tip = `${label}: ${earthName} ${fmt(earth, feature.unit)} · ${otherLabel} ${fmt(other, feature.unit)}`

  return (
    <li className="dumbbell" onMouseMove={(e) => onTip(e, tip)} onMouseLeave={onLeave} aria-label={tip}>
      <span className="dumbbell-name">
        {label}
        {feature.unit && <small> ({feature.unit})</small>}
      </span>
      <span className="dumbbell-plot">
        <span className="dumbbell-axis" />
        <span className="dumbbell-link" style={{ left: `${Math.min(pe, po)}%`, width: `${Math.abs(pe - po)}%` }} />
        <span className="dumbbell-dot" style={{ left: `${pe}%`, background: BODY_COLORS.tierra }} />
        <span className="dumbbell-dot" style={{ left: `${po}%`, background: otherColor }} />
        <span className="dumbbell-tick start">{fmt(lo)}</span>
        <span className="dumbbell-tick end">{fmt(hi)}</span>
      </span>
      <span className="dumbbell-values">
        {fmt(earth)} · {fmt(other)}
      </span>
    </li>
  )
}
