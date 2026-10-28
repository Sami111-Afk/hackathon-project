import { useQuery } from '@tanstack/react-query'
import { getLeaderboard, savedNick } from '@/lib/arena'
import { cn } from '@/lib/utils'
import { ArenaShell } from './ArenaShell'

export function ArenaTop() {
  const q = useQuery({ queryKey: ['arena-top'], queryFn: getLeaderboard, refetchInterval: 5000 })
  const me = savedNick().toLowerCase()
  return (
    <ArenaShell>
      <h2 className="text-2xl font-semibold">Clasament</h2>
      {q.isError && <p className="mt-3 text-night-danger">Serverul nu răspunde.</p>}
      <ol className="mt-4 divide-y divide-night-line overflow-hidden rounded-md border border-night-line">
        {q.data?.top.map((r) => (
          <li key={r.rank} className={cn('flex items-center gap-4 px-4 py-4 text-lg', r.nickname.toLowerCase() === me ? 'bg-brand/10' : 'bg-night-2')}>
            <span className={cn('w-8 text-right font-condensed text-2xl font-bold tabular-nums', r.rank <= 3 ? 'text-brand' : 'text-night-mute')}>{r.rank}</span>
            <span className="flex-1 truncate font-medium">{r.nickname}{r.nickname.toLowerCase() === me && <span className="ml-2 text-sm text-brand">tu</span>}</span>
            <span className="font-semibold tabular-nums">{r.points.toLocaleString('ro-RO')}</span>
          </li>
        ))}
      </ol>
      {q.data && q.data.top.length === 0 && <p className="mt-4 text-night-mute">Nimeni nu a jucat încă. Fii primul.</p>}
      {q.data && (
        <p className="mt-6 text-center text-base text-night-mute">
          {q.data.stats.players} jucători, {q.data.stats.caught} falsuri prinse, {q.data.stats.passed} au trecut
        </p>
      )}
    </ArenaShell>
  )
}
