import { Calculator, CircleAlert, CircleCheck, CircleDashed, EyeOff, Lock, ShieldCheck } from 'lucide-react'
import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { apiFetch } from '@/lib/api'
import { normAnswer, normText } from '@/lib/zk'
import { cn } from '@/lib/utils'

// Dovezile de confidențialitate ale dosarului (GET /api/cases/{id}/privacy).
// Nimic nu e decriptat pentru afișare: arătăm ce stă pe disc, ce a primit AI-ul, calculul HE și rezultatul ZK.

interface Privacy {
  at_rest: {
    scheme: string
    documents: { doc_id: string; filename: string; encrypted_bytes: number; sample: string }[]
    vault: { labels: string[]; count: number; sample: string | null }
  }
  ai_saw: { llm_calls: number; local_calls?: number; with_pii: number; blocked: number; models: string[]; redacted_sample: string | null }
  homomorphic: null | {
    he_scheme: string; he_formula: string; he_ms: string; he_ciphertext_kb: string; he_context_kb: string
    he_ciphertext_sample: string; verifier_has_secret_key: boolean
  }
  zk: null | { answer: string; reason: string; threshold_ron?: number | null; employer?: string | null }
  prompt_injection_detected: boolean
}

const kb = (n: number) => `${Math.round(n / 1024).toLocaleString('en-GB')} KB`

function Card({ n, icon, title, status, ok, children, proof }: {
  n: number; icon: ReactNode; title: string; status: string; ok: boolean | null; children: ReactNode; proof?: ReactNode
}) {
  const Mark = ok === null ? CircleDashed : ok ? CircleCheck : CircleAlert
  return (
    // arată ca o dovadă: muchie colorată după rezultat, număr, și o bucată din dovada reală vizibilă direct
    <div className={cn('flex flex-col rounded-md border border-line border-t-[3px] bg-surface p-4',
      ok === null ? 'border-t-line' : ok ? 'border-t-ok' : 'border-t-danger')}>
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-1.5 font-condensed text-xs font-semibold uppercase tracking-[0.14em] text-ink-3">
          {icon}Proof {String(n).padStart(2, '0')}
        </span>
        <Mark className={cn('h-5 w-5', ok === null ? 'text-ink-3' : ok ? 'text-ok' : 'text-danger')} aria-hidden />
      </div>
      <div className="mt-2 text-base font-semibold leading-snug text-ink">{title}</div>
      <div className={cn('mt-0.5 text-sm font-medium', ok === null ? 'text-ink-3' : ok ? 'text-ok' : 'text-danger')}>{status}</div>
      <div className="mt-3 text-sm text-ink-2">{children}</div>
      {proof && (
        <>
          <div className="relative mt-3 max-h-20 overflow-hidden" aria-hidden>
            <div className="space-y-2">{proof}</div>
            <span className="absolute inset-x-0 bottom-0 h-8 bg-linear-to-t from-surface" />
          </div>
          <details className="mt-1 text-sm">
            <summary className="cursor-pointer font-medium text-ink hover:underline">See the evidence</summary>
            <div className="mt-2 space-y-2">{proof}</div>
          </details>
        </>
      )}
    </div>
  )
}

const Mono = ({ children }: { children: ReactNode }) => (
  <pre className="max-h-48 overflow-auto whitespace-pre-wrap break-all rounded-sm bg-canvas p-2 font-mono text-xs text-ink-2">{children}</pre>
)

export function PrivacyPanel({ caseId, ready }: { caseId: string; ready: boolean }) {
  const [data, setData] = useState<Privacy | null>(null)
  const [error, setError] = useState(false)
  const [zkBusy, setZkBusy] = useState(false)

  const load = useCallback(() => {
    apiFetch(`/api/cases/${encodeURIComponent(caseId)}/privacy`)
      .then((r) => r.json())
      .then((d: Privacy) => { setData(d); setError(false) })
      .catch(() => setError(true))
  }, [caseId])

  useEffect(() => { if (ready) load() }, [ready, load])

  const askZk = () => {
    setZkBusy(true)
    apiFetch('/api/zk/demo', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ case_id: caseId }),
    })
      .then(load)
      .catch(() => alert('The ZK proof could not be generated: the server did not respond.'))
      .finally(() => setZkBusy(false))
  }

  if (!ready) return null
  if (error) return <p className="text-sm text-ink-3">The privacy evidence could not be loaded.</p>
  if (!data) return <p className="text-sm text-ink-3">Loading the privacy evidence.</p>

  const { at_rest: rest, ai_saw: ai, homomorphic: he, zk } = data
  const totalEnc = rest.documents.reduce((s, d) => s + d.encrypted_bytes, 0)

  return (
    <section aria-label="Privacy" className="space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="flex items-center gap-2.5 text-lg font-semibold text-ink"><span className="h-4 w-1 shrink-0 bg-brand" aria-hidden />What the bank can prove about the client's data</h2>
        <span className="text-sm text-ink-3">Nothing is decrypted for this page.</span>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card n={1} icon={<Lock className="h-3.5 w-3.5" />} title="Encrypted on disk" ok={rest.documents.length > 0}
          status={`${rest.documents.length} documents, ${rest.vault.count} values in the vault`}
          proof={<>
            {rest.documents.map((d) => (
              <div key={d.doc_id}><div className="text-xs text-ink-3">{d.filename}, {kb(d.encrypted_bytes)} on disk</div><Mono>{d.sample}</Mono></div>
            ))}
            {rest.vault.sample && <div><div className="text-xs text-ink-3">Vault: {rest.vault.labels.join(' ')}</div><Mono>{rest.vault.sample}</Mono></div>}
          </>}>
          The files ({kb(totalEnc)}) and personal data are stored encrypted ({rest.scheme.split(' ')[0]}, AES). There is no plaintext image or CNP on disk.
        </Card>

        <Card n={2} icon={<EyeOff className="h-3.5 w-3.5" />} title="The AI saw no personal data" ok={ai.with_pii === 0}
          status={ai.llm_calls > 0 && ai.local_calls === ai.llm_calls
            ? `${ai.llm_calls} AI requests, all on the bank's own computer`
            : `${ai.llm_calls} AI requests, ${ai.with_pii} with personal data`}
          proof={ai.redacted_sample ? <><div className="text-xs text-ink-3">The exact text the AI received:</div><Mono>{ai.redacted_sample}</Mono></> : undefined}>
          The AI works on labels like [PERSOANA_1] and [CNP_1]. Even if tricked by hidden text, it has no real data to leak.
          {ai.blocked > 0 && ` The PII gate blocked ${ai.blocked} requests.`}
          {data.prompt_injection_detected && <span className="mt-1 block font-medium text-danger">The document contains text that tries to trick the AI.</span>}
        </Card>

        <Card n={3} icon={<Calculator className="h-3.5 w-3.5" />} title="Computation on encrypted data" ok={he ? true : null}
          status={he ? `${he.he_scheme.split(',')[0]}, ${he.he_ms} ms` : 'not used for this application'}
          proof={he ? <>
            <div className="text-xs text-ink-3">Formula computed on the ciphertext: {he.he_formula}</div>
            <div className="text-xs text-ink-3">First bytes of the encrypted salary ({he.he_ciphertext_kb} KB):</div>
            <Mono>{he.he_ciphertext_sample}…</Mono>
          </> : undefined}>
          {he
            ? <>The payslip deductions were recomputed by a verifier that received only the encrypted amounts and <b>does not hold the key</b>. The bank decrypts only the result.</>
            : 'The payslip had no readable amounts for the encrypted check.'}
        </Card>

        <Card n={4} icon={<ShieldCheck className="h-3.5 w-3.5" />} title="Income proved without seeing it" ok={zk ? zk.answer === 'DA' || zk.answer === 'YES' : null}
          status={zk ? `ZK answer: ${normAnswer(zk.answer)}` : 'not requested yet'}>
          {zk
            ? <>{normText(zk.reason)}{zk.threshold_ron ? ` (threshold ${zk.threshold_ron.toLocaleString('en-GB')} lei` : ''}{zk.employer ? `, attested by ${zk.employer})` : zk.threshold_ron ? ')' : ''}.</>
            : 'The client can prove their income clears the required threshold without showing it to the bank (zero-knowledge).'}
          <button type="button" onClick={askZk} disabled={zkBusy}
            className="mt-3 flex h-9 items-center rounded-sm border border-line px-3 text-sm font-medium text-ink hover:bg-canvas disabled:opacity-40">
            {zkBusy ? 'Generating the proof…' : zk ? 'Request again' : 'Request income proof'}
          </button>
        </Card>
      </div>
    </section>
  )
}
