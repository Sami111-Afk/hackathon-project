import { Crosshair } from 'lucide-react'
import { AGENT_INFO, SEVERITY } from '@/lib/labels'
import type { AgentName, Finding, Severity } from '@/lib/types'
import { cn } from '@/lib/utils'

const ORDER: Severity[] = ['critical', 'high', 'medium', 'low', 'info']

/** Dovezile, de la cea mai gravă. Cele cu loc pe document se pot arăta pe imagine. */
export function FindingsList({
  items, onSelect, selected,
}: {
  items: { agent: AgentName; finding: Finding }[]
  onSelect?: (f: Finding) => void
  selected?: Finding | null
}) {
  const sorted = [...items]
    .filter(({ finding }) => finding.severity !== 'info')
    .sort((a, b) => ORDER.indexOf(a.finding.severity) - ORDER.indexOf(b.finding.severity))
  if (!sorted.length) return <p className="px-6 py-5 text-ink-3">No evidence yet.</p>
  return (
    <ul className="divide-y divide-line">
      {sorted.map(({ agent, finding }, i) => {
        const sev = SEVERITY[finding.severity]
        const Icon = sev.icon
        const locatable = !!finding.evidence?.bbox
        const active = selected === finding
        return (
          <li key={`${agent}-${finding.code}-${i}`}>
            {/* bara din stânga = gravitatea, citibilă de la distanță (proiector) */}
            <button type="button" disabled={!locatable} onClick={() => onSelect?.(finding)} aria-pressed={locatable ? active : undefined}
              className={cn('relative flex w-full gap-3.5 py-5 pl-7 pr-6 text-left transition-colors', locatable && 'hover:bg-canvas/70',
                active && 'bg-canvas ring-2 ring-inset ring-ink')}>
              <span className={cn('absolute inset-y-0 left-0 w-1.5', sev.bar)} aria-hidden />
              <Icon className={cn('mt-0.5 h-5 w-5 shrink-0', sev.text)} aria-hidden />
              <span className="min-w-0 flex-1">
                <span className="block text-base leading-snug text-ink">{finding.message}</span>
                <span className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-ink-3">
                  <span className={cn('rounded-sm px-1.5 py-0.5 text-xs font-bold uppercase tracking-wide', sev.bg, sev.text)}>{sev.label}</span>
                  <span>{AGENT_INFO[agent].label}</span>
                  {locatable && (
                    <span className="flex items-center gap-1 font-medium text-info"><Crosshair className="h-3.5 w-3.5" aria-hidden />Show on document</span>
                  )}
                </span>
              </span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
