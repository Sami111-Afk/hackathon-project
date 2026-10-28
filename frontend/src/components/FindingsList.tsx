import { AGENT_INFO, SEVERITY } from '@/lib/labels'
import { cn } from '@/lib/utils'
import type { AgentName, Finding, Severity } from '@/lib/types'

const ORDER: Severity[] = ['critical', 'high', 'medium', 'low', 'info']

export function FindingsList({
  items, onSelect, selected,
}: {
  items: { agent: AgentName; finding: Finding }[]
  onSelect?: (f: Finding) => void
  selected?: Finding | null
}) {
  const sorted = [...items].sort((a, b) => ORDER.indexOf(a.finding.severity) - ORDER.indexOf(b.finding.severity))
  if (!sorted.length) return <p className="text-slate-500">Încă nimic găsit.</p>
  return (
    <ul className="space-y-2">
      {sorted.map(({ agent, finding }, i) => {
        const sev = SEVERITY[finding.severity]
        const clickable = !!finding.evidence?.bbox
        return (
          <li key={`${agent}-${finding.code}-${i}`}>
            <button
              type="button"
              disabled={!clickable}
              onClick={() => onSelect?.(finding)}
              className={cn(
                'w-full rounded-lg border-l-4 p-3 text-left',
                sev.cls,
                clickable && 'cursor-pointer hover:brightness-95',
                selected === finding && 'ring-2 ring-blue-500',
              )}
            >
              <div className="flex flex-wrap items-center gap-2 text-sm font-semibold">
                <span>{sev.icon} {sev.label}</span>
                <span className="text-slate-500">· {AGENT_INFO[agent].icon} {AGENT_INFO[agent].label}</span>
                {clickable && <span className="text-slate-500">· vezi pe document</span>}
              </div>
              <div className="mt-1 text-base">{finding.message}</div>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
