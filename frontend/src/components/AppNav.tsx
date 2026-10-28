import { NavLink } from 'react-router-dom'
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
      <span className="ml-auto text-sm text-slate-400">{mock ? 'mod demo (fără backend)' : ''}</span>
      {!mock && (
        <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white" onClick={() => { logout(); window.location.assign('/login') }}>
          Ieșire
        </Button>
      )}
    </nav>
  )
}
