import type { ReactNode } from 'react'
import type { MissionId } from '../comparator/missions'
import './Missions.css'

/**
 * One small line icon per mission type, drawn like Icons.tsx (24 × 24 grid, 1.7 stroke,
 * currentColor). Decorative: always paired with the mission's name.
 */
function Svg({ size = 18, children }: { size?: number; children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="mission-icon"
      aria-hidden="true"
    >
      {children}
    </svg>
  )
}

const PATHS: Record<MissionId, ReactNode> = {
  // Six-wheeled rover with a camera mast.
  rover: (
    <>
      <path d="M4 15.5h16l-1.5-4.5h-13z" />
      <path d="M9 11V6.5M7 6.5h4.5" />
      <path d="m15 11 2.5-4" />
      <circle cx="6" cy="18.5" r="1.8" />
      <circle cx="12" cy="18.5" r="1.8" />
      <circle cx="18" cy="18.5" r="1.8" />
    </>
  ),
  // Pickaxe next to a crystal: mining / in-situ resources.
  isru: (
    <>
      <path d="M4 20 14.8 9.2" />
      <path d="M10.5 4.4Q18.8 4.6 19.4 12.6" />
      <path d="m15.5 22.2-1.6-3 1.6-3h3.2l1.6 3-1.6 3z" />
      <path d="M17.1 16.2v6" />
    </>
  ),
  // Dome habitat with a door, a window and an antenna.
  habitat: (
    <>
      <path d="M3.5 19a8.5 8.5 0 0 1 17 0" />
      <path d="M2 19h20" />
      <path d="M10 19v-3a2 2 0 0 1 4 0v3" />
      <circle cx="16.5" cy="14.5" r="1" />
      <path d="m7.5 12.5-2-3.5" />
    </>
  ),
  // Thermometer between a sun and frost: hot/cold cycles.
  thermal: (
    <>
      <path d="M10 14.2V5a2 2 0 0 1 4 0v9.2a3.6 3.6 0 1 1-4 0z" />
      <path d="M12 9.5v7" />
      <circle cx="18.5" cy="6" r="2" />
      <path d="M18.5 1.8v.5M18.5 9.7v.5M22.7 6h-.5M21.5 3l-.4.4M21.5 9l-.4-.4" />
      <path d="M5 7v5M3 8.5l4 2M3 10.5l4-2" />
    </>
  ),
  // Flask with microbes: science and astrobiology.
  science: (
    <>
      <path d="M9 3h6M10 3v6l-5.2 9.3A1.8 1.8 0 0 0 6.4 21h11.2a1.8 1.8 0 0 0 1.6-2.7L14 9V3" />
      <path d="M7.3 15h9.4" />
      <circle cx="10.5" cy="18" r="1" />
      <circle cx="14" cy="17.2" r=".7" />
    </>
  ),
  // Quadcopter seen from above.
  drone: (
    <>
      <rect x="9.5" y="9.5" width="5" height="5" rx="1.2" />
      <path d="M9.5 9.5 7.5 7.5M14.5 9.5l2-2M9.5 14.5l-2 2M14.5 14.5l2 2" />
      <circle cx="6" cy="6" r="2.6" />
      <circle cx="18" cy="6" r="2.6" />
      <circle cx="6" cy="18" r="2.6" />
      <circle cx="18" cy="18" r="2.6" />
    </>
  ),
  // Capsule on its legs over a landing pad.
  landing: (
    <>
      <path d="M12 2.5c2 1.6 3 4 3 7v4H9v-4c0-3 1-5.4 3-7z" />
      <path d="M9 11.5 6.5 16M15 11.5l2.5 4.5M12 13.5V16" />
      <path d="M3 20h18M6 18h12" />
    </>
  ),
}

export function MissionIcon({ id, size }: { id: MissionId; size?: number }) {
  return <Svg size={size}>{PATHS[id]}</Svg>
}
