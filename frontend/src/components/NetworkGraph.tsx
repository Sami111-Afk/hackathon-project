import { useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D, { type ForceGraphMethods, type NodeObject } from 'react-force-graph-2d'
import type { GraphData, GraphNode } from '@/lib/graph'

// Amprentele se desenează ca etichete scurte, nu ca emoji.
const FP_TAG: Record<string, string> = { phone: 'tel', iban: 'IBAN', email: 'email', address: 'adr', cnp: 'CNP', name: 'nume', cui: 'CUI' }
const FP_LABEL: Record<string, string> = {
  phone: 'telefon', iban: 'cont', email: 'email', address: 'adresă', cnp: 'CNP', name: 'nume', cui: 'angajator',
}
const C = { focus: '#FFE600', ring: '#F04438', other: '#98A2B3', text: '#E4E7EC', linkStrong: 'rgba(240,68,56,0.75)', link: 'rgba(152,162,179,0.35)' }

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
    if (!data.nodes.length) return
    // noduri mai depărtate, ca etichetele să nu se suprapună; aplicat după ce graful s-a montat
    const t1 = setTimeout(() => {
      const g = fg.current
      if (!g) return
      g.d3Force('charge')?.strength(-520)
      const link = g.d3Force('link') as { distance?: (d: number) => unknown } | undefined
      link?.distance?.(100)
      g.d3ReheatSimulation()
    }, 0)
    const t2 = setTimeout(() => fg.current?.zoomToFit(400, 70), 1200)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [data.nodes.length])

  const ringSize = graph.nodes.filter((n) => n.type === 'case' && n.in_cluster).length

  return (
    <div ref={wrap} className="relative w-full overflow-hidden rounded-sm bg-[#161A20]">
      {graph.nodes.length === 0 ? (
        <div className="flex items-center justify-center text-[#98A2B3]" style={{ height }}>
          Nicio legătură găsită încă.
        </div>
      ) : (
        <ForceGraph2D<N>
          ref={fg}
          width={width}
          height={height}
          graphData={data}
          cooldownTicks={120}
          linkColor={(l) => ((l as { kind: string }).kind === 'phone' || (l as { kind: string }).kind === 'iban'
            ? C.linkStrong : C.link)}
          linkWidth={(l) => ((l as { kind: string }).kind === 'phone' || (l as { kind: string }).kind === 'iban' ? 2.5 : 1)}
          nodeLabel={(n) => (n.type === 'case'
            ? `${n.label.replace(/^\[PERSOANA_(\w+)\]$/, 'Persoana $1')}, dosarul ${n.case_id}${n.risk != null ? `, risc ${Math.round(n.risk * 100)}` : ''}`
            : `${FP_LABEL[n.kind ?? ''] ?? n.kind} comun la ${n.shared_by} dosare`)}
          nodeCanvasObject={(n, ctx, scale) => {
            const x = n.x ?? 0
            const y = n.y ?? 0
            if (n.type === 'case') {
              const r = (n.is_focus ? 13 : 9) / scale // dimensiune fixă pe ecran, indiferent de zoom
              ctx.beginPath()
              ctx.arc(x, y, r, 0, 2 * Math.PI)
              ctx.fillStyle = n.is_focus ? C.focus : n.in_cluster ? C.ring : C.other
              ctx.fill()
              if (n.is_focus) { ctx.lineWidth = 3 / scale; ctx.strokeStyle = '#161A20'; ctx.stroke() }
              // o singură etichetă pe graf (dosarul curent); restul apar la hover, ca să nu se suprapună
              if (n.is_focus) {
                ctx.fillStyle = C.text
                ctx.font = `600 ${13 / scale}px 'IBM Plex Sans', sans-serif`
                ctx.textAlign = 'center'
                ctx.textBaseline = 'top'
                ctx.fillText('Acest dosar', x, y + r + 5 / scale)
              }
            } else {
              const tag = FP_TAG[n.kind ?? ''] ?? '?'
              ctx.font = `600 ${12 / scale}px 'IBM Plex Sans', sans-serif`
              const w = ctx.measureText(tag).width + 10 / scale
              const h = 18 / scale
              ctx.fillStyle = n.in_cluster ? '#3A1C1A' : '#262B33'
              ctx.strokeStyle = n.in_cluster ? C.ring : '#475467'
              ctx.lineWidth = 1 / scale
              ctx.beginPath()
              ctx.rect(x - w / 2, y - h / 2, w, h)
              ctx.fill()
              ctx.stroke()
              ctx.fillStyle = n.in_cluster ? '#FECDCA' : '#D0D5DD'
              ctx.textAlign = 'center'
              ctx.textBaseline = 'middle'
              ctx.fillText(tag, x, y + 0.5 / scale)
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
      <div className="pointer-events-none absolute bottom-3 left-3 flex flex-wrap gap-x-5 gap-y-1 text-sm text-[#D0D5DD]">
        <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-brand" />Acest dosar</span>
        <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-[#F04438]" />Rețea suspectă ({Math.max(0, ringSize - 1)} dosare)</span>
        <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-[#98A2B3]" />Alte dosare</span>
        <span className="text-[#98A2B3]">Etichetele tel, IBAN, adr, CNP sunt date comune, păstrate ca amprente. Treci cu mouse-ul peste un dosar ca să-l vezi.</span>
      </div>
    </div>
  )
}
