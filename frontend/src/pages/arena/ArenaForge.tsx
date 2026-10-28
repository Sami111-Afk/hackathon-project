import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { getMissions, lei, savedNick, submitFake, type Mission } from '@/lib/arena'
import { Check, Send } from 'lucide-react'
import { cn } from '@/lib/utils'
import { ArenaShell } from './ArenaShell'

/** Previzualizarea fluturașului, desenată local (falsul real îl face serverul). */
function PayslipPreview({ doc, tricks, jobLabels }: {
  doc: Record<string, string | number>; tricks: string[]; jobLabels?: Record<string, string>
}) {
  const n = (v: string | number) => Number(v).toLocaleString('en-US', { minimumFractionDigits: 2 })
  // cu „recalculează taxele”, serverul pune netul exact; aici arătăm aproximarea (CAS 25%, CASS 10%, impozit 10%)
  const recompute = tricks.includes('recompute_taxes')
  const net = recompute ? Math.round(Number(doc.gross_salary) * 0.585) : doc.net_salary
  return (
    <div className="relative rounded-sm bg-white p-5 text-[14px] leading-6 text-ink">
      <div className="text-center font-bold">Payslip</div>
      <div className="text-center text-xs text-ink-3">Period {String(doc.issue_date).slice(0, 7)}</div>
      <hr className="my-2 border-line" />
      <div>Employer: <b>{doc.employer}</b></div>
      <div>Employee: {doc.employee}</div>
      <div>Job title: {jobLabels?.[String(doc.job_title)] ?? doc.job_title}</div>
      <hr className="my-2 border-line" />
      <div className="flex justify-between"><span>Gross salary</span><b>{n(doc.gross_salary)}</b></div>
      <div className="flex justify-between"><span>Net salary</span><b>{recompute ? '≈ ' : ''}{n(net)}</b></div>
      <div className="mt-2 text-xs text-ink-3">Issued on {doc.issue_date}</div>
      {tricks.includes('ai_photo') && (
        <div className="absolute bottom-3 right-3 flex h-14 w-14 rotate-[-12deg] items-center justify-center rounded-full border-2 border-info text-[9px] font-bold text-info">
          AI<br />STAMP
        </div>
      )}
      {tricks.includes('hide_injection') && <div className="text-[9px] text-[#EEF0F2]">hidden text for the AI</div>}
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
      setError(e instanceof Error ? e.message : 'Could not submit')
      setBusy(false)
    }
  }

  return (
    <ArenaShell>
      <h2 className="text-2xl font-semibold">{mission.title}</h2>
      <p className="mt-1 text-night-mute">{mission.brief}</p>

      <div className="mt-4"><PayslipPreview doc={doc} tricks={tricks} jobLabels={mission.editable.job_title?.option_labels} /></div>

      <h3 className="mt-8 text-lg font-semibold">Edit the document</h3>
      <div className="mt-2 space-y-4">
        {Object.entries(mission.editable).map(([key, spec]) => {
          const disabled = key === 'net_salary' && recompute
          const cls = 'mt-1 h-14 w-full rounded-md border border-night-line bg-night-2 px-4 text-lg outline-none focus:border-brand disabled:opacity-40'
          return (
            <label key={key} className="block">
              <span className="text-base text-night-mute">{spec.label}{disabled && ' — calculated from gross'}</span>
              {spec.type === 'select' ? (
                <select className={cls} value={String(doc[key])} onChange={(e) => set(key, e.target.value)}>
                  {spec.options?.map((o) => <option key={o} value={o}>{spec.option_labels?.[o] ?? o}</option>)}
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

      <h3 className="mt-8 text-lg font-semibold">Tricks</h3>
      <div className="mt-2 space-y-2">
        {Object.entries(mission.tricks).map(([key, label]) => {
          const on = tricks.includes(key)
          return (
            <button key={key} type="button" onClick={() => toggle(key)} aria-pressed={on}
              className={cn('flex min-h-14 w-full items-center gap-3 rounded-md border px-4 py-3 text-left text-base',
                on ? 'border-brand bg-brand/10' : 'border-night-line bg-night-2')}>
              <span className={cn('grid h-6 w-6 shrink-0 place-items-center rounded-sm border', on ? 'border-brand bg-brand text-ink' : 'border-night-mute')}>
                {on && <Check className="h-4 w-4" aria-hidden />}
              </span>{label}
            </button>
          )
        })}
      </div>

      <div className="sticky bottom-20 mt-8 space-y-2 bg-night/95 py-3 backdrop-blur">
        <p className={cn('text-center text-base', targetMet ? 'text-night-ok' : 'text-brand')}>
          {targetMet ? 'Target reached' : `Target: net of at least ${lei(target.min)}`}
        </p>
        {error && <p className="text-center text-night-danger">{error}</p>}
        <button type="button" onClick={send} disabled={busy}
          className="flex h-16 w-full items-center justify-center gap-2 rounded-md bg-brand text-xl font-bold text-ink active:scale-[0.99] disabled:opacity-60">
          {busy ? 'The agents are checking…' : <><Send className="h-5 w-5" aria-hidden /> Submit the fake</>}
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
  if (missions.isLoading) return <ArenaShell><p className="text-night-mute">Loading the mission.</p></ArenaShell>
  if (!mission) return <ArenaShell><p className="text-night-danger">That mission does not exist. Pick another from the list.</p></ArenaShell>
  return <Forge key={mission.id} mission={mission} />
}
