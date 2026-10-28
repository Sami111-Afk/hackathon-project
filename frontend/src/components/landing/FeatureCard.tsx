import type { LucideIcon } from 'lucide-react'

/** Cardul unui agent: iconiță în cerc galben, nume, rol și o frază despre ce face concret. */
export function FeatureCard({ icon: Icon, title, role, text }: { icon: LucideIcon; title: string; role: string; text: string }) {
  return (
    <article className="reveal flex flex-col rounded-2xl border border-night-line bg-night-2 p-6 transition-colors hover:border-night-mute/60">
      <span className="grid h-11 w-11 place-items-center rounded-full bg-brand text-ink"><Icon className="h-5 w-5" aria-hidden /></span>
      <h3 className="mt-5 text-xl font-semibold">{title}</h3>
      <p className="mt-1 text-[15px] font-medium text-brand">{role}</p>
      <p className="mt-3 leading-relaxed text-night-mute">{text}</p>
    </article>
  )
}
