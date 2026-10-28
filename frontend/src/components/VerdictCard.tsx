import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { RECOMMENDATION_LABEL, VERDICT_LABEL, riskLevel } from '@/lib/labels'
import { cn } from '@/lib/utils'
import type { Verdict } from '@/lib/types'

export function VerdictCard({ verdict }: { verdict: Verdict | null }) {
  if (!verdict) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-xl">⚖️ Verdict</CardTitle></CardHeader>
        <CardContent className="text-slate-500">Agenții încă lucrează…</CardContent>
      </Card>
    )
  }
  const lvl = riskLevel(verdict.risk)
  return (
    <Card className="border-2 border-red-600/40">
      <CardHeader><CardTitle className="text-xl">⚖️ Verdict</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className={cn('flex items-baseline gap-3', lvl.cls)}>
          <span className="text-6xl font-bold tabular-nums">{Math.round(verdict.risk * 100)}</span>
          <span className="text-xl font-semibold">{lvl.icon} {lvl.label}</span>
        </div>
        <div className="text-lg">
          <b>{VERDICT_LABEL[verdict.label]}</b> → recomandare: <b>{RECOMMENDATION_LABEL[verdict.recommendation]}</b>
        </div>
        <p className="text-base text-slate-700">{verdict.summary}</p>
        {verdict.incomplete && <p className="text-sm text-amber-700">⚠️ Analiză incompletă — un agent a eșuat.</p>}
      </CardContent>
    </Card>
  )
}
