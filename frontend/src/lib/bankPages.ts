import type { CaseSummary } from '@/lib/api'

// Paginile băncii: App.tsx le încarcă lazy, AppNav le preîncarcă în fundal (același import → același chunk),
// ca un click în meniu să fie instant.
export const loadDashboardPage = () => import('@/pages/DashboardPage')
export const loadCasePage = () => import('@/pages/CasePage')
export const loadZkPage = () => import('@/pages/ZkPage')

/** Cel mai recent dosar al Mariei: fiecare rulare a demo-ului are id nou (`case_maria_<...>`). */
export function latestMariaId(cases: CaseSummary[]): string | undefined {
  return cases.filter((c) => c.id.startsWith('case_maria_'))
    .sort((a, b) => b.created_at.localeCompare(a.created_at))[0]?.id
}
