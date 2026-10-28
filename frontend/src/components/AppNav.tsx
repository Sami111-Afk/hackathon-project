import { LogOut } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { LocalModeToggle } from '@/components/LocalModeToggle'
import { getUserName, logout } from '@/lib/auth'
import { isMock } from '@/lib/config'
import { cn } from '@/lib/utils'

const LINKS = [
  { to: '/dashboard', label: 'Privire de ansamblu' },
  { to: '/cases/case_maria', label: 'Dosarul Mariei Ionescu' },
]

/** Bara de sus a aplicației băncii. Galbenul apare doar aici, ca semn de brand. */
export function AppNav() {
  const mock = isMock()
  const name = getUserName()
  return (
    <header className="border-b border-line bg-surface">
      <div className="h-1 bg-brand" />
      <div className="flex flex-wrap items-center gap-x-8 gap-y-2 px-4 md:px-8">
        <div className="flex items-center gap-3 py-3">
          <span className="grid h-8 w-8 place-items-center rounded-sm bg-ink font-condensed text-lg font-bold text-brand">O</span>
          <div className="leading-tight">
            <div className="text-lg font-bold tracking-tight text-ink">ORB</div>
            <div className="text-xs text-ink-3">Verificarea dosarelor de credit</div>
          </div>
        </div>
        <nav className="flex gap-6 self-stretch">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) => cn(
                'flex items-center border-b-2 text-[15px] font-medium transition-colors',
                isActive ? 'border-ink text-ink' : 'border-transparent text-ink-2 hover:text-ink',
              )}
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-4 py-2">
          {mock ? (
            <a href="?mock=0" className="rounded-sm border border-warn bg-warn-bg px-3 py-1.5 text-sm font-semibold text-warn"
               title="Ieși din modul demo">
              Date de demo, fără backend · Ieși
            </a>
          ) : (
            <>
              <LocalModeToggle />
              {name && <span className="text-sm text-ink-2">{name}</span>}
              <button type="button" onClick={() => { logout(); window.location.assign('/login') }}
                      className="flex items-center gap-1.5 text-sm text-ink-2 hover:text-ink">
                <LogOut className="h-4 w-4" aria-hidden /> Ieșire
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
