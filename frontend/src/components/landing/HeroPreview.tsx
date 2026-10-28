import mariaCase from '@shared/fixtures/maria_case.json'
import { Check } from 'lucide-react'
import { AGENT_INFO, RECOMMENDATION_LABEL, VERDICT_LABEL, riskLevel } from '@/lib/labels'
import type { AgentName, Verdict } from '@/lib/types'
import { cn } from '@/lib/utils'

// Ce a găsit fiecare agent în dosarul Mariei (dosarul demo, fictiv); verdictul vine din fixture, ca în aplicație.
const FOUND: [AgentName, string][] = [
  ['paznic', 'Personal data hidden before any AI'],
  ['functionar', '3 documents read'],
  ['verificator', 'Net pay does not follow the tax math'],
  ['detector', 'The bank statement was edited'],
  ['detectiv', 'Phone number shared with 5 other identities'],
]

/** Bucata de produs din hero: aceleași etichete și același verdict ca pagina reală a dosarului. */
export function HeroPreview() {
  const verdict = mariaCase.verdict as Verdict
  const lvl = riskLevel(verdict.risk)
  const Icon = lvl.icon
  return (
    <figure className="relative mx-auto w-full max-w-md">
      <div className="absolute -inset-6 -z-10 rounded-[2rem] bg-brand/10 blur-2xl" aria-hidden />
      <div className="overflow-hidden rounded-2xl bg-surface text-ink shadow-2xl ring-1 ring-black/5">
        <div className="flex items-center justify-between gap-3 border-b border-line px-5 py-3.5">
          <div>
            <div className="text-sm font-semibold">Loan application, {mariaCase.requested_amount_ron.toLocaleString('en-GB')} lei</div>
            <div className="text-xs text-ink-3">ID card · payslip · bank statement</div>
          </div>
          <span className="rounded-full bg-canvas px-2.5 py-1 text-xs font-medium text-ink-2">Demo</span>
        </div>
        <ul className="divide-y divide-line">
          {FOUND.map(([agent, text]) => {
            const A = AGENT_INFO[agent]
            return (
              <li key={agent} className="flex items-center gap-3 px-5 py-2.5 text-sm">
                <A.icon className="h-4 w-4 shrink-0 text-ink-2" aria-hidden />
                <span className="w-20 shrink-0 font-semibold">{A.label}</span>
                <span className="min-w-0 flex-1 truncate text-ink-2">{text}</span>
                <Check className="h-4 w-4 shrink-0 text-ok" aria-label="done" />
              </li>
            )
          })}
        </ul>
        <div className="relative border-t border-line px-5 pb-5 pt-4">
          <span className={cn('absolute inset-y-0 left-0 w-1.5', lvl.bar)} aria-hidden />
          <div className={cn('flex items-center gap-2 font-condensed text-3xl font-bold', lvl.text)}>
            <Icon className="h-7 w-7" aria-hidden /> {lvl.label}
          </div>
          <div className="mt-1 text-sm text-ink-2">{VERDICT_LABEL[verdict.label]} · recommended: {RECOMMENDATION_LABEL[verdict.recommendation]}</div>
          <div className="mt-3 text-xs text-ink-3">The analyst sees every piece of evidence and makes the decision.</div>
        </div>
      </div>
      <figcaption className="sr-only">An example: the ORB agents checking Maria Ionescu's (fictional) loan application.</figcaption>
    </figure>
  )
}
