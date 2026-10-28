import { Target, Trophy } from 'lucide-react'
import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'

const LINKS = [
  { to: '/arena', label: 'Missions', icon: Target, end: true },
  { to: '/arena/top', label: 'Leaderboard', icon: Trophy, end: false },
]

/**
 * Cadru pentru Arena. Pe telefon: navigare jos, cu loc lăsat dedesubt (și pentru bara iPhone-ului).
 * Pe desktop: navigarea urcă în antet, ca să nu acopere conținutul.
 */
export function ArenaShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-dvh bg-night pb-[calc(7rem_+_env(safe-area-inset-bottom))] text-night-ink md:pb-12">
      <div className="bg-brand px-4 py-2 text-center text-sm font-semibold text-ink">
        Demo game. Do not upload real documents.
      </div>
      {/* Antetul pe toată lățimea, cu o linie dedesubt (ca bara băncii); fila activă e subliniată cu galben */}
      <header className="border-b border-night-line">
        <div className="mx-auto flex max-w-xl items-center gap-3 px-5">
          <div className="flex items-center gap-3 py-4">
            <span className="grid h-9 w-9 place-items-center rounded-sm bg-brand font-condensed text-lg font-bold text-ink">O</span>
            <div className="leading-tight">
              <div className="text-lg font-bold tracking-tight">ORB Arena</div>
              <div className="text-sm text-night-mute">Try to fool the bank's agents</div>
            </div>
          </div>
          <nav className="ml-auto hidden gap-6 self-stretch md:flex">
            {LINKS.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.end}
                className={({ isActive }) => cn('flex items-center gap-2 border-b-2 text-base font-semibold transition-colors',
                  isActive ? 'border-brand text-brand' : 'border-transparent text-night-mute hover:text-night-ink')}>
                <l.icon className="h-4 w-4" aria-hidden /> {l.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-xl px-5 pt-8">{children}</main>
      <nav aria-label="Arena" className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-2 border-t border-night-line bg-night/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden">
        {LINKS.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end}
            className={({ isActive }) => cn('flex items-center justify-center gap-2 border-t-2 py-4 text-base font-semibold',
              isActive ? 'border-brand text-brand' : 'border-transparent text-night-mute')}>
            <l.icon className="h-5 w-5" aria-hidden /> {l.label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}

/** Titlul unei secțiuni din Arena: semnul galben (ca în aplicația băncii) și, opțional, numărul pasului. */
export function ArenaHeading({ step, children, as: Tag = 'h2', className }: { step?: number; children: ReactNode; as?: 'h1' | 'h2' | 'h3'; className?: string }) {
  return (
    <Tag className={cn('flex items-center gap-3 text-2xl font-semibold tracking-tight', className)}>
      <span className="h-5 w-1 shrink-0 bg-brand" aria-hidden />
      {step != null && <span className="font-condensed text-xl font-bold tabular-nums text-night-mute" aria-hidden>{String(step).padStart(2, '0')}</span>}
      {children}
    </Tag>
  )
}
