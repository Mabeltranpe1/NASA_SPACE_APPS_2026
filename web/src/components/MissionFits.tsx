import { useState } from 'react'
import { fitsWithWeights, switchedOffFor, topMissions } from '../comparator/missions'
import { useMissionData } from '../data/missionData'
import type { Target } from '../data/types'
import { MISSION_TEXT, MISSION_UI } from '../i18n/missions'
import { useLang } from '../i18n/useLang'
import { SIMILARITY_COLOR } from '../theme'
import { MissionIcon } from './MissionIcons'

/**
 * "Suitable for" block of the site panel: which kinds of missions this Earth place could host as an
 * analog of one Moon/Mars site. Same score as the rest of the app, recomputed with each mission's
 * weights from the per-variable similarity, and compared with the best place Earth has for that
 * mission (public/data/missions.json, 100 = the best on Earth).
 */
export default function MissionFits({ targetId, body, sim }: { targetId: string; body: Target; sim: Record<string, number | null> }) {
  const { lang } = useLang()
  const data = useMissionData()
  const [all, setAll] = useState(false)
  if (!data) return null
  const weights = data.weights[body === 'luna' ? 'Moon' : 'Mars']
  const fits = fitsWithWeights(weights, sim, data.reference[targetId])
  if (!fits.length) return null
  const top = topMissions(fits)
  const ui = MISSION_UI[lang]
  const pct = (v: number) => Math.min(100, Math.round(v * 100))
  const tip = (m: (typeof fits)[number]) =>
    ui.fitTip
      .replace('{mission}', MISSION_TEXT[lang][m.mission].name)
      .replace('{score}', String(Math.round(m.score * 100)))
      .replace('{rel}', String(pct(m.relative)))
      .replace(/ ?Clic.*$| ?Click.*$/, '')
  const notes = top.map((m) => MISSION_TEXT[lang][m.mission].note).filter((n): n is string => Boolean(n))
  // e.g. "habitats" on the Moon: it weighs the temperature, which is not compared there.
  if (top.some((m) => switchedOffFor(weights[m.mission], m.mission).length > 0)) notes.push(ui.moonTemp)
  return (
    <div className="mission-panel">
      <h4 className="panel-sub">{ui.panelTitle}</h4>
      {top.length === 0 && <p className="muted small">{ui.panelNone}</p>}
      <p className="mission-fits">
        {top.map((m) => (
          <span key={m.mission} className="pill mission static" title={tip(m)}>
            <MissionIcon id={m.mission} size={14} /> {MISSION_TEXT[lang][m.mission].short}
          </span>
        ))}
      </p>
      {all && (
        <ul className="dim-bars mission-bars">
          {fits.map((m) => (
            <li key={m.mission} title={tip(m)}>
              <span className="dim-name">
                <MissionIcon id={m.mission} size={14} /> {MISSION_TEXT[lang][m.mission].short}
              </span>
              <span className="mini-track">
                <span className="mini-fill" style={{ width: `${pct(m.relative)}%`, background: SIMILARITY_COLOR }} />
              </span>
              <span className="dim-value">{pct(m.relative)}</span>
            </li>
          ))}
        </ul>
      )}
      <button className="link small" onClick={() => setAll((v) => !v)}>
        {all ? ui.panelFewer : ui.panelAll.replace('{n}', String(fits.length))}
      </button>
      {all && <p className="muted small">{ui.panelHint}</p>}
      {notes.map((n) => (
        <p key={n} className="mission-note small">⚠ {n}</p>
      ))}
    </div>
  )
}
