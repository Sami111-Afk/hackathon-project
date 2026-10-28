import { Target, Trophy } from 'lucide-react'
import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'

/** Cadru pentru telefon: avertisment sus, navigare jos, butoane mari. */
export function ArenaShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-dvh bg-night pb-24 text-night-ink">
      <div className="bg-brand px-4 py-2 text-center text-sm font-semibold text-ink">
        Joc demonstrativ. Nu încărca documente reale.
      </div>
      <header className="flex items-center gap-3 px-5 pt-5">
        <span className="grid h-9 w-9 place-items-center rounded-sm bg-brand font-condensed text-lg font-bold text-ink">O</span>
        <div className="leading-tight">
          <div className="text-lg font-bold tracking-tight">ORB Arena</div>
          <div className="text-sm text-night-mute">Încearcă să păcălești agenții băncii</div>
        </div>
      </header>
      <main className="mx-auto max-w-xl px-5 pt-6">{children}</main>
      <nav className="fixed inset-x-0 bottom-0 grid grid-cols-2 border-t border-night-line bg-night/95 backdrop-blur">
        {[{ to: '/arena', label: 'Misiuni', icon: Target, end: true }, { to: '/arena/top', label: 'Clasament', icon: Trophy, end: false }].map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end}
            className={({ isActive }) => cn('flex items-center justify-center gap-2 py-4 text-base font-semibold',
              isActive ? 'text-brand' : 'text-night-mute')}>
            <l.icon className="h-5 w-5" aria-hidden /> {l.label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
