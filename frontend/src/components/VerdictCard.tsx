import { Loader2 } from 'lucide-react'
import { RECOMMENDATION_LABEL, VERDICT_LABEL, riskLevel } from '@/lib/labels'
import type { ScoreItem, Verdict } from '@/lib/types'
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
  // 99,8 nu se rotunjește la 100: scorul nu e o certitudine
  const pct = verdict.risk * 100
  const score = pct >= 99 && pct < 100 ? (Math.floor(pct * 10) / 10).toLocaleString('ro-RO') : Math.round(pct)
  const items = verdict.breakdown ?? []
  const critical = items.filter((i) => i.severity === 'critical').length
  return (
    <div className="relative px-6 pb-6 pt-5">
      <span className={cn('absolute inset-y-0 left-0 w-1.5', lvl.bar)} aria-hidden />
      <div className="text-sm font-medium text-ink-3">Nivel de risc</div>
      <div className={cn('mt-1 flex items-center gap-3 font-condensed text-5xl font-bold leading-none', lvl.text)}>
        <Icon className="h-9 w-9 shrink-0" aria-hidden /> {lvl.label.replace(/^Risc /, '')}
      </div>
      <div className={cn('mt-3 text-lg font-semibold', lvl.text)}>{VERDICT_LABEL[verdict.label]}</div>
      <p className="mt-1 text-sm text-ink-3 tabular-nums">
        Scor {score} / 100 · {items.length} dovezi{critical ? `, din care ${critical} critice` : ''} · un scor de gravitate, nu o probabilitate
      </p>
      <p className="mt-1 text-base text-ink-2">Recomandare: {RECOMMENDATION_LABEL[verdict.recommendation]}.</p>
      <p className="mt-4 border-t border-line pt-4 text-[15px] leading-relaxed text-ink">{verdict.summary}</p>
      {verdict.summary_source === 'llm' && <p className="mt-1 text-xs text-ink-3">Rezumat scris de AI doar din dovezi; fiecare cifră a fost verificată în dovezi.</p>}
      {verdict.summary_source === 'template_after_check' && <p className="mt-1 text-xs text-warn">Rezumatul AI conținea o cifră fără dovadă și a fost înlocuit cu cel standard.</p>}
      {verdict.incomplete && <p className="mt-3 text-sm text-warn">Analiză incompletă: un agent nu a terminat.</p>}
      {items.length > 0 && (
        <details className="mt-4 border-t border-line pt-3 text-sm">
          <summary className="cursor-pointer font-medium text-ink hover:underline">De ce acest scor?</summary>
          <p className="mt-2 text-ink-2">
            Scorul nu e o probabilitate și nu îl decide AI-ul. Fiecare dovadă are o pondere după gravitate
            (critic 0,85 · ridicat 0,6 · mediu 0,3 · scăzut 0,1; semnalele de imagine sunt plafonate la 0,3), iar
            risc = 1 − Π(1 − pondere). Multe dovezi grave împing scorul spre 100; ele nu sunt independente, de aceea scorul arată gravitatea, nu șansa de fraudă.
          </p>
          <table className="mt-2 w-full text-left">
            <thead><tr className="text-xs text-ink-3"><th className="py-1 font-medium">Dovadă</th><th className="py-1 text-right font-medium">Pondere</th><th className="py-1 text-right font-medium">Risc cumulat</th></tr></thead>
            <tbody>
              {items.reduce<{ rows: { item: ScoreItem; cum: number }[]; keep: number }>((acc, item) => {
                const keep = acc.keep * (1 - item.weight)
                acc.rows.push({ item, cum: 1 - keep })
                return { rows: acc.rows, keep }
              }, { rows: [], keep: 1 }).rows.map(({ item, cum }, i) => (
                <tr key={i} className="border-t border-line align-top">
                  <td className="py-1.5 pr-2 text-ink">{item.message}{item.hard_override && <span className="ml-1 text-xs font-semibold text-danger">(escaladare obligatorie)</span>}</td>
                  <td className="py-1.5 text-right tabular-nums text-ink-2">{item.weight.toLocaleString('ro-RO')}</td>
                  <td className="py-1.5 text-right tabular-nums text-ink-2">{(cum * 100).toLocaleString('ro-RO', { maximumFractionDigits: 1 })}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
    </div>
  )
}
