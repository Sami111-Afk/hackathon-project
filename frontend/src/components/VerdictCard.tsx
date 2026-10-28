import { Loader2 } from 'lucide-react'
import { RECOMMENDATION_LABEL, VERDICT_LABEL, riskLevel } from '@/lib/labels'
import type { Verdict } from '@/lib/types'
import { cn } from '@/lib/utils'

/** Elementul principal al paginii: scorul mare, ce înseamnă și ce recomandă. */
export function VerdictCard({ verdict }: { verdict: Verdict | null }) {
  if (!verdict) {
    return (
      <div className="flex items-center gap-3 px-6 py-8 text-ink-2">
        <Loader2 className="h-5 w-5 animate-spin" aria-hidden /> Agenții încă analizează dosarul.
      </div>
    )
  }
  const lvl = riskLevel(verdict.risk)
  const Icon = lvl.icon
  const score = Math.round(verdict.risk * 100)
  return (
    <div className="relative px-6 pb-6 pt-5">
      <span className={cn('absolute inset-y-0 left-0 w-1.5', lvl.bar)} aria-hidden />
      <div className="text-sm font-medium text-ink-3">Scor de risc</div>
      <div className="mt-1 flex items-end gap-3">
        <span className={cn('font-condensed text-8xl font-bold leading-[0.85] tabular-nums', lvl.text)}>{score}</span>
        <span className="pb-1 font-condensed text-2xl text-ink-3">/ 100</span>
      </div>
      <div className={cn('mt-3 flex items-center gap-2 text-lg font-semibold', lvl.text)}>
        <Icon className="h-5 w-5" aria-hidden /> {lvl.label}: {VERDICT_LABEL[verdict.label].toLowerCase()}
      </div>
      <p className="mt-1 text-base text-ink-2">Recomandare: {RECOMMENDATION_LABEL[verdict.recommendation]}.</p>
      <p className="mt-4 border-t border-line pt-4 text-[15px] leading-relaxed text-ink">{verdict.summary}</p>
      {verdict.incomplete && <p className="mt-3 text-sm text-warn">Analiză incompletă: un agent nu a terminat.</p>}
    </div>
  )
}
