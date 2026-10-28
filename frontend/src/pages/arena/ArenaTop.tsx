import { useQuery } from '@tanstack/react-query'
import { getLeaderboard, savedNick } from '@/lib/arena'
import { cn } from '@/lib/utils'
import { ArenaShell } from './ArenaShell'

export function ArenaTop() {
  const q = useQuery({ queryKey: ['arena-top'], queryFn: getLeaderboard, refetchInterval: 5000 })
  const me = savedNick().toLowerCase()
  return (
    <ArenaShell>
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-2xl font-semibold">Leaderboard</h2>
        {q.data && q.data.top.length > 0 && <span className="text-sm text-night-mute">{q.data.top.length} players</span>}
      </div>
      {q.isError && <p className="mt-3 text-night-danger">The server is not responding.</p>}
      <ol className="mt-4 divide-y divide-night-line overflow-hidden rounded-md border border-night-line">
        {q.data?.top.map((r) => (
          <li key={r.rank} className={cn('flex items-center gap-4 px-4 py-4 text-lg', r.nickname.toLowerCase() === me ? 'bg-brand/10' : 'bg-night-2')}>
            <span className={cn('w-8 text-right font-condensed text-2xl font-bold tabular-nums', r.rank <= 3 ? 'text-brand' : 'text-night-mute')}>{r.rank}</span>
            <span className="flex-1 truncate font-medium">{r.nickname}{r.nickname.toLowerCase() === me && <span className="ml-2 text-sm text-brand">you</span>}</span>
            <span className="font-semibold tabular-nums">{r.points.toLocaleString('ro-RO')}</span>
          </li>
        ))}
      </ol>
      {q.data && q.data.top.length === 0 && <p className="mt-4 text-night-mute">Nobody has played yet. Be the first.</p>}
      {q.data && (
        <p className="mt-6 text-center text-base text-night-mute">
          {q.data.stats.players} players, {q.data.stats.caught} fakes caught, {q.data.stats.passed} got through
        </p>
      )}
    </ArenaShell>
  )
}
