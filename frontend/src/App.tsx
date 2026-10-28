import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { lazy, Suspense, type ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { getToken } from '@/lib/auth'
import { isMock } from '@/lib/config'

// Fiecare pagină se încarcă separat: telefonul din Arena nu descarcă graficele băncii.
const CasePage = lazy(() => import('@/pages/CasePage').then((m) => ({ default: m.CasePage })))
const DashboardPage = lazy(() => import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage })))
const ZkPage = lazy(() => import('@/pages/ZkPage').then((m) => ({ default: m.ZkPage })))
const LoginPage = lazy(() => import('@/pages/LoginPage').then((m) => ({ default: m.LoginPage })))
const ArenaStart = lazy(() => import('@/pages/arena/ArenaStart').then((m) => ({ default: m.ArenaStart })))
const ArenaForge = lazy(() => import('@/pages/arena/ArenaForge').then((m) => ({ default: m.ArenaForge })))
const ArenaResult = lazy(() => import('@/pages/arena/ArenaResult').then((m) => ({ default: m.ArenaResult })))
const ArenaTop = lazy(() => import('@/pages/arena/ArenaTop').then((m) => ({ default: m.ArenaTop })))
const ArenaLive = lazy(() => import('@/pages/arena/ArenaLive').then((m) => ({ default: m.ArenaLive })))

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } })

function RequireAuth({ children }: { children: ReactNode }) {
  if (isMock() || getToken()) return <>{children}</>
  return <Navigate to="/login" replace />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<div className="p-8 text-lg text-slate-500">Se încarcă…</div>}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/dashboard" element={<RequireAuth><DashboardPage /></RequireAuth>} />
            <Route path="/zk" element={<RequireAuth><ZkPage /></RequireAuth>} />
            <Route path="/cases/:caseId" element={<RequireAuth><CasePage /></RequireAuth>} />
            {/* Arena: publică, fără login */}
            <Route path="/arena" element={<ArenaStart />} />
            <Route path="/arena/m/:missionId" element={<ArenaForge />} />
            <Route path="/arena/r/:sid" element={<ArenaResult />} />
            <Route path="/arena/top" element={<ArenaTop />} />
            <Route path="/arena/live" element={<ArenaLive />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
