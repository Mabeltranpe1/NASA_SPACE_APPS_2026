import { useEffect, useRef, useState } from 'react'
import { TOUR_STEPS, type TourStep } from '../data/tour'

const STEP_SECONDS = 12

interface Props {
  onApply: (step: TourStep) => void
  onClose: () => void
}

export default function GuidedTour({ onApply, onClose }: Props) {
  const [index, setIndex] = useState(0)
  const [playing, setPlaying] = useState(true)
  const onApplyRef = useRef(onApply)
  const step = TOUR_STEPS[index]
  const last = index === TOUR_STEPS.length - 1

  useEffect(() => {
    onApplyRef.current = onApply
  }, [onApply])

  // Apply the step to the app (mode + selected site).
  useEffect(() => {
    onApplyRef.current(TOUR_STEPS[index])
  }, [index])

  // Auto-advance.
  useEffect(() => {
    if (!playing || last) return
    const timer = window.setTimeout(() => setIndex((i) => i + 1), STEP_SECONDS * 1000)
    return () => window.clearTimeout(timer)
  }, [playing, index, last])

  // Keyboard: arrows to move, space to pause, Esc to close.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') setIndex((i) => Math.min(i + 1, TOUR_STEPS.length - 1))
      else if (e.key === 'ArrowLeft') setIndex((i) => Math.max(i - 1, 0))
      else if (e.key === 'Escape') onClose()
      else if (e.key === ' ' && (e.target as HTMLElement)?.tagName !== 'BUTTON') {
        e.preventDefault()
        setPlaying((p) => !p)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="tour" role="dialog" aria-label="Recorrido guiado" aria-live="polite">
      <div className="tour-progress" aria-hidden="true">
        {TOUR_STEPS.map((s, i) => (
          <span key={s.title} className={i < index ? 'done' : i === index ? `active ${playing ? 'playing' : ''}` : ''}>
            {i === index && <i style={{ animationDuration: `${STEP_SECONDS}s` }} />}
          </span>
        ))}
      </div>
      <p className="tour-count">
        Recorrido guiado · {index + 1} de {TOUR_STEPS.length}
      </p>
      <h2>{step.title}</h2>
      <p className="tour-text">{step.text}</p>
      <div className="tour-controls">
        <button onClick={() => setIndex((i) => Math.max(i - 1, 0))} disabled={index === 0} aria-label="Paso anterior">
          ←
        </button>
        <button onClick={() => setPlaying((p) => !p)} disabled={last} aria-label={playing ? 'Pausar' : 'Reanudar'}>
          {playing && !last ? 'Pausa' : 'Reanudar'}
        </button>
        <button
          className="primary"
          onClick={() => (last ? onClose() : setIndex((i) => i + 1))}
          aria-label={last ? 'Terminar recorrido' : 'Siguiente paso'}
        >
          {last ? 'Explorar por mi cuenta' : 'Siguiente →'}
        </button>
        <button className="tour-close" onClick={onClose} aria-label="Cerrar recorrido">
          ✕
        </button>
      </div>
    </div>
  )
}
