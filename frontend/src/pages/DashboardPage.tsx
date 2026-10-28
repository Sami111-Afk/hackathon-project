import { useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { AppNav } from '@/components/AppNav'
import { NewCaseForm } from '@/components/NewCaseForm'
import { Panel } from '@/components/Panel'
import { getStats, listCases, type CaseSummary, type DashboardStats } from '@/lib/api'
import { isMock } from '@/lib/config'
import { riskLevel } from '@/lib/labels'
import { mockCases, mockStats } from '@/lib/mockDashboard'
import type { CaseStatus } from '@/lib/types'

// Culori de stare (fixe, din ghidul de grafice) — mereu împreună cu iconiță + etichetă.
const C = { good: '#0ca30c', warning: '#fab219', critical: '#d03b3b', manual: '#98A2B3', orb: '#1F2328' }
const SURFACE = '#ffffff'
const LEGEND_ORDER = ['clear', 'review', 'escalate']

const STATUS_LABEL: Record<CaseStatus, string> = {
  received: 'Received', processing: 'In analysis', awaiting_review: 'Awaiting decision', cleared: 'Approved',
  rejected: 'Rejected', escalated: 'Under investigation', error: 'Error',
}

/** Cum citește un analist cererea: suma, nu codul intern (tipul creditului nu e cunoscut). */
function describe(c: CaseSummary): string {
  const amount = c.requested_amount_ron ? `${Math.round(c.requested_amount_ron).toLocaleString('ro-RO')} lei` : 'unknown amount'
  return `Loan application for ${amount}`
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

function Kpi({ label, value, unit, note }: { label: string; value: string; unit?: string; note?: string }) {
  return (
    <div className="bg-surface px-6 py-5">
      <div className="text-[15px] font-medium text-ink-2">{label}</div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="font-condensed text-6xl font-bold leading-none tabular-nums text-ink">{value}</span>
        {unit && <span className="text-xl font-medium text-ink-2">{unit}</span>}
      </div>
      {note && <div className="mt-2 text-[15px] text-ink-3">{note}</div>}
    </div>
  )
}

/** Ziua în ora locală (aceeași regulă pentru grafic și tabel). */
function localDay(iso: string | Date): string {
  const d = typeof iso === 'string' ? new Date(iso) : iso
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Dosare pe zi, pe rezultat (ultimele 21 de zile). */
function perDay(cases: CaseSummary[]) {
  const days: { day: string; clear: number; review: number; escalate: number }[] = []
  const idx = new Map<string, number>()
  for (let i = 20; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400000)
    const key = localDay(d)
    idx.set(key, days.length)
    days.push({ day: d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }), clear: 0, review: 0, escalate: 0 })
  }
  for (const c of cases) {
    const i = idx.get(localDay(c.created_at))
    if (i === undefined || !c.recommendation) continue
    days[i][c.recommendation]++
  }
  return days
}

export function DashboardPage() {
  const { cases, stats, mock } = useDashboard()
  const [creating, setCreating] = useState(false)
  const s = stats.data
  const list = [...(cases.data ?? [])].sort((x, y) => Date.parse(y.created_at) - Date.parse(x.created_at))

  if (stats.isError || cases.isError) {
    return (
      <div className="min-h-screen bg-canvas">
        <AppNav />
        <p className="p-8 text-lg text-danger">The figures could not be loaded: the server is not responding. Check the backend or open the demo with ?mock=1.</p>
      </div>
    )
  }

  const a = s?.assumptions
  const manualH = s && a ? (s.cases_processed * a.manual_minutes_per_case) / 60 : 0
  const orbH = s && a ? (s.cases_processed * a.review_minutes_per_case) / 60 : 0
  const timeData = [
    { name: 'Manual review', hours: Math.round(manualH), fill: C.manual },
    { name: 'With ORB, review only', hours: Math.round(orbH * 10) / 10, fill: C.orb },
  ]

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <AppNav />
      <div className="border-b border-line bg-surface px-4 py-5 md:px-8">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div className="max-w-3xl">
            <h1 className="text-3xl font-semibold tracking-tight">Overview</h1>
            <p className="mt-1 text-base leading-relaxed text-ink-2">
              For the credit analyst: ORB checks the documents of every loan application and flags what does not add up.
              The analyst no longer reads the file line by line, but reviews the evidence and decides, in about a minute instead of twenty.
            </p>
          </div>
          <div className="flex items-center gap-4">
            {!mock && <span className="flex items-center gap-2 text-sm text-ink-2"><span className="h-2 w-2 rounded-full bg-ok" />Updates every 5 seconds</span>}
            {!mock && !creating && (
              <button type="button" onClick={() => setCreating(true)}
                className="flex h-11 items-center gap-2 rounded-sm bg-ink px-4 text-[15px] font-semibold text-white hover:bg-black">
                <Plus className="h-4 w-4" aria-hidden /> New application
              </button>
            )}
          </div>
        </div>
        {mock && (
          <p className="mt-4 rounded-sm border border-warn bg-warn-bg px-4 py-3 text-base font-semibold text-warn">
            Demo data: the figures on this page are made up and do not come from the backend.
          </p>
        )}
      </div>

      <main className="space-y-6 px-4 py-6 md:px-8">
        {creating && <NewCaseForm onClose={() => setCreating(false)} />}
        <section aria-label="Indicators" className="grid gap-px overflow-hidden rounded-md border border-line bg-line sm:grid-cols-2 xl:grid-cols-4">
          <Kpi label="Applications checked" value={s ? num(s.cases_processed) : '—'}
               note={s ? `AI cost: $${s.ai_cost_usd.toLocaleString('ro-RO', { minimumFractionDigits: 2 })} in total` : undefined} />
          <Kpi label="Working time saved" value={s ? num(s.hours_saved) : '—'} unit="hours"
               note={s ? `Equivalent to ${ron(s.money_saved_ron)} in staff cost` : undefined} />
          <Kpi label="Frauds stopped" value={s ? num(s.frauds_stopped) : '—'}
               note={s ? `${ron(s.amount_stopped_ron)} in blocked loans` : undefined} />
          <Kpi label="Personal data protected" value={s ? num(s.pii_values_protected) : '—'}
               note={s ? (s.external_calls_with_pii === 0 ? 'None sent to the cloud AI' : `${s.external_calls_with_pii} sent to the cloud`) : undefined} />
        </section>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <Panel title={`Working hours for ${s ? num(s.cases_processed) : '…'} applications`}>
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={timeData} layout="vertical" margin={{ left: 8, right: 72 }}>
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" width={220} tickLine={false} axisLine={false}
                         tick={{ fill: '#1F2328', fontSize: 18 }} />
                  <Tooltip cursor={{ fill: 'rgba(31,35,40,0.04)' }} formatter={(v) => [`${Number(v).toLocaleString('ro-RO')} hours`, 'Time']} />
                  <Bar dataKey="hours" radius={[0, 3, 3, 0]} barSize={40} isAnimationActive={false}>
                    <LabelList dataKey="hours" position="right" formatter={(v) => `${Number(v).toLocaleString('ro-RO')} h`}
                               style={{ fill: '#1F2328', fontSize: 20, fontWeight: 600 }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            {a && (
              <p className="mt-2 text-[15px] text-ink-3">
                Assumptions, to be confirmed with Raiffeisen: {a.manual_minutes_per_case} minutes of manual checking per application,
                {' '}{a.review_minutes_per_case} minute of review with ORB, {a.cost_per_hour_ron} lei per hour.
              </p>
            )}
          </Panel>

          <Panel title="Applications per day, by ORB recommendation">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={perDay(list)} margin={{ left: -16, right: 8 }}>
                  <CartesianGrid vertical={false} stroke="#E4E7EC" />
                  <XAxis dataKey="day" tickLine={false} axisLine={{ stroke: '#D5D9DF' }} tick={{ fill: '#4E5764', fontSize: 15 }}
                         interval="preserveStartEnd" minTickGap={32} />
                  <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: '#4E5764', fontSize: 15 }} />
                  <Tooltip cursor={{ fill: 'rgba(31,35,40,0.04)' }} />
                  <Legend wrapperStyle={{ fontSize: 16 }} itemSorter={(i) => LEGEND_ORDER.indexOf(String(i.dataKey))}
                          formatter={(v) => <span style={{ color: '#1F2328' }}>{v}</span>} />
                  <Bar dataKey="clear" name="Auto-approved" stackId="d" fill={C.good} stroke={SURFACE} strokeWidth={2} isAnimationActive={false} />
                  <Bar dataKey="review" name="Manual review" stackId="d" fill={C.warning} stroke={SURFACE} strokeWidth={2} isAnimationActive={false} />
                  <Bar dataKey="escalate" name="Investigation" stackId="d" fill={C.critical} stroke={SURFACE} strokeWidth={2}
                       radius={[3, 3, 0, 0]} isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Panel>
        </section>

        <Panel title="Recent applications" bodyClassName="p-0 overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-base">
            <thead className="bg-canvas/60 text-sm text-ink-2">
              <tr className="border-b border-line">
                <th className="px-6 py-3 font-medium">Application</th><th className="px-4 font-medium">Submitted</th><th className="px-4 font-medium">Risk</th><th className="px-6 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {list.slice(0, 10).map((c) => {
                const lvl = c.risk != null ? riskLevel(c.risk) : null
                const Icon = lvl?.icon
                const openable = !mock || c.id === 'case_maria'
                return (
                  <tr key={c.id} className="border-b border-line last:border-0 hover:bg-canvas/50">
                    <td className="px-6 py-3.5">
                      {openable
                        ? <Link to={`/cases/${c.id}`} className="font-medium text-info hover:underline">{describe(c)}</Link>
                        : <span className="font-medium text-ink">{describe(c)}</span>}
                      <div className="text-sm text-ink-3">Anonymized applicant, case {c.id.replace(/^case_/, '')}</div>
                    </td>
                    <td className="px-4 text-ink-2">{new Date(c.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}</td>
                    <td className="px-4">
                      {lvl && Icon ? (
                        <span className={`flex items-center gap-2 font-semibold tabular-nums ${lvl.text}`}>
                          <Icon className="h-4 w-4" aria-hidden />{Math.round(c.risk! * 100)}
                          <span className="font-normal text-ink-3">{lvl.label.replace(/ risk$/i, '')}</span>
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-6 text-ink-2">{STATUS_LABEL[c.status]}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </Panel>
      </main>
    </div>
  )
}
