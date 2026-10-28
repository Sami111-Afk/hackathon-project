import { useEffect, useState } from 'react'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { getDocumentImage } from '@/lib/api'
import { DOC_LABEL, SEVERITY } from '@/lib/labels'
import { cn } from '@/lib/utils'
import type { Document, Finding } from '@/lib/types'

type View = 'original' | 'redacted' | 'ela'
const VIEWS: { id: View; label: string }[] = [
  { id: 'original', label: 'Original' },
  { id: 'redacted', label: 'Ce a văzut AI-ul' },
  { id: 'ela', label: 'Harta de editare (ELA)' },
]

/** Un document cu cele 3 vederi și chenarele (bbox) problemelor găsite pe el. */
export function DocumentViewer({
  caseId, doc, findings, mock, highlighted,
}: {
  caseId: string
  doc: Document
  findings: Finding[]
  mock: boolean
  highlighted?: Finding | null
}) {
  const [view, setView] = useState<View>('redacted')
  const [src, setSrc] = useState<string | null>(null)
  const [failed, setFailed] = useState(false)
  const page = doc.pages[0] ?? { page: 1, width: 1654, height: 2339 }

  useEffect(() => {
    setSrc(null)
    setFailed(false)
    if (mock) return
    let url: string | null = null
    let cancelled = false
    getDocumentImage(caseId, doc.id, view, page.page)
      .then((u) => { url = u; if (!cancelled) setSrc(u) })
      .catch(() => { if (!cancelled) setFailed(true) })
    return () => { cancelled = true; if (url) URL.revokeObjectURL(url) }
  }, [caseId, doc.id, view, page.page, mock])

  const boxes = findings.filter(
    (f) => f.evidence?.doc_id === doc.id && f.evidence.bbox && (f.evidence.page ?? 1) === page.page,
  )

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-xl font-semibold">
          {DOC_LABEL[doc.type]} <span className="text-base font-normal text-slate-500">· {doc.filename}</span>
        </h3>
        <Tabs value={view} onValueChange={(v) => setView(v as View)}>
          <TabsList>
            {VIEWS.map((v) => <TabsTrigger key={v.id} value={v.id}>{v.label}</TabsTrigger>)}
          </TabsList>
        </Tabs>
      </div>

      {/* Containerul are raportul paginii, iar chenarele sunt în procente → se scalează cu imaginea. */}
      <div
        className="relative w-full overflow-hidden rounded-lg border bg-slate-100"
        style={{ aspectRatio: `${page.width} / ${page.height}` }}
      >
        {src ? (
          <img src={src} alt={`${DOC_LABEL[doc.type]} — ${view}`} className="absolute inset-0 h-full w-full object-contain" />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center p-6 text-center text-slate-500">
            {mock ? (
              <pre className="max-w-full whitespace-pre-wrap font-mono text-sm">{doc.redacted_text}</pre>
            ) : failed ? 'Imaginea nu a putut fi încărcată' : 'Se încarcă…'}
          </div>
        )}
        {boxes.map((f, i) => {
          const [x0, y0, x1, y1] = f.evidence!.bbox!
          const active = highlighted === f
          return (
            <div
              key={i}
              title={f.message}
              className={cn(
                'absolute rounded-sm border-[3px] transition-all',
                f.severity === 'critical' || f.severity === 'high' ? 'border-red-600 bg-red-500/15' : 'border-amber-500 bg-amber-400/15',
                active && 'ring-4 ring-blue-500 ring-offset-2',
              )}
              style={{
                left: `${(x0 / page.width) * 100}%`,
                top: `${(y0 / page.height) * 100}%`,
                width: `${((x1 - x0) / page.width) * 100}%`,
                height: `${((y1 - y0) / page.height) * 100}%`,
              }}
            >
              <span className={cn('absolute -top-7 left-0 whitespace-nowrap rounded border px-1.5 text-xs font-semibold', SEVERITY[f.severity].cls)}>
                {SEVERITY[f.severity].icon} {f.code}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
