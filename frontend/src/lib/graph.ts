// Forma grafului trimis de Detectiv (backend/app/agents/detectiv/graph.py).

export interface GraphNode {
  id: string
  type: 'case' | 'fingerprint'
  label: string
  in_cluster: boolean
  // dosar
  case_id?: string
  status?: string
  risk?: number | null
  created_at?: string
  is_focus?: boolean
  // amprentă
  kind?: string
  shared_by?: number
}

export interface GraphLink { source: string; target: string; kind: string }

export interface GraphData { nodes: GraphNode[]; links: GraphLink[] }

export const emptyGraph: GraphData = { nodes: [], links: [] }

/** Adaugă o bucată de graf (din SSE), fără duplicate. */
export function mergeGraph(g: GraphData, delta: Partial<GraphData>): GraphData {
  const nodes = new Map(g.nodes.map((n) => [n.id, n]))
  for (const n of delta.nodes ?? []) nodes.set(n.id, { ...nodes.get(n.id), ...n })
  const key = (l: GraphLink) => `${l.source}→${l.target}`
  const links = new Map(g.links.map((l) => [key(l), l]))
  for (const l of delta.links ?? []) if (nodes.has(l.source) && nodes.has(l.target)) links.set(key(l), l)
  return { nodes: [...nodes.values()], links: [...links.values()] }
}
