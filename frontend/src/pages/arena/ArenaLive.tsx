import { useQuery, useQueryClient } from '@tanstack/react-query'
import QRCode from 'qrcode'
import { useEffect, useState } from 'react'
import { AlertOctagon, Brain, CircleHelp, ShieldCheck, Trophy } from 'lucide-react'
import { AGENT_RO, getLeaderboard, subscribeArenaLive, type Submission } from '@/lib/arena'
import { apiUrl } from '@/lib/config'
import { cn } from '@/lib/utils'
import { ArenaControls } from '@/components/ArenaControls'

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

const agentName = (a: string) => AGENT_RO[a] ?? a

function line(s: Submission): { icon: typeof Trophy; text: string; tone: string } {
  if (s.outcome === 'passed') {
    // 0 puncte = fals repetat sau plafon atins → nu afișăm „+0”
    return { icon: Trophy, text: `${s.nickname} a păcălit agenții${s.points ? `, +${s.points}` : ''}`, tone: 'text-brand' }
  }
  if (s.outcome === 'caught') return { icon: AlertOctagon, text: `${s.nickname}, prins de ${s.caught_by.map(agentName).join(' și ')}`, tone: 'text-night-ink' }
  return { icon: CircleHelp, text: `${s.nickname}: fals invalid`, tone: 'text-night-mute' }
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
  const [show, setShow] = useState<Submission[]>([]) // încercările de afișat mare, pe rând
  const current = show[0]
  useEffect(() => {
    if (!current) return
    const t = setTimeout(() => setShow((q) => q.slice(1)), current.outcome === 'passed' ? 6000 : 3500)
    return () => clearTimeout(t)
  }, [current])
  const base = publicBase()
  const url = playUrl(base)

  useEffect(() => {
    QRCode.toDataURL(url, { width: 520, margin: 1, errorCorrectionLevel: 'M' }).then(setQr).catch(() => setQr(''))
  }, [url])

  useEffect(() => {
    return subscribeArenaLive({
      onOpen: () => {
        setConnected(true)
        qc.invalidateQueries({ queryKey: ['arena-top'] }) // după o reconectare am putut pierde încercări
      },
      onDown: () => setConnected(false),
      onMessage: ({ event, data }) => {
        if (event === 'arena_scored') {
          qc.invalidateQueries({ queryKey: ['arena-top'] })
          const sub = data.data as unknown as Submission | undefined
          if (sub && sub.outcome !== 'invalid') setShow((q) => [...q, sub].slice(-6)) // coadă scurtă: nu rămânem în urmă
        }
        if (event === 'rule_proposed' || event === 'rule_approved') {
          setLearning((l) => [{ approved: event === 'rule_approved', message: data.message, at: Date.now() }, ...l].slice(0, 3))
        }
        if (event === 'agent_progress') { // rundele Atacatorului
          const st = data.data?.attacker as AttackerStatus | undefined
          if (st) { setAttacker(st); setAttackerLine(data.message ?? '') }
        }
      },
    })
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
    <div className="flex h-dvh flex-col overflow-hidden bg-night text-night-ink">
      <ArenaControls running={Boolean(attacker?.running)} />
      {current && <Spotlight key={current.id} s={current} waiting={show.length - 1} />}
      <div className="h-1.5 shrink-0 bg-brand" />
      <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,5fr)_minmax(0,7fr)_minmax(0,5fr)] gap-12 p-12">
        <section className="flex flex-col justify-center">
          <div className="flex items-center gap-4">
            <span className="grid h-14 w-14 place-items-center rounded-sm bg-brand font-condensed text-3xl font-bold text-ink">O</span>
            <h1 className="text-5xl font-bold tracking-tight">ORB Arena</h1>
          </div>
          <p className="mt-4 text-2xl leading-snug text-night-mute">Scanează codul și încearcă să păcălești agenții băncii cu un fluturaș fals.</p>
          {qr && <img src={qr} alt="Cod QR pentru Arena" className="mt-8 w-[min(100%,24rem)] rounded-md bg-white p-3" />}
          <p className="mt-5 break-all text-2xl font-semibold text-brand">{url.replace(/^https?:\/\//, '').split('?')[0]}</p>
          {isLocal(base) && (
            <p className="mt-3 rounded-sm border border-night-danger/60 bg-night-danger/10 px-3 py-2 text-lg text-night-danger">
              Telefoanele nu pot deschide localhost. Deschide pagina cu ?base=https://adresa-publică
            </p>
          )}
          <p className="mt-4 text-xl text-night-mute">Joc demonstrativ. Nu încărca documente reale.</p>
        </section>

        <section className="flex min-h-0 flex-col">
          <h2 className="flex items-center gap-3 text-3xl font-semibold">
            Încercări în timp real
            <span className={cn('h-3 w-3 rounded-full', connected ? 'bg-night-ok' : 'bg-night-line')} aria-label={connected ? 'conectat' : 'deconectat'} />
          </h2>
          {learning.length > 0 && (
            <div className={cn('mt-5 rounded-md border p-5 transition-colors', fresh ? 'border-brand bg-brand/10' : 'border-night-line bg-night-2')}>
              <div className="flex items-center gap-2 text-xl font-semibold text-brand"><Brain className="h-6 w-6" aria-hidden />Agenții au învățat</div>
              {learning.map((l) => (
                <p key={l.at} className={cn('mt-2 text-2xl leading-snug', l === learning[0] ? 'text-night-ink' : 'text-night-mute')}>{l.message}</p>
              ))}
            </div>
          )}
          <ul className="mt-5 min-h-0 flex-1 divide-y divide-night-line overflow-hidden">
            {board.data?.feed.slice(0, 9).map((s, i) => {
              const l = line(s)
              return (
                <li key={s.id} className={cn('flex items-center gap-4 py-4 text-2xl', l.tone, i === 0 && 'font-semibold')}>
                  <l.icon className="h-7 w-7 shrink-0" aria-hidden />{l.text}
                </li>
              )
            })}
            {board.data && board.data.feed.length === 0 && <li className="py-4 text-2xl text-night-mute">Așteptăm prima încercare.</li>}
          </ul>
        </section>

        <section className="flex min-h-0 flex-col">
          <h2 className="text-3xl font-semibold">Top 10</h2>
          <ol className="mt-5 divide-y divide-night-line">
            {board.data?.top.map((r) => (
              <li key={r.rank} className="flex items-center gap-4 py-2.5 text-2xl">
                <span className={cn('w-9 text-right font-condensed font-bold tabular-nums', r.rank <= 3 ? 'text-brand' : 'text-night-mute')}>{r.rank}</span>
                <span className="flex-1 truncate">{r.nickname}</span>
                <span className="font-semibold tabular-nums">{r.points.toLocaleString('ro-RO')}</span>
              </li>
            ))}
          </ol>
          {attacker && attacker.rounds.length > 0 ? (
            <div className="mt-auto rounded-md border border-night-line bg-night-2 p-5">
              <div className="text-xl font-semibold">Atacatorul automat, pe runde{attacker.running ? ' (rulează)' : ''}</div>
              <ol className="mt-4 flex flex-wrap gap-2" aria-label="Rundele atacatorului">
                {attacker.rounds.map((r) => (
                  <li key={r.round} title={r.reasons.join('; ')}
                      className={cn('flex h-14 w-14 flex-col items-center justify-center rounded-sm border text-sm font-semibold',
                        r.outcome === 'passed' ? 'border-night-danger bg-night-danger/15 text-night-danger'
                          : r.outcome === 'caught' ? 'border-night-ok/60 bg-night-ok/10 text-night-ok' : 'border-night-line text-night-mute')}>
                    {r.outcome === 'passed' ? <AlertOctagon className="h-5 w-5" aria-hidden /> : <ShieldCheck className="h-5 w-5" aria-hidden />}
                    R{r.round}
                  </li>
                ))}
              </ol>
              <div className="mt-4 flex justify-between text-xl">
                <span className="text-night-ok">{attacker.caught} prinse</span><span className="text-night-danger">{attacker.passed} au trecut</span>
              </div>
              {attackerLine && <p className="mt-2 line-clamp-2 text-lg text-night-mute">{attackerLine.replace(/^\S+\s/, '').replace(': passed', ': a trecut').replace(': caught', ': prins').replace(': invalid', ': invalid')}</p>}
            </div>
          ) : st && (
            <div className="mt-auto rounded-md border border-night-line bg-night-2 p-5">
              <div className="text-xl font-semibold">Jucătorii împotriva agenților</div>
              <div className="mt-4 flex h-3 overflow-hidden rounded-full bg-night-line" role="img" aria-label={`${st.caught} prinse, ${st.passed} trecute`}>
                <div className="bg-night-ok" style={{ width: `${100 - passRate}%` }} />
                <div className="ml-0.5 bg-night-danger" style={{ width: `${passRate}%` }} />
              </div>
              <div className="mt-3 flex justify-between text-xl">
                <span className="text-night-ok">{st.caught} prinse</span>
                <span className="text-night-danger">{st.passed} au trecut, {passRate}%</span>
              </div>
              <div className="mt-1 text-lg text-night-mute">{st.players} jucători, {st.submissions} încercări</div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

/** Încercarea curentă, mare, peste tot ecranul: PRINS sau A TRECUT. Momentul pe care îl vede sala. */
function Spotlight({ s, waiting }: { s: Submission; waiting: number }) {
  const passed = s.outcome === 'passed'
  return (
    <div className="pointer-events-none fixed inset-0 z-30 flex items-center justify-center bg-night/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className={cn('w-[min(90vw,64rem)] rounded-lg border-4 p-12 text-center shadow-2xl animate-in zoom-in-90 duration-300',
        passed ? 'border-brand bg-[#2A2610]' : 'border-night-danger bg-[#2A1517]')}>
        <div className={cn('font-condensed text-[9rem] font-bold leading-none tracking-tight', passed ? 'text-brand' : 'text-night-danger')}>
          {passed ? 'A TRECUT' : 'PRINS'}
        </div>
        <div className="mt-6 text-5xl font-semibold text-night-ink">{s.nickname}</div>
        <div className="mt-4 text-3xl text-night-mute">
          {passed
            ? `a păcălit agenții${s.points ? `, +${s.points} puncte` : ''}`
            : `de ${s.caught_by.map((a) => AGENT_RO[a] ?? a).join(' și ')}`}
        </div>
        {!passed && s.reasons[0] && <div className="mx-auto mt-6 max-w-3xl text-3xl leading-snug text-night-ink">„{s.reasons[0]}”</div>}
        {passed && <div className="mt-6 text-3xl text-night-ink">Agenții învață acum din falsul ăsta.</div>}
        {waiting > 0 && <div className="mt-8 text-xl text-night-mute">încă {waiting} {waiting === 1 ? 'încercare' : 'încercări'} la rând</div>}
      </div>
    </div>
  )
}
