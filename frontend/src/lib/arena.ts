// Arena: rute PUBLICE (fără token). Nu trimitem niciodată tokenul băncii aici.
import { fetchEventSource, EventStreamContentType } from '@microsoft/fetch-event-source'
import { API_HEADERS, apiUrl } from './config'

export interface FieldSpec {
  type: 'number' | 'select' | 'date' | 'text'
  label: string
  min?: number
  max?: number
  options?: string[]
}

export interface Mission {
  id: string
  title: string
  brief: string
  doc_type: string
  target: { field: string; min: number }
  template: Record<string, string | number>
  editable: Record<string, FieldSpec>
  tricks: Record<string, string>
}

export interface Submission {
  id: string
  nickname: string
  mission_id: string
  mission_title: string
  outcome: 'passed' | 'caught' | 'invalid'
  points: number
  duplicate: boolean
  target_met: boolean
  caught_by: string[]
  reasons: string[]
  risk: number
  changed: string[]
  ms: number
  ts: string
}

export interface LeaderRow { rank: number; nickname: string; points: number }
export interface ArenaStats { submissions: number; valid: number; passed: number; caught: number; players: number }
export interface Leaderboard { top: LeaderRow[]; feed: Submission[]; stats: ArenaStats }

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  for (const [k, v] of Object.entries(API_HEADERS)) headers.set(k, v)
  const res = await fetch(`${apiUrl()}/api/arena${path}`, { ...init, headers })
  if (!res.ok) {
    let msg = `Error ${res.status}`
    try {
      const d = (await res.json()).detail
      msg = typeof d === 'string' ? d : 'Invalid fields. Check the values and try again.'
    } catch { /* nu e JSON */ }
    if (res.status === 429) msg = 'Too many attempts. Wait a minute.'
    throw new Error(msg)
  }
  return res.json()
}

export const getMissions = () => call<Mission[]>('/missions')
export const getSubmission = (id: string) => call<Submission>(`/submissions/${encodeURIComponent(id)}`)
/** Toți jucătorii (până la 500), nu doar primii 10. */
export const getLeaderboard = () => call<Leaderboard>('/leaderboard?limit=500')
/** Imaginea falsului, cerută cu headerele noastre (un <img src> simplu nu le poate trimite prin ngrok). */
export async function getSubmissionImage(id: string): Promise<string> {
  const res = await fetch(`${apiUrl()}/api/arena/submissions/${encodeURIComponent(id)}/image`, { headers: API_HEADERS })
  if (!res.ok) throw new Error(`Error ${res.status}`)
  return URL.createObjectURL(await res.blob())
}

export interface LiveMessage { event: string; data: { message: string; data?: Record<string, unknown> | null } }

/**
 * Fluxul live al Arenei (pentru proiector). fetchEventSource în loc de EventSource,
 * ca să putem trimite headerul cerut de ngrok; reconectare cu pauză crescătoare.
 */
export function subscribeArenaLive(handlers: {
  onMessage: (m: LiveMessage) => void
  onOpen?: () => void
  onDown?: () => void
}): () => void {
  const ctrl = new AbortController()
  let attempt = 0
  const run = async () => {
    while (!ctrl.signal.aborted) {
      try {
        await fetchEventSource(`${apiUrl()}/api/arena/live`, {
          signal: ctrl.signal,
          headers: API_HEADERS,
          openWhenHidden: true, // proiectorul poate sta în fundal
          async onopen(res) {
            if (res.ok && res.headers.get('content-type')?.startsWith(EventStreamContentType)) {
              attempt = 0
              handlers.onOpen?.()
              return
            }
            throw new Error(`SSE ${res.status}`)
          },
          onmessage(msg) {
            if (!msg.data || !msg.event || msg.event === 'ping') return
            try { handlers.onMessage({ event: msg.event, data: JSON.parse(msg.data) }) } catch { /* mesaj stricat */ }
          },
          onclose() { throw new Error('closed') },
          onerror(err) { throw err },
        })
      } catch {
        if (ctrl.signal.aborted) break
      }
      handlers.onDown?.()
      attempt++
      await new Promise((r) => setTimeout(r, Math.min(1000 * 2 ** Math.min(attempt, 4), 10000)))
    }
  }
  run()
  return () => ctrl.abort()
}

export function submitFake(body: { nickname: string; mission_id: string; edits: Record<string, unknown>; tricks: string[] }) {
  return call<Submission>('/submissions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

const NICK_KEY = 'orb.arena.nick'
export function savedNick(): string {
  try { return localStorage.getItem(NICK_KEY) ?? '' } catch { return '' }
}
export function saveNick(n: string) {
  try { localStorage.setItem(NICK_KEY, n) } catch { /* mod privat */ }
}

export const AGENT_RO: Record<string, string> = {
  paznic: 'Guard', functionar: 'Clerk', verificator: 'Verifier',
  detector: 'Detector', detectiv: 'Detective', compliance: 'Compliance',
}

export const lei = (n: number) => `${Math.round(n).toLocaleString('ro-RO')} lei`

// Statistici locale ale jucătorului (doar pe telefonul lui), pentru cardul de rezultat.
const STATS_KEY = 'orb.arena.stats'
export interface MyStats { attempts: number; passed: number; caught: number; ids: string[] }

export function myStats(): MyStats {
  try {
    const s = JSON.parse(localStorage.getItem(STATS_KEY) ?? '') as MyStats
    if (Array.isArray(s.ids)) return s
  } catch { /* gol sau mod privat */ }
  return { attempts: 0, passed: 0, caught: 0, ids: [] }
}

/** Numără o încercare o singură dată (reîncărcarea paginii nu o dublează). */
export function recordAttempt(s: Submission): MyStats {
  const st = myStats()
  if (st.ids.includes(s.id) || s.outcome === 'invalid') return st
  const next = {
    attempts: st.attempts + 1,
    passed: st.passed + (s.outcome === 'passed' ? 1 : 0),
    caught: st.caught + (s.outcome === 'caught' ? 1 : 0),
    ids: [...st.ids, s.id].slice(-50),
  }
  try { localStorage.setItem(STATS_KEY, JSON.stringify(next)) } catch { /* mod privat */ }
  return next
}
