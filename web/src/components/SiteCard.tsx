import { useState } from 'react'
import { DIMENSION_LABELS, type AnalogSite, type Body, type Dimension } from '../data/types'
import { useComparisons, type Characterization } from '../data/comparisons'
import { googleEarthUrl } from '../data/focus'
import { earthSnapshotUrl } from '../map/snapshot'
import { BODY_COLORS } from '../theme'
import { useLang } from '../i18n/useLang'
import { BODY_NAMES, DIMENSION_NAMES, ENVIRONMENT_NAMES } from '../i18n/strings'
import { IconExternal } from './Icons'

interface Props {
  site: AnalogSite
  /** The place comes from the global search (not from the curated catalog). */
  discovery?: boolean
  onBack: () => void
  onBody: (body: Body) => void
}

export default function SiteCard({ site, discovery = false, onBack, onBody }: Props) {
  const { lang, t } = useLang()
  const snap = earthSnapshotUrl(site)
  const [imgOk, setImgOk] = useState(true)
  const target = site.homologues[0]

  return (
    <article className="site-card">
      <button className="link back" onClick={onBack}>
        {t('card.back')}
      </button>

      <figure className="site-hero">
        {imgOk && <img src={snap.url} alt={t('image.alt', { name: site.name })} onError={() => setImgOk(false)} />}
        <figcaption>
          <span>
            {snap.label} · {t('image.side', { km: snap.widthKm })}
          </span>
        </figcaption>
      </figure>

      <h2 className="site-name">{site.name}</h2>
      <p className="site-meta">
        {!discovery && site.country && <>{site.country} · </>}
        {site.lat.toFixed(2)}°, {site.lng.toFixed(2)}°
      </p>
      <div className="tags">
        {discovery && <span className="pill accent">{t('card.discovery')}</span>}
        {site.caseStudy && <span className="pill case">{t('badge.caseStudy')}</span>}
        {!site.wellKnown && !site.caseStudy && <span className="pill">{t('badge.lesserKnown')}</span>}
        {site.environments.map((e) => (
          <span key={e} className="pill subtle">
            {ENVIRONMENT_NAMES[lang][e]}
          </span>
        ))}
      </div>

      <h3 className="panel-sub">{t('card.analogOf')}</h3>
      <ul className="counterparts">
        {site.homologues.map((h) => (
          <li key={h.body}>
            <button onClick={() => onBody(h.body)} title={t('insight.thumbAria', { body: BODY_NAMES[lang][h.body] })}>
              <span className="dot" style={{ background: BODY_COLORS[h.body] }} />
              <span>
                <strong>{h.name}</strong>
                <small>
                  {BODY_NAMES[lang][h.body]}
                  {h.note && <> · {h.note}</>}
                  {h.approximate && t('detail.approximate')}
                </small>
              </span>
            </button>
          </li>
        ))}
      </ul>

      {discovery ? (
        <>
          <p className="lead">{t('card.discoveryText', { target: target?.name ?? '' })}</p>
          {site.country && (
            <>
              <h3 className="panel-sub">{t('card.why')}</h3>
              <p>{site.country}</p>
            </>
          )}
        </>
      ) : (
        <>
          <p className="lead">{site.similarities}</p>
          <h3 className="panel-sub">{t('detail.limitations')}</h3>
          <p>{site.limitations}</p>
          <h3 className="panel-sub">{t('detail.missionUse')}</h3>
          <p>{site.missionUse}</p>
          <SiteCharacterization siteId={site.id} />
          {Object.keys(site.dimensions).length > 0 && (
            <details className="fold">
              <summary>{t('card.more')}</summary>
              <ul className="dims">
                {(Object.keys(DIMENSION_LABELS) as Dimension[])
                  .filter((d) => site.dimensions[d])
                  .map((d) => (
                    <li key={d}>
                      <span>{DIMENSION_NAMES[lang][d]}</span>
                      <span className={`level ${site.dimensions[d]}`}>{t(`level.${site.dimensions[d]}` as 'level.alta')}</span>
                    </li>
                  ))}
              </ul>
            </details>
          )}
        </>
      )}

      <a className="btn ghost wide" href={googleEarthUrl(site.lat, site.lng)} target="_blank" rel="noreferrer">
        {t('detail.googleEarth').replace(' ↗', '')} <IconExternal size={15} />
      </a>
    </article>
  )
}

/** Santiago's detailed 10 x 10 km characterization, when the site has one. Descriptive: not part of the score. */
function SiteCharacterization({ siteId }: { siteId: string }) {
  const state = useComparisons()
  const { lang, t } = useLang()
  if (state.status !== 'ready') return null
  const c: Characterization | undefined = state.data.sites.find((s) => s.id === siteId)?.characterization
  if (!c) return null
  const n = (v: number | string | null | undefined, unit = '', digits = 1) =>
    typeof v === 'number' ? `${v.toLocaleString(lang, { maximumFractionDigits: digits })}${unit}` : '—'
  const topo: [string, string][] = c.topography
    ? [
        [t('char.slope'), n(c.topography.slope_mean_deg, '°')],
        [t('char.relief'), n(c.topography.relief_p90_p10_m, ' m', 0)],
        [t('char.flat'), n(c.topography.flat_terrain_pct, ' %', 0)],
      ]
    : []
  const env: [string, string][] = c.environment
    ? [
        [t('char.lstDay'), n(c.environment.lst_day_mean_K, ' K', 0)],
        [t('char.lstNight'), n(c.environment.lst_night_mean_K, ' K', 0)],
        [t('char.rain'), n(c.environment.annual_precipitation_mm, ' mm', 0)],
        [t('char.ndvi'), n(c.environment.ndvi_mean, '', 2)],
        [t('char.bare'), n(c.environment.bare_ground_pct, ' %', 0)],
      ]
    : []
  const spec: [string, string][] = c.spectral
    ? [
        [t('char.iron'), n(c.spectral.iron_oxide_ratio, '', 2)],
        [t('char.hydroxyl'), n(c.spectral.hydroxyl_ratio, '', 2)],
      ]
    : []
  const block = (title: string, list: [string, string][]) =>
    list.length > 0 && (
      <>
        <h4>{title}</h4>
        <dl className="char-list">
          {list.map(([k, v]) => (
            <div key={k}>
              <dt>{k}</dt>
              <dd>{v}</dd>
            </div>
          ))}
        </dl>
      </>
    )
  return (
    <details className="fold characterization">
      <summary>{t('char.title')}</summary>
      <p className="hint">{t('char.note')}</p>
      {c.quality_flags?.map((f) => (
        <p key={f} className="tag bad">
          ⚠ {f}
        </p>
      ))}
      {block(t('char.topography'), topo)}
      {block(t('char.environment'), env)}
      {block(t('char.spectral'), spec)}
      {c.topographic_index && c.topographic_index.length > 0 && (
        <>
          <h4>{t('char.pai')}</h4>
          <dl className="char-list">
            {c.topographic_index.map((p) => (
              <div key={p.target}>
                <dt>
                  {BODY_NAMES[lang][p.body]}: {p.target}
                </dt>
                <dd>{n(p.pai, ' / 100', 0)}</dd>
              </div>
            ))}
          </dl>
        </>
      )}
      {c.mineralogy && <p className="hint">{t('char.mineralogy', { n: c.mineralogy.emit_granules })}</p>}
    </details>
  )
}
