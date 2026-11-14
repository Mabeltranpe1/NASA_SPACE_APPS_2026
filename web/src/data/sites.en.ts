import type { AnalogSite, Homologue } from './types'
import type { Lang } from '../i18n/strings'
import { COUNTRY_NAMES_EN } from '../i18n/strings'

type SiteText = Pick<AnalogSite, 'name' | 'analogOf' | 'similarities' | 'limitations' | 'missionUse'>
type HomologueText = Pick<Homologue, 'name' | 'note'>

/** English text for the catalog (web/src/data/sites.ts holds the Spanish originals). */
const SITES_EN: Record<string, SiteText> = {
  'atacama-yungay': {
    name: 'Atacama Desert (Yungay)',
    analogOf: 'Hyper-arid soils of Mars',
    similarities: 'One of the driest places on Earth: oxidizing soils with very little microbial life, similar to Martian regolith.',
    limitations: 'Dense atmosphere, mild temperatures and magnetic protection against radiation.',
    missionUse: 'Testing rovers and drills, and detecting biosignatures in extremely dry conditions.',
  },
  'mcmurdo-dry-valleys': {
    name: 'McMurdo Dry Valleys',
    analogOf: 'Mid and high latitudes of Mars',
    similarities: 'Extreme cold and dryness, with permafrost, buried ice and wind erosion.',
    limitations: 'High atmospheric pressure and occasional seasonal liquid water.',
    missionUse: 'Studying subsurface ice and permafrost life, and testing instruments in extreme cold.',
  },
  'haughton-crater': {
    name: 'Haughton Crater (Devon Island)',
    analogOf: 'Polar impact craters',
    similarities: 'A well-preserved impact crater about 23 km wide, with impact breccias and a polar desert environment.',
    limitations: 'There is vegetation and Earth gravity; the cold is far less extreme than in permanently shadowed craters.',
    missionUse: 'Simulating human operations (Haughton-Mars Project), mobility and logistics.',
  },
  'death-valley': {
    name: 'Death Valley',
    analogOf: 'Evaporite deposits and alluvial fans on Mars',
    similarities: 'Alluvial fans, salt flats and evaporite deposits comparable to Martian terrains.',
    limitations: 'Extreme heat, the opposite of the cold on Mars.',
    missionUse: 'Interpreting sedimentary landforms and calibrating spectrometers.',
  },
  'mauna-kea': {
    name: 'Mauna Kea (slopes)',
    analogOf: 'Basaltic lunar regolith',
    similarities: 'Basaltic materials and tephra similar to the regolith of the lunar maria.',
    limitations: 'Atmosphere, water and weathering; no vacuum and no micrometeorite bombardment.',
    missionUse: 'Testing in-situ resource utilization (ISRU), construction and rovers.',
  },
  'rio-tinto': {
    name: 'Río Tinto',
    analogOf: 'Meridiani Planum (iron sulfates)',
    similarities: 'Acidic, iron-rich waters that form jarosite and other sulfates detected on Mars.',
    limitations: 'Abundant liquid water and a mild climate.',
    missionUse: 'Searching for life in acidic environments and calibrating mineralogy instruments.',
  },
  tatacoa: {
    name: 'Tatacoa Desert',
    analogOf: 'Eroded terrains (badlands) on Mars',
    similarities: 'Gullies and mazes of reddish sediments eroded by water and wind, similar to Martian terrains cut by ancient rivers.',
    limitations: 'It is a tropical dry forest: there is vegetation, humidity and seasonal rain.',
    missionUse: 'A lesser-studied candidate to analyze sediment erosion and practice rover navigation on rough ground.',
  },
  timanfaya: {
    name: 'Timanfaya (Lanzarote)',
    analogOf: 'Lava fields and volcanic cones',
    similarities: 'Recent basaltic lava flows with very little vegetation, cones and lava tubes.',
    limitations: 'Oceanic climate and humidity.',
    missionUse: 'Geology training for astronauts (ESA PANGAEA).',
  },
  uyuni: {
    name: 'Salar de Uyuni',
    analogOf: 'Chloride deposits on Mars',
    similarities: 'A huge high-altitude evaporite plain, with strong UV radiation and a large temperature range.',
    limitations: 'It floods seasonally and the atmospheric pressure is much higher.',
    missionUse: 'Calibrating altimeters and radar (very flat surface) and studying brines.',
  },
  'lava-beds': {
    name: 'Lava Beds (lava tubes)',
    analogOf: 'Lunar and Martian lava tubes',
    similarities: 'Hundreds of accessible lava tubes, comparable to the skylights seen on the Moon and Mars.',
    limitations: 'Lunar tubes would be much larger because of the lower gravity.',
    missionUse: 'Cave robotics, underground mapping and radiation shelters.',
  },
  pilbara: {
    name: 'Pilbara (Dresser Formation)',
    analogOf: 'Ancient hydrothermal environments on Mars',
    similarities: 'About 3.5-billion-year-old stromatolites in hydrothermal rocks: one of the oldest records of life.',
    limitations: 'Billions of years of tectonics and weathering on Earth.',
    missionUse: 'Biosignature criteria for sample selection (Mars Sample Return).',
  },
  'svalbard-bockfjorden': {
    name: 'Bockfjorden (Svalbard)',
    analogOf: 'Volcanism in cold environments on Mars',
    similarities: 'Volcanoes and hot springs in an arctic setting, with carbonates similar to those in meteorite ALH84001.',
    limitations: 'There is vegetation and abundant liquid water.',
    missionUse: 'Testing rover instruments (AMASE expeditions).',
  },
}

const HOMOLOGUES_EN: Record<string, HomologueText> = {
  shackleton: {
    name: 'Shackleton Crater (south pole)',
    note: 'Artemis candidate region; permanently shadowed interior with possible cold traps holding ice.',
  },
  tranquillitatis: { name: 'Mare Tranquillitatis (Apollo 11)', note: 'Basaltic plain: the regolith of the lunar maria.' },
  marius: { name: 'Marius Hills pit', note: 'A skylight that may open into a lava tube.' },
  phoenix: { name: 'Phoenix landing site (Vastitas Borealis)', note: 'Soil with perchlorates and water ice a few centimeters down.' },
  utopia: { name: 'Utopia Planitia (Viking 2)', note: 'Cold mid-latitude plain with subsurface ice.' },
  gale: { name: 'Gale Crater (Curiosity)', note: 'Impact crater with sediments from an ancient lake.' },
  eberswalde: { name: 'Eberswalde delta', note: 'Sedimentary fan formed by water.' },
  meridiani: { name: 'Meridiani Planum (Opportunity)', note: 'Jarosite and iron sulfates formed in acidic water.' },
  medusae: { name: 'Medusae Fossae Formation', note: 'Fine sediments carved by the wind (yardangs).' },
  arsia: { name: 'Arsia Mons', note: 'Volcano with cave skylights on its flanks.' },
  sirenum: { name: 'Terra Sirenum (chloride deposits)', note: 'Chloride salt deposits in basins.' },
  gusev: { name: 'Home Plate, Gusev Crater (Spirit)', note: 'Silica deposits of hydrothermal origin.' },
  jezero: { name: 'Jezero Crater (Perseverance)', note: 'Delta and carbonates in an ancient lake.' },
}

export function localizeSite(site: AnalogSite, lang: Lang): AnalogSite {
  if (lang === 'es') return site
  const text = SITES_EN[site.id]
  return {
    ...site,
    ...(text ?? {}),
    country: COUNTRY_NAMES_EN[site.country] ?? site.country,
    homologues: site.homologues.map((h) => ({ ...h, ...(HOMOLOGUES_EN[h.id] ?? {}) })),
  }
}
