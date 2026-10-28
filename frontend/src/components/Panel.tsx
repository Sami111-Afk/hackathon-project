import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

/** Panou de lucru: suprafață albă, o singură linie de contur, fără umbră. */
export function Panel({
  title, aside, children, className, bodyClassName,
}: {
  title?: ReactNode
  aside?: ReactNode
  children: ReactNode
  className?: string
  bodyClassName?: string
}) {
  return (
    <section className={cn('rounded-md border border-line bg-surface', className)}>
      {title && (
        <header className="flex min-h-14 items-center justify-between gap-4 border-b border-line px-5 py-3">
          <h2 className="text-lg font-semibold text-ink">{title}</h2>
          {aside}
        </header>
      )}
      <div className={cn('p-5', bodyClassName)}>{children}</div>
    </section>
  )
}
