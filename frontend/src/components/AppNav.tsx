import { NavLink } from 'react-router-dom'
import { LocalModeToggle } from '@/components/LocalModeToggle'
import { Button } from '@/components/ui/button'
import { logout } from '@/lib/auth'
import { isMock } from '@/lib/config'
import { cn } from '@/lib/utils'

const LINKS = [
  { to: '/dashboard', label: '📊 Dashboard' },
  { to: '/cases/case_maria', label: '📁 Dosarul Mariei' },
]

/** Bara de sus, comună tuturor paginilor băncii. */
export function AppNav() {
  const mock = isMock()
  return (
    <nav className="flex flex-wrap items-center gap-2 border-b bg-slate-900 px-4 py-2 text-white md:px-6">
      <span className="mr-4 text-lg font-bold">🔒 ORB</span>
      {LINKS.map((l) => (
        <NavLink
          key={l.to}
          to={l.to}
          className={({ isActive }) => cn('rounded-md px-3 py-1.5 text-base', isActive ? 'bg-white/15 font-semibold' : 'text-slate-300 hover:text-white')}
        >
          {l.label}
        </NavLink>
      ))}
      <span className="ml-auto" />
      {mock ? (
        <a href="?mock=0" className="rounded-full bg-amber-400 px-4 py-1.5 text-base font-bold text-slate-950" title="Ieși din modul demo">
          ⚠️ DATE DE DEMO · ieși
        </a>
      ) : (
        <LocalModeToggle />
      )}
      {!mock && (
        <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white" onClick={() => { logout(); window.location.assign('/login') }}>
          Ieșire
        </Button>
      )}
    </nav>
  )
}
