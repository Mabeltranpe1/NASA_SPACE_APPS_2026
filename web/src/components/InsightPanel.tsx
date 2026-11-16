import { useMemo, useState } from 'react'
import { homologueFor, type AnalogSite, type Body, type Target } from '../data/types'
import { rankForTarget, useComparisons, type ComparisonData, type ComparisonTarget } from '../data/comparisons'
import { bodiesOf, comparedTarget, discoveryAsSite, placeName } from '../data/focus'
import { dumbbellScale, featureLabel, formatCoords, makeFmt } from '../data/format'
import type { Place } from './ComparisonPanel'
import EarthThumb from './EarthThumb'
import { BODIES } from '../planet/bodies'
import { BODY_COLORS, SIMILARITY_COLOR } from '../theme'
import { useLang } from '../i18n/useLang'
import { BODY_NAMES } from '../i18n/strings'
import PlanetGlobe from './PlanetGlobe'
import MissionFits from './MissionFits'
import { IconImages, IconLock } from './Icons'
import ImageCompareModal from './ImageCompareModal'
import { useGalleryCount } from '../data/gallery'

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
  /** Fly the Earth globe to one of the similar places. */
  onGoTo: (place: Place) => void
  /** Open the photo gallery from outside (video mode of the guided tour). */
  galleryOpen?: boolean
  onGalleryClose?: () => void
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

/** Opens the image comparison pop-up with the photo carousels. */
function GalleryButton({
  site,
  body,
  forceOpen = false,
  onForceClose,
}: {
  site: AnalogSite
  body: Target | null
  forceOpen?: boolean
  onForceClose?: () => void
}) {
  const { t } = useLang()
  const [opened, setOpen] = useState(false)
  const open = opened || forceOpen
  const count = useGalleryCount(site)
  if (!site.homologues.length) return null
  return (
    <>
      <button className="btn ghost wide gallery-button" onClick={() => setOpen(true)}>
        <IconImages size={16} /> {count > 0 ? t('carousel.open', { n: count + 1 }) : t('image.compare')}
      </button>
      {open && (
        <ImageCompareModal
          site={site}
          initialBody={body}
          onClose={() => {
            setOpen(false)
            onForceClose?.()
          }}
        />
      )}
    </>
  )
}

function TerrainThumbs({ site, activeBody, compareBody, onBody, galleryOpen, onGalleryClose }: Props) {
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
                  <EarthThumb site={site} />
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
      <p className="credit">Copernicus Sentinel-2 / NASA GIBS · NASA Moon Trek (LRO WAC) · Mars Trek (Viking)</p>
      <GalleryButton site={site} body={compareBody} forceOpen={galleryOpen} onForceClose={onGalleryClose} />
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
  onGoTo,
}: Props & { data: ComparisonData }) {
  const { lang, t } = useLang()
  const [showAll, setShowAll] = useState(false)
  const { target, result } = compareBody ? comparedTarget(data, site, compareBody) : {}
  const entry = data.sites.find((s) => s.id === site.id)
  const label = (id: string) => {
    const f = data.features.find((x) => x.id === id)
    return f ? featureLabel(f, lang) : id
  }

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
  // Most similar variable first; the ones Earth cannot reach are listed apart.
  const bars = data.features
    .filter((f) => result.sim[f.id] != null)
    .sort((a, b) => (result.sim[b.id] ?? 0) - (result.sim[a.id] ?? 0))
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

      {(() => {
        // The same place against the other sites of this body: the match is rarely with one site only.
        const others = (entry?.results ?? [])
          .filter((r) => r.target !== target.id && r.score != null && data.targets.find((tg) => tg.id === r.target)?.body === compareBody)
          .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
        if (!others.length) return null
        return (
          <p className="also-like small">
            <span className="muted">{t('insight.alsoLike')}</span>{' '}
            {others.slice(0, 3).map((r, i) => (
              <span key={r.target}>
                {i > 0 && ' · '}
                {data.targets.find((tg) => tg.id === r.target)?.name} <b>{Math.round((r.score ?? 0) * 100)}</b>
              </span>
            ))}
            {others.length > 3 && <span className="muted"> {t('insight.alsoMore', { n: others.length - 3 })}</span>}
          </p>
        )
      })()}

      {result.dims && data.dimensions && (
        <>
          <h4 className="panel-sub">{t('insight.dims')}</h4>
          <ul className="dim-bars">
            {data.dimensions.map((d) => {
              const v = result.dims?.[d.id]
              return (
                <li key={d.id} className={v == null ? 'off' : ''} title={v == null ? t('insight.dimNATitle') : undefined}>
                  <span className="dim-name">{d.label[lang]}</span>
                  <span className="mini-track">
                    {v != null && <span className="mini-fill" style={{ width: `${v * 100}%`, background: SIMILARITY_COLOR }} />}
                  </span>
                  <span className="dim-value">{v == null ? t('insight.dimNA') : Math.round(v * 100)}</span>
                </li>
              )
            })}
          </ul>
        </>
      )}

      <MissionFits targetId={target.id} body={compareBody} sim={result.sim} />

      <h4 className="panel-sub">{t('cmp.values')}</h4>
      <p className="legend-line small">
        <span>
          <span className="dot" style={{ background: BODY_COLORS.tierra }} /> {BODY_NAMES[lang].tierra}
        </span>
        <span>
          <span className="dot" style={{ background: BODY_COLORS[compareBody] }} /> {target.name}
        </span>
      </p>
      <ul className="value-rows">
        {shown.map((f) => (
          <ValueRow
            key={f.id}
            label={label(f.id)}
            unit={f.unit}
            earth={entry?.values[f.id] ?? null}
            other={target.values[f.id] ?? null}
            scale={f}
            color={BODY_COLORS[compareBody]}
            mark={f.id === result.best_match ? 'good' : f.id === result.worst_match ? 'bad' : null}
            otherName={target.name}
          />
        ))}
      </ul>
      {bars.length > 5 && (
        <button className="link small" onClick={() => setShowAll((v) => !v)}>
          {showAll ? t('insight.fewer') : bars.length - 5 === 1 ? t('insight.moreOne') : t('insight.more', { n: bars.length - 5 })}
        </button>
      )}
      <p className="legend-line small">
        <span className="tag good">✓ {t('cmp.best').replace('✓ ', '')}</span>
        <span className="tag bad">⚠ {t('cmp.worst').replace('⚠ ', '')}</span>
      </p>
      <p className="muted small">{t('insight.valuesHint')}</p>
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

      <SimilarPlaces data={data} site={site} target={target} onGoTo={onGoTo} />
    </section>
  )
}

/** One variable: Earth and Moon/Mars values on the same fixed axis (dumbbell). */
function ValueRow({
  label,
  unit,
  earth,
  other,
  scale,
  color,
  mark,
  otherName,
}: {
  label: string
  unit: string
  earth: number | null
  other: number | null
  scale: Parameters<typeof dumbbellScale>[0]
  color: string
  mark: 'good' | 'bad' | null
  otherName: string
}) {
  const { lang, t } = useLang()
  const fmt = makeFmt(lang)
  const tip = `${label}: ${BODY_NAMES[lang].tierra} ${fmt(earth, unit)} · ${otherName} ${fmt(other, unit)}`
  const pos = earth != null && other != null ? dumbbellScale(scale, earth, other) : null
  return (
    <li className="value-row" title={tip} aria-label={tip}>
      <span className="value-name">
        {label}
        {unit && <small> ({unit})</small>}
        {mark === 'good' && <span className="tag good"> ✓</span>}
        {mark === 'bad' && <span className="tag bad"> ⚠</span>}
      </span>
      <span className="value-nums">
        <span style={{ color: BODY_COLORS.tierra }}>{fmt(earth)}</span>
        {' · '}
        <span style={{ color }}>{fmt(other)}</span>
      </span>
      {pos ? (
        <span className="value-plot" aria-hidden="true">
          <span className="dumbbell-axis" />
          <span className="dumbbell-link" style={{ left: `${Math.min(pos.earth, pos.other)}%`, width: `${Math.abs(pos.earth - pos.other)}%` }} />
          <span className="dumbbell-dot" style={{ left: `${pos.earth}%`, background: BODY_COLORS.tierra }} />
          <span className="dumbbell-dot" style={{ left: `${pos.other}%`, background: color }} />
          <span className="value-tick start">{fmt(pos.lo)}</span>
          <span className="value-tick end">{fmt(pos.hi)}</span>
        </span>
      ) : (
        <span className="value-plot muted small">{t('insight.noValue')}</span>
      )}
    </li>
  )
}

/** The best places on Earth for the compared Moon/Mars site (one per region), with coordinates. */
function SimilarPlaces({
  data,
  site,
  target,
  onGoTo,
}: {
  data: ComparisonData
  site: AnalogSite
  target: ComparisonTarget
  onGoTo: (place: Place) => void
}) {
  const { lang, t } = useLang()
  const defaults = useMemo(() => Object.fromEntries(data.features.map((f) => [f.id, f.default_weight])), [data])
  const top = useMemo(() => rankForTarget(data, target.id, defaults).slice(0, 5), [data, target, defaults])
  if (!top.length) return null
  const best = top[0]
  const bestSite = discoveryAsSite({ site: best.site, target, score: best.score ?? 0 }, lang)
  const go = (r: (typeof top)[number]) => onGoTo({ lat: r.site.lat, lng: r.site.lng, name: placeName(r.site, lang) })
  const tag = (r: (typeof top)[number]) =>
    r.site.kind === 'discovery' ? t('cmp.discovery') : r.site.known ? t('cmp.known') : null

  return (
    <section className="similar-places">
      <h4 className="panel-sub">{t('cmp.ranking', { target: target.name })}</h4>
      <button className="best-place" onClick={() => go(best)} title={t('cmp.goTo')}>
        <span className="best-thumb">
          <EarthThumb site={bestSite} alt={placeName(best.site, lang)} />
          <span className="best-badge">#1</span>
        </span>
        <span className="best-text">
          <strong>{placeName(best.site, lang)}</strong>
          <small>{formatCoords(best.site.lat, best.site.lng, lang)}</small>
          {tag(best) && <small>{tag(best)}</small>}
        </span>
        <span className="best-score">
          <b>{Math.round((best.score ?? 0) * 100)}</b>
          <small>/100</small>
        </span>
      </button>
      <ol className="place-rows" start={2}>
        {top.slice(1).map((r, i) => (
          <li key={r.site.id} className={r.site.id === site.id ? 'current' : ''}>
            <button onClick={() => go(r)} title={t('cmp.goTo')}>
              <span className="place-pos">{i + 2}</span>
              <span className="place-text">
                <strong>{placeName(r.site, lang)}</strong>
                <small>
                  {formatCoords(r.site.lat, r.site.lng, lang)}
                  {tag(r) && ` · ${tag(r)}`}
                </small>
              </span>
              <span className="place-score">{Math.round((r.score ?? 0) * 100)}</span>
            </button>
          </li>
        ))}
      </ol>
      <p className="muted small">{t('insight.placesHint')}</p>
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
