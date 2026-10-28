import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '@/lib/auth'
import { API_HEADERS, apiUrl } from '@/lib/config'

export function LoginPage() {
  const nav = useNavigate()
  const [name, setName] = useState('')
  const [token, setToken] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  // verificăm cheia înainte să intrăm: altfel prima cerere dă 401 și utilizatorul e scos imediat din cont
  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!name.trim() || !token.trim()) return
    setBusy(true)
    setError('')
    try {
      const r = await fetch(`${apiUrl()}/api/settings`, {
        headers: { ...API_HEADERS, Authorization: `Bearer ${token.trim()}` },
      })
      if (r.status === 401) { setError('The access key is not correct for this server.'); return }
      if (!r.ok) { setError(`The server responded with an error (${r.status}).`); return }
      login(token, name)
      nav('/dashboard')
    } catch {
      setError('The server is not responding. Check the address below or open the demo without a server.')
    } finally {
      setBusy(false)
    }
  }

  const input = 'h-11 w-full rounded-sm border border-input bg-surface px-3 text-base outline-none focus:border-info'
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <div className="h-1 bg-brand" />
      <div className="flex flex-1 items-center justify-center p-4">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-sm bg-ink font-condensed text-xl font-bold text-brand">O</span>
            <div>
              <div className="text-xl font-bold tracking-tight text-ink">ORB</div>
              <div className="text-sm text-ink-3">Loan application verification</div>
            </div>
          </div>
          <form onSubmit={submit} className="space-y-5 rounded-md border border-line bg-surface p-6">
            <h1 className="text-xl font-semibold text-ink">Sign in</h1>
            <div className="space-y-1.5">
              <label htmlFor="name" className="text-sm font-medium text-ink-2">Your name, shown on decisions</label>
              <input id="name" className={input} value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="token" className="text-sm font-medium text-ink-2">Branch access key</label>
              <input id="token" type="password" className={input} value={token} onChange={(e) => setToken(e.target.value)} autoComplete="off" />
            </div>
            {error && <p className="text-sm text-danger" role="alert">{error}</p>}
            <button type="submit" disabled={busy} className="h-11 w-full rounded-sm bg-ink text-base font-semibold text-white hover:bg-black disabled:opacity-60">
              {busy ? 'Checking…' : 'Sign in'}
            </button>
          </form>
          <p className="mt-4 text-sm text-ink-3">Server: {apiUrl()}</p>
          <a href="/cases/case_maria?mock=1" className="mt-1 inline-block text-sm font-medium text-info hover:underline">Open the demo without a server</a>
        </div>
      </div>
    </div>
  )
}
