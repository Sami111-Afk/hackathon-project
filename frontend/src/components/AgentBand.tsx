import { Check, Loader2, X } from 'lucide-react'
import type { AgentLane } from '@/lib/caseReducer'
import { AGENT_INFO } from '@/lib/labels'
import { AGENTS, type AgentName } from '@/lib/types'
import { cn } from '@/lib/utils'

/** Fluxul agenților: o secvență reală (Paznic → … → Compliance), deci pași legați, nu carduri. */
export function AgentBand({ agents }: { agents: Record<AgentName, AgentLane> }) {
  return (
    <ol className="grid grid-cols-2 gap-px overflow-hidden rounded-md border border-line bg-line md:grid-cols-3 xl:grid-cols-6">
      {AGENTS.map((name) => {
        const lane = agents[name]
        const info = AGENT_INFO[name]
        const Icon = info.icon
        const risk = lane.result?.risk
        const running = lane.status === 'running'
        const done = lane.status === 'done'
        const failed = lane.status === 'error' || lane.status === 'skipped'
        return (
          <li key={name} className={cn('relative flex flex-col gap-3 bg-surface p-4', running && 'bg-[#F5F8FF]')}>
            {running && <span className="absolute inset-x-0 top-0 h-0.5 bg-info" aria-hidden />}
            <div className="flex items-center gap-3">
              <span className={cn('grid h-9 w-9 shrink-0 place-items-center rounded-full border',
                done ? 'border-ink bg-ink text-white' : running ? 'border-info text-info' : failed ? 'border-danger text-danger' : 'border-line text-ink-3')}>
                {running ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                  : done ? <Check className="h-4 w-4" aria-hidden />
                  : failed ? <X className="h-4 w-4" aria-hidden />
                  : <Icon className="h-4 w-4" aria-hidden />}
              </span>
              <div className="min-w-0">
                <div className="font-semibold text-ink">{info.label}</div>
                <div className="truncate text-sm text-ink-3">{info.role}</div>
              </div>
            </div>
            <p className={cn('min-h-[3.75rem] text-[15px] leading-snug', lane.message ? 'text-ink-2' : 'text-ink-3')}>
              {lane.message || (running ? 'Lucrează…' : failed ? 'Nu a terminat' : 'În așteptare')}
            </p>
            {risk != null && (
              <div className="flex items-center gap-2">
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-canvas">
                  <div className={cn('h-full', risk >= 0.5 ? 'bg-danger' : risk >= 0.25 ? 'bg-warn' : 'bg-ok')}
                       style={{ width: `${Math.round(risk * 100)}%` }} />
                </div>
                <span className="w-16 text-right text-sm font-semibold tabular-nums text-ink">risc {Math.round(risk * 100)}</span>
              </div>
            )}
          </li>
        )
      })}
    </ol>
  )
}
