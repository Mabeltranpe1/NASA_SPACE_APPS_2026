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
  'la-guajira': {
    name: 'La Guajira (Taroa dunes)',
    analogOf: 'Terrain of flat Martian plains (case study)',
    similarities: 'Terrain only: according to Santiago’s topographic index (PAI), its almost flat terrain (99.7% of the ground under 5° of slope, at 200 m) is similar to Phoenix (88/100). Steady wind (about 8 m/s on average) and about 300 mm of rain a year.',
    limitations: 'It is on the coast: the analyzed window may include sea, so its result is provisional. With the full score (rain, vegetation and temperature) it is far from the Moon and Mars: it is a terrain case study, not an analog proposed by the global search.',
    missionUse: 'Rover mobility tests on sand and the study of wind processes (dunes and dust).',
  },
  'nevado-del-ruiz': {
    name: 'Nevado del Ruiz',
    analogOf: 'Steep high-mountain terrain (case study)',
    similarities: 'Terrain only: an active volcano with steep slopes (16.8° on average at 200 m) and more than 1,700 m of relief within 10 km. Its best match in Santiago’s topographic index is the de Gerlache rim (47/100); the Shackleton rim is much steeper (24/100).',
    limitations: 'Rainy (about 2,100 mm a year), with páramo vegetation on its slopes; volcanic activity limits access. With the full score (rain, vegetation and temperature) it is far from the Moon and Mars: it is a terrain case study, not an analog proposed by the global search.',
    missionUse: 'Navigation and anchoring on steep slopes, and the study of ice and volcanic deposits at altitude.',
  },
  'nevado-santa-isabel': {
    name: 'Nevado Santa Isabel',
    analogOf: 'Cold high-mountain terrain with ice (case study)',
    similarities: 'Terrain only: a volcano with a retreating glacier, more than 4,300 m high on average, with slopes of 13.7° on average (at 200 m). Its best match in Santiago’s index is the ridge between Shackleton and de Gerlache (Connecting Ridge, 48/100), which is not in the database yet; against the de Gerlache rim it gets 44/100.',
    limitations: 'Very rainy (about 2,100 mm a year) with páramo vegetation; the glacier is disappearing. With the full score (rain, vegetation and temperature) it is far from the Moon and Mars: it is a terrain case study, not an analog proposed by the global search.',
    missionUse: 'Testing ice-detection instruments and operations on cold slopes.',
  },
  'volcan-purace': {
    name: 'Puracé Volcano',
    analogOf: 'Volcanic terrain (case study)',
    similarities: 'Terrain only: an active volcano with slopes of 13° on average (at 200 m) and about 1,470 m of relief within 10 km. Its best match in Santiago’s index is Connecting Ridge (55/100), which is not in the database yet; against the de Gerlache rim it gets 49/100. It has acidic, sulfur-rich water (Vinagre river).',
    limitations: 'Humid climate (about 1,860 mm a year) and lots of vegetation: in Sentinel-2, only 2% of the window has ground with little vegetation. With the full score (rain, vegetation and temperature) it is far from the Moon and Mars: it is a terrain case study, not an analog proposed by the global search.',
    missionUse: 'Studying acidic, sulfur-rich chemistry and navigation on volcanic slopes.',
  },
  'la-candelaria': {
    name: 'La Candelaria Desert (Boyacá)',
    analogOf: 'Eroded mountain slopes (case study)',
    similarities: 'Terrain only: a dry area at about 2,400 m with eroded slopes (mean slope of 9.6°). Its best match in Santiago’s index is the ridge between Shackleton and de Gerlache (Connecting Ridge, 56/100), which is not in the database yet; against the de Gerlache rim it gets 41/100.',
    limitations: 'It rains more than its name suggests (about 1,130 mm a year in the 10 km window), and there are pastures and crops around it. With the full score (rain, vegetation and temperature) it is far from the Moon and Mars: it is a terrain case study, not an analog proposed by the global search.',
    missionUse: 'Mobility tests on moderate slopes and the study of erosion.',
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
  'de-gerlache': { name: 'de Gerlache crater rim (south pole)', note: 'Crater rim near the south pole, in the Artemis candidate region.' },
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
