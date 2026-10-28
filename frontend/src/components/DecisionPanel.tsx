import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { postDecision } from '@/lib/api'
import { getUserName } from '@/lib/auth'
import { DECISION_LABEL } from '@/lib/labels'
import type { Decision, DecisionAction } from '@/lib/types'

const ACTIONS: { action: DecisionAction; variant: 'default' | 'destructive' | 'outline' }[] = [
  { action: 'reject', variant: 'destructive' },
  { action: 'flag_network', variant: 'destructive' },
  { action: 'escalate', variant: 'outline' },
  { action: 'clear', variant: 'outline' },
]

/** Omul ia decizia. În mock, decizia rămâne doar local. */
export function DecisionPanel({
  caseId, decision, mock, disabled, onDecided,
}: {
  caseId: string
  decision: Decision | null
  mock: boolean
  disabled: boolean
  onDecided: (d: Decision) => void
}) {
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const name = getUserName() || (mock ? 'Demo' : '')

  async function decide(action: DecisionAction) {
    setBusy(true)
    setError(null)
    try {
      const d: Decision = mock
        ? { action, decided_by: name, notes, corrections: {}, decided_at: new Date().toISOString() }
        : await postDecision(caseId, { action, notes, decided_by: name })
      onDecided(d)
    } catch {
      setError('Decizia nu a putut fi salvată. Încearcă din nou.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card>
      <CardHeader><CardTitle className="text-xl">👤 Decizia ta</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {decision ? (
          <p className="text-lg">
            ✅ <b>{DECISION_LABEL[decision.action]}</b> — de {decision.decided_by || 'necunoscut'}
            {decision.notes && <span className="block text-base text-slate-600">„{decision.notes}”</span>}
          </p>
        ) : (
          <>
            <Input placeholder="Notițe (opțional)" value={notes} onChange={(e) => setNotes(e.target.value)} />
            <div className="grid grid-cols-2 gap-2">
              {ACTIONS.map(({ action, variant }) => (
                <Button key={action} size="lg" variant={variant} disabled={busy || disabled} onClick={() => decide(action)}>
                  {DECISION_LABEL[action]}
                </Button>
              ))}
            </div>
            {disabled && <p className="text-sm text-slate-500">Butoanele se activează după verdict.</p>}
            {error && <p className="text-sm text-red-700">{error}</p>}
          </>
        )}
      </CardContent>
    </Card>
  )
}
