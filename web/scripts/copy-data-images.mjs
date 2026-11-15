// Copies every image listed in public/data/analogos.json from the repo root
// into public/data/img/ (same relative path), so Vite serves it at /data/img/...
// Runs automatically before `npm run dev` and `npm run build`.
import { copyFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const web = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const repo = resolve(web, '..')
const data = JSON.parse(readFileSync(join(web, 'public/data/analogos.json'), 'utf8'))

const images = [
  ...data.sites.flatMap((s) => [...s.images, ...s.analogs.flatMap((a) => a.images)]),
  ...data.reference_photos,
]
const srcs = [...new Set(images.map((i) => i.src))]
let copied = 0
const missing = []
for (const src of srcs) {
  const from = join(repo, src)
  if (!existsSync(from)) { missing.push(src); continue }
  const to = join(web, 'public/data/img', src)
  mkdirSync(dirname(to), { recursive: true })
  copyFileSync(from, to)
  copied++
}
console.log(`copy-data-images: ${copied} images copied to public/data/img/`)
if (missing.length) {
  console.error(`copy-data-images: ${missing.length} images not found:\n  ${missing.join('\n  ')}`)
  process.exit(1)
}
