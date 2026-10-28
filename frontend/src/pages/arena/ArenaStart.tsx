import { useQuery } from '@tanstack/react-query'
import { ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMissions, lei, saveNick, savedNick } from '@/lib/arena'
import { ArenaShell } from './ArenaShell'

export function ArenaStart() {
  const nav = useNavigate()
  const [nick, setNick] = useState(savedNick())
  const missions = useQuery({ queryKey: ['arena-missions'], queryFn: getMissions, staleTime: 60_000 })
  const nickOk = nick.trim().length >= 2 && nick.trim().length <= 20

  return (
    <ArenaShell>
      <label className="block">
        <span className="text-base text-night-mute">Pseudonimul tău, apare pe ecranul mare</span>
        <input value={nick} onChange={(e) => setNick(e.target.value)} maxLength={20} placeholder="De exemplu, Andrei"
          className="mt-2 h-14 w-full rounded-md border border-night-line bg-night-2 px-4 text-xl outline-none placeholder:text-night-mute/60 focus:border-brand" />
      </label>

      <h2 className="mt-8 text-xl font-semibold">Alege o misiune</h2>
      {missions.isLoading && <p className="mt-3 text-night-mute">Se încarcă misiunile.</p>}
      {missions.isError && <p className="mt-3 text-night-danger">Serverul nu răspunde. Încearcă din nou în câteva secunde.</p>}
      <div className="mt-3 space-y-3">
        {missions.data?.map((m) => (
          <button key={m.id} type="button" disabled={!nickOk} onClick={() => { saveNick(nick.trim()); nav(`/arena/m/${m.id}`) }}
            className="flex w-full items-center gap-4 rounded-md border border-night-line bg-night-2 p-5 text-left active:scale-[0.99] disabled:opacity-40">
            <span className="flex-1">
              <span className="block text-xl font-semibold">{m.title}</span>
              <span className="mt-1 block text-base leading-snug text-night-mute">{m.brief}</span>
              <span className="mt-3 block text-sm font-semibold text-brand">Ținta: venit net de cel puțin {lei(m.target.min)}</span>
            </span>
            <ChevronRight className="h-6 w-6 shrink-0 text-night-mute" aria-hidden />
          </button>
        ))}
      </div>
      {!nickOk && <p className="mt-3 text-sm text-night-mute">Scrie întâi un pseudonim, între 2 și 20 de caractere.</p>}
    </ArenaShell>
  )
}
