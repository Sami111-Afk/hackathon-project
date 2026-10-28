import { FileUp, Loader2, X } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { createCase } from '@/lib/api'

const MAX_FILES = 5
const ACCEPT = 'image/png,image/jpeg,application/pdf'

/** Dosar nou: actele clientului + suma cerută. Analiza pornește pe server, iar pagina dosarului o arată live. */
export function NewCaseForm({ onClose }: { onClose: () => void }) {
  const nav = useNavigate()
  const [files, setFiles] = useState<File[]>([])
  const [amount, setAmount] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function pick(list: FileList | null) {
    const next = [...files, ...Array.from(list ?? [])].slice(0, MAX_FILES)
    setFiles(next)
    setError(null)
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!files.length) { setError('Add at least one document.'); return }
    setBusy(true)
    setError(null)
    try {
      const id = await createCase(files, Number(amount) || undefined)
      nav(`/cases/${id}`)
    } catch (err) {
      const status = (err as { status?: number }).status
      setError(status === 413 ? 'A file is too large (maximum 5 MB).'
        : status === 415 ? 'Only PNG, JPG or PDF are accepted.'
        : 'The application was not created: the server did not respond. Try again.')
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="rounded-md border border-line bg-surface">
      <header className="flex items-center justify-between border-b border-line px-5 py-3">
        <h2 className="text-lg font-semibold">New application</h2>
        <button type="button" onClick={onClose} aria-label="Close" className="text-ink-3 hover:text-ink"><X className="h-5 w-5" /></button>
      </header>
      <div className="grid gap-5 p-5 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div>
          <label className="flex min-h-36 cursor-pointer flex-col items-center justify-center gap-2 rounded-sm border border-dashed border-input bg-canvas/50 p-6 text-center hover:bg-canvas">
            <FileUp className="h-6 w-6 text-ink-3" aria-hidden />
            <span className="text-[15px] font-medium text-ink">Choose the client's documents</span>
            <span className="text-sm text-ink-3">ID card, payslip, bank statement. PNG, JPG or PDF, up to {MAX_FILES} files.</span>
            <input type="file" multiple accept={ACCEPT} className="sr-only" onChange={(e) => pick(e.target.files)} />
          </label>
          {files.length > 0 && (
            <ul className="mt-3 divide-y divide-line rounded-sm border border-line">
              {files.map((f, i) => (
                <li key={`${f.name}-${i}`} className="flex items-center justify-between px-3 py-2 text-[15px]">
                  <span className="truncate">{f.name}</span>
                  <button type="button" onClick={() => setFiles(files.filter((_, j) => j !== i))} className="text-sm text-ink-3 hover:text-danger">Remove</button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="space-y-4">
          <label className="block">
            <span className="text-sm font-medium text-ink-2">Requested amount (lei)</span>
            <input inputMode="numeric" value={amount} onChange={(e) => setAmount(e.target.value.replace(/\D/g, ''))} placeholder="45000"
                   className="mt-1.5 h-11 w-full rounded-sm border border-input bg-surface px-3 text-base outline-none focus:border-info" />
          </label>
          <p className="text-sm text-ink-3">Documents are encrypted on the server right away. Personal data is hidden before the AI sees it.</p>
          {error && <p className="text-sm text-danger">{error}</p>}
          <button type="submit" disabled={busy}
            className="flex h-11 w-full items-center justify-center gap-2 rounded-sm bg-ink text-base font-semibold text-white hover:bg-black disabled:opacity-50">
            {busy ? <><Loader2 className="h-4 w-4 animate-spin" aria-hidden />Uploading documents</> : 'Start analysis'}
          </button>
        </div>
      </div>
    </form>
  )
}
