import { CheckCircle2 } from 'lucide-react'
import { useState } from 'react'
import { postDecision } from '@/lib/api'
import { getUserName } from '@/lib/auth'
import { DECISION_DONE, DECISION_LABEL } from '@/lib/labels'
import type { Decision, DecisionAction } from '@/lib/types'
import { cn } from '@/lib/utils'

const BTN = 'h-11 rounded-sm px-4 text-[15px] font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-info'

/** Omul ia decizia. În mock, decizia rămâne doar local. */
export function DecisionPanel({
  caseId, decision, mock, disabled, onDecided, recommendation,
}: {
  caseId: string
  decision: Decision | null
  mock: boolean
  disabled: boolean
  onDecided: (d: Decision) => void
  /** recomandarea ORB: dacă e „escalate”, aprobarea cere un motiv scris (rămâne în auditul dosarului) */
  recommendation?: 'clear' | 'review' | 'escalate'
}) {
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const name = getUserName() || (mock ? 'Demo' : '')

  const needsReason = recommendation === 'escalate'

  async function decide(action: DecisionAction) {
    if (action === 'clear' && needsReason && notes.trim().length < 10) {
      setError('This application is flagged for investigation. To approve it, write the reason in the note (at least 10 characters).')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const d: Decision = mock
        ? { action, decided_by: name, notes, corrections: {}, decided_at: new Date().toISOString() }
        : await postDecision(caseId, { action, notes, decided_by: name })
      onDecided(d)
    } catch {
      setError('The decision was not saved: the server did not respond. Try again.')
    } finally {
      setBusy(false)
    }
  }

  if (decision) {
    return (
      <div className="flex items-start gap-3 border-t border-line bg-canvas/60 px-6 py-5">
        <CheckCircle2 className="mt-0.5 h-5 w-5 text-ok" aria-hidden />
        <div>
          <div className="text-base font-semibold text-ink">{DECISION_DONE[decision.action]}</div>
          <div className="text-sm text-ink-2">by {decision.decided_by || 'unknown'}{decision.notes ? `: “${decision.notes}”` : ''}</div>
        </div>
      </div>
    )
  }

  const off = busy || disabled
  return (
    <div className="space-y-3 border-t border-line px-6 py-5">
      <label className="block text-sm font-medium text-ink-2" htmlFor="notes">
        {needsReason ? 'Note for the application (required if you approve)' : 'Note for the application (optional)'}
      </label>
      <input id="notes" value={notes} onChange={(e) => setNotes(e.target.value)}
             className="h-10 w-full rounded-sm border border-input bg-surface px-3 text-[15px] outline-none focus:border-info" />
      <div className="grid grid-cols-2 gap-2">
        <button type="button" disabled={off} onClick={() => decide('reject')} className={cn(BTN, 'bg-danger text-white hover:bg-[#912018]')}>
          {DECISION_LABEL.reject}
        </button>
        <button type="button" disabled={off} onClick={() => decide('flag_network')} className={cn(BTN, 'border border-danger text-danger hover:bg-danger-bg')}>
          {DECISION_LABEL.flag_network}
        </button>
        <button type="button" disabled={off} onClick={() => decide('escalate')} className={cn(BTN, 'border border-line text-ink hover:bg-canvas')}>
          {DECISION_LABEL.escalate}
        </button>
        <button type="button" disabled={off} onClick={() => decide('clear')} className={cn(BTN, 'border border-line text-ink hover:bg-canvas')}>
          {DECISION_LABEL.clear}
        </button>
      </div>
      {disabled && <p className="text-sm text-ink-3">Decisions become available after the verdict.</p>}
      {error && <p className="text-sm text-danger">{error}</p>}
    </div>
  )
}
