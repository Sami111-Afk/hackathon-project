import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { AppNav } from '@/components/AppNav'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getStats, listCases, type CaseSummary, type DashboardStats } from '@/lib/api'
import { isMock } from '@/lib/config'
import { riskLevel } from '@/lib/labels'
import { mockCases, mockStats } from '@/lib/mockDashboard'
import type { CaseStatus } from '@/lib/types'

// Culori de stare (fixe, din ghidul de grafice) — mereu împreună cu iconiță + etichetă.
const C = { good: '#0ca30c', warning: '#fab219', critical: '#d03b3b', manual: '#94a3b8', orb: '#2a78d6' }
const SURFACE = '#ffffff'
const LEGEND_ORDER = ['clear', 'review', 'escalate']

const STATUS_LABEL: Record<CaseStatus, string> = {
  received: 'primit', processing: 'în lucru', awaiting_review: 'de revizuit', cleared: 'aprobat',
  rejected: 'respins', escalated: 'investigație', error: 'eroare',
}

const ron = (n: number) => `${Math.round(n).toLocaleString('ro-RO')} lei`
const num = (n: number) => n.toLocaleString('ro-RO')

function useDashboard() {
  const mock = isMock()
  const cases = useQuery({
    queryKey: ['cases', mock],
    queryFn: () => (mock ? Promise.resolve(mockCases()) : listCases()),
    refetchInterval: mock ? false : 5000, // pe scenă cifrele cresc live
  })
  const stats = useQuery<DashboardStats>({
    queryKey: ['stats', mock],
    queryFn: () => (mock ? Promise.resolve(mockStats(mockCases())) : getStats()),
    refetchInterval: mock ? false : 5000,
  })
  return { cases, stats, mock }
}

function Kpi({ icon, label, value, sub }: { icon: string; label: string; value: string; sub?: string }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="text-base text-slate-600">{icon} {label}</div>
        <div className="mt-1 text-5xl font-bold tabular-nums tracking-tight text-slate-900">{value}</div>
        {sub && <div className="mt-2 text-base text-slate-600">{sub}</div>}
      </CardContent>
    </Card>
  )
}

/** Dosare pe zi, pe rezultat (ultimele 21 de zile). */
function perDay(cases: CaseSummary[]) {
  const days: { day: string; clear: number; review: number; escalate: number }[] = []
  const idx = new Map<string, number>()
  for (let i = 20; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400000)
    const key = d.toISOString().slice(0, 10)
    idx.set(key, days.length)
    days.push({ day: d.toLocaleDateString('ro-RO', { day: 'numeric', month: 'short' }), clear: 0, review: 0, escalate: 0 })
  }
  for (const c of cases) {
    const i = idx.get(c.created_at.slice(0, 10))
    if (i === undefined || !c.recommendation) continue
    days[i][c.recommendation]++
  }
  return days
}

export function DashboardPage() {
  const { cases, stats, mock } = useDashboard()
  const s = stats.data
  const list = cases.data ?? []

  if (stats.isError || cases.isError) {
    return (
      <div className="min-h-screen bg-slate-50">
        <AppNav />
        <p className="p-8 text-xl text-red-700">Cifrele nu au putut fi încărcate. Verifică backend-ul sau deschide cu <code>?mock=1</code>.</p>
      </div>
    )
  }

  const a = s?.assumptions
  const manualH = s && a ? (s.cases_processed * a.manual_minutes_per_case) / 60 : 0
  const orbH = s && a ? (s.cases_processed * a.review_minutes_per_case) / 60 : 0
  const timeData = [
    { name: 'Verificare manuală', hours: Math.round(manualH), fill: C.manual },
    { name: 'Cu ORB (doar revizuire)', hours: Math.round(orbH * 10) / 10, fill: C.orb },
  ]

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <AppNav />
      <main className="space-y-6 p-4 md:p-6">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <span className="text-base text-slate-500">{mock ? 'date de demo' : 'se actualizează la 5 secunde'}</span>
        </div>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Kpi icon="📁" label="Dosare procesate" value={s ? num(s.cases_processed) : '—'}
               sub={s ? `cost AI total: $${s.ai_cost_usd.toFixed(2)}` : undefined} />
          <Kpi icon="⏱️" label="Timp economisit" value={s ? `${num(s.hours_saved)} ore` : '—'}
               sub={s ? `≈ ${ron(s.money_saved_ron)} cost de personal` : undefined} />
          <Kpi icon="⛔" label="Fraude oprite" value={s ? num(s.frauds_stopped) : '—'}
               sub={s ? `${ron(s.amount_stopped_ron)} credite blocate` : undefined} />
          <Kpi icon="🛡️" label="Date personale protejate" value={s ? num(s.pii_values_protected) : '—'}
               sub={s ? `${s.external_calls_with_pii === 0 ? '✅' : '⚠️'} ${s.external_calls_with_pii} trimise către AI-ul din cloud` : undefined} />
        </section>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Ore de muncă pentru {s ? num(s.cases_processed) : '…'} dosare</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={timeData} layout="vertical" margin={{ left: 8, right: 64 }}>
                    <XAxis type="number" hide />
                    <YAxis type="category" dataKey="name" width={190} tickLine={false} axisLine={false}
                           tick={{ fill: '#334155', fontSize: 16 }} />
                    <Tooltip cursor={{ fill: 'rgba(15,23,42,0.04)' }} formatter={(v) => [`${Number(v).toLocaleString('ro-RO')} ore`, 'Timp']} />
                    <Bar dataKey="hours" radius={[0, 4, 4, 0]} barSize={44} isAnimationActive={false}>
                      <LabelList dataKey="hours" position="right" formatter={(v) => `${Number(v).toLocaleString('ro-RO')} h`}
                                 style={{ fill: '#0f172a', fontSize: 18, fontWeight: 600 }} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              {a && (
                <p className="text-sm text-slate-500">
                  Presupuneri configurabile: {a.manual_minutes_per_case} min manual / dosar, {a.review_minutes_per_case} min
                  revizuire cu ORB, {a.cost_per_hour_ron} lei / oră. De confirmat cu mentorii Raiffeisen.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-xl">Dosare pe zi, după recomandarea ORB</CardTitle></CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={perDay(list)} margin={{ left: -16, right: 8 }}>
                    <CartesianGrid vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="day" tickLine={false} axisLine={{ stroke: '#cbd5e1' }} tick={{ fill: '#475569', fontSize: 13 }}
                           interval="preserveStartEnd" minTickGap={24} />
                    <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: '#475569', fontSize: 13 }} />
                    <Tooltip cursor={{ fill: 'rgba(15,23,42,0.04)' }} />
                    <Legend wrapperStyle={{ fontSize: 15 }} itemSorter={(i) => LEGEND_ORDER.indexOf(String(i.dataKey))}
                            formatter={(v) => <span style={{ color: '#334155' }}>{v}</span>} />
                    <Bar dataKey="clear" name="✅ Aprobat automat" stackId="d" fill={C.good} stroke={SURFACE} strokeWidth={2} isAnimationActive={false} />
                    <Bar dataKey="review" name="⚠️ Verificare manuală" stackId="d" fill={C.warning} stroke={SURFACE} strokeWidth={2} isAnimationActive={false} />
                    <Bar dataKey="escalate" name="⛔ Investigație" stackId="d" fill={C.critical} stroke={SURFACE} strokeWidth={2}
                         radius={[4, 4, 0, 0]} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </section>

        <Card>
          <CardHeader><CardTitle className="text-xl">Dosare recente</CardTitle></CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-base">
              <thead className="border-b text-sm text-slate-500">
                <tr><th className="py-2">Dosar</th><th>Data</th><th>Suma</th><th>Risc</th><th>Stare</th></tr>
              </thead>
              <tbody>
                {list.slice(0, 10).map((c) => {
                  const lvl = c.risk != null ? riskLevel(c.risk) : null
                  const openable = !mock || c.id === 'case_maria'
                  return (
                    <tr key={c.id} className="border-b last:border-0">
                      <td className="py-2 font-mono text-sm">
                        {openable ? <Link to={`/cases/${c.id}`} className="text-blue-700 underline">{c.id}</Link> : c.id}
                      </td>
                      <td>{new Date(c.created_at).toLocaleDateString('ro-RO')}</td>
                      <td className="tabular-nums">{c.requested_amount_ron ? ron(c.requested_amount_ron) : '—'}</td>
                      <td className={lvl?.cls}>{lvl ? `${lvl.icon} ${Math.round(c.risk! * 100)}` : '…'}</td>
                      <td>{STATUS_LABEL[c.status]}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
