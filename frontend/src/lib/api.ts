import { getToken, logout } from './auth'
import { apiUrl } from './config'
import type { GraphData } from './graph'
import type { Case, Decision, DecisionAction } from './types'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers)
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const res = await fetch(`${apiUrl()}${path}`, { ...init, headers })
  if (res.status === 401) {
    logout()
    window.location.assign('/login')
  }
  if (!res.ok) throw new ApiError(res.status, `${res.status} ${res.statusText}`)
  return res
}

export async function getCase(id: string): Promise<Case> {
  return (await apiFetch(`/api/cases/${encodeURIComponent(id)}`)).json()
}

export async function postDecision(
  id: string,
  body: { action: DecisionAction; notes?: string; decided_by: string },
): Promise<Decision> {
  const res = await apiFetch(`/api/cases/${encodeURIComponent(id)}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return res.json()
}

/** Imaginile cer Authorization, deci le luăm ca blob, nu cu <img src>. */
export async function getDocumentImage(
  caseId: string, docId: string, view: 'original' | 'redacted' | 'ela', page = 1,
): Promise<string> {
  const res = await apiFetch(
    `/api/cases/${encodeURIComponent(caseId)}/documents/${encodeURIComponent(docId)}/image?view=${view}&page=${page}`,
  )
  return URL.createObjectURL(await res.blob())
}

export async function getGraph(caseId?: string): Promise<GraphData> {
  const q = caseId ? `?case_id=${encodeURIComponent(caseId)}` : ''
  return (await apiFetch(`/api/graph${q}`)).json()
}
