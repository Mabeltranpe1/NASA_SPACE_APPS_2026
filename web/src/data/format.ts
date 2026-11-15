import type { FeatureMeta } from './comparisons'
import { FEATURE_NAMES_EN, type Lang } from '../i18n/strings'

/** Number with sensible decimals for its size, plus the unit. "—" when missing. */
export function makeFmt(locale: string) {
  return (value: number | null | undefined, unit = '') => {
    if (value == null) return '—'
    const abs = Math.abs(value)
    const digits = abs >= 100 ? 0 : abs >= 10 ? 1 : 2
    return `${value.toLocaleString(locale, { maximumFractionDigits: digits })}${unit ? ` ${unit}` : ''}`
  }
}

export function featureLabel(f: FeatureMeta, lang: Lang) {
  return lang === 'en' ? (FEATURE_NAMES_EN[f.id] ?? f.label) : f.label
}

/** Position (0..100 %) of both values on the variable's fixed physical axis. */
export function dumbbellScale(feature: FeatureMeta, earth: number, other: number) {
  const [min, max] = feature.range ?? [Math.min(earth, other), Math.max(earth, other)]
  const lo = Math.min(min, earth, other)
  const hi = Math.max(max, earth, other)
  const pct = (v: number) => (hi === lo ? 50 : ((v - lo) / (hi - lo)) * 100)
  return { lo, hi, earth: pct(earth), other: pct(other) }
}

/** "81.93° N, 34.88° W" */
export function formatCoords(lat: number, lng: number, lang: Lang) {
  const ns = lat >= 0 ? 'N' : 'S'
  const ew = lng >= 0 ? 'E' : lang === 'en' ? 'W' : 'O'
  const f = (v: number) => Math.abs(v).toLocaleString(lang, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return `${f(lat)}° ${ns}, ${f(lng)}° ${ew}`
}
