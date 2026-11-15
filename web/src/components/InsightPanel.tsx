import { useMemo, useState } from 'react'
import { homologueFor, type AnalogSite, type Body, type Target } from '../data/types'
import { useComparisons, type ComparisonData } from '../data/comparisons'
import { bodiesOf } from '../data/focus'
import { BODIES } from '../planet/bodies'
import { BODY_COLORS, SIMILARITY_COLOR } from '../theme'
import { earthSnapshotUrl } from '../map/snapshot'
import { useLang } from '../i18n/useLang'
import { BODY_NAMES, FEATURE_NAMES_EN } from '../i18n/strings'
import PlanetGlobe from './PlanetGlobe'
import { IconLock } from './Icons'

const BODY_ORDER: Body[] = ['tierra', 'luna', 'marte']

interface Props {
  site: AnalogSite
  activeBody: Body
  /** Moon/Mars body the similarity index refers to. */
  compareBody: Target | null
  onBody: (body: Body) => void
  onOpenAnalysis: () => void
  /** Id of the target whose similarity map is on the globe (null = none). */
  mapTargetId: string | null
  onToggleMap: (target: { id: string; name: string; body: Target } | null) => void
}

export default function InsightPanel(props: Props) {
  const { t } = useLang()
  return (
    <aside className="panel panel-right glass" aria-label={t('insight.index')}>
      <TerrainThumbs {...props} />
      <SimilarityIndex {...props} />
    </aside>
  )
}

function TerrainThumbs({ site, activeBody, onBody }: Props) {
  const { lang, t } = useLang()
  const allowed = bodiesOf(site)
  return (
    <section>
      <h3 className="panel-title">{t('insight.terrain')}</h3>
      <div className="thumbs">
        {BODY_ORDER.map((body) => {
          const name = BODY_NAMES[lang][body]
          const locked = !allowed.includes(body)
          return (
            <button
              key={body}
              className={`thumb ${activeBody === body ? 'active' : ''} ${locked ? 'locked' : ''}`}
              style={{ ['--body' as string]: BODY_COLORS[body] }}
              disabled={locked}
              aria-pressed={activeBody === body}
              aria-label={locked ? t('body.locked', { body: name }) : t('insight.thumbAria', { body: name })}
              title={locked ? t('body.locked', { body: name }) : undefined}
              onClick={() => onBody(body)}
            >
              <span className="thumb-media">
                {locked ? (
                  <span className="thumb-lock">
                    <IconLock size={18} />
                  </span>
                ) : body === 'tierra' ? (
                  <img src={earthSnapshotUrl(site).url} alt="" loading="lazy" />
                ) : (
                  <ThumbGlobe site={site} body={body} />
                )}
              </span>
              <span className="thumb-label">
                <span className="dot" style={{ background: BODY_COLORS[body] }} />
                {name}
              </span>
            </button>
          )
        })}
      </div>
      <p className="credit">NASA GIBS (Landsat) · Moon Trek (LRO WAC) · Mars Trek (Viking)</p>
    </section>
  )
}

/** Static close-up of the counterpart (Cesium reprojects the polar regions correctly). */
function ThumbGlobe({ site, body }: { site: AnalogSite; body: Target }) {
  const h = homologueFor(site, body)
  const focus = useMemo(() => (h ? { lat: h.lat, lng: h.lng } : null), [h])
  const markers = useMemo(() => (h ? [{ id: 'thumb', lat: h.lat, lng: h.lng, color: '#ffffff', label: '' }] : []), [h])
  if (!h || !focus) return null
  const cfg = BODIES[body]
  const polar = Math.abs(h.lat) > 80
  return (
    <PlanetGlobe
      body={body}
      markers={markers}
      focus={focus}
      variant="closeup"
      interactive={false}
      closeupHeight={polar ? cfg.closeupHeight * 6 : cfg.closeupHeight * 2}
    />
  )
}

function SimilarityIndex(props: Props) {
  const state = useComparisons()
  const { t } = useLang()
  if (state.status !== 'ready') return <p className="hint">{t('cmp.loading')}</p>
  return <SimilarityContent data={state.data} {...props} />
}

function SimilarityContent({
  data,
  site,
  compareBody,
  onOpenAnalysis,
  mapTargetId,
  onToggleMap,
}: Props & { data: ComparisonData }) {
  const { lang, t } = useLang()
  const [showAll, setShowAll] = useState(false)
  const homologue = compareBody ? homologueFor(site, compareBody) : undefined
  const entry = data.sites.find((s) => s.id === site.id)
  // Same rule as the detailed comparison: the counterpart when it is in the
  // database, otherwise the first target of that body with a result.
  const withResult = new Set(entry?.results.map((r) => r.target) ?? [])
  const target =
    data.targets.find((tg) => tg.id === homologue?.id && withResult.has(tg.id)) ??
    data.targets.find((tg) => tg.body === compareBody && withResult.has(tg.id))
  const result = target ? entry?.results.find((r) => r.target === target.id) : undefined
  const label = (id: string) =>
    lang === 'en' ? (FEATURE_NAMES_EN[id] ?? id) : (data.features.find((f) => f.id === id)?.label ?? id)

  if (!compareBody || !target || !result || result.score == null) {
    return (
      <section>
        <h3 className="panel-title">{t('insight.index')}</h3>
        <p className="hint">{t('insight.noData')}</p>
        <button className="btn ghost wide" onClick={onOpenAnalysis}>
          {t('insight.full')}
        </button>
      </section>
    )
  }

  const score = Math.round(result.score * 100)
  const bars = data.features
    .filter((f) => result.sim[f.id] != null)
    .map((f) => ({ id: f.id, sim: result.sim[f.id] as number }))
    .sort((a, b) => b.sim - a.sim)
  const shown = showAll ? bars : bars.slice(0, 5)
  const excluded = (target.excluded ?? []).map(label)
  const mapShown = mapTargetId === target.id

  return (
    <section>
      <h3 className="panel-title">{t('insight.index')}</h3>
      <div className="index-head">
        <ScoreRing value={score} color={SIMILARITY_COLOR} />
        <div className="index-meta">
          <p className="index-target">
            <span className="dot" style={{ background: BODY_COLORS[compareBody] }} />
            {t('insight.with', { target: target.name })}
          </p>
          <p>
            <strong>{t('insight.rank', { pos: result.rank.toLocaleString(lang), n: data.n_cells.toLocaleString(lang) })}</strong>
          </p>
          {result.stability != null && (
            <p className="muted small">
              {t('insight.stability', {
                top: data.stability_top,
                pct: Math.round(result.stability * 100),
                runs: data.stability_runs,
              })}
            </p>
          )}
        </div>
      </div>

      {site.caseStudy && <p className="note-line">{t('insight.caseStudy')}</p>}

      <h4 className="panel-sub">{t('insight.byFeature')}</h4>
      <ul className="mini-bars">
        {shown.map((b) => (
          <li key={b.id}>
            <span className="mini-name">
              {label(b.id)}
              {b.id === result.best_match && <span className="tag good"> ✓</span>}
              {b.id === result.worst_match && <span className="tag bad"> ⚠</span>}
            </span>
            <span className="mini-track">
              <span className="mini-fill" style={{ width: `${b.sim * 100}%`, background: SIMILARITY_COLOR }} />
            </span>
            <span className="mini-value">{b.sim.toFixed(2)}</span>
          </li>
        ))}
      </ul>
      {bars.length > 5 && (
        <button className="link small" onClick={() => setShowAll((v) => !v)}>
          {showAll ? '−' : `+${bars.length - 5}`}
        </button>
      )}
      <p className="legend-line small">
        <span className="tag good">✓ {t('cmp.best').replace('✓ ', '')}</span>
        <span className="tag bad">⚠ {t('cmp.worst').replace('⚠ ', '')}</span>
      </p>
      {excluded.length > 0 && <p className="muted small">{t('insight.notComparable', { list: excluded.join(', ') })}</p>}

      <div className="panel-actions">
        <button className="btn primary wide" onClick={onOpenAnalysis}>
          {t('insight.full')}
        </button>
        <button
          className={`btn ghost wide ${mapShown ? 'on' : ''}`}
          aria-pressed={mapShown}
          onClick={() => onToggleMap(mapShown ? null : { id: target.id, name: target.name, body: compareBody })}
        >
          {mapShown ? t('cmp.hideMap') : t('cmp.showMap')}
        </button>
      </div>
    </section>
  )
}

/** Score 0–100 as a ring: one hue, the number carries the value. */
export function ScoreRing({ value, color, size = 108 }: { value: number; color: string; size?: number }) {
  const r = 44
  const c = 2 * Math.PI * r
  return (
    <svg className="score-ring" width={size} height={size} viewBox="0 0 108 108" role="img" aria-label={`${value} / 100`}>
      <circle cx="54" cy="54" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="9" />
      <circle
        cx="54"
        cy="54"
        r={r}
        fill="none"
        stroke={color}
        strokeWidth="9"
        strokeLinecap="round"
        strokeDasharray={`${(c * value) / 100} ${c}`}
        transform="rotate(-90 54 54)"
        style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}
      />
      <text x="54" y="58" textAnchor="middle" className="ring-number">
        {value}
      </text>
      <text x="54" y="76" textAnchor="middle" className="ring-unit">
        / 100
      </text>
    </svg>
  )
}
