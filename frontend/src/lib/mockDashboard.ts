// Date de demo pentru Dashboard în modul mock — aceeași formă și aceleași formule ca backend-ul
// (backend/app/api/system.py, /api/admin/seed-demo), ca să nu „inventăm” altceva pe scenă.
import type { CaseSummary, DashboardStats } from './api'

const DAY = 86400000

function ago(days: number): string {
  return new Date(Date.now() - days * DAY).toISOString()
}

function rand(seed: number) {
  let s = seed
  return () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646
}

export function mockCases(): CaseSummary[] {
  const r = rand(7)
  const out: CaseSummary[] = [
    { id: 'case_maria', status: 'awaiting_review', created_at: ago(0.01), requested_amount_ron: 45000, risk: 0.96, recommendation: 'escalate' },
  ]
  for (let i = 0; i < 5; i++) {
    out.push({ id: `case_ring_${i + 1}`, status: i < 2 ? 'escalated' : 'awaiting_review', created_at: ago(21 - i * 4),
      requested_amount_ron: [30000, 38000, 45000, 52000][i % 4], risk: 0.82 + i * 0.03, recommendation: 'escalate' })
  }
  for (let i = 0; i < 40; i++) {
    const risk = r() < 0.15 ? 0.35 + r() * 0.3 : r() * 0.2
    out.push({ id: `case_ok_${i + 1}`, status: risk >= 0.35 ? 'awaiting_review' : 'cleared', created_at: ago(r() * 20),
      requested_amount_ron: [12000, 18000, 25000, 40000, 60000][Math.floor(r() * 5)],
      risk: Math.round(risk * 100) / 100, recommendation: risk >= 0.35 ? 'review' : 'clear' })
  }
  return out.sort((a, b) => b.created_at.localeCompare(a.created_at))
}

export function mockStats(cases: CaseSummary[]): DashboardStats {
  const assumptions = { manual_minutes_per_case: 20, review_minutes_per_case: 1, cost_per_hour_ron: 60 }
  const done = cases.filter((c) => c.risk != null)
  const fraud = done.filter((c) => c.recommendation === 'escalate' || c.status === 'rejected' || c.status === 'escalated')
  const savedMin = done.length * (assumptions.manual_minutes_per_case - assumptions.review_minutes_per_case)
  return {
    cases_processed: done.length,
    hours_saved: Math.round((savedMin / 60) * 10) / 10,
    money_saved_ron: Math.round((savedMin / 60) * assumptions.cost_per_hour_ron),
    frauds_stopped: fraud.length,
    amount_stopped_ron: fraud.reduce((s, c) => s + (c.requested_amount_ron ?? 0), 0),
    ai_cost_usd: Math.round(done.length * 0.00056 * 10000) / 10000,
    pii_values_protected: done.length * 23,
    external_calls_with_pii: 0,
    assumptions,
  }
}
