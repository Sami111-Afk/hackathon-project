import { useQuery } from '@tanstack/react-query'
import { AlertOctagon, Check, CircleHelp, Loader2, RotateCcw, Siren, Trophy } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { getSubmission, submissionImageUrl, type Submission } from '@/lib/arena'
import { AGENT_INFO } from '@/lib/labels'
import type { AgentName } from '@/lib/types'
import { cn } from '@/lib/utils'
import { ArenaShell } from './ArenaShell'

const CHECKERS: AgentName[] = ['paznic', 'verificator', 'detector']

export function ArenaResult() {
  const { sid = '' } = useParams()
  const fromForge = useLocation().state as Submission | null
  const q = useQuery({ queryKey: ['arena-sub', sid], queryFn: () => getSubmission(sid), initialData: fromForge ?? undefined })
  const s = q.data
  // agenții „verifică” pe rând, apoi apare verdictul (doar imediat după trimitere)
  const [step, setStep] = useState(fromForge ? 0 : CHECKERS.length)
  useEffect(() => {
    if (step >= CHECKERS.length) return
    const t = setTimeout(() => setStep((x) => x + 1), 600)
    return () => clearTimeout(t)
  }, [step])

  if (q.isError) return <ArenaShell><p className="text-night-danger">Încercarea nu mai există.</p></ArenaShell>
  if (!s) return <ArenaShell><p className="text-night-mute">Se încarcă rezultatul.</p></ArenaShell>
  const done = step >= CHECKERS.length

  return (
    <ArenaShell>
      <ol className="grid grid-cols-3 gap-2">
        {CHECKERS.map((a, i) => {
          const checked = i < step
          const caught = checked && s.caught_by.includes(a)
          const Icon = AGENT_INFO[a].icon
          return (
            <li key={a} className={cn('rounded-md border p-3 text-center',
              !checked ? 'border-night-line text-night-mute' : caught ? 'border-night-danger bg-night-danger/10' : 'border-night-ok/60 bg-night-ok/10')}>
              <Icon className="mx-auto h-5 w-5" aria-hidden />
              <div className="mt-1 text-sm font-semibold">{AGENT_INFO[a].label}</div>
              <div className={cn('mt-1 flex items-center justify-center gap-1 text-xs', caught ? 'text-night-danger' : checked ? 'text-night-ok' : '')}>
                {!checked ? <><Loader2 className="h-3 w-3 animate-spin" aria-hidden />verifică</>
                  : caught ? <><AlertOctagon className="h-3 w-3" aria-hidden />te-a prins</>
                  : <><Check className="h-3 w-3" aria-hidden />a trecut</>}
              </div>
            </li>
          )
        })}
      </ol>

      {done && (
        <section className="mt-6">
          {s.outcome === 'passed' && (
            <div className="rounded-md border border-night-ok/60 bg-night-ok/10 p-6 text-center">
              <Trophy className="mx-auto h-10 w-10 text-brand" aria-hidden />
              <div className="mt-3 text-3xl font-bold">Ai păcălit agenții</div>
              {s.points > 0 && <div className="mt-1 font-condensed text-3xl font-bold text-brand">+{s.points} puncte</div>}
              <p className="mt-3 text-base text-night-mute">Falsul tău ajunge la echipa de self-learning: agenții vor învăța din el o regulă nouă.</p>
            </div>
          )}
          {s.outcome === 'caught' && (
            <div className="rounded-md border border-night-danger/70 bg-night-danger/10 p-6">
              <div className="flex items-center gap-3">
                <Siren className="h-8 w-8 text-night-danger" aria-hidden />
                <div>
                  <div className="text-3xl font-bold">Te-au prins</div>
                  <div className="text-base text-night-mute">+{s.points} puncte pentru încercare</div>
                </div>
              </div>
              <h3 className="mt-5 text-base font-semibold">Ce i-a dat de gol falsul</h3>
              <ul className="mt-2 divide-y divide-night-line rounded-md border border-night-line">
                {s.reasons.map((r, i) => <li key={`${i}-${r}`} className="px-4 py-3 text-base">{r}</li>)}
              </ul>
            </div>
          )}
          {s.outcome === 'invalid' && (
            <div className="rounded-md border border-brand/60 bg-brand/10 p-6 text-center">
              <CircleHelp className="mx-auto h-9 w-9 text-brand" aria-hidden />
              <div className="mt-2 text-2xl font-bold">Falsul nu e valid</div>
              <p className="mt-2 text-base text-night-mute">
                {s.target_met ? 'Nu ai modificat nimic față de șablon.' : 'Documentul nu atinge venitul cerut de misiune.'}
              </p>
            </div>
          )}
          {s.duplicate && <p className="mt-3 text-center text-sm text-night-mute">Cineva a trimis deja exact același fals, așa că nu primești puncte.</p>}

          <img src={submissionImageUrl(s.id)} alt="Falsul tău, așa cum l-au primit agenții" className="mt-6 w-full rounded-sm border border-night-line" />

          <div className="mt-6 grid grid-cols-2 gap-3">
            <Link to={`/arena/m/${s.mission_id}`} className="flex h-14 items-center justify-center gap-2 rounded-md bg-brand text-lg font-bold text-ink">
              <RotateCcw className="h-5 w-5" aria-hidden /> Încearcă din nou
            </Link>
            <Link to="/arena/top" className="flex h-14 items-center justify-center gap-2 rounded-md border border-night-line text-lg font-semibold">
              <Trophy className="h-5 w-5" aria-hidden /> Clasament
            </Link>
          </div>
        </section>
      )}
    </ArenaShell>
  )
}
