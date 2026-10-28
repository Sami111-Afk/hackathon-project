import { useQuery, useQueryClient } from '@tanstack/react-query'
import QRCode from 'qrcode'
import { useEffect, useState } from 'react'
import { AGENT_RO, getLeaderboard, liveUrl, type Submission } from '@/lib/arena'
import { apiUrl } from '@/lib/config'
import { cn } from '@/lib/utils'

/** URL-ul din QR: dacă backend-ul vine din ?api=, îl dăm mai departe telefoanelor. */
function playUrl(): string {
  const url = new URL('/arena', window.location.origin)
  if (apiUrl() !== (import.meta.env.VITE_API_URL || 'http://localhost:8000')) url.searchParams.set('api', apiUrl())
  return url.toString()
}

function line(s: Submission): { icon: string; text: string; cls: string } {
  if (s.outcome === 'passed') return { icon: '🏆', text: `${s.nickname} a păcălit agenții! +${s.points}`, cls: 'text-emerald-300' }
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
  const url = playUrl()

  useEffect(() => {
    QRCode.toDataURL(url, { width: 520, margin: 1, errorCorrectionLevel: 'M' }).then(setQr).catch(() => setQr(''))
  }, [url])

  useEffect(() => {
    // public, fără headere → EventSource nativ (se reconectează singur)
    const es = new EventSource(liveUrl())
    es.onopen = () => setConnected(true)
    es.onerror = () => setConnected(false)
    es.addEventListener('arena_scored', () => qc.invalidateQueries({ queryKey: ['arena-top'] }))
    return () => es.close()
  }, [qc])

  const st = board.data?.stats
  const passRate = st && st.valid ? Math.round((st.passed / st.valid) * 100) : 0

  return (
    <div className="grid h-dvh grid-cols-[minmax(0,5fr)_minmax(0,7fr)_minmax(0,5fr)] gap-8 overflow-hidden bg-slate-950 p-10 text-slate-100">
      <section className="flex flex-col items-center justify-center text-center">
        <h1 className="text-5xl font-black">🎮 ORB Arena</h1>
        <p className="mt-3 text-2xl text-slate-300">Păcălește agenții AI ai băncii</p>
        {qr && <img src={qr} alt="Cod QR pentru Arena" className="mt-8 w-[min(100%,26rem)] rounded-2xl bg-white p-3" />}
        <p className="mt-6 break-all font-mono text-xl text-amber-300">{url.replace(/^https?:\/\//, '').split('?')[0]}</p>
        <p className="mt-4 text-lg text-slate-400">⚠️ Joc demonstrativ. Nu încărcați documente reale.</p>
      </section>

      <section className="flex min-h-0 flex-col">
        <h2 className="flex items-center gap-3 text-3xl font-bold">
          Live <span className={cn('h-3 w-3 rounded-full', connected ? 'bg-emerald-400' : 'bg-slate-600')} aria-label={connected ? 'conectat' : 'deconectat'} />
        </h2>
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
        {st && (
          <div className="mt-auto rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="text-xl text-slate-300">AI atacator vs AI apărător</div>
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
