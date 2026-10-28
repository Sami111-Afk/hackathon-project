import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ExternalLink, FileSearch, LayoutDashboard, LogOut, MonitorPlay, ShieldCheck } from 'lucide-react'
import { useEffect, useLayoutEffect } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { LocalModeToggle } from '@/components/LocalModeToggle'
import { getCase, listCases } from '@/lib/api'
import { getUserName, logout } from '@/lib/auth'
import { latestMariaId, loadCasePage, loadDashboardPage, loadZkPage } from '@/lib/bankPages'
import { isMock } from '@/lib/config'
import { navigateWithFade, pageDrawn } from '@/lib/pageFade'
import { cn } from '@/lib/utils'

const MARIA = '/cases/case_maria'

/**
 * După ce pagina curentă e gata (browserul stă degeaba), aducem în fundal celelalte pagini și dosarul Mariei:
 * click-ul din meniu nu mai așteaptă rețeaua. Nu atinge prima încărcare, deci nici scorul Lighthouse.
 */
function usePrefetchBankPages(mariaId: string | undefined, mock: boolean) {
  const qc = useQueryClient()
  useEffect(() => {
    const run = () => {
      void loadDashboardPage(); void loadCasePage(); void loadZkPage()
      if (mariaId && !mock) void qc.prefetchQuery({ queryKey: ['case', mariaId, false], queryFn: () => getCase(mariaId) })
    }
    if ('requestIdleCallback' in window) {
      const id = requestIdleCallback(run, { timeout: 3000 })
      return () => cancelIdleCallback(id)
    }
    const id = setTimeout(run, 1500)
    return () => clearTimeout(id)
  }, [qc, mariaId, mock])
}

/** Bara de sus a aplicației băncii. Galbenul apare doar aici, ca semn de brand. */
export function AppNav() {
  const mock = isMock()
  const name = getUserName()
  const { pathname } = useLocation()
  const navigate = useNavigate()
  useLayoutEffect(pageDrawn, [pathname]) // pagina nouă e pe ecran: estomparea poate porni
  // Linkul trece prin /cases/case_maria (alias-ul din CasePage → ultima rulare): după „Re-run live” rularea veche e ștearsă.
  // Lista e folosită doar ca să preîncărcăm dosarul.
  const cases = useQuery({ queryKey: ['cases', false], queryFn: listCases, enabled: !mock, staleTime: 5000 })
  const mariaId = cases.data ? latestMariaId(cases.data) : undefined
  usePrefetchBankPages(mariaId, mock)

  const links = [
    { to: '/dashboard', label: 'Overview', icon: LayoutDashboard },
    // Activ pe orice rulare a Mariei: /cases/case_maria_<id> nu se potrivește cu linkul /cases/case_maria.
    { to: MARIA, label: "Maria Ionescu's application", icon: FileSearch, active: pathname.startsWith(MARIA) },
    { to: '/zk', label: 'Income proof (ZK)', icon: ShieldCheck },
  ]
  return (
    <header className="border-b border-line bg-surface [view-transition-name:app-nav]">
      <div className="h-1 bg-brand" />
      {/* Pe telefon: logo și butoanele sus, meniul dedesubt, glisabil pe orizontală; de la xl totul pe un rând */}
      <div className="flex flex-wrap items-center gap-x-4 px-4 sm:gap-x-8 md:px-8">
        <div className="flex items-center gap-3 py-3">
          <span className="grid h-8 w-8 place-items-center rounded-sm bg-ink font-condensed text-lg font-bold text-brand">O</span>
          <div className="leading-tight">
            <div className="text-lg font-bold tracking-tight text-ink">ORB</div>
            <div className="hidden text-xs text-ink-3 sm:block">Loan application verification</div>
          </div>
        </div>
        <nav aria-label="Main" className="order-last -mx-4 flex w-[calc(100%+2rem)] gap-6 self-stretch overflow-x-auto border-t border-line px-4 [scrollbar-width:none] md:-mx-8 md:w-[calc(100%+4rem)] md:px-8 xl:order-none xl:mx-0 xl:w-auto xl:border-t-0 xl:px-0">
          {links.map((l) => (
            <NavLink
              key={l.label}
              to={l.to}
              onClick={(e) => {
                if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return // tab nou etc.: comportamentul normal
                e.preventDefault()
                navigateWithFade(() => navigate(l.to))
              }}
              className={({ isActive }) => cn(
                'flex shrink-0 items-center gap-2 whitespace-nowrap border-b-2 py-3 text-[15px] font-medium transition-colors xl:py-0',
                (l.active ?? isActive) ? 'border-ink text-ink' : 'border-transparent text-ink-2 hover:text-ink',
              )}
            >
              <l.icon className="h-4 w-4 opacity-70" aria-hidden />{l.label}
            </NavLink>
          ))}
          <a href="/arena/live" target="_blank" rel="noreferrer" title="The Arena projector screen, in a new tab"
             className="flex shrink-0 items-center gap-2 whitespace-nowrap border-b-2 border-transparent py-3 text-[15px] font-medium text-ink-2 hover:text-ink xl:py-0">
            <MonitorPlay className="h-4 w-4 opacity-70" aria-hidden />Arena <ExternalLink className="h-3.5 w-3.5" aria-hidden />
          </a>
        </nav>
        <div className="ml-auto flex items-center gap-3 py-2 sm:gap-4">
          {mock ? (
            <a href="?mock=0" className="rounded-sm border border-warn bg-warn-bg px-3 py-1.5 text-sm font-semibold text-warn"
               title="Exit demo mode">
              Demo data, no backend · Exit
            </a>
          ) : (
            <>
              <LocalModeToggle />
              {name && (
                <span className="hidden items-center gap-2 text-sm font-semibold text-ink sm:flex">
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-ink text-xs font-bold uppercase text-brand" aria-hidden>{name.trim().charAt(0)}</span>
                  {name}
                </span>
              )}
              <button type="button" onClick={() => { logout(); window.location.assign('/login') }}
                      className="flex items-center gap-1.5 rounded-sm border border-line px-3 py-1.5 text-sm font-semibold text-ink transition-colors hover:border-ink hover:bg-canvas">
                <LogOut className="h-4 w-4" aria-hidden /><span className="hidden sm:inline">Sign out</span><span className="sr-only sm:hidden">Sign out</span>
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
