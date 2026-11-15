import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { homologueFor, siteTargets, type AnalogSite, type Target } from '../data/types'
import { BODY_COLORS } from '../theme'
import { useLang } from '../i18n/useLang'
import { BODY_NAMES } from '../i18n/strings'
import { EarthCarousel, TargetCarousel } from './PlaceCarousels'
import { IconClose } from './Icons'

interface Props {
  site: AnalogSite
  /** Moon/Mars body shown first on the right. */
  initialBody: Target | null
  onClose: () => void
}

/** Pop-up with the Earth place on the left and its Moon or Mars counterpart on the right. */
export default function ImageCompareModal({ site, initialBody, onClose }: Props) {
  const { lang, t } = useLang()
  const targets = siteTargets(site)
  const [body, setBody] = useState<Target | null>(
    initialBody && targets.includes(initialBody) ? initialBody : (targets[0] ?? null),
  )
  const closeRef = useRef<HTMLButtonElement>(null)
  const homologue = body ? homologueFor(site, body) : undefined

  // Esc closes; focus goes to the close button and back to the opener on close.
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null
    closeRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
      }
    }
    window.addEventListener('keydown', onKey)
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = overflow
      opener?.focus?.()
    }
  }, [onClose])

  return createPortal(
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal glass"
        role="dialog"
        aria-modal="true"
        aria-labelledby="compare-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="modal-head">
          <div>
            <p className="eyebrow">{t('image.compare')}</p>
            <h2 id="compare-title" className="pair-heading">
              <span>
                <span className="dot" style={{ background: BODY_COLORS.tierra }} /> {site.name}
              </span>
              {homologue && body && (
                <span>
                  <span className="vs">≈</span>
                  <span className="dot" style={{ background: BODY_COLORS[body] }} /> {homologue.name}
                </span>
              )}
            </h2>
          </div>
          <div className="modal-tools">
            {targets.length > 1 && (
              <div className="seg" role="group" aria-label={t('body.aria')}>
                {targets.map((b) => (
                  <button key={b} className={body === b ? 'active' : ''} aria-pressed={body === b} onClick={() => setBody(b)}>
                    <span className="dot" style={{ background: BODY_COLORS[b] }} />
                    {BODY_NAMES[lang][b]}
                  </button>
                ))}
              </div>
            )}
            <button ref={closeRef} className="icon-btn" onClick={onClose} aria-label={t('intro.close')} title={t('intro.close')}>
              <IconClose size={18} />
            </button>
          </div>
        </header>

        <div className="modal-images">
          <EarthCarousel site={site} />
          {body && homologue ? (
            <TargetCarousel key={body} site={site} body={body} />
          ) : (
            <figure className="detail-image empty">
              <div className="image-loading">{t('insight.noData')}</div>
            </figure>
          )}
        </div>
        <p className="muted small modal-note">{t('image.scaleNote')}</p>
      </div>
    </div>,
    document.body,
  )
}
