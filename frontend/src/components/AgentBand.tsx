import { Check, Loader2, X } from 'lucide-react'
import type { AgentLane } from '@/lib/caseReducer'
import { AGENT_INFO } from '@/lib/labels'
import { AGENTS, type AgentName } from '@/lib/types'
import { cn } from '@/lib/utils'

/** Fluxul agenților: o secvență reală (Paznic → … → Compliance), deci pași numerotați, legați, nu carduri. */
export function AgentBand({ agents }: { agents: Record<AgentName, AgentLane> }) {
  const finished = AGENTS.filter((n) => agents[n].status === 'done').length
  const active = AGENTS.find((n) => agents[n].status === 'running')
  return (
    <div className="overflow-hidden rounded-md border border-line bg-surface">
      {/* Antet: câți agenți au terminat, cine lucrează acum; bara de jos crește cu fiecare agent gata */}
      <div className="relative flex flex-wrap items-center justify-between gap-x-6 gap-y-1 border-b border-line px-5 py-3">
        <h2 className="flex items-center gap-2.5 text-sm font-semibold uppercase tracking-[0.12em] text-ink">
          <span className="h-3.5 w-1 bg-brand" aria-hidden />Agents
        </h2>
        <p className="text-sm text-ink-2 tabular-nums" aria-live="polite">
          {active ? <><span className="font-semibold text-ink">{AGENT_INFO[active].label}</span> is working · </> : null}
          {finished} of {AGENTS.length} done
        </p>
        <span className="absolute inset-x-0 bottom-0 h-0.5 bg-canvas" aria-hidden>
          <span className="block h-full bg-ink transition-[width] duration-500 ease-out" style={{ width: `${(finished / AGENTS.length) * 100}%` }} />
        </span>
      </div>
      <ol className="grid grid-cols-2 gap-px bg-line md:grid-cols-3 xl:grid-cols-6">
        {AGENTS.map((name, i) => {
          const lane = agents[name]
          const info = AGENT_INFO[name]
          const Icon = info.icon
          const risk = lane.result?.risk
          const running = lane.status === 'running'
          const done = lane.status === 'done'
          const failed = lane.status === 'error' || lane.status === 'skipped'
          const waiting = !running && !done && !failed
          return (
            <li key={name} className={cn('relative flex flex-col gap-3 p-4 transition-colors duration-300',
              running ? 'agent-start bg-[#FFFBDB]' : 'bg-surface')}>
              {(running || failed) && <span className={cn('absolute inset-x-0 top-0 h-1', running ? 'bg-brand' : 'bg-danger')} aria-hidden />}
              <div className="flex items-start gap-3">
                <span className={cn('grid h-9 w-9 shrink-0 place-items-center rounded-full border transition-colors',
                  done ? 'border-ink bg-ink text-white' : running ? 'border-ink bg-brand text-ink' : failed ? 'border-danger text-danger' : 'border-line text-ink-3')}>
                  {running ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                    : done ? <Check className="h-4 w-4" aria-hidden />
                    : failed ? <X className="h-4 w-4" aria-hidden />
                    : <Icon className="h-4 w-4" aria-hidden />}
                </span>
                <div className="min-w-0">
                  <div className="font-condensed text-xs font-semibold tabular-nums text-ink-3">{String(i + 1).padStart(2, '0')}</div>
                  <div className={cn('font-semibold leading-tight', waiting ? 'text-ink-2' : 'text-ink')}>{info.label}</div>
                  <div className="text-sm leading-snug text-ink-3">{info.role}</div>
                </div>
              </div>
              <p className={cn('min-h-[3.75rem] text-[15px] leading-snug', lane.message ? 'text-ink-2' : 'text-ink-3')}>
                {lane.message || (running ? 'Working…' : failed ? 'Did not finish' : 'Waiting')}
              </p>
              {risk != null && (
                <div className="flex items-center gap-2">
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-canvas">
                    <div className={cn('h-full', risk >= 0.5 ? 'bg-danger' : risk >= 0.25 ? 'bg-warn' : 'bg-ok')}
                         style={{ width: `${Math.round(risk * 100)}%` }} />
                  </div>
                  <span className="w-16 text-right text-sm font-semibold tabular-nums text-ink">risk {Math.round(risk * 100)}</span>
                </div>
              )}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
