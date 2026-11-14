import { useContext } from 'react'
import { LanguageContext, type LanguageValue } from './context'

export function useLang(): LanguageValue {
  const value = useContext(LanguageContext)
  if (!value) throw new Error('useLang must be used inside LanguageProvider')
  return value
}
