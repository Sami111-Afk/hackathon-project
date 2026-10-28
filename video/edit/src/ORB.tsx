// Montajul videoului ORB (3:00), varianta 7. Scenele sunt date (SCENES); fiecare are clipul, camera (zoom-uri), textele și vocea.
import React from 'react'
import {
  AbsoluteFill, Audio, Easing, Img, interpolate, OffthreadVideo, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion'

import SUBS_AI from './subs_voice.json'
import SUBS_CLONE from './subs_voice_clone.json'

export const FPS = 30
const W = 1920, H = 1080
const YELLOW = '#FFE600', INK = '#111418', DANGER = '#F97066', OK = '#47CD89'
const MUSIC = process.env.REMOTION_MUSIC || ''   // ex. music/Dreamer.mp3 (în public/)
const VDIR = process.env.REMOTION_VOICE_DIR || 'voice'   // voice = AI, voice_clone = vocea clonată

const fontFace = `
@font-face { font-family: Noto; src: url(${staticFile('fonts/NotoSans-Regular.ttf')}); font-weight: 400; }
@font-face { font-family: Noto; src: url(${staticFile('fonts/NotoSans-Bold.ttf')}); font-weight: 700; }`

// ---------------------------------------------------------------- cameră (zoom lin între cadre-cheie)
type Key = { t: number; s: number; x: number; y: number }   // t = secunda din scenă; (x, y) = punctul adus în centru
function cam(t: number, keys: Key[]) {
  if (!keys.length) return { s: 1, x: W / 2, y: H / 2 }
  let k = keys[0]
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1], b = keys[i], d = Math.min(0.9, b.t - a.t)
    if (t >= b.t) { k = b; continue }
    if (t > b.t - d) {
      const e = Easing.inOut(Easing.cubic)((t - (b.t - d)) / d)
      return { s: a.s + (b.s - a.s) * e, x: a.x + (b.x - a.x) * e, y: a.y + (b.y - a.y) * e }
    }
    k = a; break
  }
  return k
}
const Camera: React.FC<{ keys: Key[]; children: React.ReactNode }> = ({ keys, children }) => {
  const f = useCurrentFrame()
  const { s, x, y } = cam(f / FPS, keys)
  const tx = Math.min(0, Math.max(W - W * s, W / 2 - x * s))
  const ty = Math.min(0, Math.max(H - H * s, H / 2 - y * s))
  return <AbsoluteFill style={{ transform: `translate(${tx}px, ${ty}px) scale(${s})`, transformOrigin: '0 0' }}>{children}</AbsoluteFill>
}

// ---------------------------------------------------------------- piese de text
const Caption: React.FC<{ text: string; from: number; to: number; tone?: 'info' | 'danger' | 'ok'; top?: boolean }> = ({ text, from, to, tone = 'info', top = false }) => {
  const f = useCurrentFrame(), t = f / FPS
  if (t < from || t > to) return null
  const a = Math.min(1, (t - from) / 0.3, (to - t) / 0.3)
  const y = interpolate(Math.min(1, (t - from) / 0.4), [0, 1], [24, 0], { easing: Easing.out(Easing.cubic) })
  const bar = tone === 'danger' ? DANGER : tone === 'ok' ? OK : YELLOW
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, ...(top ? { top: 96 } : { bottom: 150 }), display: 'flex', justifyContent: 'center', opacity: a, transform: `translateY(${y}px)` }}>
      <div style={{ background: 'rgba(17,20,24,.9)', color: '#fff', fontFamily: 'Noto', fontWeight: 700, fontSize: 46, padding: '20px 40px 22px 34px',
        borderRadius: 14, borderLeft: `12px solid ${bar}`, maxWidth: 1600, textAlign: 'center', boxShadow: '0 12px 40px rgba(0,0,0,.35)' }}>{text}</div>
    </div>
  )
}
const SUBS: Record<string, [number, number, string][]> = (VDIR === 'voice' ? SUBS_AI : SUBS_CLONE) as never
const Subtitle: React.FC<{ voice: string; at: number }> = ({ voice, at }) => {
  const t = useCurrentFrame() / FPS - at
  const cue = (SUBS[voice] || []).find(([a, b]) => t >= a && t < b)
  if (!cue) return null
  return (
    <div style={{ position: 'absolute', left: 0, right: 0, bottom: 34, display: 'flex', justifyContent: 'center' }}>
      <div style={{ background: 'rgba(0,0,0,.72)', color: '#fff', fontFamily: 'Noto', fontSize: 34, lineHeight: 1.3, padding: '6px 18px',
        borderRadius: 8, maxWidth: 1500, textAlign: 'center' }}>{cue[2]}</div>
    </div>
  )
}
const Badge: React.FC<{ text: string; corner: 'tl' | 'tr' | 'bl'; color?: string }> = ({ text, corner, color = YELLOW }) => {
  const f = useCurrentFrame()
  const a = Math.min(1, f / 12)
  const pos: React.CSSProperties = corner === 'tl' ? { left: 28, top: 26 } : corner === 'tr' ? { right: 28, top: 26 } : { left: 28, top: 74 }
  return <div style={{ position: 'absolute', ...pos, opacity: a, background: 'rgba(17,20,24,.86)', color, fontFamily: 'Noto', fontWeight: 700,
    fontSize: 22, letterSpacing: 1.5, padding: '8px 14px', borderRadius: 8, border: `1.5px solid ${color}55` }}>{text}</div>
}
const Card: React.FC<{ title: string; sub?: string }> = ({ title, sub }) => {
  const f = useCurrentFrame()
  const s = spring({ frame: f, fps: FPS, config: { damping: 16 } })
  return (
    <AbsoluteFill style={{ background: INK, alignItems: 'center', justifyContent: 'center', fontFamily: 'Noto' }}>
      <div style={{ transform: `scale(${0.9 + 0.1 * s})`, opacity: s, textAlign: 'center' }}>
        <div style={{ color: YELLOW, fontWeight: 700, fontSize: 30, letterSpacing: 6 }}>{sub}</div>
        <div style={{ color: '#fff', fontWeight: 700, fontSize: 96, marginTop: 10 }}>{title}</div>
      </div>
    </AbsoluteFill>
  )
}

// ---------------------------------------------------------------- scene speciale
// 1 — fluturașul Mariei: zoom pe net, apoi „should be 8,307”
const Hook: React.FC = () => {
  const f = useCurrentFrame(), t = f / FPS
  const IW = 1240, IH = 1754, scale0 = H / IH   // imaginea încape pe înălțime
  const net = { x: (820 + 1165) / 2, y: (895 + 950) / 2 }
  const z = interpolate(t, [0.5, 4], [1, 3.1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) })
  const back = interpolate(t, [9.5, 12.5], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) })
  const s = scale0 * (z - (z - 1) * back)
  const cx = IW / 2 + (net.x - IW / 2) * (1 - back), cy = IH / 2 + (net.y - IH / 2) * (1 - back)
  const strike = interpolate(t, [4.2, 4.8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
  const tag = spring({ frame: f - 5.2 * FPS, fps: FPS, config: { damping: 14 } })
  const bx = W / 2 + (820 - cx) * s, by = H / 2 + (895 - cy) * s, bw = (1165 - 820) * s, bh = (950 - 895) * s
  return (
    <AbsoluteFill style={{ background: '#E9EBEE' }}>
      <Img src={staticFile('img/maria_fluturas.jpg')} style={{ position: 'absolute', width: IW * s, height: IH * s, left: W / 2 - cx * s, top: H / 2 - cy * s,
        boxShadow: '0 30px 80px rgba(0,0,0,.25)' }} />
      {back < 0.5 && <>
        <div style={{ position: 'absolute', left: bx - 8, top: by - 6, width: (bw + 16) * strike, height: bh + 12, border: `5px solid ${DANGER}`, borderRadius: 10, opacity: strike }} />
        <div style={{ position: 'absolute', left: bx + bw - 30, top: by + bh + 26, transform: `scale(${tag})`, transformOrigin: 'left top', background: DANGER,
          color: '#fff', fontFamily: 'Noto', fontWeight: 700, fontSize: 52, padding: '10px 26px', borderRadius: 12 }}>should be 8,307</div>
      </>}
    </AbsoluteFill>
  )
}

// 8 — schema celor 6 pași; cei doi cu AI evidențiați
const STEPS = [['Guard', 'OCR · hides personal data', false], ['Clerk', 'reads the fields', true], ['Verifier', 'tax tables · registry', false],
  ['Detector', 'image forensics', false], ['Detective', 'links between files', false], ['Compliance', 'rules decide · AI summarises', true]] as const
const Design: React.FC = () => {
  const f = useCurrentFrame()
  return (
    <AbsoluteFill style={{ background: INK, fontFamily: 'Noto', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ color: '#C9CED6', fontSize: 34, marginBottom: 46 }}>The order is fixed in code: the same steps on every file</div>
      <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
        {STEPS.map(([name, role, ai], i) => {
          const s = spring({ frame: f - i * 7, fps: FPS, config: { damping: 15 } })
          const glow = ai ? 0.5 + 0.5 * Math.sin((f - 40) / 9) : 0
          return (
            <React.Fragment key={name}>
              {i > 0 && <div style={{ color: '#4E5764', fontSize: 40, opacity: s }}>→</div>}
              <div style={{ width: 214, height: 210, borderRadius: 18, padding: 22, opacity: s, transform: `translateY(${(1 - s) * 40}px)`,
                background: ai ? '#2A2610' : '#1A1E25', border: `2.5px solid ${ai ? YELLOW : '#323843'}`,
                boxShadow: ai && f > 40 ? `0 0 ${20 + 30 * glow}px ${YELLOW}55` : 'none', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div style={{ color: ai ? YELLOW : '#6B7480', fontSize: 20, fontWeight: 700, letterSpacing: 2 }}>{ai ? 'AI' : 'RULES & TOOLS'}</div>
                <div>
                  <div style={{ color: '#fff', fontSize: 36, fontWeight: 700 }}>{name}</div>
                  <div style={{ color: '#9AA3AE', fontSize: 22, marginTop: 6 }}>{role}</div>
                </div>
              </div>
            </React.Fragment>
          )
        })}
      </div>
      <div style={{ color: '#9AA3AE', fontSize: 28, marginTop: 50, opacity: interpolate(f, [9 * FPS, 10 * FPS], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }}>
        If a step fails, the others finish and the file is never shown as clean.</div>
    </AbsoluteFill>
  )
}

// 11 — cifrele, care urcă animat
const NUMS = [[0, 0, '', 'names or ID numbers\nsent to the cloud', OK], [0, 12, ' / 12', 'honest applicants\nflagged high-risk', OK],
  [36, 36, ' / 36', 'simple forgeries\ncaught', YELLOW], [12, 12, ' / 12', 'perfect forgeries\nsent to a human', YELLOW]] as const
const Numbers: React.FC = () => {
  const f = useCurrentFrame()
  return (
    <AbsoluteFill style={{ background: INK, fontFamily: 'Noto', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ color: '#fff', fontWeight: 700, fontSize: 52 }}>Measured with the real cloud AI · 60 synthetic applications</div>
      <div style={{ display: 'flex', gap: 36, marginTop: 70 }}>
        {NUMS.map(([v, , suf, label, color], i) => {
          const start = 10 + i * 40
          const s = spring({ frame: f - start, fps: FPS, config: { damping: 16 } })
          const n = Math.round(interpolate(f, [start, start + 30], [0, v], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }))
          return (
            <div key={i} style={{ width: 370, height: 380, borderRadius: 22, background: '#171B21', border: '2.5px solid #323843', opacity: s,
              transform: `translateY(${(1 - s) * 50}px)`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ color, fontWeight: 700, fontSize: 104 }}>{n}{suf}</div>
              <div style={{ color: '#C9CED6', fontSize: 32, textAlign: 'center', whiteSpace: 'pre-line', marginTop: 18 }}>{label}</div>
            </div>
          )
        })}
        {NUMS.map(([v], i) => Array.from({ length: Math.min(10, Math.max(1, v)) }, (_, k) => (
          <Sequence key={`t${i}-${k}`} from={10 + i * 40 + k * 3}><Audio src={staticFile('sfx/tick.wav')} volume={0.22} /></Sequence>
        )))}
      </div>
      <div style={{ textAlign: 'center', marginTop: 56, opacity: interpolate(f, [190, 220], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }}>
        <div style={{ color: '#fff', fontSize: 34, fontWeight: 700 }}>3 of 12 honest files went to a human · ~10 s per file</div>
        <div style={{ color: YELLOW, fontSize: 34, fontWeight: 700, marginTop: 10 }}>~$0.005 per file in the cloud · local: no per-file AI bill</div>
      </div>
      <div style={{ color: '#7C8591', fontSize: 26, marginTop: 18 }}>Synthetic data and forgeries made by us: a correctness test of the pipeline, not accuracy on real fraud.</div>
    </AbsoluteFill>
  )
}

// 12 — terminalul (ieșirea reală a testelor) + limitele
const Terminal: React.FC = () => {
  const f = useCurrentFrame()
  const lines = ['$ cd backend && python -m pytest -q', '........................................................................ [ 26%]',
    '........................................................................ [ 52%]', '........................................................................ [ 79%]',
    '...........................................................              [100%]', '275 passed in 6.9s', '',
    '$ python scripts/benchmark_pipeline.py --n 12      # no API key needed']
  const shown = Math.floor(interpolate(f, [8, 80], [1, lines.length], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }))
  return (
    <AbsoluteFill style={{ background: '#0B0D10', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: 1500, borderRadius: 16, background: '#14171C', border: '1.5px solid #2A2F37', boxShadow: '0 30px 90px rgba(0,0,0,.5)' }}>
        <div style={{ display: 'flex', gap: 10, padding: '16px 20px', borderBottom: '1.5px solid #2A2F37' }}>
          {['#F97066', '#FDB022', '#47CD89'].map((c) => <div key={c} style={{ width: 16, height: 16, borderRadius: 8, background: c }} />)}
        </div>
        <pre style={{ margin: 0, padding: '26px 34px 34px', fontFamily: 'monospace', fontSize: 30, lineHeight: 1.55, color: '#C9CED6', minHeight: 420 }}>
          {lines.slice(0, shown).map((l, i) => <div key={i} style={{ color: l.includes('passed') ? OK : l.startsWith('$') ? YELLOW : '#C9CED6', fontWeight: l.includes('passed') ? 700 : 400 }}>{l || ' '}</div>)}
        </pre>
      </div>
    </AbsoluteFill>
  )
}

// 11 — Arena: telefonul (clip vertical) într-o ramă, pe fundal închis
const Phone: React.FC<{ src: string; from: number; rate?: number }> = ({ src, from, rate = 1 }) => {
  const f = useCurrentFrame()
  const sIn = spring({ frame: f, fps: FPS, config: { damping: 18 } })
  return (
    <AbsoluteFill style={{ background: 'radial-gradient(circle at 50% 40%, #232833, #0B0D10 70%)', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ height: 960, width: 960 * 780 / 1688, borderRadius: 54, padding: 14, background: '#05060A', boxShadow: '0 40px 100px rgba(0,0,0,.6), 0 0 0 2px #2A2F37',
        transform: `translateY(${(1 - sIn) * 60}px)`, opacity: sIn }}>
        <div style={{ width: '100%', height: '100%', borderRadius: 42, overflow: 'hidden' }}>
          <OffthreadVideo src={staticFile('rec/' + src)} startFrom={Math.round(from * FPS)} playbackRate={rate} muted style={{ width: '200%', height: '200%' }} />
        </div>
      </div>
    </AbsoluteFill>
  )
}

// ---------------------------------------------------------------- un clip înregistrat, cu viteză și cameră
const Clip: React.FC<{ src: string; from: number; rate?: number; keys?: Key[]; filter?: string }> = ({ src, from, rate = 1, keys = [], filter }) => (
  <AbsoluteFill style={{ background: '#fff', overflow: 'hidden', filter }}>
    <Camera keys={keys}><OffthreadVideo src={staticFile('rec/' + src)} startFrom={Math.round(from * FPS)} playbackRate={rate} muted /></Camera>
  </AbsoluteFill>
)
// timpul dintr-un clip → timpul din scenă (pentru zoom-uri și sunete pe click)
const at = (clipT: number, from: number, rate = 1, offset = 0) => offset + (clipT - from) / rate
const Z = (t: number, s: number, x: number, y: number): Key => ({ t, s, x, y })

// ---------------------------------------------------------------- scenele (secunde)
// momentele din clipurile Arenei (din rec7/clicks.json)
const PHONE_FROM = 9.6
// din clipul nou v3_maria (se actualizează după filmare)
const EDIT_FROM = 83.7
type Part = { dur: number; el: React.ReactNode }
type Scene = { id: string; dur: number; voice?: string; voiceAt?: number; parts: Part[]; captions?: [string, number, number, ('info' | 'danger' | 'ok')?, boolean?][];
  badges?: [string, 'tl' | 'tr' | 'bl', string?][]; sfx?: [string, number, number?][] }

const SCENES: Scene[] = [
  { id: 'intro', dur: 4, parts: [{ dur: 4, el: <OffthreadVideo src={staticFile('orb_intro.mp4')} /> }] },
  { id: 'hook', dur: 14.5, voice: 's01', voiceAt: 0.05, parts: [{ dur: 14.5, el: <Hook /> }],
    captions: [['~20 min per file · our timing, not bank data', 9.6, 14.2]], sfx: [['alert', 4.3, 0.5]] },
  { id: 'new', dur: 13, voice: 's02', parts: [{ dur: 13, el: <Clip src="v2_new.webm" from={1} keys={[Z(0, 1, 960, 540), Z(3, 1, 960, 540), Z(6, 1.18, 960, 520)]} /> }],
    captions: [['User: credit analyst', 1, 5.6], ['Dashboard counters: seeded demo data, not real costs or outcomes', 6.2, 12.6]], sfx: [['click', at(4.54, 1)]] },
  // 3 — ce a văzut AI-ul (Maria)
  { id: 'names', dur: 9, voice: 's03', parts: [{ dur: 9, el: <Clip src="v3_maria.webm" from={52.3} keys={[Z(0, 1, 960, 540), Z(1.6, 1.55, 760, 420), Z(7.2, 1.55, 760, 420), Z(9.2, 1.3, 760, 420)]} /> }],
    sfx: [['click', at(53.68, 52.3)], ['click', at(59.18, 52.3)]] },
  // 4 — agenții (2×) → dovezile pe document (1,5×)
  { id: 'agents', dur: 25, voice: 's04', voiceAt: 1.4, parts: [
    { dur: 10, el: <Clip src="v3_maria.webm" from={8} rate={2.2} keys={[Z(0, 1.35, 960, 330), Z(9, 1.35, 960, 330)]} /> },
    { dur: 15, el: <Clip src="v3_maria.webm" from={63.7} rate={1.0} keys={[Z(0, 1, 960, 540), Z(0.9, 1.6, 930, 560), Z(5.0, 1.6, 930, 560), Z(6.0, 1.45, 1300, 420), Z(15, 1.45, 1300, 470)]} /> }],
    captions: [['8,307 ≠ 8,500 lei', 11.0, 15.2, 'danger', true], ['Employer: inactive · DEMO REGISTRY (real ANAF API for real companies)', 17.4, 20.6, 'info', true], ['Salary never arrives in the statement', 21.0, 24.8, 'danger', true]],
    badges: [['2× SPEED', 'tr'], ['ENCRYPTED-COMPUTE & ZK CARDS = PROTOTYPES', 'bl', '#C9CED6']], sfx: [['whoosh', 0.2, 0.6], ['click', 10 + at(64.52, 63.7, 1.0)], ['click', 10 + at(70.92, 63.7, 1.0)], ['click', 10 + at(77.35, 63.7, 1.0)]] },
  // 5 — harta editării + graful
  { id: 'detect', dur: 8, voice: 's05', parts: [
    { dur: 4, el: <Clip src="v3_maria.webm" from={EDIT_FROM} filter="brightness(2.6) contrast(1.3)" keys={[Z(0, 1.5, 760, 560), Z(4, 1.7, 760, 600)]} /> },
    { dur: 4, el: <Clip src="v5_graph.webm" from={9.2} keys={[Z(0, 1.5, 700, 440), Z(2.5, 2.1, 690, 470)]} /> }],
    captions: [['Edit map: bright = area re-saved after the first save', 0.4, 3.8, 'danger', true], ['1 bank account · Maria + 5 other applications', 4.4, 7.8, 'danger']], sfx: [['click', 0.4]] },
  // 6 — decizia
  { id: 'decide', dur: 16, voice: 's06', parts: [{ dur: 16, el: <Clip src="v6_decision.webm" from={6.4} rate={1.35}
    keys={[Z(0, 1.5, 1600, 300), Z(at(9.94, 6.4, 1.35), 1.5, 1600, 560), Z(at(16.09, 6.4, 1.35), 1.7, 1680, 420), Z(at(24.2, 6.4, 1.35), 1.6, 1680, 420)]} /> }],
    captions: [['Risk level = severity of the evidence, not an accusation', 0.4, 3.0], ['A summary with an unverified number = rejected', 3.2, 7.2], ['The AI doesn\'t decide', 11.8, 15.8, 'ok']],
    sfx: [['click', at(9.94, 6.4, 1.35)], ['ping', at(16.09, 6.4, 1.35) + 0.15, 0.7], ['click', at(24.53, 6.4, 1.35)]] },
  // 7 — al doilea dosar: poze neclare
  { id: 'blurry', dur: 13.5, voice: 's07', voiceAt: 1.4, parts: [
    { dur: 1.4, el: <Card title="Second file" sub="UNEXPECTED SITUATIONS" /> },
    { dur: 12.1, el: <Clip src="v7_blurry.webm" from={34.4} rate={1.05} keys={[Z(0, 1.4, 1600, 330), Z(4, 1.4, 1600, 330), Z(at(44.53, 34.4, 1.05), 1.65, 1660, 840), Z(12, 1.65, 1660, 840)]} /> }],
    captions: [['Unreadable photo: redaction can\'t be trusted, so its text is never sent to the AI', 1.6, 9.4]] },
  { id: 'design', dur: 15, voice: 's08', parts: [{ dur: 15, el: <Design /> }] },
  // 9 — dosarul cinstit
  { id: 'honest', dur: 8, voice: 's09', parts: [{ dur: 8, el: <Clip src="v9_honest.webm" from={31} rate={1.5} keys={[Z(0, 1.4, 1600, 330), Z(at(40.4, 31, 1.5), 1.4, 1600, 520), Z(8, 1.5, 1700, 700)]} /> }],
    captions: [['~20 min → ~1 min review (estimate) · 1 in 4 honest files still goes to a human', 3.8, 7.8, 'ok']], sfx: [['click', at(40.7, 31, 1.5)]] },
  // 10 — confidențialitate + comutatorul
  { id: 'privacy', dur: 12, voice: 's10', voiceAt: 0.15, parts: [{ dur: 12, el: <Clip src="v10_privacy.webm" from={8.4} rate={1.05}
    keys={[Z(0, 1.35, 700, 500), Z(6.0, 1.35, 700, 500), Z(6.9, 1.9, 1520, 60), Z(12, 1.9, 1520, 60)]} /> }],
    captions: [['switch shown only · local run tested on our demo laptop, ~9 s/file · demo cloud: AWS us-west-2 · production: EU region or local only', 6.8, 11.8]],
    badges: [['ENCRYPTED-COMPUTE & ZK CARDS = PROTOTYPES', 'bl', '#C9CED6']],
    sfx: [['click', at(9.15, 8.4, 1.05)], ['click', at(15.78, 8.4, 1.05)], ['click', at(20.09, 8.4, 1.05)]] },
  { id: 'numbers', dur: 15, voice: 's11', voiceAt: 0.4, parts: [{ dur: 15, el: <Numbers /> }] },
  // 11 — Arena: telefonul (prins + de ce) → proiectorul (regula propusă, testată, aprobată de om)
  { id: 'arena', dur: 12, voice: 's14', voiceAt: 0.2, parts: [
    { dur: 4.6, el: <Phone src="v11_phone.webm" from={PHONE_FROM} rate={1.15} /> },
    { dur: 2.4, el: <Clip src="v11_rule.webm" from={13} keys={[Z(0, 1.15, 640, 330), Z(2.4, 1.25, 640, 330)]} /> },
    { dur: 5, el: <Clip src="v11_approve.webm" from={3.8} rate={0.95} keys={[Z(0, 1, 960, 540), Z(0.9, 2.6, 369, 900), Z(5, 2.6, 369, 900)]} /> }],
    captions: [['Try it: orb-raiffeisen.vercel.app/arena', 0.5, 4.4, 'info', false],
      ['AI-proposed rule · back-tested on synthetic payslips · a human approves', 7.3, 11.8, 'ok', true]],
    sfx: [['whoosh', 4.5, 0.4], ['click', 7 + (8.44 - 3.8) / 0.95], ['ping', 7 + (8.44 - 3.8) / 0.95 + 0.15, 0.55]] },
  { id: 'limits', dur: 11, voice: 's12', voiceAt: 0.1, parts: [{ dur: 11, el: <Terminal /> }],
    captions: [['Limits: synthetic data · our own forgeries · a forger who also fakes the statement would pass', 1.2, 6.4, 'danger'], ['Shown: offline replay, no API key · the 60-file benchmark used the real cloud AI', 6.8, 10.8]] },
  { id: 'outro', dur: 4, voice: 's13', voiceAt: 0.6, parts: [{ dur: 4, el: <OffthreadVideo src={staticFile('orb_outro.mp4')} /> }] },
]

export const TOTAL_FRAMES = Math.round(SCENES.reduce((a, s) => a + s.dur, 0) * FPS)
const START: number[] = []
SCENES.reduce((a, s, i) => { START[i] = a; return a + s.dur }, 0)

// insigna „SYNTHETIC DATA” stă de la scena 1 până la cifre (inclusiv)
const SYN_FROM = START[1], SYN_TO = START[SCENES.findIndex((s) => s.id === 'numbers')]

export const ORB: React.FC = () => {
  const f = useCurrentFrame()
  const { durationInFrames } = useVideoConfig()
  const musicVol = (fr: number) => {
    const t = fr / FPS, T = durationInFrames / FPS
    const edge = t < 4 || t > T - 4.5 ? 0.32 : 0.11                 // mai tare pe intro/outro, discret sub voce
    return edge * Math.min(1, t / 1.5, (T - t) / 2.5)
  }
  return (
    <AbsoluteFill style={{ background: INK }}>
      <style>{fontFace}</style>
      {SCENES.map((s, i) => {
        let off = 0
        return (
          <Sequence key={s.id} from={Math.round(START[i] * FPS)} durationInFrames={Math.round(s.dur * FPS)} name={s.id}>
            {s.parts.map((p, j) => {
              const el = <Sequence key={j} from={Math.round(off * FPS)} durationInFrames={Math.round(p.dur * FPS)}>{p.el}</Sequence>
              off += p.dur
              return el
            })}
            {(s.captions || []).map(([text, a, b, tone, top], j) => <Caption key={j} text={text} from={a} to={b} tone={tone} top={top} />)}
            {(s.captions || []).map(([, a], j) => <Sequence key={'pop' + j} from={Math.round(a * FPS)}><Audio src={staticFile('sfx/pop.wav')} volume={0.28} /></Sequence>)}
            {(s.badges || []).map(([text, corner, color], j) => <Badge key={j} text={text} corner={corner} color={color} />)}
            {s.voice && s.id !== 'outro' && <Subtitle voice={s.voice} at={s.voiceAt ?? 0.3} />}
            {s.voice && <Sequence from={Math.round((s.voiceAt ?? 0.3) * FPS)}><Audio src={staticFile(`${VDIR}/${s.voice}.wav`)} /></Sequence>}
            {(s.sfx || []).map(([name, t, vol], j) => (
              <Sequence key={j} from={Math.max(0, Math.round(t * FPS))}><Audio src={staticFile(`sfx/${name}.wav`)} volume={vol ?? 0.35} /></Sequence>
            ))}
          </Sequence>
        )
      })}
      {f >= SYN_FROM * FPS && f < SYN_TO * FPS && (
        <Sequence from={Math.round(SYN_FROM * FPS)} durationInFrames={Math.round((SYN_TO - SYN_FROM) * FPS)}>
          <Badge text="SYNTHETIC DATA · DEMO" corner="tl" />
        </Sequence>
      )}
      {f >= START[2] * FPS && f < (START[2] + 6) * FPS && (
        <Sequence from={Math.round(START[2] * FPS)} durationInFrames={6 * FPS}><Badge text="SCREEN RECORDING · SPED UP · CUTS BETWEEN FILES" corner="bl" color="#C9CED6" /></Sequence>
      )}
      {MUSIC && <Audio src={staticFile(MUSIC)} volume={musicVol} />}
    </AbsoluteFill>
  )
}
