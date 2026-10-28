import { useQuery, useQueryClient } from '@tanstack/react-query'
import QRCode from 'qrcode'
import { useEffect, useState } from 'react'
import { AGENT_RO, getLeaderboard, liveUrl, type Submission } from '@/lib/arena'
import { apiUrl } from '@/lib/config'
import { cn } from '@/lib/utils'

const BASE_KEY = 'orb.arena.base'

/**
 * Adresa publică pe care o deschid telefoanele: ?base=https://... (ținută minte) → VITE_PUBLIC_URL → adresa curentă.
 * Proiectorul poate fi deschis pe localhost, dar telefoanele au nevoie de adresa Vercel / ngrok.
 */
function publicBase(): string {
  const fromUrl = new URLSearchParams(window.location.search).get('base')
  if (fromUrl) { try { localStorage.setItem(BASE_KEY, fromUrl) } catch { /* mod privat */ } }
  let saved: string | null = null
  try { saved = localStorage.getItem(BASE_KEY) } catch { /* mod privat */ }
  return (fromUrl || saved || import.meta.env.VITE_PUBLIC_URL || window.location.origin).replace(/\/+$/, '')
}

/** URL-ul din QR: dacă backend-ul vine din ?api=, îl dăm mai departe telefoanelor. */
function playUrl(base: string): string {
  const url = new URL('/arena', base)
  if (apiUrl() !== (import.meta.env.VITE_API_URL || 'http://localhost:8000')) url.searchParams.set('api', apiUrl())
  return url.toString()
}

const isLocal = (u: string) => /\/\/(localhost|127\.|0\.0\.0\.0)/.test(u)

interface AttackerRound { round: number; outcome: 'passed' | 'caught' | 'invalid'; reasons: string[] }
interface AttackerStatus { running: boolean; rounds: AttackerRound[]; passed: number; caught: number }
interface LiveEvent { type: string; message: string; data?: Record<string, unknown> | null }

function line(s: Submission): { icon: string; text: string; cls: string } {
  if (s.outcome === 'passed') {
    // 0 puncte = fals repetat sau plafon atins → nu afișăm „+0”
    return { icon: '🏆', text: `${s.nickname} a păcălit agenții!${s.points ? ` +${s.points}` : ''}`, cls: 'text-emerald-300' }
  }
  if (s.outcome === 'caught') {
    return { icon: '🚨', text: `${s.nickname} prins de ${s.caught_by.map((a) => AGENT_RO[a] ?? a).join(', ')}`, cls: 'text-slate-100' }
  }
  return { icon: '🤔', text: `${s.nickname}: fals invalid`, cls: 'text-slate-400' }
}

/** Ecranul de pe proiector (1920×1080): QR, flux live, top 10, cât de des trec falsurile. */
export function ArenaLive() {
  const qc = useQueryClient()
  const board = useQuery({ queryKey: ['arena-top'], queryFn: getLeaderboard, refetchInterval: 15000 })
  const [qr, setQr] = useState('')
  const [connected, setConnected] = useState(false)
  const [learning, setLearning] = useState<{ approved: boolean; message: string; at: number }[]>([])
  const [attacker, setAttacker] = useState<AttackerStatus | null>(null)
  const [attackerLine, setAttackerLine] = useState('')
  const [now, setNow] = useState(() => Date.now())
  const base = publicBase()
  const url = playUrl(base)

  useEffect(() => {
    QRCode.toDataURL(url, { width: 520, margin: 1, errorCorrectionLevel: 'M' }).then(setQr).catch(() => setQr(''))
  }, [url])

  useEffect(() => {
    // public, fără headere → EventSource nativ (se reconectează singur)
    const es = new EventSource(liveUrl())
    const parse = (e: MessageEvent): LiveEvent | null => { try { return JSON.parse(e.data) } catch { return null } }
    es.onopen = () => {
      setConnected(true)
      qc.invalidateQueries({ queryKey: ['arena-top'] }) // după o reconectare am putut pierde trimiteri
    }
    es.onerror = () => setConnected(false)
    es.addEventListener('arena_scored', () => qc.invalidateQueries({ queryKey: ['arena-top'] }))
    const onRule = (approved: boolean) => (e: MessageEvent) => {
      const ev = parse(e)
      if (ev) setLearning((l) => [{ approved, message: ev.message, at: Date.now() }, ...l].slice(0, 3))
    }
    es.addEventListener('rule_proposed', onRule(false))
    es.addEventListener('rule_approved', onRule(true))
    es.addEventListener('agent_progress', (e) => { // rundele Atacatorului
      const ev = parse(e)
      const st = ev?.data?.attacker as AttackerStatus | undefined
      if (st) { setAttacker(st); setAttackerLine(ev?.message ?? '') }
    })
    return () => es.close()
  }, [qc])

  // ceas pentru evidențierea regulii noi (strălucește ~15 s)
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])
  const fresh = learning[0] && now - learning[0].at < 15000 ? learning[0] : null

  const st = board.data?.stats
  const passRate = st && st.valid ? Math.round((st.passed / st.valid) * 100) : 0

  return (
    <div className="grid h-dvh grid-cols-[minmax(0,5fr)_minmax(0,7fr)_minmax(0,5fr)] gap-8 overflow-hidden bg-slate-950 p-10 text-slate-100">
      <section className="flex flex-col items-center justify-center text-center">
        <h1 className="text-5xl font-black">🎮 ORB Arena</h1>
        <p className="mt-3 text-2xl text-slate-300">Păcălește agenții AI ai băncii</p>
        {qr && <img src={qr} alt="Cod QR pentru Arena" className="mt-8 w-[min(100%,26rem)] rounded-2xl bg-white p-3" />}
        <p className="mt-6 break-all font-mono text-2xl text-amber-300">{url.replace(/^https?:\/\//, '').split('?')[0]}</p>
        {isLocal(base) && (
          <p className="mt-3 rounded-lg bg-red-500/20 px-3 py-2 text-lg text-red-200">
            Telefoanele nu pot deschide localhost. Deschide pagina cu ?base=https://adresa-publică
          </p>
        )}
        <p className="mt-4 text-xl text-slate-300">⚠️ Joc demonstrativ. Nu încărcați documente reale.</p>
      </section>

      <section className="flex min-h-0 flex-col">
        <h2 className="flex items-center gap-3 text-3xl font-bold">
          Live <span className={cn('h-3 w-3 rounded-full', connected ? 'bg-emerald-400' : 'bg-slate-600')} aria-label={connected ? 'conectat' : 'deconectat'} />
        </h2>
        {learning.length > 0 && (
          <div className={cn('mt-4 rounded-2xl border-2 p-5 transition-colors',
            fresh ? 'border-amber-400 bg-amber-400/15' : 'border-slate-800 bg-slate-900')}>
            <div className="text-xl font-semibold text-amber-300">🧠 Agenții au învățat</div>
            {learning.map((l) => (
              <p key={l.at} className={cn('mt-2 text-2xl', l === learning[0] ? 'text-slate-50' : 'text-slate-400')}>
                {l.approved ? '✅' : '📝'} {l.message}
              </p>
            ))}
          </div>
        )}
        <ul className="mt-4 min-h-0 flex-1 space-y-3 overflow-hidden">
          {board.data?.feed.slice(0, 9).map((s, i) => {
            const l = line(s)
            return (
              <li key={s.id} className={cn('rounded-xl border border-slate-800 bg-slate-900 px-5 py-4 text-2xl', l.cls, i === 0 && 'border-amber-400')}>
                <span className="mr-3">{l.icon}</span>{l.text}
              </li>
            )
          })}
          {board.data && board.data.feed.length === 0 && <li className="text-2xl text-slate-500">Așteptăm primul fals…</li>}
        </ul>
      </section>

      <section className="flex min-h-0 flex-col">
        <h2 className="text-3xl font-bold">🏆 Top 10</h2>
        <ol className="mt-4 space-y-2">
          {board.data?.top.map((r) => (
            <li key={r.rank} className="flex items-center gap-4 text-2xl">
              <span className="w-10 text-right font-bold text-slate-400">{r.rank}.</span>
              <span className="flex-1 truncate">{r.nickname}</span>
              <span className="tabular-nums font-bold">{r.points.toLocaleString('ro-RO')}</span>
            </li>
          ))}
        </ol>
        {attacker && attacker.rounds.length > 0 && (
          <div className="mt-auto rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="text-xl text-slate-300">😈 AI atacator vs 🛡️ AI apărător {attacker.running ? '· rulează' : ''}</div>
            <ol className="mt-3 flex flex-wrap gap-2" aria-label="Rundele atacatorului">
              {attacker.rounds.map((r) => (
                <li key={r.round} title={r.reasons.join('; ')}
                    className={cn('flex h-14 w-14 flex-col items-center justify-center rounded-lg text-sm font-semibold',
                      r.outcome === 'passed' ? 'bg-red-500/25 text-red-100' : r.outcome === 'caught' ? 'bg-emerald-500/20 text-emerald-100' : 'bg-slate-800 text-slate-400')}>
                  <span className="text-xl">{r.outcome === 'passed' ? '😈' : r.outcome === 'caught' ? '🛡️' : '·'}</span>R{r.round}
                </li>
              ))}
            </ol>
            <div className="mt-3 flex justify-between text-xl">
              <span>🛡️ {attacker.caught} prinse</span><span>😈 {attacker.passed} au trecut</span>
            </div>
            {attackerLine && <p className="mt-2 line-clamp-2 text-lg text-slate-400">{attackerLine}</p>}
          </div>
        )}
        {st && !(attacker && attacker.rounds.length > 0) && (
          <div className="mt-auto rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="text-xl text-slate-300">Jucători vs agenții ORB</div>
            <div className="mt-3 flex h-6 overflow-hidden rounded-full bg-slate-800" role="img"
                 aria-label={`${st.caught} prinse, ${st.passed} trecute`}>
              <div className="bg-emerald-500" style={{ width: `${100 - passRate}%` }} />
              <div className="ml-0.5 bg-red-500" style={{ width: `${passRate}%` }} />
            </div>
            <div className="mt-3 flex justify-between text-xl">
              <span>🛡️ {st.caught} prinse</span>
              <span>🏆 {st.passed} au trecut ({passRate}%)</span>
            </div>
            <div className="mt-1 text-lg text-slate-400">{st.players} jucători · {st.submissions} încercări</div>
          </div>
        )}
      </section>
    </div>
  )
}
