import { useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D, { type ForceGraphMethods, type NodeObject } from 'react-force-graph-2d'
import type { GraphData, GraphNode } from '@/lib/graph'

const FP_ICON: Record<string, string> = { phone: '📞', iban: '💳', email: '✉️', address: '🏠', cnp: '🪪', name: '👤', cui: '🏢' }
const FP_LABEL: Record<string, string> = {
  phone: 'telefon', iban: 'cont', email: 'email', address: 'adresă', cnp: 'CNP', name: 'nume', cui: 'angajator',
}

type N = NodeObject & GraphNode

/**
 * Rețeaua Detectivului. Nodurile se adaugă live; obiectele se refolosesc după id,
 * ca graful să nu se reașeze de la zero la fiecare legătură nouă.
 */
export function NetworkGraph({ graph, height = 420 }: { graph: GraphData; height?: number }) {
  const wrap = useRef<HTMLDivElement>(null)
  const fg = useRef<ForceGraphMethods<N> | undefined>(undefined)
  const cache = useRef(new Map<string, N>())
  const [width, setWidth] = useState(600)

  useEffect(() => {
    const el = wrap.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => setWidth(Math.floor(e.contentRect.width)))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const data = useMemo(() => {
    const nodes = graph.nodes.map((n) => {
      const prev = cache.current.get(n.id)
      const obj = prev ? Object.assign(prev, n) : ({ ...n } as N)
      cache.current.set(n.id, obj)
      return obj
    })
    // link-uri noi la fiecare render: force-graph le înlocuiește source/target cu obiecte
    return { nodes, links: graph.links.map((l) => ({ ...l })) }
  }, [graph])

  useEffect(() => {
    // noduri mai depărtate: etichetele nu se mai suprapun
    fg.current?.d3Force('charge')?.strength(-260)
    const link = fg.current?.d3Force('link') as { distance?: (d: number) => unknown } | undefined
    link?.distance?.(70)
    if (data.nodes.length) setTimeout(() => fg.current?.zoomToFit(400, 70), 900)
  }, [data.nodes.length])

  const ringSize = graph.nodes.filter((n) => n.type === 'case' && n.in_cluster).length

  return (
    <div ref={wrap} className="relative w-full overflow-hidden rounded-lg border bg-slate-950">
      {graph.nodes.length === 0 ? (
        <div className="flex items-center justify-center text-slate-400" style={{ height }}>
          Detectivul încă nu a găsit legături.
        </div>
      ) : (
        <ForceGraph2D<N>
          ref={fg}
          width={width}
          height={height}
          graphData={data}
          cooldownTicks={120}
          linkColor={(l) => ((l as { kind: string }).kind === 'phone' || (l as { kind: string }).kind === 'iban'
            ? 'rgba(248,113,113,0.8)' : 'rgba(148,163,184,0.4)')}
          linkWidth={(l) => ((l as { kind: string }).kind === 'phone' || (l as { kind: string }).kind === 'iban' ? 2.5 : 1)}
          nodeLabel={(n) => (n.type === 'case'
            ? `${n.label} · ${n.case_id}${n.risk != null ? ` · risc ${Math.round(n.risk * 100)}` : ''}`
            : `${FP_LABEL[n.kind ?? ''] ?? n.kind} comun la ${n.shared_by} dosare`)}
          nodeCanvasObject={(n, ctx, scale) => {
            const x = n.x ?? 0
            const y = n.y ?? 0
            const font = (px: number) => `${px / scale}px sans-serif`
            if (n.type === 'case') {
              const r = (n.is_focus ? 13 : 9) / scale // dimensiune fixă pe ecran, indiferent de zoom
              ctx.beginPath()
              ctx.arc(x, y, r, 0, 2 * Math.PI)
              ctx.fillStyle = n.is_focus ? '#facc15' : n.in_cluster ? '#ef4444' : '#64748b'
              ctx.fill()
              if (n.is_focus) { ctx.lineWidth = 3 / scale; ctx.strokeStyle = '#fff'; ctx.stroke() }
              ctx.fillStyle = '#e2e8f0'
              ctx.font = font(13)
              ctx.textAlign = 'center'
              ctx.textBaseline = 'top'
              ctx.fillText(n.is_focus ? `${n.label} (acest dosar)` : n.label, x, y + r + 4 / scale)
            } else {
              ctx.font = font(n.in_cluster ? 24 : 16)
              ctx.textAlign = 'center'
              ctx.textBaseline = 'middle'
              ctx.globalAlpha = n.in_cluster ? 1 : 0.5
              ctx.fillText(FP_ICON[n.kind ?? ''] ?? '•', x, y)
              ctx.globalAlpha = 1
            }
          }}
          nodePointerAreaPaint={(n, color, ctx) => {
            ctx.fillStyle = color
            ctx.beginPath()
            ctx.arc(n.x ?? 0, n.y ?? 0, 14, 0, 2 * Math.PI)
            ctx.fill()
          }}
        />
      )}
      <div className="pointer-events-none absolute left-3 top-3 space-y-1 rounded-md bg-slate-900/80 px-3 py-2 text-sm text-slate-200">
        <div><span className="mr-1 inline-block h-3 w-3 rounded-full bg-yellow-400 align-middle" /> acest dosar</div>
        <div><span className="mr-1 inline-block h-3 w-3 rounded-full bg-red-500 align-middle" /> rețea suspectă ({Math.max(0, ringSize - 1)} dosare)</div>
        <div><span className="mr-1 inline-block h-3 w-3 rounded-full bg-slate-500 align-middle" /> alte dosare</div>
        <div>📞 telefon · 💳 cont · 🏠 adresă · 🪪 CNP · 👤 nume · 🏢 angajator</div>
      </div>
    </div>
  )
}
