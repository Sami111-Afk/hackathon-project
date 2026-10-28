/** Pașii numerotați (cum trece un dosar prin ORB): pe telefon unul sub altul, pe ecran mare pe un rând. */
export function StepList({ steps }: { steps: { title: string; text: string }[] }) {
  return (
    <ol className="mt-14 grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-night-line bg-night-line sm:grid-cols-2 lg:grid-cols-4">
      {steps.map((s, i) => (
        <li key={s.title} className="reveal flex flex-col bg-night p-6 lg:p-7">
          <span className="font-condensed text-5xl font-bold leading-none text-brand tabular-nums" aria-hidden>{String(i + 1).padStart(2, '0')}</span>
          <h3 className="mt-6 text-xl font-semibold"><span className="sr-only">Step {i + 1}: </span>{s.title}</h3>
          <p className="mt-2 leading-relaxed text-night-mute">{s.text}</p>
        </li>
      ))}
    </ol>
  )
}
