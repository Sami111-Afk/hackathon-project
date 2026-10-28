import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '@/lib/api'
import { getToken, getUserName } from '@/lib/auth'

// Comenzi pentru prezentator pe ecranul de proiector — apar doar dacă tab-ul e logat ca bancă.
// Pornesc Atacatorul AI și arată regulile propuse, ca un om să le aprobe în fața publicului.

interface Rule { id: string; description: string; status: string; vetting?: string }

export function ArenaControls({ running }: { running: boolean }) {
  const [rules, setRules] = useState<Rule[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const authed = Boolean(getToken())

  const load = useCallback(() => {
    apiFetch('/api/rules').then((r) => r.json())
      .then((d: { rules: Rule[] }) => setRules(d.rules.filter((x) => x.status === 'proposed')))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!authed) return
    load()
    const t = setInterval(load, 4000)
    return () => clearInterval(t)
  }, [authed, load])

  if (!authed) return null

  const start = () => {
    setBusy(true); setError('')
    apiFetch('/api/admin/attacker/start', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ rounds: 6 }),
    }).catch(() => setError('The attacker did not start (already running, or the server is not responding).'))
      .finally(() => setBusy(false))
  }

  const decide = (id: string, approve: boolean) => {
    apiFetch(`/api/rules/${encodeURIComponent(id)}/${approve ? 'approve' : 'reject'}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decided_by: getUserName() || 'Analyst' }),
    }).then(load).catch(() => setError('The decision was not saved.'))
  }

  const rule = rules[rules.length - 1]
  return (
    <div className="fixed bottom-4 left-4 z-10 flex max-w-xl flex-col gap-2 text-base">
      {rule && (
        <div className="rounded-md border border-brand bg-night-2 p-4 shadow-lg">
          <div className="text-sm font-semibold uppercase tracking-wide text-brand">Rule proposed by AI, tested on history — a human approves</div>
          <p className="mt-1 text-lg text-night-ink">{rule.description}</p>
          <div className="mt-3 flex gap-2">
            <button type="button" onClick={() => decide(rule.id, true)}
              className="rounded-sm bg-night-ok px-4 py-2 font-semibold text-night">Approve</button>
            <button type="button" onClick={() => decide(rule.id, false)}
              className="rounded-sm border border-night-line px-4 py-2 font-semibold text-night-ink">Reject</button>
          </div>
        </div>
      )}
      <div className="flex items-center gap-3">
        <button type="button" onClick={start} disabled={busy || running}
          className="rounded-sm border border-night-line bg-night-2 px-4 py-2 font-semibold text-night-ink hover:border-brand disabled:opacity-40">
          {running ? 'The attacker is running…' : 'Start the automatic attacker'}
        </button>
        {error && <span className="text-sm text-night-danger">{error}</span>}
      </div>
    </div>
  )
}
