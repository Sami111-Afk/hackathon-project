import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'

/** Cadru pentru telefon: avertisment sus, navigare jos, butoane mari. */
export function ArenaShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-dvh bg-slate-950 pb-24 text-slate-100">
      <div className="bg-amber-400 px-4 py-2 text-center text-sm font-semibold text-slate-950">
        ⚠️ Joc demonstrativ. Nu încărcați documente reale.
      </div>
      <header className="px-4 pt-5">
        <h1 className="text-2xl font-black tracking-tight">🎮 ORB Arena</h1>
        <p className="text-slate-400">Poți păcăli agenții AI ai băncii?</p>
      </header>
      <main className="mx-auto max-w-xl px-4 pt-4">{children}</main>
      <nav className="fixed inset-x-0 bottom-0 grid grid-cols-2 border-t border-slate-800 bg-slate-900/95 backdrop-blur">
        {[{ to: '/arena', label: '🎯 Misiuni', end: true }, { to: '/arena/top', label: '🏆 Clasament', end: false }].map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end}
            className={({ isActive }) => cn('py-4 text-center text-lg font-semibold', isActive ? 'text-amber-400' : 'text-slate-400')}>
            {l.label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
