import { fetchEventSource, EventStreamContentType } from '@microsoft/fetch-event-source'
import { getToken } from './auth'
import { apiUrl } from './config'
import type { PipelineEvent } from './types'
import mariaEventsRaw from '@shared/fixtures/maria_events.jsonl?raw'

export type ConnectionState = 'connecting' | 'live' | 'reconnecting' | 'replay' | 'closed'

interface Handlers {
  onEvent: (ev: PipelineEvent) => void
  onState?: (s: ConnectionState) => void
}

class FatalError extends Error {}

/**
 * Ascultă evenimentele unui dosar prin SSE.
 * La reconectare trimite Last-Event-ID = ultimul seq primit, ca serverul să trimită doar ce lipsește.
 * Întoarce o funcție de oprire.
 */
export function subscribeCaseEvents(caseId: string, { onEvent, onState }: Handlers): () => void {
  const ctrl = new AbortController()
  let lastSeq = -1
  let attempt = 0

  const run = async () => {
    while (!ctrl.signal.aborted) {
      onState?.(attempt === 0 ? 'connecting' : 'reconnecting')
      const headers: Record<string, string> = {}
      const token = getToken()
      if (token) headers.Authorization = `Bearer ${token}`
      if (lastSeq >= 0) headers['Last-Event-ID'] = String(lastSeq)

      try {
        await fetchEventSource(`${apiUrl()}/api/cases/${encodeURIComponent(caseId)}/events`, {
          signal: ctrl.signal,
          headers,
          openWhenHidden: true, // nu închide stream-ul când tab-ul e în fundal (proiector!)
          async onopen(res) {
            if (res.ok && res.headers.get('content-type')?.startsWith(EventStreamContentType)) {
              attempt = 0
              onState?.('live')
              return
            }
            if (res.status === 401 || res.status === 403 || res.status === 404) {
              throw new FatalError(`SSE ${res.status}`)
            }
            throw new Error(`SSE ${res.status}`)
          },
          onmessage(msg) {
            if (!msg.data) return
            let ev: PipelineEvent
            try { ev = JSON.parse(msg.data) } catch { return }
            if (ev.type === 'ping') return
            if (ev.seq > lastSeq) lastSeq = ev.seq
            onEvent(ev)
          },
          onclose() { throw new Error('closed') }, // serverul a închis → reconectăm
          onerror(err) { throw err }, // reconectarea o facem noi, cu Last-Event-ID nou
        })
      } catch (err) {
        if (ctrl.signal.aborted) break
        if (err instanceof FatalError) { onState?.('closed'); break }
      }
      attempt++
      const delay = Math.min(1000 * 2 ** Math.min(attempt, 4), 10000)
      await new Promise((r) => setTimeout(r, delay))
    }
  }
  run()
  return () => { ctrl.abort(); onState?.('closed') }
}

export const mariaEvents: PipelineEvent[] = mariaEventsRaw
  .split('\n')
  .filter((l) => l.trim())
  .map((l) => JSON.parse(l))

/** Redă evenimentele cu întârzierile originale (din `ts`). speed = 2 → de două ori mai repede. */
export function replayEvents(
  events: PipelineEvent[], { onEvent, onState }: Handlers, speed = 1,
): () => void {
  const timers: number[] = []
  onState?.('replay')
  const t0 = Date.parse(events[0]?.ts ?? '')
  events.forEach((ev) => {
    const delay = (Date.parse(ev.ts) - t0) / speed
    timers.push(window.setTimeout(() => onEvent(ev), Math.max(0, delay)))
  })
  return () => timers.forEach(clearTimeout)
}
