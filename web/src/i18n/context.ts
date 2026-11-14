import { createContext } from 'react'
import type { Lang, StringKey } from './strings'

export interface LanguageValue {
  lang: Lang
  setLang: (lang: Lang) => void
  t: (key: StringKey, vars?: Record<string, string | number>) => string
  locale: string
}

export const LanguageContext = createContext<LanguageValue | null>(null)
