import { Bar, BarChart, CartesianGrid, LabelList, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

// Graficele stau separat de DashboardPage: recharts (~100 KB) se încarcă după ce cifrele și tabelul sunt deja pe ecran.

// Culori de stare (fixe, din ghidul de grafice) — mereu împreună cu iconiță + etichetă.
const C = { good: '#0ca30c', warning: '#fab219', critical: '#d03b3b' }
const SURFACE = '#ffffff'
const LEGEND_ORDER = ['clear', 'review', 'escalate']

export function TimeChart({ data }: { data: { name: string; hours: number; fill: string }[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 72 }}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="name" width={220} tickLine={false} axisLine={false}
               tick={{ fill: '#1F2328', fontSize: 18 }} />
        <Tooltip cursor={{ fill: 'rgba(31,35,40,0.04)' }} formatter={(v) => [`${Number(v).toLocaleString('en-GB')} hours`, 'Time']} />
        <Bar dataKey="hours" radius={[0, 3, 3, 0]} barSize={40} isAnimationActive={false}>
          <LabelList dataKey="hours" position="right" formatter={(v) => `${Number(v).toLocaleString('en-GB')} h`}
                     style={{ fill: '#1F2328', fontSize: 20, fontWeight: 600 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function PerDayChart({ data }: { data: { day: string; clear: number; review: number; escalate: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ left: -16, right: 8 }}>
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
  )
}
