import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { AGENT_RO, getSubmission, submissionImageUrl, type Submission } from '@/lib/arena'
import { cn } from '@/lib/utils'
import { ArenaShell } from './ArenaShell'

const CHECKERS = ['paznic', 'verificator', 'detector']

export function ArenaResult() {
  const { sid = '' } = useParams()
  const fromForge = useLocation().state as Submission | null
  const q = useQuery({ queryKey: ['arena-sub', sid], queryFn: () => getSubmission(sid), initialData: fromForge ?? undefined })
  const s = q.data
  // mică animație: agenții „verifică” pe rând, apoi apare verdictul (doar imediat după trimitere)
  const [step, setStep] = useState(fromForge ? 0 : CHECKERS.length)
  useEffect(() => {
    if (step >= CHECKERS.length) return
    const t = setTimeout(() => setStep((x) => x + 1), 600)
    return () => clearTimeout(t)
  }, [step])

  if (q.isError) return <ArenaShell><p className="text-red-400">Trimiterea nu mai există.</p></ArenaShell>
  if (!s) return <ArenaShell><p className="text-slate-400">Se încarcă…</p></ArenaShell>
  const done = step >= CHECKERS.length

  return (
    <ArenaShell>
      <div className="grid grid-cols-3 gap-2">
        {CHECKERS.map((a, i) => {
          const checked = i < step
          const caught = checked && s.caught_by.includes(a)
          return (
            <div key={a} className={cn('rounded-xl border-2 p-3 text-center text-sm font-semibold',
              !checked ? 'animate-pulse border-slate-700 text-slate-500'
                : caught ? 'border-red-500 bg-red-500/15 text-red-200' : 'border-emerald-500 bg-emerald-500/10 text-emerald-200')}>
              {AGENT_RO[a]}
              <div className="mt-1 text-xs font-normal">{!checked ? 'verifică…' : caught ? '🚨 te-a prins' : '✔ a trecut'}</div>
            </div>
          )
        })}
      </div>

      {done && (
        <section className="mt-6">
          {s.outcome === 'passed' && (
            <div className="rounded-2xl border-2 border-emerald-400 bg-emerald-400/10 p-6 text-center">
              <div className="text-6xl">🏆</div>
              <div className="mt-2 text-3xl font-black">Ai păcălit agenții!</div>
              <div className="mt-1 text-2xl font-bold text-emerald-300">+{s.points} puncte</div>
              <p className="mt-3 text-base text-slate-300">
                Falsul tău a ajuns la echipa de self-learning: agenții vor învăța din el o regulă nouă.
              </p>
            </div>
          )}
          {s.outcome === 'caught' && (
            <div className="rounded-2xl border-2 border-red-500 bg-red-500/10 p-6">
              <div className="text-center text-5xl">🚨</div>
              <div className="mt-2 text-center text-3xl font-black">Te-au prins!</div>
              <div className="mt-1 text-center text-xl text-red-200">+{s.points} puncte pentru încercare</div>
              <h3 className="mt-4 text-lg font-bold">De ce:</h3>
              <ul className="mt-2 space-y-2">
                {s.reasons.map((r) => <li key={r} className="rounded-lg bg-slate-900 p-3 text-base">• {r}</li>)}
              </ul>
            </div>
          )}
          {s.outcome === 'invalid' && (
            <div className="rounded-2xl border-2 border-amber-400 bg-amber-400/10 p-6 text-center">
              <div className="text-5xl">🤔</div>
              <div className="mt-2 text-2xl font-black">Fals invalid</div>
              <p className="mt-2 text-base text-slate-300">
                {s.target_met ? 'Nu ai modificat nimic față de șablon.' : 'Documentul nu atinge ținta misiunii (venitul cerut).'}
              </p>
            </div>
          )}
          {s.duplicate && <p className="mt-3 text-center text-sm text-slate-400">Cineva a încercat deja exact același fals: fără puncte.</p>}

          <img src={submissionImageUrl(s.id)} alt="Falsul tău, așa cum l-au văzut agenții"
               className="mt-6 w-full rounded-lg border border-slate-700" />

          <div className="mt-6 grid grid-cols-2 gap-3">
            <Link to={`/arena/m/${s.mission_id}`} className="flex h-14 items-center justify-center rounded-2xl bg-amber-400 text-lg font-bold text-slate-950">
              🔁 Mai încearcă
            </Link>
            <Link to="/arena/top" className="flex h-14 items-center justify-center rounded-2xl border border-slate-600 text-lg font-bold">
              🏆 Clasament
            </Link>
          </div>
        </section>
      )}
    </ArenaShell>
  )
}
