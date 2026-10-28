import { useQuery } from '@tanstack/react-query'
import { getLeaderboard, savedNick } from '@/lib/arena'
import { cn } from '@/lib/utils'
import { ArenaShell } from './ArenaShell'

const MEDAL = ['🥇', '🥈', '🥉']

export function ArenaTop() {
  const q = useQuery({ queryKey: ['arena-top'], queryFn: getLeaderboard, refetchInterval: 5000 })
  const me = savedNick().toLowerCase()
  return (
    <ArenaShell>
      <h2 className="text-2xl font-bold">🏆 Clasament</h2>
      {q.isError && <p className="mt-3 text-red-400">Serverul nu răspunde.</p>}
      <ol className="mt-4 space-y-2">
        {q.data?.top.map((r) => (
          <li key={r.rank} className={cn('flex items-center gap-3 rounded-xl border p-4 text-lg',
            r.nickname.toLowerCase() === me ? 'border-amber-400 bg-amber-400/10' : 'border-slate-800 bg-slate-900')}>
            <span className="w-9 text-center text-2xl">{MEDAL[r.rank - 1] ?? r.rank}</span>
            <span className="flex-1 truncate font-semibold">{r.nickname}</span>
            <span className="tabular-nums font-bold">{r.points.toLocaleString('ro-RO')}</span>
          </li>
        ))}
        {q.data && q.data.top.length === 0 && <p className="text-slate-400">Nimeni încă. Fii primul!</p>}
      </ol>
      {q.data && (
        <p className="mt-6 text-center text-base text-slate-400">
          {q.data.stats.players} jucători · {q.data.stats.caught} falsuri prinse · {q.data.stats.passed} au trecut
        </p>
      )}
    </ArenaShell>
  )
}
