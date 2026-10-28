import { useQuery } from '@tanstack/react-query'
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
        <span className="text-base text-slate-300">Pseudonimul tău (apare pe ecranul mare)</span>
        <input
          value={nick}
          onChange={(e) => setNick(e.target.value)}
          maxLength={20}
          placeholder="ex. Hackerul-Vesel"
          className="mt-2 h-14 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 text-xl outline-none focus:border-amber-400"
        />
      </label>

      <h2 className="mt-8 text-xl font-bold">Alege o misiune</h2>
      {missions.isLoading && <p className="mt-3 text-slate-400">Se încarcă…</p>}
      {missions.isError && <p className="mt-3 text-red-400">Serverul nu răspunde. Încearcă din nou peste câteva secunde.</p>}
      <div className="mt-3 space-y-3">
        {missions.data?.map((m) => (
          <button
            key={m.id}
            type="button"
            disabled={!nickOk}
            onClick={() => { saveNick(nick.trim()); nav(`/arena/m/${m.id}`) }}
            className="w-full rounded-2xl border border-slate-700 bg-slate-900 p-5 text-left active:scale-[0.99] disabled:opacity-50"
          >
            <div className="text-xl font-bold">{m.title}</div>
            <div className="mt-1 text-base text-slate-300">{m.brief}</div>
            <div className="mt-3 inline-block rounded-full bg-amber-400/15 px-3 py-1 text-sm font-semibold text-amber-300">
              🎯 net ≥ {lei(m.target.min)}
            </div>
          </button>
        ))}
      </div>
      {!nickOk && <p className="mt-3 text-sm text-slate-400">Scrie întâi un pseudonim (2–20 caractere).</p>}
    </ArenaShell>
  )
}
