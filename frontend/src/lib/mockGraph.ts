// Graful Mariei pentru modul mock — aceleași amprente ca în /api/admin/seed-demo.
import type { GraphLink, GraphNode } from './graph'
import type { PipelineEvent } from './types'

const fp = (kind: string, v: string, shared: number): GraphNode =>
  ({ id: `fp:${kind}:${v}`, type: 'fingerprint', kind, label: kind, shared_by: shared, in_cluster: shared >= 2 })

const PHONE = fp('phone', 'hm_9c1e', 6)
const IBAN = fp('iban', 'hm_44ab', 3)

const maria: GraphNode = {
  id: 'case:case_maria', type: 'case', case_id: 'case_maria', label: '[PERSOANA_1]',
  status: 'processing', risk: null, in_cluster: true, is_focus: true,
}

const ring = ['A', 'B', 'C', 'D', 'E'].map((x, i): GraphNode => ({
  id: `case:case_ring_${i + 1}`, type: 'case', case_id: `case_ring_${i + 1}`, label: `[PERSOANA_${x}]`,
  status: i < 2 ? 'escalated' : 'awaiting_review', risk: 0.82 + i * 0.03, in_cluster: true,
}))

const deltas: { message: string; nodes: GraphNode[]; links: GraphLink[] }[] = [
  {
    message: 'Building the graph',
    nodes: [maria, PHONE, IBAN, fp('cnp', 'hm_0f2d', 1), fp('address', 'hm_aa71', 1)],
    links: [
      { source: maria.id, target: PHONE.id, kind: 'phone' },
      { source: maria.id, target: IBAN.id, kind: 'iban' },
      { source: maria.id, target: 'fp:cnp:hm_0f2d', kind: 'cnp' },
      { source: maria.id, target: 'fp:address:hm_aa71', kind: 'address' },
    ],
  },
  ...ring.map((n, i) => ({
    message: `Link found: ${n.label}`,
    nodes: [n],
    links: [
      { source: n.id, target: PHONE.id, kind: 'phone' },
      ...(i === 1 || i === 3 ? [{ source: n.id, target: IBAN.id, kind: 'iban' }] : []),
    ],
  })),
]

/** Bagă evenimentele de graf între start-ul și finalul Detectivului și renumerotează seq. */
export function withMockGraph(events: PipelineEvent[]): PipelineEvent[] {
  const start = events.find((e) => e.type === 'agent_started' && e.agent === 'detectiv')
  const end = events.find((e) => e.type === 'agent_finished' && e.agent === 'detectiv')
  if (!start || !end) return events
  const t0 = Date.parse(start.ts)
  const step = (Date.parse(end.ts) - t0) / (deltas.length + 1)
  const extra: PipelineEvent[] = deltas.map((d, i) => ({
    case_id: start.case_id, seq: 0, ts: new Date(t0 + step * (i + 1)).toISOString(),
    type: 'agent_progress', agent: 'detectiv', message: d.message,
    data: { graph_delta: { nodes: d.nodes, links: d.links } },
  }))
  return [...events, ...extra]
    .sort((a, b) => Date.parse(a.ts) - Date.parse(b.ts) || a.seq - b.seq)
    .map((e, i) => ({ ...e, seq: i }))
}
