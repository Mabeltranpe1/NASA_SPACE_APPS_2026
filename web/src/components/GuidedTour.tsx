import { useEffect, useRef, useState } from 'react'
import { TOUR_STEPS, type TourStep } from '../data/tour'
import { useLang } from '../i18n/useLang'

const STEP_SECONDS = 12

interface Props {
  onApply: (step: TourStep) => void
  onClose: () => void
  /** Steps to play (default: the full guided tour). */
  steps?: TourStep[]
  /** Video mode: compact card without controls (Esc still closes it). */
  demo?: boolean
}

export default function GuidedTour({ onApply, onClose, steps = TOUR_STEPS, demo = false }: Props) {
  const { lang, t } = useLang()
  const [index, setIndex] = useState(0)
  const [playing, setPlaying] = useState(true)
  const onApplyRef = useRef(onApply)
  const TOUR = steps
  const step = TOUR[index]
  const last = index === TOUR.length - 1
  const seconds = step.seconds ?? STEP_SECONDS

  useEffect(() => {
    onApplyRef.current = onApply
  }, [onApply])

  // Apply the step to the app (mode + selected site).
  useEffect(() => {
    onApplyRef.current(TOUR[index])
  }, [index, TOUR])

  // Auto-advance.
  useEffect(() => {
    if (!playing || last) return
    const timer = window.setTimeout(() => setIndex((i) => i + 1), seconds * 1000)
    return () => window.clearTimeout(timer)
  }, [playing, index, last, seconds])

  // Keyboard: arrows to move, space to pause, Esc to close.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') setIndex((i) => Math.min(i + 1, TOUR.length - 1))
      else if (e.key === 'ArrowLeft') setIndex((i) => Math.max(i - 1, 0))
      else if (e.key === 'Escape') onClose()
      else if (e.key === ' ' && (e.target as HTMLElement)?.tagName !== 'BUTTON') {
        e.preventDefault()
        setPlaying((p) => !p)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose, TOUR.length])

  return (
    <div className={`tour ${demo ? 'demo' : ''}`} role="dialog" aria-label={t('tour.label')} aria-live="polite">
      <div className="tour-progress" aria-hidden="true">
        {TOUR.map((s, i) => (
          <span key={`${i}-${s.title.es}`} className={i < index ? 'done' : i === index ? `active ${playing ? 'playing' : ''}` : ''}>
            {i === index && <i style={{ animationDuration: `${seconds}s` }} />}
          </span>
        ))}
      </div>
      {!demo && (
      <p className="tour-count">
        {t('tour.count', { i: index + 1, n: TOUR.length })}
      </p>
      )}
      <h2>{step.title[lang]}</h2>
      <p className="tour-text">{step.text[lang]}</p>
      {!demo && (
      <div className="tour-controls">
        <button onClick={() => setIndex((i) => Math.max(i - 1, 0))} disabled={index === 0} aria-label={t('tour.prev')}>
          ←
        </button>
        <button onClick={() => setPlaying((p) => !p)} disabled={last} aria-label={playing ? t('tour.pause') : t('tour.resume')}>
          {playing && !last ? t('tour.pause') : t('tour.resume')}
        </button>
        <button
          className="primary"
          onClick={() => (last ? onClose() : setIndex((i) => i + 1))}
          aria-label={last ? t('tour.finishLabel') : t('tour.nextLabel')}
        >
          {last ? t('tour.finish') : t('tour.next')}
        </button>
        <button className="tour-close" onClick={onClose} aria-label={t('tour.close')}>
          ✕
        </button>
      </div>
      )}
    </div>
  )
}
