import { useQuery } from '@tanstack/react-query'
import { getLeaderboard, savedNick } from '@/lib/arena'
import { cn } from '@/lib/utils'
import { ArenaHeading, ArenaShell } from './ArenaShell'
import { usePageMeta } from '@/hooks/usePageMeta'

export function ArenaTop() {
  usePageMeta("Leaderboard · ORB Arena", "The players who got furthest against the bank's AI agents in ORB Arena.")
  const q = useQuery({ queryKey: ['arena-top'], queryFn: getLeaderboard, refetchInterval: 5000 })
  const me = savedNick().toLowerCase()
  return (
    <ArenaShell>
      <div className="flex items-center justify-between gap-3">
        <ArenaHeading>Leaderboard</ArenaHeading>
        {q.data && q.data.top.length > 0 && <span className="text-sm text-night-mute">{q.data.top.length} players</span>}
      </div>
      {q.isError && <p className="mt-3 text-night-danger">The server is not responding.</p>}
      {!!q.data?.top.length && <ol className="mt-4 divide-y divide-night-line overflow-hidden rounded-md border border-night-line">
        {q.data?.top.map((r) => (
          // primii trei au bara galbenă în stânga, ca podiumul de pe proiector
          <li key={r.rank} className={cn('relative flex items-center gap-4 px-5 py-4 text-lg', r.nickname.toLowerCase() === me ? 'bg-brand/10' : 'bg-night-2')}>
            {r.rank <= 3 && <span className={cn('absolute inset-y-0 left-0 bg-brand', r.rank === 1 ? 'w-1.5' : 'w-1 opacity-60')} aria-hidden />}
            <span className={cn('w-8 text-right font-condensed text-2xl font-bold tabular-nums', r.rank <= 3 ? 'text-brand' : 'text-night-mute')}>{r.rank}</span>
            <span className="flex-1 truncate font-medium">{r.nickname}{r.nickname.toLowerCase() === me && <span className="ml-2 rounded-sm bg-brand px-1.5 py-0.5 text-xs font-bold uppercase text-ink">you</span>}</span>
            <span className="font-condensed text-2xl font-bold tabular-nums">{r.points.toLocaleString('en-US')}</span>
          </li>
        ))}
      </ol>}
      {q.data && q.data.top.length === 0 && <p className="mt-4 text-night-mute">Nobody has played yet. Be the first.</p>}
      {q.data && (
        <dl className="mt-6 grid grid-cols-3 gap-px overflow-hidden rounded-md border border-night-line bg-night-line text-center">
          {[[q.data.stats.players, 'players', 'text-night-ink'], [q.data.stats.caught, 'fakes caught', 'text-night-danger'], [q.data.stats.passed, 'got through', 'text-brand']].map(([n, label, tone]) => (
            <div key={label} className="flex flex-col bg-night-2 px-2 py-4">
              <dt className="order-2 mt-1 text-sm text-night-mute">{label}</dt>
              <dd className={cn('order-1 font-condensed text-4xl font-bold leading-none tabular-nums', tone)}>{n}</dd>
            </div>
          ))}
        </dl>
      )}
    </ArenaShell>
  )
}
