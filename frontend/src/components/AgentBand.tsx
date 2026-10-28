import { cn } from '@/lib/utils'
import { AGENT_INFO, riskLevel } from '@/lib/labels'
import type { AgentLane } from '@/lib/caseReducer'
import { AGENTS, type AgentName } from '@/lib/types'

const STATUS: Record<AgentLane['status'], { label: string; cls: string }> = {
  pending: { label: 'în așteptare', cls: 'border-dashed border-slate-300 bg-white text-slate-400' },
  running: { label: 'lucrează…', cls: 'border-blue-500 bg-blue-50 ring-4 ring-blue-200 animate-pulse' },
  done: { label: 'gata', cls: 'border-slate-300 bg-white' },
  error: { label: 'eroare', cls: 'border-red-600 bg-red-50' },
  skipped: { label: 'sărit', cls: 'border-slate-200 bg-slate-50 text-slate-400' },
}

/** Banda „biroului”: fiecare agent cu starea lui live. */
export function AgentBand({ agents }: { agents: Record<AgentName, AgentLane> }) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
      {AGENTS.map((name) => {
        const lane = agents[name]
        const info = AGENT_INFO[name]
        const st = STATUS[lane.status]
        const risk = lane.result?.risk
        return (
          <div key={name} className={cn('rounded-xl border-2 p-3', st.cls)}>
            <div className="flex items-center gap-2 text-lg font-semibold">
              <span className="text-2xl" aria-hidden>{info.icon}</span>
              {info.label}
            </div>
            <div className="text-sm text-slate-500">{info.role}</div>
            <div className="mt-2 min-h-10 text-sm text-slate-800">
              {lane.message || <span className="text-slate-400">{st.label}</span>}
            </div>
            {risk != null && (
              <div className={cn('mt-1 text-sm font-semibold', riskLevel(risk).cls)}>
                {riskLevel(risk).icon} risc {Math.round(risk * 100)}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
