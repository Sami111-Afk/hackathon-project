import type { AgentName, AgentResult, AgentStatus, Case, Decision, PipelineEvent, Verdict } from './types'
import { AGENTS } from './types'
import { emptyGraph, mergeGraph, type GraphData } from './graph'

export interface AgentLane {
  status: AgentStatus
  message: string
  result?: AgentResult
}

export interface CaseLiveState {
  lastSeq: number
  agents: Record<AgentName, AgentLane>
  feed: PipelineEvent[] // tot ce a „spus” biroul, în ordine
  verdict: Verdict | null
  decision: Decision | null
  graph: GraphData // rețeaua Detectivului, construită live din agent_progress
}

export function initialCaseState(snapshot?: Case | null): CaseLiveState {
  const agents = Object.fromEntries(
    AGENTS.map((a) => [a, { status: 'pending', message: '' } as AgentLane]),
  ) as Record<AgentName, AgentLane>
  for (const r of snapshot?.results ?? []) {
    agents[r.agent] = { status: r.status, message: '', result: r }
  }
  return {
    lastSeq: -1,
    agents,
    feed: [],
    verdict: snapshot?.verdict ?? null,
    decision: snapshot?.decision ?? null,
    graph: emptyGraph,
  }
}

export type CaseAction =
  | { type: 'event'; event: PipelineEvent }
  | { type: 'reset'; snapshot?: Case | null }
  | { type: 'decided'; decision: Decision }
  | { type: 'graph'; graph: GraphData }

export function caseReducer(state: CaseLiveState, action: CaseAction): CaseLiveState {
  if (action.type === 'reset') return initialCaseState(action.snapshot)
  if (action.type === 'decided') return { ...state, decision: action.decision }
  if (action.type === 'graph') return { ...state, graph: mergeGraph(state.graph, action.graph) }

  const ev = action.event
  if (ev.seq <= state.lastSeq) return state // duplicat (replay după reconectare)

  const next: CaseLiveState = { ...state, lastSeq: ev.seq, feed: [...state.feed, ev] }
  const agent = ev.agent

  switch (ev.type) {
    case 'case_created':
      return { ...initialCaseState(), lastSeq: ev.seq, feed: [ev] }
    case 'agent_started':
    case 'agent_progress':
      if (agent) next.agents = { ...state.agents, [agent]: { ...state.agents[agent], status: 'running', message: ev.message } }
      if (ev.data && 'graph_delta' in ev.data) next.graph = mergeGraph(state.graph, ev.data.graph_delta as GraphData)
      break
    case 'agent_finished':
    case 'agent_error': {
      if (!agent) break
      const result = ev.data as unknown as AgentResult | undefined
      next.agents = {
        ...state.agents,
        [agent]: {
          status: ev.type === 'agent_error' ? 'error' : (result?.status ?? 'done'),
          message: ev.message,
          result,
        },
      }
      break
    }
    case 'verdict':
      next.verdict = ev.data as unknown as Verdict
      break
    case 'decision':
      next.decision = ev.data as unknown as Decision
      break
  }
  return next
}
