import { useQuery } from '@tanstack/react-query'
import { AlertOctagon, Check, CircleHelp, Loader2, RotateCcw, Share2, Trophy } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { getSubmission, getSubmissionImage, myStats, recordAttempt, type MyStats, type Submission } from '@/lib/arena'
import { AGENT_INFO } from '@/lib/labels'
import type { AgentName } from '@/lib/types'
import { cn } from '@/lib/utils'
import { ArenaShell } from './ArenaShell'

const CHECKERS: AgentName[] = ['paznic', 'verificator', 'detector']

// Ce spune fiecare agent când te prinde: scurt, pe înțeles, puțin ironic.
const CAUGHT_LINE: Partial<Record<AgentName, string>> = {
  verificator: 'Am refăcut calculul taxelor. Matematica nu minte.',
  detector: 'Am văzut pe unde ai lipit.',
  paznic: 'Am citit și textul ascuns. Nu ține.',
  functionar: 'Datele de pe acte nu se leagă între ele.',
}

const CAUGHT_TITLES = ['Te-au prins', 'Aproape. Dar nu.', 'ORB 1, tu 0', 'Frumoasă încercare']

function pick<T>(list: T[], seed: string): T {
  let h = 0
  for (const ch of seed) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return list[h % list.length]
}

export function ArenaResult() {
  const { sid = '' } = useParams()
  const fromForge = useLocation().state as Submission | null
  const q = useQuery({ queryKey: ['arena-sub', sid], queryFn: () => getSubmission(sid), initialData: fromForge ?? undefined })
  const s = q.data
  // agenții „verifică” pe rând, apoi apare verdictul (doar imediat după trimitere)
  const [step, setStep] = useState(fromForge ? 0 : CHECKERS.length)
  useEffect(() => {
    if (step >= CHECKERS.length) return
    const t = setTimeout(() => setStep((x) => x + 1), 600)
    return () => clearTimeout(t)
  }, [step])
  const stats = useMemo<MyStats>(() => (s ? recordAttempt(s) : myStats()), [s])

  if (q.isError) return <ArenaShell><p className="text-night-danger">Încercarea nu mai există.</p></ArenaShell>
  if (!s) return <ArenaShell><p className="text-night-mute">Se încarcă rezultatul.</p></ArenaShell>
  const done = step >= CHECKERS.length
  const catchers = (s.caught_by as AgentName[]).filter((a) => AGENT_INFO[a])

  return (
    <ArenaShell>
      <ol className="grid grid-cols-3 gap-2" aria-label="Agenții care au verificat">
        {CHECKERS.map((a, i) => {
          const checked = i < step
          const caught = checked && s.caught_by.includes(a)
          const Icon = AGENT_INFO[a].icon
          return (
            <li key={a} className={cn('rounded-md border p-3 text-center transition-colors',
              !checked ? 'border-night-line text-night-mute' : caught ? 'border-night-danger bg-night-danger/10' : 'border-night-ok/60 bg-night-ok/10')}>
              <Icon className="mx-auto h-5 w-5" aria-hidden />
              <div className="mt-1 text-sm font-semibold">{AGENT_INFO[a].label}</div>
              <div className={cn('mt-1 flex items-center justify-center gap-1 text-xs', caught ? 'text-night-danger' : checked ? 'text-night-ok' : '')}>
                {!checked ? <><Loader2 className="h-3 w-3 animate-spin" aria-hidden />verifică</>
                  : caught ? <><AlertOctagon className="h-3 w-3" aria-hidden />te-a prins</>
                  : <><Check className="h-3 w-3" aria-hidden />a trecut</>}
              </div>
            </li>
          )
        })}
      </ol>

      {done && (
        <section className="mt-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
          {s.outcome === 'passed' && (
            <div className="rounded-md border border-brand/70 bg-brand/10 p-6 text-center">
              <Trophy className="mx-auto h-12 w-12 text-brand" aria-hidden />
              <div className="mt-3 text-3xl font-bold">Ai păcălit ORB</div>
              {s.points > 0 && <div className="mt-1 font-condensed text-3xl font-bold text-brand">+{s.points} puncte</div>}
              <p className="mt-3 text-base leading-relaxed text-night-mute">
                Niciun agent nu a văzut falsul. Echipa băncii primește acum falsul tău, iar agenții învață din el o regulă nouă.
                Încearcă din nou: s-ar putea să nu mai treacă.
              </p>
            </div>
          )}

          {s.outcome === 'caught' && (
            <div className="rounded-md border border-night-danger/70 bg-night-danger/10 p-6">
              <div className="text-3xl font-bold">{pick(CAUGHT_TITLES, s.id)}</div>
              <div className="mt-1 text-base text-night-mute">
                {catchers.length === 1 ? 'Te-a prins un singur agent, a fost aproape. ' : ''}+{s.points} puncte pentru încercare
              </div>

              <h3 className="mt-5 text-base font-semibold">De ce te-am prins</h3>
              <ul className="mt-2 space-y-2">
                {catchers.map((a) => {
                  const Icon = AGENT_INFO[a].icon
                  return (
                    <li key={a} className="flex gap-3 rounded-md border border-night-line bg-night-2 p-4">
                      <Icon className="mt-0.5 h-5 w-5 shrink-0 text-night-danger" aria-hidden />
                      <div>
                        <div className="font-semibold">{AGENT_INFO[a].label}</div>
                        <div className="text-base italic text-night-mute">„{CAUGHT_LINE[a] ?? 'Ceva nu se potrivea.'}”</div>
                      </div>
                    </li>
                  )
                })}
              </ul>
              {s.reasons.length > 0 && (
                <>
                  <h3 className="mt-5 text-base font-semibold">Ce au găsit, concret</h3>
                  <ul className="mt-2 divide-y divide-night-line rounded-md border border-night-line">
                    {s.reasons.map((r, i) => <li key={`${i}-${r}`} className="px-4 py-3 text-base">{r}</li>)}
                  </ul>
                </>
              )}
            </div>
          )}

          {s.outcome === 'invalid' && (
            <div className="rounded-md border border-brand/60 bg-brand/10 p-6 text-center">
              <CircleHelp className="mx-auto h-9 w-9 text-brand" aria-hidden />
              <div className="mt-2 text-2xl font-bold">Falsul nu e valid</div>
              <p className="mt-2 text-base text-night-mute">
                {s.target_met ? 'Nu ai modificat nimic față de șablon.' : 'Documentul nu atinge venitul cerut de misiune. Mărește salariul net.'}
              </p>
            </div>
          )}
          {s.duplicate && <p className="mt-3 text-center text-sm text-night-mute">Cineva a trimis deja exact același fals, așa că nu primești puncte.</p>}

          <div className="mt-6 grid grid-cols-2 gap-3">
            <Link to={`/arena/m/${s.mission_id}`} className="flex h-14 items-center justify-center gap-2 whitespace-nowrap rounded-md bg-brand text-base font-bold text-ink">
              <RotateCcw className="h-5 w-5" aria-hidden /> Încearcă din nou
            </Link>
            <Link to="/arena/top" className="flex h-14 items-center justify-center gap-2 whitespace-nowrap rounded-md border border-night-line text-base font-semibold">
              <Trophy className="h-5 w-5" aria-hidden /> Clasament
            </Link>
          </div>

          <ScoreCard nick={s.nickname} stats={stats} />
          <SubmissionImage id={s.id} />
        </section>
      )}
    </ArenaShell>
  )
}

/** Cardul de arătat altora: câte încercări, câte au trecut, plus butonul de trimis. */
function ScoreCard({ nick, stats }: { nick: string; stats: MyStats }) {
  const [copied, setCopied] = useState(false)
  if (!stats.attempts) return null
  const line = stats.passed
    ? `Am păcălit ORB de ${stats.passed} ${stats.passed === 1 ? 'dată' : 'ori'} din ${stats.attempts} încercări.`
    : `ORB m-a prins de ${stats.caught} ${stats.caught === 1 ? 'dată' : 'ori'}. Încă încerc.`
  const url = `${window.location.origin}/arena`

  async function share() {
    const text = `${line} Tu poți păcăli agenții băncii?`
    try {
      if (navigator.share) { await navigator.share({ title: 'ORB Arena', text, url }); return }
      await navigator.clipboard.writeText(`${text} ${url}`)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    } catch { /* anulat de utilizator */ }
  }

  return (
    <div className="mt-6 rounded-md border border-night-line bg-gradient-to-br from-night-2 to-night p-5">
      <div className="flex items-center gap-3">
        <span className="grid h-9 w-9 place-items-center rounded-sm bg-brand font-condensed text-lg font-bold text-ink">O</span>
        <div className="leading-tight">
          <div className="font-semibold">{nick} contra ORB</div>
          <div className="text-sm text-night-mute">ORB Arena</div>
        </div>
      </div>
      <p className="mt-4 text-xl font-semibold leading-snug">{line}</p>
      <div className="mt-3 flex gap-6 text-sm text-night-mute">
        <span><b className="font-condensed text-2xl text-night-ink">{stats.attempts}</b> încercări</span>
        <span><b className="font-condensed text-2xl text-brand">{stats.passed}</b> au trecut</span>
        <span><b className="font-condensed text-2xl text-night-danger">{stats.caught}</b> prinse</span>
      </div>
      <button type="button" onClick={share}
        className="mt-4 flex h-12 w-full items-center justify-center gap-2 rounded-md border border-night-line text-base font-semibold hover:border-night-mute">
        <Share2 className="h-4 w-4" aria-hidden /> {copied ? 'Copiat. Lipește-l unde vrei.' : 'Provoacă pe cineva'}
      </button>
    </div>
  )
}

/** Imaginea falsului: cerută cu fetch (headerul pentru ngrok), apoi afișată din memorie. */
function SubmissionImage({ id }: { id: string }) {
  const q = useQuery({ queryKey: ['arena-img', id], queryFn: () => getSubmissionImage(id), staleTime: Infinity, gcTime: 60_000 })
  useEffect(() => () => { if (q.data) URL.revokeObjectURL(q.data) }, [q.data])
  if (q.isError) return <p className="mt-6 text-sm text-night-mute">Imaginea falsului nu s-a încărcat.</p>
  if (!q.data) return <div className="mt-6 aspect-[1654/2339] w-full animate-pulse rounded-sm bg-night-2" />
  return (
    <figure className="mt-6">
      <figcaption className="mb-2 text-sm text-night-mute">Falsul tău, așa cum l-au primit agenții</figcaption>
      <img src={q.data} alt="Falsul tău" className="w-full rounded-sm border border-night-line" />
    </figure>
  )
}
