import { useMemo, useState, type MouseEvent } from 'react'
import {
  rankForTarget,
  scoreWithWeights,
  useComparisons,
  type ComparisonData,
  type ComparisonTarget,
  type FeatureMeta,
} from '../data/comparisons'
import { BODY_LABELS, homologueFor, type AnalogSite, type Target } from '../data/types'
import { BODY_COLORS, SIMILARITY_COLOR } from '../theme'

/** Physical conditions Earth cannot reproduce. Always shown: the analogy breaks here for every site. */
const PHYSICAL_LIMITS: Record<Target, { label: string; earth: string; body: string }[]> = {
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

function fmt(value: number | null | undefined, unit = '') {
  if (value == null) return '—'
  const abs = Math.abs(value)
  const digits = abs >= 100 ? 0 : abs >= 10 ? 1 : 2
  return `${value.toLocaleString('es', { maximumFractionDigits: digits })}${unit ? ` ${unit}` : ''}`
}

interface Props {
  site: AnalogSite
  body: Target
}

export default function ComparisonPanel({ site, body }: Props) {
  const state = useComparisons()

  if (state.status === 'loading') return <section className="comparison muted-box">Cargando datos de comparación…</section>
  if (state.status === 'error')
    return <section className="comparison muted-box">No se pudieron cargar los datos de comparación.</section>

  return <ComparisonContent key={`${site.id}-${body}`} data={state.data} site={site} body={body} />
}

function ComparisonContent({ data, site, body }: { data: ComparisonData; site: AnalogSite; body: Target }) {
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
        <h2>Comparación detallada</h2>
        <p>
          Aún no hay datos calculados para <strong>{site.name}</strong> frente a {BODY_LABELS[body]}
          {homologue ? ` (${homologue.name})` : ''}. Se generarán con el pipeline de datos (<code>src/compare.py</code> →{' '}
          <code>src/export_web.py</code>).
        </p>
        <p className="hint">
          Con los datos de muestra actuales, prueba con <strong>Cráter Haughton</strong>, <strong>Atacama</strong>,{' '}
          <strong>McMurdo</strong> o <strong>Mauna Kea</strong>.
        </p>
      </section>
    )
  }

  const usingDefaults = data.features.every((f) => weights[f.id] === f.default_weight)
  const score = scoreWithWeights(result.sim, weights)
  const position = ranking.findIndex((r) => r.site.id === site.id) + 1
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
    <section className="comparison" aria-label="Comparación detallada">
      <header className="comparison-header">
        <div>
          <h2>Comparación detallada</h2>
          <p className="pair">
            <span className="swatch" style={{ background: BODY_COLORS.tierra }} /> {site.name} <span className="muted">frente a</span>{' '}
            <span className="swatch" style={{ background: BODY_COLORS[body] }} /> {target.name} ({BODY_LABELS[body]})
          </p>
        </div>
        {data.synthetic && (
          <span className="synthetic-badge" title="Valores inventados para probar la visualización; no son mediciones reales">
            ⚠ Datos de muestra sintéticos
          </span>
        )}
      </header>

      {available.length > 1 && (
        <div className="chips target-chips" role="group" aria-label="Objetivo de la comparación">
          {available.map((t: ComparisonTarget) => (
            <button key={t.id} className={`chip ${t.id === targetId ? 'active' : ''}`} onClick={() => setTargetId(t.id)}>
              {t.name}
              {t.id === homologue?.id ? ' · homólogo' : ''}
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
                <strong>
                  #{position} de {ranking.length}
                </strong>{' '}
                lugares para {target.name}
              </p>
              <p className="muted">
                {usingDefaults && result.stability != null
                  ? `En el top ${data.stability_top} en el ${Math.round(result.stability * 100)} % de ${data.stability_runs} variaciones de pesos`
                  : 'Recalculado con tus pesos'}
              </p>
            </div>
          </div>

          <h3>Similitud por característica</h3>
          <ul className="meter-list">
            {features.map((f) => {
              const s = result.sim[f.id]
              const off = s == null || (weights[f.id] ?? 0) === 0
              return (
                <li key={f.id} className={off ? 'off' : ''}>
                  <span className="meter-name">{f.label}</span>
                  <span
                    className="meter-track"
                    onMouseMove={(e) => showTip(e, off ? `${f.label}: no se usa` : `${f.label}: similitud ${fmt(s)} (1 = idénticos)`)}
                    onMouseLeave={hideTip}
                  >
                    {!off && <span className="meter-fill" style={{ width: `${(s ?? 0) * 100}%`, background: SIMILARITY_COLOR }} />}
                  </span>
                  <span className="meter-value">{s == null ? '—' : fmt(s)}</span>
                  <span className="meter-tag">
                    {s == null && <span className="tag muted">no aplica en {BODY_LABELS[body]}</span>}
                    {s != null && off && <span className="tag muted">sin peso</span>}
                    {!off && f.id === best?.id && <span className="tag good">✓ más parecido</span>}
                    {!off && f.id === worst?.id && <span className="tag bad">⚠ rompe la analogía</span>}
                  </span>
                </li>
              )
            })}
          </ul>

          <details className="weights">
            <summary>Ajustar pesos (qué importa más)</summary>
            {features.map((f) => (
              <label key={f.id}>
                <span>{f.label}</span>
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
              Restaurar pesos del modelo
            </button>
          </details>
        </div>

        {/* ---------- Real values, one scale per variable ---------- */}
        <div className="card">
          <h3>Valores reales</h3>
          <p className="legend">
            <span>
              <span className="swatch" style={{ background: BODY_COLORS.tierra }} /> Tierra
            </span>
            <span>
              <span className="swatch" style={{ background: BODY_COLORS[body] }} /> {BODY_LABELS[body]}
            </span>
            <span className="muted">Escala física fija por variable</span>
          </p>
          <ul className="dumbbells">
            {features.map((f) => (
              <Dumbbell
                key={f.id}
                feature={f}
                earth={entry.values[f.id]}
                other={target.values[f.id]}
                otherColor={BODY_COLORS[body]}
                otherLabel={BODY_LABELS[body]}
                onTip={showTip}
                onLeave={hideTip}
              />
            ))}
          </ul>
        </div>

        {/* ---------- Ranking ---------- */}
        <div className="card">
          <h3>Mejores lugares de la Tierra para {target.name}</h3>
          <ol className="ranking">
            {ranking.slice(0, 8).map((r, i) => {
              const current = r.site.id === site.id
              return (
                <li
                  key={r.site.id}
                  className={current ? 'current' : ''}
                  onMouseMove={(e) => showTip(e, `${r.site.name}: ${Math.round((r.score ?? 0) * 100)} / 100`)}
                  onMouseLeave={hideTip}
                >
                  <span className="rank-pos">{i + 1}</span>
                  <span className="rank-name">
                    {r.site.name}
                    {r.site.id.startsWith('cell_') && <small> · fuera del catálogo</small>}
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
        </div>

        {/* ---------- Limits + sources ---------- */}
        <div className="card">
          <h3>Lo que la Tierra no puede reproducir</h3>
          <table className="limits">
            <thead>
              <tr>
                <th />
                <th>Tierra</th>
                <th>{BODY_LABELS[body]}</th>
              </tr>
            </thead>
            <tbody>
              {PHYSICAL_LIMITS[body].map((l) => (
                <tr key={l.label}>
                  <th scope="row">{l.label}</th>
                  <td>{l.earth}</td>
                  <td>{l.body}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h3>Fuentes previstas por variable</h3>
          <ul className="sources">
            {features.map((f) => (
              <li key={f.id}>
                <strong>{f.label}:</strong> {f.source_earth} <span className="muted">frente a</span> {f.source_target[body] ?? '—'}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <details className="data-table">
        <summary>Ver tabla de datos</summary>
        <table>
          <thead>
            <tr>
              <th>Variable</th>
              <th>Tierra</th>
              <th>{BODY_LABELS[body]}</th>
              <th>Similitud</th>
              <th>Peso</th>
            </tr>
          </thead>
          <tbody>
            {features.map((f) => (
              <tr key={f.id}>
                <th scope="row">{f.label}</th>
                <td>{fmt(entry.values[f.id], f.unit)}</td>
                <td>{fmt(target.values[f.id], f.unit)}</td>
                <td>{fmt(result.sim[f.id])}</td>
                <td>{(weights[f.id] ?? 0).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted">
          Generado {new Date(data.generated_at).toLocaleString('es')} · {data.n_cells} celdas de la Tierra · fórmula de{' '}
          <code>src/compare.py</code>
        </p>
      </details>

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
  onTip,
  onLeave,
}: {
  feature: FeatureMeta
  earth: number | null
  other: number | null
  otherColor: string
  otherLabel: string
  onTip: (e: MouseEvent, text: string) => void
  onLeave: () => void
}) {
  if (earth == null || other == null) {
    return (
      <li className="dumbbell off">
        <span className="dumbbell-name">{feature.label}</span>
        <span className="muted">{other == null ? `No aplica en ${otherLabel}` : 'Sin dato en la Tierra'}</span>
      </li>
    )
  }
  // Fixed physical axis so the distance between the two dots means something.
  const [min, max] = feature.range ?? [Math.min(earth, other), Math.max(earth, other)]
  const lo = Math.min(min, earth, other)
  const hi = Math.max(max, earth, other)
  const pct = (v: number) => (hi === lo ? 50 : ((v - lo) / (hi - lo)) * 100)
  const pe = pct(earth)
  const po = pct(other)
  const tip = `${feature.label}: Tierra ${fmt(earth, feature.unit)} · ${otherLabel} ${fmt(other, feature.unit)}`

  return (
    <li className="dumbbell" onMouseMove={(e) => onTip(e, tip)} onMouseLeave={onLeave} aria-label={tip}>
      <span className="dumbbell-name">
        {feature.label}
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
