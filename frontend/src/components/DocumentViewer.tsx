import { ImageOff, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { getDocumentImage } from '@/lib/api'
import { DOC_LABEL, SEVERITY } from '@/lib/labels'
import type { Document, Finding } from '@/lib/types'
import { cn } from '@/lib/utils'

type View = 'original' | 'redacted' | 'ela'
const VIEWS: { id: View; label: string; hint: string }[] = [
  { id: 'redacted', label: 'What the AI saw', hint: 'Personal data is covered' },
  { id: 'original', label: 'Original', hint: 'The document as received' },
  { id: 'ela', label: 'Edit map', hint: 'Bright areas were modified' },
]

/** Actele din dosar: un tab pe document, trei vederi, chenare peste dovezi. */
export function DocumentViewer({
  caseId, docs, findings, mock, highlighted, docId, onDocChange,
}: {
  caseId: string
  docs: Document[]
  findings: Finding[]
  mock: boolean
  highlighted?: Finding | null
  docId: string
  onDocChange: (id: string) => void
}) {
  const [view, setView] = useState<View>('redacted')
  const [img, setImg] = useState<{ key: string; src: string | null; failed: boolean }>({ key: '', src: null, failed: false })
  const doc = docs.find((d) => d.id === docId) ?? docs[0]
  const page = doc?.pages[0] ?? { page: 1, width: 1654, height: 2339 }
  const key = `${doc?.id}|${view}`

  useEffect(() => {
    if (mock || !doc) return
    let url: string | null = null
    let cancelled = false
    getDocumentImage(caseId, doc.id, view, page.page)
      .then((u) => { url = u; if (!cancelled) setImg({ key, src: u, failed: false }) })
      .catch(() => { if (!cancelled) setImg({ key, src: null, failed: true }) })
    // Eliberarea după o secundă: în estomparea dintre pagini, imaginea veche mai e citită o clipă.
    return () => { cancelled = true; const u = url; if (u) setTimeout(() => URL.revokeObjectURL(u), 1000) }
  }, [caseId, doc, view, page.page, mock, key])

  if (!doc) return null
  const current = img.key === key ? img : { src: null, failed: false }
  const boxes = findings.filter((f) => f.evidence?.doc_id === doc.id && f.evidence.bbox && (f.evidence.page ?? 1) === page.page)
  const flagged = (id: string) => findings.some((f) => f.evidence?.doc_id === id && f.severity !== 'info')

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-3 border-b border-line px-5">
        <div role="tablist" aria-label="Documents" className="flex gap-5">
          {docs.map((d) => (
            <button key={d.id} role="tab" aria-selected={d.id === doc.id} type="button" onClick={() => onDocChange(d.id)}
              className={cn('flex items-center gap-2 border-b-2 py-3.5 text-[15px] font-medium',
                d.id === doc.id ? 'border-ink text-ink' : 'border-transparent text-ink-2 hover:text-ink')}>
              {d.type === 'unknown' ? `Document ${docs.indexOf(d) + 1}` : DOC_LABEL[d.type]}
              {flagged(d.id) && <span className="h-2 w-2 rounded-full bg-danger" aria-label="has evidence" />}
            </button>
          ))}
        </div>
        <div className="mb-2 flex overflow-hidden rounded-sm border border-line" role="group" aria-label="View">
          {VIEWS.map((v) => (
            <button key={v.id} type="button" title={v.hint} aria-pressed={view === v.id} onClick={() => setView(v.id)}
              className={cn('px-3 py-1.5 text-sm font-medium', view === v.id ? 'bg-ink text-white' : 'text-ink-2 hover:text-ink')}>
              {v.label}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-canvas p-5">
        <div className="relative mx-auto w-full max-w-3xl overflow-hidden rounded-sm bg-surface ring-1 ring-line"
             style={{ aspectRatio: `${page.width} / ${page.height}` }}>
          {current.src ? (
            <img src={current.src} alt={`${DOC_LABEL[doc.type]}: ${VIEWS.find((v) => v.id === view)?.label}`}
                 className="absolute inset-0 h-full w-full object-contain" />
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-8 text-center text-ink-3">
              {mock ? (
                <pre className="max-w-full whitespace-pre-wrap text-left text-sm leading-relaxed text-ink-2">{doc.redacted_text}</pre>
              ) : current.failed ? (
                <><ImageOff className="h-6 w-6" aria-hidden />The “{VIEWS.find((v) => v.id === view)?.label}” view is not available for this document.</>
              ) : (
                <><Loader2 className="h-6 w-6 animate-spin" aria-hidden />Loading the document</>
              )}
            </div>
          )}
          {boxes.map((f, i) => {
            const [x0, y0, x1, y1] = f.evidence!.bbox!
            const sev = SEVERITY[f.severity]
            return (
              <div key={i} title={f.message}
                className={cn('absolute border-2', f.severity === 'critical' || f.severity === 'high' ? 'border-danger bg-danger/10' : 'border-warn bg-warn/10',
                  highlighted === f && 'outline outline-2 outline-offset-4 outline-info')}
                style={{ left: `${(x0 / page.width) * 100}%`, top: `${(y0 / page.height) * 100}%`,
                         width: `${((x1 - x0) / page.width) * 100}%`, height: `${((y1 - y0) / page.height) * 100}%` }}>
                <span className={cn('absolute -top-6 left-0 whitespace-nowrap rounded-sm px-1.5 py-0.5 text-xs font-semibold text-white',
                  f.severity === 'critical' || f.severity === 'high' ? 'bg-danger' : 'bg-warn')}>
                  {sev.label}
                </span>
              </div>
            )
          })}
        </div>
        <p className="mx-auto mt-3 max-w-3xl text-sm text-ink-3">{doc.filename} · {VIEWS.find((v) => v.id === view)?.hint}</p>
      </div>
    </div>
  )
}
