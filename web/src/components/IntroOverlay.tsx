import { useEffect } from 'react'
import { useComparisons } from '../data/comparisons'
import { useLang } from '../i18n/useLang'
import { BODY_COLORS } from '../theme'
import { IconPlay, LogoMark } from './Icons'
import { Stat } from './MethodView'

const TEXT = {
  eyebrow: { es: 'NASA Space Apps Challenge 2026', en: 'NASA Space Apps Challenge 2026' },
  title: {
    es: '¿Dónde en la Tierra se ensaya vivir en la Luna y en Marte?',
    en: 'Where on Earth can we rehearse living on the Moon and Mars?',
  },
  lead: {
    es: 'Comparamos cada rincón de la Tierra con los sitios candidatos para bases lunares y para explorar Marte, usando datos abiertos de la NASA. Mostramos en qué se parecen, cuánto, y dónde deja de valer la analogía.',
    en: 'We compare every corner of Earth with the candidate sites for lunar bases and Mars exploration, using open NASA data. We show what is similar, how much, and where the analogy breaks down.',
  },
  cells: { es: 'celdas de la Tierra analizadas', en: 'Earth cells analyzed' },
  regions: { es: 'regiones de todo el mundo', en: 'regions worldwide' },
  targets: { es: 'sitios de la Luna y Marte', en: 'Moon and Mars sites' },
  tour: { es: 'Ver recorrido guiado', en: 'Take the guided tour' },
} as const

interface Props {
  onTour: () => void
  onClose: () => void
}

export default function IntroOverlay({ onTour, onClose }: Props) {
  const { lang, t } = useLang()
  const state = useComparisons()
  const data = state.status === 'ready' ? state.data : null

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="intro" role="dialog" aria-modal="true" aria-labelledby="intro-title">
      <div className="intro-card">
        <div className="intro-brand">
          <LogoMark size={44} />
          <p className="eyebrow">{TEXT.eyebrow[lang]}</p>
        </div>
        <h1 id="intro-title">{TEXT.title[lang]}</h1>
        <p className="intro-lead">{TEXT.lead[lang]}</p>
        {data && (
          <div className="stat-row">
            <Stat value={data.n_cells.toLocaleString(lang)} label={TEXT.cells[lang]} color={BODY_COLORS.tierra} />
            <Stat value={String(data.n_regions ?? '—')} label={TEXT.regions[lang]} />
            <Stat value={String(data.targets.length)} label={TEXT.targets[lang]} color={BODY_COLORS.marte} />
          </div>
        )}
        <div className="intro-actions">
          <button className="btn primary" onClick={onTour} autoFocus>
            <IconPlay size={14} /> {TEXT.tour[lang]}
          </button>
          <button className="btn ghost" onClick={onClose}>
            {t('intro.enter')} →
          </button>
        </div>
      </div>
    </div>
  )
}
