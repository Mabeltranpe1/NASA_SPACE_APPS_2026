import { useState } from 'react'
import { useLang } from '../i18n/useLang'
import { SCIENCE_STRINGS, SOURCE_EVIDENCE_LABELS } from '../i18n/science'
import { useScientificStudy, type ScienceReference, type ScienceSection, type ScienceStudy, type ScienceValue } from '../data/science'

const TABLE_COLUMNS: Record<string, string[]> = {
  geology: ['unit_symbol', 'description', 'geological_age', 'pct_study_area', 'pct_mapped_area'],
  emit_coverage: ['spectral_group', 'valid_observations', 'accepted_observations', 'accepted_pct_of_valid_observations', 'mean_valid_bins_touched_pct_200m', 'status'],
  emit_minerals: ['mineral_name', 'spectral_group', 'detection_count', 'detection_pct_of_valid_observations', 'band_depth_mean', 'fit_corrected_mean', 'band_depth_uncertainty_mean', 'status'],
  emit_quality: ['acquisition_utc', 'spectral_group', 'valid_observations', 'accepted_observations', 'valid_bins_touched_pct_200m', 'l2a_cloud_mask_applied', 'marine_mask_applied', 'status'],
  emit_scene_matches: ['acquisition_utc', 'spectral_group', 'mineral_name', 'detection_count', 'detection_pct_of_valid_observations'],
  crism: ['parameter', 'science_name', 'valid_area_pct', 'parameter_mean', 'parameter_std', 'quality_status'],
  crism_all: ['parameter', 'science_name', 'valid_area_pct', 'parameter_mean', 'quality_status'],
  crism_quality: ['science_name', 'image_overlap_pct', 'native_pixel_x_m', 'native_pixel_y_m', 'status', 'error'],
  themis: ['illumination', 'accepted_scene_count', 'brightness_scene_mean_k', 'minimum_scene_valid_area_pct', 'summary_status'],
  themis_scenes: ['observation_key', 'utc', 'illumination_used', 'band_group', 'valid_area_pct', 'brightness_mean_k', 'quality_status'],
}

export default function ScientificPanel({ reference, initialOpen = false }: { reference: ScienceReference | null | undefined; initialOpen?: boolean }) {
  const { lang } = useLang()
  const copy = SCIENCE_STRINGS[lang]
  const [open, setOpen] = useState(initialOpen)
  const state = useScientificStudy(open ? reference : null)
  if (!reference) return null
  return (
    <details className="fold science-panel" open={open} onToggle={(event) => setOpen(event.currentTarget.open)}>
      <summary>{copy.title} · {reference.name[lang]}</summary>
      {open && (
        <div className="science-body">
          {reference.overlap_study_pct != null && <p className="science-note">{copy.overlap}: {reference.overlap_study_pct.toLocaleString(lang, { maximumFractionDigits: 2 })} %. {copy.reference}</p>}
          {(state.status === 'loading' || state.status === 'idle') && <p role="status">{copy.loading}</p>}
          {state.status === 'error' && <p role="alert">{copy.error}</p>}
          {state.status === 'ready' && <StudyContent key={state.data.id} study={state.data} />}
        </div>
      )}
    </details>
  )
}

function StudyContent({ study }: { study: ScienceStudy }) {
  const { lang } = useLang()
  const copy = SCIENCE_STRINGS[lang]
  const [selected, setSelected] = useState('topography')
  const [related, setRelated] = useState<ScienceReference | null>(null)
  const current = study.sections.find((s) => s.id === selected)
  const format = (value: ScienceValue | undefined, unit = '', column = '') => {
    if (value == null) return copy.noData
    if (typeof value === 'boolean') return value ? copy.yes : copy.no
    if (typeof value === 'number') {
      const digits = String(value)
      if (column.includes('period_') && /^\d{8}$/.test(digits)) return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6)}`
      if (column.endsWith('_year')) return digits
      return `${value.toLocaleString(lang, { maximumFractionDigits: 5 })}${unit ? ` ${lang === 'en' ? unit.replace('año', 'year') : unit}` : ''}`
    }
    return value
  }
  const figure = study.assets.find((asset) => asset.source_file.endsWith('_analysis.png'))
  return (
    <section className="science-study" aria-label={`${copy.details}: ${study.name[lang]}`}>
      <h3>{study.name[lang]}</h3>
      <p className="hint">{copy.support}</p>
      {study.geometry && <p className="science-coordinates">{study.geometry.latitude.toFixed(5)}°, {study.geometry.longitude_east_signed_deg.toFixed(5)}° · {study.geometry.nominal_window_km} × {study.geometry.nominal_window_km} km · {study.geometry.resolution_m[0]} m</p>}
      <div className="science-quality" aria-label={copy.quality}>
        {study.quality_flags.map((f) => <p className={f.level === 'warning' ? 'science-warning' : 'hint'} key={f.code}>{f.level === 'warning' ? '⚠ ' : ''}{f.message[lang]}</p>)}
      </div>
      <div className="science-tabs" role="tablist" aria-label={copy.details}>
        {study.sections.map((s) => <button key={s.id} role="tab" aria-selected={selected === s.id} className={`chip ${selected === s.id ? 'active' : ''}`} onClick={() => setSelected(s.id)}>{s.title[lang]}</button>)}
        <button role="tab" aria-selected={selected === 'pai'} className={`chip ${selected === 'pai' ? 'active' : ''}`} onClick={() => setSelected('pai')}>{copy.pai}</button>
      </div>
      {current && <SectionValues key={current.id} section={current} format={format} />}
      {selected === 'spectral' && current && <ReflectanceChart section={current} />}
      {selected === 'topography' && figure && <figure className="science-figure"><a href={figure.url} target="_blank" rel="noreferrer"><img src={figure.url} alt={`${study.name[lang]} — ${copy.figure}`} loading="lazy" /></a><figcaption>{copy.figure}</figcaption></figure>}
      {selected === 'pai' && (
        <section className="science-pai">
          <h4>{copy.pai}</h4>
          <p className="science-note">{study.pai.model.note[lang]}</p>
          <code>{study.pai.model.equation}</code>
          <p className="hint">{study.pai.model.features.map((f) => `${f.id}: ${f.weight}`).join(' · ')}</p>
          <div className="science-table-scroll"><table><thead><tr><th>{study.planet === 'earth' ? copy.target : copy.candidate}</th><th>PAI / 100</th><th>{copy.position}</th><th>{copy.distance}</th></tr></thead><tbody>
            {study.pai.results.map((r) => <tr key={`${r.target}-${r.candidate}`}><th scope="row">{study.planet === 'earth' ? <button className="link" title={copy.openStudy} onClick={() => setRelated({ url: r.study_url, name: { es: r.target.replaceAll('_', ' '), en: r.target.replaceAll('_', ' ') } })}>{r.target.replaceAll('_', ' ')}</button> : r.candidate.replaceAll('_', ' ')}</th><td>{format(r.PAI)}</td><td>{r.rank_among_six} / 6</td><td>{format(r.distance)}</td></tr>)}
          </tbody></table></div>
          {related && <><button className="link" onClick={() => setRelated(null)}>{copy.back}</button><ScientificPanel key={related.url} reference={related} initialOpen /></>}
        </section>
      )}
      <details className="fold science-sources"><summary>{copy.sources}</summary><ul>{study.sources.map((source) => <li key={source.id}><a href={source.url} target="_blank" rel="noreferrer">{source.name}</a> · {source.institution}<small>{SOURCE_EVIDENCE_LABELS[source.evidence_type]?.[lang] ?? source.evidence_type}</small></li>)}</ul></details>
      <details className="fold science-assets"><summary>{copy.downloads}</summary><ul>{study.assets.map((asset) => <li key={`${asset.url}-${asset.kind ?? ''}`}><a href={asset.url} target="_blank" rel="noreferrer" download={asset.source_file.split('/').at(-1)}>{asset.source_file.split('/').at(-1)}{asset.kind === 'regional_geology' ? ` · ${study.name[lang]}` : ''}</a>{asset.bytes != null && <small>{(asset.bytes / 1024).toFixed(1)} KB</small>}</li>)}</ul></details>
    </section>
  )
}

function SectionValues({ section, format }: { section: ScienceSection; format: (v: ScienceValue | undefined, unit?: string, column?: string) => string | number }) {
  const { lang } = useLang()
  const copy = SCIENCE_STRINGS[lang]
  const [all, setAll] = useState(false)
  const columns = TABLE_COLUMNS[section.id]
  const fields = columns ? columns.map((id) => section.fields.find((f) => f.id === id)).filter((f) => f !== undefined) : section.fields.filter((f) => !['region', 'planet', 'system:index', '.geo', 'source', 'source_url', 'climate_source', 'footprint_dem', 'window_source'].includes(f.id))
  const records = all ? section.records : section.records.slice(0, 10)
  return (
    <section className="science-section" role="tabpanel" aria-label={section.title[lang]}>
      <h4>{section.title[lang]}</h4>
      {!section.records.length ? <p>{copy.unavailable}</p> : columns ? (
        <div className="science-table-scroll"><table><thead><tr>{fields.map((f) => <th key={f.id}>{f.label[lang]}{f.unit ? ` (${f.unit})` : ''}</th>)}</tr></thead><tbody>{records.map((row, i) => <tr key={i}>{fields.map((f) => <td key={f.id}>{format(row[f.id], '', f.id)}</td>)}</tr>)}</tbody></table></div>
      ) : (
        <dl className="char-list science-values">{fields.map((f) => <div key={f.id}><dt title={f.original_column}>{f.label[lang]}</dt><dd>{format(section.records[0]?.[f.id], f.unit, f.id)}</dd></div>)}</dl>
      )}
      {columns && section.records.length > 10 && <button className="link" aria-expanded={all} onClick={() => setAll(!all)}>{all ? copy.showLess : `${copy.showAll} (${section.records.length})`}</button>}
      <details className="fold science-provenance"><summary>{copy.provenance}</summary><div className="science-table-scroll"><table><thead><tr><th>{copy.variable}</th><th>{copy.original}</th><th>{copy.definition}</th><th>{copy.compatibility}</th></tr></thead><tbody>{section.fields.map((f) => <tr key={f.id}><th scope="row">{f.label[lang]} {f.unit}</th><td><code>{f.original_column}</code></td><td>{f.definition[lang]}<br />{f.method_text[lang]}<br />{f.support_text[lang]}<br />{f.period}<br />{f.source_ids.join(', ')}</td><td>{f.compatibility_text[lang]}{f.global_candidate ? ` (${f.global_candidate})` : ''}</td></tr>)}</tbody></table></div></details>
    </section>
  )
}

function ReflectanceChart({ section }: { section: ScienceSection }) {
  const { lang } = useLang()
  const row = section.records[0]
  if (!row) return null
  const bands = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12']
  const values = bands.map((b) => row[`${b}_mean`])
  const finite = values.filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
  if (!finite.length) return null
  const max = Math.max(.1, ...finite) * 1.1
  return <figure className="science-spectrum"><svg viewBox="0 0 600 180" role="img" aria-label={SCIENCE_STRINGS[lang].spectrum}><line x1="30" y1="145" x2="580" y2="145" stroke="currentColor" />{values.map((value, i) => typeof value === 'number' ? <g key={bands[i]}><rect x={42 + i * 53} y={145 - value / max * 125} width="26" height={value / max * 125} fill="#7ad8d0"><title>{bands[i]}: {value}</title></rect><text x={55 + i * 53} y="166" textAnchor="middle" fill="currentColor" fontSize="12">{bands[i]}</text></g> : null)}</svg><figcaption>{SCIENCE_STRINGS[lang].spectrum}</figcaption></figure>
}
