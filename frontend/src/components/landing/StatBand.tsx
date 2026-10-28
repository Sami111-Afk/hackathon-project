import type { ReactNode } from 'react'

/** Cifrele măsurate, mari, pe un rând; sub fiecare, ce înseamnă. Sursa stă sub bandă (o dă pagina). */
export function StatBand({ stats }: { stats: { value: string; label: string; note?: ReactNode }[] }) {
  return (
    <dl className="mt-14 grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-night-line bg-night-line sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((s) => (
        <div key={s.label} className="reveal flex flex-col bg-night-2 p-6 lg:p-7">
          <dt className="order-2 mt-3 text-base font-medium text-night-ink">{s.label}</dt>
          <dd className="order-1 font-condensed text-6xl font-bold leading-none tracking-tight text-brand tabular-nums">{s.value}</dd>
          {s.note && <dd className="order-3 mt-2 text-sm leading-relaxed text-night-mute">{s.note}</dd>}
        </div>
      ))}
    </dl>
  )
}
