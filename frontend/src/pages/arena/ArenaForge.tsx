import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { getMissions, lei, savedNick, submitFake, type Mission } from '@/lib/arena'
import { cn } from '@/lib/utils'
import { ArenaShell } from './ArenaShell'

/** Previzualizarea fluturașului, desenată local (falsul real îl face serverul). */
function PayslipPreview({ doc, tricks }: { doc: Record<string, string | number>; tricks: string[] }) {
  const n = (v: string | number) => Number(v).toLocaleString('ro-RO', { minimumFractionDigits: 2 })
  // cu „recalculează taxele”, serverul pune netul exact; aici arătăm aproximarea (CAS 25%, CASS 10%, impozit 10%)
  const recompute = tricks.includes('recompute_taxes')
  const net = recompute ? Math.round(Number(doc.gross_salary) * 0.585) : doc.net_salary
  return (
    <div className="relative rounded-lg bg-white p-4 font-mono text-[13px] leading-6 text-slate-900 shadow-lg">
      <div className="text-center font-bold tracking-wide">FLUTURAȘ DE SALARIU</div>
      <div className="text-center text-xs text-slate-500">luna {String(doc.issue_date).slice(0, 7)}</div>
      <hr className="my-2 border-slate-300" />
      <div>Angajator: <b>{doc.employer}</b></div>
      <div>Angajat: {doc.employee}</div>
      <div>Funcția: {doc.job_title}</div>
      <hr className="my-2 border-slate-300" />
      <div className="flex justify-between"><span>Salariu brut</span><b>{n(doc.gross_salary)}</b></div>
      <div className="flex justify-between"><span>Salariu net</span><b>{recompute ? '≈ ' : ''}{n(net)}</b></div>
      <div className="mt-2 text-xs text-slate-500">Emis la {doc.issue_date}</div>
      {tricks.includes('ai_photo') && (
        <div className="absolute bottom-3 right-3 flex h-14 w-14 rotate-[-12deg] items-center justify-center rounded-full border-2 border-blue-700 text-[9px] font-bold text-blue-700">
          ȘTAMPILĂ<br />AI
        </div>
      )}
      {tricks.includes('hide_injection') && <div className="text-[9px] text-slate-200">text ascuns pentru AI…</div>}
    </div>
  )
}

function Forge({ mission }: { mission: Mission }) {
  const nav = useNavigate()
  const [doc, setDoc] = useState<Record<string, string | number>>({ ...mission.template })
  const [tricks, setTricks] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const recompute = tricks.includes('recompute_taxes')
  const target = mission.target
  const shownNet = recompute ? Math.round(Number(doc.gross_salary) * 0.585) : Number(doc[target.field])
  const targetMet = shownNet >= target.min

  const set = (k: string, v: string | number) => setDoc((d) => ({ ...d, [k]: v }))
  const toggle = (t: string) => setTricks((ts) => (ts.includes(t) ? ts.filter((x) => x !== t) : [...ts, t]))

  async function send() {
    setBusy(true)
    setError(null)
    const edits = Object.fromEntries(Object.entries(doc).filter(([k, v]) => k in mission.editable && v !== mission.template[k]))
    try {
      const res = await submitFake({ nickname: savedNick(), mission_id: mission.id, edits, tricks })
      nav(`/arena/r/${res.id}`, { state: res })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Nu s-a putut trimite')
      setBusy(false)
    }
  }

  return (
    <ArenaShell>
      <h2 className="text-2xl font-bold">{mission.title}</h2>
      <p className="mt-1 text-slate-300">{mission.brief}</p>

      <div className="mt-4"><PayslipPreview doc={doc} tricks={tricks} /></div>

      <h3 className="mt-6 text-lg font-bold">✏️ Modifică documentul</h3>
      <div className="mt-2 space-y-4">
        {Object.entries(mission.editable).map(([key, spec]) => {
          const disabled = key === 'net_salary' && recompute
          const cls = 'mt-1 h-14 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 text-lg outline-none focus:border-amber-400 disabled:opacity-40'
          return (
            <label key={key} className="block">
              <span className="text-base text-slate-300">{spec.label}{disabled && ' — se calculează din brut'}</span>
              {spec.type === 'select' ? (
                <select className={cls} value={String(doc[key])} onChange={(e) => set(key, e.target.value)}>
                  {spec.options?.map((o) => <option key={o} value={o}>{o}</option>)}
                </select>
              ) : (
                <input
                  className={cls}
                  disabled={disabled}
                  type={spec.type === 'number' ? 'number' : spec.type === 'date' ? 'date' : 'text'}
                  inputMode={spec.type === 'number' ? 'numeric' : undefined}
                  min={spec.min}
                  max={spec.max}
                  value={String(doc[key])}
                  onChange={(e) => set(key, spec.type === 'number' ? Number(e.target.value) : e.target.value)}
                />
              )}
            </label>
          )
        })}
      </div>

      <h3 className="mt-6 text-lg font-bold">🧪 Trucuri</h3>
      <div className="mt-2 space-y-2">
        {Object.entries(mission.tricks).map(([key, label]) => {
          const on = tricks.includes(key)
          return (
            <button key={key} type="button" onClick={() => toggle(key)} aria-pressed={on}
              className={cn('flex min-h-14 w-full items-center gap-3 rounded-xl border px-4 py-3 text-left text-base',
                on ? 'border-amber-400 bg-amber-400/10' : 'border-slate-700 bg-slate-900')}>
              <span className="text-2xl">{on ? '✅' : '⬜'}</span>{label}
            </button>
          )
        })}
      </div>

      <div className="sticky bottom-20 mt-6 space-y-2 rounded-2xl bg-slate-950/90 py-3 backdrop-blur">
        <p className={cn('text-center text-base', targetMet ? 'text-emerald-400' : 'text-amber-300')}>
          {targetMet ? '🎯 Ținta e atinsă' : `🎯 Ținta: net ≥ ${lei(target.min)}`}
        </p>
        {error && <p className="text-center text-red-400">{error}</p>}
        <button type="button" onClick={send} disabled={busy}
          className="h-16 w-full rounded-2xl bg-amber-400 text-xl font-black text-slate-950 active:scale-[0.99] disabled:opacity-60">
          {busy ? 'Agenții verifică…' : '🚀 Trimite falsul'}
        </button>
      </div>
    </ArenaShell>
  )
}

export function ArenaForge() {
  const { missionId } = useParams()
  const missions = useQuery({ queryKey: ['arena-missions'], queryFn: getMissions, staleTime: 60_000 })
  if (!savedNick()) return <Navigate to="/arena" replace />
  const mission = missions.data?.find((m) => m.id === missionId)
  if (missions.isLoading) return <ArenaShell><p className="text-slate-400">Se încarcă…</p></ArenaShell>
  if (!mission) return <ArenaShell><p className="text-red-400">Misiunea nu există.</p></ArenaShell>
  return <Forge key={mission.id} mission={mission} />
}
