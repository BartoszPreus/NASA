// Takes the README screenshots of the Zodiak web app with headless Chrome and
// converts them to compressed WebP files in docs/figures/readme/.
// Usage (from the repository root, dev server or preview already running):
//   node web/scripts/readme_screenshots.mjs http://127.0.0.1:5185
// Optional: argv[3] virtual time budget in ms (default 15000), argv[4] comma list of page names to retake.
// Needs Chrome (set CHROME_PATH to override) and Python with Pillow for the WebP step.
import { spawnSync } from 'node:child_process'
import { mkdtempSync, mkdirSync, rmSync, statSync, existsSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const base = (process.argv[2] || 'http://127.0.0.1:5173').replace(/\/$/, '')
const budget = process.argv[3] || '15000'
const chrome = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')
const out = join(root, 'docs', 'figures', 'readme')
const SITE = 'N69E093-01'

const only = process.argv[4] ? process.argv[4].split(',') : null
const pages = [
  ['landing', '#/'],
  ['discover', '#/discover'],
  ['explore', '#/explore'],
  ['site-card', `#/explore?site=${SITE}`],
  ['compare', `#/compare?site=${SITE}`],
  ['moon', '#/moon'],
  ['method', '#/method'],
]

if (!existsSync(chrome)) { console.error('Chrome not found: ' + chrome); process.exit(1) }
mkdirSync(out, { recursive: true })
const tmp = mkdtempSync(join(tmpdir(), 'zodiak-shots-'))
let failed = 0

for (const [name, hash] of pages) {
  if (only && !only.includes(name)) continue
  const png = join(tmp, name + '.png')
  const profile = mkdtempSync(join(tmp, 'profile-'))
  const r = spawnSync(chrome, [
    '--headless=new', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
    '--hide-scrollbars', '--window-size=1440,900', `--virtual-time-budget=${name === 'moon' ? Math.max(+budget, 45000) : budget}`,
    `--user-data-dir=${profile}`, `--screenshot=${png}`, `${base}/${hash}`,
  ], { stdio: 'ignore', timeout: 120000 })
  if (!existsSync(png)) { console.error('FAILED ' + name); failed++; continue }
  console.log('shot ' + name)
}

const py = `
import sys, os
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
for f in sorted(os.listdir(src)):
    if not f.endswith('.png'): continue
    im = Image.open(os.path.join(src, f)).convert('RGB')
    target = os.path.join(dst, f[:-4] + '.webp')
    for q in (82, 74, 66, 58):
        im.save(target, 'WEBP', quality=q, method=6)
        if os.path.getsize(target) <= 350 * 1024: break
    print(f'{f[:-4]}.webp {im.size[0]}x{im.size[1]} {os.path.getsize(target)//1024} KB (q{q})')
`
const c = spawnSync('python', ['-I', '-c', py, tmp, out], { stdio: 'inherit' })
rmSync(tmp, { recursive: true, force: true })
if (c.status !== 0 || failed) process.exit(1)
