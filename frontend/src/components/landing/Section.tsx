import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

/** Containerul comun al paginii de prezentare: lățime, spațiere și eticheta mică + titlu + intro. */
export function Section({
  id, eyebrow, title, intro, children, className, center,
}: {
  id?: string
  eyebrow?: string
  title?: ReactNode
  intro?: ReactNode
  children?: ReactNode
  className?: string
  center?: boolean
}) {
  return (
    <section id={id} aria-labelledby={id && title ? `${id}-title` : undefined} className={cn('scroll-mt-20 px-4 py-20 sm:px-6 lg:px-8 lg:py-28', className)}>
      <div className="mx-auto max-w-6xl">
        {(eyebrow || title || intro) && (
          <div className={cn('reveal max-w-3xl', center && 'mx-auto text-center')}>
            {eyebrow && <p className="text-sm font-semibold uppercase tracking-[0.14em] text-brand">{eyebrow}</p>}
            {title && <h2 id={id ? `${id}-title` : undefined} className="mt-3 text-4xl font-bold tracking-tight sm:text-display-sm">{title}</h2>}
            {intro && <p className="mt-5 text-lg leading-relaxed text-night-mute">{intro}</p>}
          </div>
        )}
        {children}
      </div>
    </section>
  )
}
