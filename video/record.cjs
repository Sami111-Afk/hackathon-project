// Înregistrează automat scenele videoului (1920×1080, cursor vizibil + cerc la click) de pe site-ul public.
// Rulare (din rădăcina repo-ului):
//   NODE_PATH=<node_modules cu playwright-core> CHROME=<chrome> node video/record.cjs [scene...]
// Token-ul de bancă se citește din .env (PUBLIC_BANK_TOKEN, altfel BANK_UI_TOKEN) — nu se afișează nicăieri.
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const ROOT = path.resolve(__dirname, '..')
const SITE = process.env.SITE || 'https://orb-raiffeisen.vercel.app'
const OUT = path.join(__dirname, 'rec')
const env = Object.fromEntries(fs.readFileSync(path.join(ROOT, '.env'), 'utf8').split('\n')
  .filter((l) => l.includes('=') && !l.startsWith('#')).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1).trim()]))
const TOKEN = process.env.TOKEN_KEY ? env[process.env.TOKEN_KEY] : (env.PUBLIC_BANK_TOKEN || env.BANK_UI_TOKEN)
const HONEST = ['buletin.jpg', 'fluturas.jpg', 'extras.pdf'].map((f) => path.join(ROOT, 'data/demo/honest', f))

// cursor desenat (browserul automat nu are cursor) + cerc la click
const CURSOR = `
(() => {
  const add = () => {
    if (document.getElementById('__cur')) return
    const c = document.createElement('div'); c.id = '__cur'
    c.style.cssText = 'position:fixed;left:0;top:0;width:22px;height:22px;z-index:2147483647;pointer-events:none;transform:translate(-3px,-2px);transition:transform .05s'
    c.innerHTML = '<svg width="22" height="22" viewBox="0 0 24 24"><path d="M4 2l15 9-6.5 1.5L9 19z" fill="#111" stroke="#fff" stroke-width="1.6"/></svg>'
    document.documentElement.appendChild(c)
    addEventListener('mousemove', (e) => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px' }, true)
    addEventListener('mousedown', (e) => {
      const r = document.createElement('div')
      r.style.cssText = 'position:fixed;z-index:2147483646;pointer-events:none;border-radius:50%;border:3px solid #FFE600;' +
        'width:16px;height:16px;left:' + (e.clientX - 8) + 'px;top:' + (e.clientY - 8) + 'px;opacity:.95;transition:all .45s ease-out'
      document.documentElement.appendChild(r)
      requestAnimationFrame(() => { r.style.width = r.style.height = '54px'; r.style.left = (e.clientX - 27) + 'px'; r.style.top = (e.clientY - 27) + 'px'; r.style.opacity = '0' })
      setTimeout(() => r.remove(), 600)
    }, true)
  }
  document.readyState === 'loading' ? addEventListener('DOMContentLoaded', add) : add()
})()`

const login = (t) => `try { sessionStorage.setItem('orb.token', ${JSON.stringify(t)}); sessionStorage.setItem('orb.name', 'Ana Popescu'); sessionStorage.setItem('orb.mock', '0') } catch (e) {}`

const pause = (p, ms) => p.waitForTimeout(ms)
let mouse = { x: 960, y: 540 }
async function moveTo(p, x, y, steps = 28) { await p.mouse.move(x, y, { steps }); mouse = { x, y } }
async function point(p, loc, steps = 28) {
  await loc.scrollIntoViewIfNeeded()
  await pause(p, 300)
  const b = await loc.boundingBox()
  await moveTo(p, b.x + b.width / 2, b.y + b.height / 2, steps)
  return b
}
async function click(p, loc, after = 900) {
  await point(p, loc)
  await pause(p, 250)
  await p.mouse.down(); await p.mouse.up()
  await pause(p, after)
}
async function smoothScroll(p, top, ms = 1600) {
  await p.evaluate(([t, d]) => new Promise((res) => {
    const s = scrollY, t0 = performance.now()
    const step = (n) => { const k = Math.min(1, (n - t0) / d); scrollTo(0, s + (t - s) * (k < .5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2)); k < 1 ? requestAnimationFrame(step) : res() }
    requestAnimationFrame(step)
  }), [top, ms])
  await pause(p, 300)
}
async function scrollToEl(p, loc, offset = 120, ms = 1600) {
  const y = await loc.evaluate((el, o) => el.getBoundingClientRect().top + scrollY - o, offset)
  await smoothScroll(p, Math.max(0, y), ms)
}
// imaginea documentului vine prin ngrok, poate dura câteva secunde
async function waitDocImage(p, timeout = 30000) {
  await p.waitForFunction(() => !document.body.innerText.includes('Loading the document') &&
    [...document.images].some((i) => i.complete && i.naturalWidth > 300), null, { timeout }).catch(() => {})
}
async function waitVerdict(p, timeout = 120000) {
  await p.getByText('Risk level', { exact: true }).waitFor({ timeout })
}

const SCENES = {
  // 2 — Dashboard: se încarcă, derulare lentă pe cifre și grafice
  async s2_dashboard(p) {
    await p.goto(SITE + '/dashboard'); await pause(p, 3000)
    await moveTo(p, 700, 420)
    await smoothScroll(p, 620, 3000); await pause(p, 1500)
    await smoothScroll(p, 0, 2000); await pause(p, 800)
  },
  // 3 — dosar cinstit: New application → upload → analiză → aprobat
  async s3_honest(p) {
    await p.goto(SITE + '/dashboard'); await pause(p, 2000)
    await click(p, p.getByRole('button', { name: 'New application' }), 1200)
    await p.locator('input[type=file]').setInputFiles(HONEST); await pause(p, 1200)
    const amount = p.locator('input[inputmode=numeric]')
    await click(p, amount, 300); await amount.pressSequentially('30000', { delay: 90 }); await pause(p, 600)
    await click(p, p.getByRole('button', { name: 'Start analysis' }), 1500)
    await waitVerdict(p); await pause(p, 2500)
    await click(p, p.getByRole('button', { name: 'Approve application' }), 2500)
  },
  // 4 — Maria live: Re-run → agenții → dovada netului pe fluturaș → Edit map
  async s4_maria(p) {
    await p.goto(SITE + '/cases/case_maria'); await pause(p, 3500)
    await click(p, p.getByRole('button', { name: 'Re-run live' }), 500)
    await moveTo(p, 960, 330, 40)
    await waitVerdict(p); await pause(p, 2500)
    const net = p.locator('button', { hasText: 'Calculated net pay' })
    await scrollToEl(p, net, 300); await click(p, net, 1500)
    const viewer = p.getByRole('tablist', { name: /Documents/i })
    if (await viewer.count()) await scrollToEl(p, viewer.first(), 160)
    await waitDocImage(p); await pause(p, 3000)
    const edit = p.getByRole('button', { name: 'Edit map' })
    if (await edit.count()) { await click(p, edit.first(), 800); await waitDocImage(p); await pause(p, 3000) }
    const orig = p.getByRole('button', { name: 'Original' })
    if (await orig.count()) { await click(p, orig.first(), 1500) }
  },
  // 5 — graful rețelei
  async s5_graph(p) {
    await p.goto(SITE + '/cases/case_maria'); await pause(p, 3500)
    const g = p.getByText('Links to other applications')
    await scrollToEl(p, g, 90, 1800); await pause(p, 2000)
    const b = await g.boundingBox()
    await moveTo(p, b.x + 380, b.y + 220, 40); await pause(p, 1200)
    await moveTo(p, b.x + 330, b.y + 300, 30); await pause(p, 1500)
    await moveTo(p, b.x + 420, b.y + 260, 30); await pause(p, 1500)
  },
  // 6 — nivelul de risc → De ce acest scor → Aprobă fără motiv (cere motiv)
  async s6_risk(p) {
    await p.goto(SITE + '/cases/case_maria'); await pause(p, 3500)
    const lvl = p.getByText('Risk level', { exact: true })
    await scrollToEl(p, lvl, 140); await point(p, lvl); await pause(p, 1500)
    await click(p, p.getByText('Why this score?'), 3500)
    const approve = p.getByRole('button', { name: 'Approve application' })
    await scrollToEl(p, approve, 360); await click(p, approve, 3000)
  },
  // 9b — proiectorul: atacatorul automat trece → AI-ul propune o regulă → un om o aprobă
  async s9b_rule(p) {
    await p.goto(SITE + '/arena/live'); await pause(p, 4000)
    await click(p, p.getByRole('button', { name: 'Start the automatic attacker' }), 1000)
    await moveTo(p, 1500, 700, 40)
    await p.getByText('Rule proposed by AI', { exact: false }).waitFor({ timeout: 300000 })
    await pause(p, 3000)
    await click(p, p.getByRole('button', { name: 'Approve' }), 4000)
  },
  // 7 — confidențialitate: dovezile → ce a văzut AI-ul → butonul Local
  async s7_privacy(p) {
    await p.goto(SITE + '/cases/case_maria'); await pause(p, 4000)
    const panel = p.getByText('What the bank can prove', { exact: false })
    await scrollToEl(p, panel.first(), 110); await pause(p, 1500)
    const ev = p.getByText('See the evidence')
    if (await ev.count() > 1) { await click(p, ev.nth(1), 3500) }
    const ai = p.getByRole('button', { name: 'What the AI saw' })
    if (await ai.count()) { await scrollToEl(p, ai.first(), 200); await click(p, ai.first(), 2500) }
    await smoothScroll(p, 0, 1500)
    const local = p.getByRole('button', { name: 'Local' })
    if (await local.count()) { await point(p, local.first()); await pause(p, 2500) }
  },
}

// 9 — Arena pe telefon (alt context, ecran de telefon)
async function arena(browser) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true,
    recordVideo: { dir: OUT, size: { width: 390, height: 844 } } })
  await ctx.addInitScript(`try { localStorage.setItem('orb.arena.nick', 'Juror') } catch (e) {}`)
  const p = await ctx.newPage()
  await p.goto(SITE + '/arena'); await pause(p, 2500)
  const nick = p.locator('input').first()
  if (await nick.isVisible().catch(() => false)) {
    await nick.fill(''); await nick.pressSequentially('Juror-' + Math.floor(Math.random() * 90 + 10), { delay: 80 })
    const go = p.getByRole('button').filter({ hasText: /start|play|continue|go/i }).first()
    if (await go.count()) await go.tap(); await pause(p, 1500)
  }
  await p.getByRole('button', { name: /The 9,000 payslip/ }).tap(); await pause(p, 2000)
  const net = p.getByRole('spinbutton', { name: /Net salary/ })
  await net.fill(''); await net.pressSequentially(String(9400 + Math.floor(Math.random() * 500)), { delay: 120 }); await pause(p, 1000)
  await p.getByRole('button', { name: 'Submit the fake' }).tap()
  await pause(p, 6500)
  const v = p.video(); await ctx.close(); await v.saveAs(path.join(OUT, 's9_arena.webm')); await v.delete()
}

;(async () => {
  fs.mkdirSync(OUT, { recursive: true })
  const want = process.argv.slice(2)
  const browser = await chromium.launch({ executablePath: process.env.CHROME })
  for (const [name, fn] of Object.entries(SCENES)) {
    if (want.length && !want.includes(name)) continue
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, recordVideo: { dir: OUT, size: { width: 1920, height: 1080 } } })
    await ctx.addInitScript(login(TOKEN)); await ctx.addInitScript(CURSOR)
    const p = await ctx.newPage()
    mouse = { x: 960, y: 540 }
    try { await fn(p); console.log('ok', name) } catch (e) { console.log('EROARE', name, String(e).split('\n')[0]) }
    const v = p.video(); await ctx.close(); await v.saveAs(path.join(OUT, name + '.webm')); await v.delete()
  }
  if (!want.length || want.includes('s9_arena')) {
    try { await arena(browser); console.log('ok s9_arena') } catch (e) { console.log('EROARE s9_arena', String(e).split('\n')[0]) }
  }
  await browser.close()
})()
