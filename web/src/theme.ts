import type { Body } from './data/types'

/**
 * Identity colors for the three bodies. Validated with the dataviz palette
 * checker on the dark surface #0d111c (all checks pass; Moon↔Mars sits in the
 * 6–8 ΔE deutan band, so every use carries a text label next to the color).
 */
export const BODY_COLORS: Record<Body, string> = {
  tierra: '#3d8ef0',
  luna: '#b08f24',
  marte: '#cf4a3c',
}

/** Single sequential hue for similarity magnitudes (not an identity color). */
export const SIMILARITY_COLOR = '#2fa58f'
