import { useRef, useState, type KeyboardEvent, type PointerEvent, type ReactNode } from 'react'
import { useLang } from '../i18n/useLang'
import { IconCamera, IconExternal, IconSatellite } from './Icons'

export type SlideKind =
  | 'rover'
  | 'lander'
  | 'apollo'
  | 'orbital'
  | 'visualization'
  | 'field'
  | 'astronaut'
  | 'satellite'
  | 'radar'
  | 'sentinel'
  | 'globe'

export interface Slide {
  id: string
  kind: SlideKind
  caption: string
  /** Credit · date line under the caption. */
  meta?: string
  /** Short warning shown on the image, e.g. "Photo of the region, not of the exact spot". */
  note?: string
  sourceUrl?: string
  /** An image slide... */
  src?: string
  alt?: string
  /** ...or any content (the interactive 3D view), rendered only while active. */
  render?: () => ReactNode
}

const GROUND: SlideKind[] = ['rover', 'lander', 'apollo', 'field']

interface Props {
  slides: Slide[]
  label: string
}

export default function Carousel({ slides, label }: Props) {
  const { t } = useLang()
  const [index, setIndex] = useState(0)
  const start = useRef<number | null>(null)
  const count = slides.length
  const i = Math.min(index, count - 1)
  const slide = slides[i]
  if (!slide) return null

  const go = (delta: number) => setIndex((current) => (Math.min(current, count - 1) + delta + count) % count)
  const onKey = (e: KeyboardEvent) => {
    if (e.key === 'ArrowRight') {
      e.preventDefault()
      go(1)
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      go(-1)
    }
  }
  const onDown = (e: PointerEvent) => {
    if (slide.render) return // the 3D view uses drag to rotate
    start.current = e.clientX
  }
  const onUp = (e: PointerEvent) => {
    if (start.current == null) return
    const dx = e.clientX - start.current
    start.current = null
    if (Math.abs(dx) > 40) go(dx < 0 ? 1 : -1)
  }
  const next = slides[(i + 1) % count]

  return (
    <figure
      className="carousel"
      role="region"
      aria-roledescription="carousel"
      aria-label={label}
      tabIndex={0}
      onKeyDown={onKey}
    >
      <div className="carousel-stage" onPointerDown={onDown} onPointerUp={onUp}>
        {slide.src ? (
          <>
            <div className="carousel-backdrop" style={{ backgroundImage: `url("${slide.src}")` }} aria-hidden="true" />
            <img key={slide.id} className="carousel-img" src={slide.src} alt={slide.alt ?? slide.caption} draggable={false} />
          </>
        ) : (
          <div className="carousel-node" key={slide.id}>
            {slide.render?.()}
          </div>
        )}
        {/* Preload the next image so moving forward is instant. */}
        {next?.src && next !== slide && <link rel="preload" as="image" href={next.src} />}

        <span className={`kind-badge ${GROUND.includes(slide.kind) ? 'ground' : 'orbit'}`}>
          {GROUND.includes(slide.kind) ? <IconCamera size={13} /> : <IconSatellite size={13} />}
          {t(`kind.${slide.kind}`)}
        </span>
        {slide.note && <span className="carousel-note">{slide.note}</span>}

        {count > 1 && (
          <>
            <button className="carousel-arrow prev" onClick={() => go(-1)} aria-label={t('carousel.prev')}>
              ‹
            </button>
            <button className="carousel-arrow next" onClick={() => go(1)} aria-label={t('carousel.next')}>
              ›
            </button>
          </>
        )}
      </div>

      <figcaption className="carousel-caption">
        <span className="carousel-text">
          <strong>{slide.caption}</strong>
          {(slide.meta || slide.sourceUrl) && (
            <small>
              {slide.meta}
              {slide.sourceUrl && (
                <>
                  {' · '}
                  <a href={slide.sourceUrl} target="_blank" rel="noreferrer">
                    {t('carousel.source')} <IconExternal size={11} />
                  </a>
                </>
              )}
            </small>
          )}
        </span>
        {count > 1 && (
          <span className="carousel-dots" role="tablist" aria-label={label}>
            {slides.map((s, k) => (
              <button
                key={s.id}
                role="tab"
                aria-selected={k === i}
                aria-label={t('carousel.goTo', { n: k + 1, total: count })}
                className={k === i ? 'active' : ''}
                onClick={() => setIndex(k)}
              />
            ))}
          </span>
        )}
      </figcaption>
    </figure>
  )
}
