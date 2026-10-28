// Arena: rute PUBLICE (fără token). Nu trimitem niciodată tokenul băncii aici.
import { apiUrl } from './config'

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
  const res = await fetch(`${apiUrl()}/api/arena${path}`, init)
  if (!res.ok) {
    let msg = `Eroare ${res.status}`
    try { msg = (await res.json()).detail ?? msg } catch { /* nu e JSON */ }
    if (res.status === 429) msg = 'Prea multe încercări. Mai așteaptă un minut.'
    throw new Error(msg)
  }
  return res.json()
}

export const getMissions = () => call<Mission[]>('/missions')
export const getSubmission = (id: string) => call<Submission>(`/submissions/${encodeURIComponent(id)}`)
export const getLeaderboard = () => call<Leaderboard>('/leaderboard')
export const submissionImageUrl = (id: string) => `${apiUrl()}/api/arena/submissions/${encodeURIComponent(id)}/image`
export const liveUrl = () => `${apiUrl()}/api/arena/live`

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
  paznic: '🛡️ Paznicul', functionar: '📄 Funcționarul', verificator: '🔍 Verificatorul',
  detector: '🤖 Detectorul', detectiv: '🕵️ Detectivul', compliance: '⚖️ Compliance',
}

export const lei = (n: number) => `${Math.round(n).toLocaleString('ro-RO')} lei`
