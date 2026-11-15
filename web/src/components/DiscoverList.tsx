import { useState } from 'react'
import type { ComparisonData, RankingId } from '../data/comparisons'
import { discoveryAsSite, placeCountry, placeName, type Discovery } from '../data/focus'
import { formatCoords } from '../data/format'
import type { Target } from '../data/types'
import { BODY_COLORS } from '../theme'
import { useLang } from '../i18n/useLang'
import { BODY_NAMES } from '../i18n/strings'
import EarthThumb from './EarthThumb'

const PAGE = 20
/** Stays in the top N of the planet in at least this share of weight variations. */
const ROBUST = 0.8

export interface DiscoverItem {
  d: Discovery
  /** Position in the whole list (before the country filter). */
  rank: number
}

interface Props {
  data: ComparisonData
  body: Target
  onBody: (body: Target) => void
  list: RankingId
  onList: (list: RankingId) => void
  country: string
  onCountry: (country: string) => void
  /** Places of the list, already filtered by country. */
  items: DiscoverItem[]
  /** Countries of the whole list, with how many places each. */
  countries: [string, number][]
  onPick: (d: Discovery) => void
}

export default function DiscoverList({ data, body, onBody, list, onList, country, onCountry, items, countries, onPick }: Props) {
  const { lang, t } = useLang()
  const [shown, setShown] = useState(PAGE)
  const lists = Object.keys(data.rankings?.[body] ?? { general: [] }) as RankingId[]
  const dimLabel = (id: RankingId) =>
    id === 'general' ? t('disc.list.general') : (data.dimensions?.find((d) => d.id === id)?.label[lang] ?? id)
  const reset = () => setShown(PAGE)

  return (
    <>
      <div className="seg" role="group" aria-label={t('disc.for')}>
        <span>{t('disc.for')}</span>
        {(['luna', 'marte'] as Target[]).map((b) => (
          <button
            key={b}
            className={body === b ? 'active' : ''}
            aria-pressed={body === b}
            onClick={() => {
              onBody(b)
              reset()
            }}
          >
            <span className="dot" style={{ background: BODY_COLORS[b] }} />
            {BODY_NAMES[lang][b]}
          </button>
        ))}
      </div>

      <div className="chips list-chips" role="group" aria-label={t('disc.listAria')}>
        {lists.map((id) => (
          <button
            key={id}
            className={`chip ${list === id ? 'active' : ''}`}
            aria-pressed={list === id}
            onClick={() => {
              onList(id)
              reset()
            }}
          >
            {dimLabel(id)}
          </button>
        ))}
      </div>
      <p className="hint">
        {list === 'general'
          ? t('disc.hint.general', { n: data.rankings?.[body]?.general?.length ?? items.length, km: data.spread_km ?? 300 })
          : t('disc.hint.dim', { dim: dimLabel(list).toLowerCase() })}
      </p>

      {countries.length > 1 && (
        <label className="country-select">
          <span>{t('disc.country')}</span>
          <select
            value={country}
            onChange={(e) => {
              onCountry(e.target.value)
              reset()
            }}
          >
            <option value="">{t('disc.allCountries')}</option>
            {countries.map(([c, n]) => (
              <option key={c} value={c}>
                {c} ({n})
              </option>
            ))}
          </select>
        </label>
      )}

      <ol className="disc-list">
        {items.slice(0, shown).map(({ d, rank }) => {
          const result = d.site.results.find((r) => r.target === d.target.id)
          const robust = result?.stability != null && result.stability >= ROBUST
          const name = placeName(d.site, lang)
          const country = placeCountry(d.site, lang)
          return (
            <li key={`${d.site.id}-${d.target.id}`}>
              <button onClick={() => onPick(d)} title={d.site.note ?? undefined}>
                <span className="disc-thumb">
                  <EarthThumb site={discoveryAsSite(d, lang)} />
                  <span className="disc-rank">{rank}</span>
                </span>
                <span className="disc-body">
                  <strong>
                    {name}
                    {country && country !== name && <span className="muted"> · {country}</span>}
                  </strong>
                  <small>{formatCoords(d.site.lat, d.site.lng, lang)}</small>
                  <small>
                    ≈ {d.target.name}
                    {robust && (
                      <span
                        className="robust"
                        title={t('disc.robustTitle', {
                          top: data.stability_top,
                          pct: Math.round((result?.stability ?? 0) * 100),
                          runs: data.stability_runs,
                        })}
                      >
                        {' '}
                        · {t('disc.robust')}
                      </span>
                    )}
                  </small>
                </span>
                <span className="disc-score">{Math.round(d.score * 100)}</span>
              </button>
            </li>
          )
        })}
      </ol>
      {items.length > shown && (
        <button className="btn ghost wide" onClick={() => setShown((n) => n + PAGE)}>
          {t('disc.more', { n: Math.min(PAGE, items.length - shown), total: items.length })}
        </button>
      )}
    </>
  )
}
