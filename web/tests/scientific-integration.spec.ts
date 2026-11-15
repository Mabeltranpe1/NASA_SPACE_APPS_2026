import { test, expect, type Page } from '@playwright/test'

const sites = ['tatacoa', 'la-guajira', 'la-candelaria', 'nevado-del-ruiz', 'nevado-santa-isabel', 'volcan-purace']

async function offlineLayers(page: Page) {
  // External NASA tiles are not needed to validate the local scientific contract.
  // Data endpoints, Cesium assets, the UI and local source figures remain real.
  await page.route('**/*', (route) => {
    const url = new URL(route.request().url())
    return ['127.0.0.1', 'localhost'].includes(url.hostname) ? route.continue() : route.abort()
  })
  await page.addInitScript(() => localStorage.setItem('analogs.introSeen', '1'))
}

test('all six Colombian profiles load real science and twelve PAI comparisons', async ({ page }) => {
  await offlineLayers(page)
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  for (const site of sites) {
    await page.goto(`/?site=${site}&view=analysis&lang=es`)
    const panel = page.locator('.science-panel').first()
    await expect(panel.getByRole('tabpanel')).toBeVisible()
    await expect(panel.getByText('La caracterización regional es la fuente detallada', { exact: false })).toBeVisible()
    await panel.getByRole('tab', { name: 'PAI topográfico · 0–100', exact: true }).click()
    await expect(panel.locator('.science-pai tbody tr')).toHaveCount(12)
    await expect(panel.getByText('No incorpora clima o mineralogía', { exact: false })).toBeVisible()
    await panel.getByRole('tab', { name: 'Clima del aire y energía solar', exact: true }).click()
    await expect(panel.getByText('Temperatura media del aire a 2 m', { exact: true }).first()).toBeVisible()
    await panel.getByRole('tab', { name: 'EMIT: coincidencias de biblioteca', exact: true }).click()
    await expect(panel.getByText('EMIT contiene coincidencias provisionales', { exact: false })).toBeVisible()
    await expect(panel.locator('.science-section tbody tr').first()).toBeVisible()
    if (site === 'la-guajira') await expect(panel.getByText('47.92280', { exact: false })).toBeVisible()
    await expect(page.locator('.comparison').first()).toBeVisible()
  }
  expect(errors).toEqual([])
})

test('English research, regional target links and original figures are available', async ({ page }) => {
  await offlineLayers(page)
  await page.goto('/?site=tatacoa&view=analysis&lang=en')
  const panel = page.locator('.science-panel').first()
  await expect(panel.getByRole('tabpanel', { name: 'Topography at 200 m' })).toBeVisible()
  const image = panel.locator('.science-figure img')
  await expect(image).toBeVisible()
  await expect.poll(() => image.evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0)).toBe(true)
  await panel.getByRole('tab', { name: 'Topographic PAI · 0–100', exact: true }).click()
  await panel.getByRole('button', { name: 'mars Phoenix', exact: true }).click()
  const nested = panel.locator('.science-panel')
  await expect(nested.getByText('Phoenix CRISM has no qualified observation', { exact: false })).toBeVisible()
  await nested.getByRole('tab', { name: 'CRISM: spectral indicators', exact: true }).click()
  await expect(nested.getByText('no_qualified_observation', { exact: true }).first()).toBeVisible()
})

test('expanded international ranking is consumed and opens a candidate on the existing map', async ({ page }) => {
  await offlineLayers(page)
  await page.goto('/?view=analysis&lang=en')
  const ranking = page.getByRole('region', { name: "Marco's international ranking · 100 Moon + 100 Mars" })
  await expect(ranking).toBeVisible()
  await expect(ranking.getByText('691,035 cells · 727 regions', { exact: true })).toBeVisible()
  await expect(ranking.locator('tbody tr')).toHaveCount(10)
  await ranking.getByRole('button', { name: 'Show all observations (100)' }).click()
  await expect(ranking.locator('tbody tr')).toHaveCount(100)
  await ranking.getByRole('button', { name: 'Moon', exact: true }).click()
  await expect(ranking.locator('tbody tr')).toHaveCount(100)
  await ranking.getByRole('button', { name: 'Open on the map and compare' }).first().click()
  await expect(page.locator('.comparison').first()).toBeVisible()
  // Existing controls and references are still connected after selecting a new place.
  await expect(page.locator('.comparison .ranking').first()).toBeVisible()
  // Selecting a discovery already activates its heatmap; return to the globe
  // through the existing navigation instead of toggling that active layer off.
  await page.getByRole('button', { name: '← Back to the globe', exact: true }).click()
  await expect(page.locator('.heat-legend')).toBeVisible()
  await expect(page.locator('.heat-legend').getByText('2,500', { exact: false })).toBeVisible()
  await expect(page.locator('canvas').first()).toBeVisible()
})

test('public scientific API has real data, identifiers and both distinct indices', async ({ request }) => {
  const comparisons = await (await request.get('/data/comparisons.json')).json()
  expect(comparisons.version).toBe('3')
  expect(comparisons.synthetic).toBe(false)
  expect([comparisons.n_cells, comparisons.n_regions]).toEqual([691035, 727])
  expect(comparisons.sites.filter((s: { science_ref?: unknown }) => s.science_ref)).toHaveLength(6)
  const detail = await (await request.get('/data/science/earth/Tatacoa.json')).json()
  expect(detail.pai.results).toHaveLength(12)
  expect(detail.pai.results[0].PAI).toBe(92.02119)
  expect(detail.sections.find((s: { id: string }) => s.id === 'climate').records[0].air_temperature_mean_c).toBe(20.33373)
})
