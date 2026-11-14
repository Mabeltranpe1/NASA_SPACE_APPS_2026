import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { STRINGS, type Lang } from './strings'
import { LanguageContext, type LanguageValue } from './context'

const STORAGE_KEY = 'analogs.lang'

function initialLang(): Lang {
  try {
    const fromUrl = new URLSearchParams(window.location.search).get('lang')
    if (fromUrl === 'es' || fromUrl === 'en') return fromUrl
  } catch {
    /* ignore */
  }
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    if (stored === 'es' || stored === 'en') return stored
  } catch {
    /* storage can be blocked */
  }
  // International jury: English unless the browser prefers Spanish.
  return navigator.language?.toLowerCase().startsWith('es') ? 'es' : 'en'
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initialLang)

  const setLang = useCallback((next: Lang) => {
    setLangState(next)
    try {
      window.localStorage.setItem(STORAGE_KEY, next)
    } catch {
      /* storage can be blocked */
    }
    try {
      const url = new URL(window.location.href)
      url.searchParams.set('lang', next)
      window.history.replaceState(null, '', url)
    } catch {
      /* ignore */
    }
  }, [])

  useEffect(() => {
    document.documentElement.lang = lang
    document.title = STRINGS[lang]['app.title']
  }, [lang])

  const value = useMemo<LanguageValue>(
    () => ({
      lang,
      setLang,
      locale: lang === 'es' ? 'es' : 'en',
      t: (key, vars) => {
        let text: string = STRINGS[lang][key] ?? STRINGS.es[key] ?? key
        if (vars) for (const [k, v] of Object.entries(vars)) text = text.replaceAll(`{${k}}`, String(v))
        return text
      },
    }),
    [lang, setLang],
  )

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

