import { homologueFor, type AnalogSite, type Target } from '../data/types'
import { earthGalleryKey, galleryUrl, imagesFor, useGallery, type GalleryImage } from '../data/gallery'
import { useEarthImage } from '../map/earthImages'
import { BODIES } from '../planet/bodies'
import { useLang } from '../i18n/useLang'
import Carousel, { type Slide } from './Carousel'
import DetailImage from './DetailImage'

function gallerySlide(image: GalleryImage, lang: 'es' | 'en', note?: string): Slide {
  return {
    id: image.key,
    kind: image.kind,
    src: galleryUrl(image),
    alt: image.title,
    caption: image.caption[lang],
    meta: [image.credit, image.date].filter(Boolean).join(' · '),
    sourceUrl: image.source_url,
    note,
  }
}

/** Earth: the Sentinel-2 crop of the exact spot first, then field, astronaut and satellite photos. */
export function EarthCarousel({ site }: { site: AnalogSite }) {
  const { lang, t } = useLang()
  const gallery = useGallery()
  const crop = useEarthImage(site)
  const slides: Slide[] = []
  if (crop)
    slides.push({
      id: 'crop',
      kind: 'sentinel',
      src: crop.url,
      alt: t('image.alt', { name: site.name }),
      caption: t('carousel.crop', { km: crop.widthKm }),
      meta: `${crop.label} · ${crop.credit}`,
    })
  const note = site.region ? t('carousel.regionNote') : undefined
  for (const image of imagesFor(gallery, earthGalleryKey(site))) slides.push(gallerySlide(image, lang, note))
  if (!slides.length) return <div className="carousel carousel-empty">{t('image.loading')}</div>
  return <Carousel key={site.id} slides={slides} label={t('carousel.earthLabel', { name: site.name })} />
}

/** Moon or Mars: rover, lander and orbital photos first, then the interactive 3D close-up. */
export function TargetCarousel({ site, body }: { site: AnalogSite; body: Target }) {
  const { lang, t } = useLang()
  const gallery = useGallery()
  const homologue = homologueFor(site, body)
  if (!homologue) return null
  const slides: Slide[] = imagesFor(gallery, homologue.id).map((image) => gallerySlide(image, lang))
  slides.push({
    id: 'globe',
    kind: 'globe',
    caption: t('carousel.globe'),
    meta: BODIES[body].imageryCredit,
    render: () => <DetailImage body={body} site={site} homologue={homologue} polarZoomOut={14} />,
  })
  return <Carousel key={`${site.id}-${body}`} slides={slides} label={t('carousel.targetLabel', { name: homologue.name })} />
}
