import { useEffect, useReducer, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getCase } from '@/lib/api'
import { caseReducer, initialCaseState } from '@/lib/caseReducer'
import { isMock } from '@/lib/config'
import { mariaEvents, replayEvents, subscribeCaseEvents, type ConnectionState } from '@/lib/events'
import type { Case } from '@/lib/types'
import { withMockGraph } from '@/lib/mockGraph'
import mariaCase from '@shared/fixtures/maria_case.json'

const mockEvents = withMockGraph(mariaEvents)

/**
 * Snapshot-ul dosarului (TanStack Query) + evenimentele live (SSE sau replay).
 * În mock, documentele vin din maria_case.json, iar rezultatele din replay.
 */
export function useCaseLive(caseId: string, replayKey = 0) {
  const mock = isMock()
  const snapshot = useQuery<Case>({
    queryKey: ['case', caseId, mock],
    queryFn: () => (mock ? Promise.resolve(mariaCase as unknown as Case) : getCase(caseId)),
  })

  const [state, dispatch] = useReducer(caseReducer, undefined, () => initialCaseState())
  const [conn, setConn] = useState<ConnectionState>('connecting')

  useEffect(() => {
    if (mock) {
      dispatch({ type: 'reset' })
      return replayEvents(mockEvents, { onEvent: (event) => dispatch({ type: 'event', event }), onState: setConn })
    }
    if (!snapshot.data) return
    dispatch({ type: 'reset', snapshot: snapshot.data })
    return subscribeCaseEvents(caseId, { onEvent: (event) => dispatch({ type: 'event', event }), onState: setConn })
  }, [caseId, mock, snapshot.data, replayKey])

  return { snapshot, state, dispatch, conn, mock }
}
