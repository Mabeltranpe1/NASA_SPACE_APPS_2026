import { useMemo, useState } from 'react'
import type { AnalogSite, Body, Homologue } from '../data/types'
import { BODIES } from '../planet/bodies'
import PlanetGlobe from './PlanetGlobe'
import { useLang } from '../i18n/useLang'
import { earthSnapshotUrl } from '../map/snapshot'
import { BODY_NAMES } from '../i18n/strings'

interface Props {
  body: Body
  site: AnalogSite
  homologue?: Homologue
}

export default function DetailImage({ body, site, homologue }: Props) {
  const { lang, t } = useLang()
  const [loadedUrl, setLoadedUrl] = useState<string | null>(null)
  const [failedUrl, setFailedUrl] = useState<string | null>(null)
  const [relief, setRelief] = useState(false)
  const point = useMemo(
    () => (body === 'tierra' ? { lat: site.lat, lng: site.lng } : homologue ? { lat: homologue.lat, lng: homologue.lng } : null),
    [body, site, homologue],
  )
  const markers = useMemo(
    () => (point ? [{ id: 'punto', lat: point.lat, lng: point.lng, color: '#ffffff', label: '' }] : []),
    [point],
  )

  if (body === 'tierra') {
    const snap = earthSnapshotUrl(site)
    return (
      <figure className="detail-image">
        {loadedUrl !== snap.url && failedUrl !== snap.url && <div className="image-loading">{t('image.loading')}</div>}
        {failedUrl === snap.url ? (
          <div className="image-loading">{t('image.failed')}</div>
        ) : (
          <img
            key={snap.url}
            src={snap.url}
            alt={t('image.alt', { name: site.name })}
            onLoad={() => setLoadedUrl(snap.url)}
            onError={() => setFailedUrl(snap.url)}
          />
        )}
        <figcaption>
          <strong>{site.name}</strong>
          <span>
            {snap.label} · {t('image.side', { km: snap.widthKm })} · NASA GIBS
          </span>
        </figcaption>
      </figure>
    )
  }

  if (!homologue || !point) {
    return (
      <figure className="detail-image empty">
        <div className="image-loading">{t('image.noHomologue', { body: BODY_NAMES[lang][body] })}</div>
      </figure>
    )
  }

  const cfg = BODIES[body]
  // Near the poles the camera goes higher to show the polar region instead of the stretched pole.
  const polar = Math.abs(point.lat) > 80
  const height = polar ? cfg.closeupHeight * 6 : undefined

  return (
    <figure className="detail-image">
      <PlanetGlobe body={body} markers={markers} focus={point} variant="closeup" relief={relief} closeupHeight={height} />
      {cfg.createReliefLayer && (
        <div className="view-toggle" role="group" aria-label={t('image.view')}>
          <button className={!relief ? 'active' : ''} onClick={() => setRelief(false)}>
            {t('image.imagery')}
          </button>
          <button className={relief ? 'active' : ''} onClick={() => setRelief(true)}>
            {t('image.relief')}
          </button>
        </div>
      )}
      <figcaption>
        <strong>
          {homologue.name}
          {homologue.approximate && <em> {t('image.approximate')}</em>}
        </strong>
        <span>{relief && cfg.reliefCredit ? cfg.reliefCredit : cfg.imageryCredit}</span>
        {polar && <span className="polar-note">{t('image.polar')}</span>}
      </figcaption>
    </figure>
  )
}
