// Înregistrează automat scenele videoului, varianta 7 (1920×1080, cursor desenat + cerc la click).
// Fiecare click e notat în video/rec7/clicks.json (scena, secunda din clip, dreptunghiul elementului) → montajul face zoom acolo.
// Rulare (din rădăcina repo-ului):
//   NODE_PATH=<node_modules cu playwright-core> CHROME=<chrome> SITE=http://localhost:5173 node video/record7.cjs [scene...]
// Token-ul de bancă se citește din .env (BANK_UI_TOKEN, sau cheia din TOKEN_KEY) — nu se afișează nicăieri.
const fs = require('fs')
const path = require('path')
const { chromium } = require('playwright-core')

const ROOT = path.resolve(__dirname, '..')
const SITE = process.env.SITE || 'http://localhost:5173'
const OUT = path.join(__dirname, 'rec7')
const env = Object.fromEntries(fs.readFileSync(path.join(ROOT, '.env'), 'utf8').split('\n')
  .filter((l) => l.includes('=') && !l.startsWith('#')).map((l) => [l.slice(0, l.indexOf('=')), l.slice(l.indexOf('=') + 1).trim()]))
const TOKEN = env[process.env.TOKEN_KEY || 'BANK_UI_TOKEN']
const docs = (dir, names) => names.map((f) => path.join(ROOT, 'data/demo', dir, f))
const HONEST = docs('honest', ['buletin.jpg', 'fluturas.jpg', 'extras.pdf'])
const BLURRY = docs('blurry', ['buletin.jpg', 'fluturas.jpg', 'extras.jpg'])

// cursor desenat (browserul automat nu are cursor) + cerc galben la click
const CURSOR = `
(() => {
  const add = () => {
    if (document.getElementById('__cur')) return
    const c = document.createElement('div'); c.id = '__cur'
    c.style.cssText = 'position:fixed;left:0;top:0;width:22px;height:22px;z-index:2147483647;pointer-events:none;transform:translate(-3px,-2px)'
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
let scene = '', t0 = 0
const clicks = []
const mark = (kind, b, extra = {}) => clicks.push({ scene, kind, t: +((Date.now() - t0) / 1000).toFixed(2), x: b.x, y: b.y, w: b.width, h: b.height, ...extra })

async function moveTo(p, x, y, steps = 28) { await p.mouse.move(x, y, { steps }); mouse = { x, y } }
async function point(p, loc, steps = 28) {
  await loc.scrollIntoViewIfNeeded()
  await pause(p, 300)
  const b = await loc.boundingBox()
  await moveTo(p, b.x + b.width / 2, b.y + b.height / 2, steps)
  return b
}
async function click(p, loc, after = 900, label = '') {
  const b = await point(p, loc)
  await pause(p, 250)
  mark('click', b, { label })
  await p.mouse.down(); await p.mouse.up()
  await pause(p, after)
}
// „uită-te aici” fără click (montajul face zoom pe dreptunghi)
async function focus(p, loc, ms = 2500, label = '') {
  const b = await point(p, loc); mark('focus', b, { label, ms }); await pause(p, ms)
}
async function smoothScroll(p, top, ms = 1600) {
  await p.evaluate(([t, d]) => new Promise((res) => {
    const s = scrollY, s0 = performance.now()
    const step = (n) => { const k = Math.min(1, (n - s0) / d); scrollTo(0, s + (t - s) * (k < .5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2)); k < 1 ? requestAnimationFrame(step) : res() }
    requestAnimationFrame(step)
  }), [top, ms])
  await pause(p, 300)
}
async function scrollToEl(p, loc, offset = 120, ms = 1600) {
  const y = await loc.evaluate((el, o) => el.getBoundingClientRect().top + scrollY - o, offset)
  await smoothScroll(p, Math.max(0, y), ms)
}
async function waitDocImage(p, timeout = 30000) {
  await p.waitForFunction(() => !document.body.innerText.includes('Loading the document') &&
    [...document.images].some((i) => i.complete && i.naturalWidth > 300), null, { timeout }).catch(() => {})
}
const waitVerdict = (p, timeout = 180000) => p.getByText('Risk level', { exact: true }).waitFor({ timeout })
const finding = (p, text) => p.locator('button', { hasText: text }).first()

async function upload(p, files, amount = '30000') {
  await p.goto(SITE + '/dashboard'); await pause(p, 2000)
  await click(p, p.getByRole('button', { name: 'New application' }), 1200, 'new application')
  await p.locator('input[type=file]').setInputFiles(files); await pause(p, 1200)
  const a = p.locator('input[inputmode=numeric]')
  await click(p, a, 300, 'amount'); await a.pressSequentially(amount, { delay: 80 }); await pause(p, 500)
  await click(p, p.getByRole('button', { name: 'Start analysis' }), 1500, 'start analysis')
}

const SCENES = {
  // 2 — ecranul „New application” (static, zoom lent la montaj)
  async v2_new(p) {
    await p.goto(SITE + '/dashboard'); await pause(p, 2500)
    await click(p, p.getByRole('button', { name: 'New application' }), 7000, 'new application')
  },
  // 3+4+5a — Maria: Re-run live → agenții → ce a văzut AI-ul → dovezile pe document → harta editării
  async v3_maria(p) {
    await p.goto(SITE + '/cases/case_maria'); await pause(p, 3500)
    await click(p, p.getByRole('button', { name: 'Re-run live' }), 500, 're-run')
    await moveTo(p, 960, 330, 40)
    await waitVerdict(p); mark('verdict', { x: 0, y: 0, width: 0, height: 0 }); await pause(p, 2000)
    const viewer = p.getByRole('tablist', { name: /Documents/i })
    if (await viewer.count()) await scrollToEl(p, viewer.first(), 160)
    const slip = p.getByRole('tab', { name: /Payslip/ })
    if (await slip.count()) { await click(p, slip.first(), 600, 'payslip tab'); await waitDocImage(p); await pause(p, 800) }
    const ai = p.getByRole('button', { name: 'What the AI saw' })
    if (await ai.count()) { await click(p, ai.first(), 600, 'what the AI saw'); await waitDocImage(p); await pause(p, 3500) }
    const orig = p.getByRole('button', { name: 'Original' })
    if (await orig.count()) { await click(p, orig.first(), 600, 'original'); await waitDocImage(p); await pause(p, 1500) }
    for (const [text, label] of [['Calculated net pay', 'net'], ['listed as inactive', 'employer'], ['does not appear as a credit', 'salary']]) {
      const f = finding(p, text)
      await scrollToEl(p, f, 360); await click(p, f, 600, label); await waitDocImage(p); await pause(p, 2600)
    }
    const edit = p.getByRole('button', { name: 'Edit map' })
    if (await edit.count()) { await scrollToEl(p, edit.first(), 160); await click(p, edit.first(), 600, 'edit map'); await waitDocImage(p); await pause(p, 3500) }
  },
  // 5b — graful rețelei
  async v5_graph(p) {
    await p.goto(SITE + '/cases/case_maria'); await pause(p, 3500)
    const g = p.getByText('Links to other applications').first()
    await scrollToEl(p, g, 90, 1800); await pause(p, 1500)
    await focus(p, g, 4500, 'graph')
  },
  // 6 — riscul → de ce → Approve refuzat → motiv → trimis la investigație
  async v6_decision(p) {
    await p.goto(SITE + '/cases/case_maria'); await pause(p, 3500)
    const lvl = p.getByText('Risk level', { exact: true })
    await scrollToEl(p, lvl, 140); await focus(p, lvl, 1500, 'risk')
    await click(p, p.getByText('Why this score?'), 3000, 'why')
    const approve = p.getByRole('button', { name: 'Approve application' })
    await scrollToEl(p, approve, 380); await click(p, approve, 2200, 'approve refused')
    const notes = p.locator('#notes')
    await click(p, notes, 300, 'reason'); await notes.pressSequentially('Payslip net does not follow from gross; employer inactive; shared IBAN.', { delay: 28 })
    await pause(p, 600)
    await click(p, p.getByRole('button', { name: 'Send to investigation' }), 3500, 'investigate')
  },
  // 7 — al doilea dosar: poze neclare → nu pleacă în cloud → la om
  async v7_blurry(p) {
    await upload(p, BLURRY)
    await waitVerdict(p); mark('verdict', { x: 0, y: 0, width: 0, height: 0 }); await pause(p, 1500)
    const lvl = p.getByText('Risk level', { exact: true })
    await scrollToEl(p, lvl, 140); await focus(p, lvl, 2000, 'risk')
    const f = finding(p, 'not sent to the cloud')
    if (await f.count()) { await scrollToEl(p, f, 360); await focus(p, f, 3500, 'no cloud') }
  },
  // 9 — dosar cinstit: curat → aprobat dintr-un click
  async v9_honest(p) {
    await upload(p, HONEST)
    await waitVerdict(p); mark('verdict', { x: 0, y: 0, width: 0, height: 0 }); await pause(p, 1500)
    const lvl = p.getByText('Risk level', { exact: true })
    await scrollToEl(p, lvl, 140); await focus(p, lvl, 1800, 'risk')
    const approve = p.getByRole('button', { name: 'Approve application' })
    await scrollToEl(p, approve, 380); await click(p, approve, 2500, 'approve')
  },
  // 10 — confidențialitate: textul exact primit de AI → comutatorul Local (doar comutarea) → înapoi Cloud
  async v10_privacy(p) {
    await p.goto(SITE + '/cases/case_maria'); await pause(p, 4000)
    const panel = p.getByText('What the bank can prove', { exact: false }).first()
    if (await panel.count()) { await scrollToEl(p, panel, 110); await pause(p, 1200) }
    const ev = p.getByText('See the evidence')
    if (await ev.count() > 1) { await click(p, ev.nth(1), 3500, 'ai saw evidence') }
    await smoothScroll(p, 0, 1400)
    const local = p.getByRole('button', { name: 'Local' }).first()
    await click(p, local, 2600, 'local on')
    await click(p, p.getByRole('button', { name: 'Cloud' }).first(), 1500, 'cloud back')
  },
  // 11a — Arena pe telefon: falsifici un fluturaș → ORB te prinde și spune de ce
  async v11_phone(p) {
    await p.goto(SITE + '/arena'); await pause(p, 2500)
    const start = p.getByRole('button', { name: 'Start' })
    if (await start.count()) { await start.first().tap(); await pause(p, 1200) }
    const nick = p.getByPlaceholder('For example, Andrei')
    if (await nick.count()) {
      await nick.fill(''); await nick.pressSequentially('Juror-' + Math.floor(Math.random() * 90 + 10), { delay: 80 }); await pause(p, 500)
      await p.locator('form button[type=submit]').tap(); await pause(p, 1500)
    }
    await p.getByRole('button', { name: /The 9,000 payslip/ }).tap(); await pause(p, 2200)
    const net = p.getByRole('spinbutton', { name: /Net salary/ })
    await net.fill(''); await net.pressSequentially(String(9400 + Math.floor(Math.random() * 500)), { delay: 120 }); await pause(p, 900)
    await p.getByRole('button', { name: 'Submit the fake' }).tap()
    await p.getByText(/Why we caught you|You fooled ORB/).first().waitFor({ timeout: 60000 }).catch(() => {})
    await pause(p, 2500)
    await p.mouse.wheel(0, 500); await pause(p, 3000)
  },
  // 11b — proiectorul: atacatorul automat trece → AI-ul propune o regulă testată pe istoric → un om o aprobă
  async v11_rule(p) {
    await p.goto(SITE + '/arena/live?base=https://orb-raiffeisen.vercel.app'); await pause(p, 3500)
    await click(p, p.getByRole('button', { name: 'Start the automatic attacker' }), 1000, 'attacker')
    await moveTo(p, 1500, 700, 40)
    await p.getByText('Rule proposed by AI', { exact: false }).waitFor({ timeout: 420000 })
    mark('rule', { x: 0, y: 0, width: 0, height: 0 })
    await pause(p, 3000)
    const ap = p.getByRole('button', { name: 'Approve', exact: true }).first()
    await focus(p, ap, 1200, 'rule box'); await click(p, ap, 4000, 'approve rule')
  },
  // 11c — după atac: regula propusă (testată pe istoric) → un om o aprobă
  async v11_approve(p) {
    await p.goto(SITE + '/arena/live?base=https://orb-raiffeisen.vercel.app'); await pause(p, 3500)
    const box = p.getByText('Rule proposed by AI', { exact: false }).first()
    await box.waitFor({ timeout: 30000 })
    await focus(p, box, 3000, 'rule box')
    await click(p, p.getByRole('button', { name: 'Approve', exact: true }).first(), 3500, 'approve rule')
  },
}

const MOBILE = new Set(['v11_phone'])

;(async () => {
  fs.mkdirSync(OUT, { recursive: true })
  const want = process.argv.slice(2)
  const browser = await chromium.launch({ executablePath: process.env.CHROME })
  for (const [name, fn] of Object.entries(SCENES)) {
    if (want.length && !want.includes(name)) continue
    const ctx = MOBILE.has(name)
      ? await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, recordVideo: { dir: OUT, size: { width: 780, height: 1688 } } })
      : await browser.newContext({ viewport: { width: 1920, height: 1080 }, recordVideo: { dir: OUT, size: { width: 1920, height: 1080 } } })
    await ctx.addInitScript(login(TOKEN)); await ctx.addInitScript(CURSOR)
    const p = await ctx.newPage()
    scene = name; t0 = Date.now(); mouse = { x: 960, y: 540 }
    try { await fn(p); console.log('ok', name) } catch (e) { console.log('EROARE', name, String(e).split('\n')[0]) }
    const v = p.video(); await ctx.close(); await v.saveAs(path.join(OUT, name + '.webm')); await v.delete()
  }
  const file = path.join(OUT, 'clicks.json')
  const old = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')).filter((c) => !clicks.some((n) => n.scene === c.scene)) : []
  fs.writeFileSync(file, JSON.stringify([...old, ...clicks], null, 1))
  await browser.close()
})()
