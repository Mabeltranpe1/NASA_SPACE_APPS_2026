import { useComparisons } from '../data/comparisons'
import { useLang } from '../i18n/useLang'
import { BODY_NAMES, FEATURE_NAMES_EN, SOURCE_PHRASES_EN, type Lang } from '../i18n/strings'
import { BODY_COLORS } from '../theme'

type L = Record<Lang, string>

const TEXT = {
  eyebrow: { es: 'Método', en: 'Method' },
  title: { es: 'Cómo medimos el parecido', en: 'How we measure similarity' },
  lead: {
    es: 'Comparamos celdas terrestres seleccionadas con objetivos lunares y marcianos mediante observaciones, modelos y estimaciones identificadas. La investigación regional conserva su propia geometría, calidad y metodología para explicar qué se parece y dónde termina la analogía.',
    en: 'We compare selected Earth cells with lunar and Martian targets using identified observations, models and estimates. Regional research retains its own geometry, quality and methods to explain what is similar and where the analogy ends.',
  },
  steps: [
    {
      title: { es: '1 · Datos abiertos', en: '1 · Open data' },
      text: {
        es: 'La base global usa celdas de 0,05° (el ancho varía con la latitud), relieve a 200 m, MODIS, IMERG/MERRA-2 y ASTER. La investigación de Colombia añade ventanas propias de 10×10 km, POWER, CHIRPS, WorldCover, Sentinel-2, SGC y EMIT. Los objetivos planetarios conservan sus fuentes LOLA, Diviner, HRSC/MOLA, TES y MCD.',
        en: 'The global database uses 0.05° cells (width varies with latitude), 200 m terrain, MODIS, IMERG/MERRA-2 and ASTER. Colombian research adds independent 10×10 km windows, POWER, CHIRPS, WorldCover, Sentinel-2, SGC and EMIT. Planetary targets retain their LOLA, Diviner, HRSC/MOLA, TES and MCD sources.',
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
      title: { es: '3 · Sensibilidad y controles', en: '3 · Sensitivity and controls' },
      text: {
        es: 'Se conservan análogos conocidos como referencias y se ejecutan 100 variaciones de pesos para el puntaje web. Esa sensibilidad no es incertidumbre instrumental ni validación de campo. Las coincidencias minerales y los resultados piloto mantienen sus indicadores de calidad.',
        en: 'Known analogs remain as references, and the web score uses 100 weight variations. This sensitivity is neither instrument uncertainty nor field validation. Mineral matches and pilot results retain their quality indicators.',
      },
    },
  ],
  formulaTitle: { es: 'La fórmula', en: 'The formula' },
  formulaNote: {
    es: 'x_T: Tierra · x_P: objetivo · τ: tolerancia · w: peso. La precipitación se transforma con ln(1+x). 1 significa igualdad de las variables activas, no equivalencia física completa.',
    en: 'x_T: Earth · x_P: target · τ: tolerance · w: weight. Precipitation uses ln(1+x). 1 means equality of active variables, not complete physical equivalence.',
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
      es: 'En la base ampliada se usa MERRA-2 para precipitación a |latitud|≥60°; se conserva como reanálisis, no como una medición local. Los calendarios heredados requieren revisar esa corrección.',
      en: 'The expanded grid uses MERRA-2 precipitation at |latitude|≥60°; it remains a reanalysis, not a local measurement. Legacy seasonal calendars require review of this correction.',
    },
    {
      es: 'La temperatura de Marte viene de un modelo (Mars Climate Database), no de una medición directa.',
      en: 'Mars temperature comes from a model (Mars Climate Database), not a direct measurement.',
    },
    {
      es: 'EMIT está procesado como coincidencias provisionales de biblioteca. THEMIS es piloto; CRISM Phoenix no tiene datos calificados. La Guajira contiene agua dentro de su ventana, y la estabilidad de hielo Diviner es modelada.',
      en: 'EMIT is processed as provisional library matches. THEMIS is a pilot; Phoenix CRISM has no qualified data. La Guajira includes water in its window, and Diviner ice stability is modeled.',
    },
  ],
  teamTitle: { es: 'Equipo', en: 'Team' },
  team: [
    {
      es: 'Marco (Mabeltranpe1) · investigación global, adquisición y comparador',
      en: 'Marco (Mabeltranpe1) · global research, acquisition and comparator',
    },
    {
      es: 'Santiago (santiago-851) · caracterización regional, PAI y productos científicos complementarios',
      en: 'Santiago (santiago-851) · regional characterization, PAI and complementary scientific products',
    },
    { es: 'Sebastián (Ssalazarp420) · interfaz, mapas, visualización e integración funcional', en: 'Sebastián (Ssalazarp420) · interface, maps, visualization and functional integration' },
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

      <section className="glass tile">
        <h2>{lang === 'es' ? 'Tres resultados con alcances diferentes' : 'Three results with different scopes'}</h2>
        <p>{lang === 'es' ? 'El ranking internacional conserva el índice global completo de Marco (0–1). El puntaje web compara las dimensiones activas y muestra las exclusiones por cuerpo. El PAI regional (0–100) usa solo seis descriptores topográficos y normalización sobre seis candidatos colombianos. No se sustituyen ni se promedian.' : "The international ranking preserves Marco's full global index (0–1). The web score compares active dimensions and shows exclusions by body. The regional PAI (0–100) uses only six terrain descriptors and normalization fitted to six Colombian candidates. These scores neither replace nor average each other."}</p>
        <code>PAI = 100 / (1 + √Σ w · (zA − zB)²)</code>
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
