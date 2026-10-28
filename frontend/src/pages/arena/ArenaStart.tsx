import { useQuery } from '@tanstack/react-query'
import { ChevronRight } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMissions, lei, saveNick, savedNick } from '@/lib/arena'
import { ArenaHeading, ArenaShell } from './ArenaShell'
import { usePageMeta } from '@/hooks/usePageMeta'

type Step = 'intro' | 'nick' | 'missions'

/** Start: o propoziție + „Începe” → pseudonim → misiuni. Cine a mai jucat sare direct la misiuni. */
export function ArenaStart() {
  usePageMeta("ORB Arena: can you fool the bank with a fake payslip?", "Can you fool the bank's AI agents with a fake payslip? A one-minute game from ORB, no account needed.")
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
          <p className="inline-flex w-fit items-center gap-2 rounded-full border border-night-line px-3 py-1 text-sm font-medium text-night-mute">
            <span className="h-2 w-2 rounded-full bg-brand motion-safe:animate-pulse" aria-hidden />Live demo · ORB Arena
          </p>
          <h1 className="mt-5 text-4xl font-bold leading-[1.08] tracking-tight sm:text-5xl">Can you fool the bank with a <span className="text-brand">fake payslip</span>?</h1>
          <p className="mt-4 text-lg leading-relaxed text-night-mute">
            Edit a payslip and submit it. The bank's AI agents check it within seconds and tell you whether they caught you, and why.
          </p>
          <button type="button" onClick={() => setStep('nick')}
            className="mt-8 h-16 w-full rounded-md bg-brand text-xl font-bold text-ink active:scale-[0.99]">
            Start
          </button>
          <p className="mt-4 text-center text-sm text-night-mute">Takes a minute. No account needed.</p>
          {/* Cum merge jocul, în trei pași numerotați (același model ca pașii din aplicația băncii) */}
          <ol className="mt-10 grid grid-cols-3 gap-px overflow-hidden rounded-md border border-night-line bg-night-line text-sm">
            {['Pick a mission', 'Edit the payslip', 'See if the agents catch you'].map((t, i) => (
              <li key={t} className="bg-night-2 p-3">
                <span className="font-condensed text-lg font-bold tabular-nums text-brand" aria-hidden>{String(i + 1).padStart(2, '0')}</span>
                <span className="mt-1 block leading-snug text-night-ink">{t}</span>
              </li>
            ))}
          </ol>
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
      <ArenaHeading>Pick a mission</ArenaHeading>
      <p className="mt-1 text-sm text-night-mute">
        Playing as <span className="font-semibold text-night-ink">{savedNick()}</span>.{' '}
        <button type="button" onClick={() => setStep('nick')} className="underline underline-offset-2 hover:text-night-ink">Change</button>
      </p>
      {missions.isLoading && <p className="mt-4 text-night-mute">Loading missions.</p>}
      {missions.isError && <p className="mt-4 text-night-danger">The server is not responding. Try again in a few seconds.</p>}
      <div className="mt-4 space-y-3">
        {missions.data?.map((m, i) => (
          <button key={m.id} type="button" onClick={() => nav(`/arena/m/${m.id}`)}
            className="group flex w-full items-center gap-4 rounded-md border border-night-line bg-night-2 p-5 text-left transition-colors active:scale-[0.99] hover:border-brand">
            <span className="flex-1">
              <span className="block font-condensed text-sm font-semibold uppercase tracking-[0.14em] text-night-mute">Mission {String(i + 1).padStart(2, '0')}</span>
              <span className="mt-1 block text-xl font-semibold">{m.title}</span>
              <span className="mt-1 block text-base leading-snug text-night-mute">{m.brief}</span>
              <span className="mt-3 inline-block rounded-sm bg-brand/15 px-2 py-1 text-sm font-semibold text-brand">Target: net income of at least {lei(m.target.min)}</span>
            </span>
            <ChevronRight className="h-6 w-6 shrink-0 text-night-mute transition-transform group-hover:translate-x-0.5 group-hover:text-brand" aria-hidden />
          </button>
        ))}
      </div>
    </ArenaShell>
  )
}
