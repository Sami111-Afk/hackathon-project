import { useQuery } from '@tanstack/react-query'
import { ChevronRight } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMissions, lei, saveNick, savedNick } from '@/lib/arena'
import { ArenaShell } from './ArenaShell'

type Step = 'intro' | 'nick' | 'missions'

/** Start: o propoziție + „Începe” → pseudonim → misiuni. Cine a mai jucat sare direct la misiuni. */
export function ArenaStart() {
  const nav = useNavigate()
  const [nick, setNick] = useState(savedNick())
  const [step, setStep] = useState<Step>(savedNick() ? 'missions' : 'intro')
  const missions = useQuery({ queryKey: ['arena-missions'], queryFn: getMissions, staleTime: 60_000 })
  const nickOk = nick.trim().length >= 2 && nick.trim().length <= 20

  function confirmNick(e: FormEvent) {
    e.preventDefault()
    if (!nickOk) return
    saveNick(nick.trim())
    setStep('missions')
  }

  if (step === 'intro') {
    return (
      <ArenaShell>
        <section className="flex min-h-[60dvh] flex-col justify-center">
          <h1 className="text-4xl font-bold leading-tight tracking-tight">Can you fool the bank with a fake payslip?</h1>
          <p className="mt-4 text-lg leading-relaxed text-night-mute">
            Edit a payslip and submit it. The bank's AI agents check it within seconds and tell you whether they caught you, and why.
          </p>
          <button type="button" onClick={() => setStep('nick')}
            className="mt-8 h-16 w-full rounded-md bg-brand text-xl font-bold text-ink active:scale-[0.99]">
            Start
          </button>
          <p className="mt-4 text-center text-sm text-night-mute">Takes a minute. No account needed.</p>
        </section>
      </ArenaShell>
    )
  }

  if (step === 'nick') {
    return (
      <ArenaShell>
        <form onSubmit={confirmNick} className="flex min-h-[50dvh] flex-col justify-center">
          <label htmlFor="nick" className="text-2xl font-semibold">What should we call you?</label>
          <p className="mt-1 text-base text-night-mute">Your name appears on the big screen, next to your attempts.</p>
          <input id="nick" autoFocus value={nick} onChange={(e) => setNick(e.target.value)} maxLength={20} placeholder="For example, Andrei"
            autoComplete="nickname"
            className="mt-5 h-14 w-full rounded-md border border-night-line bg-night-2 px-4 text-xl outline-none placeholder:text-night-mute/60 focus:border-brand" />
          <button type="submit" disabled={!nickOk}
            className="mt-4 h-14 w-full rounded-md bg-brand text-lg font-bold text-ink disabled:opacity-40">
            Continue
          </button>
          {nick.length > 0 && !nickOk && <p className="mt-2 text-sm text-night-mute">Between 2 and 20 characters.</p>}
        </form>
      </ArenaShell>
    )
  }

  return (
    <ArenaShell>
      <h2 className="text-2xl font-semibold">Pick a mission</h2>
      <p className="mt-1 text-sm text-night-mute">
        Playing as <span className="font-semibold text-night-ink">{savedNick()}</span>.{' '}
        <button type="button" onClick={() => setStep('nick')} className="underline underline-offset-2 hover:text-night-ink">Change</button>
      </p>
      {missions.isLoading && <p className="mt-4 text-night-mute">Loading missions.</p>}
      {missions.isError && <p className="mt-4 text-night-danger">The server is not responding. Try again in a few seconds.</p>}
      <div className="mt-4 space-y-3">
        {missions.data?.map((m) => (
          <button key={m.id} type="button" onClick={() => nav(`/arena/m/${m.id}`)}
            className="flex w-full items-center gap-4 rounded-md border border-night-line bg-night-2 p-5 text-left active:scale-[0.99] hover:border-night-mute">
            <span className="flex-1">
              <span className="block text-xl font-semibold">{m.title}</span>
              <span className="mt-1 block text-base leading-snug text-night-mute">{m.brief}</span>
              <span className="mt-3 block text-sm font-semibold text-brand">Target: net income of at least {lei(m.target.min)}</span>
            </span>
            <ChevronRight className="h-6 w-6 shrink-0 text-night-mute" aria-hidden />
          </button>
        ))}
      </div>
    </ArenaShell>
  )
}
