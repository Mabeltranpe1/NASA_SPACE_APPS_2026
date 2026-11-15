import { useComparisons } from '../data/comparisons'
import { useLang } from '../i18n/useLang'
import { BODY_NAMES, FEATURE_NAMES_EN, SOURCE_PHRASES_EN, type Lang } from '../i18n/strings'
import { BODY_COLORS } from '../theme'

type L = Record<Lang, string>

const TEXT = {
  eyebrow: { es: 'Método', en: 'Method' },
  title: { es: 'Cómo medimos el parecido', en: 'How we measure similarity' },
  lead: {
    es: 'No basta con que un lugar se vea parecido. Describimos cada lugar de la Tierra, la Luna y Marte con las mismas variables físicas, medidas por satélites, y calculamos cuánto se parecen, en qué y dónde deja de valer la analogía.',
    en: 'Looking alike is not enough. We describe every place on Earth, the Moon and Mars with the same physical variables, measured from orbit, and compute how similar they are, in what, and where the analogy breaks down.',
  },
  steps: [
    {
      title: { es: '1 · Datos abiertos', en: '1 · Open data' },
      text: {
        es: 'La Tierra se divide en celdas de ~5 km con relieve a 200 m (NASADEM, Copernicus), temperatura y albedo (MODIS), lluvia (GPM IMERG), vegetación y tipo de roca (ASTER). La Luna y Marte usan LRO LOLA y Diviner, HRSC + MOLA, TES y el Mars Climate Database.',
        en: 'Earth is split into ~5 km cells with terrain at 200 m (NASADEM, Copernicus), temperature and albedo (MODIS), rain (GPM IMERG), vegetation and rock type (ASTER). The Moon and Mars use LRO LOLA and Diviner, HRSC + MOLA, TES and the Mars Climate Database.',
      },
    },
    {
      title: { es: '2 · Comparación', en: '2 · Comparison' },
      text: {
        es: 'Cada diferencia se divide por una tolerancia física (por ejemplo, 5° de pendiente) y se convierte en una similitud de 0 a 1. El puntaje combina todas las variables con pesos que puedes cambiar en la app.',
        en: 'Each difference is divided by a physical tolerance (for example, 5° of slope) and turned into a similarity from 0 to 1. The score combines every variable with weights you can change in the app.',
      },
    },
    {
      title: { es: '3 · Validación', en: '3 · Validation' },
      text: {
        es: 'Los análogos conocidos (Antártida, Atacama, Islandia…) se usan como control: el método debe ponerlos arriba, y lo hace. Además, cada lugar se prueba con 100 variaciones aleatorias de los pesos.',
        en: 'Known analogs (Antarctica, Atacama, Iceland…) are used as controls: the method must rank them high, and it does. Each place is also tested with 100 random weight variations.',
      },
    },
  ],
  formulaTitle: { es: 'La fórmula', en: 'The formula' },
  formulaNote: {
    es: 'x_T: valor en la Tierra · x_P: valor en la Luna o Marte · τ: tolerancia física · w: peso. 1 = idénticos.',
    en: 'x_T: Earth value · x_P: Moon or Mars value · τ: physical tolerance · w: weight. 1 = identical.',
  },
  rulesTitle: { es: 'Reglas para comparar con honestidad', en: 'Rules for an honest comparison' },
  rules: [
    {
      es: 'La elevación no se compara: cada cuerpo mide la altura desde un cero distinto.',
      en: 'Elevation is not compared: each body measures height from a different zero level.',
    },
    {
      es: 'Si ningún lugar de la Tierra alcanza un valor (la Luna está a 50–125 K), esa variable se muestra como límite y no entra en el puntaje.',
      en: 'If no place on Earth reaches a value (the Moon sits at 50–125 K), that variable is shown as a limit and is not scored.',
    },
    {
      es: 'Los descubrimientos se eligen por región, para que una sola zona no llene la lista.',
      en: 'Discoveries are picked per region, so a single area cannot fill the list.',
    },
    {
      es: 'La lluvia es exigente a propósito: en la Luna y en Marte no llueve.',
      en: 'Rain is strict on purpose: it does not rain on the Moon or Mars.',
    },
  ],
  sourcesTitle: { es: 'Variables y fuentes', en: 'Variables and sources' },
  variable: { es: 'Variable', en: 'Variable' },
  earth: { es: 'Tierra', en: 'Earth' },
  limitsTitle: { es: 'Lo que la Tierra no puede reproducir', en: 'What Earth cannot reproduce' },
  limits: {
    es: 'Gravedad (0,17 g en la Luna, 0,38 g en Marte), vacío o atmósfera tenue (6 hPa en Marte), radiación sin campo magnético y días de 29,5 días terrestres en la Luna. Por eso hablamos de análogos parciales: sirven para ensayar operaciones, instrumentos y procesos, no para reproducir el ambiente completo.',
    en: 'Gravity (0.17 g on the Moon, 0.38 g on Mars), vacuum or a thin atmosphere (6 hPa on Mars), radiation without a magnetic field, and 29.5-Earth-day days on the Moon. That is why we talk about partial analogs: they are for rehearsing operations, instruments and processes, not for reproducing the whole environment.',
  },
  caveatsTitle: { es: 'Limitaciones conocidas', en: 'Known limitations' },
  caveats: [
    {
      es: 'La lluvia de IMERG es menos confiable por encima de 60° de latitud (Antártida, Groenlandia).',
      en: 'IMERG rain is less reliable above 60° latitude (Antarctica, Greenland).',
    },
    {
      es: 'La temperatura de Marte viene de un modelo (Mars Climate Database), no de una medición directa.',
      en: 'Mars temperature comes from a model (Mars Climate Database), not a direct measurement.',
    },
    {
      es: 'La mineralogía (EMIT) aún no está procesada: hay escenas disponibles, falta el análisis.',
      en: 'Mineralogy (EMIT) is not processed yet: scenes are available, the analysis is pending.',
    },
  ],
  teamTitle: { es: 'Equipo', en: 'Team' },
  team: [
    {
      es: 'Marco · búsqueda global y comparador (compare.py)',
      en: 'Marco · global search and comparator (compare.py)',
    },
    {
      es: 'Santiago · caracterización de Colombia: relieve a 200 m, índice PAI, Sentinel-2 y EMIT',
      en: 'Santiago · Colombian characterization: 200 m terrain, PAI index, Sentinel-2 and EMIT',
    },
    { es: 'Plataforma web · globos 3D, visualización y despliegue', en: 'Web platform · 3D globes, visualization and deployment' },
  ],
} satisfies Record<string, unknown>

const tx = (v: L, lang: Lang) => v[lang]

export default function MethodView() {
  const { lang } = useLang()
  const state = useComparisons()
  const data = state.status === 'ready' ? state.data : null
  const moon = data?.targets.filter((t) => t.body === 'luna').length ?? 0
  const mars = data?.targets.filter((t) => t.body === 'marte').length ?? 0
  const src = (s: string | undefined) => (s ? (lang === 'en' ? (SOURCE_PHRASES_EN[s] ?? s) : s) : '—')

  return (
    <div className="page method">
      <header className="page-hero">
        <p className="eyebrow">{tx(TEXT.eyebrow, lang)}</p>
        <h1>{tx(TEXT.title, lang)}</h1>
        <p className="page-lead">{tx(TEXT.lead, lang)}</p>
        {data && (
          <div className="stat-row">
            <Stat value={data.n_cells.toLocaleString(lang)} label={lang === 'es' ? 'celdas de la Tierra' : 'Earth cells'} />
            <Stat value={String(data.n_regions ?? '—')} label={lang === 'es' ? 'regiones' : 'regions'} />
            <Stat value={String(moon)} label={lang === 'es' ? 'sitios de la Luna' : 'Moon sites'} color={BODY_COLORS.luna} />
            <Stat value={String(mars)} label={lang === 'es' ? 'sitios de Marte' : 'Mars sites'} color={BODY_COLORS.marte} />
          </div>
        )}
      </header>

      <section className="step-grid">
        {TEXT.steps.map((s) => (
          <article key={s.title.es} className="glass tile">
            <h3>{tx(s.title, lang)}</h3>
            <p>{tx(s.text, lang)}</p>
          </article>
        ))}
      </section>

      <section className="glass tile formula">
        <h2>{tx(TEXT.formulaTitle, lang)}</h2>
        <div className="formula-lines">
          <code>
            d<sub>f</sub> = (x<sub>T</sub> − x<sub>P</sub>) / τ<sub>f</sub>
          </code>
          <code>
            s<sub>f</sub> = e<sup>−|d<sub>f</sub>|</sup>
          </code>
          <code>
            S = e<sup>−√(Σ w<sub>f</sub> d<sub>f</sub>² / Σ w<sub>f</sub>)</sup>
          </code>
        </div>
        <p className="muted small">{tx(TEXT.formulaNote, lang)}</p>
      </section>

      <section className="two-col">
        <article className="glass tile">
          <h2>{tx(TEXT.rulesTitle, lang)}</h2>
          <ul className="check-list">
            {TEXT.rules.map((r) => (
              <li key={r.es}>{tx(r, lang)}</li>
            ))}
          </ul>
        </article>
        <article className="glass tile">
          <h2>{tx(TEXT.limitsTitle, lang)}</h2>
          <p>{tx(TEXT.limits, lang)}</p>
          <h2>{tx(TEXT.caveatsTitle, lang)}</h2>
          <ul className="warn-list">
            {TEXT.caveats.map((c) => (
              <li key={c.es}>{tx(c, lang)}</li>
            ))}
          </ul>
        </article>
      </section>

      {data && (
        <section className="glass tile">
          <h2>{tx(TEXT.sourcesTitle, lang)}</h2>
          <div className="table-scroll">
            <table className="source-table">
              <thead>
                <tr>
                  <th>{tx(TEXT.variable, lang)}</th>
                  <th>{tx(TEXT.earth, lang)}</th>
                  <th>{BODY_NAMES[lang].luna}</th>
                  <th>{BODY_NAMES[lang].marte}</th>
                </tr>
              </thead>
              <tbody>
                {data.features.map((f) => (
                  <tr key={f.id}>
                    <th scope="row">
                      {lang === 'en' ? (FEATURE_NAMES_EN[f.id] ?? f.label) : f.label}
                      {f.unit && <small> ({f.unit})</small>}
                    </th>
                    <td>{src(f.source_earth)}</td>
                    <td>{src(f.source_target.luna)}</td>
                    <td>{src(f.source_target.marte)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="glass tile">
        <h2>{tx(TEXT.teamTitle, lang)}</h2>
        <ul className="team-list">
          {TEXT.team.map((m) => (
            <li key={m.es}>{tx(m, lang)}</li>
          ))}
        </ul>
        <p className="muted small">
          NASA GIBS · NASA Moon Trek · NASA Mars Trek · NASA Earthdata · ESA Copernicus (Sentinel-2) · Microsoft Planetary Computer · USGS Astrogeology · LMD Mars Climate Database
        </p>
      </section>
    </div>
  )
}

export function Stat({ value, label, color }: { value: string; label: string; color?: string }) {
  return (
    <div className="stat">
      <span className="stat-value" style={color ? { color } : undefined}>
        {value}
      </span>
      <span className="stat-label">{label}</span>
    </div>
  )
}
