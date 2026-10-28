import { Loader2 } from 'lucide-react'
import { RECOMMENDATION_LABEL, VERDICT_LABEL, riskLevel } from '@/lib/labels'
import type { ScoreItem, Verdict } from '@/lib/types'
import { cn } from '@/lib/utils'

/** Elementul principal al paginii: scorul mare, ce înseamnă și ce recomandă. */
export function VerdictCard({ verdict }: { verdict: Verdict | null }) {
  if (!verdict) {
    return (
      <div className="flex items-center gap-3 px-6 py-8 text-ink-2">
        <Loader2 className="h-5 w-5 animate-spin" aria-hidden /> The agents are still analyzing the application.
      </div>
    )
  }
  const lvl = riskLevel(verdict.risk)
  const Icon = lvl.icon
  // 99,8 nu se rotunjește la 100: scorul nu e o certitudine
  const pct = verdict.risk * 100
  const score = pct >= 99 && pct < 100 ? (Math.floor(pct * 10) / 10).toLocaleString('en-GB') : Math.round(pct)
  const items = verdict.breakdown ?? []
  const critical = items.filter((i) => i.severity === 'critical').length
  // fundalul antetului urmează nivelul: roșu pal, chihlimbar pal sau verde pal
  const tint = lvl.text === 'text-danger' ? 'bg-danger-bg' : lvl.text === 'text-warn' ? 'bg-warn-bg' : 'bg-ok-bg'
  return (
    <div className="relative">
      <span className={cn('absolute inset-y-0 left-0 w-2', lvl.bar)} aria-hidden />
      <div className={cn('px-7 pb-5 pt-5', tint)}>
        <div className="flex items-center justify-between gap-4">
          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-2">Risk level</div>
          <div className="text-right font-condensed leading-none tabular-nums text-ink" aria-hidden>
            <span className="text-3xl font-bold">{score}</span><span className="text-base font-semibold text-ink-3"> / 100</span>
          </div>
        </div>
        <div className={cn('mt-2 flex items-center gap-3 font-condensed text-6xl font-bold leading-[0.95] tracking-tight sm:text-7xl', lvl.text)}>
          <Icon className="h-11 w-11 shrink-0" strokeWidth={2.25} aria-hidden /> {lvl.label.replace(/ risk$/i, '')}
        </div>
        <div className={cn('mt-3 text-xl font-semibold', lvl.text)}>{VERDICT_LABEL[verdict.label]}</div>
      </div>
      <div className="px-7 pb-6 pt-4">
        <p className="text-sm text-ink-3 tabular-nums">
          Score {score} / 100 · {items.length} pieces of evidence{critical ? `, ${critical} of them critical` : ''} · a severity score, not a probability
        </p>
        <p className="mt-2 border-l-2 border-ink pl-3 text-base font-medium text-ink">Recommendation: {RECOMMENDATION_LABEL[verdict.recommendation]}.</p>
        <p className="mt-4 border-t border-line pt-4 text-[15px] leading-relaxed text-ink">{verdict.summary}</p>
        {verdict.summary_source === 'llm' && <p className="mt-1 text-xs text-ink-3">Summary written by AI from the evidence only; every figure was checked against the evidence.</p>}
        {verdict.summary_source === 'template_after_check' && <p className="mt-1 text-xs text-warn">The AI summary contained a figure with no evidence behind it and was replaced with the standard one.</p>}
        {verdict.incomplete && <p className="mt-3 text-sm text-warn">Incomplete analysis: an agent did not finish.</p>}
        {items.length > 0 && (
          <details className="mt-4 border-t border-line pt-3 text-sm">
            <summary className="cursor-pointer font-medium text-ink hover:underline">Why this score?</summary>
            <p className="mt-2 text-ink-2">
              The score is not a probability and the AI does not decide it. Each piece of evidence has a weight by severity
              (critical 0.85 · high 0.6 · medium 0.3 · low 0.1; image signals are capped at 0.3), and
              risk = 1 − Π(1 − weight). Many serious findings push the score toward 100; they are not independent, so the score reflects severity, not the chance of fraud.
            </p>
            <table className="mt-2 w-full text-left">
              <thead><tr className="text-xs text-ink-3"><th className="py-1 font-medium">Evidence</th><th className="py-1 text-right font-medium">Weight</th><th className="py-1 text-right font-medium">Cumulative risk</th></tr></thead>
              <tbody>
                {items.reduce<{ rows: { item: ScoreItem; cum: number }[]; keep: number }>((acc, item) => {
                  const keep = acc.keep * (1 - item.weight)
                  acc.rows.push({ item, cum: 1 - keep })
                  return { rows: acc.rows, keep }
                }, { rows: [], keep: 1 }).rows.map(({ item, cum }, i) => (
                  <tr key={i} className="border-t border-line align-top">
                    <td className="py-1.5 pr-2 text-ink">{item.message}{item.hard_override && <span className="ml-1 text-xs font-semibold text-danger">(mandatory escalation)</span>}</td>
                    <td className="py-1.5 text-right tabular-nums text-ink-2">{item.weight.toLocaleString('en-GB')}</td>
                    <td className="py-1.5 text-right tabular-nums text-ink-2">{(cum * 100).toLocaleString('en-GB', { maximumFractionDigits: 1 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        )}
      </div>
    </div>
  )
}
