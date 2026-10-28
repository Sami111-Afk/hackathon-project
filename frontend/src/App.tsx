import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { getToken } from '@/lib/auth'
import { isMock } from '@/lib/config'
import { CasePage } from '@/pages/CasePage'
import { LoginPage } from '@/pages/LoginPage'

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } })

function RequireAuth({ children }: { children: ReactNode }) {
  if (isMock() || getToken()) return <>{children}</>
  return <Navigate to="/login" replace />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/cases/:caseId" element={<RequireAuth><CasePage /></RequireAuth>} />
          <Route path="*" element={<Navigate to="/cases/case_maria" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
