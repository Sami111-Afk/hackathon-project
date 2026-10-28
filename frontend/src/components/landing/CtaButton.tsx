import { ArrowRight } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'

const VARIANT = {
  brand: 'bg-brand text-ink hover:bg-[#FFF06A]', // pe fundal închis
  dark: 'bg-ink text-white hover:bg-black', // pe fundal galben
  outline: 'border border-night-line text-night-ink hover:border-night-ink', // pe fundal închis
  'outline-dark': 'border border-ink/30 text-ink hover:border-ink', // pe fundal galben
}

/** Butonul pastilă al paginii de prezentare: etichetă scurtă + săgeată care alunecă la hover. */
export function CtaButton({
  to, variant = 'brand', children, className, external,
}: {
  to: string
  variant?: keyof typeof VARIANT
  children: ReactNode
  className?: string
  external?: boolean
}) {
  const cls = cn(
    'group inline-flex h-12 items-center justify-center gap-2 rounded-full px-6 text-sm font-semibold uppercase tracking-wide transition-colors',
    'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand',
    VARIANT[variant], className,
  )
  const inner = <>{children}<ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden /></>
  return external
    ? <a href={to} className={cls} target="_blank" rel="noreferrer">{inner}</a>
    : <Link to={to} className={cls}>{inner}</Link>
}
